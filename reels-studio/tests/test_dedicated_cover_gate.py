import datetime as dt,json,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock,patch
from tools.dedicated_cover_gate import errors_for
from tools.post import publisher,release
from tools.youtube import direct_shorts

class Tests(unittest.TestCase):
 def setUp(self):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name);self.item={'video_id':'test-video-01','asset_digest':'sha256:'+'a'*64,'cover_sha256':'sha256:'+'b'*64};self.path=self.root/'research/production/cover-receipts/test-video-01.json';self.path.parent.mkdir(parents=True)
  self.rec={'contract':'dedicated-cover-v1','video_id':'test-video-01','video_sha256':self.item['asset_digest'],'cover_sha256':self.item['cover_sha256'],'art_sha256':'sha256:'+'c'*64,'source_kind':'purpose-made-for-this-video','frame_zero_verified':True,'frame_zero_mean_abs_rgb_error':2.3,'dimensions':[1080,1920],'headline':'ONE PROMPT','reviewed_at':'2026-11-23T22:00:00Z'}
 def save(self):self.path.write_text(json.dumps(self.rec))
 def test_receipt_required_and_hash_bound(self):
  self.assertTrue(errors_for(self.item,self.root));self.save();self.assertFalse(errors_for(self.item,self.root))
  self.rec['video_sha256']='sha256:'+'d'*64;self.save();self.assertTrue(errors_for(self.item,self.root))
 def test_no_frame_extraction_as_provenance(self):
  self.rec['source_kind']='extracted-from-video';self.save();self.assertTrue(errors_for(self.item,self.root))
  self.rec['source_kind']='purpose-made-for-this-video';self.rec['frame_zero_mean_abs_rgb_error']=6.1;self.save();self.assertTrue(errors_for(self.item,self.root))
 def test_same_art_not_reused_for_another_video(self):
  self.save();other={**self.rec,'video_id':'different-video'};(self.path.parent/'different-video.json').write_text(json.dumps(other));self.assertTrue(errors_for(self.item,self.root))
 def test_buffer_create_blocked(self):
  now=dt.datetime(2026,1,1,tzinfo=dt.timezone.utc);row={'video_id':self.item['video_id'],'platform':'instagram','category':'tool','due_at':'2026-01-02T00:00:00Z','payload':{'mode':'customScheduled'}};cfg={'buffer':{'channels':{'instagram':{}},'max_attempts':3}};j=Mock();j.records={};client=Mock()
  with patch.object(publisher,'ROOT',self.root),patch.object(publisher,'require_house_outro'):
   result=publisher.deliver([row],[self.item],j,client,cfg,clock=lambda:now)
  self.assertIn('dedicated cover',result[0]['error']);client.create.assert_not_called();j.save.assert_not_called()
 def test_youtube_upload_blocked(self):
  with patch.object(direct_shorts,'ROOT',self.root),patch.object(direct_shorts,'require_house_outro'):
   with self.assertRaisesRegex(ValueError,'dedicated cover'):direct_shorts.run(self.item,{},None,None,Mock(),Mock(),{},self.root)
 def test_media_replacement_blocked(self):
  with patch.object(release,'ROOT',self.root),patch('tools.house_outro_gate.require'):
   with self.assertRaisesRegex(ValueError,'dedicated cover'):release.refresh_input({'_key':'test-video-01:instagram'},self.item,{},None)
if __name__=='__main__':unittest.main()
