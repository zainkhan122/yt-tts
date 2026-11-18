import unittest
from unittest.mock import patch
from tools.youtube import apply_recent_covers as mod

class TestTargetedCovers(unittest.TestCase):
    def test_only_sent_public_with_approved_cover_are_written(self):
        class Journal:
            data = {'enrichment': {}}
        class API: pass
        records = {'yes:youtube': {'state':'sent','external_url':'https://youtube.com/shorts/ABCDEFGHIJK'},
                   'scheduled:youtube': {'state':'scheduled'}}
        items = [{'video_id':'yes','cover_sha256':'sha256:x','cover_reviewed_at':'date'}, {'video_id':'scheduled','cover_sha256':'sha256:y','cover_reviewed_at':'date'}]
        with patch.object(mod,'get_video',return_value={'status':{'privacyStatus':'public'}}), patch.object(mod,'fetch_short_cover',return_value={'sha256':'sha256:x','path':'x'}), patch.object(mod,'config',return_value={}), patch.object(mod,'attach_short_cover',return_value='confirmed') as attach:
            result=mod.apply(API(),Journal(),records,items,['yes','scheduled','missing'],'/tmp')
        self.assertEqual([x['state'] for x in result], ['confirmed','error','error'])
        self.assertEqual(attach.call_count,1)

    def test_private_video_never_written(self):
        class Journal: data={'enrichment':{}}
        recs={'v:youtube':{'state':'sent','youtube_id':'ABCDEFGHIJK'}}
        items=[{'video_id':'v','cover_sha256':'sha256:x','cover_reviewed_at':'date'}]
        with patch.object(mod,'get_video',return_value={'status':{'privacyStatus':'private'}}),patch.object(mod,'attach_short_cover') as attach:
            self.assertEqual(mod.apply(object(),Journal(),recs,items,['v'],'/tmp')[0]['state'],'error')
            attach.assert_not_called()

if __name__=='__main__': unittest.main()
