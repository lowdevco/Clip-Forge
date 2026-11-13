# ClipForge

A Claude skill that turns a long YouTube video, podcast or gameplay recording
into ready-to-post vertical Shorts / Reels / TikToks.

- Finds the best moments: transcript for podcasts, sound + motion + frames for gameplay
- Shows a scored table of candidates and waits for approval
- Renders 1080x1920 clips with word-by-word captions (English and Malayalam),
  a hook headline, silence trimming and -14 LUFS audio
- Four caption styles, optional channel watermark and progress bar
- Writes a title, caption and hashtags for each clip

## Commands

| Command | For |
|---|---|
| `/clip-gameplay <link>` | Game recordings and streams |
| `/clip-podcast <link>` | Podcasts, interviews, talking head |
| `/clip-video <link>` | Any other video (vlog, tutorial, event, sports) |

Each command fixes the mode, so Claude does not have to work out what kind of
video it is. Extra wishes go after the link:
`/clip-gameplay <link> top 3, neon captions, watermark @myname`.

In Claude Code the three are real slash commands once installed. In the
Claude app, type the command at the start of the message; the skill
description lists them so the skill is picked up.

## Build and install

```
python tools/build.py              # writes dist/*.zip
python tools/build.py --install    # also copies the skills to ~/.claude/skills
```

This produces four self-contained skills from the one source:

| Zip | What it is |
|---|---|
| `dist/clip-forge.zip` | All-in-one: detects the kind of video, and accepts the three commands as typed text |
| `dist/clip-gameplay.zip` | Fixed to gameplay mode |
| `dist/clip-podcast.zip` | Fixed to podcast mode |
| `dist/clip-video.zip` | Fixed to general-video mode |

**Claude app:** upload the zips you want as skills (all four, or only
`clip-forge.zip`).

**Claude Code:** run the `--install` form.

## Layout

| Path | What it is |
|---|---|
| `SKILL.md` | The instructions Claude follows |
| `references/` | One guide per mode: gameplay, podcast, video |
| `commands/` | Name, description and mode note for each command skill |
| `tools/build.py` | Packages the zips (not part of the skill itself) |
| `scripts/check_setup.py` | Reports what the machine can do, and what to install |
| `scripts/fetch.py` | Downloads a YouTube video + subtitles (yt-dlp) |
| `scripts/transcribe.py` | Word-timed transcript (subtitles, faster-whisper or sherpa-onnx) |
| `scripts/scout.py` | Ranks the stretches with the most sound and motion, with a filmstrip of each |
| `scripts/analyze_audio.py` | Finds single loud instants |
| `scripts/peek.py` | Contact sheets and filmstrips of frames, with an optional pixel grid |
| `scripts/render.py` | Renders the vertical clips |
| `assets/pc/get_video.bat` | Windows helper: downloads a video for use in Claude chat |
| `assets/fonts/` | Caption fonts (SIL Open Font License) |

## Requirements

Python 3.9+, ffmpeg (with libass), `opencv-python`, `numpy`, `yt-dlp`, and
`faster-whisper` or `sherpa-onnx` for speech-to-text. On Windows,
faster-whisper also needs the Microsoft Visual C++ runtime.
`python scripts/check_setup.py` lists what is missing.

## Status

- Tested on Windows with a real 17-minute gameplay video: YouTube download,
  audio peaks, scout ranking and filmstrips, `blur` and `center` layouts, hook
  headline, all four caption styles, watermark, progress bar, preview renders,
  and the zip build.
- Tested earlier on a synthetic sample only: `speaker` and `split` layouts,
  silence trimming, subtitle parsing, sherpa-onnx transcription.
- Not yet tested: podcast mode on a real video, faster-whisper on Windows,
  `get_video.bat` run by hand, spoken-Malayalam recognition, the command
  skills inside the Claude app.

Only clip videos you own or have permission to reuse.
