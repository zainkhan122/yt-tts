#!/usr/bin/env python3
"""Creative variety check: is the channel falling back into one template?

Reads treatments across briefs and reports the archetype run. Two identical
formats in a row is a smell; three is the template sneaking back in and this
tool exits non-zero (PLAYBOOK §8A).

  python3 tools/creative_check.py [briefs-dir]
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    d = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "briefs"
    rows = []
    for p in sorted(d.glob("*.json"), key=lambda x: x.stat().st_mtime):
        try:
            b = json.loads(p.read_text())
        except Exception:
            continue
        tr = b.get("treatment") or {}
        if tr.get("archetype"):
            rows.append((b["id"], tr["archetype"], tr.get("audience", "?")))
    for vid, arch, aud in rows:
        print(f"{vid:34s} {arch:12s} for {aud}")
    streak = 1
    for i in range(1, len(rows)):
        streak = streak + 1 if rows[i][1] == rows[i - 1][1] else 1
        if streak >= 3:
            print(f"FAIL: {streak} '{rows[i][1]}' videos in a row — vary the format")
            return 1
    print("variety ok" if rows else "no treatments found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
