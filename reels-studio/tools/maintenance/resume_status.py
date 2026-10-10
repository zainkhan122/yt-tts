#!/usr/bin/env python3
"""Read-only operational handoff; no API calls, inference, rendering or publishing.
Run this first after restoring the public SSOT. Secret values are never displayed.
"""
import argparse
import collections
import datetime as dt
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from lib.secrets import secure_vault
secure_vault()


def read(path,default=None):
    p=ROOT/path
    return json.loads(p.read_text()) if p.exists() else default


def snapshot():
    pub=read('config/publishing.json',{});yt=read('config/youtube.json',{});agent=read('config/agent-pilot.json',{})
    q=read('queue/publish.json',{'items':[]})['items'];journal=read('tracker/publications.json',{'records':{}})['records']
    yj=read('tracker/youtube-publications.json',{})
    private=Path.home()/'.config/reels-studio'
    try:sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    except Exception:sha='unknown'
    info={'generated_at':dt.datetime.now(dt.timezone.utc).isoformat(),'source_commit':sha,'repository':'zainkhan122/yt-tts','scope':'reels-studio + .github/workflows only',
          'buffer':{'enabled':pub.get('enabled'),'pilot_passed':pub.get('live_pilot_passed'),'timezone':pub.get('schedule',{}).get('timezone'),
                    'daily_target':pub.get('schedule',{}).get('daily_target'),'queue_approvals':dict(collections.Counter(i['approval'] for i in q)),
                    'platform_receipt_states':dict(collections.Counter(r['state'] for r in journal.values()))},
          'youtube':{'enabled':yt.get('enabled'),'long_pilot_passed':yt.get('live_pilot_passed'),'long_queue_count':len(read('queue/youtube-long.json',{'items':[]})['items']),
                     'metadata_completed':sum(r.get('state')=='done' for r in yj.get('enrichment',{}).values())},
          'optional_agent':{'production_enabled':agent.get('production_enabled'),'publishing_enabled':agent.get('publishing_enabled'),'qualification':agent.get('qualification'),
                            'paid_inference_limit_usd':agent.get('max_paid_inference_usd'),'models':{k:v.get('model') for k,v in agent.get('roles',{}).items()},
                            'model_selection_revision':agent.get('model_selection_revision',1)},
          'local_credentials_present':{name:(private/name).is_file() for name in ['gh_token','buffer_token','google_client.json','youtube_oauth.json','youtube_state_key','openrouter_token']},
          'important':['A missing local OpenRouter key is expected when it is stored ONLY in Actions Secrets; do not ask for it again without checking secret metadata.',
                       'Never re-upload a video with an existing platform receipt/reservation.',
                       'The optional producer/critic cannot publish or activate itself. Model scores are not parity certification.',
                       'A fresh conversation can restore operational state from git, not private chat reasoning. A completely new workspace still needs authorized GitHub access for writes; existing cloud jobs keep their encrypted secrets.']}
    p=private/'youtube_oauth.json'
    if p.exists():
        c=json.loads(p.read_text());expiry=c.get('refresh_token_expires_at')
        if expiry:info['youtube']['recorded_refresh_grant_expiry_utc']=dt.datetime.fromtimestamp(expiry,dt.timezone.utc).isoformat()
    return info


def markdown(info):
    b,y,a=info['buffer'],info['youtube'],info['optional_agent']
    lines=['# Hypeless — current operational state','',f"Generated: {info['generated_at']} · source commit: `{info['source_commit'][:12]}`",'',
      '| System | Actual state |','|---|---|',
      f"| Buffer delivery | enabled={b['enabled']}; verified pilot={b['pilot_passed']}; {b['daily_target']}/day in {b['timezone']} |",
      f"| Buffer queue | {b['queue_approvals']} |",f"| Platform receipts | {b['platform_receipt_states']} |",
      f"| YouTube metadata | enabled={y['enabled']}; completed receipts={y['metadata_completed']} |",
      f"| Long-form uploads | pilot passed={y['long_pilot_passed']}; queued={y['long_queue_count']} |",
      f"| OPTIONAL producer/critic | production={a['production_enabled']}; publishing={a['publishing_enabled']}; qualification={a['qualification']} |",'',
      '## Optional pilot model lock','']
    lines += [f'- {k}: `{v}`' for k,v in a['models'].items()]
    if y.get('recorded_refresh_grant_expiry_utc'):lines += ['', '**Recorded Google grant expiry:** '+y['recorded_refresh_grant_expiry_utc']]
    lines += ['', '## Resume rules']+['- '+v for v in info['important']]
    lines += ['', '## Start here','1. Read `RESUME.md` and `agent/ACCEPTANCE.md`.','2. Read the latest pilot report; inspect existing Actions runs before starting another.','3. Read `tracker/publications.json` and `tracker/youtube-publications.json` before any provider operation.','4. Never infer missing results. Preserve unknown/uncertain receipts and resolve them first.']
    return '\n'.join(lines)+'\n'


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true',help='Write sanitized CURRENT_STATE.md + tracker/system-status.json locally; commit separately')
    a=ap.parse_args();info=snapshot();text=markdown(info)
    if a.write:
        (ROOT/'CURRENT_STATE.md').write_text(text)
        (ROOT/'tracker/system-status.json').write_text(json.dumps(info,indent=2)+'\n')
    print(text)


if __name__=='__main__':main()
