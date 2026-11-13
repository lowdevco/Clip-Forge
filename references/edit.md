# Edit mode

The user already has the clip (or knows the exact times) and wants the
edit: `/clip-edit <file or link> [what they want]`. There is no search for
moments and no scored table.

## Steps

1. Get the video as in step 2 of the main instructions. A short file the
   user attached is used as it is.
2. Work out the span:
   - A finished short clip: the whole file is the clip (`start` 0, `end` =
     its length).
   - Times given ("from 12:30 to 13:05"): use them.
   - A long video and no times: ask which part, or offer to switch to one
     of the finding modes.
3. Look at it: `peek.py --range <start>-<end> --n 12`. Note what kind of
   footage it is, where the subject sits, whether anyone talks, and where
   the key moment falls.
4. If someone talks, run `transcribe.py` for captions. If there are people
   in a wide shot, run `track.py`.
5. Read `references/editing.md` and write `clips.json` with a real edit
   plan: layout, edit preset, hook with `*accent*` words, beats on the
   moments you saw, a callout or two where the picture supports it.
6. If the source is already vertical (9:16), use `"layout": "center"`; it
   passes through at full frame.
7. Say in two or three lines what you plan (edit, layout, beats, headline),
   then render. A plan the user can read in ten seconds does not need an
   approval stop unless they asked for one. Use `--preview` first when the
   framing is a guess.
8. Check frames, hand over the file, and offer changes: another edit
   preset, different beats, a new headline, a caption style.

## Reading what the user asked for

| They say | Do |
|---|---|
| "make it pop", "hype", "like a gaming montage" | `"edit": "hype"`, style `fire` or `neon` |
| "clean", "professional", "for LinkedIn" | `"edit": "clean"`, style `clean`, no outro |
| "podcast style", "like the big podcast clips" | `"edit": "story"`, `stack` or `speaker` via `track.py`, style `bold` |
| "just captions" | `"edit": "clean"`, `"grade": "none"`, no hook |
| "no captions", "no text" | `"captions": false`, omit `hook` |
| "slow-mo on the …" | a `slowmo` beat at that moment |
| "add my handle" | `--watermark "@theirs"` (ask for it if not given) |
