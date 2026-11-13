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

## Framing

Look at a contact sheet (`peek.py --at`) of each candidate before choosing:

| Shot | Layout |
|---|---|
| One speaker on camera | `auto` or `speaker` |
| Two people in a wide shot, both talk in the clip | `blur` with `"zoom": 1.3` so neither is cut off |
| Two people in a wide shot, one talks in the clip | `center` with `"focus_x"` on the speaker (read it off the frame: 0.25 is the left quarter) |
| The edit cuts between single-speaker cameras | `auto`; the face detector samples across the clip |
| Screen share or slides | `blur` with `"zoom": 1.0–1.3` |

## Render settings

- `"tighten": true`: removes silences longer than 0.7 s and makes talk
  noticeably faster to watch.
- Captions on, always. Style `bold` is the default; `clean` suits calm or
  business content.
- Hook line in the speaker's language. For Malayalam, write the hook in
  Malayalam script and tell the user the captions need a read-through.
- If the captions show a wrong name or term, fix the words in
  `transcript.json` for that time range and re-render with `--only`.

## Post copy

The title is the claim in the clip, rephrased. Tag the guest's name and the
topic rather than generic tags.
