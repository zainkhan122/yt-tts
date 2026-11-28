#!/usr/bin/env python3
"""Original PhoneBox motion graphics; shared house outro and aligned Option-3 voice."""
import json,math,subprocess,tempfile
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps,ImageFilter
import imageio_ffmpeg
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'renders/repo-phonebox-01';D=json.loads((OUT/'voice-handoff/timings.json').read_text());S=D['scenes']; assert len(S)==5 and D['engine']=='chatterbox' and D['overall_match']>=.95
ff=imageio_ffmpeg.get_ffmpeg_exe();fps=24;W,H=540,960
F=ROOT/'templates/_base/fonts';font=lambda n:ImageFont.truetype(str(F/'Inter.ttf'),n);bold=lambda n:ImageFont.truetype(str(F/'Anton.ttf'),n);mono=lambda n:ImageFont.truetype(str(F/'JetBrainsMono.ttf'),n)
f14,f17,f20,f24,f28,f40,f61=font(14),font(17),font(20),font(24),font(28),bold(40),bold(61)
cover=Image.open(ROOT/'covers/repo-phonebox-01/cover.jpg').convert('RGB').resize((W,H),Image.Resampling.LANCZOS)
photos={n:Image.open(ROOT/'captures/repo-phonebox-01'/f'{n}.png').convert('RGB') for n in ['home','system','settings-editor']}
# Warm studio gradient; no black backgrounds in the main content.
bg=Image.new('RGB',(W,H));p=bg.load()
for y in range(H):
 for x in range(W):
  k=y/H;q=x/W;p[x,y]=(int(246-28*k+4*q),int(238-11*k),int(218+8*k+4*q))
def rr(d,b,r,c,outline=None,width=1):d.rounded_rectangle(tuple(int(v) for v in b),int(r),fill=c,outline=outline,width=width)
def txt(d,xy,s,f,c,anchor=None):d.text(xy,s,font=f,fill=c,anchor=anchor)
def ease(v):v=max(0,min(1,v));return 1-(1-v)**3
def phone(im,x,y,w,h,screen='home',progress=1):
 # Physical hardware, independently moved/scaled as an object; official UI is demonstrative.
 d=ImageDraw.Draw(im);rr(d,(x+10,y+16,x+w+10,y+h+16),36,'#b1aaa1');rr(d,(x,y,x+w,y+h),38,'#203b43');rr(d,(x+7,y+7,x+w-7,y+h-7),31,'#52666a');rr(d,(x+12,y+12,x+w-12,y+h-12),28,'#102e34')
 inner=(int(w-32),int(h-32));screenim=ImageOps.fit(photos[screen],inner,method=Image.Resampling.LANCZOS,centering=(.5,.35));mask=Image.new('L',inner);ImageDraw.Draw(mask).rounded_rectangle((0,0,*inner),radius=22,fill=int(255*max(0,min(1,progress))));im.paste(screenim,(int(x+16),int(y+16)),mask)
 d=ImageDraw.Draw(im);rr(d,(x+w*.39,y+9,x+w*.61,y+17),4,'#183138');return d
def frame(t):
 if t<1/fps:return cover.copy()
 idx=max((i for i,s in enumerate(S[:4]) if s['start']<=t),default=0);s=S[idx];u=max(0,t-s['start']);prog=max(0,min(1,u/max(.1,s['end']-s['start'])));im=bg.copy();d=ImageDraw.Draw(im)
 # Animated background accents and persistent editorial furniture.
 for i in range(12):
  x=(i*89+20+int(6*math.sin(t+i)))%W;y=(i*121+82+int(8*math.cos(t*.7+i)))%H
  d.ellipse((x,y,x+5,y+5),fill='#97c8bd')
 txt(d,(48,105),'HYPELESS / PHONEBOX',f14,'#496e69');rr(d,(48,213,141,220),4,'#ed9a6d')
 heads=['YOUR OLD ANDROID','CONNECT TO YOUR PC','YOUR DESK, UPGRADED','MAKE IT YOURS']
 txt(d,(48,145),heads[idx],f40,'#163f43')
 if idx==0:
  # Drawer opens, phone rises and powers into a rich dashboard.
  z=ease(u/1.5);rr(d,(45,596,495,746),24,'#c7b29d');rr(d,(55,604,485,710),20,'#a18979');rr(d,(204,684,336,693),4,'#e5c7a7')
  x=153+int(8*math.sin(t));y=430-int(118*z);phone(im,x,y,234,358,'home',ease((u-.7)/1.0));d=ImageDraw.Draw(im)
  rr(d,(57,749,483,790),14,'#f7daba');txt(d,(270,757),'FROM DRAWER  →  DESK',f17,'#245354','ma')
  for k in range(4):
   px=100+k*109;py=350+int(12*math.sin(t+k));d.line((px-7,py,px+7,py),fill='#edab74',width=3);d.line((px,py-7,px,py+7),fill='#edab74',width=3)
 elif idx==1:
  z=ease(u/1.4);rr(d,(55,355,315,537),20,'#36585c');rr(d,(65,365,305,512),13,'#d3ece6');rr(d,(80,385,290,494),10,'#9bc8bd');d.line((185,538,185,565),fill='#587878',width=8);rr(d,(135,562,235,573),5,'#587878')
  d.line((272,516,310,575,359,575,374,515),fill='#ed946c',width=9,joint='curve');d.ellipse((310-7,575-7,310+7,575+7),fill='#fff0d5')
  phone(im,345,333-int(12*z),145,266,'home');d=ImageDraw.Draw(im);rr(d,(54,641,486,705),20,'#f9f0dd');txt(d,(270,655),'USB  OR  PAIRED WI-FI',f20,'#1b5453','ma');txt(d,(270,738),'PHONE APP + DESKTOP AGENT',f14,'#58736d','ma')
 elif idx==2:
  phone(im,83,286,201,370,'system');d=ImageDraw.Draw(im)
  # Narration-synchronized live-looking but explicitly illustrative metric build.
  rr(d,(303,320,489,454),20,'#ffffff');txt(d,(319,337),'SYSTEM',f17,'#397370');pts=[]
  for k,val in enumerate([.2,.35,.3,.56,.44,.71,.62,.8]):
   if k<=int(prog*11):pts.append((322+k*21,427-int(val*65)))
  if len(pts)>1:d.line(pts,fill='#37a88c',width=5,joint='curve')
  rr(d,(303,473,489,554),18,'#e6bc91');txt(d,(319,490),'♫  MUSIC',f20,'#245354');rr(d,(325,524,460,531),3,'#fff5e7');rr(d,(325,524,325+int(105*(.5+.3*math.sin(t))),531),3,'#287b6c')
  rr(d,(303,572,489,653),18,'#d9ece1');txt(d,(319,589),'↗  SHORTCUT',f17,'#245354');rr(d,(315,623,452,630),3,'#73b4a3')
  rr(d,(82,698,458,746),15,'#f7daba');txt(d,(270,708),'SAMPLE DATA • NOT A LIVE TEST',f14,'#4b706a','ma')
 else:
  # Project's actual editor screenshot with a separately animated widget and final phone.
  screen=ImageOps.fit(photos['settings-editor'],(412,246),method=Image.Resampling.LANCZOS);rr(d,(52,298,488,571),24,'#315459');im.paste(screen,(64,310));d=ImageDraw.Draw(im)
  x=68+int(240*ease(u/2.0));y=518-int(68*ease(u/2.0));rr(d,(x,y,x+114,y+57),13,'#e9a16e',outline='#fff4de',width=3);txt(d,(x+12,y+17),'WIDGET',f14,'#1c4f4b')
  d.line((267,588,267,630),fill='#58a994',width=5);d.polygon([(256,621),(278,621),(267,638)],fill='#58a994')
  phone(im,209,615,122,145,'home');d=ImageDraw.Draw(im);txt(d,(270,778),'DRAG  •  RESIZE  •  SAVE',f17,'#1d5350','ma')
 # Karaoke-style aligned captions based on the real words in this beat.
 words=s['words'];i=next((i for i,w in enumerate(words) if w[1]<=t<w[2]+.03),None)
 if i is not None:
  st=(i//3)*3;group=words[st:st+3];strings=[w[0].upper() for w in group];ft=font(25);d=ImageDraw.Draw(im);lens=[d.textlength(x,font=ft) for x in strings];gap=12;total=sum(lens)+gap*(len(lens)-1)
  if total>448:ft=font(20);lens=[d.textlength(x,font=ft) for x in strings];gap=9;total=sum(lens)+gap*(len(lens)-1)
  x=(W-total)/2;rr(d,(x-13,812,x+total+13,861),13,'#163f43')
  for k,string in enumerate(strings):txt(d,(x,820),string,ft,'#ffd28e' if st+k==i else '#fff');x+=lens[k]+gap
 if idx>0 and 0<=t-s['start']<.22:
  previous=frame(max(1/fps,s['start']-.05));im=Image.blend(previous,im,ease((t-s['start'])/.22))
 return im
cut=max(0,S[4]['words'][0][1]-.035)
with tempfile.TemporaryDirectory(prefix='phonebox-',dir='/var/tmp') as td:
 tmp=Path(td);body=tmp/'body.mp4';cta=tmp/'cta.wav';tim=tmp/'cta.json'
 cmd=[ff,'-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','540x960','-r',str(fps),'-i','-','-i',str(OUT/'voice-handoff/voice.wav'),'-vf','scale=1080:1920:flags=lanczos','-t',str(cut),'-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k',str(body)]
 proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
 for n in range(math.ceil(cut*fps)):proc.stdin.write(frame(n/fps).tobytes())
 proc.stdin.close();assert proc.wait()==0
 subprocess.run([ff,'-y','-v','error','-ss',str(cut),'-i',str(OUT/'voice-handoff/voice.wav'),'-acodec','pcm_s16le',str(cta)],check=True)
 words=[[w[0],round(max(0,w[1]-cut),3),round(max(0,w[2]-cut),3)] for w in S[4]['words']];dur=D['duration']-cut
 tim.write_text(json.dumps({'engine':'chatterbox','overall_match':D['overall_match'],'duration':dur,'scenes':[{'words':words}]}))
 subprocess.run(['python3',str(ROOT/'tools/append_house_outro.py'),'--input',str(body),'--output',str(OUT/'phonebox-review.mp4'),'--voice',str(cta),'--timings',str(tim),'--keyword','PHONE','--body-seconds',str(cut)],cwd=ROOT,check=True)
 print('Body seconds',cut,'outro seconds',dur,flush=True)
