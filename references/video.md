# Video mode (general)

For everything that is neither a podcast nor gameplay: vlogs, tutorials,
reviews, events, sports, travel, cooking, product demos. Moments can come
from the words, the pictures, or both, so use both tools and let the video
tell you which matters more.

## Find the moments

1. Run `transcribe.py` and `scout.py`. Read `transcript.txt` in full and open
   the scout filmstrips.
2. Decide which carries this video:
   - **Words lead** (tutorial, review, vlog to camera): pick passages from
     the transcript as in podcast mode: a claim, a result, a tip, a
     punchline. Use the filmstrips to check that something worth watching is
     on screen while it is said.
   - **Pictures lead** (sports, events, travel, anything with little talk):
     pick from the scout filmstrips as in gameplay mode: a goal, a reveal,
     a fall, a before-and-after. Use the transcript only for captions.
   - If transcription is not possible (exit code 3, or nobody speaks), carry
     on with pictures only and `"captions": false`.
3. Strong general-video moments: a reveal or result shown early, a
   before/after, a single tip that stands alone, a reaction, a mistake.
   Tutorials clip best as "one tip, start to finish".
4. Set times so the clip opens on the interesting thing itself. For a
   reveal, start 5–10 s before it; for a tip, start on its first sentence.

## Framing

Check a filmstrip of each candidate (`peek.py --range`), then:

| Shot | Layout |
|---|---|
| A person talking to camera | `auto` |
| Wide scenery, a group, a screen recording, text on screen | `blur` with `"zoom": 1.2–1.6` |
| One clear subject in the middle | `center` |
| Subject off to one side | `center` with `"focus_x"` |

When a clip mixes shots, `blur` is the safe choice: nothing is cut off.

## Render settings

- `"tighten": true` when the clip is mostly talk; `false` when the pictures
  or the natural sound carry it.
- Caption style `bold` by default, `clean` for calm or instructional
  content.
