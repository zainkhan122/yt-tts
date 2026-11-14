"""Command line.

  python3 -m graphics.cli lint  --sheet features.json --source readme.md --words words.json --beats beats.json
  python3 -m graphics.cli build --sheet features.json --source readme.md --words words.json --beats beats.json \
        --audio voice.mp3 --duration 36.07 --out out.mp4 --work build/

Exit codes: 0 ok, 2 feature sheet fails lint, 3 beat plan fails lint, 4 render failed.
Lint runs before any render. Nothing is rendered from a plan that fails.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .beats import lint_beats, scene_list
from .features import Violation, lint_feature_sheet
from .stage import build_doc
from .timing import close_gaps, phrases_for_scenes


def _load(p: str):
    return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def _plan(args):
    sheet = _load(args.sheet)
    source = Path(args.source).read_text(encoding="utf-8")
    words = _load(args.words)
    beats = _load(args.beats)
    f_viol = lint_feature_sheet(sheet, source)
    if f_viol:
        return None, f_viol, 2
    # One phrase per beat scene, split on the pauses in the track — the same segmentation the
    # production adapter and the preview harness use (a beat plan is linted against the timeline
    # it will actually be rendered with).
    phrases = phrases_for_scenes(words, beats.get("scenes") or [])
    if not phrases:
        return None, [Violation("G0", "no words to segment into scenes")], 2
    duration = args.duration if getattr(args, "duration", None) else round(words[-1][2] + 0.3, 3)
    closed = close_gaps(phrases, duration)
    b_viol = lint_beats(beats, closed, sheet)
    if b_viol:
        return None, b_viol, 3
    doc = build_doc(sheet, beats, closed)
    return {"doc": doc, "duration": duration, "phrases": closed}, [], 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="graphics")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("lint", "build"):
        s = sub.add_parser(name)
        s.add_argument("--sheet", required=True)
        s.add_argument("--source", required=True)
        s.add_argument("--words", required=True)
        s.add_argument("--beats", required=True)
        s.add_argument("--duration", type=float)
        if name == "build":
            s.add_argument("--audio", required=True)
            s.add_argument("--out", required=True)
            s.add_argument("--work", required=True)
    args = ap.parse_args(argv)

    plan, violations, code = _plan(args)
    if violations:
        print(json.dumps({"ok": False, "violations": [v.as_dict() for v in violations]}, indent=2))
        return code
    print(f"lint ok: {len(plan['phrases'])} phrases -> {len(plan['doc']['scenes'])} scenes, "
          f"{plan['duration']:.2f}s")
    if args.cmd == "lint":
        return 0

    from .render import render
    work = Path(args.work)
    work.mkdir(parents=True, exist_ok=True)
    (work / "scenes.json").write_text(json.dumps(plan["doc"], indent=1, ensure_ascii=False), encoding="utf-8")
    try:
        info = render(plan["doc"], Path(args.audio), Path(args.out), work, plan["duration"])
    except Exception as e:  # noqa: BLE001 - reported with a non-zero exit, never swallowed
        print(json.dumps({"ok": False, "render_error": str(e)}))
        return 4
    print(json.dumps({"ok": True, **info}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
