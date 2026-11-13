#!/usr/bin/env python3
"""Find the people in each clip and who is speaking when, so the renderer can
frame them: follow the active speaker, or stack two speakers.

Usage: python track.py VIDEO --clips WORKDIR/clips.json [--only 1,3] [--write]

For each clip it
  1. finds the camera cuts, so every shot is handled on its own (a position
     from before a cut means nothing after it);
  2. detects faces (YuNet) about six times a second and groups them into
     people by position within the shot;
  3. scores how much each person's mouth area moves compared with the rest
     of their face while there is sound, and takes the one whose mouth moves
     most as the speaker.

Prints one JSON line per clip:
  shots       each shot's time span and the people in it: face centre
              (cx, cy as 0-1), size, and share of the talking in that shot
  suggest     speaker | stack | blur, with the reason
  focus_path  [[source seconds, cx], ...] crop positions: a new one at every
              camera cut and whenever the speaker changes
  no_face     share of the clip where no face was found

--write stores "focus_path" and, where it applies, "faces" back into
clips.json, and sets the layout where it is "auto" or missing.

This is a heuristic, not a trained active-speaker model. It is usually right
for people facing the camera, and can be fooled by laughing, eating, a hand
near the mouth, or an off-screen voice. Render with --preview and look at a
few frames before trusting it on a new show.
"""
import argparse
import json
import subprocess
import sys

import cv2
import numpy as np

import faces as facelib

SAMPLE_HZ = 6
MIN_TURN = 1.5          # seconds a speaker must hold before the crop moves


def audio_activity(video, start, dur, times):
    """For each sample time: is there sound above the clip's quiet floor?"""
    raw = subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-ss", f"{start:.3f}", "-t", f"{dur:.3f}",
         "-i", video, "-vn", "-ac", "1", "-ar", "8000", "-f", "s16le", "-"],
        capture_output=True).stdout
    pcm = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
    n = 1600                                      # 0.2 s windows
    if len(pcm) < n * 5:
        return np.ones(len(times), dtype=bool)
    fr = pcm[:len(pcm) // n * n].reshape(-1, n)
    db = 20 * np.log10(np.sqrt((fr ** 2).mean(axis=1)) + 1e-6)
    loud = db > np.percentile(db, 15) + 8
    idx = np.clip(((np.array(times) - start) / 0.2).astype(int), 0, len(loud) - 1)
    return loud[idx]


def region(gray, cx, cy, w, h):
    H, W = gray.shape
    x0, x1 = int(max(cx - w / 2, 0)), int(min(cx + w / 2, W))
    y0, y1 = int(max(cy - h / 2, 0)), int(min(cy + h / 2, H))
    if x1 - x0 < 6 or y1 - y0 < 6:
        return None
    return cv2.resize(gray[y0:y1, x0:x1], (32, 20)).astype(np.float32)


def scan(video, start, end):
    """Read the clip once. Returns (samples, cuts): samples are
    (time, shot number, [face dicts with cx, cy, h, motion]); cuts are the
    times a new shot begins."""
    cap = cv2.VideoCapture(video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    step = max(int(round(fps / SAMPLE_HZ)), 3)
    cap.set(cv2.CAP_PROP_POS_MSEC, start * 1000)
    samples, cuts, recent = [], [start], []
    shot, k, held, prev_small, since_cut = 0, 0, None, None, 0
    while True:
        ok, frame = cap.read()
        t = start + k / fps
        if not ok or t > end:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        small = cv2.resize(gray, (64, 36)).astype(np.float32)
        if prev_small is not None:
            d = float(np.abs(small - prev_small).mean())
            base = float(np.median(recent)) if recent else 1.0
            # A cut changes the whole picture at once, far beyond the motion
            # of the frames before it.
            if d > 9 and d > 5 * max(base, 0.8) and since_cut > fps * 0.4:
                shot += 1
                cuts.append(round(t, 3))
                held, since_cut = None, 0
            recent = (recent + [d])[-20:]
        prev_small = small
        since_cut += 1
        phase = k % step
        if phase == 0:
            H, W = gray.shape
            held = (t, gray, [f for f in facelib.detect(frame, max_w=960)[:5]
                              if f["h"] / H >= 0.05], shot)
        elif phase == 2 and held is not None and held[3] == shot:
            t0, g0, found, _ = held
            H, W = g0.shape
            row = []
            for f in found:
                mx, my = f["mouth"]
                ex, ey = f["eyes"]
                m0 = region(g0, mx, my + f["h"] * 0.06, f["w"] * 0.55, f["h"] * 0.34)
                m1 = region(gray, mx, my + f["h"] * 0.06, f["w"] * 0.55, f["h"] * 0.34)
                e0 = region(g0, ex, ey, f["w"] * 0.7, f["h"] * 0.25)
                e1 = region(gray, ex, ey, f["w"] * 0.7, f["h"] * 0.25)
                motion = 0.0
                if not (m0 is None or m1 is None or e0 is None or e1 is None):
                    # Mouth movement beyond what the whole head is doing.
                    motion = float(max(np.abs(m1 - m0).mean()
                                       - np.abs(e1 - e0).mean(), 0))
                row.append({"cx": (f["x"] + f["w"] / 2) / W,
                            "cy": (f["y"] + f["h"] / 2) / H,
                            "h": f["h"] / H, "motion": motion})
            samples.append((t0, shot, row))
            held = None
        k += 1
    cap.release()
    return samples, cuts


def track_shot(rows, active):
    """rows: [(t, faces)] of one shot. Returns (people, speaker index per
    sample or -1). People are grouped by horizontal position."""
    people = []
    assign = []
    for _, found in rows:
        mine = {}
        for f in found:
            for i, p in enumerate(people):
                if abs(np.median(p["cx"][-30:]) - f["cx"]) < 0.10:
                    break
            else:
                people.append({"cx": [], "cy": [], "h": []})
                i = len(people) - 1
            if i in mine:
                continue
            p = people[i]
            p["cx"].append(f["cx"])
            p["cy"].append(f["cy"])
            p["h"].append(f["h"])
            mine[i] = f["motion"]
        assign.append(mine)
    n = len(rows)
    keep = [i for i, p in enumerate(people) if len(p["cx"]) >= max(2, n * 0.2)]
    if not keep:
        return [], [-1] * n
    motion = np.zeros((len(keep), n), dtype=np.float32)
    seen = np.zeros((len(keep), n), dtype=bool)
    for j, mine in enumerate(assign):
        for a, i in enumerate(keep):
            if i in mine:
                motion[a, j], seen[a, j] = mine[i], True
    w = max(int(SAMPLE_HZ * 0.9), 1)
    kern = np.ones(w) / w
    smooth = np.array([np.convolve(motion[a], kern, mode="same")
                       for a in range(len(keep))])
    speaker, cur = [], int(np.argmax(seen.sum(axis=1)))
    for j in range(n):
        if active[j] and smooth[:, j].max() > 0:
            best = int(np.argmax(smooth[:, j]))
            if smooth[best, j] > smooth[cur, j] * 1.3:
                cur = best
        speaker.append(cur)
    min_run = int(SAMPLE_HZ * MIN_TURN)
    j = 0
    while j < n:                                   # drop very short turns
        e = j
        while e < n and speaker[e] == speaker[j]:
            e += 1
        if e - j < min_run and j > 0:
            speaker[j:e] = [speaker[j - 1]] * (e - j)
        elif e - j < min_run and e < n:
            # A blip at the start of the shot: open on whoever speaks next,
            # so the crop does not jump a moment after the cut.
            speaker[j:e] = [speaker[e]] * (e - j)
            continue
        j = e
    act = np.array(active, dtype=bool)
    talk = np.bincount(np.array(speaker)[act], minlength=len(keep)) \
        if act.any() else np.zeros(len(keep))
    share = talk / max(talk.sum(), 1)
    out = [{"cx": round(float(np.median(people[i]["cx"])), 3),
            "cy": round(float(np.median(people[i]["cy"])), 3),
            "h": round(float(np.median(people[i]["h"])), 3),
            "talk_share": round(float(share[a]), 2)}
           for a, i in enumerate(keep)]
    return out, speaker


def summarise(video, clip):
    start, end = float(clip["start"]), float(clip["end"])
    samples, cuts = scan(video, start, end)
    if not samples:
        return {"id": clip.get("id"), "shots": [], "focus_path": [],
                "suggest": "blur", "why": "clip could not be read"}
    times = [s[0] for s in samples]
    active = audio_activity(video, start, end - start, times)
    counts = np.array([len(s[2]) for s in samples])
    shots, path = [], []
    bounds = cuts + [end]
    for sid in range(len(cuts)):
        idx = [j for j, s in enumerate(samples) if s[1] == sid]
        t0, t1 = bounds[sid], bounds[sid + 1]
        if not idx:
            # Too short to sample: keep the framing of the shot before.
            continue
        rows = [(samples[j][0], samples[j][2]) for j in idx]
        people, speaker = track_shot(rows, [bool(active[j]) for j in idx])
        shots.append({"start": round(t0, 2), "end": round(t1, 2), "people": people})
        if not people:
            path.append([round(t0, 2), 0.5])       # nobody found: centre
            continue
        last = None
        for (t, _), sp in zip(rows, speaker):
            if sp != last:
                path.append([round(t0 if last is None else t, 2),
                             people[sp]["cx"]])
                last = sp
    path = path[:60]

    dur = max(end - start, 0.1)
    no_face = float((counts == 0).mean())
    together = float((counts >= 2).mean())
    crowd = float((counts >= 3).mean())
    longest = max(shots, key=lambda s: s["end"] - s["start"]) if shots else None
    faces = None
    if no_face > 0.5:
        suggest, why = "blur", "no face found in most of the clip"
    elif together < 0.25:
        suggest, why = "speaker", ("one person on screen at a time; the path "
                                   "follows them through the camera cuts")
    elif crowd >= 0.25:
        suggest, why = "speaker", ("three or more people share the shot; stack "
                                   "shows only two, so the path cuts between them")
    elif longest and len(longest["people"]) == 2 and \
            (longest["end"] - longest["start"]) / dur >= 0.7:
        two = sorted(longest["people"], key=lambda p: p["cx"])
        faces = [[p["cx"], p["cy"]] for p in two]
        if min(p["talk_share"] for p in two) >= 0.25 or \
                sum(p["talk_share"] for p in two) == 0:
            suggest, why = "stack", "two people share one steady shot and both talk"
        else:
            suggest, why = "speaker", "two people share the shot, one does the talking"
    else:
        suggest, why = "speaker", ("two people share some shots, and the camera "
                                   "cuts too often for a steady stack")
    return {"id": clip.get("id"), "suggest": suggest, "why": why,
            "detector": facelib.kind(), "cuts": len(cuts) - 1,
            "no_face": round(no_face, 2), "shots": shots, "faces": faces,
            "focus_path": path}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--clips", required=True)
    ap.add_argument("--only", help="comma-separated clip ids")
    ap.add_argument("--write", action="store_true",
                    help="store the results back into clips.json")
    args = ap.parse_args()
    if facelib.kind() == "none":
        sys.exit("no face detector available (OpenCV model files missing)")
    with open(args.clips, encoding="utf-8") as fh:
        data = json.load(fh)
    wanted = {int(x) for x in args.only.split(",")} if args.only else None
    for clip in data["clips"]:
        if wanted and int(clip.get("id", 0)) not in wanted:
            continue
        r = summarise(args.video, clip)
        print(json.dumps(r, ensure_ascii=False), flush=True)
        if args.write:
            clip.pop("faces", None)
            if r["focus_path"]:
                clip["focus_path"] = r["focus_path"]
                clip["focus_mode"] = "cut"
            if r.get("faces"):
                clip["faces"] = r["faces"]
            if clip.get("layout", "auto") == "auto":
                clip["layout"] = r["suggest"]
    if args.write:
        with open(args.clips, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
