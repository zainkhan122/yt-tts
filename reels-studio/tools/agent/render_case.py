#!/usr/bin/env python3
"""Render ONE accepted shadow candidate with locked voice/brand, never publish.
Only controller-approved JSON and registered media enter the existing renderer.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.agent.evidence import validate_provenance
from tools.agent.gates import frozen_production_state,assert_production_unchanged
from tools.agent.openrouter_client import PilotBlocked
from tools.post.common import check_manifest,save_json,fingerprint


def validate_render_inputs(work):
    work=Path(work);state=json.loads((work/'agent-state.json').read_text());brief=json.loads((work/'candidate-brief.json').read_text())
    if state.get('compiled_brief_sha256')!=fingerprint(brief):raise PilotBlocked('Candidate changed after independent review')
    if state['status']!='ready_for_shadow_render' or state.get('publishing_allowed') is not False:
        raise PilotBlocked('Unaccepted candidate cannot enter the renderer')
    if not state.get('last_gate',{}).get('passed') or state.get('critic',{}).get('verdict')!='pass':
        raise PilotBlocked('Missing hard-gate / independent-critic acceptance')
    if not re.fullmatch(r'shadow-[a-z0-9-]{1,88}',brief.get('id','')) or brief['id']!=state['candidate_id']:
        raise PilotBlocked('Candidate ID must remain in the shadow namespace')
    if brief.get('template')!='tool-spotlight' or not brief.get('pilot') or brief['pilot'].get('publishing_allowed') is not False:
        raise PilotBlocked('Only the controlled shadow template is permitted')
    if any(k in brief for k in ['tts','voice','voice_fx','fps','width','height','recordings']):
        raise PilotBlocked('Model-provided render/voice override rejected')
    if brief.get('capture')!='captures/'+brief['id']:raise PilotBlocked('Capture path escape rejected')
    assets=json.loads((work/'assets.json').read_text())
    for aid in brief['pilot']['media_ids']:
        if aid not in assets:raise PilotBlocked('Unknown selected media')
        asset=assets[aid];validate_provenance(asset)
        path=work/'assets'/asset['file']
        if path.is_symlink() or not path.is_file() or 'sha256:'+hashlib.sha256(path.read_bytes()).hexdigest()!=asset['digest']:
            raise PilotBlocked('Media changed after review')
    return state,brief,assets


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--case-dir',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
    if any(os.environ.get(k) for k in ['OPENROUTER_API_KEY','BUFFER_API_KEY','YOUTUBE_OAUTH_JSON','GH_TOKEN']):
        raise SystemExit('Render stage must not receive model, social or repository-write credentials')
    before=frozen_production_state();work=Path(a.case_dir);dest=Path(a.output);dest.mkdir(parents=True,exist_ok=True)
    state,brief,assets=validate_render_inputs(work);vid=brief['id']
    target=ROOT/brief['capture'];bp=ROOT/'briefs'/(vid+'.json')
    if target.exists() or bp.exists():raise SystemExit('Refusing to overwrite existing source paths')
    target.mkdir(parents=True)
    try:
        manifest={'id':vid,'url':brief['sources'][0],'captured':'shadow-pilot','files':{},'regions_css':{},'credits':[]}
        for aid in set(brief['pilot']['media_ids']):
            asset=assets[aid];shutil.copy2(work/'assets'/asset['file'],target/asset['file'])
            manifest['files'][aid]={'file':asset['file'],'kind':asset['kind'],'source':asset['source_url']}
        save_json(target/'manifest.json',manifest);save_json(bp,brief)
        channel=json.loads((ROOT/'config/channel.json').read_text())
        tts=channel.get('tts',{})
        if tts.get('engine')!='chatterbox':raise PilotBlocked('Approved Option 3 voice is not configured')
        subprocess.run([sys.executable,str(ROOT/'reels.py'),'make',str(bp),'--quality','looks','--crf','23'],check=True,cwd=ROOT,timeout=4200)
        subprocess.run([sys.executable,str(ROOT/'tools/seo_pack.py'),str(bp)],check=True,cwd=ROOT,timeout=60)
        rendered=ROOT/'renders'/vid
        qa=json.loads((rendered/'manifest.json').read_text());check_manifest(qa,vid)
        for p in rendered.iterdir():
            if p.is_file() and p.suffix in {'.mp4','.mp3','.json','.jpg','.srt','.md'}:shutil.copy2(p,dest/p.name)
        save_json(dest/'pilot-receipt.json',{'candidate_id':vid,'case':state['case'],'technical_checks':qa['qa']['checks'],'status':'rendered_unapproved_for_publication','publishing_allowed':False})
    finally:
        bp.unlink(missing_ok=True);shutil.rmtree(target,ignore_errors=True)
        assert_production_unchanged(before)
    print('Shadow render complete. No upload, queue insertion or publication performed.')


if __name__=='__main__':main()
