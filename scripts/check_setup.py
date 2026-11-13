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


def loads(name):
    """Really import the module in a child process. A package can be installed
    and still fail to load (missing DLL), which find_spec does not notice.
    Returns (ok, last line of the error)."""
    if not has_module(name):
        return False, "not installed"
    try:
        res = subprocess.run([sys.executable, "-c", f"import {name}"],
                             capture_output=True, text=True, timeout=120)
    except Exception as exc:  # noqa: BLE001
        return False, repr(exc)
    if res.returncode == 0:
        return True, None
    tail = (res.stderr.strip().splitlines() or ["import failed"])[-1]
    return False, tail[:300]


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
    fw_ok, fw_err = loads("faster_whisper")
    so_ok, so_err = loads("sherpa_onnx")
    info = {
        "os": platform.system(),
        "python": sys.version.split()[0],
        "ffmpeg": bool(shutil.which("ffmpeg")),
        "ffprobe": bool(shutil.which("ffprobe")),
        "ffmpeg_filters": ffmpeg_filters(),
        "yt_dlp": bool(shutil.which("yt-dlp")) or has_module("yt_dlp"),
        "opencv": has_module("cv2"),
        "numpy": has_module("numpy"),
        "faster_whisper": fw_ok,
        "sherpa_onnx": so_ok,
        "speech_to_text": fw_ok or so_ok,
        "js_runtime": bool(shutil.which("deno") or shutil.which("node")),
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
    errors = {k: v for k, v in (("faster_whisper", fw_err), ("sherpa_onnx", so_err))
              if v and v != "not installed"}
    if errors:
        info["speech_to_text_errors"] = errors
    if not info["speech_to_text"] and errors:
        if platform.system() == "Windows":
            todo.append("Speech-to-text is installed but cannot load (missing "
                        "Windows runtime). Run: winget install -e --id "
                        "Microsoft.VCRedist.2015+.x64   then check again.")
        else:
            todo.append("Speech-to-text is installed but cannot load; see "
                        f"speech_to_text_errors. Try: {pip} --force-reinstall "
                        "faster-whisper")
    elif not info["speech_to_text"]:
        if info["huggingface_reachable"]:
            todo.append(f"{pip} faster-whisper   (speech-to-text, best quality)")
        elif info["github_reachable"]:
            todo.append(f"{pip} sherpa-onnx   (speech-to-text that works without "
                        "Hugging Face access)")
    if info["youtube_reachable"] and info["yt_dlp"] and not info["js_runtime"]:
        info["note"] = ("yt-dlp has no JavaScript runtime, so some YouTube "
                        "formats may be missing. Downloads usually still work; "
                        "if one fails, install Deno (Windows: winget install "
                        "DenoLand.Deno).")
    info["todo"] = todo
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
