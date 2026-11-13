#!/usr/bin/env python3
"""Find the loud, exciting moments in a video's audio (shouts, laughter,
explosions, crowd noise). This is the main signal for gameplay, where the
best moments are often not in the words at all.

Usage: python analyze_audio.py VIDEO --out WORKDIR [--top 25]

Writes WORKDIR/audio_peaks.json and prints a table:
  time | lift (dB above the surrounding minute) | how long the burst lasts
"""
import argparse
import json
import os
import subprocess

import numpy as np

SR = 8000
WIN = 0.5


def ts(t):
    t = int(t)
    return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}" if t >= 3600 \
        else f"{t // 60:02d}:{t % 60:02d}"


def loudness(video):
    """Return (db, lift, seconds): loudness per 0.5 s window, and how far each
    window rises above the median of the minute around it."""
    raw = subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-i", video, "-vn", "-ac", "1",
         "-ar", str(SR), "-f", "s16le", "-"],
        capture_output=True, check=True).stdout
    pcm = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768
    n = int(SR * WIN)
    frames = pcm[:len(pcm) // n * n].reshape(-1, n)
    db = 20 * np.log10(np.sqrt((frames ** 2).mean(axis=1)) + 1e-6)

    # Smooth to 1.5 s, then compare with the median of the surrounding minute.
    k = 3
    smooth = np.convolve(db, np.ones(k) / k, mode="same")
    half = int(30 / WIN)
    base = np.array([np.median(smooth[max(0, i - half):i + half + 1])
                     for i in range(len(smooth))])
    return db, smooth - base, len(pcm) / SR


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--out", required=True)
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--min-gap", type=float, default=20,
                    help="seconds between reported peaks")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    db, lift, seconds = loudness(args.video)

    order = np.argsort(-lift)
    peaks, gap = [], int(args.min_gap / WIN)
    for i in order:
        if lift[i] < 4:
            break
        if any(abs(i - p) < gap for p in peaks):
            continue
        peaks.append(int(i))
        if len(peaks) >= args.top:
            break

    rows = []
    for i in sorted(peaks):
        a = b = i
        while a > 0 and lift[a - 1] > lift[i] / 2:
            a -= 1
        while b < len(lift) - 1 and lift[b + 1] > lift[i] / 2:
            b += 1
        rows.append({"t": round(i * WIN, 1), "time": ts(i * WIN),
                     "lift_db": round(float(lift[i]), 1),
                     "burst_start": round(a * WIN, 1),
                     "burst_end": round((b + 1) * WIN, 1)})

    quiet = float(np.percentile(db, 10))
    result = {"duration": round(seconds, 1),
              "median_db": round(float(np.median(db)), 1),
              "quiet_floor_db": round(quiet, 1), "peaks": rows}
    with open(os.path.join(args.out, "audio_peaks.json"), "w") as fh:
        json.dump(result, fh, indent=1)

    print(f"duration {ts(result['duration'])}, {len(rows)} peaks "
          f"(strongest first is NOT the order below; sorted by time)")
    print("time     lift_dB  burst")
    for r in rows:
        print(f"{r['time']:>8} {r['lift_db']:>7}  "
              f"{ts(r['burst_start'])}-{ts(r['burst_end'])}")


if __name__ == "__main__":
    main()
