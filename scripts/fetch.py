#!/usr/bin/env python3
"""Download a YouTube video (mp4) plus its subtitles with yt-dlp.

Usage:
  python fetch.py URL --out WORKDIR [--max-height 1080] [--section 600-1500]

Prints JSON: {"video": path, "subs": [paths], "title", "duration", "channel"}.
Only works where YouTube is reachable (see check_setup.py -> "mode": "local").
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys


def ytdlp_cmd():
    exe = shutil.which("yt-dlp")
    if exe:
        return [exe]
    try:
        import yt_dlp  # noqa: F401
        return [sys.executable, "-m", "yt_dlp"]
    except ImportError:
        sys.exit("yt-dlp is not installed. Run: python -m pip install -U yt-dlp")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-height", type=int, default=1080)
    ap.add_argument("--section", help="only download START-END, in seconds "
                    "or hh:mm:ss, e.g. 600-1500")
    ap.add_argument("--langs", default="en.*,ml.*",
                    help="subtitle languages to try (yt-dlp --sub-langs)")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    h = args.max_height
    cmd = ytdlp_cmd() + [
        "--no-playlist", "--restrict-filenames",
        "-f", f"bv*[height<={h}]+ba/b[height<={h}]/b",
        "-S", "vcodec:h264,res,acodec:m4a",
        "--merge-output-format", "mp4",
        "--write-subs", "--write-auto-subs",
        "--sub-langs", args.langs + ",-live_chat",
        "--sub-format", "json3/vtt/best",
        "--write-info-json",
        "-o", os.path.join(args.out, "%(id)s.%(ext)s"),
    ]
    if args.section:
        cmd += ["--download-sections", f"*{args.section}"]
    cmd.append(args.url)

    proc = subprocess.run(cmd)
    videos = sorted(glob.glob(os.path.join(args.out, "*.mp4")),
                    key=os.path.getmtime)
    if not videos:
        # Subtitle errors (HTTP 429) can abort the run; retry video only.
        retry = [c for c in cmd if c not in ("--write-subs", "--write-auto-subs")]
        proc = subprocess.run(retry)
        videos = sorted(glob.glob(os.path.join(args.out, "*.mp4")),
                        key=os.path.getmtime)
    if not videos:
        sys.exit(f"Download failed (yt-dlp exit code {proc.returncode}). "
                 "If the error mentions sign-in or bot checks, update yt-dlp "
                 "(python -m pip install -U yt-dlp) and try again.")

    video = videos[-1]
    stem = os.path.splitext(video)[0]
    subs = sorted(glob.glob(stem + ".*.json3") + glob.glob(stem + ".*.vtt")
                  + glob.glob(stem + ".*.srt"))
    meta = {}
    info_path = stem + ".info.json"
    if os.path.exists(info_path):
        with open(info_path, encoding="utf-8") as fh:
            info = json.load(fh)
        meta = {k: info.get(k) for k in ("title", "duration", "channel",
                                         "language", "webpage_url")}
    print(json.dumps({"video": video, "subs": subs, **meta}, indent=2,
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
