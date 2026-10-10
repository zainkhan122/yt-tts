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
    # Preserve the explicit manual-upload provenance even if Buffer backfills it.
    state = "published_manual" if record.get("state") == "published_manual" and post["status"] == "sent" else post["status"]
    if state == "error":
        state = "delivery_error"
    record.update(state=state, buffer_post_id=post["id"], external_url=post.get("externalLink"),
                  due_at=post.get("dueAt"), sent_at=post.get("sentAt") or record.get("sent_at"),
                  updated_at=iso(now))
    if state in {"draft", "needs_approval"}:
        record["state"] = "approval_required"
        record["last_error"] = "Buffer did not schedule this post automatically; review draft/approval policy"
    if post.get("error"):
        record["last_error"] = redact(post["error"]["message"])
        record["help_url"] = post["error"].get("supportUrl")
    if post.get("schedulingType") == "notification" and state not in TERMINAL:
        record["state"] = "notification_required"
        record["last_error"] = "Buffer returned reminder publishing; automatic posting was requested"
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
        if parse_time(row["due_at"]) < clock() + dt.timedelta(minutes=15):
            outcomes.append({"key": k, "state": "deferred_stale_slot"})
            continue
        item = by_video[row["video_id"]]
        record = {"video_id": row["video_id"], "platform": row["platform"], "category": row["category"],
                  "channel_id": row["payload"]["channelId"], "state": "submitting", "due_at": row["due_at"],
                  "media_url": row["media_url"], "media_ref": {n: item.get(n) for n in MEDIA_KEYS},
                  "text": row["payload"]["text"], "title": item["title"],
                  "payload_sha256": fingerprint(row["payload"]), "attempts": previous.get("attempts", 0) + 1,
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


def summary(report):
    lines = ["# Hypeless delivery", "", f"**Mode:** {report['mode']} · **Buffer writes:** {report.get('created', 0)}", "",
             "| Video | Platform | Planned local time |", "|---|---|---|"]
    for row in report.get("plan", []):
        lines.append(f"| {row['video_id']} | {row['platform']} | {row['due_local']} |")
    if not report.get("plan"):
        lines.append("| No eligible posts | — | — |")
    lines += ["", "## Notes"] + ["- " + n for n in report.get("notes", [])]
    lines += ["", "## Delivery issues"] + [f"- {r['key']}: {r['state']} — {r.get('error', '')}" for r in report.get("issues", [])]
    lines += ["", "Dry-run schedules are proposals only. Scheduled is NOT the same as successfully published.",
              "Instagram native AI disclosure is supported; Facebook currently gets a caption disclosure, not a native AI-info flag."]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("video_ids", nargs="*")
    modes = ap.add_mutually_exclusive_group()
    modes.add_argument("--dry-run", action="store_true")
    modes.add_argument("--live", action="store_true")
    modes.add_argument("--reconcile-only", action="store_true")
    ap.add_argument("--pilot", action="store_true", help="one explicitly selected video; bypass daily mix only for this pilot")
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
    if args.pilot and len(items) != 1:
        raise SystemExit("Pilot mode requires exactly one video ID")
    dry = not (args.live or args.reconcile_only)
    mode = "dry-run" if dry else ("reconcile-only" if args.reconcile_only else "live")
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
            channels, posts = client.state()
            reconcile(journal.records, all_items, posts, cfg, now)
            if not dry:
                journal.data["cooldown_until"] = None
                journal.save("reconcile delivery status")
            if not args.reconcile_only:
                rows, notes = plan(items, journal.records, channels, posts, cfg, now, preview=dry, pilot=args.pilot)
                report["plan"], report["notes"] = rows, notes
                if dry:
                    report["notes"].insert(0, "Posting disabled during setup; held videos are included only for preview")
                selected = {r["video_id"] for r in rows}
                if args.verify_media or args.live:
                    verify_site(cfg, [i for i in items if i["video_id"] in selected])
                if args.live:
                    outcomes = deliver(rows, items, journal, client, cfg)
                    report["outcomes"] = outcomes
                    report["created"] = sum(1 for o in outcomes if o.get("buffer_post_id"))
            report["request_count"] = client.request_count
            report["rate_limits"] = client.policies
            for k, rec in journal.records.items():
                if rec["state"] not in TERMINAL | PENDING | RETRYABLE:
                    report["issues"].append({"key": k, "state": rec["state"], "error": rec.get("last_error", "")})
            for platform, expected in cfg["buffer"]["channels"].items():
                problem = channel_problem(next((c for c in channels if c["id"] == expected["buffer_id"]), None), expected)
                if problem:
                    report["issues"].append({"key": platform, "state": "channel_blocked", "error": problem})
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
