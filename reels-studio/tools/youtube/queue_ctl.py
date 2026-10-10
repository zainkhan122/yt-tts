#!/usr/bin/env python3
"""Pin prepared long-form Release assets; never enqueue raw local media for upload.

Required names: <id>.mp4, <id>-manifest.json, <id>-thumbnail.jpg,
<id>-thumbnail-report.json. The brief is source in briefs/long/<id>.json.
"""
import argparse
import datetime as dt
from pathlib import Path
import sys

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from lib.secrets import gh_token
from tools.post.common import config, fingerprint, iso, load_json, now_utc, parse_time, save_json, valid_id
from tools.youtube.contracts import preflight


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("enqueue")
    p.add_argument("video_id", type=valid_id)
    p.add_argument("--tag", required=True)
    p.add_argument("--category", choices=["tool", "repo", "news"], required=True)
    p = sub.add_parser("approve")
    p.add_argument("video_id", type=valid_id)
    p.add_argument("--reviewed-until", required=True)
    p.add_argument("--thumbnail-reviewed", action="store_true", required=True)
    p.add_argument("--public", action="store_true", help="Public release explicitly approved; otherwise private pilot only")
    p = sub.add_parser("hold")
    p.add_argument("video_id", type=valid_id)
    p = sub.add_parser("enable")
    p.add_argument("--confirm", choices=["OWNER_APPROVED_YOUTUBE_DELIVERY"], required=True)
    sub.add_parser("disable")
    p = sub.add_parser("pilot-passed")
    p.add_argument("video_id", type=valid_id)
    args = ap.parse_args()
    root_cfg, yt_cfg = config(), load_json(ROOT/"config/youtube.json")
    qpath = ROOT/"queue/youtube-long.json"
    queue = load_json(qpath)
    now = now_utc()
    if args.command == "enqueue":
        if any(i["video_id"] == args.video_id for i in queue["items"]):
            raise SystemExit("Already queued; do not replace a pinned in-flight video")
        brief = load_json(ROOT/"briefs/long"/(args.video_id+".json"))
        headers = {"Authorization": "Bearer " + gh_token(), "Accept": "application/vnd.github+json"}
        r = requests.get(f"https://api.github.com/repos/{root_cfg['repository']}/releases/tags/{args.tag}", headers=headers, timeout=30)
        r.raise_for_status()
        existing = {a["name"]: a for a in r.json()["assets"]}
        names = {"video": args.video_id+".mp4", "manifest": args.video_id+"-manifest.json", "thumbnail": args.video_id+"-thumbnail.jpg", "thumbnail_report": args.video_id+"-thumbnail-report.json"}
        assets = {k: {f: existing[name][f] for f in ("id", "name", "size", "digest")} for k, name in names.items()}
        queue["items"].append({"video_id": args.video_id, "category": args.category, "title": brief["seo"]["youtube"]["title"],
            "approval": "held", "public_approved": False, "priority": 100, "added_at": iso(now), "reviewed_at": None,
            "expires_at": None, "thumbnail_reviewed_at": None, "brief_sha256": fingerprint(brief), "release_tag": args.tag,
            "assets": assets, "asset_id": assets["video"]["id"], "asset_digest": assets["video"]["digest"],
            "contains_synthetic_media": brief.get("contains_synthetic_media", False)})
    elif args.command in {"approve", "hold"}:
        item = next((i for i in queue["items"] if i["video_id"] == args.video_id), None)
        if not item:
            raise SystemExit("Long video not queued")
        if args.command == "hold":
            item.update(approval="held", public_approved=False)
        else:
            expiry = parse_time(args.reviewed_until)
            maximum = 3 if item["category"] == "news" else 14
            if not now < expiry <= now+dt.timedelta(days=maximum):
                raise SystemExit(f"Review must expire within {maximum} days; do not schedule stale claims")
            item.update(approval="approved", public_approved=args.public, reviewed_at=iso(now), expires_at=iso(expiry), thumbnail_reviewed_at=iso(now))
            import tempfile
            with tempfile.TemporaryDirectory(prefix="hypeless-long-check-") as work:
                preflight(item, root_cfg, yt_cfg, work, need_video=False)
    elif args.command in {"enable", "disable"}:
        yt_cfg["enabled"] = args.command == "enable"
        save_json(ROOT/"config/youtube.json", yt_cfg)
        print("Local switch changed; commit required. OAuth and verified live pilot remain mandatory.")
        return
    else:
        record = load_json(ROOT/"tracker/youtube-publications.json")["records"].get(args.video_id, {})
        if record.get("state") != "sent" or not record.get("external_url"):
            raise SystemExit("Pilot is not confirmed public; private/processing/scheduled is not a pass")
        yt_cfg.update(live_pilot_passed=True, live_pilot_video=args.video_id)
        save_json(ROOT/"config/youtube.json", yt_cfg)
        print("Public pilot receipt verified; commit to allow routine scheduling")
        return
    save_json(qpath, queue)
    print("Queue saved locally. Zero YouTube uploads. Commit to use it in Actions.")


if __name__ == "__main__":
    main()
