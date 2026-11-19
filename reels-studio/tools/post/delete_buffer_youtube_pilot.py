#!/usr/bin/env python3
"""One explicitly authorised Buffer deletion after verifying the direct replacement."""
import os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.post.common import config, iso, load_json, now_utc, parse_time
from tools.post.state import Journal
from tools.post.buffer_api import BufferClient
from tools.post.release import delete_row
from tools.youtube.api import YouTubeAPI
from tools.youtube.metadata import get_video

KEY='repo-moneyprinterturbo-01:youtube'
ID='6aff12f1e28319f49a112c27'
YID='rp9OnMg8QII'
DUE=parse_time('2026-11-20T21:08:00Z')

def execute(buffer, publications, yt, api):
    replacement=yt.records.get('repo-moneyprinterturbo-01') or {}
    if (replacement.get('state') != 'scheduled' or replacement.get('youtube_id') != YID or
        parse_time(replacement.get('publish_at')) != DUE or not replacement.get('thumbnail_confirmed')):
        raise ValueError('Direct YouTube replacement not confirmed; no Buffer deletion')
    video=get_video(api,YID)
    if (video.get('status',{}).get('privacyStatus') != 'private' or
        parse_time(video.get('status',{}).get('publishAt')) != DUE or
        video.get('contentDetails',{}).get('hasCustomThumbnail') is not True or DUE <= now_utc()):
        raise ValueError('Direct YouTube live readback is not the expected future schedule; no Buffer deletion')
    row=publications.records.get(KEY) or {}
    if row.get('state') == 'deleted' and row.get('previous_buffer_post_id') == ID:
        return 'already deleted'
    if row.get('state') not in {'scheduled','deletion_pending'} or row.get('buffer_post_id') != ID:
        raise ValueError('Buffer journal not the expected pending post')
    _, posts=buffer.state()
    matches=[p for p in posts if p.get('id')==ID]
    if len(matches)>1: raise ValueError('Ambiguous Buffer post')
    if matches:
        post=matches[0]
        if post.get('channelId') != config()['buffer']['channels']['youtube']['buffer_id'] or post.get('status') != 'scheduled' or parse_time(post.get('dueAt')) != DUE:
            raise ValueError('Buffer post is no longer the exact scheduled YouTube post')
        row['state']='deletion_pending';publications.save('reserve owner-approved Buffer YouTube deletion')
        buffer.delete(ID)
        _, after=buffer.state()
        if any(p.get('id')==ID for p in after): raise RuntimeError('Buffer post still present; stop')
    elif row.get('state') != 'deletion_pending':
        raise ValueError('Buffer post absent before reservation; manual review required')
    delete_row(row,'owner removed duplicate after direct YouTube schedule verified',now_utc())
    publications.save('confirm deleted duplicate Buffer YouTube post')
    return 'deleted and independently absent from Buffer'


def main():
    if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('DELETE_BUFFER_YOUTUBE_PILOT')!='owner-approved':
        raise SystemExit('Owner-approved Actions execution required')
    root=config();yt=Journal(root,remote=True,path=ROOT/'tracker/youtube-publications.json',remote_path='reels-studio/tracker/youtube-publications.json')
    publications=Journal(root,remote=True)
    api=YouTubeAPI(load_json(ROOT/'config/youtube.json'),yt);api.verify_channel()
    print(execute(BufferClient(root['buffer']),publications,yt,api))
if __name__=='__main__': main()
