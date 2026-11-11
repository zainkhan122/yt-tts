"""Posting rules (owner 2026-10-21, gap removed 2026-10-30) — enforced in code, not just documented.

1. DAILY COUNT: each calendar day (America/New_York, the channel calendar) posts a random
   number of shorts from 1 to 5. The number is drawn ONCE per day with a CSPRNG and stored in
   tracker/daily-counts.json. It is never redrawn, so reruns, retries and dry-runs agree.
2. BEST TIME PER CHANNEL: each channel (YouTube, Instagram, Facebook) ranks its posting hours
   by the median views in tracker/buffer-insights.json (read-only Buffer Insights snapshot,
   America/New_York). Only hours with at least `min_samples_per_hour` sent posts are ranked.
3. SEQUENCE + RANDOM OFFSET: the k-th short of a day gets the k-th best slot of THAT channel.
   The 150-minute minimum gap was REMOVED (owner 2026-10-30). Each best-time slot gets a
   deterministic random 5-15 minute offset (CSPRNG, seeded by platform+day+slot_index) so
   actual posting times vary naturally. Hours with no reliable data fall back to the researched
   profile window.
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


def daily_count(day: dt.date, path: Path = COUNTS_PATH, rng=None, allow_draw: bool = True):
    """Return the day's count (1–5). Draw once; a stored value is never changed.

    With allow_draw=False (cloud runs) a day that was never drawn returns None, so the planner
    holds that day instead of drawing on a throwaway runner (which would differ every run).
    """
    rng = rng or secrets.SystemRandom()
    data = json.loads(path.read_text()) if path.exists() else {"schema_version": 1, "days": {}}
    key = day.isoformat()
    if key in data["days"]:
        return int(data["days"][key]["count"])
    if not allow_draw:
        return None
    count = rng.randint(DRAW_MIN, DRAW_MAX)
    data["days"][key] = {"count": count, "drawn_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                         "method": "secrets.SystemRandom().randint(1,5)"}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n")
    return count


def draw_days(first: dt.date, days: int, path: Path = COUNTS_PATH) -> dict:
    """Draw and persist counts for missing days (run locally, then commit the store)."""
    return {(first + dt.timedelta(days=i)).isoformat(): daily_count(first + dt.timedelta(days=i), path)
            for i in range(days)}


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


def _to_min(clock: str) -> int:
    return int(clock[:2]) * 60 + int(clock[3:])


def _clock(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _buffer_slots(platform: str, report: dict | None, now: dt.datetime) -> tuple[list[str], str]:
    """Buffer's windows for this platform, or ([], reason) when they cannot be used."""
    from tools.post import buffer_windows as bw
    ok, why = bw.is_fresh(report, now)
    if not ok:
        return [], why
    slots = (report["platforms"].get(platform) or {}).get("clocks_by_use") or []
    if not slots:
        return [], f"no Buffer window for {platform}"
    return slots, "fresh Buffer windows"


def buffer_gap_minutes(platform: str, pick_index: int, rules: dict) -> int:
    """Random gap 5-20 min between Buffer-bracket picks, deterministic per platform and pick index."""
    import hashlib
    gap = rules.get("buffer_gap_minutes") or {}
    lo, hi = int(gap.get("min", 5)), int(gap.get("max", 20))
    digest = hashlib.sha256(f"gap:{platform}:{pick_index}".encode()).hexdigest()
    return int(digest[:8], 16) % (hi - lo + 1) + lo


def ranked_clocks(insights_posts: dict, platform: str, profile: dict, cfg: dict, want: int,
                  zone: ZoneInfo, windows_report: dict | None = None,
                  now: dt.datetime | None = None) -> tuple[list[str], dict]:
    """Best `want` distinct clocks for one channel, best first.

    The 150-minute minimum gap was removed (owner 2026-10-30); all ranked hours are eligible.
    Missing slots come from the 18:00–21:00 fallback window, and provenance says which
    clocks came from data and which from the fallback.
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
        # Owner rule 2026-10-21: without enough data for this channel, post in the 18:00–21:00
        # window (channel time zone). Candidates are every 30 minutes in that window; the minimum
        # gap still applies, so the window holds at most floor(180/gap)+1 slots.
        # Owner 31 Oct 2026: the fallback is Buffer's own posting windows for the channel (refreshed weekly
        # by tools/post/buffer_windows.py). A stale or missing snapshot falls back to the researched window.
        buffer_slots, why = _buffer_slots(platform, windows_report, now or dt.datetime.now(dt.timezone.utc))
        lo, hi = (rules.get("fallback_window") or ["18:00", "21:00"])
        spacing = gap
        if buffer_slots:
            # Buffer's slots are many and nearly all used once, so their order alone says little. Keep the
            # researched evening window first, then the rest, and space picks apart so they do not cluster.
            # Owner 2026-10-31: a Buffer slot is a time BRACKET, not an exact time. Each slot maps to its
            # bracket start (30-minute bracket); the real posting time is bracket + random offset (cadence).
            bracket = int(rules.get("buffer_bracket_minutes", 30))
            brackets = sorted({_to_min(c) // bracket * bracket for c in buffer_slots})
            in_win = [m for m in brackets if _to_min(lo) <= m <= _to_min(hi)]
            rest = [m for m in brackets if m not in in_win]
            # rest: nearest to the researched window first, so 07:00 comes before 06:00
            rest.sort(key=lambda m: min(abs(m - _to_min(lo)), abs(m - _to_min(hi))))
            candidates = in_win + rest
            spacing = None  # per pick, below
            provenance["fallback_source"] = "buffer-windows"
            provenance["fallback_slots_by_use"] = buffer_slots[:40]
        else:
            candidates = list(range(_to_min(lo), _to_min(hi) + 1, 30))
            provenance["fallback_source"] = "researched-window"
            provenance["fallback_window"] = [lo, hi]
        provenance["fallback_note"] = why
        added = []
        for m in candidates:
            if len(clocks) >= want:
                break
            if spacing is None:
                need = buffer_gap_minutes(platform, len(clocks), rules)
            if all(abs(m - _to_min(c)) >= (need if spacing is None else spacing) for c in clocks):
                clocks.append(_clock(m))
                added.append(_clock(m))
        provenance["fallback_clocks"] = added
    return clocks[:want], provenance


def load_insights(path: Path = INSIGHTS_PATH) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text()).get("posts", {})


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Draw missing daily shorts counts (1-5) for the next N channel days.")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--from-date", help="YYYY-MM-DD (default: today in America/New_York)")
    args = ap.parse_args(argv)
    first = (dt.date.fromisoformat(args.from_date) if args.from_date
             else dt.datetime.now(ZoneInfo("America/New_York")).date())
    result = draw_days(first, args.days)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
