# ClipForge

**Paste a link. Pick your favourites. Get Shorts that look edited.**

ClipForge is a skill for Claude. You give it a YouTube link or a video file.
It finds the best moments, shows you a scored shortlist, and turns the ones
you choose into finished vertical clips for YouTube Shorts, Instagram Reels
and TikTok.

The clips come out edited, not just cut: the picture fills the screen, the
colour is graded, the camera punches in on the big moments, and the headline
and captions are animated.

Created by **samknows.ai** · MIT licence © lowdevco

## What you type

| Command | Best for |
|---|---|
| `/clip-gameplay <link>` | Game recordings and streams |
| `/clip-podcast <link>` | Podcasts, interviews, talking to camera |
| `/clip-sports <link>` | Matches and broadcasts |
| `/clip-tutorial <link>` | How-to videos, lessons, screen recordings |
| `/clip-video <link>` | Everything else: vlogs, reviews, events |
| `/clip-edit <file or link>` | A clip you have already cut |

You can add what you want after the link:

```
/clip-gameplay <link> top 3, neon captions, watermark @myname
```

No command? Just share a link and ask for shorts. ClipForge works out what
kind of video it is.

## What happens next

1. ClipForge gets the video.
2. It finds 8 to 12 moments and scores each one out of 100.
3. It shows you the list and waits. Nothing is rendered until you choose.
4. It edits and renders your picks.
5. It writes a title, caption and hashtags for each clip.

## Edit styles

Say the name of a style to use it. Each command has a sensible default.

| Style | Good for | The look |
|---|---|---|
| `hype` | Gameplay, sports | Vivid colour, zoom hits with shake and flash, a bass thump on big moments, bold all-caps headline, progress bar |
| `premium` | Most videos (the default) | Punchy colour, a slow push-in, zoom hits with a soft thump |
| `story` | Podcasts, talking to camera | Soft colour, zoom cuts between sentences, animated captions |
| `clean` | Business, tutorials | Soft colour and animated text, nothing else |
| `raw` | When you want it untouched | A plain cut with a simple headline |

## What the editor can do

| Feature | Details |
|---|---|
| Framing | Full screen, follow the speaker, two speakers stacked, facecam on top, or blurred background |
| Speaker tracking | Spots camera cuts, finds the faces in each shot, and keeps the person talking in frame |
| Big moments | Zoom hit, shake, flash or slow motion, plus a pop-up word such as "GOAL" or "CLUTCH" |
| Headline | Animated, with your key words in an accent colour |
| Captions | Word by word, in four looks: `bold`, `clean`, `neon`, `fire`. English and Malayalam |
| Sound | Volume evened out, with thump, whoosh and pop effects made by the skill itself |
| Finishing touches | Outro tag, channel watermark, progress bar, silences trimmed |
| Safe area | Text stays clear of the app buttons on Shorts, Reels and TikTok |

## Install

### Claude Code: just give it the link

In Claude Code, paste this as a message:

```
Install the ClipForge skill from https://github.com/lowdevco/Clip-Forge
```

Claude downloads the repository and runs the installer for you. It will ask
before running commands. When it finishes, start a new session and the six
commands are available.

To do the same by hand:

```
git clone https://github.com/lowdevco/Clip-Forge
```

```
python Clip-Forge/tools/build.py --install
```

### Claude chat (claude.ai and the desktop app)

1. Download `clip-forge.zip` from the
   [latest release](https://github.com/lowdevco/Clip-Forge/releases/latest).
2. In Claude, open **Settings**, find **Skills**, and upload the zip.
3. Start a message with a command, or share a link and ask for shorts.

### What your computer needs

ClipForge runs its tools on your machine, so it needs:

- Python 3.9 or newer
- ffmpeg (a full build; on Windows: `winget install Gyan.FFmpeg`)
- `pip install opencv-python numpy yt-dlp faster-whisper`
- On Windows, the Microsoft Visual C++ runtime, for turning speech into text

Not sure what you have? Run `python scripts/check_setup.py`. It lists what
is missing and the exact command to install it. Claude runs this check
itself the first time you use the skill.

### A note on YouTube in the chat app

Claude's cloud chat is blocked from downloading YouTube videos. There, you
run `assets/pc/get_video.bat` on your PC once per video. It saves the video
to an `inbox` folder and Claude carries on from there. In Claude Code on
your own PC, the link is all you need.

## What is in this repository

| Path | What it is |
|---|---|
| `SKILL.md` | The instructions Claude follows |
| `references/` | A guide for each kind of video, plus a guide to editing |
| `commands/` | The name and description of each command |
| `scripts/` | The tools that download, transcribe, analyse, track and render |
| `assets/` | Fonts, face-detection models and the Windows download helper |
| `tools/build.py` | Builds the zip files and installs the skill |
| `tools/selftest.py` | Checks the whole skill without rendering any video |

## How well tested is it?

| Tested on real videos (Windows) | Not tested yet |
|---|---|
| Gameplay: download, moment finding, the `hype` edit and every effect | Sports and tutorial videos |
| Podcast: transcript, speaker tracking through camera cuts, the `story` edit, captions | Stacked-speaker and facecam framing on real footage |
| Build, setup check and self-test (78 checks) | Speech-to-text on Windows, spoken Malayalam, and the commands inside the Claude app |

Good to know:

- Speaker tracking is an estimate based on mouth movement. It can pick the
  wrong person, so look at the preview.
- For kill feeds and scoreboards, ClipForge detects that something changed;
  Claude then reads the frame to see what.
- The edits follow what editors usually do. They make a clip look finished.
  Nobody can promise views.

## Use it fairly

Only clip videos you own or have permission to reuse.

## Credits and licence

Created by **samknows.ai**.

Released under the [MIT License](LICENSE), copyright © 2026 lowdevco.

Some bundled files keep their own licences: the Poppins, Anton and Noto Sans
Malayalam fonts (SIL Open Font License, texts in `assets/fonts/`), the YuNet
face-detection models from OpenCV Zoo (MIT), and OpenCV's Haar cascade (its
licence is stated inside the file).
