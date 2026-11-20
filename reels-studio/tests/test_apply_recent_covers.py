import unittest
from unittest.mock import patch
from tools.youtube import apply_recent_covers as mod

class TestTargetedCovers(unittest.TestCase):
    def test_cover_budget_reserves_general_quota_and_upload_starts(self):
        cfg = {'general_quota_budget_per_day': 2000, 'max_upload_starts_per_day': 2}
        limited = mod.cover_config(cfg)
        self.assertEqual(limited['general_quota_budget_per_day'], 1500)
        self.assertEqual(limited['max_upload_starts_per_day'], 2)
        self.assertEqual(cfg['general_quota_budget_per_day'], 2000)

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

    def test_retired_queue_item_with_manifest_approval_can_apply(self):
        class Journal: data={'enrichment':{}}
        recs={'retired:youtube':{'state':'sent','youtube_id':'ABCDEFGHIJK'}}
        def effective(item):
            return {**item,'cover_sha256':'sha256:x','cover_reviewed_at':'user-approved'} if item['video_id']=='retired' else item
        with patch.object(mod,'effective_item',side_effect=effective), patch.object(mod,'get_video',return_value={'status':{'privacyStatus':'public'}}), patch.object(mod,'fetch_short_cover',return_value={'sha256':'sha256:x','path':'x'}), patch.object(mod,'config',return_value={}), patch.object(mod,'attach_short_cover',return_value='confirmed'):
            self.assertEqual(mod.apply(object(),Journal(),recs,[],['retired'],'/tmp')[0]['state'],'confirmed')

    def test_unknown_existing_custom_cover_is_preserved(self):
        class Journal:
            data={'enrichment':{}}
            def save(self, message): pass
        recs={'v:youtube':{'state':'sent','youtube_id':'ABCDEFGHIJK'}}
        items=[{'video_id':'v','cover_sha256':'sha256:x','cover_reviewed_at':'date','preserve_existing_custom':True}]
        with patch.object(mod,'get_video',return_value={'status':{'privacyStatus':'public'},'contentDetails':{'hasCustomThumbnail':True}}),patch.object(mod,'attach_short_cover') as attach:
            result=mod.apply(object(),Journal(),recs,items,['v'],'/tmp')
            self.assertEqual(result[0]['state'],'existing_custom_preserved')
            attach.assert_not_called()
            self.assertEqual(Journal.data['enrichment']['ABCDEFGHIJK']['cover_hold_digest'],'sha256:x')

    def test_unknown_thumbnail_state_is_not_overwritten(self):
        class Journal:
            data={'enrichment':{}}
            def save(self, message): pass
        recs={'v:youtube':{'state':'sent','youtube_id':'ABCDEFGHIJK'}}
        items=[{'video_id':'v','cover_sha256':'sha256:x','cover_reviewed_at':'date','preserve_existing_custom':True}]
        with patch.object(mod,'get_video',return_value={'status':{'privacyStatus':'public'},'contentDetails':{}}),patch.object(mod,'attach_short_cover') as attach:
            result=mod.apply(object(),Journal(),recs,items,['v'],'/tmp')
            self.assertEqual(result[0]['state'],'thumbnail_state_unknown')
            attach.assert_not_called()

    def test_manual_upload_requires_explicit_cover_opt_in(self):
        class Journal: data={'enrichment':{}}
        recs={'manual:youtube':{'state':'published_manual','youtube_id':'ABCDEFGHIJK'}}
        items=[{'video_id':'manual','cover_sha256':'sha256:x','cover_reviewed_at':'date'}]
        with patch.object(mod,'effective_item',side_effect=lambda x:x), patch.object(mod,'get_video',return_value={'status':{'privacyStatus':'public'},'contentDetails':{'hasCustomThumbnail':False}}), patch.object(mod,'fetch_short_cover',return_value={'sha256':'sha256:x','path':'x'}), patch.object(mod,'config',return_value={}), patch.object(mod,'attach_short_cover',return_value='confirmed') as attach:
            self.assertEqual(mod.apply(object(),Journal(),recs,items,['manual'],'/tmp')[0]['state'],'error')
            items[0]['manual_cover_eligible']=True
            self.assertEqual(mod.apply(object(),Journal(),recs,items,['manual'],'/tmp')[0]['state'],'confirmed')
            self.assertEqual(attach.call_count,1)

    def test_private_video_never_written(self):
        class Journal: data={'enrichment':{}}
        recs={'v:youtube':{'state':'sent','youtube_id':'ABCDEFGHIJK'}}
        items=[{'video_id':'v','cover_sha256':'sha256:x','cover_reviewed_at':'date'}]
        with patch.object(mod,'get_video',return_value={'status':{'privacyStatus':'private'}}),patch.object(mod,'attach_short_cover') as attach:
            self.assertEqual(mod.apply(object(),Journal(),recs,items,['v'],'/tmp')[0]['state'],'error')
            attach.assert_not_called()

if __name__=='__main__': unittest.main()
