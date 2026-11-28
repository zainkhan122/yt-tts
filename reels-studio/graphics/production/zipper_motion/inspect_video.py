"""Decode the review render, make a sampled contact sheet, record timings."""
import subprocess,math,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from graphics.media import ffmpeg_exe
import av
D=Path(__file__).resolve().parent;ff=ffmpeg_exe();vid=D/'zipper-review.mp4';frames=D/'contact-frames';frames.mkdir(exist_ok=True)
r=subprocess.run([ff,'-y','-v','error','-i',str(vid),'-vf','fps=2/3,scale=270:480','-q:v','3',str(frames/'%03d.jpg')],capture_output=True);assert not r.returncode,r.stderr
paths=sorted(frames.glob('*.jpg'));cols=6;rows=math.ceil(len(paths)/cols);sheet=Image.new('RGB',(cols*270,rows*510),'#182529');draw=ImageDraw.Draw(sheet);f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
for i,p in enumerate(paths):
 with Image.open(p) as im:
  x=(i%cols)*270;y=(i//cols)*510;sheet.paste(im,(x,y));draw.text((x+8,y+485),f'{i*1.5+0.75:.2f}s approx.',font=f,fill='#e8e3d7')
sheet.save(D/'contact-sheet.jpg',quality=90)
r=subprocess.run([ff,'-v','error','-xerror','-i',str(vid),'-map','0:v:0','-map','0:a:0','-f','null','-'],capture_output=True);assert r.returncode==0,r.stderr
with av.open(str(vid)) as c:
 streams=[{'type':s.type,'duration':float(s.duration*s.time_base) if s.duration else None,'frames':s.frames,'time_base':str(s.time_base)} for s in c.streams]
T=json.loads((D/'visual-events.json').read_text())['events']
result={'decode':'passed','streams':streams,'fps':24,'event_frame_delay_seconds':{k:round(math.ceil(v*24)/24-v,6) for k,v in T.items()}}
(D/'technical-checks.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
