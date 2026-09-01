#!/usr/bin/env python3
"""Per-film thumb. Layout is a choice, not a stamp.
  python3 tools/compose_flex_thumb.py LAYOUT BASE LOGO OUT WOUND
Layouts:
  card   — object is the card (MoviePass): logo TL, wound BL
  phone  — object is the cracked phone (Quibi): Q TL, wound fills the empty RIGHT
  room   — object is the empty newsroom (Messenger): white wordmark TL, wound BL
  aisle  — object is the empty / closing toy aisle (Toys R Us): wordmark TL, wound on the empty floor
No scraps. No mandatory clipping. Do not invent a giraffe.
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageStat

LAYOUT, BASE, LOGO, OUT, WOUND = sys.argv[1:6]
W, H = 1280, 720
GOLD, WHITE, BLACK = (244, 193, 93), (255, 255, 255), (0, 0, 0)
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


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


def white_wordmark(im):
    im = im.convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            lum = 0.3 * r + 0.59 * g + 0.11 * b
            px[x, y] = (255, 255, 255, 255) if lum > 150 else (0, 0, 0, 0)
    return im


def paste_logo(im, logo, xy, max_w, max_h):
    lw, lh = logo.size
    s = min(max_w / max(lw, 1), max_h / max(lh, 1))
    logo = logo.resize((max(1, int(lw * s)), max(1, int(lh * s))), Image.Resampling.LANCZOS)
    sh = Image.new("RGBA", (logo.size[0] + 20, logo.size[1] + 20), (0, 0, 0, 0))
    blob = Image.new("RGBA", logo.size, (0, 0, 0, 160))
    blob.putalpha(logo.split()[-1].point(lambda a: min(160, a)))
    blob = blob.filter(ImageFilter.GaussianBlur(5))
    sh.paste(blob, (6, 6), blob)
    sh.paste(logo, (0, 0), logo)
    im.alpha_composite(sh, xy)
    return im


def stroke(draw, xy, text, font, fill, sw=7):
    x, y = xy
    for dx in range(-sw, sw + 1, 3):
        for dy in range(-sw, sw + 1, 3):
            if dx or dy:
                draw.text((x + dx, y + dy), text, font=font, fill=BLACK)
    draw.text((x, y), text, font=font, fill=fill)


def wound(draw, parts, x, y, size=96, stack=True):
    f = ImageFont.truetype(FONTB, size)
    if len(parts) == 1:
        stroke(draw, (x, y), parts[0], f, WHITE)
        return
    if stack:
        stroke(draw, (x, y), " ".join(parts[:-1]), f, WHITE)
        stroke(draw, (x, y + int(size * 1.05)), parts[-1], f, GOLD)
    else:
        # one line, last word gold — draw separately
        w0 = " ".join(parts[:-1]) + " "
        stroke(draw, (x, y), w0, f, WHITE)
        tw = draw.textlength(w0, font=f)
        stroke(draw, (x + tw, y), parts[-1], f, GOLD)


base = Image.open(BASE).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
lift = {"room": 1.62, "aisle": 1.40}.get(LAYOUT, 1.14)
base = ImageEnhance.Brightness(base).enhance(lift)
base = ImageEnhance.Contrast(base).enhance(1.10 if LAYOUT in {"room", "aisle"} else 1.08)
im = base.convert("RGBA")
raw = Image.open(LOGO)
parts = WOUND.split()
d = ImageDraw.Draw(im)

if LAYOUT == "card":
    logo = knockout_dark(raw)
    im = paste_logo(im, logo, (36, 28), 400, 120)
    wound(d, parts, 40, H - 230, 100, True)
elif LAYOUT == "phone":
    logo = knockout_dark(raw)
    w, h = logo.size
    logo = logo.crop((0, 0, int(w * 0.42), h))  # Q only
    im = paste_logo(im, logo, (W - 200, 36), 150, 150)
    wound(d, parts, 700, 430, 92, True)
elif LAYOUT == "room":
    # keep the real navy bar; do not chew it into white pixels
    logo = knockout_dark(raw)
    im = paste_logo(im, logo, (36, 28), 460, 100)
    wound(d, parts, 40, H - 230, 100, True)
elif LAYOUT == "aisle":
    # keep the red reverse-R; do not invent Geoffrey
    logo = knockout_dark(raw)
    im = paste_logo(im, logo, (36, 28), 480, 120)
    wound(d, parts, 40, H - 230, 108, True)
else:
    sys.exit("unknown layout")

out = im.convert("RGB")
# room layouts are night interiors — lift until the 120px test can pass
if LAYOUT in {"room", "aisle"}:
    for _ in range(6):
        small = out.copy()
        small.thumbnail((213, 120))
        mean = sum(ImageStat.Stat(small).mean) / 3
        if mean >= 39:
            break
        out = ImageEnhance.Brightness(out).enhance(1.08)
Path(OUT).parent.mkdir(parents=True, exist_ok=True)
out.save(OUT, quality=93)
small = out.copy()
small.thumbnail((213, 120))
print("WROTE", OUT, "lum", round(sum(ImageStat.Stat(small).mean) / 3, 1))
