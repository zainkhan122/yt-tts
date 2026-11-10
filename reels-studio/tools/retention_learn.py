#!/usr/bin/env python3
"""Retention learn loop: turn a YouTube Studio retention export into a filed, acted-on report.

  python3 tools/retention_learn.py repo-ahsilence-01 path/to/retention.csv

Reads the export with the vendored retention.py (HOOK LEAK / CLIFFS / SLIDE), annotates drops with
the words being said (the release kit's captions.srt is found automatically), files the report to
research/retention/<id>-<date>.md, and prints the one-line fix each signal maps to in our beats
system (pacing, archetype choice, hook rewrite). Reports feed the next batch's authoring; they are
evidence, never auto-edits.

Retention CSV: YouTube Studio -> Analytics -> Audience retention -> export. Until the youtube
worker pulls it via API, drop the CSV at research/retention/raw/<id>.csv.
"""
import json, re, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
X = ROOT / "tools" / "external" / "youtube-agent-skill"

FIXES = {
    "HOOK LEAK": "hook leak > 15%: scenes[0] over-stays or under-promises; re-author via tools/hook_panel.py formulas (add STAKES) and compress the first beat under 4s",
    "CLIFF": "cliff at T: look up the beat owning that second in beats.json; the archetype there is losing people (card held too long / static) - tighten or split it",
    "SLIDE": "middle slide steep: raise visual-change rate (motion gate floor is 75% of speech time) or cut a beat; re-check --wpm",
}


def find_srt(vid):
    for cand in (ROOT / "renders" / vid / "captions.srt", ROOT / "research" / "retention" / "raw" / f"{vid}.srt"):
        if cand.exists():
            return cand
    return None


def main():
    if len(sys.argv) < 3:
        print(__doc__); return 2
    vid, csv_path = sys.argv[1], sys.argv[2]
    srt = find_srt(vid)
    cmd = [sys.executable, str(X / "retention.py"), csv_path, "--json"]
    if srt:
        cmd += ["--transcript", str(srt)]
    rep = subprocess.run(cmd, capture_output=True, text=True)
    body = rep.stdout.strip() or rep.stderr.strip()
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_dir = ROOT / "research" / "retention"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{vid}-{date}.md"
    out.write_text(f"# Retention read: {vid} ({date})\n\nCSV: `{csv_path}` · transcript: `{srt}`\n\n```\n{body}\n```\n\n## Fix map\n- " + "\n- ".join(FIXES.values()) + "\n", encoding="utf-8")
    print(f"filed -> {out.relative_to(ROOT)}")
    for k, v in FIXES.items():
        if k.rstrip(" LEAK") in body or k in body:
            print(" !", v)
    return 0


if __name__ == "__main__":
    sys.exit(main())
