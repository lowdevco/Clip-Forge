# Tutorial mode

How-to and educational videos: coding, software walkthroughs, lessons,
explainers, cooking, repairs, reviews with a clear lesson. The clip that
works is **one idea, complete**: a single tip, fix or result that a viewer
can use without seeing the rest.

## Find the moments

1. Run `transcribe.py` and read `transcript.txt` in full. The transcript is
   required here; if it cannot be made, say what to install.
2. Mark every passage that is a complete unit:
   - one tip or shortcut, stated and shown
   - a mistake and its fix
   - a before and after
   - a surprising fact with its reason
   - a result worth showing first ("this is what we are building")
3. Drop passages that depend on earlier steps ("as we saw", "now go back to
   the file we made"), and setup with no payoff.
4. Lead with the result. If the passage builds up to something visible,
   start the clip a few seconds before the result appears, or pick the
   sentence that states the benefit ("this one setting halves your build
   time") as the opening line.
5. Check what is on screen with `peek.py --range`: the words and the picture
   must match. A tip explained over an unrelated screen does not clip well.

## Framing

| Shot | Layout |
|---|---|
| Screen recording with small text | `blur` with `"zoom": 1.5–2.2` and `"hook_hold": true`. Choose the zoom so the part being discussed is readable on a phone, and check a frame |
| Screen recording, action in one area | `center` with `"focus_x"` on that area |
| Screen plus a facecam corner | `split` with the facecam box: face on top, screen below |
| Presenter to camera | `auto` |
| Hands, a workbench, a pan on a stove | `center` |

Text on a shared screen is the hardest thing to keep readable in 9:16. If no
zoom makes it readable, say so and frame on the presenter instead.

## Edit

- `"edit": "clean"` by default; `story` if it is a presenter talking and a
  livelier feel suits the channel.
- `"tighten": true`: tutorials have long pauses while things load or type.
- Captions on, style `clean`.
- At most one beat, on the result, with a short callout ("FIXED", "3x
  faster") only when the screen shows it.
- Hooks promise the one thing: "Stop writing *for loops* for this",
  "The *one setting* that fixes blurry exports".

## Post copy

Title = the tip. Put the tool or topic name in the first hashtag. A caption
that restates the steps in one line helps people save the clip.
