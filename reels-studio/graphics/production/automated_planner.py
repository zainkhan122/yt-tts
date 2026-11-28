"""Narration-to-layer planning orchestrator. No network, model or auth bypass.

A caller-supplied adapter performs inference; this module checks its response,
uses the existing strict scheduler and passes mapped instructions to the existing
layer renderer. Actual outputs still require human semantic and audiovisual QA.
"""
from __future__ import annotations
import copy
import re
from .alignment import require_verified
from .semantic import validate_plan, PlanningError
from .scheduler import schedule
from .layer_renderer import OPS, EASING, compile_timeline

TRANSITIONS={'cut','fade'}
CAMERAS={'hold','push','pull'}
GENERIC=re.compile(r'^\s*(show|animate|display|illustrate|visualize)\s+(?:an?\s+|the\s+)?(?:[\w-]+\s*){1,2}[.!]?\s*$',re.I)

class AutomatedPlanError(ValueError):pass

def _specific(value,field):
    # A cheap rejection gate, not a substitute for semantic evaluation.
    if not isinstance(value,str) or len(re.findall(r'\b[\w-]+\b',value))<5 or GENERIC.fullmatch(value):
        raise AutomatedPlanError('Insufficient visual specificity: '+field)

def _keys(value,expected,label):
    if not isinstance(value,dict) or set(value)!=set(expected):raise AutomatedPlanError('Invalid '+label+' fields')

def asset_catalog(records):
    """Only descriptions and IDs leave this process; no local paths or credentials."""
    if not isinstance(records,dict) or not records:raise AutomatedPlanError('Real asset catalog required')
    out=[]
    for aid,item in records.items():
        _keys(item,{'path','sha256','type','description'},'catalog asset')
        if not re.fullmatch(r'[A-Za-z0-9_-]+',aid) or item['type'] not in {'image','video'}:raise AutomatedPlanError('Invalid asset id/type')
        _specific(item['description'],'asset description')
        out.append({'id':aid,'type':item['type'],'description':item['description']})
    return out

def prompt_payload(report,catalog,*,topic='',audience='',style='',fallbacks=()):
    for s in (topic,audience,style):
        if not isinstance(s,str) or len(s)>500:raise AutomatedPlanError('Invalid planning context')
    return {'narration':report['transcript'],'audio_duration':report['audio_duration'],
        'words':[{'index':x['index'],'text':x['text'],'start':x['start'],'end':x['end']} for x in report['words']],
        'context':{'topic':topic,'audience':audience,'visual_style':style},'assets':catalog,
        'renderer':{'canvas':[540,960],'output':[1080,1920],'operations':sorted(OPS),'easing':sorted(EASING),
                    'transitions':sorted(TRANSITIONS),'camera':sorted(CAMERAS),
                    'camera_values':'[scale, vertical_offset]','position_values':'[x, y]','layer_coordinates':'center in design pixels'},
        'permitted_fallbacks':[list(x) for x in fallbacks]}

def validate_response(response,words,catalog,allowed_fallbacks=()):
    _keys(response,{'semantic_plan','layout','rationale','fallbacks'},'planner response')
    semantic=response['semantic_plan'];validate_plan(semantic,words)
    beats=semantic['beats'];bybeat={b['id']:b for b in beats};layerplans=response['layout'];rationale=response['rationale']
    if not isinstance(layerplans,dict) or set(layerplans)!=set(bybeat) or not isinstance(rationale,dict) or set(rationale)!=set(bybeat):raise AutomatedPlanError('Each beat needs a layout and rationale')
    for b in beats:
        bid=b['id'];_specific(b['meaning'],bid+' meaning');_specific(b['visual_objective'],bid+' objective');_specific(b['scene_description'],bid+' scene');_specific(b['composition'],bid+' composition');_specific(rationale[bid],bid+' rationale')
        if b['transition'] not in TRANSITIONS or b['camera'] not in CAMERAS:raise AutomatedPlanError(bid+': unsupported camera/transition')
        for a in b['assets']:_specific(a['description'],bid+' asset')
        for e in b['events']:_specific(e['action'],bid+'/'+e['id']+' action')
    valid_fallbacks=set(tuple(v) for v in allowed_fallbacks)
    if not isinstance(response['fallbacks'],list):raise AutomatedPlanError('Fallbacks must be a list')
    fb={}
    for f in response['fallbacks']:
        _keys(f,{'event_id','requested','selected','reason'},'fallback')
        _specific(f['reason'],'fallback reason')
        if not all(isinstance(f[k],str) and f[k] for k in ('event_id','requested','selected')) or (f['requested'],f['selected']) not in valid_fallbacks or f['event_id'] in fb:raise AutomatedPlanError('Fallback not explicitly permitted')
        fb[f['event_id']]=f
    renderer_design={'assets':{k:{a:v for a,v in item.items() if a in {'path','sha256','type'}} for k,item in catalog.items()},'beats':{}}
    eventids=set()
    for bid,b in bybeat.items():
        layout=layerplans[bid];_keys(layout,{'layers','events','transition'},bid+' layout')
        if layout['transition']!=b['transition']:raise AutomatedPlanError('Transition differs from semantic plan')
        if not isinstance(layout['layers'],list) or not layout['layers']:raise AutomatedPlanError('Layers required')
        semantic_assets={a['id'] for a in b['assets']};layers={};mapped=set();converted=[]
        for l in layout['layers']:
            _keys(l,{'id','asset','semantic_asset','x','y','width','height','z','opacity'},bid+' layer')
            if not isinstance(l['id'],str) or not l['id'] or l['id'] in layers or l['asset'] not in catalog or l['semantic_asset'] not in semantic_assets:raise AutomatedPlanError('Invalid layer/asset association in '+bid)
            layers[l['id']]=l;mapped.add(l['semantic_asset']);converted.append({k:v for k,v in l.items() if k!='semantic_asset'})
        if mapped!=semantic_assets:raise AutomatedPlanError('Every required semantic asset needs a layer: '+bid)
        events=layout['events'];sem_events={e['id']:e for e in b['events']}
        if not isinstance(events,dict) or set(events)!=set(sem_events):raise AutomatedPlanError('Every event needs an executable instruction')
        touched=set()
        for eid,v in events.items():
            _keys(v,{'target','operation','from','to','easing'},eid+' animation')
            e=sem_events[eid];eventids.add(eid);op=v['operation']
            if op not in OPS or v['easing'] not in EASING:raise AutomatedPlanError('Unsupported operation/easing '+eid)
            if e['animation_type']!=op:raise AutomatedPlanError('Semantic operation mismatch '+eid)
            property_key=(v['target'],op)
            if property_key in touched:raise AutomatedPlanError('Renderer cannot chain multiple events on the same property: '+eid)
            touched.add(property_key)
            if e['transition']!=b['transition'] or e['camera'] not in CAMERAS:raise AutomatedPlanError('Unsupported event transition/camera '+eid)
            if op=='camera':
                if v['target']!='camera' or e['target']!='camera' or e['camera'] not in {'push','pull'}:raise AutomatedPlanError('Invalid camera target/instruction '+eid)
            else:
                target=v['target']
                if target not in layers or target!=e['target'] or layers[target]['semantic_asset']!=e['asset_id'] or e['camera']!='hold':raise AutomatedPlanError('Event must target its own semantic asset layer '+eid)
            if v['from']==v['to']:raise AutomatedPlanError('No-op animation '+eid)
            if eid in fb and fb[eid]['selected']!=op:raise AutomatedPlanError('Fallback selected operation mismatch '+eid)
        renderer_design['beats'][bid]={'layers':converted,'events':copy.deepcopy(events),'transition':layout['transition']}
    if set(fb)-eventids:raise AutomatedPlanError('Fallback references unknown event')
    return renderer_design

def generate_and_compile(*,planner,audio,transcript,alignment,catalog,topic='',audience='',style='',allowed_fallbacks=(),mode_runtimes=None,mode_fallback_policy=()):
    """Run authorized planner; fail closed before renderer on any invalid response."""
    report=require_verified(alignment,audio,transcript)
    if planner is None or not callable(getattr(planner,'plan_visual',None)):raise AutomatedPlanError('No authorized visual planner configured')
    public_catalog=asset_catalog(catalog);payload=prompt_payload(report,public_catalog,topic=topic,audience=audience,style=style,fallbacks=allowed_fallbacks)
    if mode_runtimes is not None:
        payload['mode_planning']={'intent_types':['real_application_action','visual_storytelling','process_or_chart','hybrid'],
            'required_intent_fields':['intent','mode_operations','rationale','expected_result','verification','acceptable_fallback','continuity'],
            'declared_modes':{m:{'operations':sorted(r.capability.operations),'status':r.capability.status} for m,r in mode_runtimes.items()},
            'permitted_mode_fallbacks':[list(p) for p in mode_fallback_policy],
            'note':'Declarations are not preflight or evidence; runtime will select and verify separately.'}
    response=planner.plan_visual(payload)
    if mode_runtimes is not None:
        if not isinstance(response,dict) or 'mode_intents' not in response:raise AutomatedPlanError('Model must provide mode intent for every beat')
        response=dict(response);mode_intents=response.pop('mode_intents')
    design=validate_response(response,[w['text'] for w in report['words']],catalog,allowed_fallbacks)
    scheduled=schedule(audio,transcript,alignment,response['semantic_plan'])
    timeline=compile_timeline(scheduled,design,audio)
    result={'semantic_plan':response['semantic_plan'],'rationale':response['rationale'],'fallbacks':response['fallbacks'],'scheduled':scheduled,'design':design,'timeline':timeline}
    if mode_runtimes is not None:
        from .production_modes import select_auditable_modes,attach_asset_provenance
        result['mode_plan']=attach_asset_provenance(select_auditable_modes(scheduled,mode_intents,catalog,mode_runtimes,fallback_policy=mode_fallback_policy),design,catalog)
    return result
