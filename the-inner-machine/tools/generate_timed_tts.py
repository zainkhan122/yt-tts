#!/usr/bin/env python3
"""Generate measured sentence audio and an absolute caption/timing schedule.

Uses Kokoro once, synthesizes each sentence with its voice-plan speed, appends the
requested pause as actual silence, then writes an atomic master WAV plus JSON schedule.
"""
import argparse,json,os,sys,wave
from pathlib import Path
import numpy as np

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('voice_plan'); ap.add_argument('--outdir',required=True); ap.add_argument('--voice',default=None); a=ap.parse_args()
 plan=json.load(open(a.voice_plan)); out=Path(a.outdir); out.mkdir(parents=True,exist_ok=True); chunks=out/'sentence_audio'; chunks.mkdir(exist_ok=True)
 # Use the workspace voice binary; model remains in user cache and is never committed.
 root=Path(__file__).resolve().parents[1]; os.environ.setdefault('KOKORO_VOICES',str(root/'reusable'/'voices-v1.0.bin'))
 sys.path.insert(0,str(root/'pipeline')); import tts; import soundfile as sf
 voice=a.voice or plan.get('voice','bm_george'); all_audio=[]; schedule=[]; cursor=0.0; sr=None
 for i,item in enumerate(plan['sentences']):
  sid=item['id']; wav=chunks/f'{sid}.wav'
  if wav.exists(): audio,rate=sf.read(wav,dtype='float32')
  else:
   audio,rate=tts.synth(item['narration'],voice=voice,speed=float(item.get('pace',1.0)))
   sf.write(wav,audio,rate)
  if sr is None: sr=rate
  if rate!=sr: raise RuntimeError(f'{sid}: sample-rate mismatch {rate} != {sr}')
  audio=np.asarray(audio,dtype=np.float32)
  if audio.ndim>1: audio=audio.mean(axis=1)
  speech_start=cursor; speech_dur=len(audio)/sr; speech_end=speech_start+speech_dur
  pause=float(item.get('pause_after_s',0.18)); silence=np.zeros(round(pause*sr),dtype=np.float32)
  all_audio.extend([audio,silence]); cursor=speech_end+pause
  schedule.append({'sentence_id':sid,'text':item['narration'],'emphasis':item.get('emphasis',''),'pace':item.get('pace',1.0),'start_s':round(speech_start,4),'speech_end_s':round(speech_end,4),'end_s':round(cursor,4),'pause_after_s':pause,'audio_file':str(wav.relative_to(out))})
  print(f'{sid}: speech {speech_dur:.3f}s | pause {pause:.2f}s | timeline {speech_start:.3f}-{cursor:.3f}',flush=True)
 master=out/'narration_timed.wav'; tmp=str(master)+'.part.wav'; sf.write(tmp,np.concatenate(all_audio),sr,subtype='PCM_16'); os.replace(tmp,master)
 report={'status':'pass','voice':voice,'sample_rate':sr,'sentences':len(schedule),'duration_s':round(cursor,4),'target_wpm':plan.get('target_wpm'),'schedule':schedule}
 json.dump(report,open(out/'caption_schedule.json','w'),indent=2)
 print(f'PASS: {len(schedule)} sentences, {cursor:.3f}s, {voice}; wrote {master} and caption_schedule.json')
if __name__=='__main__': main()
