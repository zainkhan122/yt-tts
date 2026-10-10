#!/usr/bin/env python3
"""Direct long-form YouTube delivery + metadata enrichment for Buffer Shorts.

Default: dry-run, no API mutation. Live modes require Actions, explicit approval,
OAuth, encrypted checkpoints and a successful pilot before unattended scheduling.
"""
import argparse
import copy
import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from lib.secrets import redact, youtube_credentials, youtube_state_key
from tools.post.common import config as root_config, fingerprint, iso, load_json, now_utc, parse_time, save_json, valid_id
from tools.post.state import Journal
from tools.youtube.api import Deferred, Uncertain, YouTubeAPI, YouTubeError
from tools.youtube.contracts import preflight, read_brief
from tools.youtube.metadata import enrich_short, get_video, playlists_for, set_thumbnail
from tools.youtube.resumable import reconcile_upload, tracking_tag, upload
from tools.youtube.schedule import plan
from tools.youtube.seo import validate as seo_validate

BLOCKED = {"duplicate_conflict", "blocked", "publication_failed"}
REMOTE_PATH = "reels-studio/tracker/youtube-publications.json"


def verify_publication(record, video, journal, clock=now_utc):
    status = video.get("status", {})
    if status.get("uploadStatus") in {"failed", "rejected", "deleted"}:
        record.update(state="publication_failed", last_error=status.get("rejectionReason") or status.get("failureReason") or status["uploadStatus"])
        journal.save("YouTube processing/delivery failure")
        return True
    if status.get("privacyStatus") == "public":
        record.update(state="sent", external_url="https://www.youtube.com/watch?v=" + video["id"],
                      sent_at=video["snippet"].get("publishedAt") or iso(clock()))
        record.pop("session_ciphertext", None)
        journal.save("confirmed YouTube public receipt " + record["video_id"])
        return True
    if status.get("publishAt"):
        due = parse_time(status["publishAt"])
        record["publish_at"] = iso(due)
        if clock() > due + dt.timedelta(minutes=15):
            record.update(state="publication_failed", last_error="Scheduled time passed but video is not public; inspect YouTube, do not re-upload")
        else:
            record["state"] = "scheduled"
        journal.save("reconcile YouTube schedule receipt")
        return True
    return False


def finish_private(item, record, media, api, journal, *, private_only=False, clock=now_utc):
    video = get_video(api, record["youtube_id"])
    if verify_publication(record, video, journal, clock):
        return
    status = video.get("status", {})
    processing = video.get("processingDetails", {}).get("processingStatus")
    if status.get("privacyStatus") != "private":
        raise YouTubeError("Video privacy changed outside the pipeline; review before scheduling", "PRIVACY_CHANGED")
    if processing in {"failed", "terminated"}:
        raise YouTubeError("YouTube processing failed; keep the existing video ID", "PROCESSING_FAILED")
    if status.get("uploadStatus") != "processed" and processing != "succeeded":
        record["state"] = "processing"
        journal.save("await YouTube processing")
        raise Deferred("Video still processing; it remains private", "PROCESSING", 900)
    desired = media["snippet"]
    if any(video["snippet"].get(k) != desired[k] for k in ("title", "description")):
        raise YouTubeError("Private video copy changed outside its approved brief; do not overwrite it", "COPY_CHANGED")
    if tracking_tag(item) not in video["snippet"].get("tags", []):
        raise YouTubeError("Upload correlation marker missing; inspect instead of duplicating", "MARKER_MISSING")
    set_thumbnail(api, record, media["thumbnail_path"], item["assets"]["thumbnail"]["digest"], journal)
    playlists_for(api, journal, record["youtube_id"], item["category"], "long")
    record.update(metadata_ready=True, state="private_ready")
    journal.save("private YouTube metadata ready")
    if private_only:
        return
    if not item.get("public_approved"):
        raise YouTubeError("Public release is not approved", "APPROVAL_REQUIRED")
    # Read back before arming. A successful thumbnail upload is not a visual review.
    video = get_video(api, record["youtube_id"])
    if verify_publication(record, video, journal, clock):
        return
    if video.get("contentDetails", {}).get("hasCustomThumbnail") is not True:
        raise Deferred("Custom thumbnail not yet confirmed by YouTube; remain private", "THUMBNAIL_PENDING", 900)
    due = parse_time(record.get("publish_at"))
    if not due or due < clock() + dt.timedelta(minutes=api.cfg["minimum_publish_lead_minutes"]):
        raise Deferred("Publication slot is stale/too close; plan a fresh slot, never publish now", "STALE_SLOT", 900)
    if parse_time(item.get("expires_at")) and due > parse_time(item["expires_at"]):
        raise YouTubeError("Fact review expires before publication", "EXPIRED_REVIEW")
    source = video.get("status", {})
    mutable = ("license", "embeddable", "publicStatsViewable", "selfDeclaredMadeForKids", "containsSyntheticMedia")
    scheduled_status = {k: source[k] for k in mutable if k in source}
    scheduled_status.update(privacyStatus="private", publishAt=iso(due), selfDeclaredMadeForKids=False,
                            containsSyntheticMedia=item.get("contains_synthetic_media", False))
    record["state"] = "scheduling"
    journal.save("reserve YouTube public schedule " + item["video_id"])
    response = api.json("PUT", "videos", params={"part": "status"}, body={"id": record["youtube_id"], "status": scheduled_status},
                        headers={"If-Match": video["etag"]} if video.get("etag") else {}, cost=50, idempotent=True)
    received = response.get("status", {})
    if received.get("privacyStatus") != "private" or parse_time(received.get("publishAt")) != due:
        raise Uncertain("YouTube did not return the intended schedule; reconcile existing ID", "SCHEDULE_RECEIPT")
    record.update(state="scheduled", scheduled_at=iso(clock()), external_url="https://www.youtube.com/watch?v=" + record["youtube_id"])
    journal.save("YouTube schedule accepted " + item["video_id"])


def process(item, planned, api, journal, root_cfg, work, uploads_playlist, private_only=False):
    record = journal.records.setdefault(item["video_id"], {"video_id": item["video_id"], "category": item["category"], "state": "queued", "attempts": 0})
    if record.get("state") in {"sent", "scheduled", "cancelled"} | BLOCKED:
        return record
    if parse_time(record.get("retry_at")) and parse_time(record["retry_at"]) > now_utc():
        return record
    if record.get("attempts", 0) >= api.cfg["max_attempts"]:
        record.update(state="blocked", last_error="Upload/metadata failure budget exhausted; agent review required")
        journal.save("YouTube retry budget exhausted")
        return record
    if planned and planned.get("publish_at"):
        record["publish_at"] = planned["publish_at"]
    if not record.get("youtube_id") and record.get("state") in {"session_start_uncertain", "upload_uncertain", "expired_uncertain"}:
        if not reconcile_upload(record, item, api, journal, uploads_playlist):
            raise Uncertain("Uncertain upload has no unique receipt; no new session", "RECONCILE_REQUIRED")
    try:
        media = preflight(item, root_cfg, api.cfg, work, need_video=not record.get("youtube_id"))
    except ValueError as exc:
        record.update(state="blocked", last_error=str(exc), error_code="MEDIA_PREFLIGHT")
        journal.save("block invalid long-form media")
        shutil.rmtree(work, ignore_errors=True)
        return record
    try:
        if not record.get("youtube_id"):
            # A new job is checked against recent owned uploads before its first create.
            if record["state"] == "queued":
                reconcile_upload(record, item, api, journal, uploads_playlist)
            if not record.get("youtube_id"):
                upload(item, record, media["video_path"], media["snippet"], api, journal)
        finish_private(item, record, media, api, journal, private_only=private_only)
        record.pop("retry_at", None)
        record.pop("last_error", None)
        journal.save("YouTube delivery checkpoint")
    except Deferred as exc:
        record.update(retry_at=iso(now_utc()+dt.timedelta(seconds=max(300, exc.wait_seconds))), last_error=str(exc), error_code=exc.code)
        # Processing and rate limits are not media-failure attempts.
        if exc.code in {"TRANSFER_RETRY", "NO_PROGRESS", "NETWORK", "SERVER"}:
            record["attempts"] = record.get("attempts", 0)+1
        if exc.code in {"RATE_LIMIT", "QUOTA_EXCEEDED", "QUOTA_BUDGET", "UPLOAD_BUDGET", "UPLOAD_LIMIT", "TOKEN_RATE"}:
            journal.data["cooldown_until"] = record["retry_at"]
        # A quota deferral before a session was accepted is safe to attempt later.
        if record.get("state") == "session_start_uncertain" and not record.get("session_ciphertext"):
            record["state"] = "queued"
        journal.save("defer YouTube operation " + exc.code)
    except Uncertain as exc:
        if not record.get("youtube_id") and not record.get("session_ciphertext"):
            record["state"] = "session_start_uncertain"
        elif not record.get("youtube_id"):
            record["state"] = "upload_uncertain" if exc.code == "MISSING_RECEIPT" else "uploading"
        record.update(last_error=str(exc), error_code=exc.code)
        journal.save("hold uncertain YouTube result")
    except YouTubeError as exc:
        if exc.code == "SESSION_EXPIRED":
            if not reconcile_upload(record, item, api, journal, uploads_playlist):
                record.update(state="expired_uncertain", last_error="Expired session; no unique receipt. Review before any restart.")
                journal.save("hold expired upload session")
        else:
            record.update(state="blocked", last_error=str(exc), error_code=exc.code)
            journal.save("block YouTube operation")
    finally:
        # MP4s never enter the repo or the workspace snapshot.
        shutil.rmtree(work, ignore_errors=True)
    return record


def external_id(url):
    match = re.search(r"(?:youtu\.be/|youtube\.com/(?:shorts/|watch\?v=))([A-Za-z0-9_-]{11})(?:[?&#/]|$)", url or "")
    return match[1] if match else None


def enrich_buffer_shorts(api, journal, shorts_records, short_items):
    if not api.cfg["metadata_enrichment"]["enabled"]:
        return []
    rows, count = [], 0
    queue_by_id = {i["video_id"]: i for i in short_items}
    for source in shorts_records.values():
        if source.get("platform") != "youtube" or source.get("state") not in {"sent", "published_manual"}:
            continue
        if source["state"] == "published_manual" and not api.cfg["metadata_enrichment"]["include_manual_uploads"]:
            continue
        vid = external_id(source.get("external_url"))
        if not vid or journal.data.get("enrichment", {}).get(vid, {}).get("state") == "done":
            continue
        item = queue_by_id.get(source["video_id"])
        if not item:
            continue
        brief = load_json(ROOT/"briefs"/(source["video_id"]+".json"))
        if fingerprint(brief) != item["brief_sha256"]:
            raise ValueError("Shorts metadata changed after approval; review instead of silently overwriting")
        snippet = seo_validate(brief, "short")
        rows.append(enrich_short(api, journal, {**source, "youtube_id": vid}, snippet["tags"], item["category"]))
        count += 1
        if count >= api.cfg["metadata_enrichment"]["max_videos_per_run"]:
            break
    return rows


def reconcile_known(api, journal):
    records = [r for r in journal.records.values() if r.get("youtube_id") and r.get("state") not in {"sent", "cancelled"}]
    for start in range(0, len(records), 50):
        batch = records[start:start+50]
        videos = api.json("GET", "videos", params={"part": "snippet,status,processingDetails", "id": ",".join(r["youtube_id"] for r in batch)}).get("items", [])
        by_id = {v["id"]: v for v in videos}
        for r in batch:
            if r["youtube_id"] not in by_id:
                r.update(state="blocked", last_error="Known video is absent; do not re-upload a possibly deleted/private video")
                journal.save("known YouTube receipt absent")
            elif by_id[r["youtube_id"]]["snippet"]["channelId"] != api.cfg["channel_id"]:
                raise YouTubeError("Receipt channel mismatch", "CHANNEL_MISMATCH")
            else:
                verify_publication(r, by_id[r["youtube_id"]], journal)


def oauth_expiry_notice(credentials):
    expiry = (credentials or {}).get("refresh_token_expires_at")
    if not expiry:
        return None
    stamp = iso(dt.datetime.fromtimestamp(expiry, dt.timezone.utc))
    return "Google offline authorization expires at " + stamp + "; ordinary access-token refresh does not extend this grant. Check the OAuth app publishing status and renew consent before expiry."


def report_text(report):
    lines = ["# Hypeless YouTube delivery", "", f"**Mode:** {report['mode']} · OAuth configured: **{report['oauth_configured']}** · Verified this run: **{report['oauth_connected']}**", "",
             "| Long video | Category | Planned local publish time |", "|---|---|---|"]
    lines += [f"| {r['video_id']} | {r['category']} | {r['publish_local']} |" for r in report.get("plan", [])]
    if not report.get("plan"):
        lines += ["| No eligible long renders queued | — | — |"]
    lines += ["", "## Receipts", "", "| Video | Actual state | YouTube ID |", "|---|---|---|"]
    lines += [f"| {r['video_id']} | {r['state']} | {r.get('youtube_id') or '—'} |" for r in report.get("receipts", [])]
    if not report.get("receipts"):
        lines += ["| No upload receipts | — | — |"]
    lines += ["", "## Notes"] + ["- "+s for s in report.get("notes", [])]
    lines += ["", "## Issues"] + ["- "+s for s in report.get("issues", [])]
    lines += ["", "Scheduled/private/processing is not published. Only a confirmed public receipt is marked sent."]
    return "\n".join(lines)+"\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("video_ids", nargs="*", type=valid_id)
    ap.add_argument("--mode", choices=["dry-run", "private-pilot", "schedule", "enrich", "reconcile"], default="dry-run")
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--report", default=str(ROOT/"renders/youtube-delivery/report.json"))
    args = ap.parse_args()
    cfg, root_cfg = load_json(ROOT/"config/youtube.json"), root_config()
    items = load_json(ROOT/"queue/youtube-long.json")["items"]
    shorts_records = load_json(ROOT/"tracker/publications.json")["records"]
    if args.video_ids:
        missing = set(args.video_ids)-{i["video_id"] for i in items}
        if missing:
            raise SystemExit("Unknown long-video IDs: "+", ".join(sorted(missing)))
        items = [i for i in items if i["video_id"] in args.video_ids]
    dry = args.mode == "dry-run"
    if not dry and os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("Use the YouTube Actions workflow for durable journal-changing operations")
    if args.mode in {"schedule", "private-pilot", "enrich"}:
        if os.environ.get("ALLOW_YOUTUBE_MUTATIONS") != "true":
            raise SystemExit("YouTube mutations not authorized by this workflow run")
        if args.mode != "private-pilot" and not cfg["enabled"]:
            raise SystemExit("YouTube delivery disabled until connection + explicit owner activation")
    if args.mode == "schedule" and not cfg["live_pilot_passed"] and not args.pilot:
        raise SystemExit("Verify a public pilot before unattended scheduling")
    if (args.pilot or args.mode == "private-pilot") and len(items) != 1:
        raise SystemExit("A pilot requires exactly one selected long video")
    journal = Journal(root_cfg, remote=not dry, path=ROOT/"tracker/youtube-publications.json", remote_path=REMOTE_PATH)
    report = {"mode": args.mode, "generated_at": iso(now_utc()), "oauth_configured": bool(youtube_credentials()), "oauth_connected": False, "plan": [], "notes": [], "issues": [], "api_requests": 0}
    expiry_notice = oauth_expiry_notice(youtube_credentials())
    if expiry_notice:
        report["notes"].append(expiry_notice)
    if not report["oauth_configured"]:
        report["notes"].append("Google OAuth not connected. Uploader/enrichment code is installed; live API behavior is not yet verified.")
        if not dry:
            report["issues"].append("OAuth required; zero YouTube requests sent")
    planned, notes = plan(items, journal.records, shorts_records, cfg, now_utc(), preview=dry)
    report["plan"], report["notes"] = planned, report["notes"] + notes
    api = None
    try:
        if not dry and report["oauth_configured"]:
            cooldown = parse_time(journal.data.get("cooldown_until"))
            if cooldown and cooldown > now_utc():
                raise Deferred("Persisted YouTube cooldown active", "COOLDOWN", (cooldown-now_utc()).total_seconds())
            api = YouTubeAPI(cfg, journal)
            own_channel = api.verify_channel()
            report["oauth_connected"] = True
            uploads = own_channel["contentDetails"]["relatedPlaylists"]["uploads"]
            reconcile_known(api, journal)
            if args.mode in {"schedule", "private-pilot"}:
                by_id = {i["video_id"]: i for i in items}
                tasks = [r for r in planned if r["upload_eligible"]]
                if args.mode == "private-pilot":
                    if items[0].get("approval") != "approved":
                        raise ValueError("Private pilot still needs an approved render and copy")
                    tasks = [{"video_id": items[0]["video_id"], "publish_at": None}]
                for row in tasks[:cfg["max_uploads_per_run"]]:
                    item = by_id[row["video_id"]]
                    work = Path(os.environ.get("RUNNER_TEMP", "/var/tmp"))/"hypeless-youtube"/item["video_id"]
                    process(item, row, api, journal, root_cfg, work, uploads, args.mode == "private-pilot")
            if args.mode in {"schedule", "enrich"}:
                report["enriched"] = enrich_buffer_shorts(api, journal, shorts_records, load_json(ROOT/"queue/publish.json")["items"])
            for r in journal.records.values():
                if r.get("state") in BLOCKED | {"session_start_uncertain", "upload_uncertain", "expired_uncertain"}:
                    report["issues"].append(r["video_id"] + ": " + r.get("last_error", r["state"]))
    except Deferred as exc:
        report["notes"].append(str(exc))
        if not dry and exc.code not in {"PROCESSING", "STALE_SLOT", "THUMBNAIL_PENDING"}:
            journal.data["cooldown_until"] = iso(now_utc()+dt.timedelta(seconds=max(exc.wait_seconds, 300)))
            journal.save("persist YouTube cooldown")
    except Exception as exc:
        report["issues"].append(type(exc).__name__ + ": " + redact(str(exc)))
    finally:
        if api:
            report["api_requests"] = api.request_count
        public_receipt_fields = ("video_id", "state", "youtube_id", "external_url", "publish_at", "sent_at", "retry_at", "error_code", "last_error", "metadata_ready")
        report["receipts"] = [{k: r[k] for k in public_receipt_fields if k in r} for r in journal.records.values()]
        # Session ciphertext, OAuth material and raw provider capabilities are never in reports.
        save_json(args.report, report)
        text = report_text(report)
        Path(args.report).with_suffix(".md").write_text(text)
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
                f.write(text)
        print(text)
    return 1 if report["issues"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
