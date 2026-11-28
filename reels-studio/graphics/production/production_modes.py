"""Mode decision and explicit verification status; never convert simulation into evidence."""
from dataclasses import dataclass

class ModeError(ValueError):pass

@dataclass(frozen=True)
class ModeCapability:
    mode:str
    operations:frozenset[str]
    status:str   # available, unavailable, unconfigured, authorization_unknown
    verified:bool
    reason:str
    def __post_init__(self):
        if self.mode not in {'screen_demo','ai_visual','motion_graphics'} or self.status not in {'available','unavailable','unconfigured','authorization_unknown'}:raise ModeError('Invalid mode capability')
        if not self.reason:raise ModeError('Capability reason required')

def choose_mode(*,intent,required_operations,capabilities,permitted_fallback=None):
    """Choose from actual declared runtime capability; explicit fallback required."""
    preferred={'real_application_action':'screen_demo','visual_storytelling':'ai_visual','process_or_chart':'motion_graphics'}
    if intent not in preferred:raise ModeError('Unknown visual intent')
    by={c.mode:c for c in capabilities};requested=preferred[intent];cap=by.get(requested)
    if cap and cap.status=='available' and cap.verified and set(required_operations)<=cap.operations:
        return {'mode':requested,'fallback':False,'label':'actual' if requested=='screen_demo' else 'illustrative'}
    if not permitted_fallback:raise ModeError('Preferred capability unavailable or unsupported; no permitted fallback')
    fallback=by.get(permitted_fallback)
    if not fallback or fallback.status!='available' or not fallback.verified or not set(required_operations)<=fallback.operations:raise ModeError('Fallback unavailable or unsupported')
    return {'mode':fallback.mode,'fallback':True,'label':'illustrative recreation','reason':f'{requested} could not execute requested operation'}

def verify_evidence(*,mode,asset_hash_ok,action_observed,timing_checked,visibility_checked,readability_checked,audiovisual_reviewed):
    if mode not in {'screen_demo','ai_visual','motion_graphics'}:raise ModeError('Unknown mode')
    facts={'asset_hash_ok':asset_hash_ok,'action_observed':action_observed,'timing_checked':timing_checked,'visibility_checked':visibility_checked,'readability_checked':readability_checked,'audiovisual_reviewed':audiovisual_reviewed}
    if any(type(v)!=bool for v in facts.values()):raise ModeError('Verification must be explicit booleans')
    return {'mode':mode,'checks':facts,'status':'reviewed' if all(facts.values()) else 'blocked','missing':[k for k,v in facts.items() if not v]}

def plan_beat_mode(*,beat_id,intent,visual_objective,assets,operations,expected_result,constraints,verification_method,capabilities,permitted_fallback=None):
    """Bind an existing semantic beat to a declared execution-mode decision.

    This is an explicit callable integration point, not an autonomous model or
    evidence that the selected adapter can reproduce the narrative correctly.
    """
    if not all(isinstance(x,str) and x.strip() for x in (beat_id,visual_objective,expected_result,verification_method)):raise ModeError('Beat purpose, expected result and verification method required')
    if not isinstance(assets,list) or not assets or not all(isinstance(a,str) and a for a in assets):raise ModeError('Required assets must be identified')
    if not isinstance(operations,list) or not operations or not all(isinstance(a,str) and a for a in operations):raise ModeError('Required operations must be identified')
    if not isinstance(constraints,list) or not all(isinstance(a,str) and a for a in constraints):raise ModeError('Invalid execution constraints')
    selected=choose_mode(intent=intent,required_operations=operations,capabilities=capabilities,permitted_fallback=permitted_fallback)
    return {'beat_id':beat_id,'intent':intent,'visual_objective':visual_objective,'required_assets':assets,'required_operations':operations,'expected_result':expected_result,'constraints':constraints,'acceptable_fallback':permitted_fallback,'verification_method':verification_method,'selection':selected}

# Extended opt-in integration. Legacy ModeCapability/choose_mode are preserved,
# but the automated planner below does not use their caller-supplied `verified` flag.
from dataclasses import field
import json
import hashlib

_PREFLIGHT_ISSUER=object()
@dataclass(frozen=True)
class PreflightReceipt:
    mode:str
    operations:tuple[str,...]
    adapter_id:str
    provider:str
    model:str
    detail:str
    _issuer:object=field(default=None,repr=False,compare=False)

@dataclass(frozen=True)
class ModeRuntime:
    """Capability metadata + configured adapter; not an assertion of success."""
    capability:ModeCapability
    adapter_id:str
    provider:str
    model:str
    adapter:object

def run_mode_preflight(runtime,operations):
    """Run an adapter's non-destructive preflight; record a process-local receipt.

    A preflight is not an executed action or verified output. The adapter itself
    is part of the trust boundary and must not issue side effects during preflight.
    """
    if not isinstance(runtime,ModeRuntime) or not all(isinstance(x,str) and x for x in (runtime.adapter_id,runtime.provider,runtime.model)):
        raise ModeError('Invalid runtime identity')
    c=runtime.capability
    if c.status!='available' or not set(operations)<=c.operations:raise ModeError('Mode unconfigured, unavailable or unsupported')
    if not operations or not all(isinstance(x,str) and x for x in operations):raise ModeError('Required operations are missing')
    probe=getattr(runtime.adapter,'preflight',None)
    if not callable(probe):raise ModeError('Runtime has no preflight implementation')
    try:r=probe(tuple(operations))
    except Exception as exc:raise ModeError('Mode preflight failed: '+type(exc).__name__) from exc
    if not isinstance(r,dict) or set(r)!={'ok','detail'} or r['ok'] is not True or not isinstance(r['detail'],str) or not r['detail'].strip():raise ModeError('Mode preflight did not succeed')
    return PreflightReceipt(c.mode,tuple(sorted(set(operations))),runtime.adapter_id,runtime.provider,runtime.model,r['detail'],_PREFLIGHT_ISSUER)

def _nonempty_strings(v):return isinstance(v,list) and bool(v) and all(isinstance(x,str) and x.strip() for x in v)

def select_auditable_modes(scheduled,intents,catalog,runtimes,*,fallback_policy=()):
    """Select from model-authored intent and *executed preflight*, not declared availability.

    Result is a planning record only. All beats remain unexecuted and unverified;
    success here is not permission to publish or evidence of visual quality.
    """
    if not isinstance(intents,dict) or set(intents)!={b['id'] for b in scheduled['beats']}:raise ModeError('Mode intent required for every beat')
    expected_intents={'real_application_action':'screen_demo','visual_storytelling':'ai_visual','process_or_chart':'motion_graphics'}
    allowed_modes=set(expected_intents.values());policy=set(tuple(x) for x in fallback_policy);result=[]
    for beat in scheduled['beats']:
        item=intents[beat['id']]
        required={'intent','mode_operations','rationale','expected_result','verification','acceptable_fallback','continuity'}
        if not isinstance(item,dict) or set(item)!=required:raise ModeError('Invalid mode-intent fields for '+beat['id'])
        intent=item['intent'];ops=item['mode_operations']
        if intent not in {*expected_intents,'hybrid'} or not isinstance(ops,dict) or not ops or set(ops)-allowed_modes:raise ModeError('Invalid mode intent')
        if not all(_nonempty_strings(v) for v in ops.values()):raise ModeError('Operation lists required')
        if not all(isinstance(item[k],str) and item[k].strip() for k in ('rationale','expected_result','continuity')) or not _nonempty_strings(item['verification']):raise ModeError('Rationale, expected result and verification required')
        primary=list(ops) if intent=='hybrid' else [expected_intents[intent]]
        if intent=='hybrid' and len(primary)<2:raise ModeError('Hybrid requires at least two distinct modes')
        if any(x not in ops for x in primary):raise ModeError('Required mode operations missing')
        fallback=item['acceptable_fallback'];chosen=[];preflights=[];deviations=[]
        for mode in primary:
            runtime=runtimes.get(mode)
            try:
                if runtime is None or runtime.capability.mode!=mode:raise ModeError('Mode runtime absent or mismatched')
                receipt=run_mode_preflight(runtime,ops[mode]);selected=mode
            except ModeError as reason:
                if intent=='hybrid' or not isinstance(fallback,str) or (mode,fallback) not in policy or fallback not in ops:raise ModeError(f"{beat['id']}: {mode} unavailable; no approved executable fallback") from reason
                alt=runtimes.get(fallback)
                if alt is None or alt.capability.mode!=fallback:raise ModeError('Approved fallback runtime absent or mismatched')
                receipt=run_mode_preflight(alt,ops[fallback]);selected=fallback
                deviations.append({'from':mode,'to':fallback,'disclosure':'illustrative recreation; not actual application/device action','reason':'required mode did not pass preflight'})
            chosen.append(selected);preflights.append({'mode':receipt.mode,'operations':list(receipt.operations),'adapter_id':receipt.adapter_id,'provider':receipt.provider,'model':receipt.model,'detail':receipt.detail})
        # Asset provenance is attached separately based on actual layer bindings
        result.append({'beat_id':beat['id'],'narration':beat['narration'],'start':beat['start'],'end':beat['end'],
            'intent':intent,'selected_mode':'hybrid' if len(chosen)>1 else chosen[0], 'components':chosen,
            'rationale':item['rationale'],'visual_objective':beat['visual_objective'],'expected_result':item['expected_result'],
            'required_operations':{m:ops[m] for m in chosen},'continuity':item['continuity'],'transition':beat['transition'],
            'events':[{'id':e['id'],'action':e['action'],'start':e['audio_time'],'end':e['end_time']} for e in beat['events']],
            'preflights':preflights,'fallbacks':deviations,'verification_checklist':item['verification'],
            'lifecycle':{'declared':True,'configured':True,'preflight':'passed','executed':False,'output_verified':False,'human_reviewed':False},
            'acceptance_status':'not_executed'})
    return result

def attach_asset_provenance(mode_plan,design,catalog):
    """Bind actual layer assets and hashes, never merely a model's asset description."""
    for b in mode_plan:
        layout=design['beats'][b['beat_id']];ids=sorted({x['asset'] for x in layout['layers']})
        if not ids or any(x not in catalog for x in ids):raise ModeError('Mode plan has missing rendered assets')
        b['assets']=[{'id':x,'sha256':catalog[x]['sha256'],'type':catalog[x]['type'],'description':catalog[x]['description'],'provenance_status':'declared; output not visually verified'} for x in ids]
    return mode_plan

def require_executed_and_verified(mode_plan):
    """Never accept status flags supplied by a planner as an execution receipt."""
    # No execution-evidence adapter is integrated yet. Failing closed is safer
    # than accepting caller-authored JSON with executed/verified=True.
    raise ModeError('Mode execution and output verification receipts are not integrated; rendering through this guarded route is blocked')
