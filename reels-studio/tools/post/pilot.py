"""One explicitly authorised immediate pilot, never an immediate batch.

Ordinary delivery continues to use the researched calendar. This startup pilot
proves actual cross-platform delivery before enabling routine scheduling.
"""
import datetime as dt
from zoneinfo import ZoneInfo

from tools.post.common import PENDING, RETRYABLE, TERMINAL, iso, key, media_url, parse_time
from tools.post.planner import channel_problem, payload_for


def immediate_plan(items, records, channels, posts, cfg, now, preview=False):
    if len(items) != 1:
        raise ValueError("Immediate pilot requires exactly one selected video")
    item = items[0]
    if not preview and item.get("approval") != "approved":
        raise ValueError("Immediate pilot is not approved")
    if not item.get("reviewed_at") or not parse_time(item.get("expires_at")) or parse_time(item["expires_at"]) <= now:
        raise ValueError("Immediate pilot needs a current fact/copy review")
    if parse_time(item.get("not_before")) and now < parse_time(item["not_before"]):
        raise ValueError("Immediate pilot would violate not_before")
    cmap = {c["id"]:c for c in channels}
    rows, notes = [], []
    for platform in item["platforms"]:
        expected = cfg["buffer"]["channels"][platform]
        problem = channel_problem(cmap.get(expected["buffer_id"]), expected)
        if problem or not expected.get("enabled") or expected.get("posting_hold"):
            raise ValueError(f"{platform}: immediate pilot blocked by channel health/policy")
        existing = records.get(key(item["video_id"],platform))
        if existing and existing["state"] not in RETRYABLE:
            notes.append(platform+": existing receipt/reservation; never recreate")
            continue
        if existing and parse_time(existing.get("retry_at")) and parse_time(existing["retry_at"])>now:
            notes.append(platform+": retry cooldown active")
            continue
        zone = ZoneInfo(cfg["schedule"]["profiles"][platform].get("timezone",cfg["schedule"]["timezone"]))
        events,pending={},set()
        for p in posts:
            if p["channelId"]!=expected["buffer_id"]:
                continue
            if p["status"] in PENDING:
                pending.add(p["id"])
            if p["status"] in PENDING | TERMINAL:
                t=parse_time(p.get("sentAt") or p.get("dueAt"))
                if t:events[p["id"]]=t
        for k,r in records.items():
            if r.get("platform")!=platform or r["state"] in RETRYABLE:
                continue
            rid=r.get("buffer_post_id") or "journal:"+k
            t=parse_time(r.get("sent_at") or r.get("due_at"))
            if t:events[rid]=t
            if r["state"] not in TERMINAL:pending.add(rid)
        if len(pending)>=min(cfg["buffer"]["queue_target_per_channel"],cfg["buffer"]["queue_limit_per_channel"]):
            raise ValueError(platform+": no pending capacity for the pilot")
        if sum(t.astimezone(zone).date()==now.astimezone(zone).date() for t in events.values())>=cfg["schedule"].get("daily_target",3):
            raise ValueError(platform+": daily posting target already reached")
        if any(abs((now-t).total_seconds()) < cfg["schedule"]["minimum_gap_minutes"]*60 for t in events.values()):
            raise ValueError(platform+": immediate pilot conflicts with recent/upcoming posts")
        if item["category"] == "repo" and any(r.get("platform")==platform and r.get("category")=="repo" and
                parse_time(r.get("sent_at") or r.get("due_at")) and parse_time(r.get("sent_at") or r.get("due_at")).astimezone(zone).date()==now.astimezone(zone).date()
                for r in records.values()):
            raise ValueError(platform+": repository daily limit reached")
        payload=payload_for(item,platform,now,cfg)
        payload["mode"]="shareNow"
        payload.pop("dueAt",None)
        rows.append({"video_id":item["video_id"],"platform":platform,"category":item["category"],"due_at":iso(now),
                     "due_local":now.astimezone(zone).isoformat(),"media_url":media_url(item,cfg),"payload":payload})
    notes.append("Owner-authorised single immediate pilot; all later videos use the normal paced calendar")
    return rows,notes
