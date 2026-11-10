#!/usr/bin/env python3
"""Topic ranking by outlier-multiple (vendored swipe.py): a topic counts by how far its reference
videos beat their OWN channel's median, never by raw views (raw views rank channel size).

  python3 tools/topic_rank.py collected.json --min 2.0          full table
  python3 tools/topic_rank.py collected.json --min 2.0 --json   machine-readable for idea_feed

collected.json: [{"title","views","channel", ...}] with >= 4 videos per channel or the tool says so
instead of ranking on noise. Feed it from research/sources scans (shorts lanes); the result lands
in the daily topics sheet (research/topics/daily-<date>.md) as the 'why now' evidence column.
"""
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
X = ROOT / "tools" / "external" / "youtube-agent-skill"

if __name__ == "__main__":
    raise SystemExit(subprocess.run([sys.executable, str(X / "swipe.py"), *sys.argv[1:]]).returncode)
