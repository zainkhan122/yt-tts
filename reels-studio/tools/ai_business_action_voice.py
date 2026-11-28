#!/usr/bin/env python3
"""Generate Chatterbox house narration for four independent draft scripts; no publication."""
import sys,json,uuid,time,hashlib,requests,concurrent.futures,io,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from lib.secrets import gh_token
base='https://api.github.com/repos/zainkhan122/yt-tts'; token=gh_token()
ids=['ai-business-action-01']
def go(id):
 s=requests.Session();s.headers.update({'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'}); lines=json.loads((ROOT/'briefs/graphics'/id/'script.json').read_text());digest=hashlib.sha256(json.dumps(lines,ensure_ascii=False,separators=(',',':')).encode()).hexdigest();d=ROOT/'renders'/id;d.mkdir(parents=True,exist_ok=True);state=d/'review-run.json'
 if state.exists():
  st=json.loads(state.read_text());assert st['script_sha256']==digest;key=st['request_key'];run=st.get('run_id')
 else:
  key=uuid.uuid4().hex[:16];run=None;state.write_text(json.dumps({'script_sha256':digest,'request_key':key,'status':'dispatching'},indent=2));r=s.post(base+'/actions/workflows/review-voice.yml/dispatches',json={'ref':'main','inputs':{'request_key':key,'script_json':json.dumps(lines,ensure_ascii=False)}},timeout=45);r.raise_for_status()
 if not run:
  for _ in range(30):
   r=s.get(base+'/actions/workflows/review-voice.yml/runs?per_page=100',timeout=45);r.raise_for_status();m=[x for x in r.json()['workflow_runs'] if x['display_title']=='House voice review '+key]
   if len(m)==1:run=m[0]['id'];break
   if len(m)>1:raise Exception('ambiguous run')
   time.sleep(3)
  if not run:raise Exception('dispatch uncertain: do not redispatch')
  state.write_text(json.dumps({'script_sha256':digest,'request_key':key,'run_id':run,'status':'dispatched'},indent=2))
 print(id,'voice run',run,flush=True)
 for _ in range(240):
  r=s.get(base+'/actions/runs/'+str(run),timeout=45);r.raise_for_status();j=r.json()
  if j['status']=='completed':
   if j['conclusion']!='success':raise Exception('voice workflow '+str(j['conclusion']))
   break
  time.sleep(15)
 else:raise Exception('still pending')
 r=s.get(base+'/actions/runs/'+str(run)+'/artifacts',timeout=45);r.raise_for_status();m=[x for x in r.json()['artifacts'] if x['name']=='review-house-voice' and not x['expired']];assert len(m)==1
 r=s.get(m[0]['archive_download_url'],timeout=120);r.raise_for_status();z=zipfile.ZipFile(io.BytesIO(r.content));dest=d/'voice-handoff';dest.mkdir(exist_ok=True)
 for name in ['voice.wav','timings.json']:
  hits=[n for n in z.namelist() if Path(n).name==name];assert len(hits)==1;(dest/name).write_bytes(z.read(hits[0]))
 doc=json.loads((dest/'timings.json').read_text());assert doc.get('script_sha256')==digest and doc.get('overall_match',0)>=.95 and doc.get('engine')=='chatterbox'
 print(id,'handoff OK',doc.get('duration'),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
 fs={pool.submit(go,id):id for id in ids}
 for f in concurrent.futures.as_completed(fs):
  try:f.result()
  except Exception as e:print(fs[f], 'ERROR',str(e),flush=True)
