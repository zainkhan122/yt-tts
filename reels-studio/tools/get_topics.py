#!/usr/bin/env python3
"""Get topics: one command for "what should we make a short about today?".

It does the whole lane in the right order and refuses to pretend:

  1. scan EVERY registered source (TikTok, YouTube, RSS, gittrend.io) and persist what they posted;
  2. build the sheet for the rolling last N hours (default 24) with consensus dedup and the
     covered-topic filter, so a topic we already made a short about can never come back;
  3. print the fresh topics, ranked, with the source coverage table.

  python3 tools/get_topics.py                     # scan + 24 h sheet
  python3 tools/get_topics.py --hours 12          # a tighter window
  python3 tools/get_topics.py --no-scan           # reuse the last scan
  python3 tools/get_topics.py --show-covered      # also show what was excluded and why

Exit codes: 0 = sheet written; 2 = the scan failed or the lane is stale; 3 = nothing fresh.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hours", type=float, default=24.0, help="rolling window in hours (default 24)")
    ap.add_argument("--latest", type=int, default=10, help="posts to pull per source (default 10)")
    ap.add_argument("--priority", choices=["daily", "weekly"], help="only scan sources at this cadence")
    ap.add_argument("--no-scan", action="store_true", help="reuse the last scan instead of fetching")
    ap.add_argument("--show-covered", action="store_true", help="list the excluded (already covered) topics")
    a = ap.parse_args(argv)

    import sources
    import todays_topics

    if not a.no_scan:
        print(f"== scanning every registered source ({a.latest} posts each) ==")
        sources.scan_all(a.latest, a.priority)
        print()

    print(f"== topics from the last {a.hours:g} h ==")
    rc = todays_topics.main(["--hours", str(a.hours)] + (["--show-covered"] if a.show_covered else []))
    if rc == 2:
        print("get topics: the source scan is stale or missing — the sheet cannot be trusted yet", file=sys.stderr)
        return 2

    payload = ROOT / "research" / "topics" / f"daily-{todays_topics.dt.datetime.now(todays_topics.dt.timezone.utc).date().isoformat()}.json"
    import json
    data = json.loads(payload.read_text(encoding="utf-8"))
    topics = data.get("topics") or []
    if not topics:
        print("get topics: no fresh topic in the window — the lane is genuinely empty", file=sys.stderr)
        return 3
    print()
    print("fresh topics (pick one; consensus = how many sources mentioned it):")
    for i, t in enumerate(topics, 1):
        src = ", ".join(t["sources"])
        print(f"  {i:2d}. {t['name']}  [consensus {t['consensus']}]  {src}")
    print()
    print("next: python3 tools/topics_covered.py check <topic>   # proves it is not already covered")
    return 0


if __name__ == "__main__":
    sys.exit(main())
