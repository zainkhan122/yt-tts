import copy
import datetime as dt
import unittest
from pathlib import Path
from unittest.mock import patch
from tools.post.common import load_json, parse_time
from tools.youtube.direct_shorts import validate_request, verify_copy

ROOT = Path(__file__).resolve().parents[1]

class DirectShortSafety(unittest.TestCase):
    def setUp(self):
        self.item = next(i for i in load_json(ROOT/'queue/publish.json')['items'] if i['video_id']=='repo-moneyprinterturbo-01')
        self.brief = load_json(ROOT/'briefs/repo-moneyprinterturbo-01.json')
        self.due = parse_time('2026-11-20T21:08:00Z')
        self.now = self.due - dt.timedelta(days=1)
        self.receipt = {'state':'scheduled','due_at':'2026-11-20T21:08:00Z', 'media_ref':{'asset_digest':self.item['asset_digest']}}
    def check(self):
        return validate_request(self.item,self.brief,self.receipt,self.due,self.now)
    def test_approved_exact_item(self):
        result=self.check(); self.assertIn('MoneyPrinterTurbo',result['title']); self.assertIn('#Shorts',result['description'])
    def test_changed_brief_blocks(self):
        self.brief['seo']['youtube']['title']='changed'
        with self.assertRaises(ValueError): self.check()
    def test_unapproved_blocks(self):
        self.item['approval']='held'
        with self.assertRaises(ValueError): self.check()
    def test_wrong_cover_blocks(self):
        self.item['cover_sha256']='sha256:incorrect'
        with self.assertRaises(ValueError): self.check()
    def test_wrong_media_blocks(self):
        self.receipt['media_ref']['asset_digest']='sha256:wrong'
        with self.assertRaises(ValueError): self.check()
    def test_changed_buffer_schedule_blocks(self):
        self.receipt['due_at']='2026-11-20T21:09:00Z'
        with self.assertRaises(ValueError): self.check()
    def test_past_or_near_slot_blocks(self):
        self.now=self.due-dt.timedelta(minutes=179)
        with self.assertRaises(ValueError): self.check()
    def test_readback_enforces_copy_and_tags(self):
        expected=self.check(); video={'snippet':copy.deepcopy(expected)}
        verify_copy(video,expected)
        video['snippet']['tags']=[]
        with self.assertRaises(ValueError): verify_copy(video,expected)

if __name__=='__main__': unittest.main()

class DirectFlow(DirectShortSafety):
    def exercise(self, *, confirmed=True, scheduled=False, rec_state="uploaded_private"):
        import tempfile
        from tools.youtube.direct_shorts import run
        from unittest.mock import patch
        snippet=validate_request(self.item,self.brief,self.receipt,self.due,self.now,allow_stale=True)
        class Journal:
            def __init__(self): self.records={'repo-moneyprinterturbo-01':{'video_id':'repo-moneyprinterturbo-01','state':rec_state,'youtube_id':'abcdef12345','asset_digest':self_item['asset_digest']}}; self.saves=[]
            def save(self, reason): self.saves.append(reason)
        self_item=self.item
        class API:
            def __init__(self): self.due = '2026-11-20T21:08:00Z' if scheduled else None; self.writes=0
            def verify_channel(self): return {'contentDetails':{'relatedPlaylists':{'uploads':'uploads'}}}
            def pages(self, endpoint, params): return iter([{'contentDetails':{'videoId':'abcdef12345'}}])
            def json(self,method,endpoint,**kwargs): self.writes+=1; self.due=kwargs['body']['status']['publishAt']; return {}
        api=API(); journal=Journal()
        def video(api, yid):
            status={'privacyStatus':'private'}
            if api.due:status['publishAt']=api.due
            return {'snippet':snippet,'status':status,'etag':'test','processingDetails':{'processingStatus':'succeeded'},'contentDetails':{'hasCustomThumbnail':confirmed}}
        with tempfile.TemporaryDirectory() as directory, patch('tools.youtube.direct_shorts.read_kit',return_value={'cover':{'sha256':self.item['cover_sha256'],'frame0':{'cover_frame':0}},'qa':{'checks':{'dedicated_cover_frame0':True}}}), patch('tools.youtube.direct_shorts.fetch_short_cover',return_value={'path':str(ROOT/'renders/covers/repo-moneyprinterturbo-01-cover.jpg'),'sha256':self.item['cover_sha256']}), patch('tools.youtube.direct_shorts.get_video',side_effect=video), patch('tools.youtube.direct_shorts.set_thumbnail'), patch('tools.youtube.direct_shorts.playlists_for'), patch('tools.youtube.direct_shorts.ensure_playlist',return_value='playlist'), patch('PIL.Image.open') as image_open:
            image_open.return_value.__enter__.return_value.width=1080
            image_open.return_value.__enter__.return_value.height=1920
            try: result=run(self.item,self.brief,self.receipt,self.due,api,journal,{},Path(directory),clock=lambda:self.now,sleep=lambda _:None)
            except Exception as e: result=e
        return result,api,journal
    def test_schedules_only_after_metadata(self):
        result,api,journal=self.exercise();self.assertEqual(result['state'],'scheduled');self.assertEqual(api.writes,1);self.assertIn('reserve direct Shorts schedule',journal.saves)
    def test_thumbnail_not_confirmed_stays_private(self):
        result,api,journal=self.exercise(confirmed=False);self.assertEqual(getattr(result,'code',None),'THUMBNAIL_PENDING');self.assertEqual(api.writes,0)
    def test_existing_schedule_is_not_rearmed(self):
        result,api,_=self.exercise(scheduled=True);self.assertEqual(result['state'],'scheduled');self.assertEqual(api.writes,0)

    def test_near_deadline_can_recover_existing_schedule(self):
        self.now=self.due-dt.timedelta(minutes=5)
        result,api,_=self.exercise(scheduled=True,rec_state='scheduling')
        self.assertEqual(result['state'],'scheduled');self.assertEqual(api.writes,0)
    def test_near_deadline_never_arms_new_schedule(self):
        self.now=self.due-dt.timedelta(minutes=5)
        result,api,_=self.exercise(scheduled=False,rec_state='scheduling')
        self.assertIsInstance(result,ValueError);self.assertEqual(api.writes,0)
