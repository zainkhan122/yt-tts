import copy, unittest
from unittest.mock import patch
from tools.post import delete_buffer_youtube_pilot as m
class Journal:
    def __init__(self, records): self.records=records; self.events=[]
    def save(self, reason): self.events.append(reason)
class Buffer:
    def __init__(self, post): self.posts=[post];self.deletions=[]
    def state(self): return [],self.posts[:]
    def delete(self, postid): self.deletions.append(postid);self.posts=[]
class TestDeletion(unittest.TestCase):
    def setUp(self):
        self.pub=Journal({m.KEY:{'state':'scheduled','buffer_post_id':m.ID,'video_id':'repo-moneyprinterturbo-01'}})
        self.yt=Journal({'repo-moneyprinterturbo-01':{'state':'scheduled','youtube_id':m.YID,'publish_at':m.iso(m.DUE),'thumbnail_confirmed':True}})
        self.video={'status':{'privacyStatus':'private','publishAt':m.iso(m.DUE)},'contentDetails':{'hasCustomThumbnail':True}}
        self.buffer=Buffer({'id':m.ID,'channelId':m.config()['buffer']['channels']['youtube']['buffer_id'],'status':'scheduled','dueAt':m.iso(m.DUE)})
    def run_delete(self):
        with patch.object(m,'get_video',return_value=self.video), patch.object(m,'now_utc',return_value=m.DUE.replace(year=2025)):
            return m.execute(self.buffer,self.pub,self.yt,None)
    def test_targeted_delete_and_terminal_journal(self):
        self.run_delete();self.assertEqual(self.buffer.deletions,[m.ID]);self.assertEqual(self.pub.records[m.KEY]['state'],'deleted');self.assertEqual(len(self.pub.events),2)
    def test_unverified_replacement_blocks(self):
        self.video['contentDetails']['hasCustomThumbnail']=False
        with self.assertRaises(ValueError): self.run_delete()
        self.assertFalse(self.buffer.deletions)
    def test_sent_buffer_blocks(self):
        self.buffer.posts[0]['status']='sent'
        with self.assertRaises(ValueError):self.run_delete()
        self.assertFalse(self.buffer.deletions)
    def test_missing_before_reservation_blocks(self):
        self.buffer.posts=[]
        with self.assertRaises(ValueError):self.run_delete()
    def test_resume_after_ambiguous_delete(self):
        self.pub.records[m.KEY]['state']='deletion_pending';self.buffer.posts=[]
        self.run_delete();self.assertEqual(self.pub.records[m.KEY]['state'],'deleted');self.assertFalse(self.buffer.deletions)
if __name__=='__main__':unittest.main()
