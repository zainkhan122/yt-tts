#!/usr/bin/env python3
"""L3 — 213×120 readability + brightness. Writes thumbnail_120.jpg beside the source.
Usage: python3 tools/thumb_test.py thumbnail.jpg
"""
import sys
from pathlib import Path
from PIL import Image, ImageStat

src = Path(sys.argv[1])
im = Image.open(src).convert("RGB")
w, h = im.size
fails = []
print(f"size {w}x{h}")
if (w, h) != (1280, 720):
    fails.append(f"thumb must be 1280x720, got {w}x{h}")
small = im.copy()
small.thumbnail((213, 120))
out = src.with_name(src.stem + "_120.jpg")
small.save(out, quality=90)
print("wrote", out)
stat = ImageStat.Stat(small)
mean = sum(stat.mean) / 3
print(f"mean luminance {mean:.1f} (fail if < 38 — too dark at 120px)")
if mean < 38:
    fails.append(f"L3 too dark at 120px (mean {mean:.1f} < 38). Brighten the object.")
if fails:
    for f in fails:
        print("  FAIL:", f)
    sys.exit(1)
print("THUMB OK")
