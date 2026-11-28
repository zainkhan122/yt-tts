"""Independent narration alignment with per-word provenance.

Trust is scoped to this process: no serialized JSON can establish an execution
receipt. The production planning API accepts only results issued in-memory by this
service after running the built-in backend and validating its transcript.
"""
from __future__ import annotations
from dataclasses import dataclass
from difflib import SequenceMatcher
import math
import hashlib, json
from pathlib import Path
import re
from .blueprint import duration, digest

class AlignmentError(ValueError): pass

def tokens(s): return re.findall(r"[a-z0-9']+",s.lower())

def finite(v): return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v)

class FasterWhisperBackend:
    """Whisper word estimates (not forced alignment); no interpolated words."""
    def __init__(self,model='base.en',language='en'):
        if not model or not language: raise AlignmentError('Model and language required')
        self.model=model; self.language=language
    def transcribe(self,audio):
        from faster_whisper import WhisperModel
        from tools.align_words import _load_mono
        engine=WhisperModel(self.model,device='cpu',compute_type='int8')
        segments,_=engine.transcribe(_load_mono(Path(audio)),word_timestamps=True,language=self.language,vad_filter=False,beam_size=5)
        return [{'text':w.word.strip(),'start':float(w.start),'end':float(w.end),'confidence':float(w.probability) if w.probability is not None else None} for s in segments for w in (s.words or [])]

@dataclass(frozen=True)
class Alignment:
    report:dict
    _proof:object=None
    _report_digest:str=""

# This is an execution guard, not authentication against malicious local Python code.
_ISSUER=object()

def analyze(audio, transcript, observed, *, provider, model, confidence_threshold=.5, method='whisper-word'):
    """Compare raw observations to exact expected text, preserving all failures.

    `observed` is raw backend output, never interpolated. Output is diagnostic
    and not trusted by itself, even if every word matches.
    """
    if not isinstance(transcript,str) or not tokens(transcript): raise AlignmentError('Transcript required')
    if not finite(confidence_threshold) or not 0<=confidence_threshold<=1: raise AlignmentError('Bad confidence threshold')
    if not provider or not model: raise AlignmentError('Provider and model required')
    expected=tokens(transcript);D=duration(audio); raw=[]; prev=0
    for idx,o in enumerate(observed):
        if not isinstance(o,dict) or set(o)!={'text','start','end','confidence'}: raise AlignmentError('Bad observation')
        ts=tokens(o['text']); a=o['start'];z=o['end'];c=o['confidence'];flags=[]
        if len(ts)!=1: flags.append('ambiguous_tokenization')
        if not finite(a) or not finite(z) or not 0<=a<z<=D: flags.append('invalid_timestamp')
        elif a<prev: flags.append('overlapping_or_out_of_order')
        if finite(z):prev=max(prev,z)
        if c is None: flags.append('missing_confidence')
        elif not finite(c) or not 0<=c<=1: flags.append('invalid_confidence')
        elif c<confidence_threshold: flags.append('low_confidence')
        raw.append({**o,'index':idx,'normalized':ts[0] if len(ts)==1 else '', 'flags':flags})
    matcher=SequenceMatcher(a=expected,b=[x['normalized'] for x in raw],autojunk=False)
    mapped={};extras=[]
    for tag,a,b,c,d in matcher.get_opcodes():
        if tag=='equal':
            for i,j in zip(range(a,b),range(c,d)):mapped[i]=j
        else: extras.extend(range(c,d))
    words=[]
    for i,t in enumerate(expected):
        j=mapped.get(i)
        if j is None:
            words.append({'index':i,'text':t,'start':None,'end':None,'confidence':None,'status':'missing','flags':['unmatched','missing'], 'source_index':None,'method':'none','provider':provider,'model':model})
        else:
            o=raw[j]; flags=o['flags'][:]
            if method!='whisper-word': flags.append('interpolated' if 'interpol' in method else 'estimated')
            words.append({'index':i,'text':t,'start':o['start'],'end':o['end'],'confidence':o['confidence'],'status':'aligned' if not flags else 'rejected','flags':flags, 'source_index':j,'method':method,'provider':provider,'model':model})
    return {'schema':1,'audio_sha256':digest(audio),'audio_duration':D,'transcript':transcript,'provider':provider,'model':model,'method':method,'confidence_threshold':confidence_threshold,'words':words,'observations':raw,'unmatched_observation_indices':extras,'exact_match':not extras and len(mapped)==len(expected),'eligible':method=='whisper-word' and not extras and all(w['status']=='aligned' for w in words)}

def run_alignment(audio, transcript, backend, *, confidence_threshold=.5):
    """Run the explicitly supported adapter locally and issue a process-local receipt."""
    if type(backend) is not FasterWhisperBackend: raise AlignmentError('Unregistered alignment adapter')
    if not finite(confidence_threshold) or confidence_threshold < .5: raise AlignmentError('Confidence threshold must be at least 0.5')
    before=digest(audio);raw=backend.transcribe(audio)
    if digest(audio)!=before: raise AlignmentError('Audio changed during alignment')
    report=analyze(audio,transcript,raw,provider='faster-whisper',model=backend.model,confidence_threshold=confidence_threshold)
    return Alignment(report,_ISSUER,_report_hash(report))

def _report_hash(report):
    return hashlib.sha256(json.dumps(report,sort_keys=True,allow_nan=False).encode()).hexdigest()

def require_verified(alignment,audio,transcript):
    if not isinstance(alignment,Alignment) or alignment._proof is not _ISSUER: raise AlignmentError('Alignment must be executed by the registered service in this process; JSON is not proof')
    r=alignment.report
    if _report_hash(r)!=alignment._report_digest: raise AlignmentError('Alignment receipt changed')
    # Recompute from observations: a mutable report cannot just flip eligible/status fields.
    raw=[{k:o[k] for k in ('text','start','end','confidence')} for o in r['observations']]
    checked=analyze(audio,transcript,raw,provider=r['provider'],model=r['model'],confidence_threshold=r['confidence_threshold'],method=r['method'])
    if checked!=r or not checked['eligible']: raise AlignmentError('Alignment rejected: missing, extra, uncertain, invalid, interpolated or changed words/audio')
    return checked
