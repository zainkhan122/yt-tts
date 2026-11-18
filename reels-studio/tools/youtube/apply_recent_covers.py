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
from tools.youtube.metadata import attach_short_cover, get_video
from tools.youtube.runner import external_id


def apply(api, journal, records, items, ids, work):
    by_id = {i['video_id']: i for i in items}
    results = []
    for vid in ids:
        try:
            rec = records.get(vid + ':youtube') or {}
            if rec.get('state') != 'sent':
                raise ValueError('Not a recorded sent YouTube Short')
            yid = rec.get('youtube_id') or external_id(rec.get('external_url'))
            if not yid:
                raise ValueError('Missing YouTube video ID')
            item = by_id.get(vid)
            if not item or not item.get('cover_sha256') or not item.get('cover_reviewed_at'):
                raise ValueError('No reviewed and pinned cover')
            video = get_video(api, yid)
            if video.get('status', {}).get('privacyStatus') != 'public':
                raise ValueError('Not currently public on YouTube')
            cover = fetch_short_cover(item, config(), work)
            row = journal.data.setdefault('enrichment', {}).setdefault(yid, {'video_id': vid, 'youtube_id': yid})
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
    records = load_json(ROOT/'tracker/publications.json')['records']; items = load_json(ROOT/'queue/publish.json')['items']
    journal = Journal(root_cfg, remote=True, path=ROOT/'tracker/youtube-publications.json', remote_path='reels-studio/tracker/youtube-publications.json')
    api = YouTubeAPI(cfg, journal); api.verify_channel()
    result = apply(api, journal, records, items, args.ids, Path(os.environ['RUNNER_TEMP'])/'approved-short-covers')
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(json.dumps({'results': result},indent=2)+'\n')
    for r in result:
        print(r['video_id'], r['state'], r.get('error') or '')
    return 0 if all(r['state'] == 'confirmed' for r in result) else 1

if __name__ == '__main__': sys.exit(main())
