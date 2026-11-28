#!/usr/bin/env python3
"""PhoneBox revised editorial: audio-cued illustrations and genuine product screenshots."""
import json,math,subprocess,tempfile,re
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps,ImageFilter
import imageio_ffmpeg
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'renders/phonebox-extra-01';orig=ROOT/'renders/repo-phonebox-01/voice-handoff';extra=OUT/'voice-handoff';cta=ROOT/'renders/phonebox-outro-fix/voice-handoff'
D=json.loads((orig/'timings.json').read_text());E=json.loads((extra/'timings.json').read_text());C=json.loads((cta/'timings.json').read_text());assert all(x['engine']=='chatterbox' and x['overall_match']>=.95 for x in (D,E,C))
heard=[str(w).lower() for c in C.get('chunks',[]) for w in c.get('heard_words',[])];assert any(heard[i]=='comment' and heard[i+1]=='phone' for i in range(len(heard)-1))
cut=19.545;extra_len=E['duration'];body_dur=cut+extra_len
S=D['scenes'][:4]+[{'start':cut+s['start'],'end':cut+s['end'],'words':[[w[0],w[1]+cut,w[2]+cut] for w in s['words']]} for s in E['scenes']]
ff=imageio_ffmpeg.get_ffmpeg_exe();fps=24;W,H=540,960;F=ROOT/'templates/_base/fonts'
font=lambda n:ImageFont.truetype(str(F/'Inter.ttf'),n);bold=lambda n:ImageFont.truetype(str(F/'Anton.ttf'),n)
f13,f15,f18,f21,f25,f30,f42,f58=font(13),font(15),font(18),font(21),font(25),font(30),bold(42),bold(58)
cover=Image.open(ROOT/'covers/repo-phonebox-01/cover.jpg').convert('RGB').resize((W,H),Image.Resampling.LANCZOS)
photo=Image.open(ROOT/'covers/repo-phonebox-01/purpose-made-art.png').convert('RGB')
photos={n:Image.open(ROOT/'captures/repo-phonebox-01'/f'{n}.png').convert('RGB') for n in ['home','system','settings-editor']};cache={}
bg=Image.new('RGB',(W,H));p=bg.load()
for y in range(H):
 for x in range(W):
  k=y/H;q=x/W;p[x,y]=(int(248-29*k+4*q),int(241-12*k),int(224+6*k+5*q))
def rr(d,b,r,c,outline=None,width=1):d.rounded_rectangle(tuple(int(v) for v in b),int(r),fill=c,outline=outline,width=int(width))
def txt(d,xy,s,f,c,anchor=None):d.text(xy,s,font=f,fill=c,anchor=anchor)
def ease(v):v=max(0,min(1,v));return 1-(1-v)**3
def cue(s,word,default):
 for w in s['words']:
  if re.sub(r'[^a-z]','',w[0].lower())==word:return w[1]
 return s['start']+default
def pop(t,start,dur=.55):return ease((t-start)/dur)
def key_screen(name,size):
 k=(name,size)
 if k not in cache:cache[k]=ImageOps.fit(photos[name],size,method=Image.Resampling.LANCZOS,centering=(.5,.42))
 return cache[k]
def phone(im,x,y,w,h,screen,alpha=1):
 x,y,w,h=map(int,(x,y,w,h));d=ImageDraw.Draw(im);rr(d,(x+10,y+14,x+w+10,y+h+14),33,'#b1aea2');rr(d,(x,y,x+w,y+h),34,'#224347');rr(d,(x+5,y+5,x+w-5,y+h-5),29,'#607774');rr(d,(x+10,y+10,x+w-10,y+h-10),24,'#183938')
 size=(max(w-28,4),max(h-28,4));pic=key_screen(screen,size);mask=Image.new('L',size);ImageDraw.Draw(mask).rounded_rectangle((0,0,*size),radius=19,fill=int(255*max(0,min(1,alpha))));im.paste(pic,(x+14,y+14),mask);d=ImageDraw.Draw(im);rr(d,(x+w*.37,y+8,x+w*.63,y+15),4,'#122f32')
def panel(d,box,title,col='#ffffff'):
 x,y,w,h=box;rr(d,(x+7,y+8,x+w+7,y+h+8),18,'#b5c9bb');rr(d,(x,y,x+w,y+h),18,col);txt(d,(x+14,y+12),title,f15,'#265755')
def moving_bg(t):
 im=bg.copy();d=ImageDraw.Draw(im)
 # Huge slow overlapping colour forms create actual compositional parallax, not flashing.
 d.ellipse((-210+int(85*math.sin(t*.45)),240,180+int(85*math.sin(t*.45)),720),fill='#cce4d4')
 d.ellipse((390+int(70*math.cos(t*.5)),100,790+int(70*math.cos(t*.5)),560),fill='#f3c9a4')
 for k in range(8):
  x=(k*127+int(45*t))%650-55;y=255+k*66+int(10*math.sin(t+k));d.ellipse((x,y,x+5,y+5),fill='#85b9a8')
 return im
def frame(t, transition=True):
 if t<1/fps:return cover.copy()
 idx=max((i for i,s in enumerate(S) if s['start']<=t),default=0);s=S[idx];u=max(0,t-s['start']);pr=max(0,min(1,u/max(.01,s['end']-s['start'])));im=moving_bg(t);d=ImageDraw.Draw(im)
 titles=['YOUR OLD ANDROID','CONNECT YOUR PHONE','YOUR DESK, UPGRADED','MAKE IT YOURS','YOUR PAGES, YOUR RULES','READY TO USE']
 txt(d,(45,99),'HYPELESS  /  PHONEBOX',f15,'#315d58');txt(d,(45,145),titles[idx],f42,'#163f43');rr(d,(45,215,150,222),4,'#ed9668')
 if idx==0:
  drawer=pop(t,cue(s,'drawer',.5),.9);power=pop(t,cue(s,'control',1.8),1)
  rr(d,(39,600+35*drawer,501,752+35*drawer),23,'#ae9278');rr(d,(52,612+35*drawer,488,716+35*drawer),18,'#d5bda1');rr(d,(198,690+35*drawer,342,698+35*drawer),4,'#98785e')
  x=143+12*math.sin(t*1.6);y=455-140*drawer-10*math.sin(t*.9);phone(im,x,y,250,370,'home',power);d=ImageDraw.Draw(im)
  a=pop(t,cue(s,'turn',1.2));rr(d,(52,765,488,804),12,'#f8e4ca');txt(d,(270,772),'FROM DRAWER  →  DESK',f18,'#24554f','ma')
 elif idx==1:
  usb=pop(t,cue(s,'usb',1.1),1);wifi=pop(t,cue(s,'wi',2),.6)
  rr(d,(50,319,320,516),20,'#335e5b');rr(d,(60,329,310,499),14,'#b8dfcf');rr(d,(77,345,293,480),12,'#f4f6e7');d.line((185,518,185,550),fill='#376d66',width=9);rr(d,(133,548,237,562),5,'#376d66')
  x=342+10*math.sin(t*1.3);y=316+8*math.sin(t);phone(im,x,y,146,270,'home');d=ImageDraw.Draw(im)
  pts=[(274,503),(315,558),(365,558),(382,526)];n=1+int(3*usb)
  if n>1:d.line(pts[:n],fill='#e58365',width=9,joint='curve')
  if wifi>.1:
   for k in range(1,4):d.arc((335-k*20,282-k*20,335+k*20,282+k*20),215,325,fill='#379c83',width=4)
  rr(d,(62,634,478,696),18,'#fff8e9');txt(d,(270,649),'USB  /  PAIRED WI-FI',f21,'#1c5951','ma');txt(d,(270,742),'APP + DESKTOP AGENT',f15,'#50736b','ma')
 elif idx==2:
  # Pop-in cards are cued to individual spoken feature names.
  phx=65+8*math.sin(t);phone(im,phx,285,210,380,'system');d=ImageDraw.Draw(im)
  a=pop(t,cue(s,'stats',.3));b=pop(t,cue(s,'music',1));c=pop(t,cue(s,'shortcuts',2));
  for k,(amt,yy,lab,col) in enumerate([(a,310,'SYSTEM','#fff9ef'),(b,454,'MEDIA','#f5cf9b'),(c,576,'SHORTCUT','#d3eddf')]):
   xx=300+int(180*(1-amt));panel(d,(xx,yy,185,110),lab,col)
   if k==0:
    points=[(xx+14+i*21,yy+83-int(v*48*a)) for i,v in enumerate([.2,.4,.25,.62,.42,.72,.58,.85])]
    if a>0:d.line(points,fill='#29a98b',width=5,joint='curve')
   elif k==1:
    rr(d,(xx+14,yy+70,xx+166,yy+78),4,'#fdf6e7');rr(d,(xx+14,yy+70,xx+14+int((100+35*math.sin(t*2))*b),yy+78),4,'#1f826e')
   else:
    rr(d,(xx+14,yy+62,xx+165,yy+84),8,'#7ec4ad');d.ellipse((xx+145-8,yy+73-8,xx+145+8,yy+73+8),fill='#1e806b')
  rr(d,(78,706,462,750),14,'#f8e4ca');txt(d,(270,716),'PROJECT DEMO • SAMPLE DATA',f15,'#466b60','ma')
 elif idx==3:
  # Browser editor + widget physically dragged and resized to the words.
  scr=key_screen('settings-editor',(412,246));rr(d,(48,295,492,569),22,'#315d59');im.paste(scr,(64,309));d=ImageDraw.Draw(im)
  move=pop(t,cue(s,'widgets',.2),1.8);xx=75+int(245*move);yy=490-int(90*move);rr(d,(xx+5,yy+7,xx+122,yy+64),13,'#b88767');rr(d,(xx,yy,xx+117,yy+57),12,'#efad76',outline='#fff9e9',width=3);txt(d,(xx+13,yy+16),'WIDGET',f15,'#27544d')
  p=pop(t,cue(s,'layout',1));d.line((270,588,270,626),fill='#3f9c80',width=6);d.polygon([(258,618),(282,618),(270,634)],fill='#3f9c80');phone(im,204+8*math.sin(t),622,132,160,'home');d=ImageDraw.Draw(im);txt(d,(270,777),'DRAG  •  RESIZE  •  SAVE',f18,'#21544b','ma')
 elif idx==4:
  p=pop(t,cue(s,'stats',.8));q=pop(t,cue(s,'media',2));phone(im,170+12*math.sin(t*1.1),310,200,365,'home');d=ImageDraw.Draw(im)
  panel(d,(44-int(160*(1-p)),365,136,125),'SYSTEM','#e2f4e4');panel(d,(361+int(160*(1-q)),465,132,125),'MEDIA','#f8d0a3')
  for k in range(5):
   x=63+k*19;h=(16+k*9)*p;rr(d,(x,463-h,x+11,463),4,'#4baa88')
  d.ellipse((397,506,445,554),fill='#e57b68');d.polygon([(416,516),(416,544),(437,530)],fill='#fff9e8')
  txt(d,(270,727),'PAGES FOR YOUR WORKFLOW',f18,'#24574e','ma')
 else:
  a=pop(t,cue(s,'drag',0),1.2);b=pop(t,cue(s,'save',.8));c=pop(t,cue(s,'permissions',3));
  rr(d,(55,305,485,648),22,'#35635e');scr=key_screen('settings-editor',(406,300));im.paste(scr,(67,317));d=ImageDraw.Draw(im)
  x=88+int(225*a);y=486-int(88*a);rr(d,(x,y,x+110+int(24*b),y+58),12,'#f2af78',outline='#fff9e9',width=3);txt(d,(x+14,y+16),'WIDGET',f15,'#24564d')
  rr(d,(111,671,429,730),17,'#4cae91');txt(d,(270,683),'✓  SAVE YOUR LAYOUT',f21,'white','ma')
  if c>.1:txt(d,(270,760),'FEATURES VARY BY SYSTEM',f15,'#476f64','ma')
 # A continuous composition-level drift adds dimensional camera motion around purposeful cues.
 if t>1/fps:
  scale=1.03+0.035*(.5+.5*math.sin(t*1.1));ww=int(W*scale);hh=int(H*scale);big=im.resize((ww,hh),Image.Resampling.BILINEAR);cx=(ww-W)//2+int((ww-W)*.35*math.sin(t*1.3));cy=(hh-H)//2+int((hh-H)*.35*math.cos(t));cx=max(0,min(ww-W,cx));cy=max(0,min(hh-H,cy));im=big.crop((cx,cy,cx+W,cy+H))
 words=s['words'];i=next((i for i,w in enumerate(words) if w[1]<=t<w[2]+.02),None)
 if i is not None:
  st=i//3*3;group=words[st:st+3];strings=[w[0].upper() for w in group];ft=f25;d=ImageDraw.Draw(im);lens=[d.textlength(x,font=ft) for x in strings];gap=12;total=sum(lens)+gap*(len(lens)-1)
  if total>446:ft=f21;lens=[d.textlength(x,font=ft) for x in strings];gap=8;total=sum(lens)+gap*(len(lens)-1)
  x=(W-total)/2;rr(d,(x-13,815,x+total+13,864),13,'#163f43')
  for k,string in enumerate(strings):txt(d,(x,823),string,ft,'#ffd28e' if st+k==i else '#fff');x+=lens[k]+gap
 if transition and idx>0 and 0<=u<.24:
  previous=frame(max(1/fps,s['start']-.04),False);im=Image.blend(previous,im,ease(u/.24))
 return im
with tempfile.TemporaryDirectory(prefix='phoneboxv2-',dir='/var/tmp') as td:
 tmp=Path(td);body=tmp/'body.mp4';mix=tmp/'narration.wav'
 filt=f'[0:a]atrim=duration={cut},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=mono[a0];[1:a]aresample=48000,aformat=channel_layouts=mono[a1];[a0][a1]concat=n=2:v=0:a=1[a]'
 subprocess.run([ff,'-y','-v','error','-i',str(orig/'voice.wav'),'-i',str(extra/'voice.wav'),'-filter_complex',filt,'-map','[a]','-acodec','pcm_s16le',str(mix)],check=True)
 cmd=[ff,'-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','540x960','-r',str(fps),'-i','-','-i',str(mix),'-vf','scale=1080:1920:flags=lanczos','-t',str(body_dur),'-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k',str(body)]
 proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
 try:
  for n in range(math.ceil(body_dur*fps)):proc.stdin.write(frame(n/fps).tobytes())
 finally:proc.stdin.close()
 assert proc.wait()==0
 subprocess.run(['python3',str(ROOT/'tools/append_house_outro.py'),'--input',str(body),'--output',str(OUT/'phonebox-v2.mp4'),'--voice',str(cta/'voice.wav'),'--timings',str(cta/'timings.json'),'--keyword','PHONE','--body-seconds',str(body_dur)],cwd=ROOT,check=True)
 scenes=S+[{'words':[[w[0],w[1]+body_dur,w[2]+body_dur] for w in C['scenes'][0]['words']]}]
 (OUT/'timing-manifest.json').write_text(json.dumps({'scenes':scenes,'body_seconds':body_dur,'outro_start':body_dur,'timing_note':'Original body, extra narration, corrected CTA; ASR-aligned words are approximate.'},indent=2)+'\n')
 print('Body',body_dur,'seconds; revised scenes',len(S),'plus shared narrated outro',flush=True)
