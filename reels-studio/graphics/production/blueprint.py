"""Strict, fail-closed beat blueprint and audio timing binding.

All timestamps are absolute seconds in the original narration. Visual spans include
pauses; spoken spans never do. No proportional word-timing fallback is accepted.
"""
from __future__ import annotations
import hashlib, json, math, re, wave
from pathlib import Path
from graphics.timing import chunk_phrases

class BlueprintError(ValueError): pass

def digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()

def duration(path):
    # Voice handoffs use PCM WAV. Do not infer from word timing or text.
    try:
        with wave.open(str(path),'rb') as f: return f.getnframes()/f.getframerate()
    except (wave.Error,EOFError) as e: raise BlueprintError('Narration must be PCM WAV; decode with existing FFmpeg first') from e

def token(s): return re.sub(r"[^a-z0-9']",'',s.lower())

def bind(audio, words, groups, specs, *, method):
    if method not in ('whisper-word','native-word','forced-alignment'):
        raise BlueprintError('Verified word alignment required; estimated alignment forbidden')
    if not words or len(groups)!=len(specs): raise BlueprintError('Missing words or beat specifications')
    d=duration(audio); last=0
    for w in words:
        if not isinstance(w,list) or len(w)!=3 or not isinstance(w[0],str) or not token(w[0]): raise BlueprintError('Invalid word')
        a,b=w[1:]
        if isinstance(a,bool) or isinstance(b,bool) or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in (a,b)) or not 0<=a<b<=d+.001 or a<last-.001: raise BlueprintError('Invalid or unordered word timestamps')
        last=b
    if sum(groups)!=len(words) or any(not isinstance(n,int) or isinstance(n,bool) or n<1 for n in groups): raise BlueprintError('Beat word groups must partition all words')
    beats=[]; i=0
    for k,(n,s) in enumerate(zip(groups,specs)):
        w=words[i:i+n]; start=0 if k==0 else w[0][1]; end=words[i+n][1] if i+n<len(words) else d
        b={'id':f'beat-{k+1:03}', 'narration':' '.join(x[0] for x in w), 'words':w,
           'audio_start':w[0][1], 'audio_end':w[-1][2], 'start':start, 'end':end, 'duration':end-start, **s}
        beats.append(b);i+=n
    result={'version':1,'audio_sha256':digest(audio),'audio_duration':d,'alignment_method':method,'beats':beats}
    validate(result,audio);return result

def validate(b,audio=None):
    top={'version','audio_sha256','audio_duration','alignment_method','beats'}
    if not isinstance(b,dict) or set(b)!=top or b['version']!=1: raise BlueprintError('Invalid blueprint envelope')
    if b['alignment_method'] not in ('whisper-word','native-word','forced-alignment'): raise BlueprintError('Estimated alignment prohibited')
    if not re.fullmatch(r'[a-f0-9]{64}',b['audio_sha256']): raise BlueprintError('Invalid audio digest')
    D=b['audio_duration']
    if not isinstance(D,(float,int)) or isinstance(D,bool) or not math.isfinite(D) or D<=0: raise BlueprintError('Invalid audio duration')
    if audio and (digest(audio)!=b['audio_sha256'] or abs(duration(audio)-D)>1e-6): raise BlueprintError('Narration changed: re-align and rebuild blueprint')
    required={'id','narration','words','audio_start','audio_end','start','end','duration','visual_objective','treatment','scene_description','subject','objects','composition','animations','camera','overlays','transition','sound_effects','assets'}
    beats=b['beats']; prev=0; ids=set()
    if not isinstance(beats,list) or not beats: raise BlueprintError('No beats')
    for x in beats:
        if not isinstance(x,dict) or set(x)!=required: raise BlueprintError('Missing or unknown beat field')
        if not re.fullmatch(r'beat-[0-9]{3}',x['id']) or x['id'] in ids: raise BlueprintError('Invalid beat id')
        ids.add(x['id'])
        for key in ('narration','visual_objective','treatment','scene_description','subject','composition','camera','transition'):
            if not isinstance(x[key],str) or not x[key].strip(): raise BlueprintError('Empty '+key)
        for key in ('objects','animations','overlays','sound_effects','assets','words'):
            if not isinstance(x[key],list): raise BlueprintError(key+' must be list')
        if any(not isinstance(v,str) or not v.strip() for v in x['objects']): raise BlueprintError('Invalid object')
        for asset in x['assets']:
            if not isinstance(asset,dict) or set(asset)!={'id','kind','provider'} or not all(isinstance(v,str) and v for v in asset.values()): raise BlueprintError('Invalid asset requirement')
        if not x['assets'] or not x['animations']: raise BlueprintError('Assets and animations required')
        a,z=x['start'],x['end']; ws=x['words']
        if not ws or abs(a-prev)>1e-6 or not a<=x['audio_start']<x['audio_end']<=z+1e-6 or not z>a or abs(x['duration']-(z-a))>1e-6: raise BlueprintError('Invalid beat timing')
        if x['audio_start']!=ws[0][1] or x['audio_end']!=ws[-1][2] or x['narration']!=' '.join(w[0] for w in ws): raise BlueprintError('Narration/word mismatch')
        for w in ws:
            if not isinstance(w,list) or len(w)!=3 or not a<=w[1]<w[2]<=z+1e-6: raise BlueprintError('Word outside beat')
        for e in x['animations']:
            if not isinstance(e,dict): raise BlueprintError('Invalid animation')
            if set(e)!={'kind','word_index','start','end'} or not isinstance(e['word_index'],int) or not 0<=e['word_index']<len(ws) or abs(e['start']-ws[e['word_index']][1])>1e-6 or not a<=e['start']<e['end']<=z: raise BlueprintError('Animation must be anchored to a beat word and finish within beat')
        prev=z
    if abs(prev-D)>1e-6: raise BlueprintError('Timeline must cover narration')
    return b

def auto_groups(words):
    """Pause and punctuation segmentation; explicit edited grouping also supported."""
    return [len(x['words']) for x in chunk_phrases(words)]

def battery_specs(words,groups):
    if len(groups)!=3: raise BlueprintError('Battery sample requires three explicitly grouped phrases')
    kinds=['phone_explode','battery_charge','ion_flow']; titles=['SMARTPHONE BATTERY','ENERGY STATE','ION MOVEMENT']; result=[]; off=0
    for i,n in enumerate(groups):
        start=words[off][1]; end=words[off+n][1] if off+n<len(words) else None
        # end is filled against the actual final word below for last beat
        event_end=(end if end is not None else words[-1][2]);
        result.append({'visual_objective':titles[i], 'treatment':['exploded_view','process_animation','scientific_visualization'][i],
          'scene_description':['Phone casing separates to reveal battery','Battery cross-section and illustrative charge indicator','Microscopic electrode cross-section with moving ions'][i],
          'subject':['smartphone','battery','lithium ions'][i], 'objects':[['casing','battery'],['electrodes','energy indicator'],['electrodes','ions']][i],
          'composition':'Centered subject with safe margins', 'animations':[{'kind':kinds[i],'word_index':0,'start':start,'end':event_end}],
          'camera':['push in','cut to cross-section','cut to microscopic view'][i], 'overlays':[], 'transition':'cut', 'sound_effects':[],
          'assets':[{'id':f'procedural-{i+1}','kind':'programmatic_motion','provider':'pillow-battery'}]});off+=n
    return result
