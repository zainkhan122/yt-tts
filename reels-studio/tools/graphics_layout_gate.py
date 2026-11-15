#!/usr/bin/env python3
"""Local layout gate for a GRAPHICS short — the tier's own gates, before any cloud dispatch.

WHY (owner, 2026-11-15): the spotlight layout audit (tools/layout_audit.py) measures the
spotlight tier's composition. A graphics brief is drawn by a different engine, so that audit
either does not apply or — worse — reports a confusing failure. The graphics tier has its own
layout gates inside the renderer (caption band reserved, nothing past the frame edge), but they
only ran inside the cloud render, so a bad layout cost a full cloud cycle to find out.

This tool builds the same scene document the pipeline would build, opens it in a real browser and
runs those same gates locally. Seconds, not a cloud cycle.

    python3 tools/graphics_layout_gate.py briefs/<id>.json
    exits 0 when the layout is clean, 1 when it is not.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from graphics.render import build_stage_html, is_house, stage_fonts, stage_layout_gates, W, H  # noqa: E402
from graphics.stage import (attach_evidence_clips, attach_evidence_images, flatten_words,  # noqa: E402
                            plan_scenes, segments_from_timing)


def fake_timing(brief: dict, wpm: float = 210.0, gap: float = 0.26) -> tuple[dict, list[str], float]:
    """One phrase per brief scene, words spread at `wpm` — the same fake clock the local preview
    uses. The gates measure geometry, and geometry does not depend on the real voice."""
    per_word = 60.0 / wpm
    t = 0.12
    timing, order = {}, []
    for sc in brief.get("scenes") or []:
        words = []
        for w in str(sc.get("say") or "").split():
            words.append([w, round(t, 3), round(t + per_word, 3)])
            t += per_word
        timing[sc["id"]] = {"words": words, "text": sc.get("say", "")}
        order.append(sc["id"])
        t += gap
    return timing, order, t


def build_doc(brief: dict, gdir: Path):
    sheet = json.loads((gdir / "features.json").read_text(encoding="utf-8"))
    source = (gdir / "source.md").read_text(encoding="utf-8")
    beats = json.loads((gdir / "beats.json").read_text(encoding="utf-8"))
    timing, order, duration = fake_timing(brief)
    words = flatten_words(timing, order)
    phrases = segments_from_timing(timing, order)
    doc, _phrases = plan_scenes(sheet, source, beats, phrases, duration, words,
                                events={"press": round(duration - 1.6, 3)})
    attach_evidence_images(doc, gdir.name)
    attach_evidence_clips(doc, gdir.name)
    return doc, duration


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("brief", help="path to the brief json, or its brief id")
    ap.add_argument("--shots", help="write the probe frames to this directory")
    args = ap.parse_args(argv)

    brief_path = Path(args.brief)
    if not brief_path.exists():
        brief_path = ROOT / "briefs" / f"{args.brief}.json"
    if not brief_path.exists():
        print(f"GRAPHICS-LAYOUT: brief not found: {args.brief}", file=sys.stderr)
        return 2
    brief = json.loads(brief_path.read_text(encoding="utf-8"))
    if brief.get("renderer") != "graphics":
        print(f"GRAPHICS-LAYOUT {brief.get('id')}: not a graphics brief (renderer="
              f"{brief.get('renderer')!r}) — nothing to check here")
        return 0
    gdir_rel = (brief.get("graphics") or {}).get("dir") or f"briefs/graphics/{brief.get('id')}"
    gdir = (ROOT / gdir_rel).resolve()
    if not (gdir / "beats.json").exists():
        print(f"GRAPHICS-LAYOUT {brief.get('id')}: no beat plan at {gdir_rel}", file=sys.stderr)
        return 2

    doc, duration = build_doc(brief, gdir)
    from playwright.sync_api import sync_playwright

    with tempfile.TemporaryDirectory(prefix="graphics-layout-") as tmp:
        work = Path(tmp)
        stage_fonts(work)
        html = work / "stage.html"
        html.write_text(build_stage_html(doc, work), encoding="utf-8")
        cap_top = 1470 if is_house(doc) else 1210
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox", "--font-render-hinting=none",
                                              "--allow-file-access-from-files"])
            page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
            page.goto(html.as_uri())
            page.wait_for_function("window.ready === true", timeout=30000)
            problems = stage_layout_gates(page, doc, cap_top)
            if args.shots:
                shots = Path(args.shots)
                shots.mkdir(parents=True, exist_ok=True)
                for sc in doc["scenes"]:
                    t = float(sc["t0"]) + 0.6
                    page.evaluate(f"window.setTime({t:.4f})")
                    page.screenshot(path=str(shots / f"{sc.get('id', 'scene')}.jpg"), type="jpeg", quality=90)
            browser.close()

    if problems:
        print(f"GRAPHICS-LAYOUT {brief.get('id')}: FAIL ({len(problems)} problem(s))")
        for p_ in problems:
            print(f"  x {p_}")
        return 1
    print(f"GRAPHICS-LAYOUT {brief.get('id')}: PASS (caption band clear, nothing past the frame; "
          f"{len(doc['scenes'])} scenes, {round(duration, 1)}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
