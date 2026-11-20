#!/usr/bin/env python3
"""Compose a subject-specific 9:16 artwork and edited headline for review.

Artwork must be prepared separately from verified subject/source research. This
is not an image generation or user-approval step; outputs must be reviewed.
"""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
FONT = ROOT/'graphics/templates/_base/fonts/Anton.ttf'

def compose(art, lines, dest):
    if not 1 <= len(lines) <= 3 or not all(s.strip() and s == s.upper() for s in lines):
        raise ValueError('Provide 1–3 short uppercase headline lines')
    im = ImageOps.fit(Image.open(art).convert('RGB'), (1080,1920), method=Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(im)
    size = 164
    while size >= 48:
        font = ImageFont.truetype(str(FONT),size)
        boxes = [draw.textbbox((0,0), line, font=font) for line in lines]
        if max(b[2]-b[0] for b in boxes) <= 940 and size * len(lines) <= 340:
            break
        size -= 2
    if size < 48: raise ValueError('Headline too long for safe zone')
    y=335
    for line in lines:
        box=draw.textbbox((0,0),line,font=font)
        x=(1080-(box[2]-box[0]))//2
        draw.text((x,y-box[1]),line,font=font,fill='#102839')
        y+=int(size*1.02)
    dest=Path(dest);dest.parent.mkdir(parents=True,exist_ok=True);im.save(dest,optimize=True)

if __name__ == '__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--art',required=True);ap.add_argument('--line',action='append',required=True);ap.add_argument('--out',required=True)
    a=ap.parse_args();compose(a.art,a.line,a.out)
