#!/usr/bin/env python3
"""Resume ONLY an explicitly rate-rejected critic call on an unchanged accepted draft.
No producer replay, model switch, gate waiver, or production mutation.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.agent.openrouter_client import OpenRouter,PilotBlocked,usage_summary
from tools.agent.evidence import EvidenceStore
from tools.agent.gates import validate_draft,frozen_production_state,assert_production_unchanged
from tools.agent.producer import compile_brief,review
from tools.post.common import load_json,save_json,fingerprint,iso,now_utc


def validate_resume(state,gate,calls,cfg,case_id):
    if state.get('configuration_sha256')!=fingerprint(cfg):raise PilotBlocked('Configuration changed; cannot silently resume')
    if state.get('status')!='blocked' or not state.get('error','').startswith('FreeQuotaDeferred:'):
        raise PilotBlocked('Only explicit quota rejection can be safely resumed this way')
    if not gate.get('passed'):raise PilotBlocked('Draft never passed the hard gates')
    label=case_id+':critic:'+str(state['revision'])
    matching=[c for c in calls if c.get('label')==label]
    if not matching or any(c.get('state')!='rejected_rate_limit' for c in matching):
        raise PilotBlocked('Critic outcome may be uncertain; do not replay it blindly')


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--work',required=True);ap.add_argument('--case',required=True);a=ap.parse_args()
    work=Path(a.work);cfg=load_json(ROOT/'config/agent-pilot.json');known={c['id'] for c in load_json(ROOT/'agent/cases/baseline-v1.json')['cases']}
    if a.case not in known:raise SystemExit('Unregistered case')
    before=frozen_production_state();report={'case':a.case,'ready':False,'publishing_allowed':False,'producer_replayed':False}
    try:
        case_dir=work/a.case;state=load_json(case_dir/'agent-state.json');case=load_json(case_dir/'case.json')
        rev=case_dir/f"revision-{state['revision']}";gate=load_json(rev/'hard-gates.json');draft=load_json(rev/'draft.json')
        calls=load_json(work/'inference/calls.json')['calls'];validate_resume(state,gate,calls,cfg,a.case)
        conversation=load_json(case_dir/'producer-conversation.json')
        submitted=[]
        for message in conversation:
            if message.get('role')=='assistant':
                for call in message.get('tool_calls',[]):
                    if call.get('function',{}).get('name')=='submit_draft':submitted.append(json.loads(call['function']['arguments']))
        if not submitted or fingerprint(submitted[-1])!=fingerprint(draft):
            raise PilotBlocked('Draft differs from the last recorded producer submission')
        assets=load_json(case_dir/'assets.json');evidence=EvidenceStore(case,case_dir/'sources',cfg['limits']);evidence.records=load_json(case_dir/'evidence-index.json');evidence.read_ids=set(state['sources_read'])
        new_gate=validate_draft(draft,evidence,assets)
        if not new_gate['passed']:raise PilotBlocked('Rechecked hard gates failed: '+'; '.join(new_gate['errors']))
        client=OpenRouter(cfg,work/'inference');client.preflight()
        accepted,critic,errors=review(client,draft,evidence,assets,rev,a.case+':critic:'+str(state['revision']))
        if accepted:
            compiled=compile_brief(draft,case,assets,state['pilot'],state['revision']);save_json(case_dir/'candidate-brief.json',compiled)
            state.update(status='ready_for_shadow_render',candidate_id=compiled['id'],compiled_brief_sha256=fingerprint(compiled),last_gate=new_gate,critic=critic,finished_at=iso(now_utc()),publishing_allowed=False)
            state.pop('error',None);save_json(case_dir/'agent-state.json',state)
            report.update(ready=True,candidate_id=compiled['id'])
            author=load_json(work/'authoring-report.json')
            author['cases']=[state if row['case']==a.case else row for row in author['cases']]
            author['ready_case_ids']=[a.case]
            author['resumed_critic_only_at']=iso(now_utc())
            save_json(work/'authoring-report.json',author)
        else:
            state.update(status='blocked_quality',critic=critic,error='Independent critic did not approve',publishing_allowed=False);save_json(case_dir/'agent-state.json',state)
            report['error']='Independent critic rejected the draft'
        report['cost_accounting']=usage_summary(client.state['calls'])
    except Exception as exc:
        from lib.secrets import redact
        report['error']=type(exc).__name__+': '+redact(str(exc))
    finally:
        assert_production_unchanged(before);save_json(work/'critic-resume-report.json',report);print(json.dumps(report,indent=2))
    return 0 if report['ready'] else 1


if __name__=='__main__':raise SystemExit(main())
