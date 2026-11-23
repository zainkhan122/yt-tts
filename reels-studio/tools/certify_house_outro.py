#!/usr/bin/env python3
"""Create a hash-bound outro review receipt AFTER inspecting the finished MP4.

A receipt is an honest editorial attestation, not automatic proof of visual quality
or speech recognition. Do not run it without watching AND listening to the video.
The publishing gate also pins this receipt to the released MP4 digest.
"""
import argparse,datetime,hashlib,json,re,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.house_outro_gate import CONTRACT

CHECKS=('house_layout','logo','follow_and_comment','animated_cursor','voiced_cta','caption_sync','ending_not_truncated')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--id',required=True);p.add_argument('--video',type=Path,required=True)
    p.add_argument('--outro-start',type=float,required=True,help='seconds in the finished video')
    p.add_argument('--keyword',required=True);p.add_argument('--reviewer',required=True,choices=('owner','production-reviewer'))
    p.add_argument('--confirm',required=True,help='exactly WATCHED_AND_LISTENED_TO_FULL_OUTRO')
    a=p.parse_args()
    if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{2,80}',a.id):p.error('bad id')
    if not re.fullmatch(r'[A-Z0-9]{1,18}',a.keyword):p.error('keyword must be uppercase alphanumeric')
    if a.confirm!='WATCHED_AND_LISTENED_TO_FULL_OUTRO':p.error('complete audiovisual review first')
    import imageio_ffmpeg
    ff=imageio_ffmpeg.get_ffmpeg_exe()
    result=subprocess.run([ff,'-hide_banner','-i',str(a.video),'-f','null','-'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
    if result.returncode:raise SystemExit('MP4 could not be completely decoded; no receipt')
    m=re.search(r'Duration:\s*(\d+):(\d+):(\d+\.\d+)',result.stderr)
    if not m or 'Audio:' not in result.stderr:raise SystemExit('duration or audio missing; no receipt')
    duration=int(m[1])*3600+int(m[2])*60+float(m[3]);outro=round(duration-a.outro_start,2)
    if a.outro_start<0 or outro<4:raise SystemExit('endcard duration under four seconds; no receipt')
    h=hashlib.sha256()
    with a.video.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    rec={'contract':CONTRACT,'video_id':a.id,'video_sha256':'sha256:'+h.hexdigest(),
         'verdict':'PASS','review_kind':'finished-video audiovisual inspection','reviewer':a.reviewer,
         'reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'keyword':a.keyword,'outro_duration_seconds':outro,'checks':dict.fromkeys(CHECKS,True),
         'note':'Reviewer attests to layout, logo, CTA, cursor motion, narrated CTA, synced captions, and complete ending after watching and listening. Automated decode only verifies technical readability.'}
    dest=ROOT/'research/production/outro-receipts'/(a.id+'.json');dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(rec,indent=2)+'\n');print('Saved',dest,'for MP4',rec['video_sha256'])
if __name__=='__main__':main()
