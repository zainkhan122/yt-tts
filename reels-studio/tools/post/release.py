#!/usr/bin/env python3
"""Owner-authorised Buffer queue clean-up (recreate scheduled posts against corrected media).

Why this exists: Buffer ingests a video when the post is created. If a render is redone for a fix,
the already-scheduled post keeps the media it ingested (its queue preview stays wrong even after
the media URL serves corrected bytes). Clearing those posts and letting the planner recreate them
is the only reliable repair. This tool does that in an auditable way:

  python3 tools/post/release.py --list                          # read-only: pending rows vs Buffer state
  python3 tools/post/release.py --keys a-01:youtube b-01:facebook \
        --confirm OWNER_APPROVED_QUEUE_CLEAR                    # mark rows re-creatable (no Buffer writes)
  python3 tools/post/release.py --keys ... --delete \
        --confirm OWNER_APPROVED_QUEUE_CLEAR                    # delete the Buffer posts, then release the rows
  python3 tools/post/release.py --release-removed \
        --confirm OWNER_APPROVED_QUEUE_CLEAR                    # posts deleted by hand in Buffer -> release rows

Rules (all enforced, all tested):
  * a sent/published row is never deleted and never released;
  * a post is only released when it is verifiably absent for a pending row, or after an explicit delete;
  * every write needs the exact confirmation string; --list never writes;
  * released rows keep their history in `previous_buffer_post_id` / `release_note`.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.post.buffer_api import BufferClient  # noqa: E402
from tools.post.common import PENDING, TERMINAL, config, iso, load_json, now_utc, save_json  # noqa: E402

CONFIRM = "OWNER_APPROVED_QUEUE_CLEAR"
RELEASED = "released"


def pending_rows(journal):
    return {k: r for k, r in journal["records"].items() if r.get("state") in PENDING or r.get("state") == "released"}


def release_row(record, note, now):
    """Mark a pending row re-creatable. Keeps the old id for audit; the planner may create again."""
    if record.get("state") in TERMINAL:
        raise ValueError("refusing to release a published row: " + str(record.get("video_id")))
    record["previous_buffer_post_id"] = record.get("buffer_post_id")
    record["buffer_post_id"] = None
    record["external_url"] = None
    record["state"] = RELEASED
    record["release_note"] = note
    record["released_at"] = iso(now)
    return record


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--keys", nargs="*", default=[], help="video:platform rows to clear (default: none)")
    ap.add_argument("--all-pending", action="store_true", help="every row that is not sent/published/released")
    ap.add_argument("--delete", action="store_true", help="delete those posts in Buffer first")
    ap.add_argument("--release-removed", action="store_true", help="release rows whose Buffer post is already gone")
    ap.add_argument("--list", action="store_true", help="read-only overview")
    ap.add_argument("--confirm", default="", help="must equal " + CONFIRM)
    ap.add_argument("--journal", default=str(ROOT / "tracker/publications.json"))
    a = ap.parse_args()
    journal = load_json(Path(a.journal))
    rows = pending_rows(journal)
    if a.all_pending:
        a.keys = [k for k, r in rows.items() if r["state"] != RELEASED]
    writes = a.keys or a.release_removed
    if writes and a.confirm != CONFIRM:
        raise SystemExit(f"refusing to write without --confirm {CONFIRM}")
    if not writes and not a.list:
        raise SystemExit("nothing to do: pass --list, --keys … or --release-removed")
    if not writes:
        print(f"{len(rows)} pending/released rows")
        for k, r in sorted(rows.items(), key=lambda kv: kv[1].get("due_at") or ""):
            print(f"  {k:34s} {r['state']:10s} due {str(r.get('due_at'))[:16]} buffer={r.get('buffer_post_id') or '-'}")
        return 0

    client = BufferClient(config())
    _, posts = client.state()
    by_id = {p["id"]: p for p in posts}
    changed = 0
    for k in a.keys:
        if k not in rows:
            print(f"skip {k}: not a pending row")
            continue
        r = rows[k]
        post = by_id.get(r.get("buffer_post_id"))
        if post and post["status"] == "sent":
            print(f"skip {k}: Buffer says sent - reconcile it, do not clear")
            continue
        if a.delete:
            if not post:
                print(f"skip {k}: already absent from Buffer (use --release-removed)")
                continue
            client.delete(post["id"])
            _, after = client.state()
            if post["id"] in {p["id"] for p in after}:
                raise SystemExit(f"{k}: post still present after deletePost; stopping (nothing else touched)")
            release_row(r, "owner-approved queue clear; recreated against corrected media", now_utc())
            changed += 1
            print(f"deleted + released {k}")
    if a.release_removed:
        for k, r in rows.items():
            if r["state"] == RELEASED:
                continue
            if r.get("buffer_post_id") and r["buffer_post_id"] not in by_id:
                release_row(r, "Buffer post no longer exists (owner cleared the queue by hand)", now_utc())
                changed += 1
                print(f"released {k} (post absent)")
    if changed:
        save_json(Path(a.journal), journal)
        print(f"journal updated: {changed} row(s); commit to let the planner recreate them")
    else:
        print("nothing changed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
