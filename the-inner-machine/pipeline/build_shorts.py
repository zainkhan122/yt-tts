#!/usr/bin/env python3
"""Build the two native portrait Shorts from their standalone scripts.

All intermediate audio/video lives in /tmp; only final Shorts and JSON schedules remain
in the workspace. CTA is synthesized as a separate final sentence so it cannot overlap.
"""
import argparse,json,os,re,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parent; sys.path.insert(0,str(HERE)); import produce
FF=produce.FF

def run(c):
 r=subprocess.run(c,capture_output=True,text=True)
 if r.returncode: print(r.stderr[-1000:]); raise SystemExit(1)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('video_dir');ap.add_argument('--kind',choices=['hook','payoff','both'],default='both');a=ap.parse_args();v=Path(a.video_dir); sroot=v/'shorts'
 kinds=('hook','payoff') if a.kind=='both' else (a.kind,)
 for kind in kinds:
  p=sroot/kind; cfg=json.loads((p/'short.json').read_text()); text=(p/'script.txt').read_text().strip();
  # split at sentence boundaries and ensure CTA is an independent terminal beat
  sentences=[x.strip() for x in re.split(r'(?<=[.!?])\s+',text) if x.strip()]; cta='Watch the full video on this channel.'
  if sentences[-1].lower().startswith('watch the full video'): core=sentences[:-1]
  else: core=sentences
  sentences=core+[cta];
  ims=sorted((p/'images').glob('*.jpg')); work=Path('/tmp')/f'inner-machine-{kind}-short'; shutil.rmtree(work,ignore_errors=True);work.mkdir(parents=True)
  import soundfile as sf, numpy as np
  os.environ.setdefault('KOKORO_VOICES',str(ROOT/'reusable'/'voices-v1.0.bin')); import tts
  audio=[];schedule=[];cursor=0.;sr=None
  for i,sent in enumerate(sentences):
   a1,r=tts.synth(sent,voice=cfg.get('voice','bm_george'),speed=0.94 if sent!=cta else 0.90)
   a1=np.asarray(a1,dtype='float32'); a1=a1.mean(axis=1) if a1.ndim>1 else a1
   if sr is None: sr=r
   if r!=sr: raise RuntimeError('sample rate mismatch')
   pause=0.28 if sent==cta else 0.16; start=cursor; sd=len(a1)/sr; end=start+sd; audio.extend([a1,np.zeros(round(pause*sr),dtype='float32')]); cursor=end+pause
   schedule.append({'sentence_id':f'{kind}_{i+1:02d}','text':sent,'start_s':round(start,4),'speech_end_s':round(end,4),'end_s':round(cursor,4),'pause_after_s':pause,'is_cta':sent==cta})
   cap='WATCH FULL VIDEO' if sent==cta else ' '.join(sent.split()[:4]).upper()
   img=str(ims[i%len(ims)].relative_to(v))
   # each sentence gets portrait asset and purposeful motion
   motions=[['zoom',1.05,1.16,.5,.5,.5,.40],['panlr',1.06,1.18,.25,.48,.72,.48],['rise',1.05,1.16,.5,.62,.5,.35],['settle',1.16,1.05,.5,.5,.5,.56]]
   schedule[-1].update({'caption':cap,'kf':img,'motion':motions[i%4]})
  sf.write(work/'audio.wav',np.concatenate(audio),sr,subtype='PCM_16')
  parts=[]
  for i,t in enumerate(schedule):
   out=work/f'v{i:02d}.mp4';produce.render_beat(str(v/t['kf']),t['caption'],t['motion'],t['end_s']-t['start_s'],str(out),1080,1920,30,last=(i==len(schedule)-1),narration=None,pause_s=t['pause_after_s'],overlay_text=t['caption'],overlay_start_frac=0.12,overlay_end_frac=0.48,font_size=16);parts.append(out)
  lf=work/'list.txt';lf.write_text(''.join(f"file \'{x.resolve()}\'\n" for x in parts)); visual=work/'visual.mp4';run([FF,'-y','-f','concat','-safe','0','-i',str(lf),'-c:v','libx264','-preset','veryfast','-crf','28','-pix_fmt','yuv420p','-r','30',str(visual)])
  final=p/f'{cfg["title"]}.mp4';part=str(final)+'.part.mp4';run([FF,'-y','-i',str(visual),'-i',str(work/'audio.wav'),'-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','96k','-t',str(cursor),part]);shutil.copy2(part,final);os.remove(part)
  json.dump({'status':'built','kind':kind,'voice':cfg.get('voice','bm_george'),'duration_s':round(cursor,4),'schedule':schedule},open(p/'caption_schedule.json','w'),indent=2)
  print('BUILT',kind,final,cursor)
if __name__=='__main__':main()
