"""Optional agent safety tests. Fixtures are not evidence of model quality."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock,patch

import requests
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.agent.openrouter_client import OpenRouter,PilotBlocked,FreeQuotaDeferred,require_free,json_content


def cfg():return json.loads((ROOT/'config/agent-pilot.json').read_text())

def response(status=200,body=None,headers=None):
 r=Mock();r.status_code=status;r.headers=headers or {};r.json.return_value=body or {};return r


class FreeOnlyClientTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.config=cfg();self.session=Mock();self.client=OpenRouter(self.config,self.temp.name,token='test-inference-key',session=self.session,sleep=lambda _:None,clock=lambda:0)
  spec=self.config['roles']['producer']
  self.client.checked['producer']={'model':spec['model'],'provider':spec['provider'],'provider_name':'Nvidia','allowed_response_models':[spec['model']],'parameters':['tools','tool_choice'],'modalities':['text'],'pricing':{'prompt':'0','completion':'0'}}

 def good(self,**extra):
  return {'id':'test-generation','model':self.config['roles']['producer']['model'],'provider':'Nvidia','usage':{'cost':0,'prompt_tokens':10,'completion_tokens':5},'choices':[{'message':{'role':'assistant','content':'{"ok":true}'}}],**extra}

 def test_nonzero_prices_blocked(self):
  for p in [{'prompt':'0.000001','completion':'0'},{'prompt':'0','completion':'0','image':'0.01'},{}]:
   with self.assertRaises(PilotBlocked):require_free(p)
  require_free({'prompt':'0','completion':'0','discount':0})

 def test_production_switch_cannot_run_pilot(self):
  c=cfg();c['production_enabled']=True
  with self.assertRaises(PilotBlocked):OpenRouter(c,self.temp.name,token='test',session=self.session)

 def test_paid_budget_config_is_rejected(self):
  c=cfg();c['max_paid_inference_usd']=1
  with self.assertRaises(PilotBlocked):OpenRouter(c,self.temp.name,token='test',session=self.session)

 def test_zero_cost_exact_model_response_recorded(self):
  self.session.post.return_value=response(body=self.good())
  out=self.client.chat('producer',[{'role':'user','content':'Public evidence only'}])
  self.assertEqual(json_content(out),{'ok':True})
  payload=self.session.post.call_args.kwargs['json']
  self.assertEqual(payload['provider']['max_price'],{'prompt':0,'completion':0})
  self.assertFalse(payload['provider']['allow_fallbacks'])
  self.assertEqual(payload['provider']['only'],['nvidia'])
  self.assertNotIn('models',payload)
  self.assertFalse(self.session.post.call_args.kwargs['allow_redirects'])

 def test_http_200_provider_error_is_recorded_and_halts(self):
  self.session.post.return_value=response(body={'error':{'code':400,'message':'Provider rejected tool response'}})
  with self.assertRaises(PilotBlocked):self.client.chat('producer',[{'role':'user','content':'Public data'}])
  self.assertIn('Provider rejected',self.client.state['calls'][-1]['provider_error']['message'])
  with self.assertRaises(PilotBlocked):self.client.chat('producer',[{'role':'user','content':'No silent replay'}])
  self.assertEqual(self.session.post.call_count,1)

 def test_returned_model_drift_is_blocked(self):
  self.session.post.return_value=response(body=self.good(model='different/model'))
  with self.assertRaises(PilotBlocked):self.client.chat('producer',[{'role':'user','content':'Public data'}])
  self.assertEqual(self.client.state['calls'][-1]['state'],'policy_blocked')

 def test_returned_provider_drift_is_blocked(self):
  self.session.post.return_value=response(body=self.good(provider='Different provider'))
  with self.assertRaises(PilotBlocked):self.client.chat('producer',[{'role':'user','content':'Public data'}])

 def test_unexpected_cost_halts_inference(self):
  self.session.post.return_value=response(body=self.good(usage={'cost':.001}))
  with self.assertRaises(PilotBlocked):self.client.chat('producer',[{'role':'user','content':'Public data'}])
  self.assertEqual(self.session.post.call_count,1)

 def test_byok_upstream_charge_is_not_silently_free(self):
  self.session.post.return_value=response(body=self.good(usage={'cost':0,'cost_details':{'upstream_inference_cost':.01}}))
  with self.assertRaises(PilotBlocked):self.client.chat('producer',[{'role':'user','content':'Public data'}])

 def test_secret_prompt_is_blocked_before_network(self):
  with patch('tools.agent.openrouter_client.contains_secret',return_value=True):
   with self.assertRaises(PilotBlocked):self.client.chat('producer',[{'role':'user','content':'sensitive test fixture'}])
  self.session.post.assert_not_called()

 def test_timeout_is_uncertain_not_replayed(self):
  self.session.post.side_effect=requests.Timeout()
  with self.assertRaises(PilotBlocked):self.client.chat('producer',[{'role':'user','content':'Public data'}])
  self.assertEqual(self.session.post.call_count,1)
  self.assertEqual(self.client.state['calls'][-1]['state'],'uncertain')

 def test_500_after_submit_not_blindly_replayed(self):
  self.session.post.return_value=response(500)
  with self.assertRaises(PilotBlocked):self.client.chat('producer',[{'role':'user','content':'Public data'}])
  self.assertEqual(self.session.post.call_count,1)

 def test_long_429_defers_without_model_change(self):
  self.session.post.return_value=response(429,headers={'Retry-After':'120'})
  with self.assertRaises(FreeQuotaDeferred):self.client.chat('producer',[{'role':'user','content':'Public data'}])
  self.assertEqual(self.session.post.call_count,1)
  self.assertTrue(self.client.state['cooldown_until'])

 def test_call_budget_persists_across_restart(self):
  self.config['limits']['max_calls_per_run']=1
  self.session.post.return_value=response(body=self.good())
  self.client.chat('producer',[{'role':'user','content':'Public data'}])
  second=OpenRouter(self.config,self.temp.name,token='test-inference-key',session=self.session)
  second.checked=self.client.checked
  with self.assertRaises(FreeQuotaDeferred):second.chat('producer',[{'role':'user','content':'No second call'}])
  self.assertEqual(self.session.post.call_count,1)

 def test_reasoning_not_persisted(self):
  data=self.good();data['choices'][0]['message']['reasoning']='internal deliberation not needed in audit'
  self.session.post.return_value=response(body=data)
  out=self.client.chat('producer',[{'role':'user','content':'Public data'}])
  self.assertNotIn('reasoning',out)
  outputs=list(Path(self.temp.name).glob('*-output.json'))
  self.assertNotIn('internal deliberation',outputs[0].read_text())

 def test_endpoint_metadata_requests_are_allowlisted(self):
  with self.assertRaises(PilotBlocked):self.client.get('/keys/create',authenticated=True)
  self.session.get.assert_not_called()

 def test_markdown_response_cannot_pass_as_schema_json(self):
  with self.assertRaises(PilotBlocked):json_content({'content':'```json\n{"ok":true}\n```'})

 def test_probe_workflow_has_no_publishing_credentials_or_schedule(self):
  import yaml
  w=yaml.safe_load((ROOT.parent/'.github/workflows/agent-probe.yml').read_text())
  events=w.get('on') or w.get(True)
  self.assertNotIn('schedule',events)
  self.assertEqual(w['permissions'],{'contents':'read'})
  text=json.dumps(w)
  self.assertNotIn('BUFFER_API_KEY',text);self.assertNotIn('YOUTUBE_OAUTH_JSON',text)
  self.assertNotIn('publish_release.py',text)


if __name__=='__main__':unittest.main()


class CostReceiptTests(unittest.TestCase):
 def test_http200_provider_failure_is_not_reported_as_measured_zero(self):
  from tools.agent.openrouter_client import usage_summary
  report=usage_summary([{'state':'received','http_status':200,'usage':{'cost':0}}, {'state':'policy_blocked','http_status':200,'generation_id':'unknown-cost-generation'}])
  self.assertEqual(report['successful_cost_receipts'],1)
  self.assertEqual(report['missing_or_uncertain_cost_receipts'],1)
  self.assertEqual(report['reported_successful_cost_usd'],'0')
  self.assertEqual(report['baseline_arena_cost'],'unknown')
