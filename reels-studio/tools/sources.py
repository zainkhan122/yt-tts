#!/usr/bin/env python3
"""
Source registry: every place content ideas come from (TikTok, YouTube Shorts/long-form, web feeds), in ONE file
(research/sources.csv), plus a git-tracked history of everything they post (research/sources/posts.csv).
Built to grow: add sources any time; each scan upserts posts (first_seen/last_seen + latest stats).

  python3 tools/sources.py add https://www.youtube.com/@danmartell --tabs shorts,videos --focus "business storytelling" --why "hooks"
  python3 tools/sources.py add https://www.tiktok.com/@someone --focus "AI tools"
  python3 tools/sources.py add https://www.producthunt.com/feed --name producthunt --focus "new launches"
  python3 tools/sources.py list
  python3 tools/sources.py scan --latest 15            # all active sources -> research/sources/posts.csv
Types: tiktok | youtube (tabs: shorts, videos or both) | rss (RSS/Atom feed). Verification runs before a source is saved.
"""
import argparse
import csv
import datetime as dt
import email.utils
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "research/sources.csv"
POSTS = ROOT / "research/sources/posts.csv"
FIELDS = ["type", "handle", "url", "tabs", "focus", "why_follow", "priority", "language", "added", "status"]
PFIELDS = ["platform", "source", "post_id", "url", "published", "title", "views", "likes", "comments", "shares", "saves",
           "duration", "first_seen", "last_seen"]
ATOM = "{http://www.w3.org/2005/Atom}"


def detect(url):
    if "tiktok.com/@" in url:
        return "tiktok", re.search(r"@([\w.]+)", url).group(1)
    if "youtube.com/@" in url:
        return "youtube", re.search(r"@([\w.-]+)", url).group(1)
    return "rss", re.sub(r"[^a-z0-9]+", "-", re.sub(r"^https?://(www\.)?", "", url).lower()).strip("-")[:40]


def load():
    return list(csv.DictReader(REG.open())) if REG.exists() else []


def save(rows):
    REG.parent.mkdir(parents=True, exist_ok=True)
    with REG.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows({k: r.get(k, "") for k in FIELDS} for r in rows)


def ytdlp_list(url, n):
    p = subprocess.run(["yt-dlp", "--flat-playlist", "--playlist-end", str(n), "-J", "--no-warnings", url],
                       capture_output=True, text=True, timeout=240)
    if p.returncode or not p.stdout.strip():
        raise RuntimeError((p.stderr or "no data").strip()[-160:])
    return json.loads(p.stdout).get("entries") or []


def rss_list(url, n):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 reels-studio"})
    for attempt in range(4):  # Reddit & co. rate-limit bursts (HTTP 429): back off and retry
        try:
            root = ET.fromstring(urllib.request.urlopen(req, timeout=40).read())
            break
        except urllib.error.HTTPError as ex:
            if ex.code != 429 or attempt == 3:
                raise
            time.sleep(6 * (attempt + 1))
    out = []
    for it in (root.findall(".//item") or root.findall(f".//{ATOM}entry"))[:n]:
        title = (it.findtext("title") or it.findtext(f"{ATOM}title") or "").strip()
        link = it.findtext("link") or ""
        if not link:
            le = it.find(f"{ATOM}link")
            link = le.get("href") if le is not None else ""
        date = it.findtext("pubDate") or it.findtext(f"{ATOM}updated") or it.findtext(f"{ATOM}published") or ""
        try:
            ts = email.utils.parsedate_to_datetime(date).timestamp() if "," in date else dt.datetime.fromisoformat(date.replace("Z", "+00:00")).timestamp()
        except (TypeError, ValueError):
            ts = 0
        desc = re.sub(r"<[^>]+>", " ", it.findtext("description") or it.findtext(f"{ATOM}summary") or it.findtext(f"{ATOM}content") or "")
        out.append({"id": link or title, "url": link, "title": title, "description": desc[:600], "timestamp": ts})
    return out


def fetch(src, n):
    """Latest posts of one source as normalized dicts."""
    if src["type"] == "rss":
        return [{**e, "platform": "web"} for e in rss_list(src["url"], n)]
    base = re.sub(r"/(shorts|videos|featured|streams)/?$", "", src["url"].rstrip("/"))  # tabs from the stored URL, not the handle
    urls = [src["url"]] if src["type"] == "tiktok" else [f"{base}/{t}" for t in (src.get("tabs") or "shorts").split(",")]
    out = []
    for u in urls:
        for e in ytdlp_list(u, n):
            out.append({"platform": src["type"] + ("-long" if u.endswith("/videos") else ""), "id": e.get("id"), "url": e.get("url"),
                        "title": e.get("title") or "", "description": e.get("description") or "", "timestamp": e.get("timestamp") or 0,
                        "views": e.get("view_count"), "likes": e.get("like_count"), "comments": e.get("comment_count"),
                        "shares": e.get("repost_count"), "saves": e.get("save_count"), "duration": e.get("duration")})
    return out


def upsert(posts_by_source):
    POSTS.parent.mkdir(parents=True, exist_ok=True)
    have = {(r["platform"], r["post_id"]): r for r in csv.DictReader(POSTS.open())} if POSTS.exists() else {}
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M")
    new = 0
    for handle, posts in posts_by_source.items():
        for e in posts:
            k = (e["platform"], str(e["id"]))
            row = have.get(k) or {"first_seen": now}
            new += k not in have
            pub = dt.datetime.fromtimestamp(e["timestamp"], dt.timezone.utc).strftime("%Y-%m-%d") if e.get("timestamp") else ""
            row.update({"platform": e["platform"], "source": handle, "post_id": str(e["id"]), "url": e.get("url") or "", "published": pub,
                        "title": re.sub(r"\s+", " ", (e.get("title") or ""))[:140], "views": e.get("views") or "", "likes": e.get("likes") or "",
                        "comments": e.get("comments") or "", "shares": e.get("shares") or "", "saves": e.get("saves") or "",
                        "duration": e.get("duration") or "", "last_seen": now})
            have[k] = row
    rows = sorted(have.values(), key=lambda r: (r["published"], r["source"]), reverse=True)
    with POSTS.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=PFIELDS)
        w.writeheader()
        w.writerows({k: r.get(k, "") for k in PFIELDS} for r in rows)
    return new, len(rows)


def scan_all(latest=15, priority=None, quiet=False):
    """Fetch every active source; persist to posts.csv; return {handle: posts} for the idea feed."""
    got = {}
    for s in load():
        if s["status"] != "active" or (priority and s["priority"] != priority):
            continue
        try:
            if "reddit.com" in s["url"]:
                time.sleep(10)  # Reddit rate-limits bursts; space its feeds out
            got[s["handle"]] = fetch(s, latest)
            if not quiet:
                print(f"  ✓ {s['type']:7s} {s['handle']:22s} {len(got[s['handle']]):3d} posts")
        except Exception as ex:
            print(f"  ✗ {s['type']:7s} {s['handle']:22s} {str(ex)[:90]}")
    new, total = upsert(got)
    print(f"posts.csv: {new} new posts, {total} total")
    return got


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("add")
    p.add_argument("url")
    p.add_argument("--name", help="handle override (rss)")
    p.add_argument("--tabs", default="shorts", help="youtube: shorts | videos | shorts,videos")
    p.add_argument("--focus", default="")
    p.add_argument("--why", default="")
    p.add_argument("--priority", default="daily", choices=["daily", "weekly"])
    p.add_argument("--lang", default="en")
    sub.add_parser("list")
    p = sub.add_parser("scan")
    p.add_argument("--latest", type=int, default=15)
    p.add_argument("--priority", choices=["daily", "weekly"])
    a = ap.parse_args()
    if a.cmd == "add":
        typ, handle = detect(a.url)
        handle = a.name or handle
        rows = load()
        if any(r["handle"].lower() == handle.lower() and r["type"] == typ for r in rows):
            raise SystemExit(f"already a source: {typ} {handle}")
        src = {"type": typ, "handle": handle, "url": a.url, "tabs": a.tabs if typ == "youtube" else "", "focus": a.focus,
               "why_follow": a.why, "priority": a.priority, "language": a.lang, "added": dt.date.today().isoformat(), "status": "active"}
        posts = fetch(src, 3)  # verification: must return posts
        if not posts:
            raise SystemExit(f"verification failed: no posts from {a.url}")
        rows.append(src)
        save(rows)
        print(f"added {typ} {handle} (verified: latest = {posts[0]['title'][:60]!r})")
    elif a.cmd == "list":
        for r in load():
            print(f"{r['status']:7s} {r['priority']:6s} {r['type']:7s} {r['handle']:22s} {r['tabs']:14s} {r['focus'][:50]}")
    else:
        scan_all(a.latest, a.priority)


if __name__ == "__main__":
    main()
