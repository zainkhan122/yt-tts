#!/usr/bin/env python3
"""Agent-operated queue controls. These edit local config only; commit to activate.

Enqueue defaults to HELD. Approval is separate from rendering/topic approval.
A live pilot must reach 'sent' on its selected platforms before daily activation.
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
from tools.post.media import read_kit


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("enqueue")
    p.add_argument("video_id", type=valid_id)
    p.add_argument("--tag", required=True)
    p.add_argument("--category", required=True, choices=["news", "tool", "repo"])
    p.add_argument("--priority", type=int, default=100)
    p = sub.add_parser("approve")
    p.add_argument("video_ids", nargs="+", type=valid_id)
    p.add_argument("--reviewed-until", required=True, help="UTC/offset ISO timestamp, after rechecking facts/copy")
    p.add_argument("--platforms", nargs="+", choices=["youtube", "instagram", "facebook"])
    p = sub.add_parser("hold")
    p.add_argument("video_ids", nargs="+", type=valid_id)
    p = sub.add_parser("enable")
    p.add_argument("--confirm", required=True, choices=["OWNER_APPROVED_LIVE_POSTING"])
    sub.add_parser("disable")
    p = sub.add_parser("pilot-passed")
    p.add_argument("video_id", type=valid_id)
    args = ap.parse_args()
    cfg = config()
    path = ROOT / "queue/publish.json"
    data = load_json(path)
    now = now_utc()
    if args.cmd == "enqueue":
        if any(i["video_id"] == args.video_id for i in data["items"]):
            raise SystemExit("Already queued. Keep pinned assets; never overwrite a scheduled video URL.")
        b = load_json(ROOT / "briefs" / (args.video_id + ".json"))
        h = {"Accept": "application/vnd.github+json"}
        if gh_token():
            h["Authorization"] = "Bearer " + gh_token()
        r = requests.get(f"https://api.github.com/repos/{cfg['repository']}/releases/tags/{args.tag}", headers=h, timeout=30)
        r.raise_for_status()
        assets = {a["name"]: a for a in r.json()["assets"]}
        a, kit = assets[args.video_id + ".mp4"], assets[args.video_id + "-kit.zip"]
        item = {"video_id": args.video_id, "category": args.category, "priority": args.priority, "approval": "held",
                "platforms": [p for p, c in cfg["buffer"]["channels"].items() if c["enabled"]],
                "release_tag": args.tag, "asset_id": a["id"], "asset_size": a["size"], "asset_digest": a.get("digest"),
                "kit_asset_id": kit["id"], "kit_digest": kit.get("digest"),
                "media_path": f"media/{a['id']}/{args.video_id}.mp4", "title": b["seo"]["youtube"]["title"],
                "brief_sha256": fingerprint(b), "added_at": iso(now), "reviewed_at": None, "expires_at": None}
        read_kit(cfg, item)
        data["items"].append(item)
    elif args.cmd in {"approve", "hold"}:
        have = {i["video_id"] for i in data["items"]}
        if set(args.video_ids) - have:
            raise SystemExit("Not all IDs are queued")
        if args.cmd == "approve":
            expiry = parse_time(args.reviewed_until)
            if not now < expiry <= now + dt.timedelta(days=14):
                raise SystemExit("Review expiry must be in the next 14 days (use shorter windows for news/pricing)")
        for i in data["items"]:
            if i["video_id"] not in args.video_ids:
                continue
            i["approval"] = "approved" if args.cmd == "approve" else "held"
            if args.cmd == "approve":
                if i["category"] == "news" and expiry > now + dt.timedelta(hours=72):
                    raise SystemExit("News needs a fresh review within 72 hours")
                read_kit(cfg, i)
                i.update(reviewed_at=iso(now), expires_at=iso(expiry))
                if args.platforms:
                    i["platforms"] = args.platforms
    elif args.cmd in {"enable", "disable"}:
        cfg["enabled"] = args.cmd == "enable"
        save_json(ROOT / "config/publishing.json", cfg)
        print("Local publishing switch:", cfg["enabled"], "(commit required; daily mode still needs a verified live pilot)")
        return
    elif args.cmd == "pilot-passed":
        item = next(i for i in data["items"] if i["video_id"] == args.video_id)
        records = load_json(ROOT / "tracker/publications.json")["records"]
        for platform in item["platforms"]:
            rec = records.get(args.video_id + ":" + platform, {})
            if rec.get("state") != "sent" or not rec.get("external_url"):
                raise SystemExit("Pilot must be confirmed sent, with an external URL, on every selected platform")
        cfg["live_pilot_passed"] = True
        cfg["live_pilot_video"] = args.video_id
        save_json(ROOT / "config/publishing.json", cfg)
        print("Verified live pilot recorded; commit to allow daily queue runs")
        return
    save_json(path, data)
    print("Queue saved. No Buffer posts created. Commit changes to use them in the cloud.")


if __name__ == "__main__":
    main()
