#!/usr/bin/env python3
"""Cover lab: three designed cover concepts per Short from tool media or designed workflow graphics.

Why: the shipped cover used to be a frame grab of the templated hook — same
skin on every video. Covers are now designed (PLAYBOOK §8A): the brief's
treatment carries 3 concepts (4–5-word text, grounded visual, curiosity
gap); this tool renders all three at 1080x1920 so the viewer panel can judge
them cold and pick the winner (treatment.selected_cover).

  python3 tools/cover_lab.py briefs/<id>.json [--shots covers/<id>]
      render cover-{1,2,3}.jpg + sheet.jpg + concepts.json (measured report)
  python3 tools/cover_lab.py briefs/<id>.json --apply
      write cover-selected.jpg + selection.json from treatment.selected_cover
      (the pipeline then pins it into renders/<id>/cover.jpg and the queue)

Effectiveness rules this tool enforces, not just reports:
  * each concept uses a different source visual unless an explicit exception applies,
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
FONT = ROOT / "templates" / "_base" / "fonts" / "Inter.ttf"
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


def cover_crop(im, tw, th, anchor="center"):
    """Resize + crop an image to tw x th. anchor="top" keeps the header of a UI."""
    im = im.convert("RGB")
    s = max(tw / im.width, th / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)))
    x = (im.width - tw) // 2
    y = 0 if anchor == "top" else (im.height - th) // 2
    return im.crop((x, y, x + tw, y + th))


def contain(im, tw, th):
    """Scale the WHOLE frame inside tw x th (no crop). A phone-shaped window over a
    landscape capture used to slice the left/right edges off the UI, so labels read
    mid-word. Letterboxing on the plate keeps every pixel of the product visible."""
    im = im.convert("RGB")
    s = min(tw / im.width, th / im.height)
    return im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))))


def fit_text(draw, text, max_w, start=190):
    from PIL import ImageFont
    size = start
    while size > 40:
        f = ImageFont.truetype(str(FONT), size)
        f.set_variation_by_name("Black")
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
    raise ValueError(f"headline cannot fit: {text!r}")


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


def is_blank(path, min_std=4.0, min_ink=0.001, min_edge=0.006):
    """Near-empty frames are never cover material (batch 2026-10-20: a 'generating' still
    whose preview pane was pure white passed contrast and layout checks).

    Note: this is a floor, not a taste test - a mostly-white UI (10.7 stddev) still
    passes, so the report carries luma_std for the panel to judge."""
    from PIL import Image, ImageStat
    try:
        with Image.open(path) as im:
            g = im.convert("L")
            if g.width > 640:
                g = g.resize((640, max(1, round(g.height * 640 / g.width))))
            std = ImageStat.Stat(g).stddev[0]
            hist = g.histogram()
            dark = sum(hist[:200])
            ink = dark / max(1, sum(hist))
            small = g.resize((160, max(1, round(160 * g.height / g.width))))
            data = small.get_flattened_data() if hasattr(small, "get_flattened_data") else small.getdata()
            px, w = list(data), small.width
            edges = sum(1 for y in range(small.height) for x in range(1, w)
                        if abs(px[y * w + x] - px[y * w + x - 1]) > 12)
            edge = edges / max(1, small.width * small.height)
    except Exception:
        return True
    # blank = flat AND empty-of-structure: a mostly-white UI has edges, a white pane does not
    return edge < min_edge or (std < min_std and ink < min_ink)



# OWNER RULE (2026-10-30): repos with no video use their own still images (no filming). These five briefs are
# allowed still-image proof (BL128/BL110) and still-image media coverage (production gate); cover concepts may share
# the pack's images when the pack is thin.
NO_VIDEO_STILL_ALLOWED = {"repo-deeptutor-01", "repo-impeccable-01", "repo-edge0-01", "repo-cleanyourtv-01"}
ALLOW_SHARED_COVER_SOURCES = False  # set in main() for NO_VIDEO_STILL_ALLOWED briefs

def concept_source(concept, brief, root=ROOT):
    """Each concept names its own media (COVER-RULES.md): a tool asset in captures/<id>/, or a designed
    graphic in covers/<id>/. Nothing else is ever used as cover media."""
    m = concept["media"]
    folder = "captures" if m["kind"] == "tool_media" else "covers"
    path = Path(root) / folder / brief["id"] / m["file"]
    if not path.exists():
        raise SystemExit(f"cover media missing for {brief['id']}: {path} (run covers/system/draw_designs.py or pull the capture pack)")
    return path


def make_concepts(brief, out_dir, root=ROOT):
    """Render the three concepts. Each layout is a real composition, not a crop of one:

    poster (bleed) — the media sits whole on a blurred ground of itself, headline on a
                     flat plate below it: the page is readable, the type is quiet.
    window         — headline at the top, the media framed in an accent border: the UI is
                     presented as an artifact, the type leads.
    split          — media fills the top band edge to edge, accent rule, headline below:
                     the loudest of the three at thumbnail size.
    """
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    tr = brief["treatment"]
    arch = tr.get("archetype", "spotlight")
    accent = ACCENTS.get(arch, ACCENTS["spotlight"])
    out_dir.mkdir(parents=True, exist_ok=True)
    concepts = tr["cover_concepts"]
    try:
        from tools import cover_rules
    except ModuleNotFoundError:
        import cover_rules
    rule_problems = cover_rules.concepts_problems(concepts, Path(root) / "captures" / brief["id"],
                                                  Path(root) / "covers" / brief["id"])
    if rule_problems:
        raise SystemExit("cover rules (COVER-RULES.md) failed before rendering:\n  " + "\n  ".join(rule_problems))
    kicker = {"quest": "MISSION BRIEF", "myth-bust": "CLAIM", "warning": "WARNING",
              # a cover is not episode one of a series: "STEP 1" read like a tutorial part number
              "workflow": "WORKFLOW", "duel": "SIDE A", "demo-first": "DEMO", "spotlight": ""}.get(arch, "")
    made, report = [], []
    for i, concept in enumerate(concepts):
        text = concept["text"]
        src = concept_source(concept, brief, root)
        layout = concept["layout"]
        # The headline always sits on the same opaque, measured plate inside the
        # platform-safe band. Layout variety comes from the treatment of the source,
        # not moving text into the UI exclusion zones or cropping away the evidence.
        with Image.open(src) as sim:
            sim.load()
            base = Image.new("RGB", (W, H), (8, 13, 22))
            d = ImageDraw.Draw(base)
            d.rectangle((0, 0, W, 18), fill=accent)
            d.text((64, 270), "FIELD NOTES  /  AI TOOLS", font=ImageFont.truetype(
                str(ROOT / "templates/_base/fonts/JetBrainsMono.ttf"), 28), fill=(170, 183, 199))
            f, lines = fit_text(d, text, W - 144, start=125)
            lh = int(f.size * 1.09)
            text_y = 338
            box = (72, text_y, W - 72, text_y + lh * len(lines))
            if box[3] > 820:
                raise ValueError(f"headline exceeds safe headline band: {text!r}")
            plate = base.copy()
            draw_text_block(base, lines, f, accent, text_y, d, x=72)
            d.rounded_rectangle((72, 830, 1008, 1540), radius=36,
                                fill=(17, 25, 38), outline=(52, 67, 86), width=3)
            if layout == "bleed":
                # Large product visual, full panel, no accidental crop of a UI label.
                media = contain(sim, 900, 660)
                base.paste(media, ((W - media.width) // 2, 855 + (660 - media.height) // 2))
            elif layout == "window":
                # Framed app/window, with deliberately separate chrome.
                d.rounded_rectangle((104, 880, 976, 1480), radius=28, fill=(6, 11, 18),
                                    outline=accent, width=4)
                d.line((104, 950, 976, 950), fill=(52, 67, 86), width=3)
                for j, color in enumerate(((247, 111, 104), (247, 194, 90), (116, 207, 157))):
                    d.ellipse((136+j*38, 907, 154+j*38, 925), fill=color)
                media = contain(sim, 800, 480)
                base.paste(media, ((W-media.width)//2, 978 + (480-media.height)//2))
            else:
                # Editorial split: visual on a tinted field, strong index rail.
                d.rounded_rectangle((100, 858, 980, 1510), radius=26, fill=(24, 34, 49))
                d.rectangle((100, 858, 115, 1510), fill=accent)
                media = contain(sim, 816, 600)
                base.paste(media, (145 + (816-media.width)//2, 884 + (600-media.height)//2))
            d = ImageDraw.Draw(base)
            d.text((72, 1570), "ILLUSTRATED WORKFLOW", font=ImageFont.truetype(
                str(ROOT / "templates/_base/fonts/JetBrainsMono.ttf"), 22), fill=(130, 145, 163))
        p = out_dir / f"cover-{i + 1}.jpg"
        base.save(p, quality=92)
        bg = block_background(plate, box)
        made.append(p)
        with Image.open(p) as chk:
            g = chk.convert("L"); g.thumbnail((640, 640))
            from PIL import ImageStat
            std = round(ImageStat.Stat(g).stddev[0], 1)
        report.append({"concept": i, "text": text, "layout": layout, "luma_std": std,
                       "source": str(src.relative_to(root)) if src.is_relative_to(root) else str(src),
                       "file": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                       "words": len(text.split()),
                       "contrast_white": round(contrast((255, 255, 255), bg), 2),
                       "contrast_accent": round(contrast(accent, bg), 2),
                       "text_box": [round(v) for v in box]})
    from PIL import Image as I
    contact = I.new("RGB", (1080, 640), (0, 0, 0))
    for i, p in enumerate(made):
        contact.paste(cover_crop(I.open(p), 360, 640), (i * 360, 0))
    contact.save(out_dir / "sheet.jpg", quality=88)
    return made, report


def audit(report):
    """A cover set is only useful if the three concepts are really three different designs."""
    try:
        from tools import cover_rules
    except ModuleNotFoundError:
        import cover_rules
    problems = []
    if len(report) != cover_rules.CONCEPTS:
        problems.append(f"a cover set needs {cover_rules.CONCEPTS} concepts, rendered {len(report)}")
    layouts = [c["layout"] for c in report]
    if len(set(layouts)) != len(layouts):
        problems.append(f"concepts reuse a layout: {layouts}")
    sources = [c["source"] for c in report]
    if len(report) >= 3 and len(set(sources)) != len(sources) and not ALLOW_SHARED_COVER_SOURCES:
        seen, dupes = set(), set()
        for src in sources:
            (dupes if src in seen else seen).add(src)
        problems.append(f"concepts share capture images ({', '.join(sorted(dupes))}); "
                        f"each concept needs its own real media")
    for c in report:
        problems += [f"concept {c['concept']}: {p}" for p in cover_rules.headline_problems(c["text"])]
        if c.get("text_box") and (c["text_box"][1] < cover_rules.SAFE_TOP or c["text_box"][3] > cover_rules.SAFE_BOTTOM):
            problems.append(f"concept {c['concept']} headline outside safe area")
        if min(c["contrast_white"], c["contrast_accent"]) < cover_rules.CONTRAST_MIN:
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
    global ALLOW_SHARED_COVER_SOURCES
    ALLOW_SHARED_COVER_SOURCES = brief.get("id") in NO_VIDEO_STILL_ALLOWED
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
