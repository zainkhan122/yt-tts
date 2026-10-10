"""Three separate weekly long-form lanes, UTC timestamps and no 'publish now'."""
import datetime as dt
from collections import Counter
from zoneinfo import ZoneInfo

from tools.post.cadence import DAYS, at_local
from tools.post.common import iso, parse_time


def week(value, zone):
    return value.astimezone(zone).strftime("%G-W%V")


def plan(items, records, shorts_records, cfg, now, preview=False):
    zone = ZoneInfo(cfg["timezone"])
    earliest = now + dt.timedelta(minutes=cfg["minimum_publish_lead_minutes"])
    end = now + dt.timedelta(days=cfg["lookahead_days"])
    occupied = [parse_time(r["publish_at"]) for r in records.values() if r.get("publish_at") and r.get("state") != "cancelled"]
    short_times = [parse_time(r.get("due_at") or r.get("sent_at")) for r in shorts_records.values()
                   if r.get("platform") == "youtube" and (r.get("due_at") or r.get("sent_at")) and r.get("state") != "retry_wait"]
    counts = Counter(week(t, zone) for t in occupied)
    slots = []
    day = earliest.astimezone(zone).date()
    while day <= end.astimezone(zone).date():
        for slot in cfg["weekly_slots"]:
            if DAYS[day.weekday()] != slot["day"]:
                continue
            t = at_local(day, slot["time"], cfg["timezone"])
            if t and earliest <= t <= end:
                slots.append((t, slot["category"]))
        day += dt.timedelta(days=1)
    result, notes, used = [], [], set()
    for item in sorted(items, key=lambda i: (i.get("priority", 100), i["video_id"])):
        old = records.get(item["video_id"], {})
        if old.get("state") in {"sent", "scheduled", "cancelled"}:
            continue
        if item.get("approval") != "approved" and not (preview and item.get("approval") == "held"):
            continue
        if not preview and (not item.get("public_approved") or not item.get("reviewed_at") or not item.get("expires_at")):
            continue
        existing = parse_time(old.get("publish_at"))
        choices = [(existing, item["category"])] if existing and earliest <= existing <= end else slots
        for due, category in choices:
            if category != item["category"] or due in used:
                continue
            if parse_time(item.get("not_before")) and due < parse_time(item["not_before"]):
                continue
            if parse_time(item.get("expires_at")) and due > parse_time(item["expires_at"]):
                continue
            if due in occupied and due != existing:
                continue
            if counts[week(due, zone)] >= cfg["max_long_videos_per_week"] and due != existing:
                continue
            if any(abs((due-t).total_seconds()) < cfg["short_long_gap_minutes"]*60 for t in short_times):
                continue
            if due != existing:
                occupied.append(due)
                counts[week(due, zone)] += 1
            used.add(due)
            result.append({"video_id": item["video_id"], "category": category, "publish_at": iso(due),
                           "publish_local": due.astimezone(zone).isoformat(),
                           "upload_eligible": due <= now + dt.timedelta(hours=cfg["upload_ahead_hours"])})
            break
        else:
            notes.append(item["video_id"] + ": no fresh, collision-free weekly slot; held, never publish immediately")
    return sorted(result, key=lambda r: r["publish_at"]), notes
