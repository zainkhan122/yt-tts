#!/usr/bin/env python3
"""Fail-closed house-outro evidence gate for managed Short publishing.

The receipt records *inspection of the exact MP4*, not merely an endcard in a
project timeline. Generate using the separate auditor, after audiovisual review.
A digest change invalidates the receipt. Existing provider schedules are not edited.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = 'hypeless-narrated-outro-v1'
DIGEST = re.compile(r'^sha256:[0-9a-f]{64}$')
ID = re.compile(r'^[a-z0-9][a-z0-9_-]{2,80}$')


def errors_for(item, root=ROOT):
    vid = item.get('video_id', '')
    digest = item.get('asset_digest', '')
    if not isinstance(vid, str) or not ID.fullmatch(vid):
        return ['house outro: invalid video identity']
    if not isinstance(digest, str) or not DIGEST.fullmatch(digest):
        return ['house outro: exact released MP4 digest missing']
    path = Path(root) / 'research' / 'production' / 'outro-receipts' / (vid + '.json')
    try:
        rec = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return ['house outro: final-video audit receipt missing or unreadable']
    problems = []
    if not isinstance(rec, dict):
        return ['house outro: malformed receipt']
    # A specific owner decision can override the editorial gate for one exact
    # file, without pretending a reviewer performed unverified checks. This does
    # not disable duplicate prevention or provider readback and does not extend
    # to other videos or changed bytes.
    if (rec.get('contract') == CONTRACT and rec.get('video_id') == vid
        and rec.get('video_sha256') == digest and rec.get('verdict') == 'OWNER_OVERRIDE'
        and rec.get('reviewer') == 'owner' and rec.get('approved_at')
        and rec.get('authorization') == 'OWNER_APPROVED_EXACT_VIDEO_WAIVE_EDITORIAL_GATES'
        and rec.get('known_issues')):
        return []
    if rec.get('contract') != CONTRACT or rec.get('video_id') != vid or rec.get('video_sha256') != digest:
        problems.append('house outro: receipt does not match the exact released MP4 and contract')
    if rec.get('verdict') != 'PASS' or rec.get('review_kind') != 'finished-video audiovisual inspection':
        problems.append('house outro: finished audiovisual review has not passed')
    if rec.get('reviewer') not in ('owner', 'production-reviewer') or not rec.get('reviewed_at'):
        problems.append('house outro: reviewer and review date required')
    checks = rec.get('checks')
    required = ('house_layout', 'logo', 'follow_and_comment', 'animated_cursor', 'voiced_cta', 'caption_sync', 'ending_not_truncated')
    if not isinstance(checks, dict) or any(checks.get(k) is not True for k in required):
        problems.append('house outro: required visual, motion, voice and caption checks are incomplete')
    duration = rec.get('outro_duration_seconds')
    if isinstance(duration, bool) or not isinstance(duration, (int, float)) or duration < 4:
        problems.append('house outro: full narrated end sequence must be at least four seconds')
    if not isinstance(rec.get('keyword'), str) or not re.fullmatch(r'[A-Z0-9]{1,18}', rec['keyword']):
        problems.append('house outro: comment keyword missing')
    return problems


def require(item, root=ROOT):
    problems = errors_for(item, root)
    if problems:
        raise ValueError('; '.join(problems))
