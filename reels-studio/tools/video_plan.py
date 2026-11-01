#!/usr/bin/env python3
"""Validate an agent-written video plan. The plan is the brain; this file only checks it.

A plan lives at videos/<id>/plan.json and is written by the agent from the tool's own material.
Nothing in the plan is supplied by a template. The checks below enforce the owner's rules:

  * one viewer question, ending with '?'
  * 1 to 5 points, numbered 1..n, each with a claim, a spoken line and a source URL (https)
  * spoken lines: no digits (no exact figures), no URLs, no legal/licence/terms/privacy words,
    at most 180 characters
  * every point has a visual of a known kind with the fields that kind needs
  * an asset named in a plan must exist in the workspace
  * a catch line (the cost, limit or what it cannot do)

Exit 0 = PASS, 1 = BLOCK. Usage:
  python3 tools/video_plan.py videos/repo-ifixai-01/plan.json
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VISUAL_KINDS = {
    "findings": ("rows",),
    "chips": ("chips",),
    "steps": ("steps",),
    "chart": ("asset",),
    "tiers": ("tiers",),
    "clip": ("asset",),
    "diagram": ("intent",),
}
LEGAL = re.compile(r"\b(licen[cs]e[ds]?|licensing|terms|privacy|legal|copyright|gdpr|tos)\b", re.I)
MAX_CHARS = 180


def check(plan):
    res = []

    def add(ok, msg):
        res.append(("PASS" if ok else "BLOCK", msg))

    q = plan.get("question", "")
    add(bool(q) and q.strip().endswith("?"), "viewer question present and ends with '?'")
    pts = plan.get("points", [])
    add(1 <= len(pts) <= 5, f"points: {len(pts)} (must be 1 to 5)")
    add([p.get("n") for p in pts] == list(range(1, len(pts) + 1)), "points numbered 1..n in order")
    for p in pts:
        n = p.get("n")
        spoken = p.get("spoken", "")
        add(bool(p.get("claim")), f"point {n}: claim written")
        add(bool(spoken), f"point {n}: spoken line written")
        add(not re.search(r"\d", spoken), f"point {n}: no digits in spoken line (no exact figures)")
        add("http" not in spoken and "www." not in spoken, f"point {n}: no URL in spoken line")
        add(not LEGAL.search(spoken), f"point {n}: no legal/licence/terms wording in spoken line")
        add(len(spoken) <= MAX_CHARS, f"point {n}: spoken line within {MAX_CHARS} characters")
        src = p.get("source", "")
        add(src.startswith("https://"), f"point {n}: source is https")
        vis = p.get("visual") or {}
        kind = vis.get("kind")
        add(kind in VISUAL_KINDS, f"point {n}: visual kind '{kind}' is known")
        for field in VISUAL_KINDS.get(kind, ()):
            add(bool(p.get(field)) if field != "intent" else bool(vis.get("intent")),
                f"point {n}: visual has '{field}'")
        if p.get("asset"):
            add((ROOT / p["asset"]).exists(), f"point {n}: asset exists {p['asset']}")
    catch = plan.get("catch", "")
    add(bool(catch), "catch line written (cost, limit or what it cannot do)")
    add(not re.search(r"https?://", catch), "no URL in catch line")
    return res


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    path = Path(argv[1])
    plan = json.loads(path.read_text(encoding="utf-8"))
    results = check(plan)
    for status, msg in results:
        print(f"{status:5} {msg}")
    blocked = [m for s, m in results if s == "BLOCK"]
    print("PLAN", "PASS" if not blocked else f"BLOCK ({len(blocked)} problem(s))")
    return 0 if not blocked else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
