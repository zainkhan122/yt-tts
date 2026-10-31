#!/usr/bin/env python3
"""Brand thumbnail generator with a real 250px mobile preview and measurable gates.

The agent must visually review the preview before marking a long video approved.
A layout/contrast test is NOT a promise that the hook will earn clicks.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.post.common import load_json, save_json

MIDNIGHT = "#050B1F"
YELLOW = "#FFD60A"
SKY = "#38BDF8"
FONT = ROOT / "templates/_base/fonts/Anton.ttf"


def contrast(a, b):
    def luminance(color):
        channels = [int(color[i:i+2], 16)/255 for i in (1, 3, 5)]
        channels = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in channels]
        return sum(v*w for v, w in zip(channels, (.2126, .7152, .0722)))
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi+.05)/(lo+.05)


def build(spec, dest, proof_image=None, rules=None):
    rules = rules or load_json(ROOT / "config/youtube.json")["thumbnail"]
    lines = spec.get("headline", [])
    if not isinstance(lines, list) or not 1 <= len(lines) <= rules["max_lines"]:
        raise ValueError("Thumbnail headline must be 1–3 short lines")
    if not all(isinstance(s, str) and s.strip() for s in lines):
        raise ValueError("Empty thumbnail headline")
    if len(" ".join(lines).split()) > rules["max_words"]:
        raise ValueError("Thumbnail headline has too many words; use 2–5, maximum 6")
    lines = [s.upper().strip() for s in lines]
    width, height = rules["width"], rules["height"]
    image = Image.new("RGB", (width, height), MIDNIGHT)
    draw = ImageDraw.Draw(image)
    # The headline sits on a solid background for a verifiable contrast ratio.
    if proof_image:
        with Image.open(proof_image) as source:
            proof = ImageOps.fit(source.convert("RGB"), (430, 556), method=Image.Resampling.LANCZOS)
        image.paste(proof, (810, 82))
        draw.rounded_rectangle((805, 77, 1245, 643), radius=20, outline=SKY, width=5)
    else:
        draw.rounded_rectangle((830, 120, 1200, 600), radius=32, fill="#102445", outline=SKY, width=6)
        draw.rounded_rectangle((878, 182, 1152, 536), radius=24, fill="#07142C", outline="#327297", width=3)
        draw.line((910, 330, 970, 390, 1120, 250), fill=YELLOW, width=24)
    available = 720
    size = 166
    while size >= 90:
        font = ImageFont.truetype(str(FONT), size)
        boxes = [draw.textbbox((0, 0), line, font=font) for line in lines]
        if max(b[2]-b[0] for b in boxes) <= available and sum(b[3]-b[1]+24 for b in boxes) <= 445:
            break
        size -= 2
    actual_heights = [(b[3]-b[1])*rules["preview_width"]/width for b in boxes]
    if min(actual_heights) < rules["minimum_text_height_at_250"]:
        raise ValueError("Text becomes too small at 250px; shorten the headline")
    kicker_font = ImageFont.truetype(str(FONT), 36)
    draw.text((64, 66), spec.get("kicker", "HYPELESS").upper()[:30], font=kicker_font, fill=SKY)
    total = sum(b[3]-b[1]+26 for b in boxes)
    y = max(150, (height-total)//2)
    positions = []
    for n, (line, box) in enumerate(zip(lines, boxes)):
        color = YELLOW if n == spec.get("highlight_line", len(lines)-1) else "#FFFFFF"
        draw.text((64, y-box[1]), line, font=font, fill=color)
        positions.append({"text": line, "bbox": [64, y, 64+box[2]-box[0], y+box[3]-box[1]], "color": color,
                          "height_at_250": round((box[3]-box[1])*rules["preview_width"]/width, 2)})
        y += box[3]-box[1]+26
    draw.rectangle((64, 630, 208, 640), fill=YELLOW)
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / "thumbnail.jpg"
    image.save(path, "JPEG", quality=93, optimize=True)
    image.resize((rules["preview_width"], round(height*rules["preview_width"]/width)), Image.Resampling.LANCZOS).save(dest/"thumbnail-250.jpg", quality=95)
    report = {"width": width, "height": height, "preview_width": rules["preview_width"], "word_count": len(" ".join(lines).split()),
              "font": "Anton", "font_size": size, "text": positions, "visual_reviewed": False,
              "sha256": "sha256:"+hashlib.sha256(path.read_bytes()).hexdigest(), "size_bytes": path.stat().st_size,
              "checks": {"16:9": width*9 == height*16, "mobile_text_height": min(actual_heights) >= rules["minimum_text_height_at_250"],
                         "contrast": min(contrast(YELLOW, MIDNIGHT), contrast("#FFFFFF", MIDNIGHT)) >= rules["contrast_min"],
                         "max_bytes": path.stat().st_size <= rules["max_bytes"], "word_limit": len(" ".join(lines).split()) <= rules["max_words"]}}
    save_json(dest/"thumbnail-report.json", report)
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("brief")
    ap.add_argument("--dest", required=True)
    ap.add_argument("--proof-image")
    a = ap.parse_args()
    report = build(load_json(a.brief)["thumbnail"], a.dest, a.proof_image)
    print("Thumbnail + 250px preview written; all automatic checks:", all(report["checks"].values()))
    print("Agent visual review still required; never claim this checkbox is an eye test.")


if __name__ == "__main__":
    main()
