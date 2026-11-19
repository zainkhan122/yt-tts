import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import topics_covered as t
class HistoryDedup(unittest.TestCase):
 def test_only_completed_renders_are_protected_even_if_registry_is_stale(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'tracker').mkdir();(root/'tracker/render-attempts.json').write_text(json.dumps({'attempts':{'a':{'brief_id':'repo-agent-desktop-01','status':'success'},'b':{'brief_id':'repo-failed-demo-01','status':'failed'}}}))
   oldroot,oldreg=t.ROOT,t.REGISTRY
   try:
    t.ROOT=root;t.REGISTRY=root/'tracker/topics-covered.json';reg=t.load()
    self.assertEqual(t.is_covered('agent-desktop',reg)['status'],'rendered')
    self.assertIsNone(t.is_covered('failed-demo',reg))
    self.assertIsNotNone(t.is_covered('vercel-labs/agent-desktop',reg))
    self.assertIsNotNone(t.is_covered('https://github.com/vercel-labs/agent-desktop.git',reg))
    self.assertIsNone(t.is_covered('other/agent-desktop-extra',reg))
   finally:t.ROOT=oldroot;t.REGISTRY=oldreg
