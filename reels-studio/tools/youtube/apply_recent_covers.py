#!/usr/bin/env python3
"""Apply only pinned, reviewed covers to explicitly identified sent YouTube Shorts.

Actions-only: verifies channel, public visibility, kit hash and reviewed image hash;
no video, title, tags, playlist or scheduling changes. Writes durable cover receipts.
"""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from lib.secrets import redact
from tools.post.common import config, load_json
from tools.post.state import Journal
from tools.youtube.api import YouTubeAPI, YouTubeError
from tools.youtube.contracts import fetch_short_cover
from tools.youtube.approved_overrides import effective_item
from tools.youtube.metadata import attach_short_cover, get_video
from tools.youtube.runner import external_id


def cover_config(cfg):
    """Preserve daily general quota for delivery; never alter the upload-start limit."""
    return {**cfg, 'general_quota_budget_per_day': max(0, cfg['general_quota_budget_per_day'] - 500)}


def apply(api, journal, records, items, ids, work):
    by_id = {i['video_id']: effective_item(i) for i in items}
    results = []
    for vid in ids:
        try:
            rec = records.get(vid + ':youtube') or {}
            # Older published Shorts may have been removed from the active queue.
            # A manually published video additionally needs an explicit per-cover opt-in.
            item = by_id.get(vid) or effective_item({'video_id': vid})
            if rec.get('state') != 'sent' and not (rec.get('state') == 'published_manual' and item.get('manual_cover_eligible') is True):
                raise ValueError('Not a recorded sent or explicitly eligible manual YouTube Short')
            yid = rec.get('youtube_id') or external_id(rec.get('external_url'))
            if not yid:
                raise ValueError('Missing YouTube video ID')
            if not item.get('cover_sha256') or not item.get('cover_reviewed_at'):
                raise ValueError('No reviewed and pinned cover')
            video = get_video(api, yid)
            if video.get('status', {}).get('privacyStatus') != 'public':
                raise ValueError('Not currently public on YouTube')
            row = journal.data.setdefault('enrichment', {}).setdefault(yid, {'video_id': vid, 'youtube_id': yid})
            # A missing receipt is not proof that a Short lacks a custom thumbnail.
            # For the missing-cover batch, preserve unknown existing custom artwork.
            if item.get('preserve_existing_custom') and not (row.get('thumbnail_confirmed') and row.get('thumbnail_digest') == item['cover_sha256']):
                present = video.get('contentDetails', {}).get('hasCustomThumbnail')
                if present is not False:
                    row.update(cover_existing_custom_hold=True, cover_hold_digest=item['cover_sha256'],
                               cover_hold_reason='existing_custom' if present is True else 'thumbnail_state_unknown')
                    journal.save('preserve existing or unknown cover ' + vid)
                    results.append({'video_id': vid, 'youtube_id': yid, 'state': 'existing_custom_preserved' if present is True else 'thumbnail_state_unknown'})
                    continue
            cover = fetch_short_cover(item, config(), work)
            state = attach_short_cover(api, journal, row, yid, cover)
            results.append({'video_id': vid, 'youtube_id': yid, 'state': state,
                            'error': row.get('thumbnail_error'), 'cover_digest': cover['sha256']})
        except YouTubeError as exc:
            results.append({'video_id': vid, 'state': 'error', 'error': redact(str(exc))})
        except RuntimeError:
            raise  # journal conflicts and ambiguous writes must halt the whole batch
        except Exception as exc:
            results.append({'video_id': vid, 'state': 'error', 'error': redact(str(exc))})
    return results


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('ids', nargs='+'); ap.add_argument('--report', required=True); args = ap.parse_args()
    if os.environ.get('GITHUB_ACTIONS') != 'true' or os.environ.get('ALLOW_YOUTUBE_COVER_MUTATIONS') != 'true':
        raise SystemExit('Cover writes require explicitly authorized Actions workflow')
    if len(args.ids) > 20 or len(set(args.ids)) != len(args.ids): raise SystemExit('Select 1–20 unique IDs')
    cfg, root_cfg = load_json(ROOT/'config/youtube.json'), config()
    # Cover assignments are lower priority than delivery. Keep 500 units of the
    # shared daily general-API budget for Shorts metadata/scheduling work. Upload
    # starts have their own existing budget and are never consumed here.
    cfg = cover_config(cfg)
    records = load_json(ROOT/'tracker/publications.json')['records']; items = load_json(ROOT/'queue/publish.json')['items']
    journal = Journal(root_cfg, remote=True, path=ROOT/'tracker/youtube-publications.json', remote_path='reels-studio/tracker/youtube-publications.json')
    # Direct uploads have their own durable journal rather than a Buffer receipt.
    for vid, rec in journal.records.items():
        if rec.get('kind') == 'direct_short' and rec.get('state') == 'sent':
            records.setdefault(vid + ':youtube', {**rec, 'video_id': vid, 'platform': 'youtube'})
    api = YouTubeAPI(cfg, journal); api.verify_channel()
    result = apply(api, journal, records, items, args.ids, Path(os.environ['RUNNER_TEMP'])/'approved-short-covers')
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(json.dumps({'results': result},indent=2)+'\n')
    for r in result:
        print(r['video_id'], r['state'], r.get('error') or '')
    return 0 if all(r['state'] in {'confirmed', 'existing_custom_preserved'} for r in result) else 1

if __name__ == '__main__': sys.exit(main())
