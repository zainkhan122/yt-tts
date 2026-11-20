#!/usr/bin/env python3
"""Generate a REVIEW-ONLY approved-voice handoff with strict transcription gates.
No publishing or production-gate bypass; final video must still pass production QA.
Input JSON is a list of scene narration strings. Intended for a 16GB runner.
"""
import argparse,difflib,hashlib,json,sys
from pathlib import Path
import numpy as np
import soundfile as sf
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from lib.pipeline import ChatterboxVoice,align_chunk,norm_word,normalized_match_text,melody_st

def mapped(words,heard,start,end):
    target=[norm_word(w) for w in words];heardnorm=[h[0] for h in heard]
    arr=[None]*len(words)
    for a,b,n in difflib.SequenceMatcher(a=target,b=heardnorm,autojunk=False).get_matching_blocks():
        for k in range(n):arr[a+k]=[words[a+k],start+heard[b+k][1],start+heard[b+k][2]]
    i=0
    while i<len(arr):
        if arr[i] is not None:i+=1;continue
        j=i
        while j<len(arr) and arr[j] is None:j+=1
        a=arr[i-1][2] if i else start;b=arr[j][1] if j<len(arr) else end;step=max(.01,(b-a)/max(1,j-i))
        for k in range(i,j):arr[k]=[words[k],a+(k-i)*step,a+(k-i+1)*step]
        i=j
    return arr

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--script',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
    lines=json.loads(Path(a.script).read_text());
    if not isinstance(lines,list) or not 1<=len(lines)<=12 or any(not isinstance(x,str) or not x.strip() or len(x)>450 for x in lines):raise SystemExit('Invalid script')
    cfg=json.loads((ROOT/'config/channel.json').read_text())['tts'];voice=ChatterboxVoice(cfg)
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True);work=out/'work';work.mkdir(exist_ok=True)
    chunks=[];cur=[]
    for i,line in enumerate(lines):
        if cur and len(' '.join(lines[j] for j in cur+[i]))>280:chunks.append(cur);cur=[]
        cur.append(i)
    if cur:chunks.append(cur)
    all_audio=[];scenes=[None]*len(lines);offset=0.;checks=[];all_expected=[];all_heard=[];sr=24000
    with (work/'voice-qa.log').open('w') as log:
        for ci,idx in enumerate(chunks):
            expected=[lines[i] for i in idx];best=None
            for attempt in range(3):
                audio,sr=voice(' '.join(expected),seed=7+ci*1000+attempt*97)
                cuts,match,heard=align_chunk(audio,sr,expected,work,log)
                mel=melody_st(audio,sr,heard); item=(match,mel,audio,cuts,heard)
                if best is None or (match,mel)>(best[0],best[1]):best=item
                if match>=.92 and mel>=12:break
            match,mel,audio,cuts,heard=best
            print(f'Chunk {ci+1}: intelligibility {match:.1%}, melody {mel:.1f} st',flush=True)
            if match<.92:raise SystemExit('Voice intelligibility did not meet 92% minimum; no handoff created')
            if mel<12:raise SystemExit('Voice melody did not meet 12 semitone minimum; no handoff created')
            all_expected.extend(' '.join(expected).split());all_heard.extend([h[0] for h in heard]);checks.append({'match':match,'melody_st':mel})
            edges=[0]+cuts+[len(audio)]
            full_words=' '.join(expected).split(); mapped_words=mapped(full_words,heard,offset,offset+len(audio)/sr);wi=0
            for k,i in enumerate(idx):
                count=len(lines[i].split());a0=offset+edges[k]/sr;b0=offset+edges[k+1]/sr
                scenes[i]={'start':a0,'end':b0,'words':mapped_words[wi:wi+count]};wi+=count
            all_audio.append(audio);all_audio.append(np.zeros(int(.06*sr),dtype=np.float32));offset+=len(audio)/sr+.06
    expected=normalized_match_text(all_expected); heard=normalized_match_text(all_heard)
    score=sum(b.size for b in difflib.SequenceMatcher(a=expected,b=heard,autojunk=False).get_matching_blocks())/max(1,len(expected))
    if score<.95:raise SystemExit(f'Overall voice QA {score:.1%} below 95%; no handoff created')
    audio=np.concatenate(all_audio[:-1]);sf.write(out/'voice.wav',audio,sr,subtype='PCM_16')
    (out/'timings.json').write_text(json.dumps({'script_sha256':hashlib.sha256(json.dumps(lines,ensure_ascii=False,separators=(',',':')).encode()).hexdigest(),'engine':'chatterbox','profile':'option-3','model_revision':voice.model_revision,'overall_match':score,'chunks':checks,'duration':len(audio)/sr,'scenes':scenes},indent=2))
    print(f'VOICE HANDOFF OK: overall {score:.1%}; {len(audio)/sr:.2f}s; review-only')
if __name__=='__main__':main()
