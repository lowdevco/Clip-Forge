#!/usr/bin/env python3
"""Report what this machine can do, as JSON. Run this first.

Usage: python check_setup.py
"""
import importlib.util
import json
import platform
import shutil
import subprocess
import sys
import urllib.request


def has_module(name):
    return importlib.util.find_spec(name) is not None


def reachable(url):
    try:
        req = urllib.request.Request(url, method="HEAD",
                                     headers={"User-Agent": "Mozilla/5.0"})
        urllib.request.urlopen(req, timeout=8)
        return True
    except Exception as exc:  # noqa: BLE001
        code = getattr(exc, "code", None)
        # 4xx/5xx from the site itself still means the network path is open,
        # but a proxy refusal shows up as a tunnel/URL error with no code.
        return code is not None and code not in (403, 407)


def ffmpeg_filters():
    try:
        out = subprocess.run(["ffmpeg", "-hide_banner", "-filters"],
                             capture_output=True, text=True, timeout=20).stdout
    except Exception:  # noqa: BLE001
        return []
    return [f for f in ("ass", "loudnorm", "boxblur") if f" {f} " in out]


def main():
    info = {
        "os": platform.system(),
        "python": sys.version.split()[0],
        "ffmpeg": bool(shutil.which("ffmpeg")),
        "ffprobe": bool(shutil.which("ffprobe")),
        "ffmpeg_filters": ffmpeg_filters(),
        "yt_dlp": bool(shutil.which("yt-dlp")) or has_module("yt_dlp"),
        "opencv": has_module("cv2"),
        "numpy": has_module("numpy"),
        "faster_whisper": has_module("faster_whisper"),
        "sherpa_onnx": has_module("sherpa_onnx"),
        "youtube_reachable": reachable("https://www.youtube.com/"),
        "huggingface_reachable": reachable("https://huggingface.co/"),
        "github_reachable": reachable("https://github.com/"),
    }
    info["mode"] = "local" if info["youtube_reachable"] else "cloud"

    todo = []
    pip = f"{sys.executable} -m pip install"
    if platform.system() == "Linux":
        pip += " --break-system-packages"
    if not info["ffmpeg"] or not info["ffprobe"]:
        todo.append("Install ffmpeg (Windows: winget install Gyan.FFmpeg ; "
                    "macOS: brew install ffmpeg ; Linux: apt install ffmpeg)")
    elif "ass" not in info["ffmpeg_filters"]:
        todo.append("This ffmpeg has no libass (no burned captions). "
                    "Install a full build (Windows: winget install Gyan.FFmpeg).")
    if not info["opencv"] or not info["numpy"]:
        todo.append(f"{pip} opencv-python-headless numpy")
    if info["youtube_reachable"] and not info["yt_dlp"]:
        todo.append(f"{pip} -U yt-dlp")
    if not info["faster_whisper"] and not info["sherpa_onnx"]:
        if info["huggingface_reachable"]:
            todo.append(f"{pip} faster-whisper   (speech-to-text, best quality)")
        elif info["github_reachable"]:
            todo.append(f"{pip} sherpa-onnx   (speech-to-text that works without "
                        "Hugging Face access)")
    info["todo"] = todo
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
