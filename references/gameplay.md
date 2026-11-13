# Gameplay mode

The moment is in the action and the reaction, not in a transcript. A good
gameplay Short shows a situation, then something happens: a multi-kill, a
clutch, a fail, a win screen, a jump scare.

## Find the moments

1. Run `scout.py`. It ranks the busiest stretches and saves a filmstrip of
   each in `<workdir>/scout/`.
2. Open every filmstrip, and `end.jpg`. Read them like a comic strip:
   - **Keep** stretches where the frames show a fight, a chase, a result
     screen, or a kill feed filling up.
   - **Drop** menus, loading screens, the lobby, looting, long drives, and
     stretches that are loud only because of music.
   - **The ending** almost always holds the win or the death. If `end.jpg`
     shows a result screen, the last fight before it is a candidate even if
     scout ranked it low.
3. Read what the game tells you on screen: the kill feed and kill counter,
   the health bar (low health = tension), the players-alive counter, banners
   such as "double kill" or "winner". Use these for the hook and the score,
   and only claim what the frames show.
4. For each stretch you keep, set exact times. Scout's `loudest_at` is
   usually the peak. Begin 8–20 s before it so the viewer sees the situation,
   and end 2–4 s after the result lands. When you need to see more closely,
   use `peek.py --range <start>-<end> --n 8`.
5. `analyze_audio.py` helps when the video has a commentator or streamer: its
   peaks are their shouts and laughs. In a video that is gunfire from start
   to finish it adds little; trust scout and the frames.

## Facecam and commentary

While looking at the filmstrips, note:

- **Is there a facecam, and where?** If yes, get its box with
  `peek.py --at <t> --grid` and read x, y, w, h off the pixel labels.
- **Does anyone talk?** If there is a streamer or commentator, run
  `transcribe.py` and use captions. If the sound is only the game and music,
  skip transcription and set `"captions": false` on every clip.

## Framing

| Situation | Layout |
|---|---|
| Facecam present | `split` with the `facecam` box: face on top, game below |
| No facecam, action in the middle (most shooters, racing) | `center`. Fills the whole screen, which is what gameplay Shorts need |
| The edges matter (kill feed, minimap, health bar are part of the story) | `blur` with `"zoom": 1.6–2.0`. Keeps more of the width, at the cost of a smaller picture |
| Action off to one side | `center` with `"focus_x"` (0.3 = left of middle, 0.7 = right) |

Default to `center`. `blur` below zoom 1.6 leaves the game in a small band
with blur above and below, which looks weak on a phone. If unsure, render
`--preview` drafts of one clip in two layouts and compare frames.

## Render settings

- `"tighten": false` always. A quiet second before the action is the tension.
- Caption style `neon` or `fire` suits gameplay; ask if the user has a look.
- `--progress` works well for clips over 25 s.
- Hooks are short and concrete: "1 HP. Four enemies.", "Last circle, no
  cover", "He never saw the grenade".

## Post copy

Name the game in the first hashtag. Titles state what happens, not how
amazing it is.
