#!/usr/bin/env python3
"""Save a contact sheet of frames so you can LOOK at moments before choosing
them (is something actually happening? is there a facecam, and where?).

Usage: python peek.py VIDEO --at 75,312.5,1040 --out WORKDIR/peek.jpg [--grid]

--grid draws 10% guide lines with pixel labels on each frame; use it to read
off a facecam box [x, y, w, h] in source pixels for the "split" layout.
"""
import argparse

import cv2
import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--at", required=True, help="comma-separated seconds")
    ap.add_argument("--out", required=True)
    ap.add_argument("--grid", action="store_true")
    ap.add_argument("--cols", type=int, default=3)
    args = ap.parse_args()

    cap = cv2.VideoCapture(args.video)
    tiles = []
    for t in [float(x) for x in args.at.split(",") if x.strip()]:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, frame = cap.read()
        if not ok:
            continue
        H, W = frame.shape[:2]
        if args.grid:
            for i in range(1, 10):
                x, y = W * i // 10, H * i // 10
                cv2.line(frame, (x, 0), (x, H), (0, 255, 255), 2)
                cv2.line(frame, (0, y), (W, y), (0, 255, 255), 2)
                cv2.putText(frame, str(x), (x + 4, 28), 0, 0.9, (0, 0, 0), 5)
                cv2.putText(frame, str(x), (x + 4, 28), 0, 0.9, (0, 255, 255), 2)
                cv2.putText(frame, str(y), (4, y - 6), 0, 0.9, (0, 0, 0), 5)
                cv2.putText(frame, str(y), (4, y - 6), 0, 0.9, (0, 255, 255), 2)
        tw = 960 if args.grid else 640
        tile = cv2.resize(frame, (tw, int(H * tw / W)))
        label = f"{int(t) // 60:02d}:{t % 60:04.1f}  ({W}x{H})"
        cv2.putText(tile, label, (10, tile.shape[0] - 14), 0, 0.8, (0, 0, 0), 5)
        cv2.putText(tile, label, (10, tile.shape[0] - 14), 0, 0.8,
                    (255, 255, 255), 2)
        tiles.append(tile)
    if not tiles:
        raise SystemExit("no frames could be read")
    cols = 1 if args.grid else min(args.cols, len(tiles))
    blank = np.zeros_like(tiles[0])
    while len(tiles) % cols:
        tiles.append(blank)
    rows = [np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]
    cv2.imwrite(args.out, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 82])
    print(args.out)


if __name__ == "__main__":
    main()
