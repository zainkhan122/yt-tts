#!/usr/bin/env python3
"""Hook panel: author Shorts hooks against the 21 calibrated formulas, scored before scripting.

Backed by the vendored youtube-agent-skill (MIT) hookscore.py + hooks.json. Scores are ADVISORY:
the upstream calibration (74 real hooks) separates deliberately-bad hooks from real ones; it does
not predict hits. A WEAK score is a reason to look again, never a block; high is not a promise.

  python3 tools/hook_panel.py formulas                 -> the 21 formulas: shape, example, fails-when
  python3 tools/hook_panel.py score "HOOK" ["HOOK2"]   -> ranked 5-property panel per candidate
  python3 tools/hook_panel.py score --brief repo-x-01  -> scores the brief's current hook (scene 0)
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
X = ROOT / "tools" / "external" / "youtube-agent-skill"
sys.path.insert(0, str(X))
import hookscore  # noqa: E402

FORMULAS = json.loads((X / "hooks.json").read_text(encoding="utf-8"))["hooks"]


def menu():
    for f in FORMULAS:
        print(f"- {f['name']}: {f['shape']}\n    e.g. {f.get('example','')[:110]}\n    fails when: {f.get('fails_when','')[:110]}")


def rank(hooks):
    out = []
    for h in hooks:
        parts, verdict, name, hits = hookscore.score(h)
        out.append((verdict, h, parts, name))
    out.sort(key=lambda r: -r[0])
    for verdict, h, parts, name in out:
        wname, wval = min(parts.items(), key=lambda kv: kv[1])
        print(f"  {verdict:>3} {hookscore.band(verdict):<8} [{name}]")
        print("    " + h)
        print(f"    weakest: {wname} {wval}")


def main():
    a = sys.argv[1:]
    if not a or a[0] not in ("formulas", "score"):
        print(__doc__); return 2
    if a[0] == "formulas":
        menu(); return 0
    b = a[1:]
    if b and b[0] == "--brief":
        brief = json.loads((ROOT / "briefs" / f"{b[1]}.json").read_text(encoding="utf-8"))
        s0 = brief["scenes"][0]
        first = str(s0.get("say", "")).split(". ")[0]
        rank([f"{s0.get('heading','')} / {first}"] if s0.get("heading") else [first])
        return 0
    rank(b)
    return 0


if __name__ == "__main__":
    sys.exit(main())
