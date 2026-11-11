#!/usr/bin/env python3
"""Reference insights from YouTube channels in the registry, read with yt-dlp (decision 2, 31 Oct 2026).

Reads every `youtube` row of research/sources.csv (so the list is never hand-kept), asks yt-dlp for the
latest videos of each channel, up to the cap per tab (videos and Shorts), metadata only, and writes tracker/reference-insights.json:
per channel, the recent video count, median views, short vs long split, and the top titles by views.

Requires yt-dlp (`pip install --user yt-dlp`). The sandbox does not keep ~/.local between sessions, so
reinstall when this tool says it is missing.

Usage:
  python3 tools/reference/ytdlp_insights.py                 # all youtube rows, 15 latest videos each
  python3 tools/reference/ytdlp_insights.py --per-channel 25 --only Fireship
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import importlib.util
import json
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / "research" / "sources.csv"
OUT = ROOT / "tracker" / "reference-insights.json"
SHORT_MAX_S = 60
TIMEOUT_S = 300


class YtDlpMissing(RuntimeError):
    pass


def reference_channels(sources: Path = SOURCES) -> list[dict]:
    with sources.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    out = []
    for r in rows:
        if r.get("type") == "youtube" and str(r.get("url", "")).startswith("https://"):
            out.append({"handle": r["handle"], "url": r["url"]})
    return out


def _check_installed() -> None:
    if importlib.util.find_spec("yt_dlp") is None:
        raise YtDlpMissing("yt-dlp is not installed. Run: pip install --user yt-dlp")


def fetch_channel(url: str, per_channel: int, runner=None) -> list[dict]:
    """Return metadata dicts for the channel's latest videos. `runner` is injectable for tests."""
    if runner is None:
        _check_installed()

        def runner(u, n):  # noqa: E306
            cmd = [sys.executable, "-m", "yt_dlp", "--dump-json", "--skip-download", "--no-warnings",
                   "--playlist-end", str(n), u]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_S)
            if proc.returncode != 0 and not proc.stdout.strip():
                raise RuntimeError(proc.stderr.strip()[-300:] or "yt-dlp failed")
            return proc.stdout
    text = runner(url, per_channel)
    videos = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            v = json.loads(line)
        except json.JSONDecodeError:
            continue
        videos.append({
            "id": v.get("id"),
            "title": v.get("title"),
            "url": v.get("webpage_url") or (f"https://www.youtube.com/watch?v={v['id']}" if v.get("id") else None),
            "upload_date": v.get("upload_date"),
            "duration_s": v.get("duration"),
            "views": v.get("view_count"),
            "likes": v.get("like_count"),
            "comments": v.get("comment_count"),
        })
    return videos


def summarise(videos: list[dict]) -> dict:
    views = [v["views"] for v in videos if isinstance(v.get("views"), int)]
    shorts = [v for v in videos if isinstance(v.get("duration_s"), (int, float)) and v["duration_s"] <= SHORT_MAX_S]
    longs = [v for v in videos if isinstance(v.get("duration_s"), (int, float)) and v["duration_s"] > SHORT_MAX_S]
    top = sorted((v for v in videos if isinstance(v.get("views"), int)), key=lambda v: -v["views"])[:5]
    return {
        "videos": len(videos),
        "median_views": int(statistics.median(views)) if views else None,
        "shorts": len(shorts),
        "long": len(longs),
        "median_views_short": int(statistics.median([v["views"] for v in shorts if isinstance(v.get("views"), int)])) if any(isinstance(v.get("views"), int) for v in shorts) else None,
        "median_views_long": int(statistics.median([v["views"] for v in longs if isinstance(v.get("views"), int)])) if any(isinstance(v.get("views"), int) for v in longs) else None,
        "top": [{"title": v["title"], "views": v["views"], "likes": v.get("likes"), "comments": v.get("comments"),
                 "duration_s": v.get("duration_s"), "upload_date": v.get("upload_date"), "url": v["url"]} for v in top],
    }


def build(per_channel: int = 15, only: set[str] | None = None, runner=None, sources: Path = SOURCES) -> dict:
    channels = reference_channels(sources)
    if only:
        channels = [c for c in channels if c["handle"] in only]
    report = {"collected_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
              "per_channel": per_channel, "channels": []}
    for c in channels:
        entry = {"handle": c["handle"], "url": c["url"]}
        try:
            entry.update(summarise(fetch_channel(c["url"], per_channel, runner=runner)))
        except YtDlpMissing:
            raise
        except Exception as exc:  # one channel failing does not stop the rest; the failure is recorded
            entry["error"] = f"{type(exc).__name__}: {exc}"
        report["channels"].append(entry)
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--per-channel", type=int, default=15)
    ap.add_argument("--only", nargs="*", default=None, help="channel handles to include")
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args(argv)
    try:
        report = build(args.per_channel, set(args.only) if args.only else None)
    except YtDlpMissing as exc:
        print(f"BLOCK {exc}", file=sys.stderr)
        return 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    bad = [c["handle"] for c in report["channels"] if "error" in c]
    print(f"{len(report['channels']) - len(bad)} channel(s) read -> {args.out}")
    if bad:
        print("failed:", ", ".join(bad), file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
