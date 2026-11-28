import csv,json,subprocess,concurrent.futures,datetime as dt,urllib.request,xml.etree.ElementTree as ET,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
rows=[r for r in csv.DictReader((ROOT/'research/sources.csv').open()) if r.get('status','').lower()=='active' and r.get('type') in {'tiktok','youtube'}]

def scan(src):
    base=src['url'].rstrip('/'); urls=[base] if src['type']=='tiktok' else [base+'/'+x.strip() for x in (src.get('tabs') or 'shorts').split(',')]
    posts=[];errors=[]
    for url in urls:
        try:
            p=subprocess.run(['/home/user/.local/bin/yt-dlp','--flat-playlist','--playlist-end','20','--socket-timeout','8','--retries','0','--extractor-retries','0','-J','--no-warnings',url],capture_output=True,text=True,timeout=45)
            if p.returncode or not p.stdout.strip(): raise RuntimeError((p.stderr or 'no data')[-350:])
            d=json.loads(p.stdout); entries=d.get('entries') or []; dates={}
            channel=d.get('channel_id') or next((e.get('channel_id') for e in entries if e and e.get('channel_id')),None)
            if src['type']=='youtube' and channel:
                try:
                    request=urllib.request.Request('https://www.youtube.com/feeds/videos.xml?channel_id='+channel,headers={'User-Agent':'Mozilla/5.0'})
                    xml=ET.fromstring(urllib.request.urlopen(request,timeout=8).read())
                    for e in xml.findall('{http://www.w3.org/2005/Atom}entry'):
                        vid=e.findtext('{http://www.youtube.com/xml/schemas/2015}videoId'); dates[vid]=e.findtext('{http://www.w3.org/2005/Atom}published')
                except Exception: pass
            for e in entries:
                if not e:continue
                ts=e.get('timestamp'); published=dt.datetime.fromtimestamp(ts,dt.timezone.utc).isoformat() if ts else dates.get(e.get('id'))
                posts.append({'title':e.get('title'), 'description':(e.get('description') or '')[:1500], 'url':e.get('url'),'published':published,'views':e.get('view_count'),'id':e.get('id'),'tab':url})
        except Exception as e:errors.append({'url':url,'error':str(e)[-350:]})
    return {'type':src['type'],'source':src['handle'],'urls':urls,'posts':posts,'errors':errors}

results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
    fs=[pool.submit(scan,r) for r in rows]
    for f in concurrent.futures.as_completed(fs):
        result=f.result();results.append(result)
        print(result['type'],result['source'],'posts',len(result['posts']),'errors',len(result['errors']),flush=True)
        Path('/home/user/yt-tts/reels-studio/research/topics/live-source-scan-2026-11-23.json').write_text(json.dumps({'observed_at_system_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'results':results},indent=2))
print('COMPLETE',len(results),flush=True)
