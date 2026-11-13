# Sports mode

Match footage and broadcasts: football, cricket, basketball, esports
broadcasts with a caster, fights, racing. The moment is a scoring play, a
save, a wicket, a knockout, a finish. Two signals find almost all of them:
the crowd and commentator getting loud and staying loud, and the scoreboard
changing.

## Find the moments

1. Look at one frame with a grid to locate the scoreboard:
   `peek.py <video> --at <a time during play> --grid --out <workdir>/grid.jpg`.
   Read its box as `x,y,w,h` in source pixels. Skip this if there is no
   on-screen score.
2. Run scout in sports mode, with the scoreboard box if you have one:

   ```
   python scripts/scout.py <video> --out <workdir> --kind sports --len 40 --roi x,y,w,h
   ```

   `--kind sports` ranks by sustained loudness (a roar lasts; a whistle does
   not). `region changes` counts how often the scoreboard changed in each
   window, and `scout.json` lists every change time under `roi_events`.
3. A scoreboard change means something happened shortly **before** it:
   usually 5–25 s earlier, since graphics update after the play. For each
   change, look back with `peek.py --range <t-30>-<t+5> --n 10`.
4. Read the score before and after to know what happened:
   `peek.py <video> --at <before>,<after> --crop x,y,w,h --out <workdir>/score.jpg`.
   Use the real score in the hook and the callout.
5. Open the scout filmstrips for the loud windows with no score change:
   near misses, saves, fouls and celebrations live there.
6. Broadcasts replay the best moments. If a filmstrip shows the same play
   twice, cut the clip from the live play and stop before the replay, or
   use the replay angle on its own if it shows the play better.
7. Run `transcribe.py` only if the commentary is worth captioning. For most
   sports clips the picture and a headline are enough; captions of fast
   commentary clutter the frame.

## Timing

- Start with the build-up: 6–12 s before the scoring moment, at the pass,
  run-up or delivery that begins it.
- End on the celebration or the reaction, 3–5 s after, before the replay.
- 15–35 s is typical.

## Framing

| Shot | Layout |
|---|---|
| Wide broadcast camera, play moves across the field | `blur` with `"zoom": 1.6–1.9` and `"hook_hold": true`. A tight crop would lose the ball |
| Play stays in one area (penalty, free throw, a wicket, a ring) | `center`, with `"focus_x"` on the area |
| Play moves steadily one way and you can see where | `center` with a `"focus_path"` of two or three points and `"focus_mode": "pan"` |
| Close-up reaction or celebration | `center` or `speaker` |

For a `focus_path`, read the subject's position off a filmstrip: 0 is the
left edge of the source frame, 1 the right edge. A few points are enough;
do not try to track the ball frame by frame.

## Edit

- `"edit": "hype"`.
- One beat on the scoring moment with `["punch", "flash"]` and a callout
  with the real result: "GOAL", "2–1", "OUT", "KO".
- `slowmo` once, on the moment of contact, if the picture is clear enough.
- Hooks state the stakes: "90th minute. *One chance.*", "Needs *6 off 1*".

## Rights

Broadcast sport is almost always owned by a league or broadcaster and is
taken down quickly. Say this once if the footage is clearly a broadcast,
then carry on with what the user asked.
