#!/usr/bin/env python3
"""Weekly performance re-rank: let last week's views re-order the topic backlog.

The PIPELINE Learn stage feeds metrics back monthly and adjusts rubric weights
manually. This closes the loop faster: read the last 7 days of views from
tracker/content-tracker.csv, score each backlog topic by how much view attention
it actually earned, and bump (or demote) its priority. Topics that performed
well get a priority bonus; topics that flopped get penalised.

  python3 tools/rerank_backlog.py --write   # update backlog priority column
  python3 tools/rerank_backlog.py --json    # machine-readable, no write

Reads: tracker/content-tracker.csv (columns: date, platform, video_id, ... views_48h)
Writes: topics/backlog.csv priority column (bump/demote), and a report to research/ideas/.

The re-rank is a signal, not an auto-select: it reorders priority for owner review.
It never overrides a topic's rubric score or approval state.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRACKER = ROOT / "tracker" / "content-tracker.csv"
BACKLOG = ROOT / "topics" / "backlog.csv"
REPORT_DIR = ROOT / "research" / "ideas"

# How much priority to shift per performance bucket.
BUMP_STRONG = 20   # > 50k 7d views
BUMP_GOOD = 10     # 10k-50k
BUMP_MEH = 0       # 1k-10k
DEMOTE = -10       # < 1k 7d views (topic didn't earn attention)


def load_tracker(days: int = 7) -> dict[str, int]:
    """Return {video_id: total_views_last_7_days} from the content tracker."""
    if not TRACKER.exists():
        return {}
    cutoff = dt.date.today() - dt.timedelta(days=days)
    by_id: dict[str, int] = defaultdict(int)
    with TRACKER.open() as f:
        for row in csv.DictReader(f):
            date_str = (row.get("date") or "").strip()
            if not date_str:
                continue
            try:
                d = dt.date.fromisoformat(date_str)
            except ValueError:
                continue
            if d < cutoff:
                continue
            vid = (row.get("video_id") or "").strip()
            if not vid:
                continue
            views = (row.get("views_48h") or "").strip()
            if not views:
                continue
            try:
                by_id[vid] += int(views)
            except ValueError:
                continue
    return dict(by_id)


def performance_bonus(views: int) -> int:
    if views >= 50000:
        return BUMP_STRONG
    if views >= 10000:
        return BUMP_GOOD
    if views >= 1000:
        return BUMP_MEH
    return DEMOTE


def rerank(write: bool = False) -> dict:
    perf = load_tracker(7)
    if not BACKLOG.exists():
        return {"error": "no backlog.csv", "perf": perf}
    rows = list(csv.DictReader(BACKLOG.open()))
    fields = list(rows[0].keys()) if rows else []
    out = []
    report = []
    for r in rows:
        vid = (r.get("video_id") or "").strip()
        views = perf.get(vid, 0)
        bonus = performance_bonus(views)
        new_row = dict(r)
        if write and vid:
            try:
                base = int(r.get("priority") or 0)
                new_row["priority"] = str(max(0, min(100, base + bonus)))
            except ValueError:
                new_row["priority"] = str(bonus)
        report.append({"video_id": vid, "views_7d": views, "bonus": bonus,
                        "priority_new": new_row.get("priority", "")})
        out.append(new_row)
    if write:
        tmp = BACKLOG.with_suffix(".tmp")
        with tmp.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows({k: r.get(k, "") for k in fields} for r in out)
        tmp.replace(BACKLOG)
    return {"perf": perf, "report": report, "written": write}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="update backlog priority column")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--days", type=int, default=7)
    a = ap.parse_args()
    res = rerank(write=a.write)
    if a.json:
        print(json.dumps(res, indent=2, default=str))
        return 0
    if "error" in res:
        print(res["error"])
        return 1
    report = res["report"]
    ranked = sorted(report, key=lambda x: -x["views_7d"])
    print(f"7-day performance re-rank ({a.days}d window, {'WRITE' if a.write else 'DRY-RUN'})")
    print(f"{'video_id':28s} {'views_7d':>10s} {'bonus':>6s} {'priority':>8s}")
    for r in ranked[:30]:
        print(f"{r['video_id']:28s} {r['views_7d']:10,d} {r['bonus']:6d} {r['priority_new']:>8s}")
    if not a.write:
        print("\n(dry-run — pass --write to update backlog priority)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
