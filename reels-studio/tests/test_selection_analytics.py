import datetime as dt
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import selection_analytics as a

NOW=dt.datetime(2026,11,6,tzinfo=dt.timezone.utc)
def snap(views, age=36, taken='2026-11-05T12:00:00Z'):
    return {'views':views,'age_hours':age,'taken_at':taken}
class AnalyticsSelectionTests(unittest.TestCase):
    def test_future_and_wrong_age_not_used_and_one_row_per_video(self):
        data={'videos':{'v':{'snapshots':[snap(50),snap(500,36,'2026-11-07T12:00:00Z'),snap(400,100),snap(60,37)]}}}
        self.assertEqual(a.cohort(data,NOW)[0]['views'],50)
        self.assertEqual(len(a.cohort(data,NOW)),1)
    def test_analytics_changes_order_and_is_not_fake_candidate_performance(self):
        rows=[{'video_id':v,'views':x,'age_hours':36,'taken_at':'2026-11-05T12:00:00Z'} for v,x in [('repo-coop-anything-01',100),('news-gemini-agent-01',80),('repo-whatsapp-mcp-01',60),('x',20),('y',20),('z',20),('w',20)]]
        agent=a.score_candidate({'name':'agent-desktop'},rows,2)
        generic=a.score_candidate({'name':'unmatched-tool'},rows,2)
        self.assertGreater(agent['total_score'],generic['total_score'])
        self.assertEqual(agent['analytics']['comparisons'][0]['n'],3)
        self.assertEqual(generic['analytics']['status'],'insufficient evidence')
    def test_missing_or_too_few_rows_are_neutral(self):
        self.assertEqual(a.signal({'name':'agent'},[])['adjustment'],0)
        rows=[{'video_id':str(i),'views':i,'age_hours':36} for i in range(5)]
        self.assertEqual(a.signal({'name':'agent'},rows)['adjustment'],0)
