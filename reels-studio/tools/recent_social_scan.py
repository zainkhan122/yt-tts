#!/usr/bin/env python3
"""Read-only social scan with publication provenance. Never writes legacy posts.csv.

python tools/recent_social_scan.py --hours 24 --limit 40
Optional YOUTUBE_API_KEY enables batched videos.list timestamp lookup. yt-dlp must be on PATH
or supplied via YT_DLP. Undated/date-only posts are quarantined, not treated as recent.
"""
import argparse, concurrent.futures, csv, datetime as dt, json, os, shutil, subprocess, sys, tempfile, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1]
UTC=dt.timezone.utc

def parse_exact(value):
    if isinstance(value,(int,float)) and not isinstance(value,bool):
        try: return dt.datetime.fromtimestamp(value,UTC)
        except (ValueError,OverflowError,OSError): return None
    if not isinstance(value,str) or 'T' not in value: return None
    try:
        x=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
        return x.astimezone(UTC) if x.tzinfo else None
    except ValueError: return None

def classify(value, now, hours):
    x=parse_exact(value)
    if not x: return 'unknown'
    age=(now-x).total_seconds()
    if age < -300: return 'future_or_clock_error'
    return 'recent' if 0 <= age <= hours*3600 else 'outside_window'

def resolve_target_date(value, now, zone, reference_date=None):
    """Resolve relative dates in the requested zone without a frozen example date.

    A user-provided reference is an editorial assumption, not an independent
    verification of wall-clock time. Metadata must retain that distinction.
    """
    if now.tzinfo is None:raise ValueError('An aware observation time is required')
    reference=dt.date.fromisoformat(reference_date) if reference_date else now.astimezone(zone).date()
    if value is None or value=='today':target=reference
    elif value=='yesterday':target=reference-dt.timedelta(days=1)
    else:target=dt.date.fromisoformat(value)
    return target,reference,('user_supplied' if reference_date else 'host_clock')

def run_json(args,timeout=45):
    p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=timeout)
    if p.returncode: raise RuntimeError('extractor failed: '+p.stderr.strip()[-400:])
    j=json.loads(p.stdout)
    if not isinstance(j,dict): raise ValueError('extractor returned no object')
    return j

def atom_dates(channel):
    if not channel: return {}
    url='https://www.youtube.com/feeds/videos.xml?'+urllib.parse.urlencode({'channel_id':channel})
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(req,timeout=12) as resp: root=ET.fromstring(resp.read())
    a='{http://www.w3.org/2005/Atom}'; y='{http://www.youtube.com/xml/schemas/2015}'
    return {e.findtext(y+'videoId'):e.findtext(a+'published') for e in root.findall(a+'entry')}

def api_dates(ids,key):
    if not key or not ids:return {}
    out={}
    for i in range(0,len(ids),50):
        url='https://www.googleapis.com/youtube/v3/videos?'+urllib.parse.urlencode({'part':'snippet','id':','.join(ids[i:i+50]),'key':key})
        with urllib.request.urlopen(url,timeout=20) as r: data=json.load(r)
        for it in data.get('items',[]): out[it['id']]=it.get('snippet',{}).get('publishedAt')
    return out

def one(src,exe,limit,now,hours,details,key):
    kind=src['type'];base=src['url'].rstrip('/');tabs=[''] if kind=='tiktok' else (src.get('tabs') or 'shorts').split(',')
    posts=[];errors=[];limited=False
    for tab in tabs:
        url=base if not tab else base+'/'+tab.strip()
        try:
            j=run_json([exe,'--flat-playlist','--playlist-end',str(limit),'--socket-timeout','10','--retries','0','--extractor-retries','0','-J','--no-warnings',url])
            entries=[e for e in j.get('entries',[]) if e and e.get('id')];limited |= len(entries)>=limit
        except Exception as ex:
            errors.append({'tab':url,'stage':'list','error':str(ex)[:500]});continue
        dates={}; api={}
        if kind=='youtube':
            channel=j.get('channel_id') or next((e.get('channel_id') for e in entries if e.get('channel_id')),None)
            try: dates=atom_dates(channel)
            except Exception as ex: errors.append({'tab':url,'stage':'atom','error':str(ex)[:300]})
            try: api=api_dates([str(e['id']) for e in entries],key)
            except Exception as ex: errors.append({'tab':url,'stage':'api','error':type(ex).__name__})
        for e in entries:
            vid=str(e['id']); link=e.get('url') or (f'https://www.youtube.com/watch?v={vid}' if kind=='youtube' else f'{base}/video/{vid}')
            stamp=api.get(vid); provenance='youtube_data_api' if parse_exact(stamp) else None
            if not provenance and parse_exact(dates.get(vid)):stamp=dates[vid];provenance='youtube_atom_published'
            if not provenance and parse_exact(e.get('timestamp')):stamp=e['timestamp'];provenance='yt_dlp_flat_timestamp'
            err=None
            if not provenance and details:
                try:
                    d=run_json([exe,'--skip-download','--no-warnings','--socket-timeout','10','--retries','0','--extractor-retries','0','-J',link],30)
                    if parse_exact(d.get('timestamp')):stamp=d['timestamp'];provenance='yt_dlp_video_timestamp'
                except Exception as ex:err=type(ex).__name__
            parsed=parse_exact(stamp) if provenance else None
            posts.append({'id':vid,'url':link,'tab':tab or 'profile','title':e.get('title'),'description':e.get('description'), 'views':e.get('view_count'), 'likes':e.get('like_count'), 'comments':e.get('comment_count'), 'reposts':e.get('repost_count'), 'duration_seconds':e.get('duration'), 'uploader':e.get('uploader'),
                          'published_utc':parsed.isoformat() if parsed else None,'published_new_york':parsed.astimezone(ZoneInfo('America/New_York')).isoformat() if parsed else None,
                          'timestamp_source':provenance,'date_only_hint':e.get('upload_date') if not parsed else None,
                          'window_status':classify(stamp if provenance else None,now,hours),'detail_error':err})
    return {'type':kind,'source':src['handle'],'posts':posts,'errors':errors,'limit_reached':limited}

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--hours',type=float,default=24);p.add_argument('--limit',type=int,default=40);p.add_argument('--workers',type=int,default=8);p.add_argument('--details',action='store_true',help='attempt individual extraction for undated entries; can be slow');p.add_argument('--output',default=str(ROOT/'research/topics/recent-social-latest.json'));p.add_argument('--source',action='append',default=[]);p.add_argument('--date',help='YYYY-MM-DD, today or yesterday; relative dates use the chosen timezone');p.add_argument('--reference-date',help='Optional user-supplied YYYY-MM-DD for resolving relative dates; not a verified clock');p.add_argument('--timezone',default='America/New_York',help='IANA timezone for the target day')
    a=p.parse_args(argv)
    if a.hours<=0 or a.limit<1 or a.workers<1:p.error('hours, limit and workers must be positive')
    exe=os.environ.get('YT_DLP') or shutil.which('yt-dlp') or str(Path.home()/'.local/bin/yt-dlp')
    if not Path(exe).exists() and not shutil.which(exe):p.error('install yt-dlp or set YT_DLP')
    with (ROOT/'research/sources.csv').open(encoding='utf-8',newline='') as f: rows=[r for r in csv.DictReader(f) if r.get('status','').lower()=='active' and r.get('type') in ('youtube','tiktok') and (not a.source or r.get('handle') in a.source)]
    now=dt.datetime.now(UTC); key=os.environ.get('YOUTUBE_API_KEY'); results=[]
    zone=ZoneInfo(a.timezone)
    target,reference,reference_source=resolve_target_date(a.date,now,zone,a.reference_date)
    start=dt.datetime.combine(target,dt.time.min,zone).astimezone(UTC)
    end=dt.datetime.combine(target+dt.timedelta(days=1),dt.time.min,zone).astimezone(UTC)
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
        fs={pool.submit(one,s,exe,a.limit,now,a.hours,a.details,key):s for s in rows}
        for f in concurrent.futures.as_completed(fs):
            s=fs[f]
            try:r=f.result()
            except Exception as ex:r={'type':s['type'],'source':s['handle'],'posts':[],'errors':[{'stage':'source','error':type(ex).__name__}],'limit_reached':False}
            results.append(r);print(r['type'],r['source'],'posts',len(r['posts']),'unknown',sum(x['window_status']=='unknown' for x in r['posts']),'errors',len(r['errors']),flush=True)
    
    for r in results:
        for post in r['posts']:
            stamp=parse_exact(post['published_utc'])
            post['target_day_status']='match' if stamp and start<=stamp<end else ('outside' if stamp else 'unknown')
            post['published_target_timezone']=stamp.astimezone(zone).isoformat() if stamp else None
    result={'target_date':target.isoformat(),'reference_date':reference.isoformat(),'reference_date_source':reference_source,'target_timezone':a.timezone,'target_start_utc':start.isoformat(),'target_end_utc_exclusive':end.isoformat(),'clock_conflict_target_future':start>now,'observed_at_utc':now.isoformat(),'observed_at_new_york':now.astimezone(ZoneInfo('America/New_York')).isoformat(),'window_start_utc':(now-dt.timedelta(hours=a.hours)).isoformat(),'window_hours':a.hours,'list_limit':a.limit,'selected_sources':len(rows),'youtube_api_enabled':bool(key),'results':sorted(results,key=lambda x:(x['type'],x['source']))}
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=out.parent,delete=False) as f:json.dump(result,f,ensure_ascii=False,indent=2);name=f.name
    os.replace(name,out)
    bad=sum(bool(r['errors']) or r['limit_reached'] or any(p['window_status']=='unknown' for p in r['posts']) for r in results)
    print('Wrote',out,'; sources with errors, unknowns or limit reached:',bad)
    return 2 if bad else 0
if __name__=='__main__':sys.exit(main())
