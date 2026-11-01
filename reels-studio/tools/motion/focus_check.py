#!/usr/bin/env python3
"""Pre-render check for image-scene focus moves (lesson: 2026-10-31 claude-mem).

Fails if a focus box PARTLY covers something the brief says must stay whole
(scene.keep_visible = [[x0,x1], ...], normalised 0-1 along the image width),
or if a scene holds still too long (no box change within MAX_HOLD_S).

Usage: python3 tools/motion/focus_check.py briefs/<id>.json   (exit 1 on failure)
"""
import json
import sys
from pathlib import Path

MAX_HOLD_S = 4.5          # owner standard: a visual change at least every 4-5 s
WORDS_PER_S = 2.5         # rough narration pace for the hold estimate


def check_scene(s):
    problems = []
    steps = s.get("focus") or []
    keep = s.get("keep_visible") or []
    band = s.get("keep_band")  # [y0, y1] normalised: where the labels sit; boxes outside it may cut freely
    for st in steps:
        x, y, w, h = st["box"]
        if band and not (y < band[1] and y + h > band[0]):
            continue
        for lo, hi in keep:
            overlaps = x < hi and x + w > lo
            contains = x <= lo and x + w >= hi
            if overlaps and not contains:
                problems.append(
                    f"{s['id']} @{st['at']}s: box x {x:.2f}-{x + w:.2f} cuts label {lo:.2f}-{hi:.2f}")
    if s.get("type") == "image":
        if len(steps) < 2:
            est = len((s.get("say") or "").split()) / WORDS_PER_S
            if est > MAX_HOLD_S:
                problems.append(
                    f"{s['id']}: static for about {est:.1f} s with one focus step (limit {MAX_HOLD_S} s)")
        else:
            gaps = [b["at"] - a["at"] for a, b in zip(steps, steps[1:])]
            if steps[0]["at"] > MAX_HOLD_S or max(gaps) > MAX_HOLD_S:
                problems.append(f"{s['id']}: holds longer than {MAX_HOLD_S} s between focus steps")
    return problems


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    brief = json.loads(Path(argv[0]).read_text())
    problems = []
    for s in brief.get("scenes") or []:
        problems += check_scene(s)
    for p in problems:
        print("FAIL", p)
    print("focus check:", "PASS" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
