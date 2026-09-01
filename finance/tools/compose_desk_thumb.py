#!/usr/bin/env python3
"""Desk-of-evidence thumb.
  python3 tools/compose_desk_thumb.py BASE.jpg LOGO.png OUT.jpg \\
      KICKER HEADLINE WOUND [clip_x clip_y] [scrap_x scrap_y SCRAP]
"""
from __future__ import annotations
import random, sys, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageStat, ImageOps

BASE, LOGO, OUT, KICKER, HEADLINE, WOUND = sys.argv[1:7]
clip_xy = (int(sys.argv[7]), int(sys.argv[8])) if len(sys.argv) >= 9 else None
scrap = None
if len(sys.argv) >= 12:
    scrap = (int(sys.argv[9]), int(sys.argv[10]), sys.argv[11])

W, H = 1280, 720
RED, GOLD, WHITE, INK = (196, 30, 58), (244, 193, 93), (255, 255, 255), (28, 24, 20)
PAPER = (236, 224, 200)
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONTS = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
FONTO = "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf"
if not Path(FONTO).exists():
    FONTO = FONTB


def knockout_dark(im, t=32):
    im = im.convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if r < t and g < t and b < t:
                px[x, y] = (0, 0, 0, 0)
    return im


def messenger_white_wordmark(im):
    """Keep light type, drop the navy plate so it sits on a dark newsroom."""
    im = im.convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            lum = 0.3 * r + 0.59 * g + 0.11 * b
            if lum > 160:
                px[x, y] = (255, 255, 255, 255)
            else:
                px[x, y] = (0, 0, 0, 0)
    return im


def quibi_q_only(im):
    im = knockout_dark(im)
    w, h = im.size
    return im.crop((0, 0, int(w * 0.42), h))


def torn_clip(kicker, headline, cw=620, ch=280):
    rng = random.Random(5)
    mask = Image.new("L", (cw, ch), 255)
    md = ImageDraw.Draw(mask)
    for x in range(0, cw, 6):
        md.rectangle((x, 0, x + 6, rng.randint(3, 12)), fill=0)
        md.rectangle((x, ch - rng.randint(3, 12), x + 6, ch), fill=0)
    for y in range(0, ch, 6):
        md.rectangle((0, y, rng.randint(3, 12), y + 6), fill=0)
        md.rectangle((cw - rng.randint(3, 12), y, cw, y + 6), fill=0)
    paper = Image.new("RGB", (cw, ch), PAPER)
    pd = ImageDraw.Draw(paper)
    fk = ImageFont.truetype(FONTB, 18)
    fh = ImageFont.truetype(FONTS, 40)
    pd.text((30, 20), kicker.upper(), font=fk, fill=RED)
    y = 52
    # slightly tighter wrap so 40pt still fits
    for line in textwrap.wrap(headline, 24):
        pd.text((30, y), line, font=fh, fill=INK)
        y += 48
    paper.putalpha(mask)
    sh = Image.new("RGBA", (cw + 28, ch + 28), (0, 0, 0, 0))
    sm = mask.filter(ImageFilter.GaussianBlur(4))
    shadow = Image.new("RGBA", (cw, ch), (0, 0, 0, 160))
    shadow.putalpha(sm)
    sh.paste(shadow, (10, 12), shadow)
    sh.paste(paper, (2, 2), paper)
    return sh.rotate(-3.5, expand=True, resample=Image.Resampling.BICUBIC)


def stroke_text(draw, xy, text, font, fill, sc=(0, 0, 0), sw=6):
    x, y = xy
    for dx in range(-sw, sw + 1, 3):
        for dy in range(-sw, sw + 1, 3):
            if dx or dy:
                draw.text((x + dx, y + dy), text, font=font, fill=sc)
    draw.text((x, y), text, font=font, fill=fill)


base = Image.open(BASE).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
base = ImageEnhance.Brightness(base).enhance(1.12)
base = ImageEnhance.Contrast(base).enhance(1.08)
im = base.convert("RGBA")

raw = Image.open(LOGO)
name = Path(LOGO).name.lower()
if "quibi" in name:
    logo = quibi_q_only(raw)
    max_w, max_h = 160, 160
elif "messenger" in name:
    logo = messenger_white_wordmark(raw)
    max_w, max_h = 480, 130
else:
    logo = knockout_dark(raw)
    max_w, max_h = 420, 130
lw, lh = logo.size
s = min(max_w / max(lw, 1), max_h / max(lh, 1))
logo = logo.resize((max(1, int(lw * s)), max(1, int(lh * s))), Image.Resampling.LANCZOS)
ls = Image.new("RGBA", (logo.size[0] + 24, logo.size[1] + 24), (0, 0, 0, 0))
blob = Image.new("RGBA", logo.size, (0, 0, 0, 180))
blob.putalpha(logo.split()[-1].point(lambda a: min(180, a)))
blob = blob.filter(ImageFilter.GaussianBlur(6))
ls.paste(blob, (8, 8), blob)
ls.paste(logo, (0, 0), logo)
im.alpha_composite(ls, (32, 24))

clip = torn_clip(KICKER, HEADLINE)
if clip_xy:
    cx, cy = clip_xy
else:
    cx, cy = W - clip.size[0] - 28, 40
im.alpha_composite(clip, (cx, cy))

d = ImageDraw.Draw(im)
if scrap:
    sx, sy, stxt = scrap
    fs = ImageFont.truetype(FONTO, 36)
    # red pencil on the physical scrap
    tmp = Image.new("RGBA", (420, 90), (0, 0, 0, 0))
    td = ImageDraw.Draw(tmp)
    td.text((4, 8), stxt, font=fs, fill=(180, 32, 40, 255))
    tmp = tmp.rotate(-8, expand=True, resample=Image.Resampling.BICUBIC)
    im.alpha_composite(tmp, (sx, sy))

parts = WOUND.split()
f1 = ImageFont.truetype(FONTB, 92)
y = H - 48 - 100 * min(2, len(parts))
x = 40
if len(parts) == 1:
    stroke_text(d, (x, y), parts[0], f1, WHITE)
else:
    stroke_text(d, (x, y), " ".join(parts[:-1]), f1, WHITE)
    stroke_text(d, (x, y + 96), parts[-1], f1, GOLD)

out = im.convert("RGB")
Path(OUT).parent.mkdir(parents=True, exist_ok=True)
out.save(OUT, quality=93)
small = out.copy()
small.thumbnail((213, 120))
mean = sum(ImageStat.Stat(small).mean) / 3
print("WROTE", OUT, f"lum {mean:.1f}")
