import sys,time,json,requests,zipfile,io
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));from lib.secrets import gh_token
base='https://api.github.com/repos/zainkhan122/yt-tts';s=requests.Session();s.headers.update({'Authorization':'Bearer '+gh_token(),'Accept':'application/vnd.github+json'})
out=Path('renders/repo-gta6-clipper-01');run=json.loads((out/'voice-run.json').read_text())['run_id']
for i in range(200):
 r=s.get(f'{base}/actions/runs/{run}',timeout=30);r.raise_for_status();data=r.json();print('Voice workflow:',data['status'],data.get('conclusion'),flush=True)
 if data['status']=='completed':
  if data['conclusion']!='success':
   j=s.get(f'{base}/actions/runs/{run}/jobs',timeout=30).json()
   for job in j.get('jobs',[]):
    for step in job.get('steps',[]):
     if step.get('conclusion')=='failure':print('Failed step:',step['name'],flush=True)
   sys.exit(1)
  a=s.get(f'{base}/actions/runs/{run}/artifacts',timeout=30).json()['artifacts'];a=next(x for x in a if x['name']=='review-house-voice');r=s.get(a['archive_download_url'],timeout=90);r.raise_for_status();z=zipfile.ZipFile(io.BytesIO(r.content));target=out/'voice-handoff';target.mkdir(exist_ok=True)
  for name in ['voice.wav','timings.json']:
   names=[n for n in z.namelist() if Path(n).name==name]
   if len(names)!=1:raise SystemExit('Missing or duplicate artifact member '+name)
   (target/name).write_bytes(z.read(names[0]))
  print('Voice artifact downloaded and retained locally',flush=True);sys.exit(0)
 time.sleep(15)
sys.exit('Timed out waiting for voice workflow')
