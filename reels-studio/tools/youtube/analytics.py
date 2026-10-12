#!/usr/bin/env python3
"""Shorts performance snapshots - 24 h / 7 d, judged against our own history.

Two data sources, one honest report:
  * YouTube Data API (current grant: youtube.force-ssl) - publishedAt, views, likes, comments.
  * YouTube Analytics API (grant: yt-analytics.readonly) - impressions, CTR, average view
    duration/percentage, i.e. the numbers that say whether a cover or a title actually works.
    That scope is NOT in the current grant. The lane still runs: those fields are recorded as
    explicitly unavailable with the reason, never as zeros. One-time remedy (owner action):
      REELS_EXTRA_SCOPES=https://www.googleapis.com/auth/yt-analytics.readonly
      python3 tools/youtube/oauth_handoff.py ...   (re-consent once), then re-run this tool.

  python3 tools/youtube/analytics.py snapshot [--store tracker/analytics.json] [--dry-run]
  python3 tools/youtube/analytics.py report   [--store tracker/analytics.json] [--json]

Read-only: this module never mutates YouTube state. It writes one tracker file
(tracker/analytics.json), which the cloud runner commits like the other journals.
"""
import argparse
import datetime as dt
import json
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from lib.secrets import redact, secure_vault  # noqa: E402
secure_vault()
from tools.post.common import config as root_config, iso, load_json, parse_time, save_json  # noqa: E402
from tools.post.state import Journal  # noqa: E402
from tools.youtube.api import ANALYTICS_REPORTS, YouTubeAPI  # noqa: E402

STORE = ROOT / "tracker/analytics.json"
SCHEMA_VERSION = 1
WINDOWS = (("24h", 24.0), ("7d", 168.0))
ANALYTICS_METRICS = "impressions,impressionClickThroughRate,averageViewDuration,averageViewPercentage"
ID_RE = re.compile(r"(?:youtu\.be/|youtube\.com/(?:shorts/|watch\?v=))([A-Za-z0-9_-]{11})(?:[?&#/]|$)")


def external_id(url):
    match = ID_RE.search(url or "")
    return match[1] if match else None


def targets(records):
    """Sent/published Shorts that carry a resolvable YouTube id, keyed by our video id."""
    out = {}
    for record in records.values():
        if record.get("platform") != "youtube" or record.get("state") not in {"sent", "published_manual"}:
            continue
        ytid = record.get("youtube_id") or external_id(record.get("external_url"))
        if ytid:
            out[record["video_id"]] = ytid
    return out


def empty_store():
    return {"schema_version": SCHEMA_VERSION, "updated_at": None, "videos": {}}


def load_store(path):
    path = Path(path)
    if not path.exists():
        return empty_store()
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("videos", {})
    return data


def data_api_stats(api, youtube_ids):
    """views / likes / comments / publishedAt, batched 50 ids per call (1 unit each)."""
    stats = {}
    for i in range(0, len(youtube_ids), 50):
        body = api.json("GET", "videos", params={"part": "snippet,statistics", "id": ",".join(youtube_ids[i:i + 50])}, cost=1)
        for v in body.get("items", []):
            st = v.get("statistics", {})
            stats[v["id"]] = {
                "published_at": v["snippet"]["publishedAt"],
                "views": int(st.get("viewCount", 0)),
                "likes": int(st.get("likeCount", 0)),
                "comments": int(st.get("commentCount", 0)),
            }
    return stats


def reports_metrics(api, youtube_id, published_at, now):
    """Analytics API summary for one video, or an explicit reason why it is missing."""
    start = parse_time(published_at).date()
    end = now.date()
    try:
        body = api.json("GET", ANALYTICS_REPORTS, params={
            "ids": "channel==MINE", "startDate": str(start), "endDate": str(end),
            "metrics": ANALYTICS_METRICS, "filters": f"video=={youtube_id}"}, cost=1)
    except Exception as exc:  # noqa: BLE001 - any failure is recorded verbatim, never guessed
        return {"unavailable": redact(f"{type(exc).__name__}: {exc}")[:200]}
    rows = body.get("rows") or []
    if not rows:
        return {"unavailable": "no rows returned (video may be younger than Analytics freshness)"}
    impressions, ctr, avg_view_s, avg_view_pct = rows[0]
    return {"impressions": int(impressions), "ctr": round(float(ctr), 5),
            "avg_view_duration_s": round(float(avg_view_s), 2), "avg_view_percentage": round(float(avg_view_pct), 2)}


def due_windows(record, age_hours):
    taken = {s["window"] for s in record.get("snapshots", [])}
    return [w for w, hours in WINDOWS if age_hours >= hours and w not in taken]


def snapshot(api, records, store, now, include_analytics=True):
    """Add every window that is due (24 h, then 7 d). Idempotent: one snapshot per window."""
    found = targets(records)
    stats = data_api_stats(api, sorted(set(found.values()))) if found else {}
    changed = []
    for video_id, ytid in sorted(found.items()):
        st = stats.get(ytid)
        if not st:
            continue  # video not readable with this grant (private/deleted); skip, do not invent
        record = store["videos"].setdefault(video_id, {"youtube_id": ytid, "title": None, "snapshots": []})
        record["youtube_id"] = ytid
        published = parse_time(st["published_at"])
        age_hours = (now - published).total_seconds() / 3600
        for window in due_windows(record, age_hours):
            entry = {"window": window, "taken_at": iso(now), "age_hours": round(age_hours, 2),
                     "published_at": st["published_at"], "views": st["views"], "likes": st["likes"],
                     "comments": st["comments"],
                     "engagement_rate": round((st["likes"] + st["comments"]) / st["views"], 5) if st["views"] else None}
            entry["analytics"] = (reports_metrics(api, ytid, st["published_at"], now)
                                  if include_analytics else {"unavailable": "skipped"})
            record["snapshots"].append(entry)
            changed.append(f"{video_id}@{window}")
        record["snapshots"].sort(key=lambda s: s["age_hours"])
    store["updated_at"] = iso(now)
    return changed


def _median(values):
    values = [v for v in values if v is not None]
    return round(statistics.median(values), 4) if len(values) >= 2 else None


def summarize(store):
    """Channel-context report: each window against the median of our own other videos.

    Medians need at least two other comparable videos; below that the report says so
    instead of implying a baseline that does not exist yet.
    """
    lines = []
    videos = store.get("videos", {})
    for window, _ in WINDOWS:
        rows = {vid: next((s for s in rec.get("snapshots", []) if s["window"] == window), None) for vid, rec in videos.items()}
        rows = {vid: s for vid, s in rows.items() if s}
        if not rows:
            continue
        lines.append(f"== {window} window ({len(rows)} videos with a snapshot)")
        views_med = _median([s["views"] for s in rows.values()])
        for vid, s in sorted(rows.items(), key=lambda kv: -kv[1]["views"]):
            others = [o["views"] for k, o in rows.items() if k != vid]
            baseline = _median(others)
            ratio = f"x{s['views'] / baseline:.2f} vs median(n={len(others)})" if baseline else "baseline: needs 2+ other videos"
            a = s.get("analytics") or {}
            perf = (f"CTR {a['ctr'] * 100:.2f}% · avg view {a['avg_view_percentage']:.1f}% · {a['impressions']} impressions"
                    if "ctr" in a else f"CTR/retention unavailable ({a.get('unavailable', 'no data')})")
            eng = f"{s['engagement_rate'] * 100:.2f}%" if s.get("engagement_rate") is not None else "-"
            lines.append(f"  {vid:26s} views {s['views']:>6} (eng {eng})  {ratio}  {perf}")
        lines.append("")
    if not lines:
        lines = ["no snapshots yet: run `analytics.py snapshot` once videos are 24 h old"]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("snapshot", "report"):
        p = sub.add_parser(name)
        p.add_argument("--store", default=str(STORE))
        p.add_argument("--json", action="store_true")
        if name == "snapshot":
            p.add_argument("--dry-run", action="store_true", help="read YouTube, change nothing")
    a = ap.parse_args()
    store = load_store(a.store)
    if a.cmd == "report":
        if a.json:
            print(json.dumps(store, indent=2))
        else:
            print(summarize(store))
        return
    cfg, root_cfg = load_json(ROOT / "config/youtube.json"), root_config()
    journal = Journal(root_cfg, remote=False, path=ROOT / "tracker/youtube-publications.json",
                      remote_path="tracker/youtube-publications.json")
    api = YouTubeAPI(cfg, journal)
    records = load_json(ROOT / "tracker/publications.json")["records"]
    changed = snapshot(api, records, store, dt.datetime.now(dt.timezone.utc))
    print(f"snapshots written: {', '.join(changed) if changed else 'none due'}")
    if not a.dry_run and changed:
        save_json(Path(a.store), store)
        print(f"store -> {a.store}")
    print(summarize(store))


if __name__ == "__main__":
    main()
