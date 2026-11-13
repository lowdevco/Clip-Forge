# Video mode (general)

For everything without its own mode: vlogs, reviews, events, travel,
reactions, product demos, music and dance. Moments can come from the words,
the pictures, or both, so use both tools and let the video tell you which
matters more. (Gameplay, podcasts, sport and tutorials each have their own
mode and guide; use those when they fit.)

## Find the moments

1. Run `transcribe.py` and `scout.py`. Read `transcript.txt` in full and open
   the scout filmstrips.
2. Decide which carries this video:
   - **Words lead** (review, vlog to camera, reaction): pick passages from
     the transcript as in podcast mode: a claim, a result, a verdict, a
     punchline. Use the filmstrips to check that something worth watching is
     on screen while it is said.
   - **Pictures lead** (events, travel, anything with little talk): pick
     from the scout filmstrips as in gameplay mode: a reveal, a fall, a
     before-and-after, a crowd reaction. Use the transcript only for
     captions.
   - If transcription is not possible (exit code 3, or nobody speaks), carry
     on with pictures only and `"captions": false`.
3. Strong general-video moments: a reveal or result shown early, a
   before/after, a verdict, a reaction, a mistake.
4. Set times so the clip opens on the interesting thing itself. For a
   reveal, start 5–10 s before it; for a verdict, start on its first
   sentence.

## Framing

Check a filmstrip of each candidate (`peek.py --range`), then:

| Shot | Layout |
|---|---|
| A person talking to camera | `auto`, or run `track.py` if the shot changes or there are two people |
| One clear subject in the middle | `center` |
| Subject off to one side, or moving | `center` with `"focus_x"`, or a short `"focus_path"` with `"focus_mode": "pan"` |
| Wide scenery, a group, text on screen | `blur` with `"zoom": 1.5–1.9` and `"hook_hold": true` |

Prefer a layout that fills the screen. Fall back to `blur` when a clip mixes
shots that no single crop serves.

## Edit

Read `references/editing.md`.

- `"edit": "premium"` by default; `story` when a person talking carries the
  clip; `hype` for events and fast action; `clean` for calm content.
- `"tighten": true` when the clip is mostly talk; `false` when the pictures
  or the natural sound carry it.
- One or two beats on the reveal or the reaction, with a callout only when
  it adds something the picture does not already say.
