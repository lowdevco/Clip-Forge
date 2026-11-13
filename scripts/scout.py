#!/usr/bin/env python3
"""Rank the stretches of a video where the most is happening, and save a
filmstrip of each so you can look at them. Built for gameplay and other
videos where the best moments are in the action, not the words.

Usage: python scout.py VIDEO --out WORKDIR [--top 12] [--len 30]

For every window of --len seconds it measures
  loud    how far the sound rises above its surroundings (shouts, gunfire,
          explosions, laughter)
  motion  how much the picture changes (fights, chases, fast cuts)
and ranks the windows by the two together. The "action" score (0-100) is a
rank inside this one video: it says where to look first, not how good the
moment is. Judge the moment from the filmstrip.

Writes WORKDIR/scout.json and WORKDIR/scout/NN.jpg (8 frames per window, in
order), plus WORKDIR/scout/end.jpg for the last 45 seconds, because results
screens, wins and fails usually sit at the very end.
"""
import argparse
import json
import os
import subprocess

import numpy as np

from analyze_audio import WIN, loudness, ts
from peek import make_sheet, spread

FPS = 4            # frames per second sampled for motion
MW, MH = 160, 90   # motion is measured on a tiny grey copy


def motion(video):
    """Mean absolute change between sampled frames, one value per 0.5 s."""
    proc = subprocess.Popen(
        ["ffmpeg", "-loglevel", "error", "-i", video, "-an",
         "-vf", f"fps={FPS},scale={MW}:{MH},format=gray", "-f", "rawvideo", "-"],
        stdout=subprocess.PIPE)
    vals, prev, size = [], None, MW * MH
    while True:
        buf = proc.stdout.read(size)
        if len(buf) < size:
            break
        frame = np.frombuffer(buf, dtype=np.uint8).astype(np.int16)
        vals.append(0.0 if prev is None else float(np.abs(frame - prev).mean()))
        prev = frame
    proc.wait()
    vals = np.array(vals, dtype=np.float32)
    if not len(vals):
        return vals
    # A hard cut changes every pixel once; cap it so cuts do not outweigh
    # sustained movement.
    vals = np.minimum(vals, np.percentile(vals, 95))
    per = int(FPS * WIN)
    return vals[:len(vals) // per * per].reshape(-1, per).mean(axis=1)


def zscore(x):
    sd = float(x.std())
    return (x - x.mean()) / sd if sd > 1e-6 else np.zeros_like(x)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--out", required=True)
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--len", dest="length", type=float, default=30,
                    help="window length in seconds")
    ap.add_argument("--no-strips", action="store_true")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    db, lift, seconds = loudness(args.video)
    mot = motion(args.video)
    n = min(len(db), len(mot)) if len(mot) else len(db)
    db, lift = db[:n], lift[:n]
    mot = mot[:n] if len(mot) else np.zeros(n, dtype=np.float32)

    win = max(int(args.length / WIN), 4)
    if n <= win:
        raise SystemExit("video is shorter than one window; lower --len")
    step = int(2 / WIN)
    above = np.maximum(lift, 0)                  # rises above the local minute
    hot = np.maximum(db - np.median(db), 0)      # louder than the whole video
    starts = np.arange(0, n - win + 1, step)
    a = np.array([above[s:s + win].mean() for s in starts])
    h = np.array([hot[s:s + win].mean() for s in starts])
    m = np.array([mot[s:s + win].mean() for s in starts])
    score = 0.35 * zscore(a) + 0.25 * zscore(h) + 0.40 * zscore(m)
    rank = score.argsort().argsort() / max(len(score) - 1, 1) * 100
    m_rank = m.argsort().argsort() / max(len(m) - 1, 1) * 100
    a_rank = (a + h).argsort().argsort() / max(len(a) - 1, 1) * 100

    picked = []
    for i in np.argsort(-score):
        s = int(starts[i])
        if any(abs(s - p) < win + int(4 / WIN) for p in picked):
            continue
        picked.append(s)
        if len(picked) >= args.top:
            break

    strips = os.path.join(args.out, "scout")
    if not args.no_strips:
        os.makedirs(strips, exist_ok=True)
    index = {int(s): i for i, s in enumerate(starts)}
    rows = []
    for num, s in enumerate(sorted(picked, key=lambda p: -score[index[p]]), 1):
        i = index[s]
        t0, t1 = s * WIN, (s + win) * WIN
        peak = (s + int(np.argmax(lift[s:s + win]))) * WIN
        row = {"n": num, "start": round(t0, 1), "end": round(t1, 1),
               "window": f"{ts(t0)}-{ts(t1)}", "action": int(round(rank[i])),
               "loud": int(round(a_rank[i])), "motion": int(round(m_rank[i])),
               "loudest_at": ts(peak), "loudest_t": round(peak, 1)}
        if not args.no_strips:
            path = os.path.join(strips, f"{num:02d}.jpg")
            if make_sheet(args.video, spread(t0, t1, 8), path, cols=4,
                          tile_w=480):
                row["strip"] = path
        rows.append(row)

    result = {"duration": round(seconds, 1), "window_seconds": args.length,
              "windows": rows}
    if not args.no_strips and seconds > 50:
        end = os.path.join(strips, "end.jpg")
        if make_sheet(args.video, spread(seconds - 45, seconds - 1, 8), end,
                      cols=4, tile_w=480):
            result["ending_strip"] = end
    with open(os.path.join(args.out, "scout.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1)

    print(f"duration {ts(seconds)}, {len(rows)} windows of {args.length:g}s, "
          "strongest first")
    print(" #  window        action  loud  motion  loudest at")
    for r in rows:
        print(f"{r['n']:>2}  {r['window']:<12} {r['action']:>6} {r['loud']:>5} "
              f"{r['motion']:>7}  {r['loudest_at']}")
    if not args.no_strips:
        print(f"filmstrips: {strips} (NN.jpg per window, end.jpg = last 45 s)")


if __name__ == "__main__":
    main()
