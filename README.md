<div align="center">

# ClipForge

**Paste a link. Pick your favourites. Get Shorts that look edited.**

ClipForge is a skill for Claude. You give it a YouTube link or a video file.
It finds the best moments, shows you a scored shortlist, and turns the ones
you choose into finished vertical clips for YouTube Shorts, Instagram Reels
and TikTok.

The clips come out edited, not just cut: the picture fills the screen, the
colour is graded, the camera punches in on the big moments, and the headline
and captions are animated.

Created by [samknows.ai](https://www.instagram.com/samknows.ai)

<a href="https://www.instagram.com/samknows.ai/">
  <img src="https://raw.githubusercontent.com/lowdevco/Video-editing-effects/main/assets/samknowsai.jpeg" width="380" alt="samknows.ai" style="border-radius: 10px;" />
</a>

## What you type

| Command | Best for |
|---|---|
| `/clip-gameplay` | Game recordings and streams |
| `/clip-podcast` | Podcasts, interviews, talking to camera |
| `/clip-sports` | Matches and broadcasts |
| `/clip-tutorial` | How-to videos, lessons, screen recordings |
| `/clip-video` | Everything else: vlogs, reviews, events |
| `/clip-edit` | A clip you have already cut |

Add what you want after the command:

```
/clip-gameplay <link> top 3, neon captions, watermark @myname
```

No command? Just ask for shorts. ClipForge works out what kind of video it is.

## What happens next

| Step | What ClipForge does |
|:---:|---|
| 1 | Gets the video |
| 2 | Finds 8 to 12 moments and scores each one out of 100 |
| 3 | Shows you the list and waits. Nothing is rendered until you choose |
| 4 | Edits and renders your picks |
| 5 | Writes a title, caption and hashtags for each clip |

## Install

### Claude Code

Paste this as a message in Claude Code:

```
Install the ClipForge skill from https://github.com/lowdevco/Clip-Forge
```

Claude downloads the repository and runs the installer, asking before it
runs commands. Then start a new session.

Or do it by hand:

```
git clone https://github.com/lowdevco/Clip-Forge
```

```
python Clip-Forge/tools/build.py --install
```

### Claude chat (claude.ai and the desktop app)

| Step | What to do |
|:---:|---|
| 1 | Download `clip-forge.zip` from the [latest release](https://github.com/lowdevco/Clip-Forge/releases/latest) |
| 2 | In Claude, open **Settings**, find **Skills**, and upload the zip |
| 3 | On the same page, make sure code execution and file creation is switched on |

## How to use it

### In Claude Code

Claude Code downloads the video for you, so the link is all it needs.

| Step | What to do |
|:---:|---|
| 1 | Type a command with your YouTube link, for example `/clip-podcast https://youtu.be/...` |
| 2 | Wait for the scored list, then answer with your picks, for example `top 3` |
| 3 | Find the finished clips in the `shorts` folder Claude tells you about |

### In Claude chat

Claude chat cannot download from YouTube, so you give it the video file.

| Step | What to do |
|:---:|---|
| 1 | Open [vidssave.com](https://vidssave.com), paste the YouTube link, and download the video as MP4. 720p is enough |
| 2 | Attach the file to a new chat (up to 500 MB) and type a command, for example `/clip-podcast` |
| 3 | Wait for the scored list, then answer with your picks, for example `top 3` |
| 4 | Download the finished clips Claude sends back |

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

## What Claude Code needs on your computer

In Claude Code the tools run on your own machine. Claude chat runs them in
its own workspace, so this section does not apply there.

| Needed | How to get it |
|---|---|
| Python 3.9 or newer | [python.org](https://www.python.org/downloads/) |
| ffmpeg, full build | Windows: `winget install Gyan.FFmpeg` |
| Python packages | `pip install opencv-python numpy yt-dlp faster-whisper` |
| Visual C++ runtime (Windows only) | Needed for turning speech into text |

Not sure what you have? Claude checks on first use and tells you what to
install. You can also run `python scripts/check_setup.py` yourself.

## What is in this repository

| Path | What it is |
|---|---|
| `SKILL.md` | The instructions Claude follows |
| `references/` | A guide for each kind of video, plus a guide to editing |
| `commands/` | The name and description of each command |
| `scripts/` | The tools that download, transcribe, analyse, track and render |
| `assets/` | Fonts, face-detection models and a Windows download helper |
| `tools/build.py` | Builds the zip files and installs the skill |
| `tools/selftest.py` | Checks the whole skill without rendering any video |

## How well tested is it?

| Tested on real videos (Windows, Claude Code) | Not tested yet |
|---|---|
| Gameplay: download, moment finding, the `hype` edit and every effect | Sports and tutorial videos |
| Podcast: transcript, speaker tracking through camera cuts, the `story` edit, captions | Stacked-speaker and facecam framing on real footage |
| Build, setup check and self-test (78 checks) | Claude chat, speech-to-text on Windows, spoken Malayalam |

## Good to know

Speaker tracking is an estimate based on mouth movement. It can pick the
wrong person, so look at the preview.

For kill feeds and scoreboards, ClipForge detects that something changed.
Claude then reads the frame to see what.

The edits follow what editors usually do. They make a clip look finished.
Nobody can promise views.

## Credits and licence

Created by [samknows.ai](https://www.instagram.com/samknows.ai)

Released under the [MIT License](LICENSE), copyright © 2026 lowdevco.

Some bundled files keep their own licences: the Poppins, Anton and Noto Sans
Malayalam fonts (SIL Open Font License, texts in `assets/fonts/`), the YuNet
face-detection models from OpenCV Zoo (MIT), and OpenCV's Haar cascade (its
licence is stated inside the file).

</div>
