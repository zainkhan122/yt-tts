"""Review-only house voice through existing review-voice workflow; no publishing."""
import hashlib,io,json,time,uuid,zipfile
from pathlib import Path
import requests
from lib.secrets import gh_token

ROOT=Path(__file__).resolve().parents[3];D=ROOT/'graphics/production/rgbmocap_short';STATE=D/'voice-request.json';SCRIPT=D/'narration.json'
def main():
    lines=json.loads(SCRIPT.read_text());fingerprint=hashlib.sha256(json.dumps(lines,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
    token=gh_token()
    if not token:raise RuntimeError('House voice workflow credential unavailable')
    s=requests.Session();s.headers.update({'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'});base='https://api.github.com/repos/zainkhan122/yt-tts'
    if STATE.exists():
        state=json.loads(STATE.read_text());assert state['script_sha256']==fingerprint
    else:
        state={'script_sha256':fingerprint,'key':uuid.uuid4().hex[:16],'run_id':None,'status':'dispatching'};STATE.write_text(json.dumps(state,indent=2));r=s.post(base+'/actions/workflows/review-voice.yml/dispatches',json={'ref':'main','inputs':{'request_key':state['key'],'script_json':json.dumps(lines,ensure_ascii=False)}},timeout=45);r.raise_for_status()
    run=state['run_id']
    if not run:
        for _ in range(30):
            r=s.get(base+'/actions/workflows/review-voice.yml/runs?per_page=100',timeout=45);r.raise_for_status();matches=[x for x in r.json()['workflow_runs'] if x['display_title']=='House voice review '+state['key']]
            if len(matches)>1:raise RuntimeError('Ambiguous voice run, no redispatch')
            if matches:run=matches[0]['id'];break
            time.sleep(3)
        if not run:raise RuntimeError('Voice dispatch uncertain, no redispatch')
        state.update(run_id=run,status='dispatched');STATE.write_text(json.dumps(state,indent=2))
    print('House voice workflow run',run,flush=True)
    for _ in range(240):
        r=s.get(base+'/actions/runs/'+str(run),timeout=45);r.raise_for_status();data=r.json()
        if data['status']=='completed':
            if data['conclusion']!='success':raise RuntimeError('Voice generation failed: '+str(data['conclusion']))
            break
        time.sleep(15)
    else:raise RuntimeError('Voice generation pending')
    r=s.get(base+'/actions/runs/'+str(run)+'/artifacts',timeout=45);r.raise_for_status();a=[x for x in r.json()['artifacts'] if x['name']=='review-house-voice' and not x['expired']]
    if len(a)!=1:raise RuntimeError('Missing or ambiguous voice artifact')
    r=s.get(a[0]['archive_download_url'],timeout=120);r.raise_for_status();z=zipfile.ZipFile(io.BytesIO(r.content))
    for name in ['voice.wav','timings.json']:
        hits=[n for n in z.namelist() if Path(n).name==name]
        if len(hits)!=1:raise RuntimeError('Missing voice file')
        (D/name).write_bytes(z.read(hits[0]))
    doc=json.loads((D/'timings.json').read_text())
    if doc.get('script_sha256')!=fingerprint or doc.get('overall_match',0)<.95 or doc.get('engine')!='chatterbox':raise RuntimeError('House voice handoff failed QA')
    state['status']='complete';STATE.write_text(json.dumps(state,indent=2));print('Approved house voice ready; match',doc['overall_match'],'duration',doc['duration'],flush=True)
if __name__=='__main__':main()
