"""Overall check of the skill without rendering any video.

Usage: python tools/selftest.py
"""
import glob, json, os, re, subprocess, sys, tempfile, zipfile

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(ROOT, "scripts")
sys.path.insert(0, S)
ok = fail = 0


def check(name, cond, detail=""):
    global ok, fail
    if cond:
        ok += 1
    else:
        fail += 1
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))


# 1. every script compiles and answers --help
for f in sorted(glob.glob(os.path.join(S, "*.py"))) + [os.path.join(ROOT, "tools", "build.py")]:
    r = subprocess.run([sys.executable, "-m", "py_compile", f], capture_output=True, text=True)
    check("compile " + os.path.basename(f), r.returncode == 0, r.stderr[-200:])
for name in ("fetch", "transcribe", "analyze_audio", "scout", "peek", "track", "render"):
    r = subprocess.run([sys.executable, os.path.join(S, name + ".py"), "--help"],
                       capture_output=True, text=True, cwd=S)
    check(f"--help {name}", r.returncode == 0 and "usage" in r.stdout.lower(), r.stderr[-200:])

# 2. setup check gives valid JSON with the expected keys
r = subprocess.run([sys.executable, os.path.join(S, "check_setup.py")], capture_output=True, text=True)
try:
    info = json.loads(r.stdout)
except Exception:
    info = {}
check("check_setup JSON", all(k in info for k in ("mode", "todo", "speech_to_text", "face_detector")))
check("check_setup: ffmpeg + ass filter", info.get("ffmpeg") and "ass" in info.get("ffmpeg_filters", []))
check("check_setup: face detector is yunet", info.get("face_detector") == "yunet", str(info.get("face_detector")))

# 3. renderer logic
import render as R
check("balanced_wrap no orphan", R.balanced_wrap("Last circle. One squad left.", 24) == ["Last circle.", "One squad left."])
rows = R.hook_lines("He quit a *40 lakh* job", 17, False)
flat = [t for row in rows for t in row]
check("hook accent words", [w for w, em in flat if em] == ["40", "lakh"] and len(flat) == 6)
pieces = R.build_pieces([(0.0, 10.0)], [(4.0, 5.0, 0.5)])
check("slow-motion pieces", pieces == [(0.0, 4.0, 1.0), (4.0, 5.0, 0.5), (5.0, 10.0, 1.0)], str(pieces))
check("remap through slow motion", abs(R.remap(6.0, pieces) - 7.0) < 1e-6 and abs(R.remap(4.5, pieces) - 5.0) < 1e-6)
segs = R.keep_segments([{"s": 0.2, "e": 1.0, "w": "a"}, {"s": 1.1, "e": 2.0, "w": "b"},
                        {"s": 4.0, "e": 4.5, "w": "c"}, {"s": 4.6, "e": 5.0, "w": "d"}], 6.0, True)
check("silence trimming", len(segs) == 2 and segs[0][1] < 2.3 and segs[1][0] > 3.7, str(segs))
check("caption filter", all(R.NOT_SPEECH.match(t) for t in (">>", "[laughter]", "[snorts", "sighs]"))
      and not any(R.NOT_SPEECH.match(t) for t in ("hat.", "I", "OH,", "Mm-")))
check("path expr cut", R.path_expr([[0, 0.2], [5, 0.8]], "cut", 1920, 606).count("gte") == 2)
check("path expr single", R.path_expr([[0, 0.5]], "cut", 1920, 606) == "656")
cuts = R.sentence_cuts([{"s": 0.0, "e": 1.0, "w": "One."}, {"s": 3.0, "e": 4.0, "w": "Two."},
                        {"s": 6.5, "e": 7.0, "w": "Three."}], 10.0)
check("zoom cuts on sentences", cuts == [(3.0, 6.5)], str(cuts))
for layout, clip, pair in (("center", {}, None), ("speaker", {}, None), ("blur", {"zoom": 1.6}, None),
                           ("split", {"facecam": [1480, 30, 420, 320]}, None),
                           ("stack", {}, [[0.25, 0.4], [0.75, 0.4]])):
    chain = R.video_chain(layout, 0.5, pair, clip, 1920, 1080)
    check(f"filter chain {layout}", chain.startswith("[v0]") and chain.endswith("[vl]"))
with tempfile.TemporaryDirectory() as td:
    for edit in R.EDITS:
        p = os.path.join(td, edit + ".ass")
        n = R.build_ass(p, [{"s": 0.5, "e": 0.9, "w": "hello"}, {"s": 0.9, "e": 1.4, "w": "world"}],
                        "A *big* claim", "center", 12.0, "bold", R.EDITS[edit], "@x",
                        [{"out": 5.0, "fx": ["punch", "flash"], "text": "Goal"}], "Follow", False, None)
        txt = open(p, encoding="utf-8").read()
        check(f"subtitle file for edit {edit}", n == 1 and "Dialogue" in txt and "GOAL" in txt and "FOLLOW" in txt)
    p = os.path.join(td, "ml.ass")
    R.build_ass(p, [{"s": 0, "e": 1, "w": "നമസ്കാരം"}], "ഇത് *കാണൂ*", "center", 8.0, "bold", R.EDITS["story"])
    check("Malayalam uses Malayalam font", "Noto Sans Malayalam" in open(p, encoding="utf-8").read())
    import sfx
    paths = sfx.write_all(os.path.join(td, "sfx"))
    check("sound effects generated", all(os.path.getsize(v) > 4000 for v in paths.values()) and len(paths) == 3)

# 4. face detector loads and finds nothing in a blank frame
import numpy as np
import faces
check("face detector kind", faces.kind() in ("yunet", "haar"))
check("blank frame -> no faces", faces.detect(np.full((360, 640, 3), 255, np.uint8)) == [])

# 5. docs: every reference and script named in SKILL.md exists; commands map to references
skill = open(os.path.join(ROOT, "SKILL.md"), encoding="utf-8").read()
check("SKILL.md front matter", skill.startswith("---\nname: clip-forge\n"))
for ref in sorted(set(re.findall(r"references/[a-z]+\.md", skill))):
    check("exists " + ref, os.path.exists(os.path.join(ROOT, ref)))
allmd = skill + "".join(open(f, encoding="utf-8").read() for f in glob.glob(os.path.join(ROOT, "references", "*.md")))
for sc in sorted(set(re.findall(r"\b([a-z_]+\.py)\b", allmd))):
    check("exists scripts/" + sc, os.path.exists(os.path.join(S, sc)))
cmds = sorted(glob.glob(os.path.join(ROOT, "commands", "*.md")))
check("six commands", len(cmds) == 6, str(len(cmds)))
for c in cmds:
    txt = open(c, encoding="utf-8").read()
    name = os.path.basename(c)[:-3]
    refs = re.findall(r"references/[a-z]+\.md", txt)
    check(f"command {name}", f"name: {name}\n" in txt and refs and all(os.path.exists(os.path.join(ROOT, r)) for r in refs)
          and ("/" + name) in skill)
for font in ("Poppins-ExtraBold.ttf", "Anton-Regular.ttf", "NotoSansMalayalam-Bold.ttf"):
    check("font " + font, os.path.exists(os.path.join(ROOT, "assets", "fonts", font)))

# 6. build produces seven valid zips
r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "build.py")], capture_output=True, text=True)
zips = sorted(glob.glob(os.path.join(ROOT, "dist", "*.zip")))
check("build: seven zips", r.returncode == 0 and len(zips) == 7, str(len(zips)))
for z in zips:
    name = os.path.basename(z)[:-4]
    with zipfile.ZipFile(z) as zf:
        names = zf.namelist()
        head = zf.read(f"{name}/SKILL.md").decode("utf-8")
        bad = [n for n in names if "__pycache__" in n or n.endswith((".mp4", ".pyc")) or "/work/" in n]
        check(f"zip {name}", head.startswith(f"---\nname: {name}\n") and not bad
              and f"{name}/scripts/render.py" in names and f"{name}/references/editing.md" in names
              and zf.testzip() is None and len(head) < 40000)

print(f"\n{ok} passed, {fail} failed")
sys.exit(1 if fail else 0)
