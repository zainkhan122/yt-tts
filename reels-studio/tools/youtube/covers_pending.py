#!/usr/bin/env python3
"""Does any sent Short still need its approved cover applied on YouTube?

This is the decision the post.yml delivery job makes before it cascades to the
YouTube worker: after Buffer sends a Short and reconcile records the video URL, the
enrichment run (youtube.yml, mode=enrich) is the only thing that can set the cover.
Rather than waiting for the next 6-hourly cron, post.yml dispatches that run as soon
as this check reports work to do.

Exit codes (so the workflow can branch without parsing text):
  0  nothing pending - no dispatch needed
  3  at least one sent Short has an agent-approved cover YouTube has not confirmed
  2  state files unreadable - fail loudly instead of silently skipping covers

Read-only, stdlib only: the post.yml runner installs post requirements, not the
YouTube ones, so this module must not import tools.youtube.runner or api.
"""
import argparse
import json
import re
import sys
from pathlib import Path

# Same pattern as tools.youtube.runner.external_id; kept local because that module
# pulls in the YouTube API dependencies this job does not install.
ID_RE = re.compile(r"(?:youtu\.be/|youtube\.com/(?:shorts/|watch\?v=))([A-Za-z0-9_-]{11})(?:[?&#/]|$)")


def external_id(url):
    match = ID_RE.search(url or "")
    return match[1] if match else None


def pending_covers(records, items, enrichment):
    """Sent Shorts whose approved cover digest YouTube has not confirmed yet.

    Mirrors runner.should_enrich for the sent+approved case, but only reports
    (never touches) state: blocked rows stay blocked, confirmed rows close, and a
    newer approved digest re-opens a previously confirmed row.
    """
    queue_by_id = {i["video_id"]: i for i in items}
    pending = []
    for record in records.values():
        if record.get("platform") != "youtube" or record.get("state") != "sent":
            continue
        youtube_id = record.get("youtube_id") or external_id(record.get("external_url"))
        if not youtube_id:
            continue
        item = queue_by_id.get(record["video_id"])
        if not item or not item.get("cover_sha256"):
            continue
        row = (enrichment or {}).get(youtube_id) or {}
        if row.get("thumbnail_blocked"):
            continue
        if row.get("thumbnail_confirmed") and row.get("thumbnail_digest") == item["cover_sha256"]:
            continue
        pending.append({"video_id": record["video_id"], "youtube_id": youtube_id,
                        "reason": "cover approved, not yet confirmed on YouTube"})
    return pending


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true", help="machine-readable list")
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[2]
    try:
        items = json.loads((root / "queue/publish.json").read_text())["items"]
        records = json.loads((root / "tracker/publications.json").read_text())["records"]
        journal = root / "tracker/youtube-publications.json"
        enrichment = json.loads(journal.read_text()).get("enrichment", {}) if journal.is_file() else {}
    except (OSError, ValueError, KeyError) as exc:
        print(f"covers_pending: cannot read state files: {exc}", file=sys.stderr)
        return 2
    pending = pending_covers(records, items, enrichment)
    if args.json:
        print(json.dumps(pending, indent=2))
    elif pending:
        for row in pending:
            print(f"{row['video_id']} (youtube {row['youtube_id']}): {row['reason']}")
    else:
        print("no sent Shorts awaiting covers")
    return 3 if pending else 0


if __name__ == "__main__":
    raise SystemExit(main())
