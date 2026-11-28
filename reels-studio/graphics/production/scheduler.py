"""Bind AI visual intent to verified spoken words, never estimated positions."""
from .alignment import require_verified, tokens
from .semantic import validate_plan, PlanningError

def schedule(audio,transcript,alignment,plan):
    r=require_verified(alignment,audio,transcript);return _schedule_report(r,plan)

def _schedule_report(r,plan):
    w=r['words'];validate_plan(plan,[x['text'] for x in w]);beats=[]
    for i,b in enumerate(plan['beats']):
        a,z=b['word_start'],b['word_end'];start=0 if i==0 else w[a]['start'];end=w[z]['start'] if z<len(w) else r['audio_duration']; events=[]
        for e in b['events']:
            phrase=tokens(e['trigger_phrase']); matches=[j for j in range(a,z-len(phrase)+1) if [v['text'] for v in w[j:j+len(phrase)]]==phrase]
            if not phrase or len(matches)<e['occurrence']:raise PlanningError('Trigger phrase occurrence not found in beat: '+e['trigger_phrase'])
            idx=matches[e['occurrence']-1];at=w[idx]['start'];stop=at+e['duration']
            if stop>end+1e-9:raise PlanningError('Event overruns beat: '+e['id'])
            events.append({**e,'word_index':idx,'audio_time':at,'beat_relative_time':at-start,'end_time':stop})
        beats.append({**b,'start':start,'end':end,'duration':end-start,'audio_start':w[a]['start'],'audio_end':w[z-1]['end'],'narration':' '.join(x['text'] for x in w[a:z]),'events':events})
    return {'version':1,'audio_sha256':r['audio_sha256'],'audio_duration':r['audio_duration'],'alignment_provider':r['provider'],'alignment_model':r['model'],'beats':beats}
