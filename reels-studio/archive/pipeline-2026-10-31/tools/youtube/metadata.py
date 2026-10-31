"""Idempotent metadata/thumbnail updates and write-ahead playlist membership.

No duplicate playlist creation/insertion after an uncertain response. Shorts
retain their public title, description and privacy while receiving tags/playlists.
"""
from pathlib import Path

from tools.post.common import iso, now_utc
from tools.youtube.api import Deferred, Uncertain, YouTubeError
from tools.youtube.seo import merge_tags_preserving_copy


def get_video(api, video_id):
    body = api.json("GET", "videos", params={"part": "snippet,status,processingDetails,contentDetails", "id": video_id})
    items = body.get("items", [])
    if len(items) != 1:
        raise Deferred("Video receipt not yet visible in YouTube; do not re-upload", "VIDEO_NOT_READY", 900)
    video = items[0]
    if video["snippet"]["channelId"] != api.cfg["channel_id"]:
        raise YouTubeError("Video belongs to a different YouTube channel", "CHANNEL_MISMATCH")
    return video


def ensure_playlist(api, journal, name):
    spec = api.cfg["playlists"][name]
    cache = getattr(api, "playlist_cache", {})
    if name in cache:
        return cache[name]
    row = journal.data.setdefault("playlists", {}).setdefault(name, {})
    playlist_id = spec.get("id") or row.get("id")
    if playlist_id:
        found = api.json("GET", "playlists", params={"part": "snippet", "id": playlist_id}).get("items", [])
        if len(found) != 1 or found[0]["snippet"]["channelId"] != api.cfg["channel_id"]:
            raise YouTubeError("Configured playlist absent or not owned by this channel", "PLAYLIST_IDENTITY")
    else:
        found = [p for p in api.pages("playlists", {"part": "snippet", "mine": "true", "maxResults": 50})
                 if p["snippet"]["title"] == spec["title"]]
        if len(found) > 1:
            raise YouTubeError("Multiple playlists have the target title; choose the ID explicitly", "PLAYLIST_CONFLICT")
        if found:
            playlist_id = found[0]["id"]
        else:
            if row.get("state") in {"creating", "uncertain"}:
                raise Uncertain("Prior playlist create has no unique receipt; do not create another", "PLAYLIST_UNCERTAIN")
            row.update(state="creating", title=spec["title"])
            journal.save("reserve playlist " + name)
            try:
                response = api.json("POST", "playlists", params={"part": "snippet,status"},
                    body={"snippet": {"title": spec["title"], "description": spec["description"], "defaultLanguage": "en"},
                          "status": {"privacyStatus": "public"}}, cost=50, idempotent=False)
                playlist_id = response["id"]
            except Deferred:
                row["state"] = "retry_wait"  # explicit rejection, no object created
                journal.save("playlist creation deferred")
                raise
            except Uncertain:
                row["state"] = "uncertain"
                journal.save("uncertain playlist create")
                raise
    row.update(id=playlist_id, state="ready")
    journal.save("playlist receipt " + name)
    cache[name] = playlist_id
    api.playlist_cache = cache
    return playlist_id


def ensure_membership(api, journal, playlist_id, video_id):
    key = playlist_id + ":" + video_id
    row = journal.data.setdefault("memberships", {}).setdefault(key, {})
    # Re-read even for a known receipt: respect deliberate removals; don't silently re-add.
    found = list(api.pages("playlistItems", {"part": "id", "playlistId": playlist_id, "videoId": video_id, "maxResults": 50}))
    if found:
        row.update(state="done", id=found[0]["id"], matching_entries=len(found))
        journal.save("playlist membership receipt")
        return
    if row.get("state") in {"adding", "uncertain", "done"}:
        raise Uncertain("Known/uncertain membership is absent; inspect before adding again", "MEMBERSHIP_UNCERTAIN")
    row.update(state="adding", playlist_id=playlist_id, video_id=video_id)
    journal.save("reserve playlist membership")
    try:
        response = api.json("POST", "playlistItems", params={"part": "snippet"},
            body={"snippet": {"playlistId": playlist_id, "resourceId": {"kind": "youtube#video", "videoId": video_id}}},
            cost=50, idempotent=False)
        row.update(state="done", id=response["id"])
        journal.save("playlist membership accepted")
    except Deferred:
        row["state"] = "retry_wait"
        journal.save("playlist membership deferred")
        raise
    except Uncertain:
        row["state"] = "uncertain"
        journal.save("playlist membership uncertain")
        raise


def playlists_for(api, journal, video_id, category, kind):
    for name in (category, kind):
        ensure_membership(api, journal, ensure_playlist(api, journal, name), video_id)


def set_thumbnail(api, record, path, digest, journal):
    if record.get("thumbnail_digest") == digest:
        return
    data = Path(path).read_bytes()
    # The exact same deterministic assignment may be retried; it creates no new video.
    api.json("POST", "upload/thumbnails/set", params={"videoId": record["youtube_id"], "uploadType": "media"},
             data=data, headers={"Content-Type": "image/jpeg"}, cost=50, idempotent=True)
    record["thumbnail_digest"] = digest
    journal.save("thumbnail assigned " + record["video_id"])


SHORT_COVER_ATTEMPT_LIMIT = 4


def attach_short_cover(api, journal, row, video_id, cover):
    """Set the agent-reviewed cover image and confirm it via a read-back.

    Returns "confirmed" | "pending" | "blocked". Bounded: after
    SHORT_COVER_ATTEMPT_LIMIT unconfirmed/failed tries the row is marked
    thumbnail_blocked for agent review (e.g. channel eligibility), not retried
    forever. Every try is idempotent — the digest gate prevents re-uploads."""
    from lib.secrets import redact
    digest = cover["sha256"]
    attempts = row.get("thumbnail_attempts", 0)
    if row.get("thumbnail_confirmed"):
        return "confirmed"
    if attempts >= SHORT_COVER_ATTEMPT_LIMIT:
        row["thumbnail_blocked"] = True
        return "blocked"
    try:
        if row.get("thumbnail_digest") != digest:
            set_thumbnail(api, row, cover["path"], digest, journal)
        fresh = get_video(api, video_id)
        if fresh.get("contentDetails", {}).get("hasCustomThumbnail") is True:
            row["thumbnail_confirmed"] = True
            row.pop("thumbnail_error", None)
            row.pop("thumbnail_blocked", None)
            journal.save("Shorts cover confirmed " + row["video_id"])
            return "confirmed"
        row["thumbnail_attempts"] = attempts + 1
        row["thumbnail_error"] = "YouTube has not confirmed the custom thumbnail yet"
    except (YouTubeError, Uncertain, Deferred) as exc:
        row["thumbnail_attempts"] = attempts + 1
        row["thumbnail_error"] = redact(str(exc)) + " (" + getattr(exc, "code", "ERROR") + ")"
    if row["thumbnail_attempts"] >= SHORT_COVER_ATTEMPT_LIMIT:
        row["thumbnail_blocked"] = True
        row["thumbnail_error"] = ("Bounded cover attempts exhausted; channel eligibility or image policy may block Shorts covers. "
                                  "Agent review required. " + row.get("thumbnail_error", "")).strip()
        journal.save("Shorts cover blocked " + row["video_id"])
        return "blocked"
    journal.save("Shorts cover pending " + row["video_id"])
    return "pending"


def enrich_short(api, journal, source, tags, category, cover=None):
    video_id = source["youtube_id"]
    row = journal.data.setdefault("enrichment", {}).setdefault(video_id, {"video_id": source["video_id"], "youtube_id": video_id})
    video = get_video(api, video_id)
    body = merge_tags_preserving_copy(video, tags)
    if body["snippet"]["tags"] != video["snippet"].get("tags", []):
        headers = {"If-Match": video["etag"]} if video.get("etag") else {}
        api.json("PUT", "videos", params={"part": "snippet"}, body=body, headers=headers, cost=50, idempotent=True)
    row["tags_done"] = True
    journal.save("Shorts backend tags enriched")
    playlists_for(api, journal, video_id, category, "shorts")
    if cover:
        state = attach_short_cover(api, journal, row, video_id, cover)
        if state == "pending":
            row["state"] = "cover_pending"  # tags/playlists recorded; the cover retries next run
            journal.save("Shorts cover pending state " + source["video_id"])
            return row
    row.update(state="done", completed_at=iso(now_utc()), public_copy_preserved=True)
    journal.save("Shorts metadata complete " + source["video_id"])
    return row
