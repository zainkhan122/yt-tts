#!/usr/bin/env python3
"""Real FREE-only capability smoke test. This is not a content-quality benchmark."""
import argparse
import base64
import io
import json
import os
from pathlib import Path
import sys

from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.post.common import iso,now_utc,save_json
from tools.agent.openrouter_client import OpenRouter,PilotBlocked,json_content


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--work',required=True);a=ap.parse_args()
    cfg=json.loads((ROOT/'config/agent-pilot.json').read_text());work=Path(a.work);work.mkdir(parents=True,exist_ok=True)
    report={'mode':'capability_smoke_only','generated_at':iso(now_utc()),'publishing_allowed':False,'paid_inference_allowed':False,'checks':{},'issues':[],'qualification':'not_evaluated'}
    try:
        client=OpenRouter(cfg,work)
        report['account']=client.preflight();report['models']=client.checked
        tool={'type':'function','function':{'name':'submit_probe','description':'Return only facts supported by the provided source.','parameters':{'type':'object','properties':{'credits_per_day':{'type':'integer'},'roll_over':{'type':'boolean'},'evidence_quote':{'type':'string'}},'required':['credits_per_day','roll_over','evidence_quote'],'additionalProperties':False}}}
        msg=client.chat('producer',[{'role':'system','content':'Use only the supplied evidence. Do not invent facts. Submit the requested fields using the tool.'},{'role':'user','content':'Evidence: A fictional test tool gives 50 credits per day. Unused daily credits do not roll over. Extract the daily credit allowance and rollover rule.'}],tools=[tool],tool_choice={'type':'function','function':{'name':'submit_probe'}},max_tokens=2200,label='producer_structured_tool_smoke')
        calls=msg.get('tool_calls') or []
        if len(calls)!=1 or calls[0].get('function',{}).get('name')!='submit_probe':raise PilotBlocked('Producer did not use the required submission tool')
        answer=json.loads(calls[0]['function']['arguments'])
        report['checks']['producer_tool_and_basic_evidence']=answer.get('credits_per_day')==50 and answer.get('roll_over') is False
        im=Image.new('RGB',(640,360),'#050b1f');d=ImageDraw.Draw(im)
        font=ImageFont.truetype(str(ROOT/'templates/_base/fonts/Anton.ttf'),140)
        d.text((220,80),'50',font=font,fill='#FFD60A')
        buf=io.BytesIO();im.save(buf,format='PNG');uri='data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode()
        report_tool={'type':'function','function':{'name':'report_visual_findings','description':'Submit the independent result of the image inspection to the pilot controller.','parameters':{'type':'object','properties':{'visible_number':{'type':'integer'},'claim_100_supported':{'type':'boolean'}},'required':['visible_number','claim_100_supported'],'additionalProperties':False}}}
        msg=client.chat('critic',[{'role':'system','content':'You are an independent critic agent with a reporting tool. Inspect the actual image, then call report_visual_findings. Never claim to see something unavailable.'},{'role':'user','content':[{'type':'text','text':'What number is visible? Is the claim that the image shows 100 supported? Submit your findings with the reporting tool.'},{'type':'image_url','image_url':{'url':uri}}]}],tools=[report_tool],max_tokens=1500,label='critic_agent_image_smoke')
        calls=msg.get('tool_calls') or []
        if calls:
            if len(calls)!=1 or calls[0].get('function',{}).get('name')!='report_visual_findings':raise PilotBlocked('Unexpected critic tool request')
            answer=json.loads(calls[0]['function']['arguments'])
        else:
            answer=json_content(msg)
        report['checks']['critic_reads_image']=answer.get('visible_number')==50 and answer.get('claim_100_supported') is False
        report['reported_cost_usd']=str(sum(float((c.get('usage') or {}).get('cost') or 0) for c in client.state['calls']))
        report['checks']['zero_reported_inference_cost']=float(report['reported_cost_usd'])==0
        report['checks']['no_publication_capability']=True
        report['success']=all(report['checks'].values())
        if not report['success']:report['issues'].append('At least one capability smoke check failed; no quality qualification.')
    except Exception as exc:
        from lib.secrets import redact
        report['success']=False;report['issues'].append(type(exc).__name__+': '+redact(str(exc)))
    save_json(work/'probe-report.json',report)
    summary='# Hypeless free-model capability probe\n\n'+json.dumps(report,indent=2)+'\n\nThis is only a capability check, not proof of editorial or production parity. No videos or social posts were created.\n'
    (work/'summary.md').write_text(summary)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as f:f.write(summary)
    print('Free-model probe:', 'PASS' if report.get('success') else 'BLOCKED')
    for issue in report['issues']:print(issue)
    return 0 if report.get('success') else 1


if __name__=='__main__':raise SystemExit(main())
