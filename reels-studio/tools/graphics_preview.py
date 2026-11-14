"""Verification harness for the house visual system.

Builds the scene document and the stage HTML from a beat plan without rendering a video, so the
linter, the cue binding and the HTML/JS contract can be checked anywhere.

    py -3 tools/graphics_preview.py <beats.json> [--features f.json] [--out dir]

It prints the lint result, the resolved visual language, the cue plan, and writes stage.html plus a
frames/ directory of PNGs when Playwright is available.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from graphics.beats import lint_beats, scene_list, script_fingerprint  # noqa: E402
from graphics.cues import compute  # noqa: E402
from graphics.features import lint_feature_sheet  # noqa: E402
from graphics.render import build_stage_html, stage_fonts  # noqa: E402
from graphics.stage import brand_block, build_doc  # noqa: E402
from graphics.timing import close_gaps, phrases_for_scenes  # noqa: E402
from graphics.visual_language import language_for, palette_for  # noqa: E402


def _phrases_from_words(beats: dict, words: list[list], gap: float = 0.42) -> list[dict]:
    """Split the word track into one phrase per beat scene.

    A pause in the voice is a scene boundary — the same rule the production adapter uses (one brief
    scene per spoken phrase). Falls back to even weighting when the track has no pauses.
    """
    return phrases_for_scenes(words, beats.get("scenes") or [], gap_s=gap)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("beats")
    ap.add_argument("--features")
    ap.add_argument("--source")
    ap.add_argument("--out", default=str(ROOT / "work" / "graphics-preview"))
    ap.add_argument("--frames", type=int, default=0, help="how many stills to grab (needs playwright)")
    args = ap.parse_args()

    beats_path = Path(args.beats).resolve()
    beats = json.loads(beats_path.read_text(encoding="utf-8-sig"))
    sheet = json.loads(Path(args.features or beats_path.with_name("features.json")).read_text(encoding="utf-8-sig"))
    source = Path(args.source or beats_path.with_name("source.md"))
    source_text = source.read_text(encoding="utf-8") if source.exists() else ""

    fviol = lint_feature_sheet(sheet, source_text)
    print("feature sheet:", "OK" if not fviol else [v.as_dict() for v in fviol])

    # A word track: the real one from words.json when the fixture has it, otherwise a synthetic one
    # so the cue binder always has something to bind to.
    words_path = beats_path.with_name("words.json")
    if words_path.exists():
        words = json.loads(words_path.read_text(encoding="utf-8-sig"))
    else:
        words = []
        t = 0.0
        for sc in beats["scenes"]:
            for chunk in sc["payload"].get("cue_phrases") or sc["payload"].get("chips") or \
                    sc["payload"].get("nodes") or sc["payload"].get("steps") or sc["payload"].get("lines") or \
                    sc["payload"].get("labels") or [sc.get("depicts", "")]:
                for w in str(chunk).split():
                    words.append([w, round(t, 3), round(t + 0.22, 3)])
                    t += 0.22
            t += 0.5
    phrases = _phrases_from_words(beats, words)
    # The preview must show the timeline the renderer will use: gaps closed, first scene at 0.
    duration = round(float(words[-1][2]) + 0.3, 3) if words else 1.0
    phrases = close_gaps(phrases, duration)

    bviol = lint_beats(beats, phrases, sheet, script_fp=None)
    print("beat plan:", "OK" if not bviol else [v.as_dict() for v in bviol])

    lang = language_for(sheet.get("tool"))
    print("visual language:", json.dumps({k: lang[k] for k in ("category", "label", "plates", "palette")},
                                          ensure_ascii=False))
    print("palette:", json.dumps(palette_for(sheet.get("tool"))))

    scenes = scene_list(beats, phrases)
    for s in scenes:
        print(f"  {s['id']:>4}  {s['archetype']:<14} t0={s['t0']:>6.2f} t1={s['t1']:>6.2f} "
              f"cue={s['cue']:>6.2f} cues={s['cues']} fallback={s.get('fallback')}")

    doc = build_doc(sheet, beats, phrases)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    stage_fonts(out)
    html = out / "stage.html"
    html.write_text(build_stage_html(doc, out), encoding="utf-8")
    (out / "scenes.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    print("stage html:", html)

    if args.frames:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("frames: playwright is not installed — skipped")
            return 0
        dur = max(s["t1"] for s in scenes)
        with sync_playwright() as p:
            b = p.chromium.launch(args=["--no-sandbox", "--font-render-hinting=none",
                                         "--allow-file-access-from-files"])
            page = b.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
            page.goto(html.as_uri())
            page.wait_for_function("window.ready === true", timeout=30000)
            step = dur / max(1, args.frames)
            for i in range(args.frames):
                t = min(dur - 0.05, i * step)
                page.evaluate(f"window.setTime({t:.3f})")
                page.screenshot(path=str(out / f"frame-{i:02d}.png"))
                print(f"  frame {i:02d} t={t:.2f}")
            b.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
