#!/usr/bin/env python3
"""Private-first, explicitly selected direct Shorts pilot; never touches Buffer.

A second live YouTube upload is permitted only for an explicitly authorised pilot.
Durable write-ahead state is shared with the YouTube uploader. An uncertain create
is held, never restarted blindly. Scheduled publication requires readback of all
metadata and a verified future timestamp.
"""
import datetime as dt
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.post.common import config, fingerprint, iso, load_json, now_utc, parse_time
from tools.post.media import asset_metadata, public_download, read_kit
from tools.post.state import Journal
from tools.youtube.api import Deferred, Uncertain, YouTubeAPI
from tools.youtube.contracts import fetch_short_cover
from tools.youtube.metadata import get_video, playlists_for, set_thumbnail, ensure_playlist
from tools.youtube.resumable import reconcile_upload, tracking_tag, upload
from tools.youtube.seo import validate

REMOTE = 'reels-studio/tracker/youtube-publications.json'


def validate_request(item, brief, buffer_record, due, now):
    if item.get('approval') != 'approved' or 'youtube' not in item.get('platforms', []):
        raise ValueError('Short and YouTube platform must be approved')
    if fingerprint(brief) != item.get('brief_sha256'):
        raise ValueError('Approved brief fingerprint mismatch')
    if not item.get('cover_reviewed_at') or item.get('cover_sha256') != item.get('approved_cover_sha'):
        raise ValueError('Reviewed cover digest missing or inconsistent')
    if item.get('review', {}).get('mp4_sha256') != item.get('asset_digest', '').removeprefix('sha256:'):
        raise ValueError('Reviewed video digest mismatch')
    # Legacy controlled duplicate pilot only; production passes None and independently
    # blocks existing Buffer publications in the production admission layer.
    if buffer_record is not None:
        if buffer_record.get('state') != 'scheduled' or parse_time(buffer_record.get('due_at')) != due:
            raise ValueError('Buffer schedule not verified or time differs; stop')
        if (buffer_record.get('media_ref') or {}).get('asset_digest') != item.get('asset_digest'):
            raise ValueError('Buffer receipt does not pin the same approved video')
    if not item.get('reviewed_at') or not item.get('expires_at'):
        raise ValueError('Dated editorial review and expiry required')
    if parse_time(item.get('not_before')) and due < parse_time(item['not_before']):
        raise ValueError('Slot precedes approved publication window')
    if due < now + dt.timedelta(hours=3):
        raise ValueError('Schedule is too close or in the past; refusing immediate publication')
    if parse_time(item.get('expires_at')) and due > parse_time(item['expires_at']):
        raise ValueError('Fact review expires before publication')
    return validate(brief, 'short', tracking_tag(item))


def verify_copy(video, snippet):
    actual = video.get('snippet', {})
    for field in ('title', 'description', 'categoryId'):
        if actual.get(field) != snippet[field]:
            raise ValueError('YouTube readback mismatch: ' + field)
    if not set(snippet['tags']).issubset(set(actual.get('tags', []))):
        raise ValueError('YouTube tag readback mismatch')


def run(item, brief, buffer_record, due, api, journal, root_cfg, work, clock=now_utc, sleep=time.sleep):
    snippet = validate_request(item, brief, buffer_record, due, clock())
    vid = item['video_id']
    record = journal.records.setdefault(vid, {'video_id': vid, 'category': item['category'], 'state': 'queued', 'attempts': 0})
    if record.get('asset_digest') and record['asset_digest'] != item['asset_digest']:
        raise ValueError('Existing YouTube checkpoint belongs to different media')
    if record.get('state') in {'blocked', 'duplicate_conflict', 'sent', 'cancelled'}:
        raise ValueError('Existing YouTube state requires manual review: ' + record['state'])
    work.mkdir(parents=True, exist_ok=True)
    manifest = read_kit(root_cfg, item)
    if manifest.get('cover', {}).get('sha256') != item['cover_sha256']:
        raise ValueError('Render manifest cover differs from reviewed cover')
    if (manifest.get('cover', {}).get('frame0', {}).get('cover_frame') != 0 or
            manifest.get('qa', {}).get('checks', {}).get('dedicated_cover_frame0') is not True):
        raise ValueError('Verified approved cover at decoded frame zero is required')
    cover = fetch_short_cover(item, root_cfg, work)
    if not cover:
        raise ValueError('Approved cover is required')
    from PIL import Image
    with Image.open(cover['path']) as im:
        if im.width * 16 != im.height * 9:
            raise ValueError('Direct Shorts cover must be exactly 9:16')
    upload_item = {**item, 'assets': {'video': {'size': item['asset_size']}},
                   'contains_synthetic_media': bool(item.get('youtube_ai_generated'))}
    channel = api.verify_channel()
    uploads = channel['contentDetails']['relatedPlaylists']['uploads']
    if not record.get('youtube_id'):
        if record.get('state') in {'session_start_uncertain', 'upload_uncertain', 'expired_uncertain'}:
            if not reconcile_upload(record, upload_item, api, journal, uploads):
                raise Uncertain('Prior upload uncertain; never start another', 'RECONCILE_REQUIRED')
        elif record.get('state') == 'queued':
            reconcile_upload(record, upload_item, api, journal, uploads)
    if not record.get('youtube_id'):
        asset = asset_metadata(root_cfg, item['asset_id'])
        if asset.get('name') != vid + '.mp4' or asset.get('size') != item['asset_size']:
            raise ValueError('Release asset identity differs from approved video')
        path = work / (vid + '.mp4')
        public_download(asset['browser_download_url'], item['asset_size'], item['asset_digest'], path)
        upload(upload_item, record, path, snippet, api, journal)
        path.unlink(missing_ok=True)
    yid = record['youtube_id']
    # Poll a bounded period; a later explicitly targeted run resumes the same ID.
    for _ in range(36):
        video = get_video(api, yid)
        status = video.get('status', {})
        if status.get('privacyStatus') != 'private':
            raise ValueError('Video is no longer private; stop for manual review')
        if video.get('processingDetails', {}).get('processingStatus') == 'succeeded':
            break
        if video.get('processingDetails', {}).get('processingStatus') in {'failed', 'terminated'}:
            raise ValueError('YouTube processing failed; retain existing video ID')
        sleep(10)
    else:
        record['state'] = 'processing'; journal.save('Short processing pending')
        raise Deferred('Short still processing; remains private', 'PROCESSING', 600)
    verify_copy(video, snippet)
    set_thumbnail(api, record, cover['path'], cover['sha256'], journal)
    playlists_for(api, journal, yid, item['category'], 'shorts')
    # Independently read membership and thumbnail after write; do not schedule on a weak receipt.
    for name in (item['category'], 'shorts'):
        pid = ensure_playlist(api, journal, name)
        entries = list(api.pages('playlistItems', {'part': 'contentDetails', 'playlistId': pid, 'videoId': yid, 'maxResults': 50}))
        if len(entries) != 1 or entries[0].get('contentDetails', {}).get('videoId') != yid:
            raise ValueError('Playlist membership readback missing or ambiguous: ' + name)
    video = get_video(api, yid)
    verify_copy(video, snippet)
    if video.get('contentDetails', {}).get('hasCustomThumbnail') is not True:
        raise Deferred('Custom thumbnail not confirmed; video remains private', 'THUMBNAIL_PENDING', 600)
    if parse_time(video.get('status', {}).get('publishAt')):
        if parse_time(video['status']['publishAt']) != due:
            raise ValueError('Existing YouTube schedule differs; no overwrite')
    else:
        if due < clock() + dt.timedelta(hours=3):
            raise ValueError('Schedule became stale; remain private')
        status = video['status']
        allowed = ('license', 'embeddable', 'publicStatsViewable', 'selfDeclaredMadeForKids', 'containsSyntheticMedia')
        body_status = {k: status[k] for k in allowed if k in status}
        body_status.update(privacyStatus='private', publishAt=iso(due), selfDeclaredMadeForKids=False,
                           containsSyntheticMedia=bool(item.get('youtube_ai_generated')))
        record.update(state='scheduling', publish_at=iso(due)); journal.save('reserve direct Shorts schedule')
        api.json('PUT', 'videos', params={'part': 'status'}, body={'id': yid, 'status': body_status},
                 headers={'If-Match': video['etag']} if video.get('etag') else {}, cost=50, idempotent=True)
    fresh = get_video(api, yid)
    verify_copy(fresh, snippet)
    if fresh.get('status', {}).get('privacyStatus') != 'private' or parse_time(fresh['status'].get('publishAt')) != due:
        raise Uncertain('Schedule readback unconfirmed; do not upload again', 'SCHEDULE_RECEIPT')
    if fresh.get('contentDetails', {}).get('hasCustomThumbnail') is not True:
        raise ValueError('Thumbnail not confirmed after scheduling')
    record.update(state='scheduled', publish_at=iso(due), external_url='https://youtube.com/shorts/'+yid,
                  thumbnail_confirmed=True, metadata_ready=True, scheduled_at=iso(clock()), kind='direct_short')
    journal.save('verified direct Short schedule')
    return record


def main():
    # The pilot is explicitly scoped: never make this a broad automatic publisher.
    if os.environ.get('GITHUB_ACTIONS') != 'true' or os.environ.get('DIRECT_SHORT_PILOT') != 'moneyprinterturbo-2026-11-20':
        raise SystemExit('Explicit Actions pilot authorization required')
    item = next(i for i in load_json(ROOT/'queue/publish.json')['items'] if i['video_id'] == 'repo-moneyprinterturbo-01')
    brief = load_json(ROOT/'briefs'/('repo-moneyprinterturbo-01.json'))
    cfg, root_cfg = load_json(ROOT/'config/youtube.json'), config()
    source = Journal(root_cfg, remote=True)
    buffer_record = source.records['repo-moneyprinterturbo-01:youtube']
    due = parse_time('2026-11-20T21:08:00Z')
    journal = Journal(root_cfg, remote=True, path=ROOT/'tracker/youtube-publications.json', remote_path=REMOTE)
    api = YouTubeAPI(cfg, journal)
    result = run(item, brief, buffer_record, due, api, journal, root_cfg, Path(os.environ['RUNNER_TEMP'])/'direct-short')
    print('Direct Short:', result['youtube_id'], result['state'], result['publish_at'], 'thumbnail and playlists confirmed by API')

if __name__ == '__main__': main()
