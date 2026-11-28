import pytest
from graphics.production.production_modes import ModeCapability,choose_mode,verify_evidence,ModeError

def test_no_implicit_fallback():
    screen=ModeCapability('screen_demo',frozenset({'click'}),'unavailable',False,'not accessible')
    graph=ModeCapability('motion_graphics',frozenset({'click'}),'available',True,'illustrative animation')
    with pytest.raises(ModeError):choose_mode(intent='real_application_action',required_operations=['click'],capabilities=[screen,graph])
    x=choose_mode(intent='real_application_action',required_operations=['click'],capabilities=[screen,graph],permitted_fallback='motion_graphics')
    assert x['label']=='illustrative recreation' and x['fallback']

def test_no_review_is_not_acceptance():
    r=verify_evidence(mode='screen_demo',asset_hash_ok=True,action_observed=True,timing_checked=True,visibility_checked=True,readability_checked=True,audiovisual_reviewed=False)
    assert r['status']=='blocked' and 'audiovisual_reviewed' in r['missing']

def test_beat_contract_has_explicit_evidence():
    from graphics.production.production_modes import plan_beat_mode
    cap=ModeCapability('screen_demo',frozenset({'click'}),'available',True,'verified demo click')
    p=plan_beat_mode(beat_id='one',intent='real_application_action',visual_objective='Show playback state change',assets=['browser-video'],operations=['click'],expected_result='Playing icon changes to paused',constraints=['demo data only'],verification_method='DOM and before/after screenshots',capabilities=[cap])
    assert p['selection']['mode']=='screen_demo' and p['expected_result']=='Playing icon changes to paused'

def _beat():
    return {'beats':[{'id':'b1','narration':'the music is playing','start':0.,'end':2.,'visual_objective':'Show a playback state change','transition':'cut','events':[{'id':'e1','action':'Toggle the media playback button','audio_time':.4,'end_time':1.1}]}]}
def _intent():
    return {'b1':{'intent':'real_application_action','mode_operations':{'screen_demo':['click'],'motion_graphics':['position']},'rationale':'An observed UI action is required for the stated result','expected_result':'Playback state changes after an actual click','verification':['before and after state','target visibility'],'acceptable_fallback':'motion_graphics','continuity':'Same application panel during the whole beat'}}
def _runtime(mode,ops,status='available',ok=True):
    from graphics.production.production_modes import ModeRuntime
    class Adapter:
        def preflight(self,required):return {'ok':ok,'detail':'test adapter preflight'}
    return ModeRuntime(ModeCapability(mode,frozenset(ops),status,True,'test declaration'),'test-adapter','test-provider','test-model',Adapter())

def test_preflight_not_execution_and_explicit_fallback():
    from graphics.production.production_modes import select_auditable_modes,require_executed_and_verified
    b=_beat();i=_intent();screen=_runtime('screen_demo',['click'],ok=False);motion=_runtime('motion_graphics',['position'])
    with pytest.raises(ModeError,match='no approved'):select_auditable_modes(b,i,{}, {'screen_demo':screen,'motion_graphics':motion})
    p=select_auditable_modes(b,i,{}, {'screen_demo':screen,'motion_graphics':motion},fallback_policy=[('screen_demo','motion_graphics')]);assert p[0]['selected_mode']=='motion_graphics';assert p[0]['fallbacks'][0]['disclosure'].startswith('illustrative');assert p[0]['lifecycle']['executed'] is False
    with pytest.raises(ModeError,match='receipts'):require_executed_and_verified(p)

def test_availability_boolean_not_preflight():
    from graphics.production.production_modes import select_auditable_modes,ModeRuntime
    cap=ModeCapability('screen_demo',frozenset({'click'}),'available',True,'declared')
    r=ModeRuntime(cap,'id','provider','model',object())
    with pytest.raises(ModeError):select_auditable_modes(_beat(),_intent(),{}, {'screen_demo':r})

def test_hybrid_requires_two_successful_preflights():
    from graphics.production.production_modes import select_auditable_modes
    i=_intent();i['b1']['intent']='hybrid';i['b1']['acceptable_fallback']=None
    r={'screen_demo':_runtime('screen_demo',['click']), 'motion_graphics':_runtime('motion_graphics',['position'])}
    p=select_auditable_modes(_beat(),i,{},r);assert p[0]['selected_mode']=='hybrid';assert len(p[0]['preflights'])==2
    r['motion_graphics']=_runtime('motion_graphics',['position'],ok=False)
    with pytest.raises(ModeError):select_auditable_modes(_beat(),i,{},r)
