#!/usr/bin/env python3
"""Read-only channel upload/thumbnail census; all API quota usage is journaled.

Durations <= 180 seconds are candidates, not definitive proof of Shorts format.
This makes no cover writes and never enumerates private video details in the report.
"""
import argparse, json, re, sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.post.common import config, load_json
from tools.post.state import Journal
from tools.youtube.api import YouTubeAPI
from tools.youtube.covers_pending import external_id


def seconds(value):
    m=re.fullmatch(r'P(?:(\d+)D)?T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?',value or '')
    if not m: return None
    d,h,mi,s=(int(x or 0) for x in m.groups());return d*86400+h*3600+mi*60+s

def main():
    p=argparse.ArgumentParser();p.add_argument('--report',required=True);args=p.parse_args()
    cfg=load_json(ROOT/'config/youtube.json');cfg['general_quota_budget_per_day']=max(0,cfg['general_quota_budget_per_day']-500)
    journal=Journal(config(),remote=True,path=ROOT/'tracker/youtube-publications.json',remote_path='reels-studio/tracker/youtube-publications.json')
    api=YouTubeAPI(cfg,journal);channel=api.verify_channel();playlist=channel['contentDetails']['relatedPlaylists']['uploads']
    entries=list(api.pages('playlistItems',{'part':'contentDetails','playlistId':playlist,'maxResults':50},maximum=30))
    ids=list(dict.fromkeys(x['contentDetails']['videoId'] for x in entries if x.get('contentDetails',{}).get('videoId')))
    source=load_json(ROOT/'tracker/publications.json')['records'];mapping={}
    for rec in source.values():
        if rec.get('platform')=='youtube' and rec.get('state') in {'sent', 'published_manual'}:
            yid=rec.get('youtube_id') or external_id(rec.get('external_url'));mapping[yid]=rec.get('video_id')
    for vid,rec in journal.data.get('records',{}).items():
        if rec.get('kind')=='direct_short' and rec.get('youtube_id'):mapping[rec['youtube_id']]=vid
    rows=[];absent=[]
    for i in range(0,len(ids),50):
        body=api.json('GET','videos',params={'part':'id,snippet,status,contentDetails','id':','.join(ids[i:i+50]),'maxResults':50})
        observed={v['id'] for v in body.get('items',[])};absent.extend(set(ids[i:i+50])-observed)
        for v in body.get('items',[]):
            if v.get('status',{}).get('privacyStatus')!='public':continue
            content=v.get('contentDetails',{});dur=seconds(content.get('duration'));y=v['id']
            rows.append({'youtube_id':y,'tracked_video_id':mapping.get(y),'title':v.get('snippet',{}).get('title'),'description':v.get('snippet',{}).get('description',''),'published_at':v.get('snippet',{}).get('publishedAt'),'duration_seconds':dur,'custom_thumbnail':content.get('hasCustomThumbnail'),'short_candidate':dur is not None and dur<=180,'known_short':y in mapping})
    report={'upload_playlist_entries':len(ids),'not_returned_count':len(absent),'public_count':len(rows),'short_definition':'tracked Short or public duration <= 180 sec; untracked candidates require portrait/Shorts verification','videos':rows}
    out=Path(args.report);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    candidates=[r for r in rows if r['known_short'] or r['short_candidate']];print('Upload entries:',len(ids),'public:',len(rows),'not returned:',len(absent));print('Short candidates:',len(candidates),'custom-state:',dict(Counter(str(r['custom_thumbnail']) for r in candidates)))
    print('Report saved; no YouTube videos or thumbnails changed.')
if __name__=='__main__':main()
