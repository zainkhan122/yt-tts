#!/usr/bin/env python3
"""Pin/retrieve baseline evidence and registered media. No social credentials.
Raw capture packs are reused as a declared controlled comparison asset pool.
"""
import argparse
import hashlib
import io
import json
import os
import re
from pathlib import Path,PurePosixPath
import shutil
import subprocess
import sys
import tarfile
import zipfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from PIL import Image
from tools.post.common import config as publishing_config,save_json
from tools.post.media import asset_metadata,public_download
from tools.agent.evidence import EvidenceStore,validate_provenance
from tools.agent.openrouter_client import PilotBlocked


def download_ref(ref,root_cfg,path):
    m=asset_metadata(root_cfg,ref['id'])
    if m['name']!=ref['name'] or m['size']!=ref['size'] or (m.get('digest') and m['digest']!=ref['digest']):
        raise PilotBlocked('Pinned baseline asset changed')
    public_download(m['browser_download_url'],ref['size'],ref['digest'],path)


def safe_unpack_tar(path,dest,expected_prefix,max_bytes=150_000_000):
    dest=Path(dest);dest.mkdir(parents=True,exist_ok=True);total=0
    with tarfile.open(path,'r') as archive:
        for member in archive.getmembers():
            p=PurePosixPath(member.name)
            if p.is_absolute() or '..' in p.parts or not p.parts or p.parts[0]!=expected_prefix or member.issym() or member.islnk():
                raise PilotBlocked('Unsafe capture archive member')
            if member.isdir():continue
            if not member.isfile():raise PilotBlocked('Unsupported archive member')
            total+=member.size
            if total>max_bytes:raise PilotBlocked('Capture archive expands beyond budget')
            target=dest/Path(*p.parts[1:]);target.parent.mkdir(parents=True,exist_ok=True)
            with archive.extractfile(member) as src,target.open('wb') as out:shutil.copyfileobj(src,out)


def classify(value):
    v=value.lower()
    if 'explanatory' in v:return 'explanatory_graphic'
    if 'illustration' in v:return 'illustration'
    if 'live browser demo' in v or 'browser demo' in v:return 'recorded_demo'
    if 'demo' in v and ('official' in v or 'maker' in v):return 'maker_demo'
    if 'capture' in v:return 'screenshot'
    if 'image' in v:return 'maker_image'
    return 'unknown'


def assets_from_pack(case,path):
    path=Path(path);m=json.loads((path/'manifest.json').read_text());out={}
    for source in m.get('files',{}).values():
        name=source.get('file','')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*\.(jpg|jpeg|png|webp|mp4)',name):
            continue
        file=path/name
        if file.is_symlink():raise PilotBlocked('Symlink in capture pool')
        if not file.is_file() or file.suffix.lower() not in {'.jpg','.jpeg','.png','.webp','.mp4'}:continue
        kind=classify(source.get('kind',''))
        if kind in {'explanatory_graphic','illustration','unknown'}:continue # do not hand our authored baseline graphics to the producer
        digest='sha256:'+hashlib.sha256(file.read_bytes()).hexdigest()
        aid='a'+str(len(out)+1)
        row={'id':aid,'file':name,'kind':kind,'digest':digest,'size_bytes':file.stat().st_size,
             'source_url':source.get('source') if str(source.get('source','')).startswith('https://') else m['url'],'capture_date':m.get('captured'),'usage_basis':case['asset_policy'],
             'description':source.get('alt') or source.get('kind',''),'newly_acquired_by_candidate':False}
        if file.suffix.lower()=='.mp4':
            r=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(file)],capture_output=True,text=True,check=True,timeout=20)
            row['duration_seconds']=float(json.loads(r.stdout)['format']['duration'])
        else:
            with Image.open(file) as im:row['width'],row['height']=im.size
        validate_provenance(row);out[aid]=row
    if len(out)<2:raise PilotBlocked('Insufficient traceable assets for a comparison')
    return out


def prepare_case(case,work,cfg):
    dest=Path(work)/case['id'];dest.mkdir(parents=True,exist_ok=True)
    pcfg=publishing_config();cap=case['capture_pack'];archive=dest/'capture.tar'
    download_ref(cap,pcfg,archive);safe_unpack_tar(archive,dest/'assets',case['id']);archive.unlink()
    assets=assets_from_pack(case,dest/'assets');save_json(dest/'assets.json',assets)
    ev=EvidenceStore(case,dest/'sources',cfg['limits'])
    # Fetch before model access. Each tool read still records which source was consulted.
    failures=[]
    for source in case['sources']:
        try:ev.read_source(source['id'])
        except Exception as exc:failures.append({'id':source['id'],'error':str(exc)[:300]})
    if failures:save_json(dest/'source-failures.json',failures)
    if not any(r.get('kind')=='primary_source' for r in ev.records.values()):raise PilotBlocked('No usable primary evidence')
    if failures:raise PilotBlocked('Required source fetch failed; do not fill gaps with invention')
    save_json(dest/'evidence-index.json',ev.records)
    # Baseline brief is ONLY for the independent comparator, never producer input.
    baseline=dest/'baseline';baseline.mkdir(exist_ok=True)
    shutil.copy2(ROOT/case['baseline_brief'],baseline/'brief.json')
    pin=case['baseline'];m=asset_metadata(pcfg,pin['kit_asset_id'])
    kit=baseline/'kit.zip';public_download(m['browser_download_url'],m['size'],pin['kit_digest'],kit)
    with zipfile.ZipFile(kit) as z:
        for end in ['manifest.json','contact.jpg','cover.jpg','captions.srt','voiceover.mp3']:
            names=[n for n in z.namelist() if n.endswith('/'+end) or n==end]
            if len(names)!=1:raise PilotBlocked('Baseline kit has missing/ambiguous '+end)
            if z.getinfo(names[0]).file_size>10_000_000:raise PilotBlocked('Baseline kit member too large')
            (baseline/end).write_bytes(z.read(names[0]))
    kit.unlink()
    save_json(dest/'case.json',case)
    return {'case':case['id'],'source_count':len(ev.records),'source_failures':failures,'asset_count':len(assets),'baseline_script_hidden_from_producer':True,'asset_acquisition':'controlled reused capture pool; no claim of fresh hands-on tests'}


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--work',required=True);ap.add_argument('--cases',nargs='*');a=ap.parse_args()
    cfg=json.loads((ROOT/'config/agent-pilot.json').read_text());cases=json.loads((ROOT/'agent/cases/baseline-v1.json').read_text())['cases'];results=[]
    for c in cases:
        if a.cases and c['id'] not in a.cases:continue
        try:results.append(prepare_case(c,a.work,cfg));print(c['id'],'prepared',flush=True)
        except Exception as exc:results.append({'case':c['id'],'blocked':str(exc)[:300]});print(c['id'],'source preparation blocked',flush=True)
    save_json(Path(a.work)/'preparation.json',results)
    if not any('blocked' not in r for r in results):return 1
    return 0


if __name__=='__main__':raise SystemExit(main())
