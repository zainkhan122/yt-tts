#!/usr/bin/env python3
"""Portrait kit for claude-mem (lesson 14: build media at the 9:16 card proportion).

One 1080x1440 image: the tool's own animation frame on top (native pixels, 1.69x),
the own vector record -> compress -> recall diagram below. Every scene uses this
one image, so the card fills the middle of the 9:16 frame.

Writes captures/repo-claude-mem-01/img-2.jpg and prints the keep_visible ranges
(normalised to 1080 px width) that focus_check.py needs.
Usage: python3 tools/motion/make_stacked_kit.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
CAP = ROOT / "captures" / "repo-claude-mem-01"
FONT = ROOT / "templates" / "_base" / "fonts" / "Anton.ttf"
W, H = 1080, 1440
ACCENT = (250, 204, 21)
MUTED = (150, 160, 180)
WHITE = (255, 255, 255)
BG = (11, 15, 26)
NODE_X = [180, 540, 900]
NODE_Y = 1080


def font(size):
    return ImageFont.truetype(str(FONT), size)


def main():
    canvas = Image.new("RGB", (W, H), BG)
    # feed: the tool's own README animation, frame 150, full width (1.69x of 640 px)
    g = Image.open(CAP / "cm-preview.gif")
    g.seek(150)
    feed = g.convert("RGB").resize((W, round(360 * W / 640)), Image.LANCZOS)
    feed = feed.filter(ImageFilter.UnsharpMask(radius=1.5, percent=50, threshold=2))
    canvas.paste(feed, (0, 60))
    d = ImageDraw.Draw(canvas)
    # diagram band
    cy = NODE_Y
    d.line((NODE_X[0], cy, NODE_X[2], cy), fill=(60, 70, 90), width=8)
    d.line((NODE_X[0], cy, NODE_X[1], cy), fill=ACCENT, width=8)
    names = [("RECORD", "each session"), ("COMPRESS", "decisions, fixes"), ("RECALL", "next session")]
    for i, (x, (n, s)) in enumerate(zip(NODE_X, names)):
        d.ellipse((x - 70, cy - 70, x + 70, cy + 70), fill=(15, 20, 32),
                  outline=ACCENT if i == 1 else (120, 130, 150), width=7)
        d.text((x, cy), str(i + 1), font=font(70), fill=ACCENT, anchor="mm")
        d.text((x, cy + 150), n, font=font(64), fill=WHITE, anchor="mm")
        d.text((x, cy + 210), s, font=font(38), fill=MUTED, anchor="mm")
    canvas.save(CAP / "img-2.jpg", quality=95)
    # label extents, normalised to width: label half-width ~ 110 px at this size
    ranges = [[round((x - 115) / W, 3), round((x + 115) / W, 3)] for x in NODE_X]
    print("wrote img-2.jpg", canvas.size)
    print("keep_visible", ranges)


if __name__ == "__main__":
    main()
