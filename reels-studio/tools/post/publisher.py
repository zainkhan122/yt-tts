#!/usr/bin/env python3
"""Paced Buffer delivery. Default is READ-ONLY dry-run; --live is cloud-only.

  python3 reels.py post --dry-run
  python3 reels.py post news-claude-free-01 --dry-run --pilot
  post.yml -> --live (requires enabled config + explicitly approved queue entries)
  post.yml -> --reconcile-only (no Buffer mutations, updates delivery receipts)
"""
import argparse
import copy
import datetime as dt
import os
from pathlib import Path
import re
import sys

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from lib.secrets import redact
from tools.post.buffer_api import AmbiguousResult, BufferClient, BufferError, Deferred
from tools.post.common import (PENDING, RETRYABLE, TERMINAL, UNCERTAIN, config, fingerprint,
                               iso, key, media_url, now_utc, parse_time, queue, save_json)
from tools.post.media import verify_site
from tools.post.planner import channel_problem, copy_for, plan
from tools.post.state import Journal

MEDIA_KEYS = ("video_id", "asset_id", "asset_size", "asset_digest", "kit_asset_id", "kit_digest", "media_path", "release_tag")


def normalized_title(value):
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def matches(post, record):
    if post["channelId"] != record["channel_id"]:
        return False
    asset_match = any(a.get("source") == record.get("media_url") for a in post.get("assets", []))
    text_match = bool(record.get("text")) and post.get("text", "").strip() == record["text"].strip()
    title = (post.get("metadata") or {}).get("title")
    title_match = bool(title and record.get("title")) and normalized_title(title) == normalized_title(record["title"])
    return asset_match or text_match or title_match


def adopt(record, post, now):
    before = {k: v for k, v in record.items() if k != "updated_at"}
    # Preserve the explicit manual-upload provenance even if Buffer backfills it.
    state = "published_manual" if record.get("state") == "published_manual" and post["status"] == "sent" else post["status"]
    if state == "error":
        state = "delivery_error"
    record.update(state=state, buffer_post_id=post["id"], external_url=post.get("externalLink"),
                  due_at=post.get("dueAt"), sent_at=post.get("sentAt") or record.get("sent_at"))
    if state in {"draft", "needs_approval"}:
        record["state"] = "approval_required"
        record["last_error"] = "Buffer did not schedule this post automatically; review draft/approval policy"
    if post.get("error"):
        record["last_error"] = redact(post["error"]["message"])
        record["help_url"] = post["error"].get("supportUrl")
    if post.get("schedulingType") == "notification" and state not in TERMINAL:
        record["state"] = "notification_required"
        record["last_error"] = "Buffer returned reminder publishing; automatic posting was requested"
    if before != {k: v for k, v in record.items() if k != "updated_at"}:
        record["updated_at"] = iso(now)
    return record


def reconcile(records, items, posts, cfg, now):
    """Recover receipts, backfilled manual posts, and lost create responses. No writes."""
    by_id = {p["id"]: p for p in posts}
    for record in records.values():
        pid = record.get("buffer_post_id")
        if pid and pid in by_id:
            adopt(record, by_id[pid], now)
        elif record["state"] in UNCERTAIN:
            found = [p for p in posts if matches(p, record)]
            if len(found) == 1:
                adopt(record, found[0], now)
            else:
                record["state"] = "uncertain"
                record["last_error"] = "No unique Buffer receipt; no automatic recreate. Inspect Buffer before resolving."
        elif pid and record["state"] in PENDING:
            # Never assume a missing/removed post means it is safe to duplicate.
            record["state"] = "uncertain"
            record["last_error"] = "Known Buffer post absent from complete active/recent scan; inspect its ID"
    for item in items:
        for platform in item["platforms"]:
            k = key(item["video_id"], platform)
            if k in records and records[k]["state"] not in RETRYABLE:
                continue
            text, brief = copy_for(item, platform, cfg)
            probe = {"video_id": item["video_id"], "platform": platform,
                     "channel_id": cfg["buffer"]["channels"][platform]["buffer_id"],
                     "media_url": media_url(item, cfg), "text": text,
                     "title": brief["seo"]["youtube"]["title"]}
            found = [p for p in posts if matches(p, probe)]
            if len(found) == 1:
                probe["source"] = "Buffer history reconciliation; no createPost sent"
                records[k] = adopt(probe, found[0], now)
            elif len(found) > 1:
                records[k] = {**probe, "state": "duplicate_conflict", "last_error": "Multiple matching Buffer posts; inspect, do not create another", "updated_at": iso(now)}
    return records


def deliver(rows, items, journal, client, cfg, clock=now_utc):
    """Write-ahead per post, persist result immediately. Never bulk-fire mutations."""
    outcomes = []
    by_video = {i["video_id"]: i for i in items}
    immediate = [r for r in rows if r["payload"].get("mode") == "shareNow"]
    if immediate and (not cfg.get("_authorised_immediate_pilot") or len({r["video_id"] for r in rows}) != 1 or len({r["platform"] for r in rows}) != len(rows)):
        raise ValueError("Immediate publication requires an explicitly authorised single-video pilot")
    for row in rows:
        k = key(row["video_id"], row["platform"])
        if cfg["buffer"]["channels"][row["platform"]].get("posting_hold"):
            outcomes.append({"key": k, "state": "policy_held"})
            continue
        previous = journal.records.get(k, {})
        if previous and previous["state"] not in RETRYABLE:
            outcomes.append({"key": k, "state": "skipped_duplicate"})
            continue
        if previous.get("attempts", 0) >= cfg["buffer"]["max_attempts"]:
            previous["state"] = "dead_letter"
            previous["last_error"] = "Automatic attempt budget exhausted; explicit review required"
            journal.save("retry budget exhausted for " + k)
            outcomes.append({"key": k, "state": "dead_letter"})
            continue
        # Long-running batches must not accidentally turn old timestamps into 'post now'.
        if row["payload"].get("mode") != "shareNow" and parse_time(row["due_at"]) < clock() + dt.timedelta(minutes=15):
            outcomes.append({"key": k, "state": "deferred_stale_slot"})
            continue
        item = by_video[row["video_id"]]
        record = {"video_id": row["video_id"], "platform": row["platform"], "category": row["category"],
                  "channel_id": row["payload"]["channelId"], "state": "submitting", "due_at": row["due_at"],
                  "media_url": row["media_url"], "media_ref": {n: item.get(n) for n in MEDIA_KEYS},
                  "text": row["payload"]["text"], "title": item["title"],
                  "payload_sha256": fingerprint(row["payload"]), "attempts": previous.get("attempts", 0) + 1,
                  "notify_subscribers": row["payload"].get("metadata", {}).get("youtube", {}).get("notifySubscribers", False),
                  "updated_at": iso(clock())}
        journal.records[k] = record
        journal.save("reserve " + k)  # If persistence fails, createPost is never called.
        stop = False
        try:
            post = client.create(row["payload"])
            adopt(record, post, clock())
        except Deferred as exc:
            record.update(state="retry_wait", retry_at=iso(clock() + dt.timedelta(seconds=max(exc.wait_seconds, 300))),
                          last_error=str(exc), error_code=exc.code)
            if exc.code != "POSTING_LIMIT":
                journal.data["cooldown_until"] = record["retry_at"]
            stop = True
        except AmbiguousResult as exc:
            record.update(state="uncertain", last_error=str(exc), error_code=exc.code)
            stop = True
        except BufferError as exc:
            record.update(state="blocked", last_error=str(exc), error_code=exc.code)
            stop = exc.code in {"AUTH", "UnauthorizedError"}
        journal.save("receipt " + k + " " + record["state"])
        outcomes.append({"key": k, "state": record["state"], "buffer_post_id": record.get("buffer_post_id"), "error": record.get("last_error")})
        print(f"{k}: {record['state']}", flush=True)
        if stop:
            break
    return outcomes


def inventory(channels, posts, records, cfg, items, now):
    """Read-only proof of what this token can see: org, channels, posts, journal drift."""
    channel_by_id = {c["id"]: c for c in channels}
    configured = {name: c["buffer_id"] for name, c in cfg["buffer"]["channels"].items()}
    out = {"generated_at": iso(now), "organization_id": cfg["buffer"]["organization_id"],
           "channels": [], "posts": [], "missing_channels": [], "journal": []}
    for channel in channels:
        row = {k: channel.get(k) for k in ("id", "name", "service", "serviceId", "externalLink",
                                           "timezone", "isDisconnected", "isLocked", "isQueuePaused")}
        row["configured_as"] = next((n for n, cid in configured.items() if cid == channel["id"]), None)
        out["channels"].append(row)
    seen = {c["id"] for c in channels}
    out["missing_channels"] = [{"platform": n, "buffer_id": cid} for n, cid in configured.items() if cid not in seen]
    live = {p["id"]: p for p in posts}
    for post in posts:
        channel = channel_by_id.get(post.get("channelId"), {})
        out["posts"].append({"id": post["id"], "channel": channel.get("name"), "service": channel.get("service"),
                             "status": post.get("status"), "dueAt": post.get("dueAt"),
                             "sentAt": post.get("sentAt"), "externalLink": post.get("externalLink"),
                             "schedulingType": post.get("schedulingType"),
                             "error": redact(((post.get("error") or {}).get("message") or "")) or None,
                             "assets": [a.get("source") for a in (post.get("assets") or [])],
                             "text": (post.get("text") or "")[:90]})
    queued = {i["video_id"] for i in items}
    for k, rec in records.items():
        found = live.get(rec.get("buffer_post_id"))
        out["journal"].append({"key": k, "in_queue": rec.get("video_id") in queued,
                               "journal_state": rec.get("state"),
                               "buffer_post_id": rec.get("buffer_post_id"),
                               "journal_due_at": rec.get("due_at"),
                               "live_present": bool(found), "live_status": (found or {}).get("status"),
                               "live_due_at": (found or {}).get("dueAt")})
    return out


def local_time(value, zone="Asia/Karachi"):
    """Owner-facing time; the report never asks anyone to convert UTC in their head."""
    moment = parse_time(value)
    if not moment:
        return "—"
    try:
        from zoneinfo import ZoneInfo
        return moment.astimezone(ZoneInfo(zone)).strftime("%Y-%m-%d %H:%M %Z")
    except Exception:
        return iso(moment)


def media_name(post):
    """Filename of the video Buffer holds; stable across re-pinned hosting URLs."""
    for asset in (post or {}).get("assets") or []:
        source = asset.get("source") or ""
        if source:
            return source.split("?")[0].rstrip("/").rsplit("/", 1)[-1]
    return None


def verify_plan(records, items, posts, cfg, now):
    """Read-back: prove Buffer holds exactly what the journal claims, or say what drifted.

    Creation receipts are not evidence. A post can be accepted by Buffer and then sit in
    draft, lose its scheduled time, point at stale media, or disappear. This compares the
    journal against a fresh scan and returns one row per platform plus every problem found.
    """
    by_id = {p["id"]: p for p in posts}
    rows, issues = [], []
    for item in items:
        expected_media = (item.get("media_path") or "").rsplit("/", 1)[-1] or None
        for platform in item["platforms"]:
            k = key(item["video_id"], platform)
            record = records.get(k)
            if not record:
                # Never scheduled is a planning fact, not drift; it must not mask real mismatches.
                rows.append({"key": k, "journal_state": None, "live_status": None,
                             "problem": None, "note": "no receipt; not scheduled yet"})
                continue
            live = by_id.get(record.get("buffer_post_id"))
            problem = None
            if record["state"] in TERMINAL:
                if not live and not record.get("external_url"):
                    problem = "terminal receipt without a Buffer post or public URL"
            elif record["state"] in PENDING:
                if not live:
                    problem = f"journal says {record['state']} but Buffer has no such post"
                elif live.get("status") in {"draft", "needs_approval"}:
                    problem = f"Buffer holds it as {live['status']}, not scheduled"
                elif live.get("status") == "error":
                    problem = "Buffer reported a delivery error: " + redact(((live.get("error") or {}).get("message") or ""))
                else:
                    want, got = parse_time(record.get("due_at")), parse_time(live.get("dueAt"))
                    if want and got and abs((want - got).total_seconds()) > 120:
                        problem = f"due time drifted: journal {iso(want)} vs Buffer {iso(got)}"
                    elif expected_media and media_name(live) and media_name(live) != expected_media:
                        problem = f"Buffer holds {media_name(live)} but queue pins {expected_media}"
            else:
                problem = f"unsettled delivery state {record['state']}"
            rows.append({"key": k, "journal_state": record["state"], "buffer_post_id": record.get("buffer_post_id"),
                         "journal_due_at": record.get("due_at"), "live_status": (live or {}).get("status"),
                         "live_due_at": (live or {}).get("dueAt"), "live_media": media_name(live),
                         "expected_media": expected_media, "problem": problem})
            if problem:
                issues.append({"key": k, "state": "drift", "error": problem})
    return rows, issues


def readback(records, keys, posts, now):
    """Adopt a fresh scan after createPost so 'scheduled' means Buffer agrees, not that we asked."""
    live = {p["id"]: p for p in posts}
    rows = []
    for k in keys:
        record = records[k]
        found = live.get(record.get("buffer_post_id"))
        if not found:
            record["state"] = "unverified_missing"
            record["last_error"] = "Create accepted but post absent from read-back scan"
            rows.append({"key": k, "journal_state": record["state"], "live_status": None,
                         "live_due_at": None, "live_media": None, "problem": record["last_error"]})
            continue
        adopt(record, found, now)
        record["verified_at"] = iso(now)
        rows.append({"key": k, "journal_state": record["state"], "live_status": found.get("status"),
                     "live_due_at": found.get("dueAt"), "live_media": media_name(found),
                     "problem": record.get("last_error")})
    return rows


def summary(report):
    lines = ["# Hypeless delivery", "", f"**Mode:** {report['mode']} · **Buffer writes:** {report.get('created', 0)}", "",
             "| Video | Platform | Planned local time |", "|---|---|---|"]
    for row in report.get("plan", []):
        lines.append(f"| {row['video_id']} | {row['platform']} | {row['due_local']} |")
    if not report.get("plan") and report.get("mode") in {"reconcile-only", "verify", "inventory"}:
        lines.append("| No new posts planned | — | — |")
    elif not report.get("plan"):
        lines.append("| No eligible posts | — | — |")
    if report.get("verification"):
        lines += ["", "## Read-back verification (independent of create responses)", "",
                  "| Receipt | Journal | Buffer status | Buffer due (UTC) | Media | Result |",
                  "|---|---|---|---|---|---|"]
        for row in report["verification"]:
            lines.append(f"| {row['key']} | {row.get('journal_state') or '—'} | {row.get('live_status') or '—'} | "
                         f"{row.get('live_due_at') or '—'} | {row.get('live_media') or '—'} | "
                         f"{('DRIFT: ' + row['problem']) if row.get('problem') else 'verified'} |")
    if report.get("inventory"):
        inv = report["inventory"]
        lines += ["", "## Buffer inventory (read-only)", "",
                  f"Organization: `{inv['organization_id']}`", "",
                  "| Channel | Service | Configured as | Disconnected | Locked | Paused |",
                  "|---|---|---|---|---|---|"]
        for c in inv["channels"]:
            lines.append(f"| {c['name']} ({c['id']}) | {c['service']} | {c.get('configured_as') or '—'} | "
                         f"{c.get('isDisconnected')} | {c.get('isLocked')} | {c.get('isQueuePaused')} |")
        missing = inv.get("missing_channels") or []
        if missing:
            lines += ["", "**Configured channel IDs absent from this token:** " +
                      ", ".join(f"{m['platform']}={m['buffer_id']}" for m in missing)]
        lines += ["", "| Post | Channel | Status | Scheduling | Due (UTC) | Due (PKT) | Media | Error |",
                  "|---|---|---|---|---|---|---|---|"]
        for p in inv["posts"]:
            media = "; ".join(a.rsplit("/", 1)[-1] for a in (p["assets"] or [])) or "—"
            lines.append(f"| {p['id']} | {p.get('channel')} | {p['status']} | {p.get('schedulingType') or '—'} | "
                         f"{p.get('dueAt') or '—'} | {local_time(p.get('dueAt'))} | {media} | {p.get('error') or '—'} |")
        if not inv["posts"]:
            lines.append("| No posts visible to this token | — | — | — | — | — | — | — |")
        lines += ["", "| Journal key | Queued | Journal state | Buffer ID | Live status | Live due (UTC) | Drift |", "|---|---|---|---|---|---|---|"]
        for j in inv["journal"]:
            drift = "MISSING from Buffer" if not j["live_present"] else ("state differs" if j["live_status"] != j["journal_state"] else "consistent")
            lines.append(f"| {j['key']} | {'yes' if j.get('in_queue') else 'no'} | {j['journal_state']} | {j['buffer_post_id'] or '—'} | "
                         f"{j['live_status'] or '—'} | {j['live_due_at'] or '—'} | {drift} |")
    lines += ["", "## Notes"] + ["- " + n for n in report.get("notes", [])]
    lines += ["", "## Delivery issues"] + [f"- {r['key']}: {r['state']} — {r.get('error', '')}" for r in report.get("issues", [])]
    lines += ["", "Dry-run schedules are proposals only. Scheduled is NOT the same as successfully published.",
              "Facebook is included per owner instruction; its caption disclosure does not assert that a native AI label was applied."]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("video_ids", nargs="*")
    modes = ap.add_mutually_exclusive_group()
    modes.add_argument("--dry-run", action="store_true")
    modes.add_argument("--live", action="store_true")
    modes.add_argument("--reconcile-only", action="store_true")
    modes.add_argument("--verify", action="store_true",
                       help="read-back check that Buffer holds the approved queue; exits non-zero on drift")
    modes.add_argument("--inventory", action="store_true",
                       help="read-only proof of visible Buffer organization/channels/posts and journal drift")
    ap.add_argument("--pilot", action="store_true", help="one explicitly selected video; bypass daily mix only for this pilot")
    ap.add_argument("--pilot-now", action="store_true", help="Owner-authorised single immediate pilot only; never a bulk posting mode")
    ap.add_argument("--verify-media", action="store_true")
    ap.add_argument("--report", default=str(ROOT / "renders/publishing/report.json"))
    args = ap.parse_args()
    cfg, all_items = config(), queue()
    now = now_utc()
    items = all_items
    if args.video_ids:
        unknown = set(args.video_ids) - {i["video_id"] for i in all_items}
        if unknown:
            raise SystemExit("Unknown queued video IDs: " + ", ".join(sorted(unknown)))
        items = [i for i in all_items if i["video_id"] in args.video_ids]
    if args.pilot_now and not args.pilot:
        raise SystemExit("--pilot-now requires --pilot and exactly one selected video")
    if args.pilot and len(items) != 1:
        raise SystemExit("Pilot mode requires exactly one video ID")
    dry = not (args.live or args.reconcile_only)
    mode = ("inventory" if args.inventory else "verify" if args.verify
            else "dry-run" if dry else ("reconcile-only" if args.reconcile_only else "live"))
    if args.inventory or args.verify:
        dry = True  # never persist a journal change from a diagnostic/verification run
    if not dry and os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("Journal-changing/live runs must use post.yml in GitHub Actions")
    if args.live and (not cfg.get("enabled") or os.environ.get("ALLOW_BUFFER_MUTATIONS") != "true"):
        raise SystemExit("Publishing disabled; owner approval + enabled config + explicit workflow live mode required")
    if args.live and not cfg.get("live_pilot_passed", False) and not args.pilot:
        raise SystemExit("Run and verify one live pilot before activating the daily queue")
    journal = Journal(cfg, remote=not dry)
    # Dry-run may simulate reconciliation, but must never persist even a local receipt.
    if dry:
        journal.data = copy.deepcopy(journal.data)
    report = {"generated_at": iso(now), "mode": mode, "created": 0, "plan": [], "notes": [], "issues": []}
    cooldown = parse_time(journal.data.get("cooldown_until"))
    exit_code = 0
    if cooldown and cooldown > now:
        report["notes"].append("API cooldown active until " + iso(cooldown) + "; no Buffer requests made")
    else:
        client = BufferClient(cfg["buffer"])
        try:
            if args.inventory:
                channels = client.channels()
                posts = client.state([c["id"] for c in channels])[1]
                report["inventory"] = inventory(channels, posts, journal.records, cfg, all_items, now)
                cfg["buffer"]["capabilities"] = client.capabilities
                report["capabilities"] = client.capabilities
                report["request_count"] = client.request_count
                report["rate_limits"] = client.policies
                save_json(args.report, report)
                md = summary(report)
                Path(args.report).with_suffix(".md").write_text(md, encoding="utf-8")
                if os.environ.get("GITHUB_STEP_SUMMARY"):
                    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
                        f.write(md)
                print(md)
                return 0
            if args.verify:
                approved = [i for i in items if i.get("approval") == "approved"]
                channels, posts = client.state()
                rows_v, issues_v = verify_plan(journal.records, approved, posts, cfg, now)
                report["verification"], report["issues"] = rows_v, issues_v
                report["request_count"] = client.request_count
                report["rate_limits"] = client.policies
                save_json(args.report, report)
                md = summary(report)
                Path(args.report).with_suffix(".md").write_text(md, encoding="utf-8")
                if os.environ.get("GITHUB_STEP_SUMMARY"):
                    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
                        f.write(md)
                print(md)
                print(f"verified {sum(1 for r in rows_v if not r.get('problem'))}/{len(rows_v)} receipts; {len(issues_v)} drift")
                return 1 if issues_v else 0
            channels, posts = client.state()
            cfg["buffer"]["capabilities"] = client.capabilities
            report["capabilities"] = client.capabilities
            reconcile(journal.records, all_items, posts, cfg, now)
            if not dry:
                journal.data["cooldown_until"] = None
                journal.save("reconcile delivery status")
            if args.reconcile_only:
                # Reconcile is also the owner-facing status check: prove the approved queue is live.
                approved = [i for i in items if i.get("approval") == "approved"]
                rows_v, issues_v = verify_plan(journal.records, approved, posts, cfg, now)
                report["verification"], report["issues"] = rows_v, issues_v
                if issues_v:
                    exit_code = 1
            if not args.reconcile_only:
                if args.pilot_now:
                    from tools.post.pilot import immediate_plan
                    cfg["_authorised_immediate_pilot"] = True
                    rows, notes = immediate_plan(items, journal.records, channels, posts, cfg, now, preview=dry)
                else:
                    rows, notes = plan(items, journal.records, channels, posts, cfg, now, preview=dry, pilot=args.pilot)
                report["plan"], report["notes"] = rows, notes
                if dry:
                    report["notes"].insert(0, "Read-only preview: no provider writes; held videos may be included for planning")
                selected = {r["video_id"] for r in rows}
                if args.verify_media or args.live:
                    verify_site(cfg, [i for i in items if i["video_id"] in selected])
                if args.live:
                    outcomes = deliver(rows, items, journal, client, cfg)
                    report["outcomes"] = outcomes
                    report["created"] = sum(1 for o in outcomes if o.get("buffer_post_id"))
                    touched = [o["key"] for o in outcomes if o.get("buffer_post_id")]
                    if touched:
                        # A create response is not proof. Re-scan and only then call it scheduled.
                        _, after = client.state()
                        report["verification"] = readback(journal.records, touched, after, now_utc())
                        journal.save("read-back verification")
                        if any(row.get("problem") for row in report["verification"]):
                            report["issues"] += [{"key": r["key"], "state": "drift", "error": r["problem"]}
                                                 for r in report["verification"] if r.get("problem")]
                            exit_code = 1
            report["request_count"] = client.request_count
            report["rate_limits"] = client.policies
            for k, rec in journal.records.items():
                if rec["state"] not in TERMINAL | PENDING | RETRYABLE:
                    report["issues"].append({"key": k, "state": rec["state"], "error": rec.get("last_error", "")})
            for platform, expected in cfg["buffer"]["channels"].items():
                problem = channel_problem(next((c for c in channels if c["id"] == expected["buffer_id"]), None), expected)
                if problem:
                    report["issues"].append({"key": platform, "state": "channel_blocked", "error": problem})
            report["receipts"] = [{"key": k, **{f:r.get(f) for f in ("state","buffer_post_id","external_url","sent_at","due_at")}} for k,r in journal.records.items()]
            if report["issues"]:
                exit_code = 1
        except Deferred as exc:
            until = iso(now_utc() + dt.timedelta(seconds=max(exc.wait_seconds, 300)))
            report["notes"].append(f"Deferred: {exc}; next permitted attempt {until}")
            if not dry:
                journal.data["cooldown_until"] = until
                journal.save("persist API cooldown")
        except (BufferError, ValueError, requests.RequestException) as exc:
            report["issues"].append({"key": "preflight", "state": "blocked", "error": redact(str(exc))})
            exit_code = 1
    save_json(args.report, report)
    md = summary(report)
    Path(args.report).with_suffix(".md").write_text(md, encoding="utf-8")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write(md)
    print(md)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
