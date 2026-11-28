"""Mock-provider tests of the opt-in planner boundary, not model acceptance."""
import copy
import pytest
from graphics.production.test_automated_planner import fixture
from graphics.production.automated_planner import generate_and_compile,AutomatedPlanError
from graphics.production.production_modes import ModeRuntime,ModeCapability,ModeError

class Probe:
    def __init__(self):self.calls=0
    def preflight(self,operations):self.calls+=1;return {'ok':True,'detail':'synthetic test probe'}
class MockPlanner:
    def __init__(self,response):self.response=response;self.payload=None
    def plan_visual(self,payload):
        self.payload=payload;r=copy.deepcopy(self.response)
        r['mode_intents']={'b1':{'intent':'process_or_chart','mode_operations':{'motion_graphics':['position']},'rationale':'A diagram makes the changing position visible','expected_result':'A cloud layer changes its visible position','verification':['check target visible','check movement timing'],'acceptable_fallback':None,'continuity':'Maintain the same cloud image'}}
        return r

def test_integrated_selection_uses_probe_and_preserves_provenance(fixture):
    audio,text,alignment,catalog,response=fixture;probe=Probe();cap=ModeCapability('motion_graphics',frozenset({'position'}),'available',False,'declared')
    r=ModeRuntime(cap,'layer-renderer','local','pillow',probe);planner=MockPlanner(response)
    o=generate_and_compile(planner=planner,audio=audio,transcript=text,alignment=alignment,catalog=catalog,mode_runtimes={'motion_graphics':r})
    assert planner.payload['mode_planning']['declared_modes']['motion_graphics']['status']=='available'
    assert probe.calls==1 and o['mode_plan'][0]['selected_mode']=='motion_graphics'
    assert o['mode_plan'][0]['assets'][0]['sha256']==catalog['art']['sha256']
    assert not o['mode_plan'][0]['lifecycle']['executed'] and not o['mode_plan'][0]['lifecycle']['output_verified']

def test_planner_cannot_skip_mode_contract(fixture):
    audio,text,alignment,catalog,response=fixture
    class Planner:
        def plan_visual(self,p):return response
    with pytest.raises(AutomatedPlanError,match='mode intent'):
        generate_and_compile(planner=Planner(),audio=audio,transcript=text,alignment=alignment,catalog=catalog,mode_runtimes={})
