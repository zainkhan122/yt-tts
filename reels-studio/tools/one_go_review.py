#!/usr/bin/env python3
"""One-command setup + approved cloud voice + local review assembly, never publishing.
Usage: python3 tools/one_go_review.py --id ID --script PATH --renderer PATH
Script/inputs and voice artifacts on public repository Actions are not confidential.
The renderer consumes renders/ID/voice-handoff/{voice.wav,timings.json}; final QA is separate.
"""
import argparse,hashlib,io,json,os,re,subprocess,sys,time,uuid,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--id',required=True);p.add_argument('--script',required=True,type=Path);p.add_argument('--renderer',required=True,type=Path);p.add_argument('--resume',type=int);a=p.parse_args()
 if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,99}',a.id):p.error('invalid id')
 script=a.script.resolve();renderer=a.renderer.resolve()
 if ROOT not in script.parents or ROOT not in renderer.parents or not renderer.is_file():p.error('script and renderer must be files within reels-studio')
 lines=json.loads(script.read_text());
 if not isinstance(lines,list) or not 1<=len(lines)<=12 or any(not isinstance(x,str) or not x.strip() or len(x)>450 for x in lines):p.error('script must be a JSON array of 1-12 short lines')
 digest=hashlib.sha256(json.dumps(lines,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
 state_dir=ROOT/'renders'/a.id;state_dir.mkdir(parents=True,exist_ok=True);state_path=state_dir/'review-run.json'
 try:
  import requests,playwright,imageio_ffmpeg,PIL,numpy,soundfile
 except ImportError:
  subprocess.run(['bash',str(ROOT/'setup/restore-production.sh')],check=True)
  import requests
 from lib.secrets import gh_token
 session=requests.Session();session.headers.update({'Authorization':'Bearer '+gh_token(),'Accept':'application/vnd.github+json'})
 base='https://api.github.com/repos/zainkhan122/yt-tts'
 def get(path):
  r=session.get(base+path,timeout=45);r.raise_for_status();return r.json()
 state=json.loads(state_path.read_text()) if state_path.exists() else {}
 if a.resume:run=a.resume
 elif state.get('script_sha256')==digest and state.get('run_id'):run=state['run_id'];print('Resuming saved run',run,flush=True)
 else:
  if state.get('script_sha256')==digest and state.get('request_key'):
   key=state['request_key'];print('Looking for previously dispatched review',key,flush=True)
  else:
   key=uuid.uuid4().hex[:16]
   state={'script_sha256':digest,'request_key':key,'status':'dispatching'};state_path.write_text(json.dumps(state,indent=2))
   r=session.post(base+'/actions/workflows/review-voice.yml/dispatches',json={'ref':'main','inputs':{'request_key':key,'script_json':json.dumps(lines,ensure_ascii=False)}},timeout=45);r.raise_for_status()
  run=None
  for _ in range(20):
   data=get('/actions/workflows/review-voice.yml/runs?per_page=50');matches=[x for x in data.get('workflow_runs',[]) if x.get('display_title')=='House voice review '+key]
   if len(matches)==1:run=matches[0]['id'];break
   if len(matches)>1:raise SystemExit('Ambiguous voice workflow run, refusing')
   time.sleep(3)
  if not run:raise SystemExit('Dispatch outcome uncertain; check Actions before retrying or clearing the saved run state')
  state={'script_sha256':digest,'run_id':run,'request_key':key,'status':'dispatched'};state_path.write_text(json.dumps(state,indent=2));print('Voice run',run,flush=True)
 for _ in range(240):
  job=get('/actions/runs/'+str(run))
  if job['status']=='completed':
   if job['conclusion']!='success':raise SystemExit('Voice workflow did not pass: '+str(job['conclusion']))
   break
  time.sleep(15)
 else:raise SystemExit('Voice run still pending; rerun this command to resume')
 artifacts=get('/actions/runs/'+str(run)+'/artifacts')['artifacts'];matches=[x for x in artifacts if x['name']=='review-house-voice' and not x['expired']]
 if len(matches)!=1:raise SystemExit('Missing or ambiguous voice artifact')
 r=session.get(matches[0]['archive_download_url'],timeout=120);r.raise_for_status();z=zipfile.ZipFile(io.BytesIO(r.content));dest=state_dir/'voice-handoff';dest.mkdir(exist_ok=True)
 for name in ['voice.wav','timings.json']:
  hits=[x for x in z.namelist() if Path(x).name==name]
  if len(hits)!=1:raise SystemExit('Voice artifact member missing or duplicated')
  (dest/name).write_bytes(z.read(hits[0]))
 doc=json.loads((dest/'timings.json').read_text());
 if doc.get('script_sha256')!=digest or doc.get('overall_match',0)<.95 or doc.get('engine')!='chatterbox':raise SystemExit('Voice artifact mismatch or failed voice QA')
 subprocess.run([sys.executable,str(renderer)],cwd=ROOT,check=True)
 print('Review assembly completed. No publish/schedule. Production QA, rights and cover approval remain required.')
if __name__=='__main__':main()
