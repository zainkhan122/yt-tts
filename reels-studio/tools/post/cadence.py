"""Audience-local, DST-aware calendars; each network has its OWN time windows.

Explicit dueAt is the source of truth. Buffer's UI queue and its display timezone
are read-only. Extra fourth/fifth daily slots require a config change, never arise
because a render batch happens to be large.
"""
import datetime as dt
from collections import defaultdict
from zoneinfo import ZoneInfo

from tools.post.common import PENDING, RETRYABLE, TERMINAL, ROOT, iso, key, load_json, media_url, parse_time
from tools.post import planner as copy_rules

DAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def at_local(day, clock, timezone):
    hour, minute = map(int, clock.split(":"))
    zone = ZoneInfo(timezone)
    local = dt.datetime.combine(day, dt.time(hour, minute), zone).replace(fold=0)
    utc = local.astimezone(dt.timezone.utc)
    # Skip a nonexistent spring-forward time. Fall-back times occur once, fold=0.
    if utc.astimezone(zone).replace(tzinfo=None) != local.replace(tzinfo=None):
        return None
    return utc


def clocks_for(profile, day, target):
    target = min(5, max(1, target))
    name = DAYS[day.weekday()]
    base = profile["weekly_slots"][name]
    chosen = base[:target] + profile.get("optional_slots", {}).get(name, [])[:max(0, target-len(base))]
    return sorted(set(chosen))


def can_notify(when, events, limit):
    """Check every affected rolling 24h window, including already queued future posts."""
    others = list(events)
    ends = [when] + [t for t in others if when <= t < when + dt.timedelta(days=1)]
    return all(sum(end-dt.timedelta(days=1) < t <= end for t in others) + 1 <= limit for end in ends)


def _time(record):
    return parse_time(record.get("due_at") or record.get("sent_at"))


def plan(items, records, channels, posts, cfg, now, preview=False, pilot=False, long_records=None):
    settings = cfg["schedule"]
    target = min(settings.get("daily_target", 3), settings.get("max_videos_per_day", 5), 5)
    earliest = now + dt.timedelta(minutes=settings["minimum_lead_minutes"])
    end = now + dt.timedelta(hours=settings["lookahead_hours"])
    if long_records is None:
        p = ROOT / "tracker/youtube-publications.json"
        long_records = load_json(p).get("records", {}) if p.exists() else {}
    long_events = [parse_time(r.get("publish_at")) for r in long_records.values()
                   if r.get("publish_at") and r.get("state") not in {"cancelled", "blocked"}]
    long_ids = {r.get("youtube_id") for r in long_records.values() if r.get("youtube_id")}
    by_video = {i["video_id"]: i for i in items}
    live_channels = {c["id"]: c for c in channels}
    notes, rows = [], []
    for platform, expected in cfg["buffer"]["channels"].items():
        if not expected.get("enabled"):
            continue
        problem = copy_rules.channel_problem(live_channels.get(expected["buffer_id"]), expected)
        if problem or expected.get("posting_hold"):
            notes.append(f"{platform}: policy hold / blocked — {problem or expected['posting_hold']}")
            continue
        profile = settings["profiles"][platform]
        zone = ZoneInfo(profile.get("timezone", settings["timezone"]))
        events, pending, known_categories = {}, set(), defaultdict(set)
        for post in posts:
            if post["channelId"] != expected["buffer_id"]:
                continue
            external = post.get("externalLink") or ""
            if platform == "youtube" and any(vid in external for vid in long_ids):
                continue  # Long videos have a separate quota/calendar, but still a gap guard below.
            if post["status"] in PENDING:
                pending.add(post["id"])
            if post["status"] in PENDING | TERMINAL:
                t = parse_time(post.get("dueAt") or post.get("sentAt"))
                if t:
                    events[post["id"]] = t
        for rec_key, record in records.items():
            if record.get("platform") != platform or record["state"] in RETRYABLE:
                continue
            rid = record.get("buffer_post_id") or "journal:" + rec_key
            t = _time(record)
            if t:
                events[rid] = t
                category = record.get("category") or by_video.get(record["video_id"], {}).get("category")
                if not category and record["video_id"].startswith("repo-"):
                    category = "repo"
                if category:
                    known_categories[t.astimezone(zone).date()].add((record["video_id"], category))
            if record["state"] not in TERMINAL:
                pending.add(rid)
        capacity = min(cfg["buffer"]["queue_target_per_channel"], cfg["buffer"]["queue_limit_per_channel"]) - len(pending)
        if capacity <= 0:
            notes.append(f"{platform}: pending capacity reached; backlog retained")
            continue
        candidates = []
        for item in sorted(items, key=lambda i: (i.get("priority", 100), i["video_id"])):
            if platform not in item["platforms"]:
                continue
            rec = records.get(key(item["video_id"], platform))
            if rec and rec["state"] not in RETRYABLE:
                continue
            if rec and parse_time(rec.get("retry_at")) and parse_time(rec["retry_at"]) > now:
                continue
            if item.get("approval") != "approved" and not (preview and item.get("approval") == "held"):
                continue
            if not preview and (not item.get("reviewed_at") or not item.get("expires_at")):
                notes.append(f"{item['video_id']}: fresh review/expiry required")
                continue
            candidates.append(item)
        used = set()
        day = earliest.astimezone(zone).date()
        while day <= end.astimezone(zone).date() and capacity > 0:
            kinds = [cat for _, cat in known_categories[day]]
            clocks = clocks_for(profile, day, target)
            slots = [at_local(day, clock, profile.get("timezone", settings["timezone"])) for clock in clocks]
            slots = [t for t in slots if t and earliest <= t <= end]
            for idx, due in enumerate(slots):
                todays_events = [t for t in events.values() if t.astimezone(zone).date() == day]
                if len(todays_events) >= target:
                    break
                if any(abs((due-t).total_seconds()) < settings["minimum_gap_minutes"]*60 for t in events.values()):
                    continue
                if platform == "youtube" and any(abs((due-t).total_seconds()) < settings.get("short_long_gap_minutes",120)*60 for t in long_events):
                    notes.append(f"youtube: skip {iso(due)} to protect long-video spacing")
                    continue
                eligible = []
                for item in candidates:
                    if item["video_id"] in used:
                        continue
                    if parse_time(item.get("not_before")) and due < parse_time(item["not_before"]):
                        continue
                    if parse_time(item.get("expires_at")) and due > parse_time(item["expires_at"]):
                        continue
                    if item["category"] == "repo" and kinds.count("repo") >= settings["max_repo_videos_per_day"]:
                        continue
                    eligible.append(item)
                missing = set(settings.get("required_daily_categories", [])) - set(kinds)
                available = {i["category"] for i in eligible}
                free_slots = sum(not any(abs((t-b).total_seconds()) < settings["minimum_gap_minutes"]*60 for b in events.values()) for t in slots[idx:])
                if not pilot and (missing - available or len(missing) > min(free_slots, target-len(todays_events))):
                    notes.append(f"{platform} {day}: await sufficient news/tool mix; no repo-only dump")
                    break
                preferred = [cat for cat in ("news", "tool") if cat in missing] + ["repo", "tool", "news"]
                eligible.sort(key=lambda i: (preferred.index(i["category"]), i.get("priority", 100)))
                if not eligible:
                    break
                item = eligible[0]
                row = {"video_id": item["video_id"], "platform": platform, "category": item["category"],
                       "due_at": iso(due), "due_local": due.astimezone(zone).isoformat(),
                       "schedule_timezone": profile.get("timezone", settings["timezone"]),
                       "media_url": media_url(item, cfg), "payload": copy_rules.payload_for(item, platform, due, cfg)}
                rows.append(row)
                used.add(item["video_id"])
                events["plan:" + item["video_id"]] = due
                kinds.append(item["category"])
                capacity -= 1
                if capacity <= 0:
                    break
            day += dt.timedelta(days=1)
    # Every API mutation is paced separately; prioritise nearest publication times.
    rows.sort(key=lambda r: (r["due_at"], r["platform"], r["video_id"]))
    if len(rows) > settings["max_posts_per_run"]:
        rows = rows[:settings["max_posts_per_run"]]
        notes.append("Per-run mutation budget reached; excess remains in backlog")
    yt_events = {}
    for p in posts:
        if p["channelId"] == cfg["buffer"]["channels"]["youtube"]["buffer_id"] and p["status"] in PENDING | TERMINAL:
            if (p.get("metadata") or {}).get("notifySubscribers", True):
                t = parse_time(p.get("dueAt") or p.get("sentAt"))
                if t:
                    yt_events[p["id"]] = t
    for k, r in records.items():
        if r.get("platform") == "youtube" and r["state"] not in RETRYABLE and _time(r):
            rid = r.get("buffer_post_id") or "journal:" + k
            if r.get("notify_subscribers", True):
                yt_events[rid] = _time(r)
            else:
                yt_events.pop(rid, None)
    for row in rows:
        if row["platform"] == "youtube":
            due = parse_time(row["due_at"])
            notify = can_notify(due, yt_events.values(), settings.get("youtube_short_notifications_per_24h", 2))
            notify &= can_notify(due, list(yt_events.values()) + long_events, 3)
            row["payload"].setdefault("metadata", {}).setdefault("youtube", {})["notifySubscribers"] = bool(notify)
            if notify:
                yt_events["plan:" + row["video_id"]] = due
    if not cfg["buffer"].get("capabilities", {}).get("facebook_ai_generated", False):
        notes.append("Facebook included by owner instruction; caption disclosure used. Native AI flag remains unsupported; no compliance-equivalence claim.")
    return rows, sorted(set(notes))
