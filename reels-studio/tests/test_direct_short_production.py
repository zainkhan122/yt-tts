import copy
import datetime as dt
import unittest
from pathlib import Path
from unittest.mock import patch
from tools.post.common import load_json,parse_time
from tools.youtube import direct_short_production as d
from tools.youtube.api import Deferred,Uncertain
ROOT=Path(__file__).resolve().parents[1]
class J:
    def __init__(self, data=None): self.data=data or {'records':{}};self.events=[]
    @property
    def records(self):return self.data['records']
    def save(self,reason):self.events.append(reason)
class Tests(unittest.TestCase):
    def setUp(self):
        self.item=next(x for x in load_json(ROOT/'queue/publish.json')['items'] if x['video_id']=='repo-moneyprinterturbo-01')
        self.brief=load_json(ROOT/'briefs/repo-moneyprinterturbo-01.json')
        self.due=parse_time('2026-11-20T21:08:00Z');self.now=self.due-dt.timedelta(days=1)
        self.pub=J();self.yt=J()
    def reserve(self):return d.reserve(self.item,self.brief,self.due,self.pub,self.yt,self.now)
    def test_reservation_is_durable_and_idempotent(self):
        a=self.reserve();b=self.reserve();self.assertIs(a,b);self.assertEqual(len(self.yt.events),1)
    def test_changed_time_or_pin_not_replaced(self):
        self.reserve();self.item['asset_id']+=1
        with self.assertRaises(ValueError):self.reserve()
    def test_existing_buffer_schedule_blocks(self):
        self.pub.records[self.item['video_id']+':youtube']={'state':'scheduled'}
        with self.assertRaises(ValueError):self.reserve()
    def test_sent_enrichment_blocks(self):
        self.yt.data['enrichment']={'existing':{'video_id':self.item['video_id']}}
        with self.assertRaises(ValueError):self.reserve()
    def test_existing_direct_record_blocks(self):
        self.yt.records[self.item['video_id']]={'state':'scheduled','youtube_id':'exampleid00'}
        with self.assertRaises(ValueError):self.reserve()
    def test_slot_conflict_blocks(self):
        self.yt.records['different']={'state':'scheduled','kind':'direct_short','publish_at':d.iso(self.due)}
        with self.assertRaises(ValueError):self.reserve()
    def test_ship_error_blocks(self):
        with self.assertRaises(ValueError):d.reserve(self.item,self.brief,self.due,self.pub,self.yt,self.now,ship_errors=['bad review'])
    def test_reserved_job_schedules(self):
        job=self.reserve()
        with patch.object(d,'run',return_value={'state':'scheduled','youtube_id':'abcdef12345'}):
            state=d.execute_job(job,self.item,self.brief,self.pub,self.yt,None,{},Path('/tmp/nonexistent-direct-test'),clock=lambda:self.now)
        self.assertEqual(state,'scheduled');self.assertEqual(job['youtube_id'],'abcdef12345')
    def test_quota_deferral_retries_no_reupload(self):
        job=self.reserve()
        with patch.object(d,'run',side_effect=Deferred('wait','QUOTA_BUDGET',900)):
            state=d.execute_job(job,self.item,self.brief,self.pub,self.yt,None,{},Path('/tmp/nonexistent-direct-test'),clock=lambda:self.now)
        self.assertEqual(state,'pending');self.assertEqual(job['error_code'],'QUOTA_BUDGET');self.assertGreater(parse_time(job['retry_at']),self.now)
    def test_uncertain_upload_holds(self):
        job=self.reserve()
        with patch.object(d,'run',side_effect=Uncertain('unknown','RECONCILE_REQUIRED')):
            state=d.execute_job(job,self.item,self.brief,self.pub,self.yt,None,{},Path('/tmp/nonexistent-direct-test'),clock=lambda:self.now)
        self.assertEqual(state,'needs_review')
    def test_changed_job_pins_refuses_upload(self):
        job=self.reserve();self.item['asset_id']+=1
        with self.assertRaises(ValueError):d.execute_job(job,self.item,self.brief,self.pub,self.yt,None,{},Path('/tmp/nonexistent-direct-test'),clock=lambda:self.now)
if __name__=='__main__':unittest.main()
