"""Posting rules (owner 2026-10-21) — enforced in code, not just documented.

1. DAILY COUNT: each calendar day (America/New_York, the channel calendar) posts a random
   number of shorts from 1 to 5. The number is drawn ONCE per day with a CSPRNG and stored in
   tracker/daily-counts.json. It is never redrawn, so reruns, retries and dry-runs agree.
2. BEST TIME PER CHANNEL: each channel (YouTube, Instagram, Facebook) ranks its posting hours
   by the median views in tracker/buffer-insights.json (read-only Buffer Insights snapshot,
   America/New_York). Only hours with at least `min_samples_per_hour` sent posts are ranked.
3. SEQUENCE, NO SHARED TIMES: the k-th short of a day gets the k-th best slot of THAT channel.
   Slots on one channel are at least `minimum_gap_minutes` apart, so no two shorts share a
   time on the same channel. Hours with no reliable data fall back to the researched profile.
"""
from __future__ import annotations

import datetime as dt
import json
import secrets
import statistics
from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
COUNTS_PATH = ROOT / "tracker" / "daily-counts.json"
INSIGHTS_PATH = ROOT / "tracker" / "buffer-insights.json"
DRAW_MIN, DRAW_MAX = 1, 5
# The metric each channel is ranked by (names as Buffer reports them).
METRIC_TYPE = {"youtube": "views", "instagram": "views", "facebook": "impressions"}


class BestTimeError(ValueError):
    pass


def daily_count(day: dt.date, path: Path = COUNTS_PATH, rng=None) -> int:
    """Return the day's count (1–5). Draw once; a stored value is never changed."""
    rng = rng or secrets.SystemRandom()
    data = json.loads(path.read_text()) if path.exists() else {"schema_version": 1, "days": {}}
    key = day.isoformat()
    if key in data["days"]:
        return int(data["days"][key]["count"])
    count = rng.randint(DRAW_MIN, DRAW_MAX)
    data["days"][key] = {"count": count, "drawn_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                         "method": "secrets.SystemRandom().randint(1,5)"}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n")
    return count


def _views(post: dict, platform: str):
    wanted = METRIC_TYPE[platform]
    for metric in post.get("metrics") or []:
        if metric.get("type") == wanted:
            return metric.get("value")
    return None


def hourly_medians(insights_posts: dict, platform: str, zone: ZoneInfo, min_samples: int) -> dict[int, float]:
    """Median metric per local hour for one channel, only hours with enough sent posts."""
    buckets: dict[int, list] = defaultdict(list)
    for post in insights_posts.values():
        if post.get("platform") != platform or post.get("metrics_status") != "fresh":
            continue
        value = _views(post, platform)
        sent = post.get("sent_at")
        if value is None or not sent:
            continue
        local = dt.datetime.fromisoformat(sent.replace("Z", "+00:00")).astimezone(zone)
        buckets[local.hour].append(value)
    return {h: statistics.median(v) for h, v in buckets.items() if len(v) >= min_samples}


def ranked_clocks(insights_posts: dict, platform: str, profile: dict, cfg: dict, want: int,
                  zone: ZoneInfo) -> tuple[list[str], dict]:
    """Best `want` distinct clocks for one channel, best first, honouring the minimum gap.

    Returns (clocks, provenance). Missing slots are filled from the profile's weekly slots,
    and provenance says which clocks came from data and which from the fallback.
    """
    rules = cfg["schedule"].get("best_times", {})
    min_samples = int(rules.get("min_samples_per_hour", 3))
    gap = int(cfg["schedule"]["minimum_gap_minutes"])
    medians = hourly_medians(insights_posts, platform, zone, min_samples)
    ordered = sorted(medians, key=lambda h: (-medians[h], h))
    chosen: list[int] = []
    for hour in ordered:
        if len(chosen) >= want:
            break
        if all(abs(hour * 60 - c * 60) >= gap for c in chosen):
            chosen.append(hour)
    provenance = {"source": "buffer-insights", "metric": METRIC_TYPE[platform],
                  "hours_with_data": len(medians), "min_samples_per_hour": min_samples,
                  "ranked_hours": {f"{h:02d}:00": medians[h] for h in ordered}}
    clocks = [f"{h:02d}:00" for h in chosen]
    if len(clocks) < want:
        # Researched profile slots first, then the configured 150-minute extended grid, so a
        # day's full count is always placeable. Every fallback clock keeps the minimum gap.
        ext = cfg["schedule"].get("extended_slots") or {}
        grid_gap = max(int(ext.get("gap_minutes", gap)), gap)
        start = int(ext.get("start", "00:00")[:2]) * 60 + int(ext.get("start", "00:00")[3:])
        grid = [f"{(start + i * grid_gap) // 60:02d}:{(start + i * grid_gap) % 60:02d}"
                for i in range(0, 24 * 60 // grid_gap + 1) if start + i * grid_gap < 24 * 60]
        profile_slots = sorted({c for day in profile.get("weekly_slots", {}).values() for c in day})
        added = []
        for clock in profile_slots + grid:
            if len(clocks) >= want:
                break
            m = int(clock[:2]) * 60 + int(clock[3:])
            if all(abs(m - (int(c[:2]) * 60 + int(c[3:]))) >= gap for c in clocks):
                clocks.append(clock)
                added.append(clock)
        provenance["fallback_clocks"] = added
    return clocks[:want], provenance


def load_insights(path: Path = INSIGHTS_PATH) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text()).get("posts", {})
