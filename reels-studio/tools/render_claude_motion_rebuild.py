#!/usr/bin/env python3
"""Narration-synchronized Claude Motion workflow, honest illustrative recreation."""
import math,json,re,subprocess,sys,tempfile
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import imageio_ffmpeg
R=Path(__file__).resolve().parents[1];I='claude-motion-rebuild';O=R/'renders'/I;V=O/'voice-handoff';J=json.loads((V/'timings.json').read_text());S=J['scenes'];assert J['engine']=='chatterbox' and J['overall_match']>=.95 and len(S)==6
RATE=1.08
for scene in S:
 scene['start']/=RATE;scene['end']/=RATE;scene['words']=[[w[0],w[1]/RATE,w[2]/RATE] for w in scene['words']]
J['duration']/=RATE
W,H=540,960;FPS=24;FF=imageio_ffmpeg.get_ffmpeg_exe();F=R/'templates/_base/fonts';font=lambda n:ImageFont.truetype(str(F/'Inter.ttf'),n);bold=lambda n:ImageFont.truetype(str(F/'Anton.ttf'),n)
F12,F15,F18,F21,F24,F28,F37,F48,F62=font(12),font(15),font(18),font(21),font(24),font(28),bold(37),bold(48),bold(62)
C={'cream':'#f8f0e5','ink':'#172f3d','muted':'#68817c','orange':'#db785b','mint':'#83c2ac','mint2':'#c8e6d3','blue':'#284d5a','dark':'#203c48','shadow':'#c9c3b0','card':'#fffaf3','line':'#d8e2d7'}
cover=Image.open(R/'covers'/I/'cover.jpg').convert('RGB').resize((W,H),Image.Resampling.LANCZOS)
def ease(x):
 x=max(0,min(1,x));return 1-(1-x)**3
def clip(x):return max(0,min(1,x))
def cue(sc,word,offset=0):
 word=word.lower(); return next((float(w[1]) for w in sc['words'] if re.sub('[^a-z0-9]','',w[0].lower())==word),sc['start']+offset)
def rr(d,b,r,fill,outline=None,width=1): d.rounded_rectangle(tuple(map(int,b)),int(r),fill=fill,outline=outline,width=width)
def txt(d,xy,s,f,fill=None,anchor=None):d.text(xy,str(s),font=f,fill=fill or C['ink'],anchor=anchor)
def line(d,xy,fill,width=1):d.line([(int(x),int(y)) for x,y in xy],fill=fill,width=width,joint='curve')
def cursor(d,x,y,scale=1):
 p=[(x,y),(x+3*scale,y+24*scale),(x+9*scale,y+18*scale),(x+14*scale,y+29*scale),(x+19*scale,y+27*scale),(x+14*scale,y+15*scale),(x+22*scale,y+14*scale)]
 d.polygon(p,fill='#172f3d',outline='#fffaf3',width=2)
def panel(d,x,y,w,h):
 rr(d,(x+7,y+10,x+w+7,y+h+10),19,'#d9d8cb');rr(d,(x,y,x+w,y+h),19,C['card'],outline='#dbe3d7',width=2)
def chip(d,x,y,w,label,fill=None):
 rr(d,(x,y,x+w,y+33),16,fill or C['mint2']);txt(d,(x+w/2,y+8),label,F12,C['ink'],'ma')
def header(d,section):
 txt(d,(35,65),'HYPELESS  /  CLAUDE MOTION',F15,C['blue']);txt(d,(35,102),section,F48);rr(d,(35,170,150,177),3,C['orange']);txt(d,(35,195),'ILLUSTRATIVE RECREATION  •  SAMPLE DATA',F12,C['muted'])
def chart(d,x,y,w,h,t,start,edit=0,small=False):
 # Every bar has an independent eased growth and label; orange edit cross-fades in-place.
 xs=[x+int(w*k/4)+int(w/12) for k in range(4)];bw=int(w/7);base=y+h-44;top=y+20
 for q in range(4):
  yy=base-int((base-top)*q/3);line(d,[(x+10,yy),(x+w-10,yy)],'#e1e9df',1)
 vals=[.33,.54,.70,.88]; labs=['Q1','Q2','Q3','Q4'];colors=['#a6d4bd','#83c2ac','#67ad98','#539581']
 for k in range(4):
  a=ease((t-start-k*.3)/.65);bh=(base-top)*vals[k]*a;col=colors[k]
  if k==3 and edit>0:col=tuple(int(v*(1-edit)+z*edit) for v,z in zip((83,149,129),(219,120,91)))
  rr(d,(xs[k],base-bh,xs[k]+bw,base),min(9,bw/4),col);txt(d,(xs[k]+bw/2,base+10),labs[k],F12 if small else F15,C['muted'],'ma')
  if a>.85:txt(d,(xs[k]+bw/2,base-bh-20),str([32,52,68,86][k]),F12,C['blue'],'ma')
def bg(t):
 im=Image.new('RGB',(W,H),C['cream']);d=ImageDraw.Draw(im)
 for n in range(6):
  yy=242+n*104;xx=int(12*math.sin(t*.7+n));line(d,[(0,yy+xx),(W,yy+xx)],'#f0e3d4',1)
 return im
def frame(t,trans=True):
 if t<1/FPS:return cover.copy()
 idx=max((k for k,s in enumerate(S[:-1]) if s['start']<=t),default=0);s=S[idx];u=max(0,t-s['start']);dur=max(.1,s['end']-s['start']);p=clip(u/dur);im=bg(t);d=ImageDraw.Draw(im)
 headers=['FROM CHART TO STORY','ASK FOR MOTION','WATCH IT BUILD','EDIT ONE DETAIL','EXPORT YOUR MP4'];header(d,headers[idx])
 if idx==0:
  # Static spreadsheet rows transform into a real sequential animated chart.
  panel(d,35,254,470,449);txt(d,(65,275),'QUARTERLY SALES',F21,C['blue']);chip(d,344,274,128,'SAMPLE DATA')
  chart(d,60,330,420,298,t,s['start']+.6)
  a=ease((t-s['start']-1.4)/.7);rr(d,(63,650,63+int(320*a),664),7,C['orange']);txt(d,(270,742),'YOUR DATA  →  ANIMATED STORY',F18,C['blue'],'ma')
 elif idx==1:
  # A recreated interface shows a real cursor choosing the option, typing a concrete prompt, and sending it.
  panel(d,30,246,480,478);txt(d,(58,270),'Claude',F28,C['ink']);rr(d,(58,324,481,447),15,'#f1f5ed',outline='#d6e1d7',width=2);txt(d,(75,339),'Your message',F12,C['muted'])
  content='Animate my sales chart.\nMake each bar grow in sequence.';begin=cue(s,'type',2.2);n=int(len(content)*clip((t-begin)/2.3));typed=content[:n]
  for k,row in enumerate(typed.split('\n')):txt(d,(75,365+k*27),row,F18,C['ink'])
  if int(t*2)%2==0 and n<len(content):
   last=typed.split('\n')[-1];x=75+int(d.textlength(last,font=F18));y=365+27*(len(typed.split('\n'))-1);line(d,[(x,y),(x,y+22)],C['orange'],2)
  rr(d,(58,470,197,518),12,C['card'],outline='#bdcec3',width=2);txt(d,(73,482),'Output  ▾',F18)
  menu=ease((t-cue(s,'output',.6))/.35); 
  if menu>.04:
   rr(d,(58,534,266,666),14,C['dark']);txt(d,(75,547),'OUTPUT TYPE',F12,'#c4d9cb');rr(d,(70,578,253,622),10,C['orange']);txt(d,(86,589),'✦  Motion',F18,'white')
  send=ease((t-begin-2.2)/.4);d.ellipse((425,470,475,520),fill=C['orange']);txt(d,(449,480),'↑',F24,'white','ma');cursor(d,140+int(295*send),560-int(70*send),.8)
  txt(d,(270,762),'SELECT  →  DESCRIBE  →  SEND',F18,C['blue'],'ma')
 elif idx==2:
  # Code characters flow into the chart, which animates in progressive order.
  panel(d,33,247,474,501);txt(d,(60,271),'BUILDING YOUR ANIMATION',F18,C['blue']);chip(d,350,265,118,'CODE-BASED')
  rr(d,(57,318,483,400),12,C['dark']);code=['animate(bar1, { height: 32 })','animate(bar2, { height: 52 })','animate(bar3, { height: 68 })'];
  for k,l in enumerate(code):txt(d,(72,327+k*21),l[:int(len(l)*clip((u-k*.25)/.9))],F12,'#b9e7c9')
  chart(d,60,415,420,260,t,cue(s,'bars',1.3)-.3)
  show=ease((t-cue(s,'takeaway',4))/.4);rr(d,(74,690,74+int(390*show),722),12,C['mint2']);
  if show>.85:txt(d,(270,697),'SALES TREND  ↗',F15,C['ink'],'ma')
 elif idx==3:
  # Continuity: same chart, same data, a single highlighted bar changes color, exactly as narrated.
  panel(d,33,252,474,490);txt(d,(58,276),'REFINE WITHOUT RESTARTING',F18,C['blue']);chart(d,58,325,425,230,999,0,edit=ease((t-cue(s,'coral',2.2))/.5))
  rr(d,(57,598,481,681),14,'#eef5ed');txt(d,(73,610),'Highlight the last bar',F18);txt(d,(73,640),'in coral.',F18,C['orange']);cursor(d,424+int(8*math.sin(t*3)),650,.8)
  txt(d,(270,766),'SAME CHART  •  ONE CHANGE',F18,C['blue'],'ma')
 else:
  # Actual file-shaped object travels out of an export menu into a destination folder.
  panel(d,37,254,466,468);txt(d,(65,280),'YOUR ANIMATION',F21,C['blue']);chart(d,70,316,270,200,999,0,edit=1,small=True)
  rr(d,(354,325,468,374),12,C['blue']);txt(d,(411,338),'Export',F18,'white','ma');a=ease((t-cue(s,'export',.2))/.55)
  if a>.05:
   rr(d,(350,386,475,448),12,C['dark']);txt(d,(412,405),'MP4  ↓',F18,'white','ma')
  move=ease((t-cue(s,'mp4',1.2))/.9);x=365-int(move*95);y=475+int(move*92);rr(d,(x,y,x+66,y+79),10,C['orange']);txt(d,(x+33,y+25),'MP4',F15,'white','ma');rr(d,(141,616,371,679),14,'#8dc7a9');txt(d,(256,635),'ANIMATION READY',F15,C['ink'],'ma')
  rr(d,(51,750,489,789),12,C['dark']);txt(d,(270,760),'TEAM + ENTERPRISE  •  BETA',F15,'#e4f5e9','ma')
 # Drift adds a camera move without changing labels or obscuring the action.
 scale=1.07+.045*(.5+.5*math.sin(t*1.15));ww=int(W*scale);hh=int(H*scale);z=im.resize((ww,hh),Image.Resampling.BILINEAR);x=int((ww-W)*(.5+.35*math.sin(t*1.15)));y=int((hh-H)*(.5+.35*math.cos(t)));im=z.crop((max(0,min(ww-W,x)),max(0,min(hh-H,y)),max(0,min(ww-W,x))+W,max(0,min(hh-H,y))+H));d=ImageDraw.Draw(im)
 if trans and idx and u<.26:im=Image.blend(frame(max(1/FPS,s['start']-.05),False),im,ease(u/.26));d=ImageDraw.Draw(im)
 # Actual word-level caption timing, grouped into readable short phrases.
 words=s['words'];wi=next((k for k,w in enumerate(words) if w[1]<=t<w[2]+.02),None)
 if wi is not None:
  st=wi//3*3;group=words[st:st+3];parts=[w[0].upper() for w in group];f=F24;lens=[d.textlength(q,font=f) for q in parts];gap=9;total=sum(lens)+gap*(len(lens)-1)
  if total>450:f=F18;lens=[d.textlength(q,font=f) for q in parts];total=sum(lens)+gap*(len(lens)-1)
  x=(W-total)/2;rr(d,(x-15,832,x+total+15,883),12,C['dark'])
  for k,q in enumerate(parts):txt(d,(x,844),q,f,'#ffd18c' if st+k==wi else 'white');x+=lens[k]+gap
 return im
body=S[-1]['start'];O.mkdir(parents=True,exist_ok=True);out=O/'claude-motion-rebuilt-v2.mp4'
assert not out.exists(),'refusing to overwrite reviewed video'
with tempfile.TemporaryDirectory(prefix='motion-rebuild-') as tmp:
 tmp=Path(tmp);video=tmp/'body.mp4';cta=tmp/'cta.wav';tim=tmp/'cta.json';paced=tmp/'paced.wav';subprocess.run([FF,'-y','-loglevel','error','-i',str(V/'voice.wav'),'-af',f'atempo={RATE}','-acodec','pcm_s16le',str(paced)],check=True);last=S[-1];j=dict(J);j['duration']=J['duration']-body;j['scenes']=[{'start':0,'end':last['end']-body,'words':[[w[0],w[1]-body,w[2]-body] for w in last['words']]}];tim.write_text(json.dumps(j))
 subprocess.run([FF,'-y','-loglevel','error','-ss',str(body),'-i',str(paced),'-acodec','pcm_s16le',str(cta)],check=True)
 cmd=[FF,'-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','540x960','-r',str(FPS),'-i','-','-i',str(paced),'-t',str(body),'-vf','scale=1080:1920:flags=lanczos','-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k',str(video)]
 proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
 for n in range(math.ceil(body*FPS)):
  proc.stdin.write(frame(n/FPS).tobytes())
 proc.stdin.close();assert proc.wait()==0
 subprocess.run([sys.executable,str(R/'tools/append_house_outro.py'),'--input',str(video),'--output',str(out),'--voice',str(cta),'--timings',str(tim),'--keyword','MOTION','--body-seconds',str(body),'--prompt','for the guide'],cwd=R,check=True)
 (O/'timing-manifest.json').write_text(json.dumps({'scenes':S,'outro_start':body},indent=2)+'\n')
print('render complete; QA and human review still required',flush=True)
