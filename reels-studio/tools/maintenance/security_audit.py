#!/usr/bin/env python3
"""Sanitized secret/boundary audit. Never prints values or matching source lines.
Only inspects the allowed studio/workflow paths; no other project is touched.
"""
import argparse
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from lib.secrets import contains_secret,gh_token,VAULT_PERMISSION_REPAIRS
from tools.post.common import iso,now_utc,save_json


def run(cloud=False):
    private=Path.home()/'.config/reels-studio'
    checks={"restored_vault_permission_repairs":list(VAULT_PERMISSION_REPAIRS)};issues=[]
    if private.exists():
        checks['vault_directory_mode']=oct(stat.S_IMODE(private.stat().st_mode))
        if stat.S_IMODE(private.stat().st_mode)!=0o700:issues.append('Private vault directory is not mode 700')
        bad=[]
        for p in private.iterdir():
            if p.is_symlink():bad.append(p.name+' (symlink)')
            elif p.is_file() and stat.S_IMODE(p.stat().st_mode)!=0o600:bad.append(p.name)
        checks['private_file_permission_issues']=bad
        if bad:issues.append('Some private files are not regular mode-600 files')
    else:checks['vault_directory_mode']='absent; cloud secrets may still exist'
    paths=subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard','--','reels-studio/','.github/workflows/'],cwd=ROOT.parent).split(b'\0')
    scanned=0;hits=[]
    for raw in set(p for p in paths if p):
        path=ROOT.parent/raw.decode()
        if not path.is_file() or path.is_symlink():continue
        if path.stat().st_size>5_000_000:
            issues.append('Oversized source file requires separate review: '+raw.decode());continue
        data=path.read_bytes().decode('utf-8',errors='ignore')
        scanned+=1
        if contains_secret(data):hits.append(raw.decode())
    checks['source_files_scanned']=scanned;checks['credential_pattern_or_known_value_hits']=hits
    if hits:issues.append('Credential-like content found; filenames only, never print contents')
    try:
        remote=subprocess.check_output(['git','remote','get-url','origin'],cwd=ROOT,text=True).strip()
        checks['remote_has_embedded_credentials']='@' in remote.split('://',1)[-1].split('/',1)[0]
        if checks['remote_has_embedded_credentials']:issues.append('Git remote URL contains embedded credentials')
    except Exception:checks['remote_has_embedded_credentials']='unknown'
    for name in ['agent-probe.yml','agent-pilot.yml']:
        p=ROOT.parent/'.github/workflows'/name
        if not p.exists():continue
        text=p.read_text()
        forbidden=['BUFFER_API_KEY','YOUTUBE_OAUTH_JSON','YOUTUBE_STATE_KEY','publish_release.py','tools/post/publisher.py','contents: write','pages: write','cron:']
        found=[v for v in forbidden if v in text]
        checks[name]={'forbidden_publishing_capabilities':found,'credential_persistence_disabled':'persist-credentials: false' in text}
        if found or 'persist-credentials: false' not in text:issues.append(name+': optional-pilot isolation review failed')
    if cloud:
        import requests
        token=gh_token()
        if not token:issues.append('Cloud secret metadata cannot be checked without authorized GitHub access')
        else:
            r=requests.get('https://api.github.com/repos/zainkhan122/yt-tts/actions/secrets?per_page=100',headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'},timeout=25)
            if r.status_code==200:
                names={v['name'] for v in r.json().get('secrets',[])}
                checks['encrypted_actions_secrets_present']={n:n in names for n in ['BUFFER_API_KEY','YOUTUBE_OAUTH_JSON','YOUTUBE_STATE_KEY','OPENROUTER_API_KEY']}
                if not all(checks['encrypted_actions_secrets_present'].values()):issues.append('An expected encrypted Actions secret is absent')
            else:issues.append('Cannot read cloud secret metadata: HTTP '+str(r.status_code))
    return {'checked_at':iso(now_utc()),'checks':checks,'issues':issues,'passed':not issues,
            'limits':'Pattern/known-value audit of current allowed source files, not a guarantee about unknown credentials or every historical log. Secret values were not retrieved from Actions or printed.'}


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cloud',action='store_true');ap.add_argument('--report');a=ap.parse_args()
    report=run(a.cloud)
    if a.report:save_json(a.report,report)
    print(json.dumps(report,indent=2));return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
