#!/usr/bin/env python3
"""Build one 1080x1440 kit image per plan point, from the plan's own visual spec.

The plan (videos/<id>/plan.json) is the brain: it names each point's visual kind and the rows,
chips, steps, tiers or asset it needs. This script only draws what the plan says. Nothing about the
tool is written here.

Output: captures/<id>/plan-<n>.jpg, and captures/<id>/plan-keep.json with keep_visible ranges
(normalised to height) for tools/motion/focus_check.py.

Usage: python3 tools/motion/build_plan_kit.py videos/<id>/plan.json
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
FONT_HEAD = ROOT / "templates" / "_base" / "fonts" / "Anton.ttf"
FONT_TEXT = ROOT / "templates" / "_base" / "fonts" / "Inter.ttf"
W, H = 1080, 1440
BG = (11, 15, 26)
WHITE = (255, 255, 255)
MUTED = (150, 160, 180)
ACCENT = (250, 204, 21)
RED = (248, 113, 113)
GREEN = (74, 222, 128)
BLUE = (96, 165, 250)
CARD = (22, 28, 44)
LINE = (40, 48, 66)


def f(path, size):
    return ImageFont.truetype(str(path), size)


def wrap(d, text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def header(d, title):
    d.text((60, 70), title.upper(), font=f(FONT_HEAD, 84), fill=WHITE)
    d.rectangle((60, 190, 260, 198), fill=ACCENT)


def draw_findings(img, d, p, top):
    f34, f32, f24 = f(FONT_TEXT, 34), f(FONT_TEXT, 32), f(FONT_TEXT, 24)
    d.text((60, top), "EVALS SAY", font=f34, fill=MUTED)
    d.text((560, top), "AUDIT FINDS", font=f34, fill=MUTED)
    d.line((60, top + 52, 1020, top + 52), fill=LINE, width=2)
    y = top + 80
    for r in p["rows"]:
        col = GREEN if r["severity"].lower() == "passed" else RED
        d.rounded_rectangle((60, y, 1020, y + 102), radius=18, fill=CARD)
        d.text((88, y + 20), r["step"], font=f32, fill=WHITE)
        d.text((88, y + 62), "Evals: " + r["eval"], font=f24, fill=GREEN)
        d.text((560, y + 20), r["finding"], font=f32, fill=WHITE)
        d.rounded_rectangle((560, y + 62, 790, y + 102), radius=10, fill=col)
        d.text((580, y + 66), r["severity"].upper(), font=f24, fill=BG)
        y += 118
    return y


def draw_chips(img, d, p, top):
    f32 = f(FONT_TEXT, 32)
    x, y = 60, top + 40
    for chip in p["chips"]:
        tw = d.textlength(chip, font=f32) + 52
        if x + tw > 1020:
            x, y = 60, y + 96
        d.rounded_rectangle((x, y, x + tw, y + 74), radius=37, fill=CARD, outline=BLUE, width=3)
        d.text((x + 26, y + 17), chip, font=f32, fill=WHITE)
        x += tw + 22
    return y + 74


def draw_steps(img, d, p, top):
    f40, f28 = f(FONT_HEAD, 56), f(FONT_TEXT, 30)
    y = top + 40
    for i, s in enumerate(p["steps"], 1):
        d.ellipse((60, y, 60 + 96, y + 96), fill=ACCENT)
        d.text((60 + 30, y + 14), str(i), font=f40, fill=BG)
        d.text((200, y + 26), s, font=f28, fill=WHITE)
        if i < len(p["steps"]):
            d.line((108, y + 96, 108, y + 176), fill=LINE, width=4)
        y += 176
    return y


def draw_tiers(img, d, p, top):
    f32, f28 = f(FONT_HEAD, 60), f(FONT_TEXT, 30)
    y = top + 40
    for i, t in enumerate(p["tiers"]):
        col = GREEN if i == 0 else BLUE
        d.rounded_rectangle((60, y, 1020, y + 180), radius=24, fill=CARD)
        d.rectangle((60, y, 80, y + 180), fill=col)
        d.text((120, y + 30), t.split(":")[0].upper(), font=f32, fill=col)
        rest = t.split(":", 1)[1].strip() if ":" in t else ""
        for j, line in enumerate(wrap(d, rest, f28, 860)[:2]):
            d.text((120, y + 100 + j * 38), line, font=f28, fill=WHITE)
        y += 210
    return y


def draw_chart(img, d, p, top):
    chart = Image.open(ROOT / p["asset"]).convert("RGB")
    cw = 1000
    ch = round(chart.height * cw / chart.width)
    img.paste(chart.resize((cw, ch), Image.LANCZOS), ((W - cw) // 2, top))
    return top + ch


def build(plan_path):
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    cap = ROOT / "captures" / plan["id"]
    cap.mkdir(parents=True, exist_ok=True)
    keep = {}
    for p in plan["points"]:
        kind = p["visual"]["kind"]
        if kind == "animation":          # built by tools/motion/make_ifixai_anim.py, not a card
            continue
        drawers = {"findings": draw_findings, "chips": draw_chips, "steps": draw_steps,
                   "tiers": draw_tiers, "chart": draw_chart}
        if kind not in drawers:
            raise SystemExit(f"point {p['n']}: visual kind '{kind}' has no drawer")

        def render(top):
            im = Image.new("RGB", (W, H), BG)
            dr = ImageDraw.Draw(im)
            header(dr, p.get("title", f"Point {p['n']}"))
            return im, drawers[kind](im, dr, p, top)

        # Measuring pass, then centre the block in the 9:16 card (lesson 14: no empty third).
        _, measured_end = render(250)
        block_h = measured_end - 250
        top = max(250, (H - block_h) // 2)
        img, end = render(top)
        out = cap / f"plan-{p['n']}.jpg"
        img.save(out, quality=92)
        keep[f"plan-{p['n']}"] = [round(max(0, top - 20) / H, 3), round(min(end + 20, H) / H, 3)]
        print("wrote", out.relative_to(ROOT), "keep", keep[f"plan-{p['n']}"])
    # The catch card, drawn from catch_visual the same way as a point (unless it is an animation file).
    cv = plan.get("catch_visual") or {}
    if cv.get("kind") and cv["kind"] != "animation":
        catch_pt = {"n": "catch", "title": plan.get("catch_title", "The catch"), "sub": plan.get("catch_sub", ""),
                    "visual": cv, **{k: v for k, v in cv.items() if k not in ("kind", "intent")}}
        kind = cv["kind"]
        drawers = {"findings": draw_findings, "chips": draw_chips, "steps": draw_steps, "tiers": draw_tiers, "chart": draw_chart}
        if kind not in drawers:
            raise SystemExit(f"catch visual kind '{kind}' has no drawer")

        def render_catch(top):
            im = Image.new("RGB", (W, H), BG)
            dr = ImageDraw.Draw(im)
            header(dr, catch_pt["title"])
            return im, drawers[kind](im, dr, catch_pt, top)

        _, measured_end = render_catch(250)
        top = max(250, (H - (measured_end - 250)) // 2)
        img, end = render_catch(top)
        out = cap / "plan-catch.jpg"
        img.save(out, quality=92)
        keep["plan-catch"] = [round(max(0, top - 20) / H, 3), round(min(end + 20, H) / H, 3)]
        print("wrote", out.relative_to(ROOT), "keep", keep["plan-catch"])
    (cap / "plan-keep.json").write_text(json.dumps(keep, indent=2), encoding="utf-8")
    write_manifest(plan, cap)
    return keep


def write_manifest(plan, cap):
    """captures/<id>/manifest.json: every kit image with its sha256, read by tools/receipt_build.py.
    The facts are the plan's own sources, so the receipt can show where each card's words came from."""
    import datetime as dt
    import hashlib
    files = {}
    for path in sorted(cap.glob("plan-*.jpg")):
        n = path.stem.removeprefix("plan-")
        kind = "own graphic: card built from the plan's visual spec"
        if n == "catch":
            kind = "own graphic: catch card built from the plan's catch visual"
        files[path.stem] = {"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "kind": kind}
    sources = [p["source"] for p in plan["points"]]
    manifest = {
        "id": plan["id"],
        "url": plan.get("repo_url") or sources[0],
        "captured": dt.date.today().isoformat(),
        "facts": {"source": "maker README and repo page, read on the day of the plan", "sources": sources},
        "files": files,
    }
    (cap / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("wrote", (cap / "manifest.json").relative_to(ROOT), len(files), "files")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    build(sys.argv[1])
