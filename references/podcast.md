# Podcast mode

Podcasts, interviews and talking-head videos. The moment is in the words, so
the transcript is the main tool and it is required. If `check_setup.py` shows
`speech_to_text: false` and the video has no subtitles, stop and tell the
user what to install; do not fall back to guessing from audio.

## Find the moments

1. Run `transcribe.py`, then read `<workdir>/transcript.txt` in full.
2. Look for passages that work with zero context:
   - a bold or contrarian claim
   - a number that surprises
   - a confession or a story with a turn
   - a clear how-to in three steps or fewer
   - a punchline
3. Start the clip on the sentence that hooks, not on the question that led
   to it. End on the payoff, not a trailing "so yeah". A clip that needs the
   host's question to make sense should include it only if it is short.
4. Run `analyze_audio.py` as a second opinion: its peaks are laughter and
   raised voices. A passage you liked that also has a peak is a strong
   candidate; a peak with no good passage around it is not one.
5. Snap `start` and `end` to word boundaries from `transcript.json` so a clip
   never opens or closes mid-word. Leave 0.15 s of air on each side.

## Framing: follow the speaker

After the user approves clips and you have written `clips.json` (with
`"layout": "auto"`), run the tracker:

```
python scripts/track.py <video> --clips <workdir>/clips.json --write
```

For each clip it finds the camera cuts, tracks the people inside each shot,
estimates who is talking when, and writes back a suggested layout and a
`focus_path`: a crop position for every shot and every change of speaker.
Read its output (`cuts`, `no_face`, and the people in each shot):

| It reports | Layout to use |
|---|---|
| One person on screen at a time (single camera, or an edit that cuts between cameras) | `speaker`. The path keeps the crop on them through camera changes |
| Two people in one steady shot, both talk in the clip | `stack`: both on screen, one above the other, captions on the seam. The safest choice for a conversation |
| Two people in one shot, one does the talking | `speaker` with the path: the crop sits on the talker and cuts across when the other answers |
| Three or more people in a wide shot | `speaker` with the path. `stack` shows only two people, so it would drop someone |
| No faces (screen share, slides) | `blur` with `"zoom": 1.0–1.3` |

The tracker is a heuristic: it compares mouth movement between faces. It is
usually right for people facing the camera and can be fooled by laughter,
eating, or a voice from off screen. Before the full render, run
`render.py --preview` and look at eight to ten frames spread across each
clip, not just the start: an empty frame (bare wall, half a chair) means the
crop is pointing at nobody. If the crop is wrong in a steady two-person
shot, switch that clip to `stack`, which needs no guess about who is
talking.

Two more things to read off its output:

- **`cuts`** – if the source already cuts between cameras every few seconds
  (say more than one cut per five seconds), it has its own rhythm. Set
  `"zoomcuts": false` on the clip so the `story` edit does not add zoom
  changes on top.
- **What sits above the faces** – the headline's default spot is the top of
  the frame. If something that matters is there (a prop, a name card, a
  picture on a headband), move the headline with `"hook_y"`, for example
  `940` to place it on the chest above the captions.

## Edit

Read `references/editing.md`. For talk:

- `"edit": "story"`: zoom cuts on sentence changes give a single-camera
  shot the rhythm of a multi-camera edit. Use `clean` for serious or
  business content.
- `"tighten": true`: removes silences longer than 0.7 s.
- Captions on, always. Style `bold`; `clean` for calm content.
- Beats are optional in talk. One `punch` on the punchline or the key
  number, with a callout of that number, is plenty.
- Hook line in the speaker's language, with `*stars*` on the key words. For
  Malayalam, write the hook in Malayalam script and tell the user the
  captions need a read-through.
- If the captions show a wrong name or term, fix the words in
  `transcript.json` for that time range and re-render with `--only`.

## Post copy

The title is the claim in the clip, rephrased. Tag the guest's name and the
topic rather than generic tags.
