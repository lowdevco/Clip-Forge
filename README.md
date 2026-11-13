# ClipForge

A Claude skill that turns a long YouTube video, podcast or gameplay recording
into ready-to-post vertical Shorts / Reels / TikToks.

- Finds the best moments: transcript for podcasts, audio spikes + frames for gameplay
- Shows a scored table of candidates and waits for approval
- Renders 1080x1920 clips with word-by-word captions (English and Malayalam),
  a hook headline, silence trimming and -14 LUFS audio
- Writes a title, caption and hashtags for each clip

## Layout

| Path | What it is |
|---|---|
| `SKILL.md` | The instructions Claude follows |
| `scripts/check_setup.py` | Reports what the machine can do |
| `scripts/fetch.py` | Downloads a YouTube video + subtitles (yt-dlp) |
| `scripts/transcribe.py` | Word-timed transcript (subtitles, faster-whisper or sherpa-onnx) |
| `scripts/analyze_audio.py` | Finds loud, exciting moments |
| `scripts/peek.py` | Contact sheet of frames, with an optional pixel grid |
| `scripts/render.py` | Renders the vertical clips |
| `assets/pc/get_video.bat` | Windows helper: downloads a video for use in Claude chat |
| `assets/fonts/` | Caption fonts (SIL Open Font License) |

## Install

**Claude Code:** copy this folder to `~/.claude/skills/clip-forge/`.

**Claude app:** zip the folder so the zip contains `clip-forge/SKILL.md`, then
upload it as a skill.

## Requirements

Python 3.9+, ffmpeg (with libass), `opencv-python-headless`, `numpy`, `yt-dlp`,
and `faster-whisper` or `sherpa-onnx` for speech-to-text.
`python scripts/check_setup.py` lists what is missing.

## Status

- Tested: all four layouts, captions, silence trimming, audio peaks, subtitle
  parsing, sherpa-onnx transcription (on a synthetic sample).
- Not yet tested: live YouTube download, `get_video.bat`, faster-whisper,
  spoken-Malayalam recognition.

Only clip videos you own or have permission to reuse.
