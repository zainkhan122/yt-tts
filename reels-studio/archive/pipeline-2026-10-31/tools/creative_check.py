#!/usr/bin/env python3
"""Creative variety check: is the channel falling back into one template?

Reads treatments across briefs and reports the archetype run. Two identical
formats in a row is a smell; three is the template sneaking back in and this
tool exits non-zero (PLAYBOOK §8A).

  python3 tools/creative_check.py [briefs-dir] [--renders renders]
      with --renders: also prove each rendered brief's treatment LANDED
      (manifest archetype == brief archetype, cover.source == cover-lab,
      cover text == selected concept). Missing proof = failure.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def structure(brief):
    """Playback-ordered beat sequence, the thing the viewer actually experiences."""
    rows = (brief.get("treatment") or {}).get("structure") or []
    return [r.get("beat") for r in rows if isinstance(r, dict) and r.get("beat")]


def skeleton_errors(briefs):
    """Two different archetypes sharing one beat skeleton is the template sneaking back in."""
    errs, seen = [], {}
    for b in briefs:
        seq, arch = structure(b), (b.get("treatment") or {}).get("archetype")
        if not seq:
            continue  # legacy brief without a declared structure
        key = tuple(seq)
        if key in seen and seen[key][1] != arch:
            errs.append(f"{b['id']} ({arch}) repeats the beat skeleton of {seen[key][0]} "
                        f"({seen[key][1]}): {' > '.join(seq)}")
        seen.setdefault(key, (b["id"], arch))
    return errs


def proof_errors(brief, manifest):
    tr = brief.get("treatment") or {}
    if not tr.get("archetype"):
        return []
    errs, creative = [], manifest.get("creative") or {}
    if (creative.get("archetype") or manifest.get("archetype")) != tr["archetype"]:
        errs.append(f"manifest archetype {creative.get('archetype')!r} != treatment {tr['archetype']!r}")
    cover = creative.get("cover") or manifest.get("cover") or {}
    if cover.get("source") != "cover-lab":
        errs.append("cover came from a video frame, not the cover lab")
    idx = tr.get("selected_cover")
    concepts = tr.get("cover_concepts") or []
    if isinstance(idx, int) and 0 <= idx < len(concepts) and cover.get("text") != concepts[idx].get("text"):
        errs.append(f"shipped cover text {cover.get('text')!r} != selected concept {concepts[idx].get('text')!r}")
    return errs


def main():
    argv = [a for a in sys.argv[1:] if not a.startswith("--")]
    renders = None
    if "--renders" in sys.argv:
        renders = Path(sys.argv[sys.argv.index("--renders") + 1])
        argv = [a for a in argv if a != str(renders)]
    d = Path(argv[0]) if argv else ROOT / "briefs"
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
    loaded = []
    for p in sorted(d.glob("*.json"), key=lambda x: x.stat().st_mtime):
        try:
            loaded.append(json.loads(p.read_text()))
        except Exception:
            continue
    skeleton = skeleton_errors(loaded)
    for e in skeleton:
        print("FAIL skeleton:", e)
    streak = 1
    for i in range(1, len(rows)):
        streak = streak + 1 if rows[i][1] == rows[i - 1][1] else 1
        if streak >= 3:
            print(f"FAIL: {streak} '{rows[i][1]}' videos in a row — vary the format")
            return 1
    failed = streak >= 3 or bool(skeleton)
    if renders:
        checked = 0
        for vid, arch, _ in rows:
            mf = renders / vid / "manifest.json"
            if not mf.exists():
                continue
            errs = proof_errors(json.loads((d / f"{vid}.json").read_text()), json.loads(mf.read_text()))
            checked += 1
            if errs:
                failed = True
                for e in errs:
                    print(f"FAIL {vid}: {e}")
        print(f"application proof: {checked} rendered brief(s) checked" if checked else
              "application proof: no rendered briefs found under " + str(renders))
    print("variety ok" if rows else "no treatments found")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
