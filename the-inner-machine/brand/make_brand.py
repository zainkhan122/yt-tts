#!/usr/bin/env python3
"""Compose The Inner Machine brand finals from the generated _raw art.
  logo_raw.png   -> logo.png (1024x1024) + logo_800x800.png (800)
  banner_raw.png -> banner.jpg (2560x1440) with title+tagline in the YT safe area.
Idempotent; re-run any time to rebuild finals.
"""
from PIL import Image, ImageDraw, ImageFont
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
COPPER = (224, 164, 88)
CYAN = (111, 211, 224)


def logo():
    im = Image.open(f"{HERE}/logo_raw.png").convert("RGBA")
    im = im.resize((1024, 1024))
    im.save(f"{HERE}/logo.png")
    im.resize((800, 800)).save(f"{HERE}/logo_800x800.png")
    print("logo.png (1024) + logo_800x800.png (800)")


def banner():
    im = Image.open(f"{HERE}/banner_raw.png").convert("RGB")
    im = im.resize((2560, 1440))
    d = ImageDraw.Draw(im, "RGBA")
    # soft dark scrim band behind the title for legibility (center safe area)
    for i in range(360):
        a = int(95 * (1 - abs(i - 180) / 180))
        d.rectangle([0, 540 + i, 2560, 541 + i], fill=(8, 10, 12, a))
    f = ImageFont.truetype(FONT, 118)
    t = "THE INNER MACHINE"
    w = d.textlength(t, font=f); x = (2560 - w) / 2
    d.text((x, 596 + 4), t, font=f, fill=(0, 0, 0, 170))
    d.text((x, 596), t, font=f, fill=COPPER)
    f2 = ImageFont.truetype(FONT, 44)
    t2 = "THE HIDDEN MACHINERY OF YOUR MIND"
    w2 = d.textlength(t2, font=f2); x2 = (2560 - w2) / 2
    d.text((x2, 764), t2, font=f2, fill=CYAN)
    im.save(f"{HERE}/banner.jpg", quality=92)
    print("banner.jpg (2560x1440)")


if __name__ == "__main__":
    logo()
    banner()
