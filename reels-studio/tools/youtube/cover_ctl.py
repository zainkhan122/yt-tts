#!/usr/bin/env python3
"""Agent-side Shorts cover review — the human gate for `thumbnails.set`.

The cloud enrichment worker sets a custom cover on sent Buffer Shorts only when the
queue item records explicit agent review of that exact image digest. This tool
produces the preview to look at, and (after you have actually looked) records the
approval:

  python3 tools/youtube/cover_ctl.py extract <video_id> [...]   # kits -> renders/covers/ previews
  python3 tools/youtube/cover_ctl.py approve <video_id> [...]   # re-verifies against the live kit, then records
  python3 tools/youtube/cover_ctl.py status                     # queue view of cover approvals

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


def status():
    for item in load_json(queue_path())["items"]:
        approval = item["approval"]
        cover = "approved" if (item.get("cover_sha256") and item.get("cover_reviewed_at")) else "—"
        print(f"{item['video_id']:28s} queue={approval:9s} cover={cover}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("extract", help="download kits and extract cover previews for visual review")
    p.add_argument("video_ids", nargs="+", type=valid_id)
    p = sub.add_parser("approve", help="record approval after visually reviewing the preview")
    p.add_argument("video_ids", nargs="+", type=valid_id)
    sub.add_parser("status", help="show queue cover approval state")
    args = ap.parse_args()
    if args.cmd == "extract":
        extract(args.video_ids)
    elif args.cmd == "approve":
        approve(args.video_ids)
    else:
        status()


if __name__ == "__main__":
    main()
