#!/usr/bin/env python3
"""Save a contact sheet of frames so you can LOOK at moments before choosing
them (is something actually happening? is there a facecam, and where?).

Usage:
  python peek.py VIDEO --at 75,312.5,1040 --out WORKDIR/peek.jpg [--grid]
  python peek.py VIDEO --range 998-1032 --n 8 --out WORKDIR/strip.jpg

--range takes N evenly spaced frames from START-END (seconds): a filmstrip
that shows how one moment plays out from start to finish.
--grid draws 10% guide lines with pixel labels on each frame; use it to read
off a facecam box [x, y, w, h] in source pixels for the "split" layout.
"""
import argparse

import cv2
import numpy as np


def spread(start, end, n):
    """N times evenly spaced inside start-end, away from the very edges."""
    n = max(int(n), 1)
    return [start + (end - start) * (i + 0.5) / n for i in range(n)]


def make_sheet(video, times, out, grid=False, cols=3, tile_w=None):
    cap = cv2.VideoCapture(video)
    tiles = []
    for t in times:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, frame = cap.read()
        if not ok:
            continue
        H, W = frame.shape[:2]
        if grid:
            for i in range(1, 10):
                x, y = W * i // 10, H * i // 10
                cv2.line(frame, (x, 0), (x, H), (0, 255, 255), 2)
                cv2.line(frame, (0, y), (W, y), (0, 255, 255), 2)
                cv2.putText(frame, str(x), (x + 4, 28), 0, 0.9, (0, 0, 0), 5)
                cv2.putText(frame, str(x), (x + 4, 28), 0, 0.9, (0, 255, 255), 2)
                cv2.putText(frame, str(y), (4, y - 6), 0, 0.9, (0, 0, 0), 5)
                cv2.putText(frame, str(y), (4, y - 6), 0, 0.9, (0, 255, 255), 2)
        tw = tile_w or (960 if grid else 640)
        tile = cv2.resize(frame, (tw, int(H * tw / W)))
        label = f"{int(t) // 60:02d}:{t % 60:04.1f}  ({W}x{H})"
        cv2.putText(tile, label, (10, tile.shape[0] - 14), 0, 0.8, (0, 0, 0), 5)
        cv2.putText(tile, label, (10, tile.shape[0] - 14), 0, 0.8,
                    (255, 255, 255), 2)
        tiles.append(tile)
    cap.release()
    if not tiles:
        return None
    cols = 1 if grid else min(cols, len(tiles))
    blank = np.zeros_like(tiles[0])
    while len(tiles) % cols:
        tiles.append(blank)
    rows = [np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]
    cv2.imwrite(out, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 82])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--at", help="comma-separated seconds")
    ap.add_argument("--range", dest="span", help="START-END in seconds")
    ap.add_argument("--n", type=int, default=8, help="frames for --range")
    ap.add_argument("--out", required=True)
    ap.add_argument("--grid", action="store_true")
    ap.add_argument("--cols", type=int)
    args = ap.parse_args()

    if args.span:
        a, b = (float(x) for x in args.span.split("-", 1))
        times, cols = spread(a, b, args.n), args.cols or 4
    elif args.at:
        times, cols = [float(x) for x in args.at.split(",")], args.cols or 3
    else:
        raise SystemExit("give --at or --range")
    if not make_sheet(args.video, times, args.out, args.grid, cols):
        raise SystemExit("no frames could be read")
    print(args.out)


if __name__ == "__main__":
    main()
