#!/usr/bin/env python3
"""Buffer posting windows per channel, read-only (owner 31 Oct 2026: best-time windows from Buffer, refreshed weekly).

Reads each connected YouTube, Instagram and Facebook channel's `postingSchedule` from Buffer (per day of
week: the time slots and whether the day is paused) and writes tracker/buffer-windows.json. Read-only:
it never creates, edits or deletes a post or a schedule.

best_times.py uses these windows as the fallback slots for a channel that has too little of its own
view data. A snapshot older than MAX_AGE_DAYS is not used; best_times then falls back to the researched
window and says so in its provenance. The weekly workflow (.github/workflows/buffer-windows.yml) keeps it fresh.

Usage:
  BUFFER_API_KEY=... python3 tools/post/buffer_windows.py            # write tracker/buffer-windows.json
  python3 tools/post/buffer_windows.py --check                        # report freshness of the stored file
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "post"))
OUT = ROOT / "tracker" / "buffer-windows.json"
PLATFORMS = {"youtube": "youtube", "instagram": "instagram", "facebook": "facebook"}
MAX_AGE_DAYS = 8          # weekly refresh + one day of slack
DAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
CLOCK = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")

WINDOWS_QUERY = """query HypelessWindows($org: OrganizationId!) {
  channels(input: { organizationId: $org }) {
    id name service timezone isDisconnected
    postingSchedule { day paused times }
  }
}"""


def _day_name(value) -> str | None:
    if isinstance(value, str) and value.strip().lower() in DAYS:
        return value.strip().lower()
    return None


def build(channels: list[dict], now: dt.datetime) -> dict:
    """Turn Buffer's channel list into the stored report. Pure function, so it is testable offline."""
    platforms, skipped = {}, []
    for ch in channels:
        service = str(ch.get("service") or "").lower()
        if service not in PLATFORMS:
            continue
        if ch.get("isDisconnected"):
            skipped.append({"platform": service, "reason": "channel disconnected in Buffer"})
            continue
        days, freq, bad = {}, {}, []
        for slot in ch.get("postingSchedule") or []:
            day = _day_name(slot.get("day"))
            if day is None:
                bad.append(f"unknown day {slot.get('day')!r}")
                continue
            clocks = []
            for t in slot.get("times") or []:
                if isinstance(t, str) and CLOCK.match(t.strip()):
                    clocks.append(t.strip())
                else:
                    bad.append(f"{day}: time {t!r} is not HH:MM")
            days[day] = {"paused": bool(slot.get("paused")), "times": sorted(set(clocks))}
            if not slot.get("paused"):
                for c in set(clocks):
                    freq[c] = freq.get(c, 0) + 1
        # most-used slots first, then earliest; this is the order best_times consumes them in
        clocks_ranked = [c for c, _ in sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))]
        platforms[service] = {
            "channel_id": ch.get("id"),
            "name": ch.get("name"),
            "timezone": ch.get("timezone"),
            "days": {d: days[d] for d in DAYS if d in days},
            "clocks_by_use": clocks_ranked,
            "problems": bad,
        }
    return {
        "fetched_at": now.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "Buffer channel.postingSchedule (read-only)",
        "max_age_days": MAX_AGE_DAYS,
        "platforms": platforms,
        "skipped": skipped,
    }


def fetch(settings: dict, client=None) -> list[dict]:
    if client is None:
        from buffer_api import BufferClient  # noqa: WPS433 (imported only when a live call is needed)
        client = BufferClient(settings)
    data = client.request(WINDOWS_QUERY, {"org": settings["organization_id"]})
    return data["channels"]


def is_fresh(report: dict | None, now: dt.datetime, max_age_days: int = MAX_AGE_DAYS) -> tuple[bool, str]:
    if not report or not report.get("fetched_at"):
        return False, "no Buffer windows snapshot"
    try:
        at = dt.datetime.strptime(report["fetched_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return False, "Buffer windows snapshot has an unreadable timestamp"
    age = now - at
    if age > dt.timedelta(days=max_age_days):
        return False, f"Buffer windows snapshot is {age.days} days old (limit {max_age_days})"
    return True, "fresh"


def load(path: Path = OUT) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="only report whether the stored snapshot is fresh")
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args(argv)
    now = dt.datetime.now(dt.timezone.utc)
    if args.check:
        ok, why = is_fresh(load(args.out), now)
        print(("OK " if ok else "STALE ") + why)
        return 0 if ok else 1
    settings = json.loads((ROOT / "config" / "publishing.json").read_text(encoding="utf-8"))["buffer"]
    report = build(fetch(settings), now)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for name, p in report["platforms"].items():
        print(f"{name}: {len(p['clocks_by_use'])} slot(s) {p['clocks_by_use']} ({p['timezone']})")
        for prob in p["problems"]:
            print(f"  note: {prob}")
    if not report["platforms"]:
        print("no connected YouTube/Instagram/Facebook channel found", file=sys.stderr)
        return 1
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
