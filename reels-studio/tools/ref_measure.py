#!/usr/bin/env python3
"""Measure a reference short's visual system from frames, in numbers, not adjectives.

    python3 tools/ref_measure.py uploads/*.png --out ref/pulse_ref.fingerprint.json

Why this exists: every previous attempt copied a reference by *describing* it ("dark, bold,
clean") and then rebuilt something that shared the adjectives but not the geometry. This prints
the geometry: where the type sits, how big it is, what the ground colour is, how much of the
frame is empty, and which single hue the accent is. A style file is then written from these
numbers, and QA can re-measure the render against them.

Everything is normalised to the 1080-wide canvas so screenshots of any size compare.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

CANVAS_W = 1080


def load(path: Path) -> tuple[np.ndarray, float]:
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    return a, CANVAS_W / a.shape[1]


def ground_colour(a: np.ndarray) -> dict:
    """The modal colour of the frame's border ring — the actual ground, not an average."""
    ring = np.concatenate([a[:8].reshape(-1, 3), a[-8:].reshape(-1, 3),
                           a[:, :8].reshape(-1, 3), a[:, -8:].reshape(-1, 3)])
    q = (ring // 8 * 8).astype(int)
    vals, counts = np.unique(q, axis=0, return_counts=True)
    bg = vals[counts.argmax()]
    share = counts.max() / len(q)
    return {"rgb": [int(v) for v in bg], "hex": "#%02X%02X%02X" % tuple(int(v) for v in bg),
            "share_of_border": round(float(share), 3)}


def ink_bands(a: np.ndarray, bg: np.ndarray, k: float) -> list[dict]:
    """Find horizontal bands of high-contrast content and describe each one."""
    lum = a.mean(axis=2)
    bg_lum = float(bg.mean())
    # distance from the ground, per pixel
    dist = np.abs(lum - bg_lum)
    strong = dist > 60                       # type and hard UI edges
    rows = strong.mean(axis=1)               # fraction of the row that is content
    bands, start = [], None
    for y, v in enumerate(rows):
        on = v > 0.004
        if on and start is None:
            start = y
        elif not on and start is not None:
            if y - start >= 2:
                bands.append((start, y))
            start = None
    if start is not None:
        bands.append((start, len(rows)))

    out = []
    H, W = lum.shape
    for (y0, y1) in bands:
        seg = strong[y0:y1]
        cols = np.where(seg.any(axis=0))[0]
        if len(cols) == 0:
            continue
        x0, x1 = int(cols[0]), int(cols[-1])
        # ink colour = the brightest common colour inside the band
        px = a[y0:y1][seg]
        if len(px) == 0:
            continue
        pl = px.mean(axis=1)
        ink = px[pl >= np.percentile(pl, 90)].mean(axis=0)
        out.append({
            "y_px": [int(y0 * k), int(y1 * k)],
            "y_pct": [round(y0 / H, 4), round(y1 / H, 4)],
            "cap_height_px": int((y1 - y0) * k),
            "x_span_px": [int(x0 * k), int(x1 * k)],
            "x_pct": [round(x0 / W, 4), round(x1 / W, 4)],
            "fill_pct_of_width": round((x1 - x0) / W, 3),
            "ink_hex": "#%02X%02X%02X" % tuple(int(v) for v in ink),
        })
    return out


def accent(a: np.ndarray, bg: np.ndarray) -> dict | None:
    """The one saturated hue that is not the ground — the accent."""
    px = a.reshape(-1, 3)
    mx, mn = px.max(axis=1), px.min(axis=1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
    m = (sat > 0.45) & (mx > 70)
    if m.sum() < 40:
        return None
    sel = px[m]
    q = (sel // 16 * 16).astype(int)
    vals, counts = np.unique(q, axis=0, return_counts=True)
    c = vals[counts.argmax()]
    return {"hex": "#%02X%02X%02X" % tuple(int(v) for v in c),
            "share_of_frame": round(float(m.mean()), 4)}


def emptiness(a: np.ndarray, bg: np.ndarray) -> float:
    """Fraction of the frame that is within 12 levels of the ground on every channel."""
    d = np.abs(a - bg).max(axis=2)
    return round(float((d <= 12).mean()), 3)


def asymmetric_ground(a: np.ndarray) -> dict:
    """Dark shorts are rarely one flat colour; measure the glow direction if there is one."""
    lum = a.mean(axis=2)
    H, W = lum.shape
    q = {
        "top": float(lum[: H // 4].mean()), "bottom": float(lum[-H // 4:].mean()),
        "left": float(lum[:, : W // 4].mean()), "right": float(lum[:, -W // 4:].mean()),
        "centre": float(lum[H // 3: 2 * H // 3, W // 4: 3 * W // 4].mean()),
    }
    lo = min(q, key=q.get)
    hi = max(q, key=q.get)
    return {"mean_lum_by_region": {k: round(v, 1) for k, v in q.items()},
            "brightest_region": hi, "darkest_region": lo,
            "delta": round(q[hi] - q[lo], 1)}


def measure(path: Path, ignore_bottom_px: int = 0) -> dict:
    a, k = load(path)
    H, W = a.shape[:2]
    full_h = H
    if ignore_bottom_px:
        # Player chrome (play button, scrubber, timestamp) is drawn OVER the video.
        # It is not part of the design; mask it before looking for type bands.
        a = a[: max(1, H - ignore_bottom_px)]
        H = a.shape[0]
    bg = ground_colour(a)
    bgv = np.array(bg["rgb"], dtype=np.float32)
    bands = ink_bands(a, bgv, k)
    acc = accent(a, bgv)
    for b in bands:
        b["y_pct"] = [round(b["y_pct"][0] * H / full_h, 4), round(b["y_pct"][1] * H / full_h, 4)]
    return {
        "file": path.name,
        "ignored_bottom_px": ignore_bottom_px,
        "screenshot_px": [int(W), int(H)],
        "aspect": round(W / H, 4),
        "canvas_1080x1920": abs(W / H - 9 / 16) < 0.03,
        "ground": bg,
        "accent": acc,
        "empty_fraction": emptiness(a, bgv),
        "ground_gradient": asymmetric_ground(a),
        "bands": bands,
        "band_count": len(bands),
    }


def summarise(measures: list[dict]) -> dict:
    """The cross-frame contract: what every frame of this reference agrees on."""
    tops = []
    for m in measures:
        b = m["bands"]
        if b:
            tops.append(b[0])                      # headline band
    caps = [m["bands"][-1] for m in measures if len(m["bands"]) >= 2]
    grounds = {m["ground"]["hex"] for m in measures}
    accents = [m["accent"]["hex"] for m in measures if m["accent"]]
    return {
        "frames": len(measures),
        "vertical_canvas": all(m["canvas_1080x1920"] for m in measures),
        "ground_colours": sorted(grounds),
        "accent_colours": accents,
        "headline": {
            "top_pct": [round(min(t["y_pct"][0] for t in tops), 3),
                        round(max(t["y_pct"][1] for t in tops), 3)] if tops else None,
            "cap_height_px": [min(t["cap_height_px"] for t in tops),
                              max(t["cap_height_px"] for t in tops)] if tops else None,
            "x_start_pct": sorted({round(t["x_pct"][0], 3) for t in tops}),
            "fill_pct_of_width": [min(t["fill_pct_of_width"] for t in tops),
                                  max(t["fill_pct_of_width"] for t in tops)] if tops else None,
        },
        "caption": {
            "top_pct": [round(min(c["y_pct"][0] for c in caps), 3),
                        round(max(c["y_pct"][1] for c in caps), 3)] if caps else None,
            "cap_height_px": [min(c["cap_height_px"] for c in caps),
                              max(c["cap_height_px"] for c in caps)] if caps else None,
            "x_start_pct": sorted({round(c["x_pct"][0], 3) for c in caps}),
        },
        "empty_fraction_range": [min(m["empty_fraction"] for m in measures),
                                 max(m["empty_fraction"] for m in measures)],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("frames", nargs="+", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--ignore-bottom", type=int, default=0,
                    help="px of player chrome at the bottom to mask (play button / scrubber)")
    args = ap.parse_args()
    measures = [measure(p, args.ignore_bottom) for p in args.frames]
    doc = {"measured": measures, "contract": summarise(measures)}
    text = json.dumps(doc, indent=1)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n")
        print(f"wrote {args.out}")
    print(json.dumps(doc["contract"], indent=1))


if __name__ == "__main__":
    main()
