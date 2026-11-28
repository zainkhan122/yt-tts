#!/usr/bin/env python3
"""Four distinctive narrated motion-graphic review drafts, never schedules."""
import argparse,json,math,subprocess,sys,tempfile,re
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
import imageio_ffmpeg
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('id',choices=['claude-motion-25','ai-income-25','paper-motion-25','free-video-25']);a=p.parse_args();ID=a.id;D=ROOT/'renders'/ID;data=json.loads((D/'voice-handoff/timings.json').read_text());S=data['scenes'];assert data['engine']=='chatterbox' and data['overall_match']>=.95 and len(S)==5
body=S[-1]['start'];fps=24;W,H=540,960;ff=imageio_ffmpeg.get_ffmpeg_exe();fontdir=ROOT/'templates/_base/fonts';font=lambda x:ImageFont.truetype(str(fontdir/'Inter.ttf'),x);bold=lambda x:ImageFont.truetype(str(fontdir/'Anton.ttf'),x);f12,f15,f19,f24,f31,f43,f54=font(12),font(15),font(19),font(24),bold(31),bold(43),bold(54)
style={
'claude-motion-25':{'bg':'#171e43','ink':'#fff4e8','accent':'#ffad85','panel':'#303663','titles':['AN IDEA → MOTION','WRITE THE BRIEF','SHAPE YOUR STYLE','CHECK ACCESS'],'tag':'HYPELESS  /  CLAUDE MOTION','keyword':'MOTION'},
'ai-income-25':{'bg':'#f7eddb','ink':'#21453e','accent':'#df725a','panel':'#fffaf1','titles':['14 IDEAS. ONE YOU.','NINE SERVICE IDEAS','FIVE LONGER PLAYS','START WITH A PROBLEM'],'tag':'HYPELESS  /  SOLO BUSINESS','keyword':'IDEAS'},
'paper-motion-25':{'bg':'#f5dfb9','ink':'#204b51','accent':'#ec785b','panel':'#fff4da','titles':['MAKE PAPER MOVE','BUILD YOUR STILL','GIVE IT MOTION','REFINE YOUR CLIP'],'tag':'HYPELESS  /  PAPER ANIMATION','keyword':'PAPER'},
'free-video-25':{'bg':'#111d48','ink':'#eef4ff','accent':'#8bf0dd','panel':'#27386d','titles':['FREE ≠ UNLIMITED','PROMPT YOUR CLIP','CHOOSE YOUR OUTPUT','KNOW THE LIMIT'],'tag':'HYPELESS  /  AI VIDEO','keyword':'VIDEO'}}[ID];cover=Image.open(ROOT/'covers'/ID/'cover.jpg').resize((W,H))
def rr(d,b,r,c,outline=None,width=1):d.rounded_rectangle(tuple(map(int,b)),int(r),fill=c,outline=outline,width=width)
def text(d,pos,s,f,c=None,anchor=None):d.text(pos,s,font=f,fill=c or style['ink'],anchor=anchor)
def ease(x):return 1-(1-max(0,min(1,x)))**3
def appeared(t,s,word,fallback=0):
 hit=next((w[1] for w in s['words'] if re.sub('[^a-z]','',str(w[0]).lower())==word),s['start']+fallback)
 return ease((t-hit)/.45)
def frame(t, transition=True):
 if t<1/fps:return cover.copy()
 i=max((k for k,s in enumerate(S[:-1]) if s['start']<=t),default=0);s=S[i];u=t-s['start'];progress=max(0,min(1,u/max(.01,s['end']-s['start'])));im=Image.new('RGB',(W,H),style['bg']);d=ImageDraw.Draw(im)
 # Each palette, material and visual language is topic-specific.
 if ID=='paper-motion-25':
  for x in range(0,W,33):
   for y in range(0,H,35):d.ellipse((x+(y%7),y,x+1+(y%7),y+1),fill='#e4ca9d')
 elif ID=='ai-income-25':
  for n in range(7):d.line((0,260+n*75,W,260+n*75),fill='#e6d8c6',width=1)
 else:
  for n in range(12):
   x=(n*101+int(t*12))%W;y=230+n*43;d.ellipse((x,y,x+3,y+3),fill=style['panel'])
 text(d,(40,85),style['tag'],f15,style['accent']);text(d,(40,123),style['titles'][i],f43);rr(d,(40,190,145,197),3,style['accent'])
 if ID=='claude-motion-25':
  if i==0:
   rr(d,(55,275,485,425),20,style['panel']);text(d,(75,300),'PROMPT',f15,style['accent']);text(d,(75,340),'Explain this idea',f24);text(d,(270,449),'↓',f43,style['accent'],'ma')
   for k in range(4):
    h=45+(k+1)*27*(.5+.5*math.sin(t*1.7+k));rr(d,(95+k*90,715-h,150+k*90,715),10,['#f3a27f','#f5d8b4','#9dc4f0','#f1b1bb'][k])
  elif i==1:
   rr(d,(45,270,495,625),23,style['panel']);text(d,(75,300),'CREATIVE BRIEF',f19,style['accent'])
   labels=['01   EXPLAIN THE IDEA','02   DEFINE THE AUDIENCE','03   DESCRIBE THE MOTION']
   for k,l in enumerate(labels):
    z=ease((progress-k*.22)*4);x=75+int(80*(1-z));rr(d,(x,355+k*77,x+365,408+k*77),10,'#465083');text(d,(x+12,369+k*77),l,f15)
   text(d,(270,690),'BRIEF  →  CODE  →  ANIMATION',f15,style['accent'],'ma')
  elif i==2:
   rr(d,(50,280,490,630),23,'#f7eadb');text(d,(75,300),'YOUR BRAND',f19,'#27345d')
   for k,c in enumerate(['#ffad85','#fbca8b','#779be1','#3b4c86']):d.ellipse((80+k*90,365,140+k*90,425),fill=c)
   for k in range(4):
    h=(50+k*26)*(.45+.55*abs(math.sin(t*1.3+k)));rr(d,(90+k*85,570-h,145+k*85,570),8,['#ffad85','#fbca8b','#779be1','#3b4c86'][k])
   text(d,(270,670),'ASK  →  REVIEW  →  REFINE',f19,style['accent'],'ma')
  else:
   rr(d,(58,290,482,610),24,style['panel']);text(d,(270,325),'CLAUDE MOTION',f31,style['ink'],'ma');text(d,(270,395),'TEAM + ENTERPRISE',f24,style['accent'],'ma');text(d,(270,450),'BETA  •  CHECK EXPORT',f19,style['ink'],'ma');d.arc((160,510,380,730),190,340,fill=style['accent'],width=8)
 elif ID=='ai-income-25':
  if i==0:
   text(d,(270,280),'14',ImageFont.truetype(str(fontdir/'Anton.ttf'),200),style['accent'],'ma');text(d,(270,540),'IDEAS',f54,style['ink'],'ma');text(d,(270,635),'ONE PROBLEM TO SOLVE',f19,style['ink'],'ma')
  elif i in (1,2):
   items=['TRAINING','CONTENT','SEARCH','ADS','WORKFLOWS','SUPPORT','ONGOING SERVICE','AI ADVICE','CLIENT SOFTWARE'] if i==1 else ['AUDIENCE','DIGITAL PRODUCT','PAID COMMUNITY','RESELL SOFTWARE','YOUR OWN APP']
   # reveal the cards sequentially in pace with the corresponding spoken list
   cols=3 if i==1 else 1; rows=3 if i==1 else 5
   for k,l in enumerate(items):
    z=ease((progress-(k/len(items))*.78)*9);x=45+(k%cols)*(153 if cols==3 else 0);y=260+(k//cols)*(140 if cols==3 else 95)+int((1-z)*35);w=137 if cols==3 else 450
    rr(d,(x+4,y+5,x+w+4,y+(115 if cols==3 else 72)+5),12,'#dac9b5');rr(d,(x,y,x+w,y+(115 if cols==3 else 72)),12,style['panel']);text(d,(x+13,y+12),f'{k+1 if i==1 else k+10:02}',f24,style['accent']);txt=l.split();
    if cols==3:
     for j,word in enumerate(txt):text(d,(x+12,y+50+j*18),word,f12,style['ink'])
    else:text(d,(x+85,y+22),l,f19,style['ink'])
  else:
   rr(d,(65,285,475,600),24,'#fffaf1');text(d,(270,320),'REAL CUSTOMER',f31,style['ink'],'ma');text(d,(270,390),'↓',f43,style['accent'],'ma');text(d,(270,460),'TEST YOUR OFFER',f31,style['ink'],'ma');text(d,(270,650),'NO INCOME GUARANTEE',f19,style['accent'],'ma')
 elif ID=='paper-motion-25':
  # Layered shapes with offset shadows and animated parallax simulate tactile cut paper.
  shift=int(13*math.sin(t*1.4));rr(d,(48,280,492,715),18,'#caac88');rr(d,(44,274,488,709),18,'#f8e5c6');d.ellipse((180+shift,313,346+shift,479),fill='#f2a45e');d.polygon([(44,600),(180+shift,440),(295,600)],fill='#e7806c');d.polygon([(180,640),(355-shift,415),(488,630)],fill='#538f88');d.polygon([(44,630),(170,525),(365,720),(44,709)],fill='#9dc9b3');d.polygon([(165,709),(345+shift,565),(488,640),(488,709)],fill='#2e6c69');
  for k in range(5):
   x=78+k*80+int(12*math.sin(t*1.8+k)); y=642+int(9*math.sin(t*2+k));d.ellipse((x,y,x+28,y+47),fill=['#eab35e','#e6745b','#67a596','#d3b765','#6b9a84'][k]);d.line((x+14,y+10,x+14,y+47),fill='#f6e8ca',width=2)
  if i==0:text(d,(270,739),'A STILL  →  A PAPER WORLD',f19,style['ink'],'ma')
  elif i==1:text(d,(270,739),'LAYERS  +  EDGES  +  SHADOWS',f19,style['ink'],'ma')
  elif i==2:
   rr(d,(80,640,460,690),10,'#fff8e9');text(d,(270,651),'SUN RISES  •  LEAVES SWAY',f15,style['ink'],'ma');text(d,(270,739),'IMAGE  →  MOTION PROMPT',f19,style['ink'],'ma')
  else:rr(d,(85,650,455,704),10,'#fff8e9');text(d,(270,666),'CHECK CREDITS + RIGHTS',f15,style['ink'],'ma')
 else:
  if i==0:
   rr(d,(55,285,485,645),26,style['panel']);text(d,(270,320),'FREE VIDEO',f43,style['ink'],'ma');text(d,(270,420),'100 / DAY',f54,style['accent'],'ma');text(d,(270,520),'NOT UNLIMITED',f24,style['ink'],'ma')
  elif i==1:
   rr(d,(55,280,485,645),23,style['panel']);text(d,(80,310),'VIDEO GENERATOR',f24);rr(d,(80,375,460,492),12,'#ebf4ff');text(d,(99,394),'A cinematic scene...',f19,'#233866');text(d,(99,440),'IMAGE + PROMPT',f15,'#456087');rr(d,(80,525,285,575),13,style['accent']);text(d,(182,537),'GENERATE  →',f19,'#10284e','ma');text(d,(270,690),'SIMULATED INTERFACE',f12,style['ink'],'ma')
  elif i==2:
   for k,l in enumerate(['FAST','QUALITY','ASPECT RATIO']):
    y=285+k*120;rr(d,(60,y,480,y+90),18,style['panel']);text(d,(85,y+25),l,f24);d.ellipse((410,y+28,445,y+63),fill=style['accent'])
   text(d,(270,687),'GENERATE  →  REVIEW  →  SAVE',f15,style['accent'],'ma')
  else:
   rr(d,(65,285,475,635),24,style['panel']);text(d,(270,325),'100 / DAY',f54,style['accent'],'ma');text(d,(270,420),'SIGN-IN REQUIRED',f24,style['ink'],'ma');text(d,(270,490),'LIMITS CAN CHANGE',f19,style['ink'],'ma');text(d,(270,550),'CHECK USAGE RIGHTS',f19,style['ink'],'ma')
 # A slow continuous camera move adds dimensional motion; content itself remains independently animated.
 scale=1.04+.035*(.5+.5*math.sin(t*.95));ww=int(W*scale);hh=int(H*scale);big=im.resize((ww,hh),Image.Resampling.BILINEAR);cx=max(0,min(ww-W,(ww-W)//2+int((ww-W)*.42*math.sin(t*1.3))));cy=max(0,min(hh-H,(hh-H)//2+int((hh-H)*.42*math.cos(t*.9))));im=big.crop((cx,cy,cx+W,cy+H));d=ImageDraw.Draw(im)
 # Scene-to-scene cross-dissolve tied to narrated beat boundaries.
 if transition and i>0 and 0<=u<.28:
  previous=frame(max(1/fps,s['start']-.05),False)
  im=Image.blend(previous,im,ease(u/.28));d=ImageDraw.Draw(im)
 # synchronized narration captions: actual aligned word times, never guessed
 words=s['words'];wi=next((k for k,w in enumerate(words) if w[1]<=t<w[2]+.02),None)
 if wi is not None:
  st=wi//3*3; group=words[st:st+3]; labels=[str(w[0]).upper() for w in group];ft=f24;lens=[d.textlength(x,font=ft) for x in labels];gap=9;total=sum(lens)+gap*(len(lens)-1)
  if total>450:ft=f19;lens=[d.textlength(x,font=ft) for x in labels];total=sum(lens)+gap*(len(lens)-1)
  x=(W-total)/2;rr(d,(x-12,815,x+total+12,864),12,'#192c3f')
  for k,l in enumerate(labels):text(d,(x,825),l,ft,'#ffcf8a' if st+k==wi else 'white');x+=lens[k]+gap
 return im
D.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix='four-reel-') as tmp:
 tmp=Path(tmp);vb=tmp/'body.mp4';cta=tmp/'cta.wav';ctaj=tmp/'cta.json';last=S[-1];doc=dict(data);doc['duration']=data['duration']-body;doc['scenes']=[{'start':0,'end':last['end']-body,'words':[[w[0],w[1]-body,w[2]-body] for w in last['words']]}];ctaj.write_text(json.dumps(doc))
 subprocess.run([ff,'-y','-loglevel','error','-ss',str(body),'-i',str(D/'voice-handoff/voice.wav'),'-acodec','pcm_s16le',str(cta)],check=True)
 cmd=[ff,'-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(fps),'-i','-','-i',str(D/'voice-handoff/voice.wav'),'-t',str(body),'-vf','scale=1080:1920:flags=lanczos','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k',str(vb)]
 process=subprocess.Popen(cmd,stdin=subprocess.PIPE)
 for n in range(math.ceil(body*fps)):
  process.stdin.write(frame(n/fps).tobytes())
 process.stdin.close();assert process.wait()==0
 subprocess.run([sys.executable,str(ROOT/'tools/append_house_outro.py'),'--input',str(vb),'--output',str(D/'draft-v2.mp4'),'--voice',str(cta),'--timings',str(ctaj),'--keyword',style['keyword'],'--body-seconds',str(body),'--prompt','for the guide'],cwd=ROOT,check=True)
 (D/'timing-manifest.json').write_text(json.dumps({'scenes':S,'outro_start':body},indent=2));print(ID,'render complete',flush=True)
