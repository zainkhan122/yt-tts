"""Fault injection for evidence, authenticity, tool boundaries and renderer locks."""
import copy
import hashlib
import io
import json
from pathlib import Path
import socket
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import Mock,patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.agent.evidence import EvidenceStore,normalized,safe_url,validate_provenance
from tools.agent.gates import validate_draft,validate_critic
from tools.agent.openrouter_client import PilotBlocked
from tools.agent.prepare import safe_unpack_tar
from tools.agent.producer import compile_brief
from tools.agent.render_case import validate_render_inputs
from tools.post.common import fingerprint,save_json

SOURCE='Example Tool provides 50 credits per day to every account. Unused daily credits do not roll over into another day. The official maker states that Example Tool can create draft presentations from notes.'


def setup_data(tmp):
 case={'id':'test-case','task':'Explain Example Tool','category':'tool','as_of':'2026-10-10','source_hosts':['example.com'],
       'sources':[{'id':'s1','url':'https://example.com/','kind':'primary_source'}]}
 ev=EvidenceStore(case,Path(tmp)/'sources',{'max_source_bytes':10000,'max_source_text_chars':10000,'source_timeout_seconds':10})
 ev.records={'s1':{'id':'s1','url':'https://example.com/','text':SOURCE,'text_sha256':hashlib.sha256(SOURCE.encode()).hexdigest(),'retrieved_at':'2026-10-10T00:00:00Z','kind':'primary_source'}};ev.read_ids={'s1'}
 claims=[{'id':'c1','statement':'The tool provides 50 daily credits.','attribution':'source_fact','supports':[{'source_id':'s1','quote':'Example Tool provides 50 credits per day to every account.'}]},
         {'id':'c2','statement':'Unused daily credits do not roll over.','attribution':'source_fact','supports':[{'source_id':'s1','quote':'Unused daily credits do not roll over into another day.'}]},
         {'id':'c3','statement':'The maker says it can create draft presentations from notes.','attribution':'maker_claim','supports':[{'source_id':'s1','quote':'The official maker states that Example Tool can create draft presentations from notes.'}]}]
 assets={'a1':{'id':'a1','file':'page.jpg','kind':'screenshot','digest':'sha256:'+'a'*64,'source_url':'https://example.com/','usage_basis':'shadow comparison only'},
         'a2':{'id':'a2','file':'demo.mp4','kind':'maker_demo','duration_seconds':20,'digest':'sha256:'+'b'*64,'source_url':'https://example.com/','usage_basis':'registered demonstration for shadow comparison'}}
 texts=[('hook','Example Tool gives you a simple way to create draft presentations, but its free allowance has limits.','a1',['c3']),
        ('proof','The official page states that every account receives fifty daily credits, rather than unlimited free generation.','a2',['c1']),
        ('steps','You can start a draft, check the result carefully, and decide whether the tool fits your workflow.','a1',['c3']),
        ('metric','The documented daily allowance is fifty credits, and unused credits do not roll into the next day.',None,['c1','c2']),
        ('catch','That reset matters when you plan repeated work, so do not assume unused credits remain available later.',None,['c2']),
        ('cta','Would a small daily allowance fit your workflow? Comment TOOLS.',None,[])]
 scenes=[]
 for kind,say,aid,ids in texts:
  scenes.append({'id':kind,'kind':kind,'statement_type':'cta' if kind=='cta' else 'factual','say':say,'claim_ids':ids,'asset_id':aid,
                 'asset_usage':'evidence' if aid else 'none','headline':'EXAMPLE TOOL' if kind=='hook' else 'READ THE LIMITS','subtext':'Check before using',
                 'bullets':['Create a draft','Review the result'] if kind=='steps' else ['Daily credits expire'] if kind=='catch' else [],
                 'metric':{'value':50,'prefix':'','suffix':'','label':'credits per day','claim_id':'c1','decimals':0} if kind=='metric' else None,'clip_start':0})
 draft={'version':1,'topic':'Example Tool daily allowance','keyword':'Example Tool','angle':'A useful tool with an explicit daily-credit limitation.','claims':claims,'scenes':scenes,
        'metadata':{'title':'Example Tool: What Its Free Credits Really Mean','youtube_description':'Example Tool provides a documented daily allowance. Check how credits work and review generated drafts before using them.','instagram_caption':'Example Tool has a daily allowance. Check the limits.','facebook_caption':'Example Tool helps with drafts, but daily credits reset.','hashtags':['#AItools','#Productivity','#Hypeless'],'tags':['Example Tool','AI tools','presentation tool','daily credits'],'cta_keyword':'TOOLS'},'limitations':['Daily credits do not roll over to another day.']}
 return case,ev,assets,draft


class EvidenceAndDraftTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
  self.case,self.ev,self.assets,self.draft=setup_data(self.t.name)

 def gate(self,d=None):return validate_draft(d or self.draft,self.ev,self.assets)

 def test_valid_traceable_fixture_passes_structure_not_truth_certificate(self):
  r=self.gate();self.assertTrue(r['passed'],r['errors']);self.assertIn('not entailment',r['warning'])

 def test_fabricated_quote_is_blocked(self):
  self.draft['claims'][0]['supports'][0]['quote']='Example Tool provides 500 credits per day to every account.'
  self.assertFalse(self.gate()['passed'])

 def test_unread_source_cannot_be_cited(self):
  self.ev.read_ids.clear();self.assertFalse(self.gate()['passed'])

 def test_typography_variation_does_not_change_evidence_words(self):
  text="The maker’s free plan includes 50 credits — the allowance is not unlimited."
  self.ev.records['s1']['text']=text
  self.ev.records['s1']['text_sha256']=hashlib.sha256(text.encode()).hexdigest()
  ref={'source_id':'s1','quote':"The maker's free plan includes 50 credits - the allowance is not unlimited."}
  self.assertEqual(self.ev.citation(ref)['source_id'],'s1')
  ref['quote']=ref['quote'].replace('not unlimited','unlimited')
  with self.assertRaises(PilotBlocked):self.ev.citation(ref)

 def test_protocol_integer_is_explicit_and_still_strict(self):
  from tools.agent.gates import DRAFT_SCHEMA
  self.assertEqual(DRAFT_SCHEMA['properties']['version']['type'],'integer')
  self.draft['version']='1'
  self.assertFalse(self.gate()['passed'])

 def test_tampered_snapshot_hash_is_blocked(self):
  self.ev.records['s1']['text']+=' fabricated addendum'
  self.assertFalse(self.gate()['passed'])

 def test_fake_test_attribution_is_blocked(self):
  self.draft['claims'][0]['attribution']='recorded_observation'
  self.assertFalse(self.gate()['passed'])

 def test_i_tested_claim_blocked_without_new_demo(self):
  self.draft['scenes'][1]['say']='I tested this product myself and confirmed that it works exactly as the creator claims.'
  self.assertTrue(any('hands-on' in x for x in self.gate()['errors']))

 def test_factual_scene_cannot_omit_claim_links(self):
  self.draft['scenes'][1]['claim_ids']=[];self.assertFalse(self.gate()['passed'])

 def test_unknown_claim_id_is_blocked(self):
  self.draft['scenes'][1]['claim_ids']=['c99'];self.assertFalse(self.gate()['passed'])

 def test_duplicate_claims_and_scenes_blocked(self):
  self.draft['claims'][1]['id']='c1';self.draft['scenes'][1]['id']='hook'
  self.assertFalse(self.gate()['passed'])

 def test_unsupported_metric_rejected(self):
  self.draft['scenes'][3]['metric']['value']=999
  self.assertTrue(any('metric number absent' in x for x in self.gate()['errors']))

 def test_voice_override_cannot_be_added(self):
  self.draft['voice']='different-voice';self.assertFalse(self.gate()['passed'])

 def test_executable_html_is_blocked(self):
  self.draft['metadata']['youtube_description']+='<script>doSomething()</script>'
  self.assertFalse(self.gate()['passed'])

 def test_unknown_asset_is_blocked(self):
  self.draft['scenes'][0]['asset_id']='imaginary-file';self.assertFalse(self.gate()['passed'])

 def test_illustration_cannot_be_evidence(self):
  self.assets['a1']['kind']='illustration';self.assertFalse(self.gate()['passed'])

 def test_video_cannot_be_still_background(self):
  self.draft['scenes'][2]['asset_id']='a2';self.assertFalse(self.gate()['passed'])

 def test_missing_explicit_catch_is_blocked(self):
  self.draft['scenes'][4]['kind']='proof';self.assertFalse(self.gate()['passed'])

 def test_metric_editorial_loophole_is_blocked(self):
  self.draft['scenes'][1].update(statement_type='editorial',say='It gives every user 999 free credits every day, which should be enough for your next project.')
  self.assertFalse(self.gate()['passed'])

 def test_fabricated_pinned_comment_promise_blocked(self):
  self.draft['scenes'][-1]['say']='Comment TOOLS and I will pin the link for you.'
  self.assertFalse(self.gate()['passed'])

 def test_critic_cannot_average_away_material_error(self):
  review={'verdict':'pass','all_material_claims_accounted_for':True,'scores':{'facts':4,'authenticity':4,'script':4},'issues':[{'severity':'major','area':'facts','scene_id':'price','finding':'Wrong price stated in the video.','evidence_ids':['s1'],'required_fix':'Correct the price using the actual source.'}],'summary':'Polished, but the material error must block.'}
  self.assertFalse(validate_critic(review)[0])

 def test_compiler_locks_voice_template_namespace_and_question(self):
  b=compile_brief(self.draft,self.case,self.assets,'pilot1',0)
  self.assertTrue(b['id'].startswith('shadow-'));self.assertEqual(b['template'],'tool-spotlight')
  for key in ['voice','tts','voice_fx']:self.assertNotIn(key,b)
  self.assertFalse(b['pilot']['publishing_allowed'])
  self.assertEqual(b['scenes'][-1]['question'],'READ THE LIMITS')
  self.assertEqual(b['scenes'][2]['url'],'example.com')


class URLArchiveAndRenderTests(unittest.TestCase):
 def resolve(self,*args,**kwargs):return [(socket.AF_INET,socket.SOCK_STREAM,6,'',('8.8.8.8',443))]

 def test_only_explicit_https_hosts_allowed(self):
  self.assertEqual(safe_url('https://example.com/page',['example.com'],self.resolve),'https://example.com/page')
  for u in ['http://example.com','https://evil.invalid','file:///etc/passwd','https://user:pass@example.com','https://example.com:8443','https://example.com/?api_key=hidden']:
   with self.assertRaises(PilotBlocked):safe_url(u,['example.com'],self.resolve)

 def test_private_and_metadata_ip_dns_are_blocked(self):
  for ip in ['127.0.0.1','10.0.0.1','169.254.169.254','::1']:
   with self.assertRaises(PilotBlocked):safe_url('https://example.com',['example.com'],lambda *a,**k:[(socket.AF_INET,socket.SOCK_STREAM,6,'',(ip,443))])

 def test_arbitrary_source_id_does_not_make_request(self):
  with tempfile.TemporaryDirectory() as tmp:
   case,ev,_,_=setup_data(tmp);ev.session=Mock()
   with self.assertRaises(PilotBlocked):ev.read_source('http://169.254.169.254')
   ev.session.get.assert_not_called()

 def test_asset_path_escape_is_rejected(self):
  for name in ['../secret.jpg','/root/token.jpg','https://evil.invalid/a.jpg','sub/file.jpg']:
   with self.assertRaises(PilotBlocked):validate_provenance({'file':name,'digest':'sha256:'+'a'*64,'source_url':'https://example.com','kind':'screenshot','usage_basis':'test'})

 def test_missing_asset_provenance_is_rejected(self):
  with self.assertRaises(PilotBlocked):validate_provenance({'file':'a.jpg','digest':'sha256:'+'a'*64})

 def test_tar_traversal_and_symlink_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   for name,symlink in [('pack/../../outside',False),('pack/link',True)]:
    p=Path(tmp)/'bad.tar'
    with tarfile.open(p,'w') as t:
     m=tarfile.TarInfo(name)
     if symlink:m.type=tarfile.SYMTYPE;m.linkname='/etc/passwd';t.addfile(m)
     else:m.size=3;t.addfile(m,io.BytesIO(b'bad'))
    with self.assertRaises(PilotBlocked):safe_unpack_tar(p,Path(tmp)/'dest','pack')

 def test_modified_candidate_cannot_render_after_review(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);case,ev,assets,draft=setup_data(tmp);brief=compile_brief(draft,case,assets,'test',0)
   state={'status':'ready_for_shadow_render','publishing_allowed':False,'last_gate':{'passed':True},'critic':{'verdict':'pass'},'candidate_id':brief['id'],'compiled_brief_sha256':fingerprint(brief)}
   brief['scenes'][0]['say']='Changed after independent review'
   save_json(p/'agent-state.json',state);save_json(p/'candidate-brief.json',brief)
   with self.assertRaises(PilotBlocked):validate_render_inputs(p)

 def test_workflow_has_no_social_credentials_or_cron(self):
  import yaml
  w=yaml.safe_load((ROOT.parent/'.github/workflows/agent-pilot.yml').read_text())
  events=w.get('on') or w.get(True);self.assertNotIn('schedule',events)
  self.assertEqual(w['permissions'],{'contents':'read'})
  text=json.dumps(w);self.assertNotIn('BUFFER_API_KEY',text);self.assertNotIn('YOUTUBE_OAUTH_JSON',text)
  self.assertNotIn('publish_release.py',text);self.assertNotIn('queue_ctl.py',text)


if __name__=='__main__':unittest.main()
