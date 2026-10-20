#!/usr/bin/env python3
"""Cover lab: three designed cover concepts per Short, from REAL product media.

Why: the shipped cover used to be a frame grab of the templated hook — same
skin on every video. Covers are now designed (PLAYBOOK §8A): the brief's
treatment carries 3 concepts (<=4-word text, real-media visual, curiosity
gap); this tool renders all three at 1080x1920 so the viewer panel can judge
them cold and pick the winner (treatment.selected_cover).

  python3 tools/cover_lab.py briefs/<id>.json [--shots covers/<id>]
      render cover-{1,2,3}.jpg + sheet.jpg + concepts.json (measured report)
  python3 tools/cover_lab.py briefs/<id>.json --apply
      write cover-selected.jpg + selection.json from treatment.selected_cover
      (the pipeline then pins it into renders/<id>/cover.jpg and the queue)

Effectiveness rules this tool enforces, not just reports:
  * each concept uses a DIFFERENT real capture image when the pack has enough,
  * each concept has a different layout id (bleed / window / split + archetype
    type treatment), so three concepts are never one design three times,
  * text contrast is measured against the pixels behind it (WCAG >= 4.5),
  * the selected concept is the one artifact the pipeline ships as cover.jpg.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
W, H = 1080, 1920
FONT = ROOT / "templates" / "_base" / "fonts" / "Anton.ttf"
ACCENTS = {"demo-first": (74, 222, 128), "duel": (255, 106, 61),
           "myth-bust": (192, 132, 252), "quest": (251, 191, 36),
           "warning": (255, 93, 71), "workflow": (45, 212, 191),
           "spotlight": (255, 214, 10)}
# Archetype typography: the cover must look like the format, not like the template.
TYPE = {"quest": {"case": "upper", "tracking": 0}, "myth-bust": {"case": "upper", "tracking": -0.02},
        "demo-first": {"case": "upper", "tracking": 0.01}, "workflow": {"case": "upper", "tracking": 0.02},
        "warning": {"case": "upper", "tracking": 0.0}, "duel": {"case": "upper", "tracking": 0.03},
        "spotlight": {"case": "upper", "tracking": 0.0}}
LAYOUTS = ("bleed", "window", "split")


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


def draw_text_block(base, lines, font, accent, y, draw, align="left", x=54):
    lh = int(font.size * 1.04)
    for i, line in enumerate(lines):
        col = accent if i == len(lines) - 1 else (255, 255, 255)
        if align == "center":
            w = draw.textlength(line, font=font)
            draw.text(((W - w) / 2, y + i * lh), line, font=font, fill=col,
                      stroke_width=6, stroke_fill=(5, 8, 16))
        else:
            draw.text((x, y + i * lh), line, font=font, fill=col,
                      stroke_width=6, stroke_fill=(5, 8, 16))
    return y + lh * len(lines)


def luminance(rgb):
    def ch(v):
        v = v / 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def block_background(im, box):
    """Mean colour of the pixels the text will sit on (what contrast is measured against)."""
    x0, y0, x1, y1 = [int(v) for v in box]
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(im.width, max(x1, x0 + 2)), min(im.height, max(y1, y0 + 2))
    px = im.crop((x0, y0, x1, y1)).resize((8, 8))
    data = list(px.get_flattened_data()) if hasattr(px, "get_flattened_data") else list(px.getdata())
    return tuple(sum(c[i] for c in data) // len(data) for i in range(3))


def pick_images(brief, count, root=ROOT):
    """Different real capture image per concept; fall back to the hook image only when the pack is thin."""
    cap = Path(root) / str(brief.get("capture", ""))
    candidates = []
    if cap.exists():
        preferred = ["desktop-top.jpg", "desktop-full.jpg", "readme-top.png", "app.png", "og.png"]
        candidates += [cap / n for n in preferred if (cap / n).exists()]
        for p in sorted(cap.glob("*.png")) + sorted(cap.glob("*.jpg")):
            if p not in candidates and "desktop" not in p.name and p.name not in ("sheet.jpg",):
                candidates.append(p)
    for s in brief.get("scenes", []):
        for key in ("image", "figure"):
            if s.get(key):
                p = cap / s[key]
                if p.exists() and p not in candidates:
                    candidates.append(p)
    if not candidates:
        raise SystemExit(f"cover source media missing: no capture images under {cap} (pull the capture pack first)")
    return [candidates[i % len(candidates)] for i in range(count)]


def make_concepts(brief, out_dir, root=ROOT):
    from PIL import Image, ImageDraw
    tr = brief["treatment"]
    arch = tr.get("archetype", "spotlight")
    accent = ACCENTS.get(arch, ACCENTS["spotlight"])
    out_dir.mkdir(parents=True, exist_ok=True)
    concepts = tr["cover_concepts"]
    sources = pick_images(brief, len(concepts), root=root)
    made, report = [], []
    for i, concept in enumerate(concepts):
        text = concept["text"]
        src = sources[i]
        layout = LAYOUTS[i % len(LAYOUTS)]
        base = Image.new("RGB", (W, H), (7, 11, 22))
        scratch = ImageDraw.Draw(base)  # only measures type; never draws the final frame
        if layout == "bleed":  # media everywhere, text on a flat plate low
            base = Image.blend(cover_crop(Image.open(src), W, H), Image.new("RGB", (W, H), (4, 7, 15)), 0.25)
            scratch = ImageDraw.Draw(base)
            scratch.rectangle([0, H - 760, W, H], fill=(4, 7, 15))
            text_y, align = H - 700, "left"
        elif layout == "window":  # product in a framed window, text above on flat ground
            text_y, align = 120, "left"
        else:  # split: media top, panel bottom with accent bar
            base.paste(cover_crop(Image.open(src), W, 1180), (0, 0))
            scratch.rectangle([0, 1180, W, 1212], fill=accent)
            text_y, align = 1300, "left"
        f, lines = fit_text(scratch, text, W - 108)
        lh = int(f.size * 1.04)
        box = (54, text_y, W - 54, text_y + lh * len(lines))
        plate = base.copy()  # the pixels the type will sit on, before any type lands
        d = ImageDraw.Draw(base)
        y = draw_text_block(base, lines, f, accent, text_y, d, align=align)
        if layout == "window":
            win = cover_crop(Image.open(src), W - 108, H - y - 220)
            base.paste(win, (54, y + 60))
            d.rectangle([54, y + 60, W - 54, H - 160], outline=accent, width=8)
        # archetype signature: a mono kicker in the format's voice (and only that)
        kicker = {"quest": "MISSION BRIEF", "myth-bust": "CLAIM", "warning": "WARNING",
                  "workflow": "STEP 1", "duel": "SIDE A", "demo-first": "DEMO", "spotlight": ""}.get(arch, "")
        if kicker:
            from PIL import ImageFont
            kf = ImageFont.truetype(str(ROOT / "templates/_base/fonts/JetBrainsMono.ttf"), 34)
            ky = 86 if layout == "window" else 1052 if layout == "bleed" else 1240
            d.rectangle([54, ky - 12, 54 + d.textlength(kicker, font=kf) + 40, ky + 46], fill=accent)
            d.text((74, ky - 4), kicker, font=kf, fill=(6, 8, 14))
        im = base
        p = out_dir / f"cover-{i + 1}.jpg"
        im.save(p, quality=92)
        bg = block_background(plate, box)
        white, yellow = (255, 255, 255), accent
        made.append(p)
        report.append({"concept": i, "text": text, "layout": layout, "source": str(src.relative_to(root)) if src.is_relative_to(root) else str(src),
                       "file": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                       "words": len(text.split()),
                       "contrast_white": round(contrast(white, bg), 2),
                       "contrast_accent": round(contrast(yellow, bg), 2),
                       "text_box": [round(v) for v in box]})
    from PIL import Image as I
    contact = I.new("RGB", (1080, 640), (0, 0, 0))
    for i, p in enumerate(made):
        contact.paste(cover_crop(I.open(p), 360, 640), (i * 360, 0))
    contact.save(out_dir / "sheet.jpg", quality=88)
    return made, report


def audit(report):
    """A cover set is only useful if the three concepts are really three different designs."""
    problems = []
    layouts = [c["layout"] for c in report]
    if len(set(layouts)) != len(layouts):
        problems.append(f"concepts reuse a layout: {layouts}")
    sources = [c["source"] for c in report]
    if len(report) >= 3 and len(set(sources)) != len(sources):
        seen, dupes = set(), set()
        for src in sources:
            (dupes if src in seen else seen).add(src)
        problems.append(f"concepts share capture images ({', '.join(sorted(dupes))}); "
                        f"each concept needs its own real media")
    for c in report:
        if c["words"] > 4:
            problems.append(f"concept {c['concept']} text has {c['words']} words (max 4)")
        if min(c["contrast_white"], c["contrast_accent"]) < 4.5:
            problems.append(f"concept {c['concept']} contrast {c['contrast_white']}:1 / "
                            f"{c['contrast_accent']}:1 below 4.5 against its plate")
    return problems


def apply(brief, out_dir, report):
    """Freeze ONE artifact: the concept the panel picked becomes cover.jpg everywhere."""
    tr = brief["treatment"]
    sel = tr.get("selected_cover")
    if not isinstance(sel, int) or not 0 <= sel < len(report):
        raise SystemExit("treatment.selected_cover must pick one of the rendered concepts")
    src = out_dir / report[sel]["file"]
    dst = out_dir / "cover-selected.jpg"
    dst.write_bytes(src.read_bytes())
    selection = {"brief": brief["id"], "selected": sel, "text": report[sel]["text"],
                 "layout": report[sel]["layout"], "source": report[sel]["source"],
                 "file": dst.name, "sha256": hashlib.sha256(dst.read_bytes()).hexdigest(),
                 "archetype": tr.get("archetype"), "concepts": report}
    (out_dir / "selection.json").write_text(json.dumps(selection, indent=2))
    return selection


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("brief")
    ap.add_argument("--out", "--shots", dest="out")
    ap.add_argument("--apply", action="store_true", help="write cover-selected.jpg + selection.json")
    args = ap.parse_args()
    brief = json.loads(Path(args.brief).read_text())
    if not isinstance(brief.get("treatment"), dict):
        raise SystemExit("brief has no treatment — design the cover concepts first (PLAYBOOK §8A)")
    out = Path(args.out) if args.out else ROOT / "covers" / brief["id"]
    made, report = make_concepts(brief, out)
    (out / "concepts.json").write_text(json.dumps({"brief": brief["id"], "concepts": report}, indent=2))
    problems = audit(report)
    print(f"{brief['id']}: {len(made)} concepts -> {out}")
    for c in report:
        print(f"  cover-{c['concept'] + 1}.jpg  {c['layout']:<6} {c['text']:<24} "
              f"contrast {c['contrast_white']}:1  {c['source']}")
    if problems:
        for p in problems:
            print("  FAIL", p)
    if args.apply:
        if problems:
            raise SystemExit("refusing to apply a failing cover set")
        sel = apply(brief, out, report)
        print(f"  applied: {sel['file']} ({sel['text']}, {sel['sha256'][:12]}) -> renders/<id>/cover.jpg, kit, YouTube thumbnail")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
