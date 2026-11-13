#!/usr/bin/env python3
"""Build a word-timed transcript for a video.

Usage:
  python transcribe.py VIDEO --out WORKDIR [--subs FILE] [--lang en|ml|auto]
                       [--engine auto|subs|faster-whisper|sherpa] [--model small]

Order tried in "auto": subtitle file (--subs, or one sitting next to the video)
-> faster-whisper -> sherpa-onnx (models come from GitHub, so it also works
where Hugging Face is blocked).

Writes WORKDIR/transcript.json  {"language","source","words":[{"s","e","w"}],
                                 "segments":[{"start","end","text"}]}
and    WORKDIR/transcript.txt   compact "[mm:ss] text" lines for reading.
Exit code 3 means no transcript could be made (use audio-only mode).
"""
import argparse
import glob
import html
import json
import os
import re
import subprocess
import sys
import tarfile
import urllib.request

CACHE = os.path.join(os.path.expanduser("~"), ".cache", "clip-forge")
GH = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/"


# ---------- helpers ----------------------------------------------------------
def spread_words(text, start, end):
    """Give each word in a timed line a share of its time, by length."""
    toks = text.split()
    if not toks or end <= start:
        return []
    total = sum(len(t) + 1 for t in toks)
    out, t = [], start
    for tok in toks:
        d = (end - start) * (len(tok) + 1) / total
        out.append({"s": round(t, 3), "e": round(t + d, 3), "w": tok})
        t += d
    return out


def words_to_segments(words, max_len=9.0, gap=0.8):
    segs, cur = [], []
    for w in words:
        if cur and (w["s"] - cur[-1]["e"] > gap
                    or w["e"] - cur[0]["s"] > max_len
                    or cur[-1]["w"][-1:] in ".?!"):
            segs.append(cur)
            cur = []
        cur.append(w)
    if cur:
        segs.append(cur)
    return [{"start": s[0]["s"], "end": s[-1]["e"],
             "text": " ".join(x["w"] for x in s)} for s in segs]


def ts(t):
    t = int(t)
    return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}" if t >= 3600 \
        else f"{t // 60:02d}:{t % 60:02d}"


# ---------- subtitle parsers -------------------------------------------------
def parse_json3(path):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    words = []
    for ev in data.get("events", []):
        segs = [s for s in ev.get("segs", []) if s.get("utf8", "").strip()]
        if not segs:
            continue
        t0 = ev.get("tStartMs", 0) / 1000
        t1 = t0 + ev.get("dDurationMs", 0) / 1000
        timed = len(segs) > 1 or "tOffsetMs" in segs[0]
        if timed:  # auto captions: one seg per word, each with its own offset
            starts = [t0 + s.get("tOffsetMs", 0) / 1000 for s in segs]
            for i, s in enumerate(segs):
                end = starts[i + 1] if i + 1 < len(segs) else min(t1, starts[i] + 1.2)
                words += spread_words(s["utf8"].strip(), starts[i],
                                      max(end, starts[i] + 0.05))
        else:
            words += spread_words(segs[0]["utf8"].replace("\n", " "), t0, t1)
    return words


TIME = re.compile(r"(?:(\d+):)?(\d{1,2}):(\d{2})[.,](\d{3})")


def _sec(m):
    return int(m.group(1) or 0) * 3600 + int(m.group(2)) * 60 + int(m.group(3)) \
        + int(m.group(4)) / 1000


def parse_vtt_srt(path):
    with open(path, encoding="utf-8-sig") as fh:
        blocks = re.split(r"\n\s*\n", fh.read().replace("\r", ""))
    words, last_text = [], None
    for block in blocks:
        lines = [ln for ln in block.split("\n") if ln.strip()]
        idx = next((i for i, ln in enumerate(lines) if "-->" in ln), None)
        if idx is None:
            continue
        times = list(TIME.finditer(lines[idx]))
        if len(times) < 2:
            continue
        start, end = _sec(times[0]), _sec(times[1])
        text = " ".join(lines[idx + 1:])
        text = html.unescape(re.sub(r"<[^>]+>", "", text)).strip()
        # YouTube auto .vtt repeats the previous line in each rolling cue.
        if last_text and text.startswith(last_text):
            text = text[len(last_text):].strip()
        elif text == last_text:
            text = ""
        if text:
            words += spread_words(text, start, end)
            last_text = " ".join(lines[idx + 1:]).strip()
            last_text = html.unescape(re.sub(r"<[^>]+>", "", last_text))
    return words


def find_subs(video, lang):
    stem = os.path.splitext(video)[0]
    found = glob.glob(stem + ".*.json3") + glob.glob(stem + ".*.vtt") \
        + glob.glob(stem + ".*.srt") + glob.glob(stem + ".srt") \
        + glob.glob(stem + ".vtt")
    if not found:
        return None

    def rank(p):
        name = os.path.basename(p).lower()
        code = name[len(os.path.basename(stem)) + 1:].split(".")[0]
        score = 0
        if lang not in ("auto", None) and code.startswith(lang):
            score -= 10
        if code.endswith("-orig"):
            score -= 5          # original-language auto captions
        if name.endswith(".json3"):
            score -= 2          # carries per-word timing
        score += len(code)      # prefer "en" over "en-xx-yy" translations
        return score
    return sorted(found, key=rank)[0]


def from_subs(path):
    words = parse_json3(path) if path.endswith(".json3") else parse_vtt_srt(path)
    return words, f"subtitles:{os.path.basename(path)}"


# ---------- speech-to-text engines ------------------------------------------
def extract_wav(video, out):
    wav = os.path.join(out, "audio16k.wav")
    if not os.path.exists(wav):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video,
                        "-vn", "-ac", "1", "-ar", "16000", wav], check=True)
    return wav


def with_faster_whisper(video, out, lang, model):
    from faster_whisper import WhisperModel
    wav = extract_wav(video, out)
    wm = WhisperModel(model, device="auto", compute_type="auto")
    segments, info = wm.transcribe(
        wav, language=None if lang == "auto" else lang,
        word_timestamps=True, vad_filter=True)
    words = []
    for seg in segments:
        for w in seg.words or []:
            if w.word.strip():
                words.append({"s": round(w.start, 3), "e": round(w.end, 3),
                              "w": w.word.strip()})
        print(f"  ...{ts(seg.end)}", end="\r", file=sys.stderr)
    return words, f"faster-whisper:{model}", info.language


def _download(url, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if not os.path.exists(dest):
        print(f"downloading {os.path.basename(dest)} ...", file=sys.stderr)
        urllib.request.urlretrieve(url, dest + ".part")
        os.replace(dest + ".part", dest)
    return dest


def with_sherpa(video, out, lang, model):
    import wave

    import numpy as np
    import sherpa_onnx

    name = f"sherpa-onnx-whisper-{model}"
    mdir = os.path.join(CACHE, name)
    if not os.path.isdir(mdir):
        tar = _download(GH + name + ".tar.bz2",
                        os.path.join(CACHE, name + ".tar.bz2"))
        with tarfile.open(tar) as tf:
            try:
                tf.extractall(CACHE, filter="data")
            except TypeError:  # Python < 3.12
                tf.extractall(CACHE)
        os.remove(tar)
    vad_path = _download(GH + "silero_vad.onnx",
                         os.path.join(CACHE, "silero_vad.onnx"))
    rec = sherpa_onnx.OfflineRecognizer.from_whisper(
        encoder=os.path.join(mdir, f"{model}-encoder.int8.onnx"),
        decoder=os.path.join(mdir, f"{model}-decoder.int8.onnx"),
        tokens=os.path.join(mdir, f"{model}-tokens.txt"),
        language="" if lang == "auto" else lang, task="transcribe",
        num_threads=max(1, (os.cpu_count() or 2)))
    cfg = sherpa_onnx.VadModelConfig()
    cfg.silero_vad.model = vad_path
    cfg.silero_vad.min_silence_duration = 0.25
    cfg.silero_vad.max_speech_duration = 12
    cfg.sample_rate = 16000
    vad = sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=60)

    wav = extract_wav(video, out)
    words = []

    def drain():
        while not vad.empty():
            seg = vad.front
            start = seg.start / 16000
            samples = np.array(seg.samples, dtype=np.float32)
            vad.pop()
            stream = rec.create_stream()
            stream.accept_waveform(16000, samples)
            rec.decode_stream(stream)
            text = stream.result.text.strip()
            if text:
                words.extend(spread_words(text, start,
                                          start + len(samples) / 16000))
            print(f"  ...{ts(start)}", end="\r", file=sys.stderr)

    win = cfg.silero_vad.window_size
    with wave.open(wav) as wf:
        while True:
            raw = wf.readframes(win * 200)
            if not raw:
                break
            pcm = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
            for i in range(0, len(pcm) - win + 1, win):
                vad.accept_waveform(pcm[i:i + win])
            drain()
    vad.flush()
    drain()
    return words, f"sherpa-whisper:{model}", lang


# ---------- main -------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--out", required=True)
    ap.add_argument("--subs")
    ap.add_argument("--lang", default="auto")
    ap.add_argument("--engine", default="auto",
                    choices=["auto", "subs", "faster-whisper", "sherpa"])
    ap.add_argument("--model", default="small",
                    help="whisper size: tiny, base, small, medium (bigger = "
                         "slower and more accurate; use small+ for Malayalam)")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    words, source, language = [], None, args.lang
    errors = []
    if args.engine in ("auto", "subs"):
        subs = args.subs or find_subs(args.video, args.lang)
        if subs:
            words, source = from_subs(subs)
    if not words and args.engine in ("auto", "faster-whisper"):
        try:
            words, source, language = with_faster_whisper(
                args.video, args.out, args.lang, args.model)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"faster-whisper: {exc!r}")
    if not words and args.engine in ("auto", "sherpa"):
        try:
            words, source, language = with_sherpa(
                args.video, args.out, args.lang, args.model)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"sherpa-onnx: {exc!r}")

    if not words:
        print(json.dumps({"ok": False, "errors": errors,
                          "hint": "No subtitles and no working speech-to-text "
                                  "engine. Continue in audio-only mode, or "
                                  "install an engine (see check_setup.py)."},
                         indent=2))
        sys.exit(3)

    words.sort(key=lambda w: w["s"])
    segments = words_to_segments(words)
    if any("ഀ" <= ch <= "ൿ" for w in words[:400] for ch in w["w"]):
        language = "ml"
    with open(os.path.join(args.out, "transcript.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"language": language, "source": source, "words": words,
                   "segments": segments}, fh, ensure_ascii=False)
    with open(os.path.join(args.out, "transcript.txt"), "w",
              encoding="utf-8") as fh:
        for seg in segments:
            fh.write(f"[{ts(seg['start'])}] {seg['text']}\n")
    print(json.dumps({"ok": True, "source": source, "language": language,
                      "words": len(words), "segments": len(segments),
                      "exact_word_timing": "json3" in (source or "")
                      or "faster-whisper" in (source or ""),
                      "transcript_txt": os.path.join(args.out, "transcript.txt")},
                     indent=2))


if __name__ == "__main__":
    main()
