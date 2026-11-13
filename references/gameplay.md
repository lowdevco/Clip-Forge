# Gameplay mode

The moment is in the action and the reaction, not in a transcript. A good
gameplay Short shows a situation, then something happens: a multi-kill, a
clutch, a fail, a win screen, a jump scare.

## Find the moments

1. Look at one mid-game frame with a grid:
   `peek.py <video> --at <t> --grid --out <workdir>/grid.jpg`. Note where
   the kill feed (or score, or event log) sits and whether there is a
   facecam. Read the kill-feed box as `x,y,w,h` in source pixels.
2. Run scout, with the kill-feed box if the game has one:

   ```
   python scripts/scout.py <video> --out <workdir> --roi x,y,w,h
   ```

   It ranks the busiest stretches by sound and motion and saves a filmstrip
   of each in `<workdir>/scout/`. With `--roi`, every change in the kill
   feed counts as an event: windows with several are multi-kills and
   fights, and the exact times are in `scout.json` under `roi_events`.
3. Open every filmstrip, and `end.jpg`. Read them like a comic strip:
   - **Keep** stretches where the frames show a fight, a chase, a result
     screen, or a kill feed filling up.
   - **Drop** menus, loading screens, the lobby, looting, long drives, and
     stretches that are loud only because of music.
   - **The ending** almost always holds the win or the death. If `end.jpg`
     shows a result screen, the last fight before it is a candidate even if
     scout ranked it low.
4. Read what the game tells you on screen: the kill feed and kill counter,
   the health bar (low health = tension), the players-alive counter, banners
   such as "double kill" or "winner". `peek.py --crop x,y,w,h` enlarges a
   region so small text is readable. Use these for the hook, the callouts
   and the score, and only claim what the frames show.
5. For each stretch you keep, set exact times. Begin 8–20 s before the peak
   so the viewer sees the situation, and end 2–4 s after the result lands.
   Check the last seconds with `peek.py --range`: do not run into the
   creator's own end card or a menu.
6. `analyze_audio.py` helps when the video has a commentator or streamer:
   its peaks are their shouts and laughs. In a video that is gunfire from
   start to finish it adds little; trust scout and the frames.

## Facecam and commentary

- **Facecam?** If yes, get its box from the grid frame for the `split`
  layout.
- **Does anyone talk?** If there is a streamer or commentator, run
  `transcribe.py` and use captions. If the sound is only the game and music,
  skip transcription and set `"captions": false` on every clip.

## Framing

| Situation | Layout |
|---|---|
| Facecam present | `split` with the `facecam` box: face on top, game below |
| No facecam, action in the middle (most shooters, racing) | `center`. Fills the whole screen, which is what gameplay Shorts need |
| Action off to one side | `center` with `"focus_x"` (0.3 = left of middle, 0.7 = right) |
| The edges are the story (a scoreboard, a minimap) | `blur` with `"zoom": 1.6–2.0` and `"hook_hold": true` |

Default to `center`. A small picture floating in blur looks low-effort on a
phone.

## Edit

Read `references/editing.md`. For gameplay:

- `"edit": "hype"`, caption style `fire` or `neon`.
- Leave `"beats"` unset for automatic beats on the loudest hits, or give
  your own where you can see the exact moment. Add `"auto"` to the list to
  keep both.
- Callouts from what the screen shows: "SQUAD WIPE", "1 HP", "#1 WINNER".
- `slowmo` once, on the best kill or the winning moment.
- `"tighten": false` always. A quiet second before the action is the
  tension.
- Hooks are short and concrete: "1 HP. *Four enemies.*", "Last circle,
  *no cover*", "He never saw the *grenade*".

## Post copy

Name the game in the first hashtag. Titles state what happens, not how
amazing it is.
