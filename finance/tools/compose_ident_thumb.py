#!/usr/bin/env python3
"""Ident thumbnail: REAL logo + sourced headline card + 2-4 word wound.
Never invent a masthead. Kicker names the real outlet + date.
Usage:
  python3 tools/compose_ident_thumb.py OUT.jpg LOGO.png KICKER HEADLINE WOUND
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageStat

OUT, LOGO, KICKER, HEADLINE, WOUND = sys.argv[1:6]
W, H = 1280, 720
CHAR = (16, 16, 18)
PAPER = (237, 230, 217)
INK = (22, 20, 18)
RED = (196, 30, 58)
GOLD = (244, 193, 93)
WHITE = (255, 255, 255)
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTS = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"

im = Image.new("RGB", (W, H), CHAR)
d = ImageDraw.Draw(im)

# left plate for logo
plate = Image.new("RGB", (560, 420), (245, 245, 247))
logo = Image.open(LOGO).convert("RGBA")
# scale logo into plate with padding
max_w, max_h = 500, 280
lw, lh = logo.size
scale = min(max_w / lw, max_h / lh)
logo = logo.resize((max(1, int(lw * scale)), max(1, int(lh * scale))), Image.Resampling.LANCZOS)
px = (560 - logo.size[0]) // 2
py = (420 - logo.size[1]) // 2
if logo.mode == "RGBA":
    plate = plate.convert("RGBA")
    plate.paste(logo, (px, py), logo)
    plate = plate.convert("RGB")
else:
    plate.paste(logo, (px, py))
im.paste(plate, (40, 40))

# clipping card
card = Image.new("RGB", (620, 420), PAPER)
cd = ImageDraw.Draw(card)
cd.rectangle((0, 0, 8, 420), fill=RED)
fk = ImageFont.truetype(FONTB, 18)
fh = ImageFont.truetype(FONTS, 36)
cd.text((28, 24), KICKER.upper(), font=fk, fill=RED)
# wrap headline
import textwrap
y = 70
for line in textwrap.wrap(HEADLINE, 22):
    cd.text((28, y), line, font=fh, fill=INK)
    y += 48
im.paste(card, (620, 40))

# wound
fw = ImageFont.truetype(FONTB, 92)
# shadow
tw = d.textlength(WOUND, font=fw)
x = 48
y = 500
for dx, dy in ((-4, 0), (4, 0), (0, -4), (0, 4), (-4, -4), (4, 4)):
    d.text((x + dx, y + dy), WOUND, font=fw, fill=(0, 0, 0))
d.text((x, y), WOUND, font=fw, fill=GOLD if WOUND != "SUICIDE MATH" else WHITE)
# if two words, second gold — handled by caller as one string
# split last word gold
parts = WOUND.split()
if len(parts) >= 2:
    d.rectangle((0, 490, W, H), fill=CHAR)  # clear
    y = 510
    f1 = ImageFont.truetype(FONTB, 88)
    w1 = " ".join(parts[:-1])
    w2 = parts[-1]
    for dx, dy in ((-4, 0), (4, 0), (0, -4), (0, 4)):
        d.text((48 + dx, y + dy), w1, font=f1, fill=(0, 0, 0))
        d.text((48 + dx, y + 90 + dy), w2, font=f1, fill=(0, 0, 0))
    d.text((48, y), w1, font=f1, fill=WHITE)
    d.text((48, y + 90), w2, font=f1, fill=GOLD)

im = im.resize((1280, 720))
Path(OUT).parent.mkdir(parents=True, exist_ok=True)
im.save(OUT, quality=92)
print("WROTE", OUT)
# quick luminance
small = im.copy()
small.thumbnail((213, 120))
mean = sum(ImageStat.Stat(small.convert("RGB")).mean) / 3
print(f"mean luminance ~{mean:.1f}")
