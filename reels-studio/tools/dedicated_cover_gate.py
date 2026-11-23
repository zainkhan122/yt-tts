"""Fail-closed evidence of a purpose-made cover embedded in the exact Short.

The receipt is generated from the actual finished file by certify_dedicated_cover;
image origin is an editorial provenance attestation, not automated proof of taste.
Applies to new managed posts and replacements, not existing provider schedules.
"""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HASH=re.compile(r'^sha256:[0-9a-f]{64}$')
ID=re.compile(r'^[a-z0-9][a-z0-9_-]{2,80}$')

def errors_for(item,root=ROOT):
    vid=item.get('video_id','');video=item.get('asset_digest','');cover=item.get('cover_sha256','')
    if not isinstance(vid,str) or not ID.fullmatch(vid):return ['dedicated cover: invalid video id']
    if not all(isinstance(v,str) and HASH.fullmatch(v) for v in (video,cover)):
        return ['dedicated cover: video and cover digests are required']
    path=Path(root)/'research/production/cover-receipts'/(vid+'.json')
    try:r=json.loads(path.read_text())
    except (OSError,ValueError):return ['dedicated cover: receipt missing or unreadable']
    if not isinstance(r,dict):return ['dedicated cover: malformed receipt']
    issues=[]
    if r.get('contract')!='dedicated-cover-v1' or r.get('video_id')!=vid or r.get('video_sha256')!=video or r.get('cover_sha256')!=cover:
        issues.append('dedicated cover: exact video/cover identity mismatch')
    if r.get('source_kind')!='purpose-made-for-this-video' or not HASH.fullmatch(str(r.get('art_sha256',''))):
        issues.append('dedicated cover: purpose-made artwork provenance missing')
    else:
        for other in path.parent.glob('*.json'):
            if other == path: continue
            try: previous=json.loads(other.read_text())
            except (OSError,ValueError): continue
            if isinstance(previous,dict) and previous.get('art_sha256')==r['art_sha256'] and previous.get('video_id')!=vid:
                issues.append('dedicated cover: artwork already assigned to another video');break
    if r.get('frame_zero_verified') is not True or r.get('dimensions')!=[1080,1920]:
        issues.append('dedicated cover: first-frame or portrait verification missing')
    diff=r.get('frame_zero_mean_abs_rgb_error')
    if isinstance(diff,bool) or not isinstance(diff,(int,float)) or diff>6 or diff<0:
        issues.append('dedicated cover: cover does not match embedded first frame')
    if not r.get('reviewed_at') or not r.get('headline'):issues.append('dedicated cover: design review metadata missing')
    return issues

def require(item,root=ROOT):
    errs=errors_for(item,root)
    if errs:raise ValueError('; '.join(errs))
