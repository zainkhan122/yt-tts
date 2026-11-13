#!/usr/bin/env python3
"""Isolate the video viewport inside a phone-player screenshot.

    python3 tools/ref_crop.py uploads/image-3.png --out ref/ref-A-3.viewport.png

A reference screenshot is not the short. It is a phone player: letterbox bars, a play button,
a scrubber, a caption burn-in. Measuring the screenshot copies the phone. This finds the largest
rectangle that is not the player's own chrome, crops to it, and reports what was cut — so the
numbers in ref_measure.py describe the video, not the device.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image


def chrome_colour(a: np.ndarray, pad: int = 4) -> np.ndarray:
    ring = np.concatenate([a[:pad].reshape(-1, 3), a[-pad:].reshape(-1, 3),
                           a[:, :pad].reshape(-1, 3), a[:, -pad:].reshape(-1, 3)])
    q = (ring // 6 * 6).astype(int)
    vals, counts = np.unique(q, axis=0, return_counts=True)
    return vals[counts.argmax()].astype(np.float32)


def viewport(a: np.ndarray, tol: float = 10.0) -> tuple[int, int, int, int, float]:
    """bbox of everything that is not the surrounding chrome colour."""
    bg = chrome_colour(a)
    d = np.abs(a - bg).max(axis=2)
    content = d > tol
    # Ignore thin sticky chrome: require a row/col to have real content in it.
    rows = content.mean(axis=1) > 0.02
    cols = content.mean(axis=0) > 0.02
    ys, xs = np.where(rows)[0], np.where(cols)[0]
    if len(ys) == 0 or len(xs) == 0:
        H, W = a.shape[:2]
        return 0, 0, W, H, 1.0
    y0, y1, x0, x1 = ys[0], ys[-1] + 1, xs[0], xs[-1] + 1
    return int(x0), int(y0), int(x1), int(y1), float(content.mean())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("src", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--tol", type=float, default=10.0)
    args = ap.parse_args()

    im = Image.open(args.src).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    x0, y0, x1, y1, _ = viewport(a, args.tol)
    W, H = im.size
    crop = im.crop((x0, y0, x1, y1))
    cw, ch = crop.size
    print(f"{args.src.name}: screenshot {W}x{H} -> viewport {cw}x{ch} "
          f"at ({x0},{y0}) aspect {cw / ch:.4f}  "
          f"[cut L{x0} T{y0} R{W - x1} B{H - y1}]")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        crop.save(args.out)
        print(f"  wrote {args.out}")


if __name__ == "__main__":
    main()
