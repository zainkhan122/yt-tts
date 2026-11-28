import copy,wave
import pytest
from graphics.production.alignment import analyze,run_alignment,require_verified,AlignmentError,FasterWhisperBackend,Alignment,tokens
from graphics.production.semantic import create_plan,PlanningError
from graphics.production.scheduler import schedule

@pytest.fixture
def audio(tmp_path):
    p=tmp_path/'vo.wav'
    with wave.open(str(p),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(8000);f.writeframes(b'\0\0'*80000)
    return p

def observed(text):
    return [{'text':s,'start':i*.4+.1,'end':i*.4+.3,'confidence':.9} for i,s in enumerate(tokens(text))]

def issue(monkeypatch,audio,text,obs=None):
    # Simulates adapter observations. This is not a live audio recognition test.
    monkeypatch.setattr(FasterWhisperBackend,'transcribe',lambda self,path:obs if obs is not None else observed(text))
    return run_alignment(audio,text,FasterWhisperBackend('fixture'))

def test_missing_repeated_low_extra(audio):
    t='go go stop';o=observed(t);o.pop(1)
    r=analyze(audio,t,o,provider='test',model='x');assert not r['eligible'];assert any(x['status']=='missing' for x in r['words'])
    o=observed(t);o[1]['confidence']=.1;r=analyze(audio,t,o,provider='test',model='x');assert r['words'][1]['flags']==['low_confidence']
    o=observed(t);o.append({'text':'extra','start':2,'end':2.2,'confidence':.9});r=analyze(audio,t,o,provider='test',model='x');assert r['unmatched_observation_indices']==[3]
    r=analyze(audio,t,observed(t),provider='test',model='x');assert [x['source_index'] for x in r['words']]==[0,1,2]

@pytest.mark.parametrize('change',[
    lambda o:o[1].update(start=-1),lambda o:o[1].update(end=100),
    lambda o:o[1].update(start=.2),lambda o:o[1].update(start=float('nan')),
    lambda o:o[1].update(confidence=None)])
def test_bad_observations(audio,change):
    o=observed('one two three');change(o);r=analyze(audio,'one two three',o,provider='test',model='x');assert not r['eligible']

def test_json_is_not_receipt_and_estimates_fail(monkeypatch,audio):
    text='one two three';a=issue(monkeypatch,audio,text);assert require_verified(a,audio,text)['eligible']
    with pytest.raises(AlignmentError):require_verified(Alignment(a.report),audio,text)
    bad=analyze(audio,text,observed(text),provider='test',model='x',method='length-weighted');assert not bad['eligible']; assert 'estimated' in bad['words'][0]['flags']
    inter=analyze(audio,text,observed(text),provider='test',model='x',method='interpolated');assert 'interpolated' in inter['words'][0]['flags']
    a.report['words'][0]['start']=1
    with pytest.raises(AlignmentError):require_verified(a,audio,text)

def test_audio_and_transcript_change(monkeypatch,audio):
    text='one two three';a=issue(monkeypatch,audio,text)
    with pytest.raises(AlignmentError):require_verified(a,audio,'one four three')
    with audio.open('ab') as f:f.write(b'change')
    with pytest.raises(AlignmentError):require_verified(a,audio,text)

def plan():
    # Controlled model response, not evidence of independent model inference.
    def asset(i):return {'id':'a'+str(i),'kind':'motion','description':'graphic','reuse_of':None}
    def event(i,phrase,target,action):return {'id':'e'+str(i),'trigger_phrase':phrase,'occurrence':1,'action':action,'target':target,'animation_type':'motion','duration':.15,'camera':'hold','asset_id':'a'+str(i),'transition':'cut'}
    def beat(i,a,z,treatment,subject,objects,event_):return {'id':'b'+str(i),'word_start':a,'word_end':z,'meaning':'explain','visual_objective':'show '+subject,'treatment':treatment,'scene_description':'subject and mechanism','subject':subject,'objects':objects,'composition':'center','camera':'push','transition':'cut','assets':[asset(i)],'events':[event_]}
    return {'beats':[beat(1,0,3,'exploded_view','smartphone',['phone','battery'],event(1,'smartphone','phone','reveal battery')),beat(2,3,9,'process_animation','battery',['electrodes','indicator'],event(2,'power','battery','cross section and changing energy')),beat(3,9,15,'scientific_visualization','ions',['electrodes','ions'],event(3,'chemistry','ions','move between electrodes'))]}

class FakePlanner:
    def plan(self,*,transcript,words):return plan()

def test_separate_planner_scheduler_multi_event(monkeypatch,audio):
    text="Your smartphone battery doesn't simply run out of power. Its chemistry is changing every second."
    al=issue(monkeypatch,audio,text);p=create_plan(FakePlanner(),text,tokens(text));extra=copy.deepcopy(p['beats'][0]['events'][0]);extra.update(id='e-extra',trigger_phrase='battery',action='separate casing');p['beats'][0]['events'].append(extra)
    b=schedule(audio,text,al,p);assert len(b['beats'])==3;assert len(b['beats'][0]['events'])==2
    assert b['beats'][0]['events'][1]['audio_time']==observed(text)[2]['start'];assert b['beats'][2]['events'][0]['target']=='ions'
    p['beats'][1]['events'][0]['duration']=8
    with pytest.raises(PlanningError,match='overruns'):schedule(audio,text,al,p)

def test_repeat_occurrence(monkeypatch,audio):
    text='go go stop';a=issue(monkeypatch,audio,text);p=plan();p['beats']=p['beats'][:1];b=p['beats'][0];b['word_start']=0;b['word_end']=3;b['events'][0]['trigger_phrase']='go';b['events'][0]['occurrence']=2
    assert schedule(audio,text,a,p)['beats'][0]['events'][0]['audio_time']==.5
    b['events'][0]['occurrence']=3
    with pytest.raises(PlanningError,match='not found'):schedule(audio,text,a,p)

def test_validation_rejects_unregistered_assets():
    p=plan();p['beats'][0]['events'][0]['asset_id']='unknown'
    class P:
        def plan(self,**kwargs):return p
    with pytest.raises(PlanningError):create_plan(P(),'x',['w']*15)
