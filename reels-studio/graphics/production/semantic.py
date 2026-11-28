"""Provider-independent semantic intent, with a strict JSON contract.

The caller supplies a planner adapter. No network API or provider is assumed.
The planner returns phrase references, not invented timestamps.
"""
from typing import Protocol
import re

class PlanningError(ValueError): pass
class Planner(Protocol):
    def plan(self, *, transcript:str, words:list[str]) -> dict: ...

TREATMENTS={'photorealistic','product_visualization','exploded_view','3d_animation','scientific_visualization','process_animation','chart','kinetic_typography','infographic','split_screen','cinematic','visual_metaphor'}

def _string(v): return isinstance(v,str) and bool(v.strip())
def _fields(d,fields,where):
    if not isinstance(d,dict) or set(d)!=set(fields): raise PlanningError('Invalid '+where+' fields')

def validate_plan(doc,words):
    _fields(doc,['beats'],'plan')
    if not isinstance(doc['beats'],list) or not doc['beats']: raise PlanningError('At least one beat required')
    cursor=0;seen=set(); asset_ids=set()
    for b in doc['beats']:
        _fields(b,['id','word_start','word_end','meaning','visual_objective','treatment','scene_description','subject','objects','composition','camera','transition','assets','events'],'beat')
        if not _string(b['id']) or b['id'] in seen:raise PlanningError('Duplicate or invalid beat ID')
        seen.add(b['id']); a,z=b['word_start'],b['word_end']
        if type(a)!=int or type(z)!=int or a!=cursor or not a<z<=len(words):raise PlanningError('Beat word ranges must partition narration in order')
        cursor=z
        for k in ('meaning','visual_objective','scene_description','subject','composition','camera','transition'):
            if not _string(b[k]):raise PlanningError('Empty '+k)
        if b['treatment'] not in TREATMENTS:raise PlanningError('Unknown treatment')
        if not isinstance(b['objects'],list) or not b['objects'] or not all(_string(x) for x in b['objects']):raise PlanningError('Objects required')
        if not isinstance(b['assets'],list) or not b['assets']:raise PlanningError('Assets required')
        local=set()
        for x in b['assets']:
            _fields(x,['id','kind','description','reuse_of'],'asset')
            if not all(_string(x[k]) for k in ('id','kind','description')) or x['id'] in local or x['id'] in asset_ids:raise PlanningError('Invalid asset')
            if x['reuse_of'] is not None and x['reuse_of'] not in asset_ids:raise PlanningError('Reuse must reference an earlier asset')
            local.add(x['id']);asset_ids.add(x['id'])
        if not isinstance(b['events'],list) or not b['events']:raise PlanningError('Events required')
        for e in b['events']:
            _fields(e,['id','trigger_phrase','occurrence','action','target','animation_type','duration','camera','asset_id','transition'],'event')
            if not _string(e['id']) or e['id'] in seen:raise PlanningError('Duplicate event ID')
            seen.add(e['id'])
            for k in ('trigger_phrase','action','target','animation_type','camera','asset_id','transition'):
                if not _string(e[k]):raise PlanningError('Invalid event '+k)
            if e['asset_id'] not in local:raise PlanningError('Event asset not in beat')
            if type(e['occurrence'])!=int or e['occurrence']<1:raise PlanningError('Occurrence must be positive')
            if type(e['duration']) not in (int,float) or not 0<e['duration']<=60:raise PlanningError('Invalid event duration')
    if cursor!=len(words):raise PlanningError('Plan omits narration words')
    return doc

def create_plan(planner,transcript,words):
    if planner is None or not callable(getattr(planner,'plan',None)):raise PlanningError('No semantic planning provider configured')
    return validate_plan(planner.plan(transcript=transcript,words=words),words)
