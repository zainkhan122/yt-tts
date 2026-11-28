"""Bridge review-only Chatterbox handoff to the existing scheduler.

Never issues an alignment receipt or changes the strict production scheduler.
Accepts only exact one-to-one matching, so draft_voice.mapped cannot have
interpolated word times for the accepted script (word confidence unavailable).
"""
import hashlib,json,math
from pathlib import Path
from .alignment import tokens
from .blueprint import digest,duration
from .scheduler import _schedule_report

class ReviewHandoffError(ValueError):pass

def schedule_review(audio,script_lines,handoff,plan):
    if len(script_lines)!=1 or handoff.get('engine')!='chatterbox' or handoff.get('profile')!='option-3':raise ReviewHandoffError('Expected single-chunk approved house voice')
    script_hash=hashlib.sha256(json.dumps(script_lines,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
    if script_hash!=handoff.get('script_sha256') or handoff.get('overall_match',0)<.95:raise ReviewHandoffError('Handoff script/QA mismatch')
    if len(handoff.get('chunks',[]))!=1 or len(handoff.get('scenes',[]))!=1:raise ReviewHandoffError('One voice chunk required')
    expected=tokens(script_lines[0]);heard=[tokens(x) for x in handoff['chunks'][0]['heard_words']]
    if any(len(x)!=1 for x in heard) or [x[0] for x in heard]!=expected:raise ReviewHandoffError('Transcript not exact; interpolation cannot be ruled out')
    raw=handoff['scenes'][0]['words'];D=duration(audio)
    if len(raw)!=len(expected) or abs(D-handoff['duration'])>.001:raise ReviewHandoffError('Voice timing/duration mismatch')
    words=[];last=0
    for i,row in enumerate(raw):
        if len(row)!=3 or tokens(row[0])!=[expected[i]] or not all(type(x) in (int,float) and math.isfinite(x) for x in row[1:]) or not 0<=row[1]<row[2]<=D or row[1]<last:raise ReviewHandoffError('Invalid word timestamp')
        words.append({'text':expected[i],'start':row[1],'end':row[2]});last=row[2]
    report={'words':words,'audio_sha256':digest(audio),'audio_duration':D,'provider':'review-house-voice / whisper.cpp','model':'small.en; no per-word confidence'}
    result=_schedule_report(report,plan);result['review_only']=True;return result
