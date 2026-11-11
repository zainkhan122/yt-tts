#!/usr/bin/env python3
"""Independent, anonymously ordered text/frame/audio comparison. NEVER promotion.
A model's preference is a signal; owner review and unseen cases remain mandatory.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import sys

from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.agent.openrouter_client import OpenRouter,PilotBlocked,json_content,usage_summary
from tools.agent.producer import tool,args_for
from tools.post.common import check_manifest,iso,now_utc,save_json


def obj(properties):return {'type':'object','properties':properties,'required':list(properties),'additionalProperties':False}
SCORE={'type':'integer','minimum':0,'maximum':4}
TEXT={'type':'string','maxLength':1800}
VISUAL_SCHEMA=obj({'images_actually_assessed':{'type':'boolean'},'A':obj({k:SCORE for k in ['facts','authenticity','script','visuals']}),
 'B':obj({k:SCORE for k in ['facts','authenticity','script','visuals']}),
 'material_issues':{'type':'array','maxItems':20,'items':obj({'label':{'enum':['A','B','both']},'finding':TEXT,'evidence_reference':TEXT})},'limitations':TEXT,'summary':TEXT})
AUDIO_SCHEMA=obj({'audio_actually_assessed':{'type':'boolean'},'A':obj({'intelligibility':SCORE,'natural_flow':SCORE,'pronunciation':SCORE,'heard_excerpt':TEXT}),
 'B':obj({'intelligibility':SCORE,'natural_flow':SCORE,'pronunciation':SCORE,'heard_excerpt':TEXT}),'issues':{'type':'array','maxItems':10,'items':TEXT},'limitations':TEXT})


def parse_review(message,name,schema):
    calls=message.get('tool_calls') or []
    result=args_for(calls[0],name) if len(calls)==1 else json_content(message)
    errors=list(Draft202012Validator(schema).iter_errors(result))
    if errors:raise PilotBlocked('Comparison response fails schema: '+errors[0].message[:200])
    return result


def spoken_only(value):
    return re.sub(r"\{[^{}|]+\|([^{}]+)\}",r"\1",value or '')


def visible_brief(brief):
    # Hide implementation IDs and trailing provenance labels that would reveal
    # which side is the shadow candidate; retain the substantive public copy.
    description=re.split(r"\n\s*(?:Sources?|Credits|Media|Footage):",brief['seo']['youtube']['description'],maxsplit=1,flags=re.I)[0]
    scenes=[]
    for n,scene in enumerate(brief['scenes'],1):
        row={k:scene.get(k) for k in ['headline','heading','sub','type']}
        row.update(scene_number=n,say=spoken_only(scene.get('say','')))
        scenes.append(row)
    return {'title':brief['seo']['youtube']['title'],'description':description,'scenes':scenes}


def excerpt_matches(excerpt,brief):
    # Audio reviewer receives no transcript. Require a recognizable phrase from
    # the actual script, not merely its own boolean claim that it listened.
    def words(s):return re.findall(r"[a-z]+",spoken_only(s).lower())
    said=words(' '.join(s.get('say','') for s in brief['scenes']))
    heard=words(excerpt)
    if len(heard)<5:return False
    source={' '.join(said[n:n+5]) for n in range(max(0,len(said)-4))}
    return any(' '.join(heard[n:n+5]) in source for n in range(len(heard)-4))


def image_part(path):
    from PIL import Image
    import io
    with Image.open(path) as source:
        im=source.convert('RGB');im.thumbnail((1560,1600));buf=io.BytesIO();im.save(buf,'JPEG',quality=88)
    return {'type':'image_url','image_url':{'url':'data:image/jpeg;base64,'+base64.b64encode(buf.getvalue()).decode()}}


def compare_case(client,case_dir,candidate_dir,pilot_id):
    case_dir=Path(case_dir);candidate_dir=Path(candidate_dir);case=json.loads((case_dir/'case.json').read_text());state=json.loads((case_dir/'agent-state.json').read_text())
    actual=json.loads((candidate_dir/'manifest.json').read_text());check_manifest(actual,state['candidate_id'])
    baseline=case_dir/'baseline';baseline_manifest=json.loads((baseline/'manifest.json').read_text())
    base_brief=json.loads((baseline/'brief.json').read_text());cand_brief=json.loads((case_dir/'candidate-brief.json').read_text())
    evidence=json.loads((case_dir/'evidence-index.json').read_text())
    candidate_is_A=int(hashlib.sha256((pilot_id+case['id']).encode()).hexdigest(),16)%2==0
    choices=[(cand_brief,candidate_dir),(base_brief,baseline)] if candidate_is_A else [(base_brief,baseline),(cand_brief,candidate_dir)]
    text={'task':'Blind paired comparison. Do not guess provenance or favor an expected winner. Check all facts against evidence. Visuals must be judged from the supplied images.',
          'A':visible_brief(choices[0][0]),'B':visible_brief(choices[1][0]),'evidence':evidence}
    content=[{'type':'text','text':json.dumps(text,ensure_ascii=False)}, {'type':'text','text':'A — actual contact sheet'},image_part(choices[0][1]/'contact.jpg'),{'type':'text','text':'B — actual contact sheet'},image_part(choices[1][1]/'contact.jpg')]
    name='submit_pair_comparison';t=tool(name,'Submit independent paired evidence/script/image ratings.',VISUAL_SCHEMA)
    result=client.chat('critic',[{'role':'system','content':(ROOT/'agent/prompts/critic-v1.md').read_text()},{'role':'user','content':content}],tools=[t],tool_choice={'type':'function','function':{'name':name}},label=case['id']+':paired_visual')
    visual=parse_review(result,name,VISUAL_SCHEMA)
    if not visual['images_actually_assessed']:raise PilotBlocked('Critic did not assess actual images')
    audio=None;audio_issue=None
    try:
        parts=[{'type':'text','text':'Independently compare the TWO actual synthetic narration clips A and B. Assess intelligibility, natural flow and pronunciation. Include a short phrase you actually heard in each. Do not invent listening if audio cannot be processed; report that limitation. No transcripts are supplied.'}]
        for label,(_,folder) in zip(['A','B'],choices):
            file=folder/'voiceover.mp3'
            if not file.exists():raise PilotBlocked('Voiceover missing; audio comparison cannot be claimed')
            parts += [{'type':'text','text':'Audio '+label},{'type':'input_audio','input_audio':{'data':base64.b64encode(file.read_bytes()).decode(),'format':'mp3'}}]
        name='submit_audio_comparison';t=tool(name,'Submit independent audio listening findings.',AUDIO_SCHEMA)
        message=client.chat('audio_critic',[{'role':'system','content':'You are a separate audio critic. Evaluate actual clips, not filenames. Report uncertainty. Return findings with the reporting tool.'},{'role':'user','content':parts}],tools=[t],tool_choice={'type':'function','function':{'name':name}},label=case['id']+':paired_audio')
        audio=parse_review(message,name,AUDIO_SCHEMA)
        if not audio['audio_actually_assessed']:audio_issue='Audio modality not actually assessed'
        elif not all(excerpt_matches(audio[label]['heard_excerpt'],brief) for label,(brief,_) in zip(['A','B'],choices)):
            audio_issue='Listening evidence is insufficient: the quoted audio excerpts do not match the supplied narration'

    except Exception as exc:audio_issue=type(exc).__name__+': '+str(exc)
    candidate='A' if candidate_is_A else 'B';base='B' if candidate_is_A else 'A'
    noninferior=not visual['material_issues'] and all(visual[candidate][k]>=visual[base][k] for k in ['facts','authenticity','script','visuals'])
    if audio and not audio_issue:
        noninferior &= all(audio[candidate][k]>=audio[base][k] for k in ['intelligibility','natural_flow','pronunciation'])
    else:noninferior=False
    return {'case':case['id'],'labels':{'candidate':candidate,'baseline':base},'visual_review':visual,'audio_review':audio,'audio_issue':audio_issue,
            'candidate_qa':actual['qa'],'baseline_qa':baseline_manifest['qa'],
            'candidate_voice_audit':actual['stages']['voice'],'baseline_voice_audit':baseline_manifest['stages']['voice'],
            'recorded_repairs':state.get('repairs',[]),'model_noninferiority_signal':bool(noninferior),
            'qualification':'owner_review_required' if noninferior else 'not_qualified',
            'publishing_allowed':False,'limitations':['Matched existing asset pool plus fresh page captures; autonomous novel-topic discovery/rights judgement is not proven.','Model scores do not certify accuracy or general parity.','Baseline Arena monetary cost is unavailable.']}


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--work',required=True);ap.add_argument('--renders',required=True);a=ap.parse_args()
    work=Path(a.work);dest=work/'comparison';dest.mkdir(parents=True,exist_ok=True)
    cfg=json.loads((ROOT/'config/agent-pilot.json').read_text());author=json.loads((work/'authoring-report.json').read_text())
    report={'pilot_id':author['pilot_id'],'created_at':iso(now_utc()),'qualification':'not_qualified','activation_allowed':False,'publishing_writes':0,'cases':[],'issues':[],'baseline_arena_monetary_cost':'unknown'}
    try:
        client=OpenRouter(cfg,work/'inference');client.preflight()
        for case in author['cases']:
            cid=case['case']
            if case['status']!='ready_for_shadow_render':report['cases'].append({'case':cid,'qualification':'not_qualified','reason':case['status']});continue
            receipts=list(Path(a.renders).rglob('pilot-receipt.json'))
            matches=[p.parent for p in receipts if json.loads(p.read_text()).get('case')==cid]
            if len(matches)!=1:report['cases'].append({'case':cid,'qualification':'not_qualified','reason':'missing/ambiguous shadow render receipt'});continue
            try:
                result=compare_case(client,work/cid,matches[0],author['pilot_id']);report['cases'].append(result);save_json(dest/(cid+'.json'),result)
            except Exception as exc:report['cases'].append({'case':cid,'qualification':'not_qualified','reason':type(exc).__name__+': '+str(exc)})
        report['reported_model_cost_usd']=sum(float((c.get('usage') or {}).get('cost') or 0) for c in client.state['calls'] if c['state']=='received')
        report['inference_calls']=len(client.state['calls'])
        report['cost_accounting']=usage_summary(client.state['calls'])
        if len(report['cases'])==len(cfg['baseline_cases']) and all(c['qualification']=='owner_review_required' for c in report['cases']):
            report['qualification']='comparison_signal_only_pending_owner_and_unseen_cases'
    except Exception as exc:report['issues'].append(type(exc).__name__+': '+str(exc))
    save_json(dest/'comparison-report.json',report)
    lines=['# Optional producer/critic comparison','',f"Qualification: **{report['qualification']}**. Activation remains **OFF**.",'','| Case | Result |','|---|---|']
    lines += [f"| {r['case']} | {r['qualification']} — {r.get('reason','independent paired review recorded')} |" for r in report['cases']]
    lines += ['','Model ratings are evidence, not a certification of human-level quality. No automatic promotion exists.','']+['- '+x for x in report['issues']]
    (dest/'comparison-report.md').write_text('\n'.join(lines)+'\n')
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as f:f.write('\n'.join(lines))
    print('\n'.join(lines))
    return 0 if not report['issues'] else 1


if __name__=='__main__':raise SystemExit(main())
