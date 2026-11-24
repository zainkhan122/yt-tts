import hashlib,json,tempfile,unittest
from pathlib import Path
from graphics.stage import require_house_outro_plan,GraphicsError
from lib.pipeline import require_purpose_made_cover

class CoverAndOutroProductionTests(unittest.TestCase):
 def test_cover_needs_purpose_made_art_and_matching_digest(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t); folder=root/'covers'/'video-01';folder.mkdir(parents=True);brief={'id':'video-01'}
   with self.assertRaises(SystemExit):require_purpose_made_cover(brief,root)
   (folder/'art.png').write_bytes(b'illustration')
   sel={'brief':'video-01','purpose_made_art':'art.png','art_origin':'purpose-made-for-this-video','art_sha256':'sha256:'+hashlib.sha256(b'illustration').hexdigest()}
   (folder/'selection.json').write_text(json.dumps(sel));self.assertTrue(require_purpose_made_cover(brief,root))
   (folder/'art.png').write_bytes(b'changed')
   with self.assertRaises(SystemExit):require_purpose_made_cover(brief,root)
 def test_cover_rejects_paths_outside_video_directory(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t); folder=root/'covers'/'video-01';folder.mkdir(parents=True)
   (folder/'selection.json').write_text(json.dumps({'purpose_made_art':'../other.png'}))
   with self.assertRaises(SystemExit):require_purpose_made_cover({'id':'video-01'},root)
 def test_house_outro_requires_timed_narration_and_last_scene(self):
  final={'archetype':'endcard','t0':4,'t1':9,'payload':{'keyword':'TOOL'},'words':[[w,4+i*.5,4.4+i*.5] for i,w in enumerate(['Comment','TOOL','and','follow','Hypeless'])]}
  good={'brand':{'logo':'data:image/png;base64,ok','cta_button':'Follow'},'scenes':[final]}
  require_house_outro_plan(good)
  for changed in [[],[{'archetype':'endcard'}, {'archetype':'other'}],[{**final,'words':[]}],[{**final,'t1':7}],[{**final,'payload':{'keyword':'OTHER'}}]]:
   with self.assertRaises(GraphicsError):require_house_outro_plan({**good,'scenes':changed})
if __name__=='__main__':unittest.main()
