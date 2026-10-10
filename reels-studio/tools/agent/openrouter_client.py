"""Free-only, pinned OpenRouter client. No model/provider fallback or auto-router.
Only this module handles the inference key; prompts/tools never receive it.
"""
import datetime as dt
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import time
import uuid

import requests

from lib.secrets import contains_secret, openrouter_token, redact, register_sensitive
from tools.post.common import iso, now_utc, save_json
from tools.post.buffer_api import retry_after

BASE='https://openrouter.ai/api/v1'


class PilotBlocked(RuntimeError):
    pass


class FreeQuotaDeferred(PilotBlocked):
    pass


def require_free(pricing):
    if not isinstance(pricing,dict) or 'prompt' not in pricing or 'completion' not in pricing:
        raise PilotBlocked('Missing authoritative pricing; no inference request sent')
    for name,value in pricing.items():
        if name=='discount':continue
        try:
            if value is not None and Decimal(str(value))!=0:
                raise PilotBlocked('Nonzero price rejected: '+name)
        except InvalidOperation:
            raise PilotBlocked('Unrecognized price field: '+name)


class OpenRouter:
    def __init__(self, config, work, *, token=None, session=None, sleep=time.sleep, clock=time.monotonic):
        self.config=config;self.work=Path(work);self.work.mkdir(parents=True,exist_ok=True)
        self.session=session or requests.Session();self.sleep=sleep;self.clock=clock;self.last_call=None
        self.token=token or openrouter_token()
        if not self.token:raise PilotBlocked('OPENROUTER_API_KEY is missing; no real-model results can be claimed')
        register_sensitive(self.token)
        if config.get('max_paid_inference_usd')!=0 or config.get('inference_policy')!='free_only':
            raise PilotBlocked('This pilot is authorized for free-only inference')
        if config.get('publishing_enabled') or config.get('production_enabled'):
            raise PilotBlocked('Shadow pilot cannot run with production/publishing enabled')
        if config.get('routing',{}).get('data_collection')=='allow' and not config.get('provider_training_consent',{}).get('approved'):
            raise PilotBlocked('Provider training/retention requires explicit owner consent')
        self.path=self.work/'calls.json'
        self.state=json.loads(self.path.read_text()) if self.path.exists() else {'version':1,'calls':[],'reported_cost_usd':'0','cooldown_until':None}
        self.checked={}

    def _persist(self):
        save_json(self.path,self.state)

    def get(self,path,params=None,authenticated=False):
        allowed=path=='/key' or path=='/models' or path.startswith('/models/') or path=='/generation'
        if not allowed or '..' in path:raise PilotBlocked('OpenRouter metadata path not allowed')
        h={'Accept':'application/json'}
        if authenticated:h['Authorization']='Bearer '+self.token
        r=self.session.get(BASE+path,headers=h,params=params,timeout=(10,35),allow_redirects=False)
        if r.status_code!=200:raise PilotBlocked('OpenRouter metadata unavailable: HTTP '+str(r.status_code))
        try:return r.json()
        except ValueError:raise PilotBlocked('Malformed OpenRouter metadata')

    def preflight(self):
        raw=self.get('/key',authenticated=True).get('data',{})
        if raw.get('is_management_key'):raise PilotBlocked('Use an inference key, not a management key')
        account={k:raw.get(k) for k in ['limit','limit_remaining','limit_reset','is_free_tier','free_model_daily_requests']}
        save_json(self.work/'account-check.json',account)
        remaining=(raw.get('free_model_daily_requests') or {}).get('remaining')
        if remaining is not None and remaining<=0:raise FreeQuotaDeferred('Free-model daily quota exhausted; no paid fallback')
        catalog={m['id']:m for m in self.get('/models').get('data',[])}
        for role,spec in self.config['roles'].items():
            mid=spec['model']
            if not mid.endswith(':free') or mid.startswith('openrouter/'):
                raise PilotBlocked('Only explicitly pinned free variants are allowed')
            m=catalog.get(mid)
            if not m:raise PilotBlocked(role+': pinned model no longer in catalog')
            require_free(m.get('pricing'))
            mods=(m.get('architecture') or {}).get('input_modalities',[])
            if not set(spec['input_modalities']).issubset(set(mods)):
                raise PilotBlocked(role+': required input capability is unavailable')
            endpoints=self.get('/models/'+mid+'/endpoints').get('data',{}).get('endpoints',[])
            found=[e for e in endpoints if e.get('tag')==spec['provider'] and e.get('name')==spec['expected_endpoint_name']]
            if len(found)!=1:raise PilotBlocked(role+': pinned provider/version changed or is unavailable')
            e=found[0];require_free(e.get('pricing'))
            canonical=e['name'].split(' | ',1)[-1]
            self.checked[role]={'model':mid,'provider':spec['provider'],'provider_name':e.get('provider_name'),
                'endpoint_name':e['name'],'allowed_response_models':sorted({mid,mid.removesuffix(':free'),canonical,canonical.removesuffix(':free')}),
                'parameters':e.get('supported_parameters',[]),'modalities':mods,'pricing':e['pricing']}
        save_json(self.work/'model-lock-check.json',self.checked)
        return account

    def _receipt(self,body,role):
        spec=self.checked[role]
        if body.get('model') not in spec['allowed_response_models']:
            raise PilotBlocked('Returned model differs from pinned model/version')
        usage=body.get('usage') or {}
        serving=body.get('provider')
        if not serving or usage.get('cost') is None:
            gid=body.get('id')
            if not gid:raise PilotBlocked('Missing model/provider/cost receipt')
            meta=self.get('/generation',params={'id':gid},authenticated=True).get('data',{})
            serving=serving or meta.get('provider_name')
            if usage.get('cost') is None:usage['cost']=meta.get('total_cost')
            if meta.get('upstream_inference_cost') is not None:
                usage.setdefault('cost_details',{})['upstream_inference_cost']=meta['upstream_inference_cost']
        if str(serving).casefold()!=str(spec['provider_name']).casefold():
            raise PilotBlocked('Serving provider changed; no fallback is permitted')
        if usage.get('cost') is None:raise PilotBlocked('Unknown inference cost; cannot claim zero cost')
        try:
            if Decimal(str(usage['cost']))!=0 or Decimal(str((usage.get('cost_details') or {}).get('upstream_inference_cost') or 0))!=0:
                raise PilotBlocked('Unexpected nonzero charge; halt all further inference')
        except InvalidOperation:raise PilotBlocked('Invalid cost receipt')
        return {k:usage.get(k) for k in ['prompt_tokens','completion_tokens','total_tokens','cost','cost_details','completion_tokens_details']}

    def chat(self,role,messages,*,tools=None,tool_choice=None,max_tokens=None,label='call'):
        if self.state.get('halted'):raise PilotBlocked('Pilot inference halted after an uncertain/policy-invalid result; inspect receipts')
        if role not in self.checked:raise PilotBlocked('Model/account preflight must pass first')
        spec=self.config['roles'][role];lock=self.checked[role];limits=self.config['limits']
        if contains_secret(json.dumps(messages,ensure_ascii=False)):
            raise PilotBlocked('Credential-like content rejected before sending a prompt')
        route={**self.config['routing'],'only':[spec['provider']],'order':[spec['provider']]}
        if route.get('allow_fallbacks') is not False:raise PilotBlocked('Provider fallbacks must remain disabled')
        body={'model':spec['model'],'messages':messages,'provider':route,'temperature':0.2,
              'max_tokens':max_tokens or spec['max_tokens'],'stream':False}
        if 'reasoning' in lock['parameters']:body['reasoning']={'effort':'medium','exclude':True}
        if tools:body['tools']=tools
        if tool_choice is not None:
            if 'tool_choice' not in lock['parameters']:raise PilotBlocked('Pinned model lacks required tool-choice support')
            body['tool_choice']=tool_choice
        headers={'Authorization':'Bearer '+self.token,'Content-Type':'application/json','X-OpenRouter-Title':'Hypeless shadow comparison'}
        for attempt in range(limits['max_safe_attempts']):
            if len(self.state['calls'])>=limits['max_calls_per_run']:raise FreeQuotaDeferred('Per-run inference-call cap reached')
            if self.state.get('cooldown_until') and dt.datetime.fromisoformat(self.state['cooldown_until'].replace('Z','+00:00'))>now_utc():
                raise FreeQuotaDeferred('Persisted model cooldown remains active')
            if self.last_call is not None:
                pause=limits['minimum_request_interval_seconds']-(self.clock()-self.last_call)
                if pause>0:self.sleep(pause)
            self.last_call=self.clock()
            record={'request_id':str(uuid.uuid4()),'role':role,'model':spec['model'],'provider':spec['provider'],'label':label,
                    'requested_at':iso(now_utc()),'request_sha256':hashlib.sha256(json.dumps(body,sort_keys=True).encode()).hexdigest(),'state':'submitting'}
            self.state['calls'].append(record);self._persist() # write before the potentially accepted request
            try:
                r=self.session.post(BASE+'/chat/completions',headers=headers,json=body,timeout=(15,300),allow_redirects=False)
            except (requests.Timeout,requests.ConnectionError):
                record['state']='uncertain';self.state['halted']=True;self._persist()
                raise PilotBlocked('Inference response lost; hold instead of silently repeating or changing models')
            record['http_status']=r.status_code
            if r.status_code==429:
                wait=retry_after(r.headers)
                record.update(state='rejected_rate_limit',retry_after_seconds=wait)
                self.state['cooldown_until']=iso(now_utc()+dt.timedelta(seconds=max(wait,1)));self._persist()
                if wait>limits['max_inline_wait_seconds'] or attempt+1>=limits['max_safe_attempts']:
                    raise FreeQuotaDeferred('Free inference rate limit; no paid fallback')
                self.sleep(max(wait,1)+1);self.state['cooldown_until']=None;continue
            if r.status_code!=200:
                try:
                    error=r.json().get('error',{})
                    detail=redact(str(error.get('message','Request rejected')))[:700]
                    record['provider_error']={'code':error.get('code'),'message':detail}
                except (ValueError,AttributeError):
                    detail='Unparseable provider error'
                record['state']='blocked' if r.status_code<500 else 'uncertain';self._persist()
                raise PilotBlocked(f'Pinned free inference failed (HTTP {r.status_code}): {detail}; model unchanged')
            try:
                result=r.json()
                if not isinstance(result,dict):raise ValueError()
                if result.get('error'):
                    error=result['error'];detail=redact(str(error.get('message','Provider rejected the completion')))[:700]
                    record['provider_error']={'code':error.get('code'),'message':detail}
                    record['generation_id']=result.get('id')
                    raise PilotBlocked('Provider returned an error inside HTTP 200: '+detail)
                usage=self._receipt(result,role)
                message=result['choices'][0]['message']
                if contains_secret(json.dumps(message,ensure_ascii=False)):
                    raise PilotBlocked('Credential-like content in model output; quarantined')
            except (ValueError,KeyError,IndexError,TypeError):
                record['state']='uncertain';self.state['halted']=True;self._persist();raise PilotBlocked('Malformed inference receipt; hold')
            except PilotBlocked as exc:
                record.update(state='policy_blocked',error=redact(str(exc)));self.state['halted']=True;self._persist();raise
            # Do not persist raw reasoning/chain-of-thought. Keep final structured output and auditable receipts.
            public_message={k:message[k] for k in ['role','content','tool_calls'] if k in message}
            record.update(state='received',generation_id=result.get('id'),returned_model=result.get('model'),serving_provider=lock['provider_name'],usage=usage)
            self._persist()
            save_json(self.work/(record['request_id']+'-output.json'),public_message)
            return public_message
        raise FreeQuotaDeferred('Safe retry limit reached')


def json_content(message):
    text=message.get('content') or ''
    if not isinstance(text,str):raise PilotBlocked('Expected a JSON text answer')
    if text.strip().startswith('```'):raise PilotBlocked('Markdown fences are not a structured JSON result')
    try:
        result=json.loads(text)
        if not isinstance(result,dict):raise ValueError()
        return result
    except ValueError:raise PilotBlocked('Model answer is not a valid JSON object')
