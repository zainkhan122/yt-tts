"""Pure scheduling/copy functions: capacity, calendar pacing, daily mix and dedupe."""
import datetime as dt
from collections import defaultdict
from zoneinfo import ZoneInfo

from tools.post.common import (ROOT, PENDING, RETRYABLE, TERMINAL, fingerprint, iso,
                               key, load_json, media_url, parse_time)


def channel_problem(channel, expected):
    if not channel:
        return "channel missing"
    if channel.get("serviceId") != expected["service_id"]:
        return "social account identity changed"
    for field in ("isDisconnected", "isLocked", "isQueuePaused"):
        if channel.get(field):
            return field
    if (channel.get("metadata") or {}).get("defaultToReminders"):
        return "notification-only channel; automatic publishing required"
    return None


def copy_for(item, platform, cfg):
    b = load_json(ROOT / "briefs" / (item["video_id"] + ".json"))
    if item.get("brief_sha256") and fingerprint(b) != item["brief_sha256"]:
        raise ValueError(f"{item['video_id']}: brief changed since queue review; re-pin and re-approve")
    seo = b["seo"][platform]
    text = seo["description" if platform == "youtube" else "caption"].strip()
    credits = (b.get("credits_on_screen") or "").strip()
    if credits and credits.casefold() not in text.casefold():
        text += "\n\nCredits: " + credits
    if platform == "facebook":
        text += "\n\n" + cfg["disclosure"]["facebook_caption"]
    tags = seo.get("hashtags", [])
    if tags:
        text += "\n\n" + " ".join(tags)
    maximum = {"youtube": 5000, "instagram": 2200, "facebook": 5000}[platform]
    if len(text) > maximum:
        raise ValueError(f"{item['video_id']}: {platform} caption exceeds {maximum} characters")
    return text, b


def payload_for(item, platform, due, cfg):
    text, brief = copy_for(item, platform, cfg)
    meta = {}
    if platform == "youtube":
        title = brief["seo"]["youtube"]["title"]
        if not title or len(title) > 100:
            raise ValueError("YouTube title must be 1–100 characters")
        meta = {"title": title, "categoryId": "28", "privacy": "public", "madeForKids": False,
                "isAiGenerated": item.get("youtube_ai_generated", cfg["disclosure"]["youtube_ai_generated"]),
                "license": "youtube", "embeddable": True, "notifySubscribers": True}
    elif platform == "instagram":
        meta = {"type": "reel", "shouldShareToFeed": True,
                "isAiGenerated": cfg["disclosure"]["instagram_ai_generated"]}
    else:
        meta = {"type": "reel"}
    video = {"url": media_url(item, cfg)}
    if platform == "instagram":
        video["metadata"] = {"thumbnailOffset": 1000}
    return {"channelId": cfg["buffer"]["channels"][platform]["buffer_id"], "text": text,
            "schedulingType": "automatic", "mode": "customScheduled", "dueAt": iso(due),
            "saveToDraft": False, "needsApproval": False, "aiAssisted": True,
            "assets": [{"video": video}], "metadata": {platform: meta}}


def plan(items, records, channels, remote_posts, cfg, now, preview=False, pilot=False):
    settings = cfg["schedule"]
    zone = ZoneInfo(settings["timezone"])
    earliest = now + dt.timedelta(minutes=settings["minimum_lead_minutes"])
    end = now + dt.timedelta(hours=settings["lookahead_hours"])
    cmap = {c["id"]: c for c in channels}
    by_platform = cfg["buffer"]["channels"]
    by_video = {i["video_id"]: i for i in items}
    notes, result, used = [], [], set()
    for platform, expected in by_platform.items():
        problem = channel_problem(cmap.get(expected["buffer_id"]), expected)
        if problem:
            notes.append(f"{platform}: blocked — {problem}")
        if expected.get("posting_hold"):
            notes.append(f"{platform}: policy hold — {expected['posting_hold']}")
    busy = defaultdict(set)
    pending = defaultdict(set)
    daily_videos = defaultdict(set)
    booked_slots = {}
    # Include platform posts created outside this integration, too.
    channel_to_platform = {v["buffer_id"]: k for k, v in by_platform.items()}
    for post in remote_posts:
        platform = channel_to_platform.get(post["channelId"])
        if not platform:
            continue
        if post["status"] in PENDING:
            pending[platform].add(post["id"])
        t = parse_time(post.get("sentAt") if post["status"] == "sent" else post.get("dueAt"))
        t = t or parse_time(post.get("dueAt"))
        if t and post["status"] in PENDING | TERMINAL:
            busy[platform].add(t)
    remote_ids = {p["id"] for p in remote_posts}
    for k, record in records.items():
        platform = record["platform"]
        t = parse_time(record.get("sent_at") or record.get("due_at"))
        if t and record["state"] not in RETRYABLE:
            busy[platform].add(t)
            daily_videos[t.astimezone(zone).date()].add(record["video_id"])
            due = parse_time(record.get("due_at"))
            if due:
                base = due - dt.timedelta(minutes=settings["platform_offset_minutes"].get(platform, 0))
                prior = booked_slots.get(base)
                booked_slots[base] = record["video_id"] if prior in (None, record["video_id"]) else "__conflict__"
        if record["state"] not in TERMINAL | RETRYABLE and record.get("buffer_post_id") not in remote_ids:
            pending[platform].add("journal:" + k)
    candidates = []
    for item in sorted(items, key=lambda i: (i.get("priority", 100), i["video_id"])):
        if item.get("approval") != "approved" and not (preview and item.get("approval") == "held"):
            notes.append(f"{item['video_id']}: held for posting approval")
            continue
        if not preview and (not item.get("reviewed_at") or not item.get("expires_at")):
            notes.append(f"{item['video_id']}: missing dated fact/copy review and expiry")
            continue
        expires = parse_time(item.get("expires_at"))
        if expires and expires <= earliest:
            notes.append(f"{item['video_id']}: review expired; re-verify facts")
            continue
        candidates.append(item)

    def eligible(item, platform, due):
        expected = by_platform.get(platform)
        if not expected or not expected.get("enabled") or expected.get("posting_hold"):
            return False
        if channel_problem(cmap.get(expected["buffer_id"]), expected):
            return False
        rec = records.get(key(item["video_id"], platform))
        if rec:
            if rec["state"] not in RETRYABLE:
                return False
            if rec.get("retry_at") and parse_time(rec["retry_at"]) > now:
                return False
        if len(pending[platform]) >= min(cfg["buffer"]["queue_target_per_channel"], cfg["buffer"]["queue_limit_per_channel"]):
            return False
        expires = parse_time(item.get("expires_at"))
        if expires and due > expires:
            return False
        not_before = parse_time(item.get("not_before"))
        if not_before and due < not_before:
            return False
        same_day = [t for t in busy[platform] if t.astimezone(zone).date() == due.astimezone(zone).date()]
        if len(same_day) >= settings["max_videos_per_day"]:
            return False
        if any(abs((due - t).total_seconds()) < settings["minimum_gap_minutes"] * 60 for t in busy[platform]):
            return False
        return True

    day = earliest.astimezone(zone).date()
    while day <= end.astimezone(zone).date():
        kinds = [by_video.get(v, {"category": "repo" if v.startswith("repo-") else "unknown"})["category"] for v in daily_videos[day]]
        remaining_categories = {i["category"] for i in candidates if i["video_id"] not in used and
            any(not records.get(key(i["video_id"], p)) or records[key(i["video_id"], p)]["state"] in RETRYABLE for p in i["platforms"])}
        missing = set(settings.get("required_daily_categories", [])) - set(kinds) - remaining_categories
        if missing and not pilot:
            notes.append(f"{day}: backlog needs {' + '.join(sorted(missing))}; hold rather than publish a repo-only day")
            day += dt.timedelta(days=1)
            continue
        for clock in settings["slots"]:
            hour, minute = map(int, clock.split(":"))
            base = dt.datetime.combine(day, dt.time(hour, minute), tzinfo=zone).astimezone(dt.timezone.utc)
            booked = booked_slots.get(base)
            if base < earliest or base > end or (not booked and len(daily_videos[day]) >= settings["max_videos_per_day"]):
                continue
            priority_kinds = [k for k in ("news", "tool") if k not in kinds] + ["repo", "tool", "news"]
            choices = sorted(candidates, key=lambda i: (priority_kinds.index(i["category"]), i.get("priority", 100)))
            if booked:
                choices = [i for i in choices if i["video_id"] == booked]
            for item in choices:
                if item["video_id"] in used:
                    continue
                if item["video_id"] not in daily_videos[day] and item["category"] == "repo" and kinds.count("repo") >= settings["max_repo_videos_per_day"]:
                    continue
                rows = []
                for platform in item["platforms"]:
                    due = base + dt.timedelta(minutes=settings["platform_offset_minutes"].get(platform, 0))
                    if due <= end and eligible(item, platform, due):
                        rows.append({"video_id": item["video_id"], "platform": platform, "category": item["category"],
                                     "due_at": iso(due), "due_local": due.astimezone(zone).isoformat(),
                                     "media_url": media_url(item, cfg), "payload": payload_for(item, platform, due, cfg)})
                if not rows:
                    continue
                if len(result) + len(rows) > settings["max_posts_per_run"]:
                    notes.append("Per-run mutation budget reached; remainder stays in our backlog")
                    return result, sorted(set(notes))
                result.extend(rows)
                used.add(item["video_id"])
                if item["video_id"] not in daily_videos[day]:
                    kinds.append(item["category"])
                daily_videos[day].add(item["video_id"])
                booked_slots[base] = item["video_id"]
                for row in rows:
                    busy[row["platform"]].add(parse_time(row["due_at"]))
                    pending[row["platform"]].add("planned:" + item["video_id"])
                break
        day += dt.timedelta(days=1)
    return result, sorted(set(notes))
