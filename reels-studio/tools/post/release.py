#!/usr/bin/env python3
"""Auditable in-place Buffer media repair; owner-gated queue clear only as a last resort.

Why this exists: Buffer ingests a video when the post is created. If a render is redone for a fix,
the already-scheduled post keeps the media it ingested (its queue preview stays wrong even after
the media URL serves corrected bytes). The preferred repair is editPost with a complete payload,
replacing assets in place while preserving the scheduled slot, caption and tracker row. A targeted,
owner-confirmed clear exists only when in-place refresh cannot repair a specific post. This tool does:

  python3 tools/post/release.py --list                          # read-only: pending rows vs Buffer state
  python3 tools/post/release.py --keys a-01:youtube b-01:facebook \
        --confirm OWNER_APPROVED_QUEUE_CLEAR                    # mark rows re-creatable (no Buffer writes)
  python3 tools/post/release.py --keys ... --delete \
        --confirm OWNER_APPROVED_QUEUE_CLEAR                    # delete the Buffer posts, then release the rows
  python3 tools/post/release.py --release-removed \
        --confirm OWNER_APPROVED_QUEUE_CLEAR                    # posts deleted by hand in Buffer -> release rows

Preferred repair (2026-10-12): a scheduled post keeps the media Buffer ingested when it was created,
so a post that predates a media fix must have its assets replaced in place. `editPost` does that and
keeps the slot, the tracker row and the platform metadata:

  python3 tools/post/release.py --refresh --confirm OWNER_APPROVED_MEDIA_REFRESH

`--refresh` walks every pending row, compares the media URL Buffer holds with the URL the queue
publishes now and re-points the stale ones at the current file (the same bytes every platform will
fetch at send time). Nothing is deleted and no row changes state.

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
from tools.post.common import (PENDING, TERMINAL, config, iso, load_json, media_url, now_utc,  # noqa: E402
                               parse_time, save_json)

CONFIRM = "OWNER_APPROVED_QUEUE_CLEAR"
CONFIRM_REFRESH = "OWNER_APPROVED_MEDIA_REFRESH"
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


def audit(journal_rows, posts, queue, cfg):
    """Does Buffer still hold the file we gave it when the post was created?

    Buffer ingests a video when the post is created, so a post that predates a media fix keeps the
    old URL. This compares the URL Buffer holds with the URL the queue publishes today, read-only.
    """
    by_id = {p["id"]: p for p in posts}
    items = {i["video_id"]: i for i in queue["items"]}
    rows = []
    for key, r in sorted(journal_rows.items()):
        post = by_id.get(r.get("buffer_post_id"))
        if not post:
            continue
        item = items.get(r["video_id"])
        expected = media_url(item, cfg) if item else None
        held = [a.get("source") for a in (post.get("assets") or [])]
        rows.append({"key": key, "status": post["status"], "due": post.get("dueAt"),
                     "held": held, "expected": expected,
                     "verdict": "OK" if held and expected in held else ("STALE" if expected else "?")})
    return rows


def sent_in_buffer(status):
    """An API read may race behind the tracker; a sent Buffer post must never be editPost-ed."""
    return str(status or "").strip().lower() in {"sent", "published", "published_manual"}


def refresh_candidates(found):
    """Only stale posts Buffer still considers editable belong in the refresh mutation batch.

    A schedule can start while a post has just sent but before this repo has reconciled it. Treat
    that send as a receipt/reconcile concern, not a media-edit target. Never make an editPost call
    against sent media; publisher.py reconciles it immediately after this pre-delivery guard.
    """
    return [r for r in found if r["verdict"] != "OK" and not sent_in_buffer(r.get("status"))]


def refresh_input(record, item, cfg, due):
    """EditPostInput that swaps the video asset.

    editPost validates the resulting post as a whole, and a service metadata object must carry all
    of its required members, so we rebuild metadata+assets with the planner's own payload builder
    (identical copy, disclosure and thumbnailOffset settings to the original create) while leaving
    text, dueAt, mode and schedulingType out - those stay exactly as stored, so the post keeps its
    caption and its slot without us writing a stale copy back over them.
    """
    from tools.post.planner import payload_for
    platform = record["_key"].split(":")[-1]
    if isinstance(due, str):
        due = parse_time(due)
    payload = payload_for(item, platform, due or now_utc(), cfg)
    return {"id": record["buffer_post_id"], "assets": payload["assets"], "metadata": payload["metadata"]}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--keys", nargs="*", default=[], help="video:platform rows to clear (default: none)")
    ap.add_argument("--all-pending", action="store_true", help="every row that is not sent/published/released")
    ap.add_argument("--delete", action="store_true", help="delete those posts in Buffer first")
    ap.add_argument("--release-removed", action="store_true", help="release rows whose Buffer post is already gone")
    ap.add_argument("--list", action="store_true", help="read-only overview")
    ap.add_argument("--audit", action="store_true", help="read-only: compare the media URL Buffer holds with the queue")
    ap.add_argument("--schema", action="store_true", help="read-only: dump EditPostInput/AssetInput field shapes")
    ap.add_argument("--refresh", action="store_true", help="re-point stale scheduled posts at the current media, in place")
    ap.add_argument("--confirm", default="", help="must equal " + CONFIRM)
    ap.add_argument("--journal", default=str(ROOT / "tracker/publications.json"))
    a = ap.parse_args()
    journal = load_json(Path(a.journal))
    rows = pending_rows(journal)
    if a.all_pending:
        a.keys = [k for k, r in rows.items() if r["state"] != RELEASED]
    writes = a.keys or a.release_removed
    if a.refresh and a.confirm != CONFIRM_REFRESH:
        raise SystemExit(f"refusing to refresh without --confirm {CONFIRM_REFRESH}")
    if writes and a.confirm != CONFIRM:
        raise SystemExit(f"refusing to write without --confirm {CONFIRM}")
    if not writes and not (a.list or a.audit or a.schema or a.refresh):
        raise SystemExit("nothing to do: pass --list, --audit, --keys … or --release-removed")
    if a.refresh:
        client = BufferClient(config()["buffer"])
        _, posts = client.state()
        queue = load_json(ROOT / "queue/publish.json")
        items = {i["video_id"]: i for i in queue["items"]}
        found = audit(rows, posts, queue, config())
        todo = refresh_candidates(found)
        sent_stale = [r for r in found if r["verdict"] != "OK" and sent_in_buffer(r.get("status"))]
        print(f"refresh: {len(todo)} stale editable posts of {len(found)} tracked posts")
        for entry in sent_stale:
            print(f"  skip {entry['key']}: Buffer says sent; do not edit; publisher reconciliation will record it")
        done = 0
        for entry in todo:
            record = rows[entry["key"]]
            record["_key"] = entry["key"]
            item = items.get(record["video_id"])
            if not item:
                print(f"  skip {entry['key']}: video not in queue")
                continue
            payload = refresh_input(record, item, config(), parse_time(record.get("due_at")))
            result = client.request("""mutation HypelessEdit($input: EditPostInput!) {
 editPost(input: $input) {
  __typename
  ... on PostActionSuccess { post { id assets { source } } }
  ... on MutationError { message }
 }
}""", {"input": payload}, mutation=True).get("editPost") or {}
            post = result.get("post") or {}
            ok = post.get("id") and any(a.get("source") == media_url(item, config()) for a in post.get("assets") or [])
            print(f"  {entry['key']:34s} {'updated' if ok else 'FAILED: ' + str(result.get('message') or result.get('__typename'))}")
            done += 1 if ok else 0
        # Read back Buffer's actual state rather than trusting mutation acknowledgements alone.
        _, after_posts = client.state()
        after = audit(rows, after_posts, queue, config())
        remaining = refresh_candidates(after)
        sent_after = [r for r in after if sent_in_buffer(r.get("status")) and r["verdict"] != "OK"]
        ok_after = sum(r["verdict"] == "OK" for r in after)
        print(f"refresh: {done}/{len(todo)} updated; post-refresh audit: "
              f"{ok_after} OK, {len(remaining)} stale editable, "
              f"{len(sent_after)} sent-stale (reconcile only)")
        for entry in remaining:
            print(f"  FAIL {entry['key']}: Buffer still holds stale media")
        return 0 if done == len(todo) and not remaining else 1

    if not writes:
        print(f"{len(rows)} pending/released rows")
        for k, r in sorted(rows.items(), key=lambda kv: kv[1].get("due_at") or ""):
            print(f"  {k:34s} {r['state']:10s} due {str(r.get('due_at'))[:16]} buffer={r.get('buffer_post_id') or '-'}")
        if a.schema:
            client = BufferClient(config()["buffer"])
            q = """query S($a: String!, $b: String!) {
 a: __type(name: $a) { inputFields { name type { kind name ofType { kind name ofType { kind name } } } } }
 b: __type(name: $b) { inputFields { name type { kind name ofType { kind name ofType { kind name } } } } }
}"""
            data = client.request(q, {"a": "EditPostInput", "b": "AssetInput"})
            for key in ("a", "b"):
                t = data.get(key) or {}
                print(f"{key}:")
                for f in t.get("inputFields") or []:
                    print("   ", f["name"], f["type"])
            return 0
        if a.audit:
            client = BufferClient(config()["buffer"])
            _, posts = client.state()
            queue = load_json(ROOT / "queue/publish.json")
            found = audit(rows, posts, queue, config())
            stale = [r for r in found if r["verdict"] != "OK"]
            for r in found:
                print(f"  {r['key']:34s} {r['status']:10s} due {str(r['due'])[:16]} {r['verdict']:5s} "
                      f"held={('|'.join(r['held']) or '-')[-40:]}")
            print(f"audit: {len(found)} posts, {len(stale)} not on the current media")
        return 0

    client = BufferClient(config()["buffer"])
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
