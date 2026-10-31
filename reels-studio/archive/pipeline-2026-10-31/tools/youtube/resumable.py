"""Write-ahead resumable upload state machine. Always private on initial upload.

A 308 is an upload receipt, not an HTTP redirect. Offset comes from Google, never
from a guessed local counter. Lost final responses are probed/reconciled without
starting a new videos.insert session.
"""
import re
from pathlib import Path

from tools.post.common import iso, now_utc
from tools.youtube.api import Deferred, Uncertain, YouTubeError, validate_session_url
from tools.youtube.secure_state import decrypt_session, encrypt_session, validate_key
from tools.youtube.seo import tracking_tag


def offset_from(response, total):
    if response.status_code != 308:
        raise ValueError("Offset requires a 308 upload receipt")
    value = response.headers.get("Range")
    if not value:
        return 0
    match = re.fullmatch(r"bytes=0-(\d+)", value.strip())
    if not match or not 0 < int(match[1])+1 <= total:
        raise YouTubeError("Invalid upload offset receipt; no guessed retry", "BAD_RANGE")
    return int(match[1]) + 1


def adopt_upload(record, response, journal, clock=now_utc):
    try:
        data = response.json()
        vid = data["id"]
        if not re.fullmatch(r"[A-Za-z0-9_-]{11}", vid):
            raise ValueError()
    except (ValueError, TypeError, KeyError):
        raise Uncertain("Upload completed without a usable video ID; reconcile marker", "MISSING_RECEIPT")
    record.update(youtube_id=vid, state="uploaded_private", uploaded_at=iso(clock()), updated_at=iso(clock()))
    record.pop("session_ciphertext", None)
    journal.save("YouTube upload receipt " + record["video_id"])
    return vid


def owned_matches(api, marker, uploads_playlist):
    ids, token = [], None
    complete = False
    # Bound to recent owned uploads, never a public search. A negative truncated scan
    # cannot authorize restarting a possibly completed upload.
    for _ in range(api.cfg["manual_upload_scan_pages"]):
        params = {"part": "contentDetails", "playlistId": uploads_playlist, "maxResults": 50}
        if token:
            params["pageToken"] = token
        page = api.json("GET", "playlistItems", params=params)
        ids.extend(p["contentDetails"]["videoId"] for p in page.get("items", []))
        token = page.get("nextPageToken")
        if not token:
            complete = True
            break
    found = []
    for n in range(0, len(ids), 50):
        response = api.json("GET", "videos", params={"part": "snippet,status,processingDetails", "id": ",".join(ids[n:n+50])})
        found.extend(v for v in response.get("items", []) if marker in v.get("snippet", {}).get("tags", []))
    return found, complete


def reconcile_upload(record, item, api, journal, uploads_playlist):
    found, complete = owned_matches(api, record.get("tracking_tag") or tracking_tag(item), uploads_playlist)
    if len(found) == 1:
        record.update(youtube_id=found[0]["id"], state="uploaded_private", updated_at=iso(now_utc()))
        record.pop("session_ciphertext", None)
        journal.save("recover YouTube upload receipt " + item["video_id"])
        return found[0]["id"]
    if len(found) > 1:
        record["state"] = "duplicate_conflict"
        journal.save("hold multiple matching YouTube uploads")
        raise YouTubeError("Multiple marker matches; do not upload another", "DUPLICATE_CONFLICT")
    return None


def upload(item, record, path, snippet, api, journal, *, state_key=None, clock=now_utc):
    path = Path(path)
    total = path.stat().st_size
    if total != item["assets"]["video"]["size"]:
        raise ValueError("Local MP4 length differs from pinned media")
    if record.get("youtube_id"):
        return record["youtube_id"]
    if record.get("state") in {"session_start_uncertain", "upload_uncertain", "expired_uncertain", "duplicate_conflict"}:
        raise Uncertain("Existing uncertain upload must be reconciled first", "RECONCILE_REQUIRED")
    validate_key(state_key)  # fail before any upload session is allocated
    if not record.get("session_ciphertext"):
        record.update(state="session_start_uncertain", tracking_tag=tracking_tag(item),
                      asset_digest=item["asset_digest"], video_id=item["video_id"], updated_at=iso(clock()), final_chunk_submitted=False)
        journal.save("reserve YouTube upload session " + item["video_id"])
        body = {"snippet": snippet, "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False,
                "containsSyntheticMedia": item.get("contains_synthetic_media", False)}}
        r = api.request("POST", "upload/videos", params={"uploadType": "resumable", "part": "snippet,status", "notifySubscribers": "true"},
                        body=body, headers={"X-Upload-Content-Length": str(total), "X-Upload-Content-Type": "video/mp4"},
                        cost=0, upload_start=True, idempotent=False)
        uri = r.headers.get("Location")
        if not uri:
            raise Uncertain("Upload session response lacked Location; no media sent", "SESSION_LOCATION")
        validate_session_url(uri)
        record.update(session_ciphertext=encrypt_session(uri, item, api.cfg["channel_id"], state_key), state="uploading", confirmed_bytes=0)
        journal.save("persist encrypted upload session " + item["video_id"])
    uri = decrypt_session(record["session_ciphertext"], item, api.cfg["channel_id"], state_key)

    def probe():
        return api.request("PUT", uri, data=b"", headers={"Content-Range": f"bytes */{total}", "Content-Length": "0"}, cost=0, idempotent=True)

    def respect_pause(response):
        if response.headers.get("Retry-After"):
            from tools.post.buffer_api import retry_after
            wait = retry_after(response.headers)
            if wait > api.cfg["max_inline_wait_seconds"]:
                raise Deferred("Upload server requested a pause", "UPLOAD_PAUSE", wait)
            api.sleep(wait + api.jitter())

    r = probe()  # even on a resumed run, ask Google what was really accepted
    if r.status_code in (200, 201):
        return adopt_upload(record, r, journal, clock)
    offset = offset_from(r, total)
    respect_pause(r)
    chunk_size = api.cfg["upload_chunk_bytes"]
    if chunk_size <= 0 or chunk_size % 262144:
        raise ValueError("Upload chunk size must be a positive multiple of 256 KiB")
    failures = 0
    with path.open("rb") as source:
        while offset < total:
            source.seek(offset)
            chunk = source.read(min(chunk_size, total-offset))
            if not chunk:
                raise ValueError("Unexpected end of upload source")
            final = offset + len(chunk) == total
            if final:
                record["final_chunk_submitted"] = True
                journal.save("reserve final upload chunk " + item["video_id"])
            try:
                r = api.request("PUT", uri, data=chunk, headers={"Content-Type": "video/mp4", "Content-Length": str(len(chunk)),
                    "Content-Range": f"bytes {offset}-{offset+len(chunk)-1}/{total}"}, cost=0, idempotent=False, timeout=(10, 300))
            except Uncertain:
                failures += 1
                record["last_error"] = "Chunk response lost; querying authoritative upload offset"
                journal.save("checkpoint interrupted transfer")
                if failures >= api.cfg["max_attempts"]:
                    raise Deferred("Transfer retry budget exhausted; keep the same session", "TRANSFER_RETRY", 900)
                api.sleep(2 ** failures + api.jitter())
                r = probe()
            if r.status_code in (200, 201):
                return adopt_upload(record, r, journal, clock)
            next_offset = offset_from(r, total)
            if next_offset == total:
                r = probe()
                if r.status_code in (200, 201):
                    return adopt_upload(record, r, journal, clock)
                raise Deferred("All bytes acknowledged; awaiting final receipt, do not restart", "FINAL_RECEIPT", 300)
            if next_offset <= offset:
                failures += 1
                if failures >= api.cfg["max_attempts"]:
                    raise Deferred("No upload progress; retain resumable checkpoint", "NO_PROGRESS", 900)
            offset = next_offset
            record.update(confirmed_bytes=offset, state="uploading", updated_at=iso(clock()))
            journal.save("checkpoint upload progress " + item["video_id"])
            respect_pause(r)
    raise Uncertain("No final upload receipt; reconcile before doing anything else", "FINAL_RECEIPT")
