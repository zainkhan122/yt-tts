"""Contract tests use simulated backend output, never external AI inference."""
import copy,wave
from pathlib import Path
import pytest
from PIL import Image
from graphics.production.alignment import FasterWhisperBackend,run_alignment,tokens,AlignmentError
from graphics.production.blueprint import digest
from graphics.production.automated_planner import generate_and_compile,AutomatedPlanError
from graphics.production.layer_renderer import render
from graphics.production.semantic import PlanningError

@pytest.fixture
def fixture(tmp_path,monkeypatch):
    # Silence and deterministic fake ASR observations are plumbing tests only.
    audio=tmp_path/'test.wav'
    with wave.open(str(audio),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(8000);f.writeframes(b'\0\0'*16000)
    text='Clouds drift slowly across the valley';ws=tokens(text)
    observed=[{'text':w,'start':.1+i*.25,'end':.25+i*.25,'confidence':.98} for i,w in enumerate(ws)]
    monkeypatch.setattr(FasterWhisperBackend,'transcribe',lambda self,path:observed)
    alignment=run_alignment(audio,text,FasterWhisperBackend('synthetic-test'))
    asset=tmp_path/'scene.png';Image.new('RGBA',(30,30),(48,95,170,255)).save(asset)
    catalog={'art':{'path':str(asset),'sha256':digest(asset),'type':'image','description':'Blue cloud silhouette on transparent canvas'}}
    event={'id':'cloud-drift','trigger_phrase':'slowly','occurrence':1,'action':'Move the cloud layer across the valley','target':'cloud-layer','animation_type':'position','duration':.4,'camera':'hold','asset_id':'cloud-art','transition':'cut'}
    beat={'id':'b1','word_start':0,'word_end':6,'meaning':'Clouds drift slowly across a valley','visual_objective':'Move a cloud layer across the valley','treatment':'process_animation','scene_description':'A blue cloud moves across an open valley','subject':'cloud','objects':['cloud'],'composition':'Place the cloud centered above the valley','camera':'hold','transition':'cut','assets':[{'id':'cloud-art','kind':'image','description':'A blue cloud shape with simple soft edges','reuse_of':None}],'events':[event]}
    layer={'id':'cloud-layer','asset':'art','semantic_asset':'cloud-art','x':270,'y':300,'width':90,'height':90,'z':1,'opacity':1}
    op={'target':'cloud-layer','operation':'position','from':[270,300],'to':[270,400],'easing':'smooth'}
    response={'semantic_plan':{'beats':[beat]},'layout':{'b1':{'layers':[layer],'events':{'cloud-drift':op},'transition':'cut'}},'rationale':{'b1':'Cloud movement accompanies the described drift over the valley'},'fallbacks':[]}
    return audio,text,alignment,catalog,response

class FakePlanner:
    def __init__(self,response):self.response=response;self.payload=None
    def plan_visual(self,payload):self.payload=payload;return copy.deepcopy(self.response)

def run(f,plan=None,**kw):
    audio,text,alignment,catalog,response=f;p=plan or FakePlanner(response)
    return generate_and_compile(planner=p,audio=audio,transcript=text,alignment=alignment,catalog=catalog,**kw)

def test_planner_bridge_and_real_synthetic_render(fixture,tmp_path):
    p=FakePlanner(fixture[-1]);result=run(fixture,p,topic='Weather',audience='General')
    assert result['scheduled']['beats'][0]['events'][0]['audio_time']==.6
    assert result['timeline']['beats'][0]['events'][0]['operation']=='position'
    assert 'path' not in str(p.payload['assets'])
    out=tmp_path/'output.mp4';render(result['timeline'],fixture[0],out,tmp_path/'cache',fps=5);assert out.stat().st_size>0

def test_generic_instruction_rejected(fixture):
    fixture[-1]['semantic_plan']['beats'][0]['events'][0]['action']='Animate the phone'
    with pytest.raises(AutomatedPlanError,match='specificity'):run(fixture)

def test_missing_asset_and_bad_target(fixture):
    fixture[-1]['layout']['b1']['layers'][0]['asset']='unknown'
    with pytest.raises(AutomatedPlanError,match='association'):run(fixture)
    fixture[-1]['layout']['b1']['layers'][0]['asset']='art';fixture[-1]['layout']['b1']['events']['cloud-drift']['target']='other'
    with pytest.raises(AutomatedPlanError,match='target'):run(fixture)

def test_bad_operations_and_overrun(fixture):
    fixture[-1]['layout']['b1']['events']['cloud-drift']['operation']='flow'
    with pytest.raises(AutomatedPlanError,match='Unsupported'):run(fixture)
    fixture[-1]['layout']['b1']['events']['cloud-drift']['operation']='position';fixture[-1]['semantic_plan']['beats'][0]['events'][0]['duration']=2
    with pytest.raises(PlanningError,match='overruns'):run(fixture)

def test_unapproved_fallback_rejected_and_explicit_allowed(fixture):
    fixture[-1]['fallbacks']=[{'event_id':'cloud-drift','requested':'fluid_simulation','selected':'position','reason':'Use moving layer instead of a fluid simulation'}]
    with pytest.raises(AutomatedPlanError,match='permitted'):run(fixture)
    assert run(fixture,allowed_fallbacks=[('fluid_simulation','position')])['fallbacks']

def test_script_coverage_and_noop(fixture):
    fixture[-1]['semantic_plan']['beats'][0]['word_end']=5
    with pytest.raises(PlanningError,match='omits'):run(fixture)
    fixture[-1]['semantic_plan']['beats'][0]['word_end']=6;fixture[-1]['layout']['b1']['events']['cloud-drift']['to']=[270,300]
    with pytest.raises(AutomatedPlanError,match='No-op'):run(fixture)

def test_requires_in_process_alignment(fixture):
    from graphics.production.alignment import Alignment
    f=list(fixture);f[2]=Alignment(f[2].report)
    with pytest.raises(AlignmentError,match='process'):run(f)

def test_battery_regression_fixture_intact():
    p=Path(__file__).parent/'demo_assets/battery-demo.mp4'
    assert p.exists() and digest(p)=='088f77d8e8778d60382ad908e796cf1c26f46cc4a089e6c1b0dd950f3ffa9385'
