#!/usr/bin/env python3
"""Media fallback: a scene whose tool has no usable media gets a generated feature card.

Owner rule (4 Nov 2026): a tool with no media does not fail the Short. The card is drawn from the tool's own
features (plan `points` titles, else the other scene headings, else the SEO keywords), and its focus boxes move
from one feature to the next in step with the voice. The timing comes from the script's word count at the plan
speech rate, so the same spoken line drives the card; the render's real word timings are measured afterwards by
tools/short_qa.py.

A scene is a fallback candidate when its `image` (or a `clip`'s `src`) is neither in the capture pack on disk nor
recorded in the pushed release pack. Image scenes keep their type. A clip scene becomes an image card that keeps
its say line, heading and sub, so the spoken line still plays over a moving picture.

Output: captures/<id>/generated/<scene-id>.png (inside the pack, so the release push carries it) and the brief
is updated in place. Idempotent: a scene that already has its media is left alone.

  python3 tools/feature_card.py <brief-id>
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORTRAIT = (1080, 1440)
BAND_TOP, BAND_BOTTOM = 470, 1110     # the card content sits between the engine heading and the caption zone
MIN_FEATURES = 2
MAX_FEATURES = 5
FONT_BOLD = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
FONT_REG = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")


class FallbackError(RuntimeError):
    """A scene has no media and no features to draw a card from."""


def _thresholds() -> dict:
    return json.loads((ROOT / "config" / "qa-thresholds.json").read_text(encoding="utf-8"))


def _words(text) -> list[str]:
    return re.findall(r"[A-Za-z0-9][A-Za-z0-9'\u2019\-]*", str(text or ""))


def pushed_files(cap: str, root: Path | None = None) -> set[str]:
    path = (Path(root) if root else ROOT) / "tracker" / "capture-pushes.json"
    if not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    return set((data.get(cap) or {}).get("files") or {})


def media_missing(scene: dict, cap: str, cap_dir: Path, pushed: set[str]) -> str | None:
    """The media path the scene needs, when it is neither local nor pushed; else None."""
    if scene.get("type") == "image":
        ref = scene.get("image")
    elif scene.get("type") == "clip":
        ref = scene.get("src")
    else:
        return None
    if not ref:
        return ref or "(none)"
    if (cap_dir / ref).exists() or ref in pushed:
        return None
    return ref


def features_for(brief: dict, plan: dict | None) -> list[str]:
    """The tool's own features, in order: plan points, else the other scene headings, else SEO keywords."""
    if plan and plan.get("points"):
        feats = [str(p.get("title") or p.get("claim") or "").strip() for p in plan["points"]]
    else:
        feats = [str(s.get("heading") or "").strip() for s in brief.get("scenes") or [] if s.get("id") != "hook"]
    feats = [f for f in feats if f]
    if len(feats) < MIN_FEATURES:
        feats = [str(k).strip() for k in (brief.get("keywords") or []) if str(k).strip()]
    seen, out = set(), []
    for f in feats:
        if f.lower() not in seen:
            seen.add(f.lower())
            out.append(f)
    return out[:MAX_FEATURES]


def _font(path: Path, size: int):
    from PIL import ImageFont
    if path.exists():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size=size)


def row_rects(n: int, size=PORTRAIT) -> list[tuple[int, int, int, int]]:
    """Pixel rectangles (x0, y0, x1, y1) for n feature rows inside the content band."""
    w, _ = size
    gap = 24
    row_h = (BAND_BOTTOM - BAND_TOP - gap * (n - 1)) // n
    return [(60, BAND_TOP + i * (row_h + gap), w - 60, BAND_TOP + i * (row_h + gap) + row_h) for i in range(n)]


def render_card(features: list[str], out: Path) -> list[list[float]]:
    """Draw the feature card (portrait) and return each row as a normalised [x, y, w, h] box."""
    from PIL import Image, ImageDraw
    W, H = PORTRAIT
    img = Image.new("RGB", (W, H), (11, 16, 32))
    draw = ImageDraw.Draw(img)
    for y in range(H):  # a quiet vertical gradient, so the card never reads as an empty frame
        t = y / H
        draw.line([(0, y), (W, y)], fill=(int(11 + 14 * t), int(16 + 20 * t), int(32 + 36 * t)))
    rects = row_rects(len(features), PORTRAIT)
    bold, reg = _font(FONT_BOLD, 58), _font(FONT_REG, 40)
    for i, ((x0, y0, x1, y1), text) in enumerate(zip(rects, features)):
        draw.rounded_rectangle((x0, y0, x1, y1), radius=28, fill=(22, 31, 58), outline=(60, 78, 128), width=3)
        draw.rounded_rectangle((x0 + 26, y0 + 26, x0 + 26 + 78, y0 + 26 + 78), radius=18, fill=(255, 107, 61))
        draw.text((x0 + 65, y0 + 65), f"{i + 1}", font=reg, fill=(11, 16, 32), anchor="mm")
        label = text if len(text) <= 36 else text[:33].rstrip() + "..."
        draw.text((x0 + 130, (y0 + y1) // 2), label, font=bold if len(label) <= 24 else reg,
                  fill=(240, 244, 255), anchor="lm")
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, format="PNG", optimize=True)
    return [[round(x0 / W, 4), round(y0 / H, 4), round((x1 - x0) / W, 4), round((y1 - y0) / H, 4)]
            for (x0, y0, x1, y1) in rects]


def focus_schedule(say: str, boxes: list[list[float]], wpm: float, whole_band: list[float]) -> list[dict]:
    """One focus step per feature, timed from the spoken words (even split across the line), plus an opening view."""
    words = len(_words(say))
    per_word = 60.0 / wpm
    steps = [{"box": whole_band, "at": 0.0, "pad": 1.0}]
    for i, box in enumerate(boxes):
        start_word = (i * words) // len(boxes)
        steps.append({"box": box, "at": round(start_word * per_word, 2), "pad": 1.0})
    return steps


def ensure_media(brief_id: str, root: Path | None = None) -> dict:
    """Generate feature cards for scenes without media. Returns a summary; writes the brief only when it changed."""
    root = Path(root) if root else ROOT
    path = root / "briefs" / f"{brief_id}.json"
    brief = json.loads(path.read_text(encoding="utf-8"))
    cap = Path(str(brief.get("capture") or "")).name
    if not cap:
        raise FallbackError(f"{brief_id}: no capture pack, so there is nowhere to put a generated card")
    cap_dir = root / "captures" / cap
    pushed = pushed_files(cap, root)
    plan_path = root / "videos" / brief_id / "plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8")) if plan_path.exists() else None
    th = _thresholds()
    changed, generated = False, []
    for scene in brief.get("scenes") or []:
        ref = media_missing(scene, cap, cap_dir, pushed)
        if ref is None:
            continue
        features = features_for(brief, plan)
        if len(features) < MIN_FEATURES:
            raise FallbackError(f"{brief_id}: scene {scene.get('id')} has no media ({ref}) and fewer than "
                                f"{MIN_FEATURES} features to draw a card from; add plan points")
        sid = re.sub(r"[^A-Za-z0-9_-]", "-", str(scene.get("id") or "scene"))
        rel = f"generated/{sid}.png"
        boxes = render_card(features, cap_dir / rel)
        n_words = len(_words(scene.get("say")))
        whole = [0.06, round(BAND_TOP / PORTRAIT[1], 4), 0.88, round((BAND_BOTTOM - BAND_TOP) / PORTRAIT[1], 4)]
        if scene.get("type") == "clip":
            keep = {k: scene[k] for k in ("id", "say", "heading", "sub") if k in scene}
            scene.clear()
            scene.update({"type": "image", **keep})
        scene["image"] = rel
        scene["generated"] = "feature-card"
        scene["focus"] = focus_schedule(scene.get("say"), boxes, th["speech_wpm_plan_estimate"], whole)
        scene.pop("src", None)
        changed = True
        generated.append({"scene": scene.get("id"), "file": f"captures/{cap}/{rel}", "features": len(features),
                          "words": n_words})
    if changed:
        path.write_text(json.dumps(brief, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"id": brief_id, "generated": generated, "changed": changed}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("brief_id")
    args = ap.parse_args(argv)
    try:
        summary = ensure_media(args.brief_id)
    except (FallbackError, OSError, ValueError) as exc:
        print(f"BLOCK  {args.brief_id}: {exc}")
        return 1
    if not summary["generated"]:
        print(f"PASS   {args.brief_id}: every scene has media")
    for g in summary["generated"]:
        print(f"GEN    {g['scene']}: {g['file']} ({g['features']} features, {g['words']} words)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
