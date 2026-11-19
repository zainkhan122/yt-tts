"""A real viewer-outcome opening must be possible without breaking old plans."""
import json, sys, tempfile, unittest
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import video_plan
import brief_from_plan

class ViewerFirstScript(unittest.TestCase):
 def setUp(self):
  self.plan=json.loads((ROOT/'videos/tool-claude-tokens-01/plan.json').read_text())
 def test_statement_hook_and_review_are_accepted(self):
  self.plan['hook']='Create a complete video from one topic.'
  self.plan['script_review']={'viewer_outcome':'Get a first video draft','hook_reason':'Immediate result','demonstration':'Topic to footage to video','payoff':'Share after review','caveat':'Provider costs and rights vary','reviewer':'editor'}
  blocks=[m for status,m in video_plan.check(self.plan) if status=='BLOCK']
  self.assertFalse([m for m in blocks if 'hook' in m or 'editorial review' in m],blocks)
 def test_missing_review_cannot_pass_as_new_statement_hook(self):
  self.plan['hook']='Create a complete video from one topic.'
  blocks=[m for status,m in video_plan.check(self.plan) if status=='BLOCK']
  self.assertTrue(any('viewer-first editorial review' in m for m in blocks))
 def test_existing_question_plan_remains_compatible(self):
  blocks=[m for status,m in video_plan.check(self.plan) if status=='BLOCK']
  self.assertFalse([m for m in blocks if 'viewer question' in m],blocks)
 def test_builder_preserves_hook_and_review(self):
  p=self.plan;p['hook']='Create a complete video from one topic.';p['script_review']={'viewer_outcome':'video','hook_reason':'payoff','demonstration':'flow','payoff':'draft','caveat':'review','reviewer':'editor'}
  with tempfile.TemporaryDirectory() as tmp:
   r=Path(tmp);(r/'briefs').mkdir();cap=r/'captures'/p['id'];cap.mkdir(parents=True);(cap/'plan-keep.json').write_text('{}')
   for point in p['points']:
    v=point['visual']
    if v['kind']=='animation':(cap/v['animation']).touch()
   v=p['catch_visual']
   if v['kind']=='animation':(cap/v['animation']).touch()
   path=r/'plan.json';path.write_text(json.dumps(p))
   with mock.patch.object(brief_from_plan,'ROOT',r):out=brief_from_plan.build(path)
   brief=json.loads(out.read_text());self.assertEqual(brief['scenes'][0]['say'],p['hook']);self.assertEqual(brief['script_review'],p['script_review'])

class ReceiptReview(unittest.TestCase):
 def test_review_required_when_standard_marked(self):
  from tools.production_gate import validate_viewer_first_review, ProductionGateError
  with self.assertRaises(ProductionGateError):validate_viewer_first_review({'script_standard':'viewer-first-v1','script_review':{}})
  validate_viewer_first_review({'script_standard':'viewer-first-v1','script_review':{k:'reviewed' for k in ('viewer_outcome','hook_reason','demonstration','payoff','caveat','reviewer')}})
 def test_legacy_is_not_retroactively_blocked(self):
  from tools.production_gate import validate_viewer_first_review
  validate_viewer_first_review({})
