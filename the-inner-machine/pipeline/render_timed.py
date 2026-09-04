#!/usr/bin/env python3
"""Render long-form visuals against the already-measured sentence timeline.

One call renders a resumable chunk. It never re-synthesizes TTS and never guesses timing.
"""
import argparse,json,os,subprocess,sys,re
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parent; sys.path.insert(0,str(HERE))
import produce
FF=produce.FF

def run(cmd):
 r=subprocess.run(cmd,capture_output=True,text=True)
 if r.returncode:
  print('CMD FAILED:', ' '.join(map(str,cmd[:8]))); print(r.stderr[-1200:]); raise SystemExit(1)
 return r

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('video_dir'); ap.add_argument('--chunk',type=int,default=8); ap.add_argument('--width',type=int,default=1280); ap.add_argument('--height',type=int,default=720); ap.add_argument('--audio',default=None); a=ap.parse_args()
 v=Path(a.video_dir); shots=json.load(open(v/'shots.json')); timing=json.load(open(v/'tts/caption_schedule.json'))['schedule']; audio_path=Path(a.audio) if a.audio else v/'tts/narration_timed.wav'
 if len(shots)!=len(timing): raise SystemExit('shot/schedule count mismatch')
 work=Path('/tmp/inner-machine-video01-render'); work.mkdir(exist_ok=True); statefile=v/'run_state.json'; state=json.load(open(statefile)) if statefile.exists() else {}
 start=int(state.get('render_index',0)); end=min(start+a.chunk,len(shots))
 for i in range(start,end):
  s=shots[i]; t=timing[i]; dur=round(t['end_s']-t['start_s'],3); out=work/f'v_{i:03d}.mp4'
  if not out.exists(): produce.render_beat(str(v/s['kf']),s['caption'],s['motion'],dur,str(out),a.width,a.height,30,last=(i==len(shots)-1),narration=s['narration'],pause_s=float(s.get('pause_after_s',0.15)))
  print(f'rendered beat {i+1}/{len(shots)} {dur:.3f}s',flush=True)
 state['render_index']=end; state['step']='render' if end<len(shots) else 'rendered'; state['render_status']='in_progress' if end<len(shots) else 'complete'; json.dump(state,open(statefile,'w'),indent=2)
 if end<len(shots): print(f'NEXT CHUNK: {end}-{min(end+a.chunk,len(shots))-1}'); return
 lf=work/'list.txt'; lf.write_text(''.join(f"file '{(work/f'v_{i:03d}.mp4').resolve()}'\n" for i in range(len(shots))))
 visual=work/'visual.mp4'; run([FF,'-y','-f','concat','-safe','0','-i',str(lf),'-c:v','libx264','-preset','fast','-crf','21','-pix_fmt','yuv420p','-r','30',str(visual)])
 title=json.load(open(v/'project.json')).get('title','video')
 final=v/f'{title} {a.width}x{a.height}.mp4'; part=str(final)+'.part.mp4'
 run([FF,'-y','-i',str(visual),'-i',str(audio_path),'-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','128k','-t',str(timing[-1]['end_s']),part])
 os.replace(part,final)
 state['output']=str(final); state['step']='rendered'; state['render_status']='complete'; json.dump(state,open(statefile,'w'),indent=2)
 print('LONG RENDER COMPLETE:',final)
if __name__=='__main__': main()
