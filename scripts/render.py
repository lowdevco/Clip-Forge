#!/usr/bin/env python3
"""Render approved clips as 1080x1920 vertical Shorts with burned-in captions.

Usage:
  python render.py VIDEO --clips WORKDIR/clips.json --out OUTDIR
                   [--transcript WORKDIR/transcript.json] [--only 1,3]
                   [--style bold|clean|neon|fire] [--watermark "@handle"]
                   [--progress] [--preview]

--style, --watermark and --progress set the default for every clip; a clip can
override each with its own "style", "watermark" and "progress" keys.
--preview renders small, fast drafts (540x960, *_preview.mp4) for checking
framing and timing before the full-quality render.

clips.json:
{"clips": [{
   "id": 1, "start": 754.2, "end": 791.0,
   "hook": "He quit a 40 lakh job for this",   # top headline, first 3.5 s
   "slug": "quit-job",                          # optional file-name part
   "layout": "auto",      # auto | speaker | blur | center | split
   "facecam": [1500, 20, 400, 300],  # split only: x,y,w,h in source pixels
   "zoom": 1.4,           # blur only: enlarge the sharp picture, trimming sides
   "focus_x": 0.5,        # center only: 0 = left edge, 1 = right edge
   "tighten": true,       # cut silences > 0.7 s (talk clips; needs transcript)
   "captions": true,
   "style": "bold",       # caption look: bold | clean | neon | fire
   "watermark": "@handle",  # small channel tag for the whole clip
   "progress": true       # thin progress bar along the top edge
}]}

Layouts
  speaker  9:16 crop centred on the detected face (podcasts, talking head)
  blur     whole frame kept, blurred copy fills top and bottom (gameplay,
           screen recordings, two people far apart)
  center   9:16 crop of the middle (gameplay where the action is central)
  split    facecam on top, gameplay below (needs "facecam")
  auto     speaker if a clear face is found, otherwise blur
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "..", "assets", "fonts")
OUT_W, OUT_H = 1080, 1920
SPLIT_TOP = 608            # facecam band height in the split layout

# Caption looks. Colours are ASS order (&HBBGGRR&); "bar" is the same accent
# as RRGGBB for the progress bar.
STYLES = {
    "bold":  {"size": 86, "upper": True,  "hi": "&H00E6FF&", "bar": "FFE600",
              "outline": 7, "shadow": 3, "outline_col": "&H00000000", "y": 1300},
    "clean": {"size": 64, "upper": False, "hi": "&HFFD28C&", "bar": "8CD2FF",
              "outline": 4, "shadow": 1, "outline_col": "&H00000000", "y": 1420},
    "neon":  {"size": 82, "upper": True,  "hi": "&H14FF39&", "bar": "39FF14",
              "outline": 8, "shadow": 0, "outline_col": "&H003D0A2B", "y": 1300},
    "fire":  {"size": 92, "upper": True,  "hi": "&H007AFF&", "bar": "FF7A00",
              "outline": 8, "shadow": 4, "outline_col": "&H00000000", "y": 1300},
}


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def probe(video):
    out = run(["ffprobe", "-v", "error", "-select_streams", "v:0",
               "-show_entries", "stream=width,height,r_frame_rate:format=duration",
               "-of", "json", video]).stdout
    data = json.loads(out)
    st = data["streams"][0]
    num, den = st["r_frame_rate"].split("/")
    return {"w": int(st["width"]), "h": int(st["height"]),
            "fps": float(num) / float(den or 1),
            "duration": float(data["format"]["duration"])}


def even(x):
    return int(x) // 2 * 2


# ---------- framing ----------------------------------------------------------
def find_face(video, start, end):
    """Sample frames; return (centre_x_fraction, hit_rate, face_height_fraction)."""
    try:
        import cv2
        import numpy as np
    except ImportError:
        return None, 0.0, 0.0
    cascade = None
    for xml in (os.path.join(getattr(getattr(cv2, "data", None), "haarcascades", ""),
                             "haarcascade_frontalface_default.xml"),
                os.path.join(HERE, "..", "assets",
                             "haarcascade_frontalface_default.xml")):
        if os.path.exists(xml):
            try:
                c = cv2.CascadeClassifier(xml)
                if not c.empty():
                    cascade = c
                    break
            except Exception:  # noqa: BLE001
                pass
    if cascade is None:
        return None, 0.0, 0.0
    cap = cv2.VideoCapture(video)
    n = 14
    xs, hs = [], []
    for i in range(n):
        cap.set(cv2.CAP_PROP_POS_MSEC, (start + (end - start) * (i + 0.5) / n) * 1000)
        ok, frame = cap.read()
        if not ok:
            continue
        H, W = frame.shape[:2]
        scale = 640 / W
        gray = cv2.cvtColor(cv2.resize(frame, (640, int(H * scale))),
                            cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, 1.1, 6, minSize=(36, 36))
        if len(faces):
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            xs.append((x + w / 2) / 640)
            hs.append(h / gray.shape[0])
    cap.release()
    if not xs:
        return None, 0.0, 0.0
    return float(np.median(xs)), len(xs) / n, float(np.median(hs))


def choose_layout(clip, video, start, end):
    layout = clip.get("layout", "auto")
    if layout == "split" and not clip.get("facecam"):
        layout = "blur"
    cx = None
    if layout in ("auto", "speaker"):
        cx, rate, size = find_face(video, start, end)
        if layout == "auto":
            layout = "speaker" if (rate >= 0.5 and size >= 0.12) else "blur"
        elif cx is None:
            cx = 0.5
    if layout == "center" and clip.get("focus_x") is not None:
        cx = min(max(float(clip["focus_x"]), 0.0), 1.0)
    return layout, cx


def video_chain(layout, cx, clip, W, H):
    """Return filter text turning [v0] into [vf] at 1080x1920."""
    if layout in ("speaker", "center"):
        cw = min(even(H * 9 / 16), W)
        x = even(min(max((cx if cx is not None else 0.5) * W - cw / 2, 0), W - cw))
        return (f"[v0]crop={cw}:{H}:{x}:0,scale={OUT_W}:{OUT_H}:"
                f"force_original_aspect_ratio=increase,crop={OUT_W}:{OUT_H}[vf]")
    if layout == "split":
        fx, fy, fw, fh = [even(v) for v in clip["facecam"]]
        fw, fh = min(fw, W - fx), min(fh, H - fy)
        bot_h = OUT_H - SPLIT_TOP
        gw = min(even(H * OUT_W / bot_h), W)
        return (f"[v0]split[a][b];"
                f"[a]crop={fw}:{fh}:{fx}:{fy},scale={OUT_W}:{SPLIT_TOP}:"
                f"force_original_aspect_ratio=increase,crop={OUT_W}:{SPLIT_TOP}[top];"
                f"[b]crop={gw}:{H}:{even((W - gw) / 2)}:0,"
                f"scale={OUT_W}:{bot_h}[bot];[top][bot]vstack[vf]")
    # blur: "zoom" > 1 enlarges the sharp picture and trims its sides
    zw = even(OUT_W * min(max(float(clip.get("zoom", 1.0)), 1.0), 2.5))
    return (f"[v0]split[a][b];"
            f"[a]scale=270:480:force_original_aspect_ratio=increase,"
            f"crop=270:480,boxblur=8:2,scale={OUT_W}:{OUT_H},eq=brightness=-0.08[bg];"
            f"[b]scale={zw}:-2,crop={OUT_W}:ih[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2[vf]")


# ---------- timing -----------------------------------------------------------
def keep_segments(words, dur, tighten, max_gap=0.7, pad=0.15):
    """Parts of the clip (clip-relative seconds) to keep."""
    if not tighten or len(words) < 4:
        return [(0.0, dur)]
    segs, a = [], 0.0
    prev_end = words[0]["s"]
    for w in words:
        if w["s"] - prev_end > max_gap:
            segs.append((a, min(prev_end + pad, dur)))
            a = max(w["s"] - pad, 0)
        prev_end = max(prev_end, w["e"])
    segs.append((a, dur))
    segs = [(round(s, 3), round(e, 3)) for s, e in segs if e - s > 0.2]
    return segs or [(0.0, dur)]


def remap(t, segs):
    acc = 0.0
    for s, e in segs:
        if t < s:
            return acc
        if t <= e:
            return acc + (t - s)
        acc += e - s
    return acc


# ---------- captions ---------------------------------------------------------
def ass_time(t):
    t = max(t, 0)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def clean(text):
    return re.sub(r"[{}\\\r\n]", " ", text).strip()


def is_malayalam(text):
    return any("ഀ" <= ch <= "ൿ" for ch in text)


def balanced_wrap(text, width, max_lines=3):
    """Wrap like textwrap, then narrow the width until the lines are even, so
    a headline never ends with one short word alone on the last line."""
    lines = textwrap.wrap(text, width=width)
    if len(lines) < 2:
        return lines
    n = len(lines)
    for w in range(max(len(text) // n, 6), width + 1):
        trial = textwrap.wrap(text, width=w)
        if len(trial) <= n:
            return trial[:max_lines]
    return lines[:max_lines]


def build_ass(words, hook, layout, total, path, style="bold", watermark=None):
    st = STYLES.get(style, STYLES["bold"])
    text_all = " ".join(w["w"] for w in words) + " " + (hook or "")
    ml = is_malayalam(text_all)
    font = "Noto Sans Malayalam" if ml else "Poppins ExtraBold"
    size = round(st["size"] * 0.81) if ml else st["size"]
    cap_y = SPLIT_TOP if layout == "split" else st["y"]
    hook_y = 120 if layout == "split" else 250
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {OUT_W}
PlayResY: {OUT_H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{font},{size},&H00FFFFFF,&H00FFFFFF,{st["outline_col"]},&H96000000,{-1 if ml else 0},0,0,0,100,100,0,0,1,{st["outline"]},{st["shadow"]},5,60,60,60,1
Style: Mark,Poppins ExtraBold,38,&H59FFFFFF,&H59FFFFFF,&H59000000,&H96000000,0,0,0,0,100,100,1,0,1,3,0,5,60,60,60,1
Style: Hook,{font},{58 if ml else 64},&H00101010,&H00101010,&H00FFFFFF,&H00FFFFFF,{-1 if ml else 0},0,0,0,100,100,0,0,3,16,0,5,60,60,60,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    if hook:
        wrapped = balanced_wrap(clean(hook), 20 if ml else 24)
        for i, ln in enumerate(wrapped):
            y = hook_y + i * (112 if ml else 104)
            lines.append(f"Dialogue: 1,{ass_time(0)},{ass_time(min(3.5, total))},"
                         f"Hook,,0,0,0,,{{\\pos({OUT_W // 2},{y})}}{ln}")

    if watermark:
        lines.append(f"Dialogue: 0,{ass_time(0)},{ass_time(total)},Mark,,0,0,0,,"
                     f"{{\\pos({OUT_W // 2},1560)}}{clean(str(watermark))}")

    # Group words into short chunks; show the chunk, light up the spoken word.
    chunks, cur = [], []
    limit = 14 if ml else 16
    for w in words:
        tok = clean(w["w"])
        if not tok:
            continue
        w = {**w, "w": tok.upper() if (st["upper"] and not ml) else tok}
        length = sum(len(x["w"]) + 1 for x in cur) + len(tok)
        if cur and (len(cur) >= 3 or length > limit or w["s"] - cur[-1]["e"] > 0.6):
            chunks.append(cur)
            cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    for ci, chunk in enumerate(chunks):
        next_start = chunks[ci + 1][0]["s"] if ci + 1 < len(chunks) else total
        chunk_end = min(chunk[-1]["e"] + 0.25, next_start, total)
        for i, w in enumerate(chunk):
            s = w["s"]
            e = chunk[i + 1]["s"] if i + 1 < len(chunk) else chunk_end
            if e - s < 0.02:
                continue
            parts = []
            for j, x in enumerate(chunk):
                parts.append(f"{{\\c{st['hi']}}}{x['w']}{{\\c&HFFFFFF&}}"
                             if j == i else x["w"])
            lines.append(f"Dialogue: 0,{ass_time(s)},{ass_time(e)},Cap,,0,0,0,,"
                         f"{{\\pos({OUT_W // 2},{cap_y})}}" + " ".join(parts))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(head + "\n".join(lines) + "\n")
    return len(chunks)


# ---------- render one clip --------------------------------------------------
def render_clip(video, info, clip, all_words, outdir, workdir, opts=None):
    opts = opts or {}
    start = max(float(clip["start"]), 0)
    end = min(float(clip["end"]), info["duration"])
    dur = end - start
    if dur < 3:
        return {"id": clip.get("id"), "ok": False, "error": "clip shorter than 3 s"}

    words = [{"s": w["s"] - start, "e": min(w["e"], end) - start, "w": w["w"]}
             for w in all_words if w["s"] >= start - 0.05 and w["s"] < end - 0.1]
    segs = keep_segments(words, dur, clip.get("tighten", False))
    total = sum(e - s for s, e in segs)
    words = [{"s": remap(w["s"], segs), "e": remap(w["e"], segs), "w": w["w"]}
             for w in words]

    layout, cx = choose_layout(clip, video, start, end)
    cid = int(clip.get("id", 0))
    slug = re.sub(r"[^a-z0-9]+", "-", str(clip.get("slug") or clip.get("hook")
                                           or "clip").lower()).strip("-")[:40]
    preview = bool(opts.get("preview"))
    out_name = (f"short_{cid:02d}_{slug or 'clip'}"
                f"{'_preview' if preview else ''}.mp4")
    style = clip.get("style") or opts.get("style") or "bold"
    if style not in STYLES:
        style = "bold"
    watermark = clip.get("watermark", opts.get("watermark"))
    progress = clip.get("progress", opts.get("progress", False))
    out_path = os.path.abspath(os.path.join(outdir, out_name))

    # ffmpeg runs inside workdir with relative names, so Windows drive letters
    # never appear inside the filter string (the ':' would break it).
    ass_name = f"clip_{cid:02d}.ass"
    show_caps = clip.get("captions", True) and words
    n_chunks = build_ass(words if show_caps else [], clip.get("hook"), layout,
                         total, os.path.join(workdir, ass_name), style,
                         watermark)

    parts = []
    if len(segs) > 1:
        sel = "+".join(f"between(t,{s},{e})" for s, e in segs)
        parts.append(f"[0:v]select='{sel}',setpts=N/FRAME_RATE/TB[v0]")
        parts.append(f"[0:a]aselect='{sel}',asetpts=N/SR/TB[a0]")
    else:
        parts.append("[0:v]setpts=PTS-STARTPTS[v0]")
        parts.append("[0:a]asetpts=PTS-STARTPTS[a0]")
    parts.append(video_chain(layout, cx, clip, info["w"], info["h"]))
    fps = min(round(info["fps"]), 60) or 30
    tail = f"fps={fps},format=yuv420p"
    if preview:
        tail = f"scale={OUT_W // 2}:{OUT_H // 2}," + tail
    if progress:
        # A bar as wide as the frame slides in from the left edge.
        parts.append(f"[vf]ass={ass_name}:fontsdir=fonts[vc]")
        parts.append(f"color=c=0x{STYLES[style]['bar']}:s={OUT_W}x12:r={fps}:"
                     f"d={total + 1:.2f}[bar]")
        parts.append(f"[vc][bar]overlay=x='-w+w*t/{total:.3f}':y=0:shortest=1,"
                     f"{tail}[vout]")
    else:
        parts.append(f"[vf]ass={ass_name}:fontsdir=fonts,{tail}[vout]")
    parts.append("[a0]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]")

    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start:.3f}",
           "-t", f"{dur:.3f}", "-i", os.path.abspath(video),
           "-filter_complex", ";".join(parts),
           "-map", "[vout]", "-map", "[aout]",
           "-c:v", "libx264", "-preset", "ultrafast" if preview else "veryfast",
           "-crf", "28" if preview else "20",
           "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out_path]
    res = run(cmd, cwd=workdir)
    ok = res.returncode == 0 and os.path.exists(out_path)
    return {"id": cid, "ok": ok, "file": out_path if ok else None,
            "layout": layout, "style": style, "seconds": round(total, 1),
            "silence_cut": round(dur - total, 1), "caption_chunks": n_chunks,
            "error": None if ok else res.stderr[-600:]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--clips", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--transcript")
    ap.add_argument("--only", help="comma-separated clip ids")
    ap.add_argument("--style", choices=sorted(STYLES), default="bold")
    ap.add_argument("--watermark", help='channel tag on every clip, e.g. "@name"')
    ap.add_argument("--progress", action="store_true",
                    help="thin progress bar along the top edge")
    ap.add_argument("--preview", action="store_true",
                    help="fast 540x960 drafts (*_preview.mp4)")
    args = ap.parse_args()
    opts = {"style": args.style, "watermark": args.watermark,
            "progress": args.progress, "preview": args.preview}

    with open(args.clips, encoding="utf-8") as fh:
        clips = json.load(fh)["clips"]
    if args.only:
        wanted = {int(x) for x in args.only.split(",")}
        clips = [c for c in clips if int(c.get("id", 0)) in wanted]
    words = []
    tpath = args.transcript or os.path.join(os.path.dirname(args.clips),
                                            "transcript.json")
    if os.path.exists(tpath):
        with open(tpath, encoding="utf-8") as fh:
            words = json.load(fh)["words"]

    os.makedirs(args.out, exist_ok=True)
    workdir = os.path.abspath(os.path.join(args.out, "_work"))
    os.makedirs(os.path.join(workdir, "fonts"), exist_ok=True)
    for f in os.listdir(FONTS):
        if f.lower().endswith((".ttf", ".otf")):
            shutil.copy(os.path.join(FONTS, f), os.path.join(workdir, "fonts", f))

    info = probe(args.video)
    results = []
    for clip in clips:
        r = render_clip(args.video, info, clip, words, args.out, workdir, opts)
        results.append(r)
        print(json.dumps(r, ensure_ascii=False), flush=True)
    with open(os.path.join(args.out, "render_report.json"), "w",
              encoding="utf-8") as fh:
        json.dump(results, fh, indent=1, ensure_ascii=False)
    sys.exit(0 if all(r["ok"] for r in results) else 1)


if __name__ == "__main__":
    main()
