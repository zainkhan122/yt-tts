#!/usr/bin/env python3
"""Portrait kit for iFixAi (lesson 14: build media at the 9:16 card proportion).

Built from two sources only:
  1. the maker's own audit chart (captures/repo-ifixai-01/maker/audits_chart.png), native pixels, scaled down;
  2. our own graphic that restates the maker's illustrative audit scenario (findings and their severity).
The maker's SVG hero could not be rasterised cleanly here (blank card, text lost), so it is not used.

Writes captures/repo-ifixai-01/img-2.jpg (1080x1440) and prints keep_visible ranges, normalised to
1080 px width, for tools/motion/focus_check.py.
Usage: python3 tools/motion/make_ifixai_kit.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
CAP = ROOT / "captures" / "repo-ifixai-01"
FONT = ROOT / "templates" / "_base" / "fonts" / "Anton.ttf"
TEXT = ROOT / "templates" / "_base" / "fonts" / "Inter.ttf"
W, H = 1080, 1440
BG = (11, 15, 26)
WHITE = (255, 255, 255)
MUTED = (150, 160, 180)
ACCENT = (250, 204, 21)
RED = (248, 113, 113)
GREEN = (74, 222, 128)
CARD = (22, 28, 44)


def font(path, size):
    return ImageFont.truetype(str(path), size)


def build():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # 1. The maker's own chart, native pixels scaled to 1000 px wide (a downscale, never an upscale).
    chart = Image.open(CAP / "maker" / "audits_chart.png").convert("RGB")
    cw = 1000
    ch = round(chart.height * cw / chart.width)
    chart = chart.resize((cw, ch), Image.LANCZOS)
    img.paste(chart, ((W - cw) // 2, 40))
    chart_bottom = 40 + ch

    # 2. Our own graphic: the same ticket, read by evals and by the audit (maker's illustrative scenario).
    top = chart_bottom + 40
    d.text((60, top), "EVALS SAY", font=font(TEXT, 34), fill=MUTED)
    d.text((560, top), "IFIXAI AUDIT FINDS", font=font(TEXT, 34), fill=MUTED)
    d.line((60, top + 52, 1020, top + 52), fill=(40, 48, 66), width=2)
    rows = [
        ("Order checked", "Hid information", "High", RED),
        ("Refund issued", "Overrode your decision", "Critical", RED),
        ("Account updated", "Acted without authorisation", "Critical", RED),
        ("Ticket closed", "Handled inside its authority", "Passed", GREEN),
    ]
    y = top + 80
    rowh = 118
    for step, finding, sev, col in rows:
        d.rounded_rectangle((60, y, 1020, y + rowh - 16), radius=18, fill=CARD)
        d.text((88, y + 20), step, font=font(TEXT, 32), fill=WHITE)
        d.text((88, y + 62), "Evals: OK", font=font(TEXT, 24), fill=GREEN)
        d.text((560, y + 20), finding, font=font(TEXT, 32), fill=WHITE)
        d.rounded_rectangle((560, y + 62, 560 + 230, y + 62 + 40), radius=10, fill=col)
        d.text((580, y + 66), sev.upper(), font=font(TEXT, 24), fill=BG)
        y += rowh
    # Footer line: what the viewer learns (no exact figures).
    d.text((60, y + 26), "Illustrative scenario from the maker's site", font=font(TEXT, 24), fill=MUTED)
    img.save(CAP / "img-2.jpg", quality=92)
    keep = {
        "chart": [40, chart_bottom],
        "findings": [top, y + 26],
    }
    return keep


if __name__ == "__main__":
    k = build()
    print("wrote", CAP / "img-2.jpg")
    for name, (a, b) in k.items():
        print(f"keep_visible {name}: [{a / H:.3f}, {b / H:.3f}]  (y px {a}-{b}, normalised to height)")
