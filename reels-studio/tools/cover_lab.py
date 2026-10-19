#!/usr/bin/env python3
"""Cover lab: three designed cover concepts per Short, from REAL product media.

Why: the shipped cover used to be a frame grab of the templated hook — same
skin on every video. Covers are now designed (PLAYBOOK §8A): the brief's
treatment carries 3 concepts (<=4-word text, real-media visual, curiosity
gap); this tool renders all three at 1080x1920 so the viewer panel can judge
them cold and pick the winner (treatment.selected_cover).

  python3 tools/cover_lab.py briefs/<id>.json [--out covers/<id>]
  -> cover-1.jpg (bleed), cover-2.jpg (window), cover-3.jpg (split), sheet.jpg
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
W, H = 1080, 1920
FONT = ROOT / "templates" / "_base" / "fonts" / "Anton.ttf"
ACCENTS = {"demo-first": (74, 222, 128), "duel": (255, 106, 61),
           "myth-bust": (192, 132, 252), "quest": (251, 191, 36),
           "warning": (255, 93, 71), "workflow": (45, 212, 191),
           "spotlight": (255, 214, 10)}


def cover_crop(im, tw, th):
    """Resize+center-crop an image to tw x th."""
    im = im.convert("RGB")
    s = max(tw / im.width, th / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)))
    x, y = (im.width - tw) // 2, (im.height - th) // 2
    return im.crop((x, y, x + tw, y + th))


def fit_text(draw, text, max_w, start=190):
    from PIL import ImageFont
    size = start
    while size > 40:
        f = ImageFont.truetype(str(FONT), size)
        words, lines, cur = text.upper().split(), [], ""
        for w in words:
            t = (cur + " " + w).strip()
            if draw.textlength(t, font=f) <= max_w:
                cur = t
            else:
                lines.append(cur); cur = w
        if cur:
            lines.append(cur)
        if all(draw.textlength(l, font=f) <= max_w for l in lines) and len(lines) <= 3:
            return f, lines
        size -= 12
    return ImageFont.truetype(str(FONT), 40), [text.upper()]


def draw_text_block(base, lines, font, accent, y, draw):
    lh = int(font.size * 1.04)
    for i, line in enumerate(lines):
        col = accent if i == len(lines) - 1 else (255, 255, 255)
        draw.text((54, y + i * lh), line, font=font, fill=col,
                  stroke_width=6, stroke_fill=(5, 8, 16))
    return y + lh * len(lines)


def make_concepts(brief, img_path, out_dir):
    from PIL import Image, ImageDraw, ImageFilter
    src = Image.open(img_path)
    tr = brief["treatment"]
    accent = ACCENTS.get(tr.get("archetype", "spotlight"), ACCENTS["spotlight"])
    out_dir.mkdir(parents=True, exist_ok=True)
    made = []
    for i, concept in enumerate(tr["cover_concepts"]):
        text = concept["text"]
        if i == 0:  # bleed: media everywhere, text low
            im = cover_crop(src, W, H)
            ov = Image.new("RGB", (W, H), (4, 7, 15))
            im = Image.blend(im, ov, 0.25)
            d = ImageDraw.Draw(im)
            d.rectangle([0, H - 760, W, H], fill=(4, 7, 15))
            f, lines = fit_text(d, text, W - 108)
            draw_text_block(im, lines, f, accent, H - 700, d)
        elif i == 1:  # window: product in a framed window, text above
            im = Image.new("RGB", (W, H), (7, 11, 22))
            d = ImageDraw.Draw(im)
            f, lines = fit_text(d, text, W - 108)
            y = draw_text_block(im, lines, f, accent, 120, d)
            win = cover_crop(src, W - 108, H - y - 220)
            im.paste(win, (54, y + 60))
            d.rectangle([54, y + 60, W - 54, H - 160], outline=accent, width=8)
        else:  # split: media top, panel bottom with accent bar
            im = Image.new("RGB", (W, H), (7, 11, 22))
            im.paste(cover_crop(src, W, 1180), (0, 0))
            d = ImageDraw.Draw(im)
            d.rectangle([0, 1180, W, 1212], fill=accent)
            f, lines = fit_text(d, text, W - 108)
            draw_text_block(im, lines, f, accent, 1300, d)
        p = out_dir / f"cover-{i + 1}.jpg"
        im.save(p, quality=90)
        made.append(p)
    sheet = cover_crop(Image.open(made[0]), 360, 640)
    from PIL import Image as I
    contact = I.new("RGB", (1080, 640), (0, 0, 0))
    for i, p in enumerate(made):
        contact.paste(cover_crop(I.open(p), 360, 640), (i * 360, 0))
    contact.save(out_dir / "sheet.jpg", quality=88)
    return made


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("brief")
    ap.add_argument("--out")
    args = ap.parse_args()
    brief = json.loads(Path(args.brief).read_text())
    if not isinstance(brief.get("treatment"), dict):
        raise SystemExit("brief has no treatment — design the cover concepts first (PLAYBOOK §8A)")
    cap = ROOT / str(brief.get("capture", ""))
    hook = next((s for s in brief["scenes"] if s.get("id") == "hook"), brief["scenes"][0])
    img = cap / (hook.get("image") or "desktop-top.jpg")
    if not img.exists():
        raise SystemExit(f"cover source media missing: {img} (pull the capture pack first)")
    out = Path(args.out) if args.out else ROOT / "covers" / brief["id"]
    made = make_concepts(brief, img, out)
    sel = brief["treatment"].get("selected_cover")
    print(f"{brief['id']}: concepts -> {out} (selected_cover={sel}: "
          f"{brief['treatment']['cover_concepts'][sel]['text'] if isinstance(sel, int) and 0 <= sel <= 2 else 'UNSET'})")
    for p in made:
        print(" ", p)


if __name__ == "__main__":
    main()
