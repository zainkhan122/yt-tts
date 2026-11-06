#!/usr/bin/env python3
"""Draw three *illustrated*, README-grounded agent-desktop cover source graphics.

This produces local source art only, not a cover approval or a release. Run the
cover lab afterwards and have the owner/panel review all three compositions.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "covers/repo-agent-desktop-01"
FONT = ROOT / "templates/_base/fonts/Inter.ttf"
MONO = ROOT / "templates/_base/fonts/JetBrainsMono.ttf"
INK = (10, 17, 27)
PAPER = (238, 245, 247)
MUTED = (157, 181, 193)
TEAL = (98, 229, 193)
CORAL = (255, 150, 125)


def font(size, weight="Bold", mono=False):
    f = ImageFont.truetype(str(MONO if mono else FONT), size)
    if not mono:
        f.set_variation_by_name(weight)
    return f


def base(label):
    im = Image.new("RGB", (1400, 1000), INK)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((55, 75, 1345, 925), 58, fill=(19, 31, 45), outline=(76, 98, 113), width=4)
    d.rounded_rectangle((55, 75, 1345, 190), 58, fill=(33, 49, 64))
    d.rectangle((55, 135, 1345, 190), fill=(33, 49, 64))
    for i, c in enumerate((CORAL, (255, 204, 111), TEAL)):
        d.ellipse((105 + i*43, 120, 126 + i*43, 141), fill=c)
    d.text((280, 111), label, font=font(36), fill=PAPER)
    return im, d


def chip(d, xy, text, color=TEAL, size=48):
    x, y = xy
    f = font(size, mono=True)
    w = int(d.textlength(text, font=f)) + 64
    d.rounded_rectangle((x, y, x+w, y+90), 18, fill=(13, 49, 50), outline=color, width=3)
    d.text((x+32, y+16), text, font=f, fill=color)


def make():
    OUT.mkdir(parents=True, exist_ok=True)
    im, d = base("DESKTOP APP  /  ACCESSIBILITY")
    d.text((125, 255), "Your next task", font=font(66, "Black"), fill=PAPER)
    d.text((125, 352), "Accessible target", font=font(32), fill=MUTED)
    d.rounded_rectangle((120, 415, 800, 560), 26, fill=PAPER)
    d.text((165, 452), "Open Documents", font=font(52), fill=INK)
    d.polygon([(740, 510), (800, 670), (813, 607), (865, 585)], fill=TEAL)
    d.text((125, 638), "SNAPSHOT REF", font=font(30), fill=MUTED)
    chip(d, (125, 700), "@s8f3k2p9:e8")
    if not (OUT / "cover-c1.png").exists():
        im.save(OUT / "cover-c1.png")

    im, d = base("APP  →  SNAPSHOT  →  REF")
    d.text((120, 255), "Documents", font=font(75, "Black"), fill=PAPER)
    d.text((120, 360), "A target the agent can act on", font=font(37), fill=MUTED)
    d.rounded_rectangle((120, 448, 850, 565), 22, fill=(39, 64, 75), outline=TEAL, width=4)
    d.text((160, 475), "Open Documents", font=font(48), fill=PAPER)
    d.line((490, 580, 490, 660), fill=TEAL, width=8)
    d.polygon([(470, 650), (510, 650), (490, 680)], fill=TEAL)
    chip(d, (260, 705), "@s8f3k2p9:e8")
    if not (OUT / "cover-c2.png").exists():
        im.save(OUT / "cover-c2.png")

    im, d = base("REF RECOVERY  /  ILLUSTRATION")
    d.text((120, 250), "UI changed?", font=font(72, "Black"), fill=PAPER)
    d.rounded_rectangle((120, 370, 1250, 540), 24, fill=(65, 36, 43), outline=CORAL, width=3)
    d.text((160, 402), "STALE_REF", font=font(51, mono=True), fill=CORAL)
    d.text((160, 469), "Take a fresh snapshot", font=font(34), fill=PAPER)
    d.line((210, 590, 210, 665), fill=TEAL, width=8)
    d.polygon([(190, 655), (230, 655), (210, 685)], fill=TEAL)
    chip(d, (120, 710), "@t4a6m1n7:e8")
    if not (OUT / "cover-c3.png").exists():
        im.save(OUT / "cover-c3.png")
    print(f"Illustrated source art written to {OUT}; existing art retained; review is still required.")


if __name__ == "__main__":
    make()
