import copy
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from tools.house_outro_gate import CONTRACT, errors_for, require
from tools.post import publisher, release
from tools.youtube import direct_shorts

class HouseOutroGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.item = {'video_id':'test-video-01','asset_digest':'sha256:' + 'a'*64}
        self.path = self.root/'research/production/outro-receipts/test-video-01.json'
        self.path.parent.mkdir(parents=True)
        self.receipt = {'video_id':'test-video-01','video_sha256':self.item['asset_digest'],
            'contract':CONTRACT,'verdict':'PASS','review_kind':'finished-video audiovisual inspection',
            'reviewer':'production-reviewer','reviewed_at':'2026-11-24T00:00:00Z',
            'keyword':'EFFECTS','outro_duration_seconds':5.7,
            'checks':dict.fromkeys(('house_layout','logo','follow_and_comment','animated_cursor','voiced_cta','caption_sync','ending_not_truncated'),True)}
    def save(self): self.path.write_text(json.dumps(self.receipt))
    def test_missing_corrupt_and_bad_identifier_fail_closed(self):
        self.assertTrue(errors_for(self.item,self.root));self.path.write_text('{');self.assertTrue(errors_for(self.item,self.root))
        self.assertTrue(errors_for({'video_id':'../bad','asset_digest':self.item['asset_digest']},self.root))
    def test_exact_mp4_and_full_audiovisual_checks_required(self):
        self.save();self.assertEqual(errors_for(self.item,self.root),[])
        self.item['asset_digest']='sha256:'+'b'*64;self.assertTrue(errors_for(self.item,self.root))
        self.item['asset_digest']=self.receipt['video_sha256'];self.receipt['checks']['voiced_cta']=False;self.save();self.assertTrue(errors_for(self.item,self.root))
        self.receipt['checks']['voiced_cta']=True;self.receipt['outro_duration_seconds']=1.9;self.save();self.assertTrue(errors_for(self.item,self.root))
    def test_explicit_owner_override_is_exact_file_only(self):
        self.receipt.update(verdict='OWNER_OVERRIDE', reviewer='owner', approved_at='2026-11-23T22:00:00Z', authorization='OWNER_APPROVED_EXACT_VIDEO_WAIVE_EDITORIAL_GATES', known_issues=['motion QA blocked'])
        self.save(); self.assertEqual(errors_for(self.item,self.root),[])
        other={**self.item,'asset_digest':'sha256:'+'c'*64}; self.assertTrue(errors_for(other,self.root))
        self.receipt.pop('known_issues');self.save();self.assertTrue(errors_for(self.item,self.root))
    def test_missing_receipt_blocks_direct_before_any_upload(self):
        with patch.object(direct_shorts,'ROOT',self.root):
            with self.assertRaisesRegex(ValueError,'house outro'):
                direct_shorts.run(self.item,{},None,None,Mock(),Mock(),{},self.root)
    def test_missing_receipt_blocks_buffer_before_create_and_reservation(self):
        now=dt.datetime(2026,1,1,tzinfo=dt.timezone.utc)
        row={'video_id':self.item['video_id'],'platform':'instagram','category':'tool','due_at':'2026-01-02T00:00:00Z','payload':{'mode':'customScheduled'}}
        cfg={'buffer':{'channels':{'instagram':{}},'max_attempts':3}}
        journal=Mock();journal.records={};client=Mock()
        with patch.object(publisher,'ROOT',self.root):
            out=publisher.deliver([row],[self.item],journal,client,cfg,clock=lambda:now)
        self.assertEqual(out[0]['state'],'outro_held');client.create.assert_not_called();journal.save.assert_not_called()
    def test_superseded_hosted_media_needs_receipt_for_actual_bytes(self):
        from tools.post import media
        item={**self.item,'asset_id':1,'asset_size':100,'media_path':'media/1/test-video-01.mp4'}
        cfg={'media':{'base_url':'https://example.invalid'}}
        index={'assets':{'1':{'video_id':self.item['video_id'],'url':'https://example.invalid/media/1/test-video-01.mp4','digest':'sha256:'+'b'*64,'size':100,'superseded_by':'2'},'2':{'digest':'sha256:'+'b'*64,'size':100}}}
        response=Mock(status_code=200);response.json.return_value=index
        with patch.object(media,'ROOT',self.root), patch.object(media.requests,'get',return_value=response):
            with self.assertRaisesRegex(ValueError,'house outro'):
                media.verify_site(cfg,[item])
    def test_refresh_cannot_swap_uninspected_new_asset(self):
        with patch.object(release,'ROOT',self.root):
            with self.assertRaisesRegex(ValueError,'house outro'):
                release.refresh_input({'_key':'test-video-01:instagram'},self.item,{},None)

if __name__=='__main__':unittest.main()
