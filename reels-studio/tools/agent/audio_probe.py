#!/usr/bin/env python3
"""Test the pinned audio specialist on a real EXISTING studio narration clip.
This is a modality test, not a candidate/baseline comparison or qualification.
No transcript is sent to the model, and no new video/publication is created.
"""
import argparse
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.agent.compare import excerpt_matches
from tools.agent.openrouter_client import OpenRouter,PilotBlocked,usage_summary
from tools.agent.producer import tool,args_for
from tools.post.common import load_json,save_json,iso,now_utc
from tools.post.media import asset_metadata,public_download

SCHEMA={'type':'object','properties':{
 'audio_actually_assessed':{'type':'boolean'},
 'heard_excerpt':{'type':'string','minLength':15,'maxLength':500},
 'observations':{'type':'array','maxItems':8,'items':{'type':'string','maxLength':400}},
 'limitations':{'type':'string','maxLength':700}},
 'required':['audio_actually_assessed','heard_excerpt','observations','limitations'],'additionalProperties':False}


def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--work',required=True);a=ap.parse_args()
 work=Path(a.work);work.mkdir(parents=True,exist_ok=True)
 report={'mode':'baseline_audio_capability_only','created_at':iso(now_utc()),'candidate_video_created':False,'publishing_allowed':False,'qualification':'not_evaluated','issues':[]}
 client=None
 try:
  cfg=load_json(ROOT/'config/agent-pilot.json');cases=load_json(ROOT/'agent/cases/baseline-v1.json')['cases']
  case=next(c for c in cases if c['id']=='news-haiku-55-01');pin=case['baseline']
  repo=load_json(ROOT/'config/publishing.json');meta=asset_metadata(repo,pin['kit_asset_id'])
  _,_,blob=public_download(meta['browser_download_url'],meta['size'],pin['kit_digest'])
  with zipfile.ZipFile(io.BytesIO(blob)) as archive:
   names=[n for n in archive.namelist() if n.endswith('/voiceover.mp3') or n=='voiceover.mp3']
   if len(names)!=1 or archive.getinfo(names[0]).file_size>3_000_000:raise PilotBlocked('Invalid baseline voice artifact')
   audio=archive.read(names[0])
  client=OpenRouter(cfg,work/'inference');client.preflight()
  request=[{'type':'text','text':'Listen to the attached synthetic narration. Return a verbatim excerpt of at least eight consecutive words that you actually heard, plus brief observations about intelligibility and delivery. No transcript is provided. If audio is unavailable, say so honestly.'},
           {'type':'input_audio','input_audio':{'data':base64.b64encode(audio).decode(),'format':'mp3'}}]
  name='submit_audio_observation'
  response=client.chat('audio_critic',[{'role':'system','content':'You are an audio reviewer of a public synthetic studio narration clip. Do not guess a transcript. Use the reporting tool; no hidden chain-of-thought is needed.'},{'role':'user','content':request}],
   tools=[tool(name,'Report actual listening evidence, not a claimed quality pass.',SCHEMA)],tool_choice={'type':'function','function':{'name':name}},max_tokens=2200,label='baseline_audio_modality_check')
  calls=response.get('tool_calls') or []
  if len(calls)!=1:raise PilotBlocked('Audio reviewer did not return one reporting tool call')
  result=args_for(calls[0],name)
  from jsonschema import Draft202012Validator
  errs=list(Draft202012Validator(SCHEMA).iter_errors(result))
  if errs:raise PilotBlocked('Audio response schema failed')
  brief=load_json(ROOT/case['baseline_brief']) # used only locally for validation, not in the prompt
  matched=excerpt_matches(result['heard_excerpt'],brief)
  report.update(result=result,heard_excerpt_matches_known_recording=matched,success=result['audio_actually_assessed'] and matched,
   input_audio_sha256=hashlib.sha256(audio).hexdigest(),baseline_case=case['id'])
  if not report['success']:report['issues'].append('Audio capability was not established from actual listening evidence')
 except Exception as exc:
  from lib.secrets import redact
  report.update(success=False);report['issues'].append(type(exc).__name__+': '+redact(str(exc)))
 if client:report['cost_accounting']=usage_summary(client.state['calls'])
 save_json(work/'audio-probe-report.json',report)
 md='# Optional audio specialist capability test\n\n'+json.dumps(report,indent=2)+'\n\nNot a comparison verdict. No candidate video or social post was created.\n'
 (work/'summary.md').write_text(md)
 if os.environ.get('GITHUB_STEP_SUMMARY'):
  with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as f:f.write(md)
 print('Pinned free audio capability:', 'PASS' if report.get('success') else 'NOT ESTABLISHED')
 for issue in report['issues']:print(issue)
 return 0 if report.get('success') else 1


if __name__=='__main__':raise SystemExit(main())
