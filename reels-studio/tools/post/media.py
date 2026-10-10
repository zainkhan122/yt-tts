#!/usr/bin/env python3
"""Build an immutable-ID GitHub Pages media bundle; never overwrite a queued URL.

Pins Release asset IDs and digests, checks QA/approved voice, and retains assets
for every nonterminal journal entry + seven days after successful publication.
If the site budget would be exceeded, fail rather than evict a pending video.
"""
import argparse
import datetime as dt
import hashlib
import html
import io
import json
import os
from pathlib import Path
import shutil
import sys
import zipfile

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from lib.secrets import gh_token
from tools.post.common import (TERMINAL, check_manifest, config, iso, load_json,
                               media_url, now_utc, parse_time, queue, save_json)


def asset_metadata(cfg, asset_id):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "Hypeless-Reels-Studio"}
    if gh_token():
        headers["Authorization"] = "Bearer " + gh_token()
    r = requests.get(f"https://api.github.com/repos/{cfg['repository']}/releases/assets/{int(asset_id)}", headers=headers, timeout=(10, 30))
    if r.status_code != 200:
        raise RuntimeError(f"Pinned Release asset {asset_id} is unavailable (HTTP {r.status_code})")
    return r.json()


def public_download(url, expected_size=None, digest=None, dest=None):
    # Only this unauthenticated request follows CDN redirects. Never forward a PAT.
    r = requests.get(url, stream=True, timeout=(10, 120))
    r.raise_for_status()
    sha, total, chunks = hashlib.sha256(), 0, []
    sink = open(dest, "wb") if dest else None
    try:
        for part in r.iter_content(1024 * 1024):
            total += len(part)
            if expected_size and total > expected_size:
                raise ValueError("Release asset size changed during download")
            sha.update(part)
            if sink:
                sink.write(part)
            else:
                chunks.append(part)
    finally:
        r.close()
        if sink:
            sink.close()
    if expected_size and total != expected_size:
        raise ValueError("Incomplete Release asset")
    actual = "sha256:" + sha.hexdigest()
    if digest and digest != actual:
        raise ValueError("Release asset digest mismatch")
    return actual, total, b"".join(chunks)


def read_kit(cfg, item):
    asset = asset_metadata(cfg, item["kit_asset_id"])
    if asset["name"] != item["video_id"] + "-kit.zip" or asset["size"] > 10_000_000:
        raise ValueError("Unexpected post kit")
    _, _, blob = public_download(asset["browser_download_url"], asset["size"], item.get("kit_digest") or asset.get("digest"))
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        name = item["video_id"] + "/manifest.json"
        info = z.getinfo(name)
        if info.file_size > 2_000_000:
            raise ValueError("Oversized kit manifest")
        manifest = json.loads(z.read(name))
    check_manifest(manifest, item["video_id"])
    return manifest


def references(items, records, cfg, now):
    refs = {}
    cutoff = now - dt.timedelta(days=cfg["media"]["retention_days"])
    for item in items:
        active_platforms = [p for p in item["platforms"] if cfg["buffer"]["channels"].get(p, {}).get("enabled")
                            and not cfg["buffer"]["channels"][p].get("posting_hold")]
        states = [records.get(f"{item['video_id']}:{p}") for p in active_platforms]
        all_done_old = all(r and r["state"] in TERMINAL and parse_time(r.get("sent_at")) and parse_time(r["sent_at"]) < cutoff for r in states)
        if item.get("approval") != "cancelled" and not all_done_old:
            refs[item["asset_id"]] = item
    for rec in records.values():
        item = rec.get("media_ref")
        if not item:
            continue
        sent = parse_time(rec.get("sent_at"))
        if rec["state"] not in TERMINAL or not sent or sent >= cutoff:
            refs[item["asset_id"]] = item
    return list(refs.values())


def build(dest, cfg, items, records):
    refs = references(items, records, cfg, now_utc())
    if sum(i["asset_size"] for i in refs) > cfg["media"]["max_site_bytes"]:
        raise RuntimeError("Pages media budget exceeded; no pending assets will be evicted")
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    index = {"generated_at": iso(now_utc()), "assets": {}}
    for item in refs:
        if item["media_path"] != f"media/{int(item['asset_id'])}/{item['video_id']}.mp4":
            raise ValueError("Invalid immutable media path")
        manifest = read_kit(cfg, item)
        asset = asset_metadata(cfg, item["asset_id"])
        if asset["name"] != item["video_id"] + ".mp4" or asset["size"] != item["asset_size"]:
            raise ValueError("Pinned video asset identity changed")
        path = dest / item["media_path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        digest, size, _ = public_download(asset["browser_download_url"], asset["size"], item.get("asset_digest") or asset.get("digest"), path)
        index["assets"][str(item["asset_id"])] = {"video_id": item["video_id"], "url": media_url(item, cfg), "digest": digest,
                                                    "size": size, "qa": manifest["qa"]["checks"]}
        print(f"media ready: {item['video_id']} · QA 7/7 · {size / 1e6:.1f} MB", flush=True)
    save_json(dest / "media-index.json", index)
    (dest / ".nojekyll").touch()
    callback = ROOT / "cloud/pages/oauth-callback.html"
    if callback.exists():
        callback_dir = dest / "oauth/callback"
        callback_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(callback, callback_dir / "index.html")
    links = "".join(f'<a href="{html.escape(c["url"], quote=True)}" rel="noopener">{html.escape(p.title())} ↗</a>' for p, c in cfg["buffer"]["channels"].items())
    page = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Hypeless — AI tools, minus the hype.</title><meta name="description" content="AI tools, news and useful open-source projects. Honest demos. Real limits."><style>*{box-sizing:border-box}body{margin:0;min-height:100vh;background:#050b1f;color:#f5f7ff;font:18px/1.6 system-ui;display:grid;place-items:center;padding:30px}main{width:min(720px,100%)}small{color:#38bdf8;text-transform:uppercase;letter-spacing:.2em}h1{font-size:clamp(60px,12vw,112px);line-height:1;letter-spacing:-.07em;margin:24px 0;color:#ffd60a}p{max-width:520px;color:#bbc7df}nav{display:flex;flex-wrap:wrap;gap:14px;margin:40px 0}a{color:#fff;text-decoration:none;padding:12px 24px;border:1px solid #34415e;border-radius:8px}a:hover{border-color:#38bdf8;color:#38bdf8}footer{font-size:13px;color:#8392b0}</style></head><body><main><small>Practical AI. Honest takes.</small><h1>Hypeless.</h1><p>AI tools, minus the hype.<br>Useful demos, AI news and open-source discoveries—with the catches left in.</p><nav>''' + links + '''</nav><footer>AI-generated narration. Sources and media credits accompany each video.</footer></main></body></html>'''
    (dest / "index.html").write_text(page, encoding="utf-8")
    return index


def verify_url(url, expected_size, session=None):
    session = session or requests
    if not url.startswith("https://"):
        raise ValueError("Media URL must use HTTPS")
    r = session.get(url, headers={"Range": "bytes=0-1023"}, stream=True, timeout=(10, 30), allow_redirects=False)
    try:
        if r.status_code not in (200, 206):
            raise ValueError(f"Media URL not direct/public (HTTP {r.status_code})")
        if r.headers.get("Content-Type", "").split(";", 1)[0] != "video/mp4":
            raise ValueError("Media URL did not return video/mp4")
        total = r.headers.get("Content-Range", "").rsplit("/", 1)[-1] if r.status_code == 206 else r.headers.get("Content-Length", "")
        if not total.isdigit() or int(total) != expected_size:
            raise ValueError("Hosted video length does not match pinned asset")
        first = next(r.iter_content(1024), b"")
        if len(first) < 12 or first[4:8] != b"ftyp":
            raise ValueError("Hosted file is not an MP4")
    finally:
        r.close()


def verify_site(cfg, items):
    url = cfg["media"]["base_url"].rstrip("/") + "/media-index.json"
    r = requests.get(url, timeout=(10, 30), allow_redirects=False)
    if r.status_code != 200:
        raise ValueError(f"Media index not ready (HTTP {r.status_code})")
    index = r.json()["assets"]
    for item in items:
        entry = index.get(str(item["asset_id"]))
        if not entry or entry["video_id"] != item["video_id"] or entry["url"] != media_url(item, cfg):
            raise ValueError("Pinned media absent from deployment")
        if item.get("asset_digest") and entry["digest"] != item["asset_digest"]:
            raise ValueError("Hosted media index digest mismatch")
        if not entry.get("qa", {}).get("approved_voice") or not all(entry["qa"].values()):
            raise ValueError("Hosted media failed QA/voice gate")
        verify_url(entry["url"], item["asset_size"])
        print("verified public media:", item["video_id"], flush=True)
    return index


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=["build", "verify"])
    ap.add_argument("--dest", default="/var/tmp/hypeless-pages")
    args = ap.parse_args()
    cfg, items = config(), queue()
    if args.command == "build":
        records = load_json(ROOT / "tracker/publications.json")["records"]
        build(args.dest, cfg, items, records)
    else:
        records = load_json(ROOT / "tracker/publications.json")["records"]
        verify_site(cfg, references(items, records, cfg, now_utc()))


if __name__ == "__main__":
    main()
