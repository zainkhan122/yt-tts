#!/usr/bin/env python3
"""Agent-side Shorts cover review — the human gate for `thumbnails.set`.

The cloud enrichment worker sets a custom cover on sent Buffer Shorts only when the
queue item records explicit agent review of that exact image digest. This tool
produces the preview to look at, and (after you have actually looked) records the
approval:

  python3 tools/youtube/cover_ctl.py extract <video_id> [...]   # kits -> renders/covers/ previews
  python3 tools/youtube/cover_ctl.py approve <video_id> [...]   # re-verifies against the live kit, then records
  python3 tools/youtube/cover_ctl.py status [--live]            # one line per video: approved -> applied -> confirmed

No social write happens here; nothing is set on YouTube by this tool. The digest it
records is what metadata.attach_short_cover demands before issuing thumbnails.set.
"""
import argparse
import datetime as dt
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from lib.secrets import secure_vault  # noqa: E402
secure_vault()
from tools.post.common import config, iso, load_json, save_json, valid_id  # noqa: E402
from tools.youtube.contracts import cover_digest, fetch_kit_cover, validate_short_cover  # noqa: E402

PREVIEW_DIR = ROOT / "renders/covers"  # git-ignored scratch; the kit Release stays authoritative


def queue_path():
    return ROOT / "queue/publish.json"


def find_item(video_id):
    for item in load_json(queue_path())["items"]:
        if item["video_id"] == video_id:
            return item
    raise SystemExit(f"{video_id} is not in queue/publish.json")


def extract(video_ids):
    cfg = config()
    for video_id in video_ids:
        item = find_item(video_id)
        PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
        cover = fetch_kit_cover(item, cfg, PREVIEW_DIR)
        final = PREVIEW_DIR / (video_id + "-cover.jpg")
        if cover != final:
            final.write_bytes(cover.read_bytes())
        info = validate_short_cover(final, cover_digest(final))
        print(f"{video_id}: preview {final.relative_to(ROOT)} · {info['width']}x{info['height']} {info['format']} "
              f"{info['size_bytes']}B · {info['sha256']}")
    print("Look at each preview image, then approve the ones that actually look right.")


def approve(video_ids):
    data = load_json(queue_path())
    cfg = config()
    stamp = iso(dt.datetime.now(dt.timezone.utc))
    for video_id in video_ids:
        item = next((i for i in data["items"] if i["video_id"] == video_id), None)
        if item is None:
            raise SystemExit(f"{video_id} is not in queue/publish.json")
        preview = PREVIEW_DIR / (video_id + "-cover.jpg")
        if not preview.is_file():
            raise SystemExit(f"{video_id}: no extracted preview; run `extract {video_id}` and look at it first")
        # Bind the approval to the immutable kit the cloud worker will fetch, not to the local preview copy.
        live = fetch_kit_cover(item, cfg, PREVIEW_DIR / "_verify")
        digest = cover_digest(live)
        validate_short_cover(live, digest)
        item["cover_sha256"] = digest
        item["cover_reviewed_at"] = stamp
        print(f"{video_id}: cover approval recorded · {digest}")
    save_json(queue_path(), data)
    print("Queue updated. Commit to let the enrichment worker set these covers on sent Shorts.")


def manual_included():
    return bool(load_json(ROOT / "config/youtube.json")["metadata_enrichment"]["include_manual_uploads"])


def pipeline_rows():
    """Join queue approval, tracker publication and the worker journal into one row per video.

    The three surfaces answer different questions: the queue says whether an agent approved a
    cover digest, the tracker says whether the Short was sent and reconciled (no YouTube id, no
    cover work), and the journal says what the enrichment worker actually did on YouTube.
    """
    from tools.youtube.runner import external_id
    records = load_json(ROOT / "tracker/publications.json")["records"]
    jpath = ROOT / "tracker/youtube-publications.json"
    enrichment = load_json(jpath).get("enrichment", {}) if jpath.is_file() else {}
    rows = []
    for item in load_json(queue_path())["items"]:
        rec = records.get(item["video_id"] + ":youtube") or {}
        ytid = rec.get("youtube_id") or external_id(rec.get("external_url") or "")
        rows.append({**item, "ytid": ytid, "publish_state": rec.get("state"),
                     "enrich": enrichment.get(ytid) if ytid else None})
    return rows


def cover_stage(item, publish_state, enrich, live=None):
    """One honest line per video, from approval to a confirmed read-back."""
    approved = bool(item.get("cover_sha256") and item.get("cover_reviewed_at"))
    digest = (item.get("cover_sha256") or "")[-12:]
    if enrich and enrich.get("thumbnail_blocked"):
        return "X", f"BLOCKED after {enrich.get('thumbnail_attempts', '?')} attempts · {str(enrich.get('last_error'))[:70]}"
    if not approved:
        if publish_state in {"sent", "published_manual"}:
            return "!", "no cover approved — approve one and the worker re-opens this row"
        return "-", "no cover approved"
    if enrich and enrich.get("thumbnail_confirmed"):
        stale = enrich.get("thumbnail_digest") != item.get("cover_sha256")
        if live is False:
            return "?", "worker confirmed, but YouTube reports no custom thumbnail — investigate"
        return "OK", f"confirmed on YouTube · {enrich.get('thumbnail_digest', '')[-12:]}" + (" (newer approval pending)" if stale else "")
    if item["approval"] == "held" and publish_state is None:
        return "...", "held in queue — cover approved, applies after it is scheduled, sent and reconciled"
    if publish_state in {None, "scheduled", "uploaded_private"}:
        return "...", "approved · waiting for Buffer send + reconcile (cover needs a video id)"
    if publish_state == "published_manual" and not manual_included():
        return "...", "approved · hand-published upload: cron skips it, dispatch enrich with include_manual to apply"
    if not enrich:
        return "...", "approved · queued for next enrichment run"
    if enrich.get("state") == "cover_pending":
        return "...", f"applying · attempt {enrich.get('thumbnail_attempts', '?')} of 4"
    if enrich.get("state") == "done":
        return "...", "enrichment finished without a cover — re-opens on the next run for this approval"
    return "...", f"enrichment state {enrich.get('state')}"


def status(live=False):
    rows = pipeline_rows()
    live_map = {}
    if live:
        ytids = [r["ytid"] for r in rows if r["ytid"]]
        if ytids:
            from tools.post.state import Journal
            from tools.youtube.api import YouTubeAPI
            from tools.youtube.metadata import get_video
            api = YouTubeAPI(load_json(ROOT / "config/youtube.json"), Journal(
                config(), remote=False, path=ROOT / "tracker/youtube-publications.json",
                remote_path="tracker/youtube-publications.json"))
            for r in rows:
                if not r["ytid"]:
                    continue
                video = get_video(api, r["ytid"])
                live_map[r["video_id"]] = bool(video["contentDetails"].get("hasCustomThumbnail"))
    counts = {}
    for row in rows:
        state, note = cover_stage(row, row["publish_state"], row["enrich"], live_map.get(row["video_id"]))
        if live and row["video_id"] in live_map:
            note += " · YouTube now: " + ("custom thumbnail" if live_map[row["video_id"]] else "auto frame")
        counts[state] = counts.get(state, 0) + 1
        print(f"{row['video_id']:28s} queue={row['approval']:9s} cover={'-' if state in {'-', '!'} else 'ok':3s} {state:>3s} {note}")
    summary = " · ".join(f"{k}:{v}" for k, v in counts.items())
    print(f"\n{len(rows)} videos · {summary}")
    print("OK = agent-approved digest applied and read back on YouTube; ... = in flight; X = blocked; ! = needs an approval.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("extract", help="download kits and extract cover previews for visual review")
    p.add_argument("video_ids", nargs="+", type=valid_id)
    p = sub.add_parser("approve", help="record approval after visually reviewing the preview")
    p.add_argument("video_ids", nargs="+", type=valid_id)
    p = sub.add_parser("status", help="cover pipeline: approved -> applied -> confirmed, per video")
    p.add_argument("--live", action="store_true", help="also read hasCustomThumbnail from YouTube (1 quota unit)")
    args = ap.parse_args()
    if args.cmd == "extract":
        extract(args.video_ids)
    elif args.cmd == "approve":
        approve(args.video_ids)
    else:
        status(live=args.live)


if __name__ == "__main__":
    main()
