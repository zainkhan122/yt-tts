import hashlib
import tempfile
import unittest
from pathlib import Path
from tools.youtube.approved_cover_backlog import classify

class BacklogTests(unittest.TestCase):
    def test_only_approved_matching_files_are_pending(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'repo-demo-01.png'; p.write_bytes(b'approved')
            digest = 'sha256:' + hashlib.sha256(p.read_bytes()).hexdigest()
            records = {'a': {'video_id':'repo-demo-01','platform':'youtube','state':'sent','youtube_id':'ABCDEFGHIJK'},
                       'b': {'video_id':'repo-other-01','platform':'youtube','state':'sent','youtube_id':'ABCDEFGHIJL'},
                       'c': {'video_id':'repo-future-01','platform':'youtube','state':'scheduled','youtube_id':'ABCDEFGHIJM'}}
            approvals = {'repo-demo-01': {'file':p.name,'sha256':digest}}
            rows = classify(records, {}, approvals, td)
            self.assertEqual([r['status'] for r in rows], ['pending','needs_approved_design'])
            self.assertEqual(classify(records, {'ABCDEFGHIJK':{'thumbnail_confirmed':True,'thumbnail_digest':digest}}, approvals, td)[0]['status'], 'confirmed')
            p.write_bytes(b'tampered')
            self.assertEqual(classify(records, {}, approvals, td)[0]['status'], 'invalid_approval')

    def test_manual_needs_explicit_eligibility(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'repo-demo-01.png';p.write_bytes(b'cover')
            digest='sha256:'+hashlib.sha256(p.read_bytes()).hexdigest()
            rec={'a':{'video_id':'repo-demo-01','platform':'youtube','state':'published_manual','youtube_id':'ABCDEFGHIJK'}}
            appr={'repo-demo-01':{'file':p.name,'sha256':digest}}
            self.assertEqual(classify(rec,{},appr,td),[])
            appr['repo-demo-01']['manual_cover_eligible']=True
            self.assertEqual(classify(rec,{},appr,td)[0]['status'],'pending')

    def test_new_approval_reopens_old_block(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'repo-demo-01.png';p.write_bytes(b'new')
            digest='sha256:'+hashlib.sha256(p.read_bytes()).hexdigest()
            rec={'a':{'video_id':'repo-demo-01','platform':'youtube','state':'sent','youtube_id':'ABCDEFGHIJK'}}
            approved={'repo-demo-01':{'file':p.name,'sha256':digest}}
            old={'ABCDEFGHIJK':{'thumbnail_blocked':True,'thumbnail_digest':'sha256:'+'0'*64}}
            self.assertEqual(classify(rec,old,approved,td)[0]['status'],'pending')
            old['ABCDEFGHIJK']['thumbnail_digest']=digest
            self.assertEqual(classify(rec,old,approved,td)[0]['status'],'blocked_review')
            old['ABCDEFGHIJK'].update(cover_existing_custom_hold=True, cover_hold_digest=digest)
            self.assertEqual(classify(rec,old,approved,td)[0]['status'],'existing_custom_preserved')

if __name__ == '__main__': unittest.main()
