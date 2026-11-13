# Editing: making a clip look made, not cut

A raw cut with a label on top reads as low effort. What separates a clip an
experienced editor made is a handful of deliberate choices: the frame is
full, the colour has punch, the picture moves on the moments that matter, the
sound backs those moments up, and the text is designed and timed. `render.py`
does the mechanics; your job is the choices. Read this before writing
`clips.json`.

## Pick the edit

`"edit"` on a clip (or `--edit` for all) sets the whole treatment:

| Edit | Use for | What it does |
|---|---|---|
| `hype` | Gameplay, sports, anything fast | Vivid grade, slow push-in, punch + shake + flash with a bass thump on each beat, condensed all-caps headline, progress bar |
| `premium` | General video, calmer gameplay | Punchy grade, slow push-in, punch-in with a soft thump on each beat, bold headline |
| `story` | Podcasts, interviews, talking head | Soft grade, zoom cuts on sentence changes, animated captions, a whoosh under the headline |
| `clean` | Business, tutorials, serious topics | Soft grade and animated text only; no zooms, no sound effects |
| `raw` | When the user wants it untouched | Plain cut, boxed headline, static captions |

Default is `premium`. If the user names a look ("hype edit", "keep it
clean"), that settles it.

## Beats: where the picture reacts

A beat is a moment the edit should land on: the shot, the goal, the
punchline, the reveal. On a beat the picture punches in (and in `hype`,
shakes and flashes) with a thump underneath.

- `"beats": "auto"` (the default in `hype` and `premium`) finds the hardest
  jumps in the sound: at most one per ~7 s, none under the headline. Good
  enough for most action clips.
- When you can see or read the exact moment, say so. It is always better
  than auto:

```json
"beats": ["auto",
  {"t": 1028.2, "fx": ["flash", "punch"], "text": "#1 Winner"},
  {"t": 771.5, "fx": "slowmo", "len": 1.2}]
```

`t` is in source-video seconds, like `start` and `end`. `"auto"` inside the
list keeps the found beats and adds yours.

| fx | Effect | Use it for |
|---|---|---|
| `punch` | Quick zoom in that settles back | Any hit, kill, goal, punchline |
| `shake` | Short camera shake | Explosions, heavy impacts, a clutch |
| `flash` | Brief white flash | A result screen, a cut to the payoff |
| `slowmo` | Half speed for `len` seconds | The one best moment of the clip, once |

`"text"` on a beat pops a callout word on screen for about a second
("CLUTCH", "1 HP", "GOAL"). Rules for callouts:

- Only what the frames or the transcript show. Never invent a kill count.
- One to three words. At most two or three callouts per clip.
- Slow motion at most once per clip, on the payoff. More than that reads as
  padding.

Restraint matters. Three well-placed beats in 30 seconds feel edited; ten
feel like a filter.

## Headline

The `hook` is the headline for the first 3.5 seconds.

- 3–8 words. Put `*stars*` around the one or two words that carry it; they
  take the accent colour: `"He quit a *40 lakh* job"`.
- It must be true to the clip. Curiosity, not a lie.
- `"hook_hold": true` keeps it up for the whole clip. Use that with the
  `blur` layout, where the band above the picture would otherwise sit empty.
- `stack` layout: keep the hook to one short line; it sits over the top
  speaker.

## Captions

- Talk needs captions; most viewers watch without sound at first. Gameplay
  with no voice needs none (`"captions": false`).
- Styles: `bold` (default), `clean` (calm content), `neon` and `fire`
  (gameplay, hype).
- The transcript is the caption. If a name or term is wrong, fix it in
  `transcript.json` and re-render with `--only`.

## Framing

Fill the screen. A small picture floating in blur is the clearest sign of a
low-effort clip.

- `center` or `speaker` first. `blur` only when the edges really matter, and
  then with `"zoom": 1.6` or more and `"hook_hold": true`.
- Two people in one wide shot: run `track.py`, then `stack` (both on screen)
  or `speaker` with the `focus_path` it writes (cuts to whoever is talking).
- Check a frame of every clip. A cropped-off face or a caption over the
  action undoes everything else.

## Closing and branding

- `"outro": "Follow for more"` (or `--outro`) pops a tag over the last
  1.6 s. Skip it when the clip ends on a strong line or image; let that be
  the ending.
- `--watermark "@name"` adds a small, see-through channel tag. Ask for the
  handle once; never invent one.
- `--progress` shows a thin bar along the top (on by default in `hype`).
- End the clip on the payoff. Check the last two seconds with
  `peek.py --range`: source videos often end with the creator's own end
  card, and a clip that runs into it looks careless.

## Where text can go

The apps cover parts of the frame with their own buttons and captions. The
renderer keeps its text inside the free area, roughly x 60–890 and
y 290–1250 of the 1080x1920 frame (the bottom third and the right edge
belong to the app). Nothing to do unless you override positions: just know
that the lower third of the picture will be partly hidden, so the subject
should not live there.

## What is evidence and what is craft

Be straight with the user if they ask what "works":

- Supported by platform guidance: state the point within the first 3
  seconds, use captions or on-screen text, use sound, keep it vertical and
  sharp. Clips of roughly 20–35 s are a safe default length.
- Craft, not proof: how often to zoom, which sound effect, loop endings.
  These follow editing convention. They make a clip feel finished; nobody
  can promise they raise views.

## After the render

1. Look at a frame from the headline, from one beat, and from the last
   second of each clip.
2. If a `--preview` pass would have caught it (framing, a callout at the
   wrong time), use `--preview` next time before the full render.
3. If the session has an `effects` skill and the clip is a talking head,
   offer it as an extra step on the finished file. It is a separate skill;
   do not assume it is installed.
