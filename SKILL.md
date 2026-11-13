---
name: clip-forge
description: Turn a long YouTube video, podcast or gameplay recording into ready-to-post vertical Shorts / Reels / TikToks. Finds the most viral moments (from the transcript for podcasts, from audio spikes and frames for gameplay), shows a scored table for approval, then renders 1080x1920 clips with word-by-word captions (English and Malayalam), a hook headline and loudness-normalised audio. Use whenever the user gives a YouTube link or a long video file and wants shorts, reels, clips, highlights, "viral parts", "best moments" or "cut this into short videos", even if they do not name this skill.
---

# ClipForge

Long video in, a handful of finished vertical clips out. The pipeline is:

1. `check_setup.py` – what can this machine do?
2. Get the video (three routes, below)
3. `transcribe.py` – words with timings
4. `analyze_audio.py` – loud, exciting moments
5. You pick and score candidates, the user approves
6. `render.py` – 9:16 clips with captions
7. Titles, captions and hashtags for each clip

All scripts live in `scripts/` next to this file. Run them with the absolute
path to that folder. Keep everything for one video in one work folder
(`<workdir>`), with finished clips in `<workdir>/shorts`.

Only work on videos the user owns or has permission to reuse. If they are
clipping someone else's channel, mention once that re-uploading needs the
owner's permission, then carry on with what they asked.

## 1. Check the machine

```
python scripts/check_setup.py
```

Read `mode` and `todo`. Install what `todo` lists (they are copy-paste
commands). `mode` decides how the video arrives:

- **`local`** – YouTube is reachable (Claude Code on the user's own PC). The
  whole pipeline runs from just a link.
- **`cloud`** – YouTube is blocked (Claude chat / cloud sessions). The
  download has to happen on the user's computer; everything after that runs
  here. Do not retry the download through other tools or mirrors, the block
  is at the network level.

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
   keep the file small; `get_video.bat <url> 1080` gives sharper speaker crops.
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

## 3. Transcribe

```
python scripts/transcribe.py <video> --out <workdir> [--lang en|ml|auto] [--model small]
```

It tries, in order: a subtitle file → faster-whisper → sherpa-onnx whisper
(downloads from GitHub, so it works in cloud mode). Read the JSON it prints:

- `exact_word_timing: false` means word timings are estimated inside each
  line. Captions still work, the highlight is just a little less tight.
- Speech-to-text on a long video is slow on a small machine (roughly real
  time with `small` on 2 CPUs). Run it in the background and tell the user.
  `--model base` or `tiny` is faster but weak; do not go below `small` for
  Malayalam, and tell the user Malayalam captions will need a read-through.
- Exit code 3 = no transcript possible. Carry on in audio-only mode: pick
  moments from audio peaks and frames, render with `"captions": false`.

Then read `<workdir>/transcript.txt` in full. It is the compact
`[mm:ss] text` version; the JSON is for the renderer, not for reading.

## 4. Find loud moments

```
python scripts/analyze_audio.py <video> --out <workdir>
```

Prints time, lift in dB above the surrounding minute, and how long each
burst lasts. For gameplay this is the main signal: shouts, laughter, a
clutch, an explosion. For podcasts it flags laughter and raised voices.

## 5. Choose candidates

First decide what kind of video this is, because the two kinds go viral for
different reasons:

**Podcast / talking head** – the moment is in the words. Look for a
self-contained story or claim that makes sense with zero context: a bold or
contrarian statement, a number that surprises, a confession, a clear
how-to, a punchline. Start the clip on the sentence that hooks, not on the
question that led to it. End on the payoff, not a trailing "so yeah".

**Gameplay** – the moment is in the action and the reaction. Start from the
audio peaks, then look at what is happening:

```
python scripts/peek.py <video> --at 754,760,766 --out <workdir>/peek.jpg
```

Open the image. Keep peaks where something visibly happens (a fight, a win
or fail screen, a jump scare) and drop peaks that are menus, loading screens
or music. A gameplay clip needs build-up: begin 8–20 s before the peak so
the viewer sees the situation, and end 2–4 s after the reaction lands.
While you are looking, note whether there is a facecam and where.

Aim for 8–12 candidates on a long video (fewer if it is short), each 20–60 s;
gameplay moments can be as short as 12 s. Do not overlap them.

Score each out of 100:

| Part | Points | What earns them |
|---|---|---|
| Hook | 30 | First 3 seconds make a stranger stop: a claim, a question, or action already under way |
| Payoff | 25 | It delivers: the answer, the punchline, the kill, the fail |
| Stands alone | 20 | Makes sense without the rest of the video |
| Emotion | 15 | Surprise, laughter, tension, awe, or strong disagreement |
| Pace | 10 | No dead stretch; the length fits the content |

Be honest with the scores. A long video with three good moments should get
three high scores and several mediocre ones, not twelve 85s.

Show the table and stop for approval:

| # | Time | Len | Score | Type | Hook line (on screen) | Why it works |
|---|---|---|---|---|---|---|
| 1 | 12:34–13:10 | 36s | 88 | Podcast | He quit a ₹40 lakh job for this | Bold claim up front, clean ending |

Ask which numbers to render (and offer "top 5"). Do not render before the
user answers; rendering is the slow part and their taste decides.

The hook line is the 3–8 word headline burned at the top for the first
3.5 seconds. Write it to create curiosity without lying about the clip. Use
the language the speaker uses (Malayalam hook for a Malayalam clip).

## 6. Render

Write `<workdir>/clips.json` for the approved clips:

```json
{"clips": [
  {"id": 1, "start": 754.2, "end": 790.6, "hook": "He quit a ₹40 lakh job for this",
   "slug": "quit-job", "layout": "auto", "tighten": true},
  {"id": 4, "start": 2210, "end": 2236, "hook": "1 HP. Four enemies.",
   "layout": "split", "facecam": [1480, 30, 420, 320]}
]}
```

Snap `start` and `end` to word boundaries from `transcript.json` so a clip
never opens or closes mid-word.

Layout guide:

| Video | Layout | Notes |
|---|---|---|
| One speaker on camera | `auto` or `speaker` | Crops onto the detected face |
| Two-person podcast, wide shot | `blur` with `"zoom": 1.3` | A crop would lose one speaker; if only one person talks in the clip, `speaker` is better |
| Gameplay with facecam | `split` | Facecam on top, game below. Get the box with `peek.py --grid` and read x, y, w, h off the pixel labels |
| Gameplay, no facecam, action in the middle | `center` | Fills the screen; check a frame to be sure the HUD you need is not cut off |
| Gameplay or screen recording where the edges matter | `blur` with `"zoom": 1.3–1.6` | Keeps the whole width |

`tighten: true` removes silences longer than 0.7 s. Use it for talk; leave it
off for gameplay, where a quiet second before the action is the tension.

```
python scripts/render.py <video> --clips <workdir>/clips.json --out <workdir>/shorts
```

One JSON line per clip (`ok`, `file`, `layout`, `seconds`, `silence_cut`).
Roughly real time per clip on a small machine, so say how long it will take.

Then check your own work before showing it: pull one frame from each clip
and look at it.

```
ffmpeg -y -loglevel error -ss 2 -i <clip.mp4> -frames:v 1 <workdir>/check_01.jpg
```

Confirm the subject is in frame, the hook is readable, and captions do not
sit on a face. Fix by changing the layout, `zoom` or `facecam` and re-render
just that clip with `--only <id>`.

## 7. Post copy

For each rendered clip write, in the clip's language:

- **Title** (under 60 characters, the hook rephrased, no clickbait the clip
  does not pay off)
- **Caption** (1–2 lines plus a question or call to action)
- **Hashtags** (3–5: one broad, the rest specific to the topic or game)

Save them as `<workdir>/shorts/posts.md` and show them in the reply.

## 8. Hand over

- Local mode: say where the `shorts` folder is.
- Cloud mode: send each `.mp4` and `posts.md` to the user as files. If the
  video came from a connected folder on their computer, also save the clips
  into a `shorts` folder beside the `inbox`.

Finish with one line per clip (number, length, hook) and offer changes:
different start or end, another layout, a new hook line, more clips from the
remaining candidates.

## Things that go wrong

- **Download fails in local mode with a sign-in or bot message** – update
  yt-dlp (`python -m pip install -U yt-dlp`) and retry once. If it still
  fails, ask the user to download the video another way and use route C.
- **Captions are wrong words** – the transcript is wrong, not the renderer.
  Fix the words in `transcript.json` for that clip's time range and
  re-render, or re-run `transcribe.py` with a bigger `--model`.
- **Face crop follows the wrong person** – switch that clip to `blur`, or
  `center` if the speaker is in the middle.
- **`ass` filter missing** – ffmpeg was built without libass; `check_setup`
  says how to install a full build.
