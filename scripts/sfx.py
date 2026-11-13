#!/usr/bin/env python3
"""Make the small sound effects the renderer mixes in. They are synthesised
here, so the skill ships no audio files and has no licensing questions.

  boom    low thump for an impact or a punch-in zoom
  whoosh  airy sweep for a title or a transition
  pop     short blip for a callout

Usage: python sfx.py OUTDIR   (writes boom.wav, whoosh.wav, pop.wav)
"""
import os
import sys
import wave

import numpy as np

SR = 48000


def _save(path, x):
    x = np.tanh(np.asarray(x, dtype=np.float64) * 1.2)      # soft clip
    x = x / (np.abs(x).max() + 1e-9) * 0.89
    pcm = (x * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def _band_noise(n, lo, hi, rng):
    spec = np.fft.rfft(rng.standard_normal(n))
    freq = np.fft.rfftfreq(n, 1 / SR)
    spec[(freq < lo) | (freq > hi)] = 0
    out = np.fft.irfft(spec, n)
    return out / (np.abs(out).max() + 1e-9)


def boom():
    n = int(SR * 0.75)
    t = np.arange(n) / SR
    freq = 38 + 62 * np.exp(-t * 14)                 # 100 Hz falling to 38 Hz
    body = np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-t * 5.5)
    rng = np.random.default_rng(7)
    click = _band_noise(n, 80, 900, rng) * np.exp(-t * 70) * 0.5
    fade = np.minimum(1, (n - np.arange(n)) / (SR * 0.05))
    return (body + click) * fade


def whoosh():
    n = int(SR * 0.6)
    t = np.arange(n) / SR
    rng = np.random.default_rng(11)
    air = _band_noise(n, 500, 7000, rng)
    low = _band_noise(n, 150, 900, rng)
    peak = 0.62                                       # swell, then fall away
    env = np.where(t / 0.6 < peak, (t / 0.6 / peak) ** 2.2,
                   ((1 - t / 0.6) / (1 - peak)) ** 1.6)
    return (air * 0.8 + low * 0.5) * env


def pop():
    n = int(SR * 0.09)
    t = np.arange(n) / SR
    freq = 520 + 600 * np.exp(-t * 60)
    return np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-t * 45)


def write_all(outdir):
    os.makedirs(outdir, exist_ok=True)
    paths = {}
    for name, fn in (("boom", boom), ("whoosh", whoosh), ("pop", pop)):
        paths[name] = os.path.join(outdir, f"{name}.wav")
        _save(paths[name], fn())
    return paths


if __name__ == "__main__":
    print(write_all(sys.argv[1] if len(sys.argv) > 1 else "."))
