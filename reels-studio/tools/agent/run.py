#!/usr/bin/env python3
"""Shadow authoring only: producer, critic, hard gates. Never publication."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.agent.gates import frozen_production_state,assert_production_unchanged
from tools.agent.openrouter_client import OpenRouter,PilotBlocked,usage_summary
from tools.agent.producer import produce_case
from tools.post.common import iso,now_utc,save_json,fingerprint


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--work',required=True);ap.add_argument('--pilot-id',required=True);ap.add_argument('--cases',nargs='*')
    a=ap.parse_args()
    import re
    if not re.fullmatch(r'[a-z0-9-]{1,25}',a.pilot_id):raise SystemExit('Unsafe pilot ID')
    cfg=json.loads((ROOT/'config/agent-pilot.json').read_text())
    if cfg.get('production_enabled') or cfg.get('publishing_enabled'):raise SystemExit('Optional system must remain OFF')
    if os.environ.get('BUFFER_API_KEY') or os.environ.get('YOUTUBE_OAUTH_JSON'):
        raise SystemExit('Publishing credentials must not be supplied to the pilot')
    work=Path(a.work);work.mkdir(parents=True,exist_ok=True)
    before=frozen_production_state()
    report={'pilot_id':a.pilot_id,'created_at':iso(now_utc()),'mode':'shadow_nonpublishing','qualification':'unqualified',
            'configuration_sha256':hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest(),
            'baseline_arena_monetary_cost':'unknown','cases':[],'issues':[],'publishing_writes':0,'activation_allowed':False}
    client=None
    try:
        preparation=json.loads((work/'preparation.json').read_text())
        report['cases'] += [{'case':r['case'],'status':'blocked_source','error':r['blocked']} for r in preparation if r.get('blocked')]
        client=OpenRouter(cfg,work/'inference');client.preflight()
        for path in sorted(work.glob('*/case.json')):
            case=json.loads(path.read_text())
            if a.cases and case['id'] not in a.cases:continue
            state_path=path.parent/'agent-state.json'
            if state_path.exists():
                state=json.loads(state_path.read_text())
                # No silent replay after a crash/lost model response. Owner/agent can
                # select a NEW pilot ID after inspecting prior receipts.
                if state.get('pilot')!=a.pilot_id:raise PilotBlocked('Checkpoint belongs to another pilot')
                if state.get('configuration_sha256')!=fingerprint(cfg):raise PilotBlocked('Configuration/model lock changed since checkpoint; no silent reuse')
                if state.get('status') in {'ready_for_shadow_render','blocked_quality','blocked'}:
                    report['cases'].append(state);continue
                raise PilotBlocked('Interrupted case checkpoint: inspect inference receipts before resuming')
            result=produce_case(client,case,path.parent,a.pilot_id);report['cases'].append(result)
        report['calls']=len(client.state['calls'])
        known=[r for r in client.state['calls'] if r['state']=='received']
        report['reported_model_cost_usd']=sum(float((r.get('usage') or {}).get('cost') or 0) for r in known)
        report['cost_accounting']=usage_summary(client.state['calls'])
        report['unknown_outcome_calls']=report['cost_accounting']['missing_or_uncertain_cost_receipts']
        report['ready_case_ids']=[r['case'] for r in report['cases'] if r['status']=='ready_for_shadow_render']
        report['status']='authoring_complete' if len(report['ready_case_ids'])==len(report['cases']) and report['cases'] else 'authoring_partial_or_blocked'
    except Exception as exc:
        from lib.secrets import redact
        report['issues'].append(type(exc).__name__+': '+redact(str(exc)));report['status']='blocked'
    finally:
        try:assert_production_unchanged(before);report['production_state_unchanged']=True
        except Exception as exc:report['production_state_unchanged']=False;report['issues'].append(str(exc))
        save_json(work/'authoring-report.json',report)
        md=['# Optional agent — shadow authoring report','',f"Status: **{report['status']}** · production activation: **OFF**",'',
            '| Case | Actual stage |','|---|---|']
        md += [f"| {r['case']} | {r['status']} |" for r in report['cases']]
        md += ['','No publication was attempted. Model ratings are not parity certification.','']+['- '+x for x in report['issues']]
        (work/'authoring-summary.md').write_text('\n'.join(md)+'\n')
        if os.environ.get('GITHUB_STEP_SUMMARY'):
            with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as f:f.write('\n'.join(md))
        print('\n'.join(md))
    return 0 if report.get('ready_case_ids') and not report['issues'] else 1


if __name__=='__main__':raise SystemExit(main())
