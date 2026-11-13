---
name: clip-forge
description: Turn a long YouTube video, podcast or gameplay recording into ready-to-post vertical Shorts / Reels / TikToks. Finds the most viral moments (from the transcript for podcasts, from action and sound for gameplay), shows a scored table for approval, then renders 1080x1920 clips with word-by-word captions (English and Malayalam), a hook headline and loudness-normalised audio. Use whenever the user gives a YouTube link or a long video file and wants shorts, reels, clips, highlights, "viral parts", "best moments" or "cut this into short videos", even if they do not name this skill. Also use when a message starts with /clip-gameplay, /clip-podcast or /clip-video.
---

# ClipForge

Long video in, a handful of finished vertical clips out. The pipeline is:

1. `check_setup.py` – what can this machine do?
2. Get the video (three routes, below)
3. Find the moments – how depends on the **mode**
4. Show a scored table, the user approves
5. `render.py` – 9:16 clips with captions
6. Titles, captions and hashtags for each clip

All scripts live in `scripts/` next to this file. Run them with the absolute
path to that folder. Keep everything for one video in one work folder
(`<workdir>`), with finished clips in `<workdir>/shorts`.

Only work on videos the user owns or has permission to reuse. If they are
clipping someone else's channel, mention once that re-uploading needs the
owner's permission, then carry on with what they asked.

## Mode

The kind of video decides how moments are found, framed and captioned. Read
the one reference file for the mode before step 3, and follow it.

| Command | Mode | Reference | Use for |
|---|---|---|---|
| `/clip-gameplay <link>` | gameplay | `references/gameplay.md` | Game recordings and streams, with or without a facecam |
| `/clip-podcast <link>` | podcast | `references/podcast.md` | Podcasts, interviews, talking head: the moment is in the words |
| `/clip-video <link>` | video | `references/video.md` | Everything else: vlogs, tutorials, events, sports, reviews |

- If the message starts with one of the commands (or the user names the kind
  of video in words), the mode is settled. Do not second-guess it.
- With no command, decide from the title, channel and a contact sheet
  (`peek.py --at` with five times spread over the video). If it is still
  unclear, ask in one line which of the three it is.

Anything after the link is a request to honour, for example
`/clip-gameplay <link> top 3, neon captions, watermark @myname`.

## 1. Check the machine

```
python scripts/check_setup.py
```

Read `mode`, `todo` and `speech_to_text`. Install what `todo` lists (they are
copy-paste commands; ask before installing on the user's own PC).

- **`mode: local`** – YouTube is reachable (Claude Code on the user's own PC).
  The whole pipeline runs from just a link.
- **`mode: cloud`** – YouTube is blocked (Claude chat / cloud sessions). The
  download has to happen on the user's computer; everything after that runs
  here. Do not retry the download through other tools or mirrors, the block
  is at the network level.
- **`speech_to_text: false`** – no transcript can be made here unless the
  video has subtitles. Podcast mode needs one; say so before starting.

## 2. Get the video

**A. Local mode, link given**

```
python scripts/fetch.py "<url>" --out <workdir>
```

It prints the video path and any subtitle files. For videos over ~90 minutes
ask whether they want the whole thing or a section (`--section 600-3000`).

**B. Cloud mode, link given**

Say plainly, in one or two sentences, that this chat cannot download from
YouTube itself and the download takes one step on their PC. Then:

1. Send them `assets/pc/get_video.bat` (once; they keep it in a folder of
   their choice, e.g. a project folder they have connected to the chat).
2. They double-click it and paste the link. It saves the video, subtitles
   and info file into an `inbox` folder next to the .bat. Default is 720p to
   keep the file small; `get_video.bat <url> 1080` gives sharper crops.
3. If computer-folder tools are available in this session (names containing
   `remote-devices`), list the `inbox` folder, copy the `.mp4` and every
   `.json3` / `.vtt` beside it into the workspace, and continue. Those tools
   usually cap one file at about 400 MB: if the video is bigger, ask them to
   re-run the .bat at 480, or to tell you which part of the video matters.
4. If there are no such tools, ask them to attach the video and subtitle
   file to the chat (works for small files only), or to run this skill in
   Claude Code on the PC where route A works end to end.

**C. A video file is already here** (attached, or in a connected folder) –
use it directly. A subtitle file with the same name beside it is picked up
automatically.

## 3. Find the moments

Follow the reference file for the mode. The tools it draws on:

| Tool | What it gives |
|---|---|
| `transcribe.py <video> --out <workdir> [--lang en\|ml\|auto] [--model small]` | Word-timed transcript: subtitle file → faster-whisper → sherpa-onnx. Exit code 3 = no transcript possible |
| `scout.py <video> --out <workdir> [--top 12] [--len 30]` | The stretches with the most sound and motion, ranked, each with an 8-frame filmstrip in `<workdir>/scout/`, plus `end.jpg` for the last 45 s |
| `analyze_audio.py <video> --out <workdir>` | Single loud instants (a laugh, a shout) with their lift in dB |
| `peek.py <video> --at 754,760 --out x.jpg` | Frames at exact times |
| `peek.py <video> --range 998-1032 --n 8 --out x.jpg` | A filmstrip of one stretch, start to finish |
| `peek.py <video> --at 600 --grid --out x.jpg` | One frame with a pixel grid, for reading a facecam box |

Notes on transcription:

- `exact_word_timing: false` means word timings are estimated inside each
  line. Captions still work, the highlight is just a little less tight.
- Speech-to-text on a long video is slow on a small machine (roughly real
  time with `small` on 2 CPUs). Run it in the background and tell the user.
  Do not go below `small` for Malayalam, and tell the user Malayalam captions
  will need a read-through.
- After it finishes, read `<workdir>/transcript.txt` in full. It is the
  compact `[mm:ss] text` version; the JSON is for the renderer.

`scout.py` takes about two minutes for a 17-minute 1080p video. Its `action`
number is a rank inside that one video: it tells you where to look first, not
how good the moment is. Open the filmstrips and judge with your own eyes.

## 4. Score and get approval

Aim for 8–12 candidates on a long video (fewer if it is short), each 20–60 s;
action moments can be as short as 12 s. Do not overlap them.

Score each out of 100:

| Part | Points | What earns them |
|---|---|---|
| Hook | 30 | First 3 seconds make a stranger stop: a claim, a question, or action already under way |
| Payoff | 25 | It delivers: the answer, the punchline, the kill, the fail |
| Stands alone | 20 | Makes sense without the rest of the video |
| Emotion | 15 | Surprise, laughter, tension, awe, or strong disagreement |
| Pace | 10 | No dead stretch; the length fits the content |

Be honest with the scores. A long video with three good moments should get
three high scores and several mediocre ones, not twelve 85s. If you judged a
moment from still frames only, say so.

Show the table and stop for approval:

| # | Time | Len | Score | Hook line (on screen) | Why it works |
|---|---|---|---|---|---|
| 1 | 12:34–13:10 | 36s | 88 | He quit a ₹40 lakh job for this | Bold claim up front, clean ending |

Ask which numbers to render (and offer "top 5"). Do not render before the
user answers; rendering is the slow part and their taste decides. In the same
message, ask once for anything not yet known that changes the render: caption
style, a channel tag for the watermark, progress bar on or off.

The hook line is the 3–8 word headline burned at the top for the first
3.5 seconds. Write it to create curiosity without lying about the clip: only
claim what you saw or read. Use the language the speaker uses (Malayalam hook
for a Malayalam clip).

## 5. Render

Write `<workdir>/clips.json` for the approved clips:

```json
{"clips": [
  {"id": 1, "start": 754.2, "end": 790.6, "hook": "He quit a ₹40 lakh job for this",
   "slug": "quit-job", "layout": "auto", "tighten": true},
  {"id": 4, "start": 2210, "end": 2236, "hook": "1 HP. Four enemies.",
   "layout": "split", "facecam": [1480, 30, 420, 320], "captions": false}
]}
```

Layouts (the mode reference says which to pick):

| Layout | Result |
|---|---|
| `speaker` | 9:16 crop centred on the detected face |
| `auto` | `speaker` if a clear face is found, otherwise `blur` |
| `center` | 9:16 crop that fills the screen; `"focus_x": 0–1` slides it left or right |
| `blur` | Whole width kept in the middle, blurred copy above and below; `"zoom": 1.0–2.5` enlarges the sharp picture and trims its sides |
| `split` | Facecam on top, game below; needs `"facecam": [x, y, w, h]` |

Looks, set for every clip on the command line or per clip in `clips.json`:

| Option | Per-clip key | What it does |
|---|---|---|
| `--style bold\|clean\|neon\|fire` | `"style"` | Caption look. `bold`: big white capitals, yellow highlight (default). `clean`: smaller sentence case, pale blue highlight, sits lower. `neon`: green highlight, purple outline. `fire`: largest, orange highlight |
| `--watermark "@name"` | `"watermark"` | Small see-through channel tag for the whole clip |
| `--progress` | `"progress"` | Thin bar along the top that fills as the clip plays |

```
python scripts/render.py <video> --clips <workdir>/clips.json --out <workdir>/shorts [--style neon] [--watermark "@name"] [--progress]
```

One JSON line per clip (`ok`, `file`, `layout`, `style`, `seconds`,
`silence_cut`). Roughly real time per clip on a small machine, so say how
long it will take. When the framing is a guess (a new layout, a facecam box,
a zoom level), run once with `--preview` first: it makes small fast drafts
(`*_preview.mp4`) to check before the full render.

Then check your own work before showing it: pull one frame from each clip
and look at it.

```
ffmpeg -y -loglevel error -ss 2 -i <clip.mp4> -frames:v 1 <workdir>/check_01.jpg
```

Confirm the subject is in frame, the hook is readable, and captions do not
sit on a face or on the part of the game that matters. Fix by changing the
layout, `zoom`, `focus_x` or `facecam` and re-render just that clip with
`--only <id>`.

## 6. Post copy

For each rendered clip write, in the clip's language:

- **Title** (under 60 characters, the hook rephrased, no clickbait the clip
  does not pay off)
- **Caption** (1–2 lines plus a question or call to action)
- **Hashtags** (3–5: one broad, the rest specific to the topic or game)

Save them as `<workdir>/shorts/posts.md` and show them in the reply.

## 7. Hand over

- Local mode: say where the `shorts` folder is.
- Cloud mode: send each `.mp4` and `posts.md` to the user as files. If the
  video came from a connected folder on their computer, also save the clips
  into a `shorts` folder beside the `inbox`.

Finish with one line per clip (number, length, hook) and offer changes:
different start or end, another layout or caption style, a new hook line,
more clips from the remaining candidates.

## Things that go wrong

- **Download fails in local mode with a sign-in or bot message** – update
  yt-dlp (`python -m pip install -U yt-dlp`) and retry once. If it still
  fails, ask the user to download the video another way and use route C.
- **`transcribe.py` exits 3 with a "could not find module ... dll" error** –
  the speech engine is installed but cannot load. `check_setup.py` prints the
  fix (on Windows, the Visual C++ runtime). This is a machine problem, not a
  silent video: say so rather than treating the video as speechless.
- **Captions are wrong words** – the transcript is wrong, not the renderer.
  Fix the words in `transcript.json` for that clip's time range and
  re-render, or re-run `transcribe.py` with a bigger `--model`.
- **Face crop follows the wrong person** – switch that clip to `blur`, or
  `center` with a `focus_x`.
- **`ass` filter missing** – ffmpeg was built without libass; `check_setup`
  says how to install a full build.
