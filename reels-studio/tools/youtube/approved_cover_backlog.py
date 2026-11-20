#!/usr/bin/env python3
"""Inventory sent Shorts and select only explicit approved-thumbnail replacements.

Read-only. The cron may apply the bounded selection via apply_recent_covers.py.
Missing designs are reported, never silently made or falsely approved.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ID = re.compile(r'^[a-z0-9][a-z0-9_-]{2,80}$')
from tools.youtube.covers_pending import external_id


def classify(records, enrichment, approvals, folder):
    rows = []
    for record in records.values():
        if record.get('platform') != 'youtube' or record.get('state') != 'sent':
            continue
        vid = record.get('video_id', '')
        yid = record.get('youtube_id') or external_id(record.get('external_url'))
        if not ID.fullmatch(vid) or not yid:
            rows.append({'video_id': vid, 'status': 'needs_valid_publication_id'})
            continue
        entry = approvals.get(vid)
        old = enrichment.get(yid, {})
        if not entry:
            rows.append({'video_id': vid, 'youtube_id': yid, 'status': 'needs_approved_design',
                         'other_thumbnail_confirmed': bool(old.get('thumbnail_confirmed'))})
            continue
        name, digest = entry.get('file'), entry.get('sha256', '')
        path = Path(folder) / (vid + '.png')
        if name != vid + '.png' or not re.fullmatch(r'sha256:[a-f0-9]{64}', digest) or not path.is_file():
            rows.append({'video_id': vid, 'youtube_id': yid, 'status': 'invalid_approval'})
            continue
        if 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            rows.append({'video_id': vid, 'youtube_id': yid, 'status': 'invalid_approval'})
            continue
        if old.get('thumbnail_confirmed') and old.get('thumbnail_digest') == digest:
            status = 'confirmed'
        elif old.get('thumbnail_blocked') and old.get('thumbnail_digest') == digest:
            status = 'blocked_review'
        else:
            status = 'pending'
        rows.append({'video_id': vid, 'youtube_id': yid, 'status': status, 'approved_digest': digest})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ids', action='store_true', help='print up to five approved pending IDs')
    args = ap.parse_args()
    load = lambda p: json.loads((ROOT / p).read_text())
    records = load('tracker/publications.json')['records']
    journal = load('tracker/youtube-publications.json')
    for vid, rec in journal.get('records', {}).items():
        if rec.get('kind') == 'direct_short' and rec.get('state') == 'sent':
            records.setdefault(vid + ':youtube', {**rec, 'video_id': vid, 'platform': 'youtube'})
    rows = classify(records, journal.get('enrichment', {}),
                    load('approved-thumbnails/manifest.json'), ROOT/'approved-thumbnails')
    if args.ids:
        print(' '.join([r['video_id'] for r in rows if r['status'] == 'pending'][:5]))
    else:
        print(json.dumps(rows, indent=2))

if __name__ == '__main__':
    main()
