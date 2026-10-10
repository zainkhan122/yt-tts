"""Deterministic gates. Model opinions cannot override these results."""
import hashlib
import json
from pathlib import Path
import re
from decimal import Decimal,InvalidOperation

from jsonschema import Draft202012Validator

from lib.secrets import contains_secret
from tools.agent.evidence import normalized,validate_provenance
from tools.agent.openrouter_client import PilotBlocked

ROOT=Path(__file__).resolve().parents[2]
DRAFT_SCHEMA=json.loads((ROOT/'agent/schemas/draft-v1.json').read_text())
CRITIC_SCHEMA=json.loads((ROOT/'agent/schemas/critic-v1.json').read_text())


def numbers(text):
    result=set()
    for value in re.findall(r'(?<![A-Za-z0-9])\d[\d,]*(?:\.\d+)?',text):
        try:result.add(Decimal(value.replace(',','')).normalize())
        except InvalidOperation:pass
    return result


def validate_draft(draft,evidence,assets):
    errors=[];bindings={}
    for e in Draft202012Validator(DRAFT_SCHEMA).iter_errors(draft):
        errors.append('schema '+'.'.join(str(x) for x in e.path)+': '+e.message[:180])
    if errors:return {'passed':False,'errors':errors,'bindings':{}}
    encoded=json.dumps(draft,ensure_ascii=False)
    if contains_secret(encoded):errors.append('credential-like content')
    if any(x in encoded.lower() for x in ['</script','<script','javascript:','file://','169.254.169.254','localhost','127.0.0.1']):
        errors.append('active markup/private target is not allowed in a content brief')
    claims={c['id']:c for c in draft['claims']}
    if len(claims)!=len(draft['claims']):errors.append('duplicate claim IDs')
    for claim in draft['claims']:
        refs=[]
        for ref in claim['supports']:
            try:refs.append(evidence.citation(ref))
            except PilotBlocked as exc:errors.append(claim['id']+': '+str(exc))
        bindings[claim['id']]=refs
        if claim['attribution']=='recorded_observation' and not any(r['kind']=='recorded_observation' for r in refs):
            errors.append(claim['id']+': invented test/observation attribution')
        if claim['attribution']=='source_fact' and re.search(r'\b(benchmark|outperform|faster|accuracy|savings|speedup)\b',claim['statement'],re.I):
            if refs and all(r['kind']=='primary_source' for r in refs):errors.append(claim['id']+': performance claim needs explicit maker attribution')
    scene_ids=set();proof_assets=set();words=[]
    for scene in draft['scenes']:
        sid=scene['id']
        if sid in scene_ids:errors.append('duplicate scene ID '+sid)
        scene_ids.add(sid);words.extend(scene['say'].split())
        refs=scene['claim_ids']
        if scene['statement_type']=='factual' and not refs:errors.append(sid+': factual narration has no claim IDs')
        if any(c not in claims for c in refs):errors.append(sid+': unknown claim ID')
        if scene['statement_type'] in ('editorial','cta') and numbers(scene['say']):
            errors.append(sid+': numeric assertions cannot be hidden in editorial/CTA text')
        if re.search(r"\b(?:I|we)(?:'ve| have)?\s+(?:tested|ran|tried|measured|recorded)\b",scene['say'],re.I):
            errors.append(sid+': new hands-on claim is not authorized by a recorded baseline demo')
        if re.search(r"(?:pin (?:the|a) link|DM (?:you|me)|send you (?:the|a) link)",scene['say'],re.I):
            errors.append(sid+': unsupported automated-comment/link promise')
        asset=assets.get(scene['asset_id']) if scene['asset_id'] else None
        if scene['asset_id'] and not asset:errors.append(sid+': nonexistent asset')
        if asset:
            try:validate_provenance(asset)
            except PilotBlocked as exc:errors.append(sid+': '+str(exc))
            if asset['kind'] in {'explanatory_graphic','illustration'} and scene['asset_usage']!='illustration':
                errors.append(sid+': illustration presented as product evidence')
            if scene['asset_usage']=='recorded_demo' and asset['kind']!='recorded_demo':
                errors.append(sid+': fabricated demo provenance')
            if asset['kind'] in {'screenshot','maker_demo','recorded_demo'}:proof_assets.add(scene['asset_id'])
            if asset['file'].endswith('.mp4'):
                if scene['kind'] not in {'hook','proof'}:errors.append(sid+': video cannot be used as a still-image background')
                duration=asset.get('duration_seconds',0)
                if scene['clip_start']>=duration:errors.append(sid+': clip starts beyond real media')
                if duration-scene['clip_start'] < len(scene['say'].split())/3:
                    errors.append(sid+': not enough source footage for the spoken segment')
        elif scene['kind'] in {'hook','proof'}:
            errors.append(sid+': hook/proof requires a registered visual asset')
        if not asset and scene['asset_usage']!='none':errors.append(sid+': asset usage without an asset')
        metric=scene['metric']
        if scene['kind']=='metric':
            if not metric:errors.append(sid+': metric scene has no bound metric')
            else:
                cid=metric['claim_id']
                if cid not in refs:errors.append(sid+': metric claim not linked to narration')
                raw=' '.join(r['quote'] for r in bindings.get(cid,[]))
                if Decimal(str(metric['value'])).normalize() not in numbers(raw):errors.append(sid+': metric number absent from its evidence quote')
        elif metric is not None:errors.append(sid+': metric attached to a non-metric scene')
        if scene['kind']=='steps' and len(scene['bullets'])<2:errors.append(sid+': steps need at least two items')
        if scene['kind']=='catch' and not scene['bullets']:errors.append(sid+': catch must be explicit')
    if not 90<=len(words)<=140:errors.append(f'narration word count {len(words)} outside 90–140')
    kinds=[s['kind'] for s in draft['scenes']]
    if kinds[0]!='hook' or kinds[-1]!='cta' or 'catch' not in kinds:errors.append('requires hook, deliberate catch and final CTA')
    if len(proof_assets)<2:errors.append('requires at least two traceable proof assets')
    first=draft['scenes'][0]
    key=normalized(draft['keyword']).lower()
    if key not in normalized(first['say']+' '+first['headline']+' '+first['subtext']).lower():
        errors.append('primary keyword absent from the hook')
    meta=draft['metadata']
    if len(','.join(meta['tags']))>450:errors.append('backend tags exceed reserved operational budget')
    if re.search(r'\b(guaranteed|unlimited free|100% accurate)\b',meta['title']+' '+meta['youtube_description'],re.I):
        errors.append('unqualified guarantee/free/accuracy claim')
    return {'passed':not errors,'errors':errors,'bindings':bindings,'word_count':len(words),'proof_asset_count':len(proof_assets),
            'warning':'Quote presence and structure are not entailment; independent critic and owner review still required.'}


def validate_critic(review):
    errors=[e.message[:200] for e in Draft202012Validator(CRITIC_SCHEMA).iter_errors(review)]
    if errors:return False,errors
    severe=[i for i in review['issues'] if i['severity'] in {'critical','major'}]
    passed=review['verdict']=='pass' and review['all_material_claims_accounted_for'] and not severe and all(v>=3 for v in review['scores'].values())
    return passed,[]


def frozen_production_state():
    paths=['config/publishing.json','config/youtube.json','queue/publish.json','queue/youtube-long.json','tracker/publications.json','tracker/youtube-publications.json','config/channel.json']
    return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}


def assert_production_unchanged(before):
    after=frozen_production_state()
    if before!=after:raise PilotBlocked('Production state changed inside the optional pilot; no promotion permitted')
