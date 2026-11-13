#!/usr/bin/env python3
"""Render approved clips as edited 1080x1920 vertical Shorts.

Usage:
  python render.py VIDEO --clips WORKDIR/clips.json --out OUTDIR
                   [--transcript WORKDIR/transcript.json] [--only 1,3]
                   [--edit premium|hype|story|clean|raw]
                   [--style bold|clean|neon|fire] [--watermark "@handle"]
                   [--outro "FOLLOW FOR MORE"] [--progress] [--preview]

Command-line options set the default for every clip; a clip can override each
with its own key. --preview renders small, fast drafts (540x960,
*_preview.mp4) for checking framing and timing before the full render.

clips.json:
{"clips": [{
   "id": 1, "start": 754.2, "end": 791.0,     # seconds in the source video
   "hook": "He quit a *40 lakh* job",  # headline; *stars* mark the accent words
   "hook_hold": false,    # true keeps the headline up for the whole clip
   "hook_y": 340,         # headline height (px from top) if the default
                          #   spot covers something that matters
   "slug": "quit-job",    # optional file-name part
   "layout": "auto",      # auto | speaker | center | blur | split | stack
   "focus_x": 0.5,        # center: 0 = left edge, 1 = right edge
   "focus_path": [[754.2, 0.3], [760.0, 0.7]],  # speaker/center: follow a
   "focus_mode": "cut",   #   subject over time; "cut" jumps, "pan" glides
   "zoom": 1.4,           # blur: enlarge the sharp picture, trimming sides
   "facecam": [1500, 20, 400, 300],   # split: x,y,w,h in source pixels
   "faces": [[0.27, 0.4], [0.74, 0.42]],  # stack: centre of each face (0-1)
   "tighten": true,       # cut silences > 0.7 s (talk clips; needs transcript)
   "zoomcuts": false,     # turn off story's zoom cuts when the source
                          #   already cuts between cameras every few seconds
   "captions": true,
   "edit": "premium",     # the editing treatment, see below
   "beats": [             # key moments; "auto" finds them from the sound
     "auto",              #   (in a list: the found ones plus your own)
     {"t": 771.5, "fx": ["punch", "shake"], "text": "SQUAD WIPE"},
     {"t": 780.0, "fx": "slowmo", "len": 1.2}],
   "grade": "punchy",     # soft | punchy | vivid | none
   "style": "bold",       # caption look: bold | clean | neon | fire
   "outro": "FOLLOW FOR MORE",   # tag over the last 1.6 s
   "watermark": "@handle",
   "progress": true
}]}

Edits (what an editor would do by hand, as one word)
  premium  colour grade, slow push-in, punch-in zoom with a soft thump on the
           loudest moments, animated headline and captions  (default)
  hype     gameplay and sports: stronger grade, punch + shake + flash on the
           beats, big condensed headline, progress bar
  story    talk: zoom cuts on sentence changes, soft grade, animated captions
  clean    soft grade and animated text, no zooms or sound effects
  raw      no treatment: plain cut, boxed headline, static captions

Beat effects: punch (zoom hit), shake, flash, slowmo (half speed for "len"
seconds). "text" adds a callout word that pops on screen at that moment.

Text stays inside the area the Shorts, Reels and TikTok buttons leave free:
roughly x 60-890 and y 290-1250 of the 1080x1920 frame.
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
sys.path.insert(0, HERE)
FONTS = os.path.join(HERE, "..", "assets", "fonts")
OUT_W, OUT_H = 1080, 1920
SPLIT_TOP = 608            # facecam band height in the split layout
STACK_H = OUT_H // 2       # each speaker's cell in the stack layout
HOOK_Y, CALL_Y, OUTRO_Y, MARK_Y = 340, 660, 980, 1242
HOOK_SECONDS = 3.5
NOT_SPEECH = re.compile(r"^(>+|\[[^\]]*\]?|[^\[\]]*\]|[\W_]*)$")

# Caption looks. Colours are ASS order (&HBBGGRR&); "bar" is the same accent
# as RRGGBB for the progress bar.
STYLES = {
    "bold":  {"size": 80, "upper": True,  "hi": "&H00E6FF&", "bar": "FFE600",
              "outline": 7, "shadow": 3, "outline_col": "&H00000000", "y": 1150},
    "clean": {"size": 62, "upper": False, "hi": "&HFFD28C&", "bar": "8CD2FF",
              "outline": 4, "shadow": 1, "outline_col": "&H00000000", "y": 1180},
    "neon":  {"size": 78, "upper": True,  "hi": "&H14FF39&", "bar": "39FF14",
              "outline": 8, "shadow": 0, "outline_col": "&H003D0A2B", "y": 1150},
    "fire":  {"size": 86, "upper": True,  "hi": "&H007AFF&", "bar": "FF7A00",
              "outline": 8, "shadow": 4, "outline_col": "&H00000000", "y": 1150},
}

GRADES = {
    "soft":   "eq=contrast=1.04:saturation=1.08,unsharp=5:5:0.35",
    "punchy": "eq=contrast=1.08:saturation=1.20:brightness=0.01,unsharp=5:5:0.6",
    "vivid":  "eq=contrast=1.12:saturation=1.32:brightness=0.015,"
              "unsharp=5:5:0.8,vignette=PI/5.5",
}

# title: box = plain white label, bold = big outlined text, impact = condensed caps
EDITS = {
    "raw":     {"grade": None, "push": 0.0, "beats": None, "fx": (),
                "sfx": 0.0, "anim": False, "title": "box", "zoomcuts": False,
                "punch": 0.0, "progress": False},
    "clean":   {"grade": "soft", "push": 0.0, "beats": None, "fx": (),
                "sfx": 0.0, "anim": True, "title": "bold", "zoomcuts": False,
                "punch": 0.0, "progress": False},
    "premium": {"grade": "punchy", "push": 0.05, "beats": "auto",
                "fx": ("punch",), "sfx": 0.40, "anim": True, "title": "bold",
                "zoomcuts": False, "punch": 0.11, "progress": False},
    "hype":    {"grade": "vivid", "push": 0.06, "beats": "auto",
                "fx": ("punch", "shake", "flash"), "sfx": 0.65, "anim": True,
                "title": "impact", "zoomcuts": False, "punch": 0.16,
                "progress": True},
    "story":   {"grade": "soft", "push": 0.0, "beats": None, "fx": ("punch",),
                "sfx": 0.30, "anim": True, "title": "bold", "zoomcuts": True,
                "punch": 0.10, "progress": False},
}
TITLES = {  # font, size, characters per line, upper case
    "box":    ("Poppins ExtraBold", 64, 24, False),
    "bold":   ("Poppins ExtraBold", 82, 17, False),
    "impact": ("Anton", 122, 18, True),
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


def clamp(v, lo, hi):
    return min(max(v, lo), hi)


# ---------- framing ----------------------------------------------------------
def find_faces(video, start, end, n=14):
    """Sample frames; return the faces seen in at least a third of them, each
    as {cx, cy, h, rate} in 0-1 fractions, most prominent first."""
    try:
        import cv2
        import numpy as np
        import faces as facelib
    except ImportError:
        return []
    cap = cv2.VideoCapture(video)
    tracks = []
    for i in range(n):
        cap.set(cv2.CAP_PROP_POS_MSEC, (start + (end - start) * (i + 0.5) / n) * 1000)
        ok, frame = cap.read()
        if not ok:
            continue
        H, W = frame.shape[:2]
        for f in facelib.detect(frame)[:4]:
            if f["h"] / H < 0.07:
                continue
            cx, cy = (f["x"] + f["w"] / 2) / W, (f["y"] + f["h"] / 2) / H
            for tr in tracks:
                if abs(np.median(tr["cx"]) - cx) < 0.12:
                    break
            else:
                tr = {"cx": [], "cy": [], "h": []}
                tracks.append(tr)
            tr["cx"].append(cx)
            tr["cy"].append(cy)
            tr["h"].append(f["h"] / H)
    cap.release()
    out = [{"cx": float(np.median(t["cx"])), "cy": float(np.median(t["cy"])),
            "h": float(np.median(t["h"])), "rate": len(t["cx"]) / n}
           for t in tracks if len(t["cx"]) / n >= 0.33]
    out.sort(key=lambda t: -t["rate"] * t["h"])
    return out


def choose_layout(clip, video, start, end):
    """Return (layout, centre x fraction or None, two face centres or None)."""
    layout = clip.get("layout", "auto")
    if layout == "split" and not clip.get("facecam"):
        layout = "blur"
    cx, pair = None, None
    if layout == "stack":
        pair = clip.get("faces")
        if not pair or len(pair) < 2:
            found = sorted(find_faces(video, start, end)[:2], key=lambda f: f["cx"])
            pair = [[f["cx"], f["cy"]] for f in found]
        if len(pair) < 2:
            layout, pair = "blur", None
    if layout in ("auto", "speaker"):
        found = find_faces(video, start, end)
        best = found[0] if found else None
        if layout == "auto":
            layout = "speaker" if (best and best["rate"] >= 0.5
                                   and best["h"] >= 0.12) else "blur"
        cx = best["cx"] if best else 0.5
    if layout == "center" and clip.get("focus_x") is not None:
        cx = clamp(float(clip["focus_x"]), 0.0, 1.0)
    return layout, cx, pair


def path_expr(points, mode, W, cw):
    """ffmpeg expression for the crop's left edge following [[t, cx], ...]
    (t in output seconds). "cut" holds each position until the next point."""
    pts = [(max(float(t), 0.0), clamp(float(c) * W - cw / 2, 0, W - cw))
           for t, c in points][:60]
    if not pts:
        return None
    if len(pts) == 1:
        return str(even(pts[0][1]))
    terms = []
    for i, (t, x) in enumerate(pts):
        a = 0.0 if i == 0 else t
        if i + 1 == len(pts):
            terms.append(f"gte(t,{a:.2f})*{x:.0f}")
            continue
        b, x1 = pts[i + 1]
        gate = f"gte(t,{a:.2f})*lt(t,{b:.2f})"
        if mode == "pan":
            terms.append(f"{gate}*({x:.0f}+({x1 - x:.0f})*(t-{a:.2f})/"
                         f"{max(b - a, 0.05):.2f})")
        else:
            terms.append(f"{gate}*{x:.0f}")
    return "+".join(terms)


def video_chain(layout, cx, pair, clip, W, H, follow=None):
    """Return filter text turning [v0] into [vl] at 1080x1920."""
    if layout in ("speaker", "center"):
        cw = min(even(H * 9 / 16), W)
        x = even(clamp((cx if cx is not None else 0.5) * W - cw / 2, 0, W - cw))
        xe = path_expr(follow, clip.get("focus_mode", "cut"), W, cw) if follow else None
        return (f"[v0]crop={cw}:{H}:'{xe or x}':0,scale={OUT_W}:{OUT_H}:"
                f"force_original_aspect_ratio=increase,crop={OUT_W}:{OUT_H}[vl]")
    if layout == "split":
        fx, fy, fw, fh = [even(v) for v in clip["facecam"]]
        fw, fh = min(fw, W - fx), min(fh, H - fy)
        bot_h = OUT_H - SPLIT_TOP
        gw = min(even(H * OUT_W / bot_h), W)
        return (f"[v0]split[a][b];"
                f"[a]crop={fw}:{fh}:{fx}:{fy},scale={OUT_W}:{SPLIT_TOP}:"
                f"force_original_aspect_ratio=increase,crop={OUT_W}:{SPLIT_TOP}[top];"
                f"[b]crop={gw}:{H}:{even((W - gw) / 2)}:0,"
                f"scale={OUT_W}:{bot_h}[bot];[top][bot]vstack[vl]")
    if layout == "stack":
        # Two speakers, one above the other, each in a 1080x960 cell.
        ch = even(H * clamp(float(clip.get("stack_crop", 0.8)), 0.3, 1.0))
        cw = min(even(ch * OUT_W / STACK_H), W)
        ch = even(cw * STACK_H / OUT_W)
        cells = []
        for (fx, fy), tag in zip(pair[:2], ("p", "q")):
            x = even(clamp(float(fx) * W - cw / 2, 0, W - cw))
            y = even(clamp(float(fy) * H - ch * 0.42, 0, H - ch))
            cells.append(f"[{tag}]crop={cw}:{ch}:{x}:{y},"
                         f"scale={OUT_W}:{STACK_H}[{tag}o]")
        return (f"[v0]split[p][q];{cells[0]};{cells[1]};"
                f"[po][qo]vstack,drawbox=x=0:y={STACK_H - 3}:w={OUT_W}:h=6:"
                f"color=white@0.9:t=fill[vl]")
    # blur: "zoom" > 1 enlarges the sharp picture and trims its sides
    zw = even(OUT_W * clamp(float(clip.get("zoom", 1.0)), 1.0, 2.5))
    return (f"[v0]split[a][b];"
            f"[a]scale=270:480:force_original_aspect_ratio=increase,"
            f"crop=270:480,boxblur=12:3,scale={OUT_W}:{OUT_H},"
            f"eq=brightness=-0.20:saturation=1.15[bg];"
            f"[b]scale={zw}:-2,crop={OUT_W}:ih,"
            f"pad=iw:ih+8:0:4:color=white[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2[vl]")


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


def build_pieces(segs, slow):
    """Kept segments plus slow-motion spans -> [(start, end, speed)]."""
    out = []
    for s, e in segs:
        cur = s
        for a, b, sp in sorted(slow):
            a2, b2 = max(a, s), min(b, e)
            if b2 - a2 < 0.1 or a2 < cur:
                continue
            if a2 - cur > 0.02:
                out.append((cur, a2, 1.0))
            out.append((a2, b2, sp))
            cur = b2
        if e - cur > 0.02:
            out.append((cur, e, 1.0))
    return out


def remap(t, pieces):
    """Clip-relative source time -> time in the rendered clip."""
    acc = 0.0
    for s, e, sp in pieces:
        if t < s:
            return acc
        if t <= e:
            return acc + (t - s) / sp
        acc += (e - s) / sp
    return acc


def auto_beats(video, start, dur):
    """The moments where the sound jumps hardest (a shot, a shout, a laugh),
    as clip-relative seconds. At most one per ~7 s, none under the headline."""
    try:
        import numpy as np
    except ImportError:
        return []
    raw = subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-ss", f"{start:.3f}", "-t", f"{dur:.3f}",
         "-i", video, "-vn", "-ac", "1", "-ar", "8000", "-f", "s16le", "-"],
        capture_output=True).stdout
    pcm = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
    n = 800                                       # 0.1 s windows
    if len(pcm) < n * 30:
        return []
    fr = pcm[:len(pcm) // n * n].reshape(-1, n)
    db = 20 * np.log10(np.sqrt((fr ** 2).mean(axis=1)) + 1e-6)
    rise = np.array([db[i] - db[max(0, i - 10):i].mean() if i else 0.0
                     for i in range(len(db))])
    picked = []
    for i in np.argsort(-rise):
        t = i * 0.1
        if rise[i] < 6 or len(picked) >= min(4, int(dur / 7) + 1):
            break
        if t < 3.0 or t > dur - 1.2 or any(abs(t - p) < 5 for p in picked):
            continue
        picked.append(round(float(t), 2))
    return sorted(picked)


def sentence_cuts(words, total, min_len=2.6):
    """Spans (output seconds) to show slightly zoomed in, alternating with
    normal framing at sentence changes: the classic talking-head zoom cut."""
    if not words:
        return []
    starts = [0.0]
    for prev, w in zip(words, words[1:]):
        ended = prev["w"].rstrip().endswith((".", "?", "!"))
        if (ended or w["s"] - prev["e"] > 0.45) and w["s"] - starts[-1] >= min_len:
            starts.append(w["s"])
    if len(starts) < 2:
        return []
    starts.append(total)
    return [(round(a, 2), round(b, 2))
            for i, (a, b) in enumerate(zip(starts, starts[1:])) if i % 2 == 1]


# ---------- text -------------------------------------------------------------
def ass_time(t):
    t = max(t, 0)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def clean(text):
    return re.sub(r"[{}\\\r\n]", " ", str(text)).strip()


def is_malayalam(text):
    return any("ഀ" <= ch <= "ൿ" for ch in text)


def balanced_wrap(text, width, max_lines=3):
    """Wrap like textwrap, then narrow the width until the lines are even, so
    a headline never ends with one short word alone on the last line."""
    kw = {"break_long_words": False, "break_on_hyphens": False}
    lines = textwrap.wrap(text, width=width, **kw)
    if len(lines) < 2:
        return lines
    n = len(lines)
    for w in range(max(len(text) // n, 6), width + 1):
        trial = textwrap.wrap(text, width=w, **kw)
        if len(trial) <= n:
            return trial[:max_lines]
    return lines[:max_lines]


def hook_lines(hook, width, upper):
    """Headline -> lines of (word, is_accent). *Stars* mark accent words."""
    toks = []
    for i, seg in enumerate(clean(hook).split("*")):
        for w in seg.split():
            toks.append((w.upper() if upper else w, i % 2 == 1))
    lines, k = [], 0
    for ln in balanced_wrap(" ".join(w for w, _ in toks), width):
        n = len(ln.split())
        lines.append(toks[k:k + n])
        k += n
    return lines


POP = (r"\fscx72\fscy72\t(0,150,\fscx108\fscy108)"
       r"\t(150,240,\fscx100\fscy100)")


def build_ass(path, words, hook, layout, total, style, edit, watermark=None,
              beats=(), outro=None, hook_hold=False, hook_pos=None):
    st = STYLES.get(style, STYLES["bold"])
    text_all = " ".join(w["w"] for w in words) + " " + (hook or "")
    ml = is_malayalam(text_all)
    cap_font = "Noto Sans Malayalam" if ml else "Poppins ExtraBold"
    size = round(st["size"] * 0.81) if ml else st["size"]
    cap_y = {"split": SPLIT_TOP, "stack": STACK_H}.get(layout, st["y"])
    hook_y = 120 if layout == "split" else HOOK_Y
    if hook_pos is not None:
        hook_y = int(clamp(float(hook_pos), 100, 1500))
    t_font, t_size, t_width, t_upper = TITLES[edit["title"]]
    if ml:
        t_font, t_size, t_width, t_upper = "Noto Sans Malayalam", 62, 18, False
    accent = "&H00" + st["hi"][2:-1]             # style colour form
    bold = -1 if ml else 0
    boxed = edit["title"] == "box"
    if boxed:
        hook_style = (f"Style: Hook,{t_font},{58 if ml else 64},&H00101010,"
                      f"&H00101010,&H00FFFFFF,&H00FFFFFF,{bold},0,0,0,100,100,"
                      f"0,0,3,16,0,5,60,60,60,1")
    else:
        hook_style = (f"Style: Hook,{t_font},{t_size},&H00FFFFFF,&H00FFFFFF,"
                      f"&H00000000,&H78000000,{bold},0,0,0,100,100,"
                      f"{1 if edit['title'] == 'impact' else 0},0,1,9,5,5,"
                      f"60,60,60,1")
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {OUT_W}
PlayResY: {OUT_H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{cap_font},{size},&H00FFFFFF,&H00FFFFFF,{st["outline_col"]},&H96000000,{bold},0,0,0,100,100,0,0,1,{st["outline"]},{st["shadow"]},5,60,60,60,1
{hook_style}
Style: Call,{t_font},{round(t_size * 1.12)},{accent},{accent},&H00000000,&H78000000,{bold},0,0,0,100,100,1,-4,1,9,5,5,60,60,60,1
Style: Outro,{t_font},{round(t_size * 0.8)},&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,{bold},0,0,0,100,100,1,0,1,8,4,5,60,60,60,1
Style: Mark,Poppins ExtraBold,38,&H59FFFFFF,&H59FFFFFF,&H59000000,&H96000000,0,0,0,0,100,100,1,0,1,3,0,5,60,60,60,1
Style: Flash,Arial,20,&H00FFFFFF,&H00FFFFFF,&H00FFFFFF,&H00FFFFFF,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    cx = OUT_W // 2
    anim = edit["anim"]

    if hook:
        hold = total if hook_hold else min(HOOK_SECONDS, total)
        rows = hook_lines(hook, 20 if (ml and boxed) else t_width, t_upper)
        if boxed:
            step = 112 if ml else 104
        else:
            step = round(t_size * (1.6 if ml else 1.22))
        for i, row in enumerate(rows):
            y = hook_y + i * step
            if boxed:
                text = " ".join(w for w, _ in row)
                tags = f"\\pos({cx},{y})"
            else:
                text = " ".join(f"{{\\c{st['hi']}}}{w}{{\\c&HFFFFFF&}}" if em else w
                                for w, em in row)
                tags = f"\\pos({cx},{y})\\fad(0,220)" + (POP if anim else "")
            s = i * 0.07 if anim else 0
            lines.append(f"Dialogue: 2,{ass_time(s)},{ass_time(hold)},Hook,,"
                         f"0,0,0,,{{{tags}}}{text}")

    for b in beats:
        t = b["out"]
        if "flash" in b["fx"]:
            lines.append(f"Dialogue: 5,{ass_time(t)},{ass_time(t + 0.26)},Flash,,"
                         f"0,0,0,,{{\\pos(0,0)\\1a&H78&\\fad(0,230)\\p1}}"
                         f"m 0 0 l {OUT_W} 0 {OUT_W} {OUT_H} 0 {OUT_H}{{\\p0}}")
        if b.get("text"):
            word = clean(b["text"])
            word = word if ml else word.upper()
            lines.append(f"Dialogue: 3,{ass_time(t)},{ass_time(min(t + 1.2, total))},"
                         f"Call,,0,0,0,,{{\\pos({cx},{CALL_Y})\\fad(0,200){POP}}}{word}")

    if outro and total > 6:
        lines.append(f"Dialogue: 3,{ass_time(total - 1.6)},{ass_time(total)},Outro,,"
                     f"0,0,0,,{{\\pos({cx},{OUTRO_Y}){POP}}}"
                     f"{clean(outro) if ml else clean(outro).upper()}")

    if watermark:
        lines.append(f"Dialogue: 0,{ass_time(0)},{ass_time(total)},Mark,,0,0,0,,"
                     f"{{\\pos({cx},{MARK_Y})}}{clean(watermark)}")

    # Group words into short chunks; show the chunk, light up the spoken word.
    chunks, cur = [], []
    limit = 12 if ml else 13
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
    grow = r"\fscx114\fscy114\t(0,110,\fscx100\fscy100)" if anim else ""
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
                parts.append(f"{{\\c{st['hi']}{grow}}}{x['w']}"
                             f"{{\\c&HFFFFFF&\\fscx100\\fscy100}}"
                             if j == i else x["w"])
            lines.append(f"Dialogue: 1,{ass_time(s)},{ass_time(e)},Cap,,0,0,0,,"
                         f"{{\\pos({cx},{cap_y})}}" + " ".join(parts))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(head + "\n".join(lines) + "\n")
    return len(chunks)


# ---------- render one clip --------------------------------------------------
def normalise_beats(spec, edit, video, start, dur):
    """-> [{"t": clip-relative source seconds, "fx": [...], "text", "len"}]."""
    if spec == "auto":
        return [{"t": t, "fx": list(edit["fx"]), "len": 1.0}
                for t in auto_beats(video, start, dur)]
    out = []
    spec = list(spec or [])
    want_auto = "auto" in spec
    for b in [b for b in spec if isinstance(b, dict)]:
        t = float(b.get("t", 0))
        if start <= t <= start + dur:               # given in source time
            t -= start
        if not 0 <= t < dur:
            continue
        fx = b.get("fx") or list(edit["fx"]) or ["punch"]
        fx = [fx] if isinstance(fx, str) else list(fx)
        out.append({"t": t, "fx": fx, "text": b.get("text"),
                    "len": float(b.get("len", 1.0))})
    if want_auto:                       # ["auto", {...}]: found beats plus yours
        for t in auto_beats(video, start, dur):
            if all(abs(t - b["t"]) > 1.5 for b in out):
                out.append({"t": t, "fx": list(edit["fx"]), "len": 1.0})
    return sorted(out, key=lambda b: b["t"])


def render_clip(video, info, clip, all_words, outdir, workdir, opts=None, sfx=None):
    opts = opts or {}
    start = max(float(clip["start"]), 0)
    end = min(float(clip["end"]), info["duration"])
    dur = end - start
    if dur < 3:
        return {"id": clip.get("id"), "ok": False, "error": "clip shorter than 3 s"}

    edit_name = clip.get("edit") or opts.get("edit") or "premium"
    if edit_name not in EDITS:
        edit_name = "premium"
    edit = EDITS[edit_name]
    style = clip.get("style") or opts.get("style") or "bold"
    if style not in STYLES:
        style = "bold"
    watermark = clip.get("watermark", opts.get("watermark"))
    outro = clip.get("outro", opts.get("outro"))
    progress = clip.get("progress", opts.get("progress") or edit["progress"])
    preview = bool(opts.get("preview"))
    grade = clip.get("grade", edit["grade"])
    grade = None if grade in (None, "none") else grade

    # YouTube subtitles carry speaker-change marks (>>) and sound tags
    # ([laughter], [music]); neither belongs in a caption.
    words = [{"s": w["s"] - start, "e": min(w["e"], end) - start, "w": w["w"]}
             for w in all_words if w["s"] >= start - 0.05 and w["s"] < end - 0.1
             and not NOT_SPEECH.match(w["w"].strip())]
    beats = normalise_beats(clip.get("beats", edit["beats"]), edit, video, start, dur)
    slow = [(max(b["t"] - 0.1, 0),
             min(b["t"] - 0.1 + clamp(b["len"], 0.3, 3), dur), 0.5)
            for b in beats if "slowmo" in b["fx"]]
    pieces = build_pieces(keep_segments(words, dur, clip.get("tighten", False)), slow)
    total = sum((e - s) / sp for s, e, sp in pieces)
    words = [{"s": remap(w["s"], pieces), "e": remap(w["e"], pieces), "w": w["w"]}
             for w in words]
    for b in beats:
        b["out"] = round(remap(b["t"], pieces), 2)

    layout, cx, pair = choose_layout(clip, video, start, end)
    follow = None
    if clip.get("focus_path") and layout in ("speaker", "center"):
        follow = [[remap(clamp(float(t) - start, 0, dur), pieces), c]
                  for t, c in clip["focus_path"] if float(t) <= end]
    cid = int(clip.get("id", 0))
    slug = re.sub(r"[^a-z0-9]+", "-", str(clip.get("slug") or clip.get("hook")
                                           or "clip").lower()).strip("-")[:40]
    out_name = (f"short_{cid:02d}_{slug or 'clip'}"
                f"{'_preview' if preview else ''}.mp4")
    out_path = os.path.abspath(os.path.join(outdir, out_name))

    # ffmpeg runs inside workdir with relative names, so Windows drive letters
    # never appear inside the filter string (the ':' would break it).
    ass_name = f"clip_{cid:02d}.ass"
    show_caps = clip.get("captions", True) and words
    n_chunks = build_ass(os.path.join(workdir, ass_name),
                         words if show_caps else [], clip.get("hook"), layout,
                         total, style, edit, watermark, beats, outro,
                         bool(clip.get("hook_hold")), clip.get("hook_y"))

    fps = min(round(info["fps"]), 60) or 30
    parts = []
    whole = len(pieces) == 1 and pieces[0][2] == 1.0 and \
        pieces[0][0] < 0.01 and dur - pieces[0][1] < 0.01
    if whole:
        parts.append("[0:v]setpts=PTS-STARTPTS[v0]")
        parts.append("[0:a]asetpts=PTS-STARTPTS[a0]")
    else:
        n = len(pieces)
        parts.append(f"[0:v]split={n}" + "".join(f"[vs{i}]" for i in range(n)))
        parts.append(f"[0:a]asplit={n}" + "".join(f"[as{i}]" for i in range(n)))
        for i, (s, e, sp) in enumerate(pieces):
            parts.append(f"[vs{i}]trim=start={s:.3f}:end={e:.3f},"
                         f"setpts=(PTS-STARTPTS)/{sp}[vp{i}]")
            parts.append(f"[as{i}]atrim=start={s:.3f}:end={e:.3f},"
                         f"asetpts=PTS-STARTPTS"
                         + (f",atempo={sp}" if sp != 1.0 else "") + f"[ap{i}]")
        parts.append("".join(f"[vp{i}][ap{i}]" for i in range(n))
                     + f"concat=n={n}:v=1:a=1[v0][a0]")
    parts.append(video_chain(layout, cx, pair, clip, info["w"], info["h"], follow))

    # Grade and camera moves. Zooms are skipped on split/stack, where moving
    # the whole frame would slide the seam between the two pictures.
    chain = f"[vl]fps={fps}"
    if grade in GRADES:
        chain += "," + GRADES[grade]
    T = f"(on/{fps})"
    z, sx, sy = ["1"], [], []
    if layout not in ("split", "stack"):
        push = float(clip.get("push", edit["push"]))
        if push > 0 and layout != "speaker":     # a slow push jitters on a still face
            z.append(f"{push:.3f}*{T}/{total:.2f}")
        for b in beats:
            hit = f"max({T}-{b['out']},0))*gte({T},{b['out']})"
            if "punch" in b["fx"]:
                z.append(f"{edit['punch'] or 0.11}*exp(-5*{hit}")
            if "shake" in b["fx"]:
                z.append(f"0.04*exp(-6*{hit}")
                sx.append(f"16*sin({T}*75)*exp(-7*{hit}")
                sy.append(f"12*cos({T}*61)*exp(-7*{hit}")
        if clip.get("zoomcuts", edit["zoomcuts"]) and layout == "speaker":
            for a, b in sentence_cuts(words, total):
                z.append(f"0.10*gte({T},{a})*lt({T},{b})")
    if len(z) > 1:
        ay = 0.42 if layout == "speaker" else 0.5
        chain += (f",zoompan=z='{'+'.join(z)}'"
                  f":x='iw/2-(iw/zoom/2)+{'+'.join(sx) or 0}'"
                  f":y='(ih-ih/zoom)*{ay}+{'+'.join(sy) or 0}'"
                  f":d=1:s={OUT_W}x{OUT_H}:fps={fps}")
    chain += f",ass={ass_name}:fontsdir=fonts"
    tail = "format=yuv420p"
    if preview:
        tail = f"scale={OUT_W // 2}:{OUT_H // 2}," + tail
    if progress:
        # A bar as wide as the frame slides in from the left edge.
        parts.append(chain + "[vc]")
        parts.append(f"color=c=0x{STYLES[style]['bar']}:s={OUT_W}x12:r={fps}:"
                     f"d={total + 1:.2f}[bar]")
        parts.append(f"[vc][bar]overlay=x='-w+w*t/{total:.3f}':y=0:shortest=1,"
                     f"{tail}[vout]")
    else:
        parts.append(f"{chain},{tail}[vout]")

    # Sound: level the clip, then lay the effects on top.
    events = []
    vol = edit["sfx"] if sfx else 0
    if vol:
        if clip.get("hook") and edit["anim"]:
            events.append(("whoosh", 0.0, vol * 0.8))
        for b in beats:
            if "punch" in b["fx"] or "shake" in b["fx"]:
                events.append(("boom", max(b["out"] - 0.03, 0), vol))
            elif b.get("text"):
                events.append(("pop", b["out"], vol))
    fmt = "aformat=sample_rates=48000:channel_layouts=stereo"
    extra_inputs = []
    if events:
        used = sorted({n for n, _, _ in events})
        parts.append(f"[a0]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,{fmt}[an]")
        for k, name in enumerate(used):
            extra_inputs += ["-i", os.path.relpath(sfx[name], workdir)]
            mine = [e for e in events if e[0] == name]
            parts.append(f"[{k + 1}:a]asplit={len(mine)}"
                         + "".join(f"[{name}{j}]" for j in range(len(mine))))
            for j, (_, t, v) in enumerate(mine):
                parts.append(f"[{name}{j}]adelay={int(t * 1000)}:all=1,"
                             f"volume={v:.2f},{fmt}[fx{name}{j}]")
        labels = "".join(f"[fx{n}{j}]" for n in used
                         for j in range(sum(1 for e in events if e[0] == n)))
        parts.append(f"[an]{labels}amix=inputs={len(events) + 1}:normalize=0:"
                     f"duration=first,alimiter=limit=0.84:level=0[aout]")
    else:
        parts.append("[a0]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]")

    cmd = (["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start:.3f}",
            "-t", f"{dur:.3f}", "-i", os.path.abspath(video)] + extra_inputs
           + ["-filter_complex", ";".join(parts),
              "-map", "[vout]", "-map", "[aout]", "-t", f"{total:.3f}",
              "-c:v", "libx264", "-preset", "ultrafast" if preview else "veryfast",
              "-crf", "28" if preview else "21",
              "-maxrate", "9M", "-bufsize", "18M",
              "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out_path])
    res = run(cmd, cwd=workdir)
    ok = res.returncode == 0 and os.path.exists(out_path)
    return {"id": cid, "ok": ok, "file": out_path if ok else None,
            "layout": layout, "edit": edit_name, "style": style,
            "seconds": round(total, 1),
            "silence_cut": round(dur - sum(e - s for s, e, _ in pieces), 1),
            "caption_chunks": n_chunks,
            "beats": [{"at": b["out"], "fx": b["fx"]} for b in beats],
            "error": None if ok else res.stderr[-900:]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--clips", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--transcript")
    ap.add_argument("--only", help="comma-separated clip ids")
    ap.add_argument("--edit", choices=sorted(EDITS), default="premium")
    ap.add_argument("--style", choices=sorted(STYLES), default="bold")
    ap.add_argument("--watermark", help='channel tag on every clip, e.g. "@name"')
    ap.add_argument("--outro", help='tag over the last 1.6 s, e.g. "FOLLOW FOR MORE"')
    ap.add_argument("--progress", action="store_true",
                    help="thin progress bar along the top edge")
    ap.add_argument("--preview", action="store_true",
                    help="fast 540x960 drafts (*_preview.mp4)")
    args = ap.parse_args()
    opts = {"edit": args.edit, "style": args.style, "watermark": args.watermark,
            "outro": args.outro, "progress": args.progress,
            "preview": args.preview}

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
    try:
        import sfx as sfxlib
        sfx = sfxlib.write_all(os.path.join(workdir, "sfx"))
    except Exception:  # noqa: BLE001  (no numpy: render without sound effects)
        sfx = None

    info = probe(args.video)
    results = []
    for clip in clips:
        r = render_clip(args.video, info, clip, words, args.out, workdir, opts, sfx)
        results.append(r)
        print(json.dumps(r, ensure_ascii=False), flush=True)
    with open(os.path.join(args.out, "render_report.json"), "w",
              encoding="utf-8") as fh:
        json.dump(results, fh, indent=1, ensure_ascii=False)
    sys.exit(0 if all(r["ok"] for r in results) else 1)


if __name__ == "__main__":
    main()
