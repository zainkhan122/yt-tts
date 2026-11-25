import copy,datetime as dt,unittest
from unittest.mock import patch
from tools.post import cadence
from tools.post.common import config,iso
UTC=dt.timezone.utc;NOW=dt.datetime(2026,11,25,21,0,tzinfo=UTC);DUE=dt.datetime(2026,11,26,2,0,tzinfo=UTC)
class ExplicitOwnerTime(unittest.TestCase):
 def setUp(self):
  self.cfg=config(); self.cfg['buffer']['channels']['youtube']['enabled']=False
  self.channels=[{'id':v['buffer_id'],'serviceId':v['service_id'],'metadata':{}} for v in self.cfg['buffer']['channels'].values()]
  self.item={'video_id':'test-explicit','category':'tool','priority':1,'approval':'approved','platforms':['instagram','facebook'],'reviewed_at':iso(NOW),'expires_at':iso(DUE+dt.timedelta(hours=1)),'not_before':iso(NOW),'requested_publish_at':iso(DUE),'asset_id':123,'media_path':'media/123/test-explicit.mp4'}
 def plan(self,posts=(),records=None,item=None):
  with patch('tools.post.cadence.copy_rules.payload_for',side_effect=lambda i,p,t,c:{'dueAt':iso(t),'channelId':c['buffer']['channels'][p]['buffer_id']}):
   return cadence.plan([item or self.item],records or {},self.channels,posts,self.cfg,NOW,long_records={})
 def test_exact(self):
  rows,_=self.plan();self.assertEqual({x['platform'] for x in rows},{'instagram','facebook'});self.assertTrue(all(x['due_at']==iso(DUE) for x in rows));self.assertTrue(all(x['slot_source']=='owner-explicit' for x in rows))
 def test_conflict_no_fallback(self):
  ch=self.cfg['buffer']['channels']['instagram']['buffer_id'];p={'channelId':ch,'id':'already','status':'scheduled','dueAt':iso(DUE)};rows,_=self.plan([p]);self.assertEqual([x['platform'] for x in rows],['facebook'])
 def test_expired_or_too_close_no_fallback(self):
  item=copy.deepcopy(self.item);item['requested_publish_at']=iso(NOW+dt.timedelta(minutes=10));rows,_=self.plan(item=item);self.assertFalse(rows)
 def test_already_scheduled_no_duplicate(self):
  rows,_=self.plan(records={'test-explicit:instagram':{'platform':'instagram','video_id':'test-explicit','state':'scheduled','due_at':iso(DUE)}});self.assertEqual([x['platform'] for x in rows],['facebook'])
if __name__=='__main__':unittest.main()
