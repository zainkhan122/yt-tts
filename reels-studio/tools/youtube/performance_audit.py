#!/usr/bin/env python3
"""Fetch a current, read-only channel-video performance audit for tracked Shorts."""
import argparse, datetime as dt, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.post.common import config, load_json, now_utc, parse_time, iso
from tools.post.state import Journal
from tools.youtube.api import YouTubeAPI, ANALYTICS_REPORTS
from tools.youtube.analytics import targets, data_api_stats

METRICS='views,engagedViews,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained,shares'

def collect(api, records, now):
    ids=targets(records); stats=data_api_stats(api, sorted(set(ids.values())))
    dates=[parse_time(x['published_at']).date() for x in stats.values() if x.get('published_at')]
    if not dates: raise ValueError('No tracked published YouTube videos found')
    start=min(dates).isoformat();end=now.date().isoformat()
    body=api.json('GET', ANALYTICS_REPORTS, params={'ids':'channel==MINE','startDate':start,'endDate':end,
        'dimensions':'video','metrics':METRICS,'sort':'-views','maxResults':200})
    headers=[x['name'] for x in body.get('columnHeaders', [])]
    if not headers: raise ValueError('Analytics response did not provide column headers')
    rows={r[0]:dict(zip(headers,r)) for r in body.get('rows',[])}
    output=[]
    for vid,yid in sorted(ids.items()):
        st=stats.get(yid)
        if st is None: continue
        output.append({'video_id':vid,'youtube_id':yid,'published_at':st['published_at'],
            'age_hours':round((now-parse_time(st['published_at'])).total_seconds()/3600,1),
            'data_api':st,'analytics':rows.get(yid)})
    return {'generated_at':iso(now),'analytics_start_date':start,'analytics_end_date':end,
            'analytics_rows':len(rows),'analytics_limit':200,'videos':output,
            'notes':['Analytics totals and Data API counts may differ and may lag.',
                     'Top-video response is limited to 200; omitted videos are not zero.',
                     'Lifetime totals compare videos of different ages; not causal.',
                     'Thumbnail impressions, CTR and viewed-versus-swiped are not returned by this query.']}

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args()
    root=config(); cfg=load_json(ROOT/'config/youtube.json')
    journal=Journal(root,remote=True,path=ROOT/'tracker/youtube-publications.json',remote_path='reels-studio/tracker/youtube-publications.json')
    api=YouTubeAPI(cfg,journal);api.verify_channel();records=load_json(ROOT/'tracker/publications.json')['records']
    out=collect(api,records,now_utc());path=Path(a.out);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(out,indent=2)+'\n')
    print('Read-only performance audit: videos',len(out['videos']),'Analytics rows',out['analytics_rows'])
if __name__=='__main__':main()
