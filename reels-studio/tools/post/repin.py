#!/usr/bin/env python3
"""Re-pin a queued video to a corrected render without breaking already-created posts.

When a render is redone for a fix (e.g. the 2026-10-12 blank first frame), the queue must point
at the new immutable Release asset, and every URL already handed to Buffer must keep serving the
SAME video. This tool does both:

  * new asset_id/kit_asset_id/size/digests/media_path from the target tag, verified against the
    release (mp4 + kit present, video id matches);
  * the previous media path is appended to `legacy_media_paths` so the Pages deployment serves
    the corrected file at the old URL as well (tools/post/media.py build);
  * the cover approval is CLEARED: a re-render means a new cover file, and the owner/agent
    reviewed the old bytes, so the enrichment worker must not apply an unreviewed image.

  python3 tools/post/repin.py --tag renders-2026-10-12-r3 --video-ids a-01 b-01            # dry run
  python3 tools/post/repin.py --tag renders-2026-10-12-r3 --video-ids a-01 b-01 --apply
"""
import argparse
import json
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from lib.secrets import gh_token  # noqa: E402
from tools.post.common import config, iso, load_json, now_utc, save_json, valid_id  # noqa: E402

MAX_ALIASES = 4


def release_assets(tag, cfg, session=None):
    session = session or requests
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "Hypeless-Reels-Studio"}
    if gh_token():
        headers["Authorization"] = "Bearer " + gh_token()
    r = session.get(f"https://api.github.com/repos/{cfg['repository']}/releases/tags/{tag}", headers=headers, timeout=(10, 30))
    if r.status_code != 200:
        raise RuntimeError(f"Release {tag} not found (HTTP {r.status_code})")
    return {a["name"]: a for a in r.json()["assets"]}


def repin(item, assets, tag, now=None):
    """-> (updated item copy, list of changes). Raises when the release cannot satisfy the pin."""
    vid = item["video_id"]
    mp4, kit = assets.get(vid + ".mp4"), assets.get(vid + "-kit.zip")
    if not mp4 or not kit:
        raise ValueError(f"{vid}: release is missing {vid}.mp4 / {vid}-kit.zip")
    if mp4["name"].split(".")[0] != vid:
        raise ValueError(f"{vid}: asset name mismatch")
    new_path = f"media/{int(mp4['id'])}/{vid}.mp4"
    changes = []
    updated = dict(item)
    for field, value in (("asset_id", mp4["id"]), ("asset_size", mp4["size"]), ("asset_digest", mp4.get("digest")),
                         ("kit_asset_id", kit["id"]), ("kit_digest", kit.get("digest")),
                         ("release_tag", tag), ("media_path", new_path)):
        if item.get(field) != value:
            changes.append(f"{field}: {item.get(field)} -> {value}")
            updated[field] = value
    old_path = item.get("media_path")
    if old_path and old_path != new_path:
        aliases = [p for p in (item.get("legacy_media_paths") or []) if p != old_path]
        updated["legacy_media_paths"] = ([old_path] + aliases)[-MAX_ALIASES:]
        changes.append(f"legacy URL kept: {old_path}")
    if not changes:
        return item, []
    if item.get("cover_sha256") or item.get("cover_reviewed_at"):
        updated["cover_sha256"] = None
        updated["cover_reviewed_at"] = None
        changes.append("cover approval cleared (new render = new cover file; re-extract + approve)")
    updated["repinned_at"] = iso(now or now_utc())
    return updated, changes


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--video-ids", nargs="+", required=True, type=valid_id)
    ap.add_argument("--apply", action="store_true", help="write queue/publish.json (otherwise dry run)")
    a = ap.parse_args()
    cfg = config()
    path = ROOT / "queue/publish.json"
    data = load_json(path)
    by_id = {i["video_id"]: i for i in data["items"]}
    missing = [v for v in a.video_ids if v not in by_id]
    if missing:
        raise SystemExit("not queued: " + ", ".join(missing))
    assets = release_assets(a.tag, cfg)
    touched = 0
    for vid in a.video_ids:
        updated, changes = repin(by_id[vid], assets, a.tag)
        print(f"{vid}: {'/'.join(changes) if changes else 'already pinned to ' + a.tag}")
        if changes:
            by_id[vid] = updated
            touched += 1
    if a.apply and touched:
        data["items"] = [by_id[i["video_id"]] for i in data["items"]]
        save_json(path, data)
        print(f"queue updated ({touched} item(s)); commit to activate")
    elif touched:
        print("dry run: nothing written (pass --apply)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
