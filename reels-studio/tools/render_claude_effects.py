#!/usr/bin/env python3
"""Render the approved ContentSkills short with house-voice-aligned animated graphics."""
import json, math, subprocess, sys, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
import imageio_ffmpeg
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'renders/claude-video-effects-01'; VO=OUT/'voice-handoff/voice.wav'
D=json.loads((OUT/'voice-handoff/timings.json').read_text()); scenes=D['scenes']; duration=D['duration'];fps=24; W,H=540,960
F=ROOT/'templates/_base/fonts'; anton=lambda n:ImageFont.truetype(str(F/'Anton.ttf'),n); inter=lambda n:ImageFont.truetype(str(F/'Inter.ttf'),n); mono=lambda n:ImageFont.truetype(str(F/'JetBrainsMono.ttf'),n)
f22,f26,f31,f42,f54,f75=inter(22),inter(26),inter(31),anton(42),anton(54),anton(75)
cover=Image.open(ROOT/'covers/claude-video-effects-01/custom-cover-proposal.png').convert('RGB').resize((W,H),Image.Resampling.LANCZOS)
art=Image.open(ROOT/'covers/claude-video-effects-01/art.png').convert('RGB'); art=ImageOps.fit(art,(320,568),centering=(.5,.55))
editor=Image.open(ROOT/'captures/claude-video-effects-01/editor.jpg').convert('RGB')
logo=Image.open(ROOT/'brand/logo/mark-transparent-1024.png').convert('RGBA');logo.thumbnail((72,72))
# Static high quality gradient, then all major graphic objects animated separately.
bg=Image.new('RGB',(W,H)); pix=bg.load()
for y in range(H):
 for x in range(W):
  a=y/H;b=x/W;pix[x,y]=(int(45+100*a+12*b),int(23+20*a+4*b),int(125+31*a-36*b))

def rr(d,box,r,fill,outline=None,width=1):d.rounded_rectangle(tuple(int(x) for x in box),radius=r,fill=fill,outline=outline,width=width)
def txt(d,xy,s,font,fill,anchor=None,stroke=0,stroke_fill=None):d.text(xy,s,font=font,fill=fill,anchor=anchor,stroke_width=stroke,stroke_fill=stroke_fill)
def ease(x):x=max(0,min(1,x));return 1-(1-x)**3

def label(d,s):
 txt(d,(48,145),s,f42,'#fff1da')
 d.rounded_rectangle((49,210,143,216),radius=3,fill='#ffbb7d')

def person(d,x,y,scale=1):
 # Original illustrated creator. Layered separately so type actually passes behind.
 def B(a,b,c,e):return (int(x+a*scale),int(y+b*scale),int(x+c*scale),int(y+e*scale))
 d.ellipse(B(-82,-160,82,2),fill='#221742');d.rounded_rectangle(B(-110,-17,110,180),radius=int(45*scale),fill='#30c2bd')
 d.polygon([tuple(map(int,p)) for p in [(x-47*scale,y+30*scale),(x,y+80*scale),(x+47*scale,y+30*scale)]],fill='#168b95')
 d.ellipse(B(-58,-142,58,-14),fill='#e9a078');d.ellipse(B(-14,-70,-7,-63),fill='#34203d');d.ellipse(B(18,-70,25,-63),fill='#34203d')
 d.arc(B(-16,-61,23,-30),0,150,fill='#8e3d50',width=max(1,int(3*scale)))
 d.pieslice(B(-66,-163,65,-50),180,345,fill='#25163c');d.ellipse(B(-75,-143,-36,-65),fill='#25163c');d.ellipse(B(40,-139,76,-65),fill='#25163c')

def backdrop(d,t):
 for i in range(9):
  x=(i*109+32+20*math.sin(t*.7+i))%W;y=(170+i*119+10*math.cos(t*.8+i))%H
  d.ellipse((x,y,x+4+(i%3)*2,y+4+(i%3)*2),fill='#d5a8ef')
 d.arc((-160,300,280,720),40+int(t*4)%360,210+int(t*4)%360,fill='#ff8291',width=3)
 d.arc((380,40,720,380),100-int(t*5)%360,260-int(t*5)%360,fill='#8ee5ed',width=3)

def caption(im,t):
 words=[w for s in scenes for w in s.get('words',[])];idx=next((i for i,w in enumerate(words) if w[1]<=t<w[2]+.07),None)
 if idx is None:return
 # groups anchored to scene; display 3 words max, each highlighted as spoken
 scene=next((s for s in scenes if s['start']<=t<=s['end']+.05),None)
 if not scene:return
 ws=scene.get('words',[]);idx=next((i for i,w in enumerate(ws) if w[1]<=t<w[2]+.07),None)
 if idx is None:return
 start=(idx//3)*3;group=ws[start:start+3];d=ImageDraw.Draw(im)
 strings=[w[0].upper().strip() for w in group];font=inter(27)
 lengths=[d.textlength(s,font=font) for s in strings];total=sum(lengths)+12*(len(strings)-1)
 if total>470:
  font=inter(22);lengths=[d.textlength(s,font=font) for s in strings];total=sum(lengths)+9*(len(strings)-1)
 x=(W-total)/2;y=805
 rr(d,(x-13,y-9,x+total+13,y+38),14,'#21163c')
 for k,s in enumerate(strings):
  txt(d,(x,y),s,font,'#ffd978' if start+k==idx else '#ffffff');x+=lengths[k]+12

def make(t):
 if t < 1/fps:return cover.copy()
 i=max((j for j,s in enumerate(scenes) if s['start']<=t), default=0);s=scenes[i];u=max(0,t-s['start']); progress=min(1,u/max(.01,s['end']-s['start']));im=bg.copy();d=ImageDraw.Draw(im);backdrop(d,t)
 if i==0:
  label(d,'ONE PROMPT.')
  z=ease(u/1.0); x=110-15*z; y=270-15*z; sz=(int(320+30*z),int(500+40*z));small=ImageOps.fit(art,sz)
  rr(d,(x-8,y-8,x+sz[0]+8,y+sz[1]+8),30,'#ffe4bf');im.paste(small,(int(x),int(y)));d=ImageDraw.Draw(im)
  rr(d,(135,720,410,770),18,'#fff3da');txt(d,(272,728),'RAW  →  READY',inter(22),'#512e81',anchor='ma')
 elif i==1:
  label(d,'DROP. DESCRIBE.');z=ease(u/.9);x=int(75+45*z);y=int(290+75*z)
  rr(d,(x,y,x+300,y+300),25,'#f9e8d6');rr(d,(x+15,y+15,x+285,y+205),15,'#4d388d');person(d,x+150,y+140,.56)
  rr(d,(x+17,y+223,x+283,y+279),14,'#d6d2fc');txt(d,(x+30,y+235),'edit my clip...',mono(18),'#37265f')
  rr(d,(40,710,500,754),15,'#2a1955');n=int(28+350*progress);rr(d,(50,720,50+n,744),9,'#ff9c92')
 elif i==2:
  label(d,'TEXT BEHIND YOU')
  rr(d,(66,270,474,705),28,'#ffc193');rr(d,(76,280,464,695),22,'#8853c3')
  shift=int(115*(1-ease(u/1.4)));txt(d,(270+shift,369),'BIG',anton(137),'#fff0cf',anchor='ma');txt(d,(270-shift,480),'WORDS',anton(91),'#fff0cf',anchor='ma')
  person(d,270,540,1.22)
 elif i==3:
  label(d,'ADD A 3D ORB');cx=270+int(20*math.sin(t*1.4));cy=480+int(12*math.cos(t*1.7));r=int(145*ease(u/.9))
  for k in range(4,0,-1):d.ellipse((cx-r-k*10,cy-r-k*10,cx+r+k*10,cy+r+k*10),outline=['#7250a6','#826aca','#8e9fda','#a9ecee'][4-k],width=4)
  d.ellipse((cx-r,cy-r,cx+r,cy+r),fill='#4055ad',outline='#cafff9',width=5)
  for k in range(7):
   a=t*2+k*math.pi/3.5;xx=cx+math.cos(a)*r*.72;yy=cy+math.sin(a*1.8)*r*.7;d.line((cx,cy,xx,yy),fill='#a6f8ff',width=3);d.ellipse((xx-7,yy-7,xx+7,yy+7),fill='#f4ffff')
  d.ellipse((cx-20,cy-20,cx+20,cy+20),fill='#fff6fd')
 elif i==4:
  label(d,'CHARTS IN MOTION');rr(d,(60,275,480,680),26,'#f8ecd9');d.line((110,620,440,620),fill='#665588',width=3)
  for k,h in enumerate([108,190,145,270]):
   h=int(h*ease((u-k*.18)/1.15));x=120+k*78;rr(d,(x,620-h,x+48,620),10,['#ff8f80','#9c76e6','#55cad2','#feab7a'][k])
  pts=[(140,555),(220,493),(295,530),(375,405)]; n=min(len(pts),max(1,int(progress*6)))
  if n>1:d.line(pts[:n],fill='#433075',width=5,joint='curve')
  for x,y in pts[:n]:d.ellipse((x-6,y-6,x+6,y+6),fill='#433075')
 elif i==5:
  label(d,'WATCH IT TRANSFORM');z=ease(u/.8);rr(d,(70,275,470,690),25,'#fcebd4');
  small=ImageOps.fit(art,(int(355),int(360)));im.paste(small,(92,296));d=ImageDraw.Draw(im)
  rr(d,(105,605,435,655),16,'#ffb88f');txt(d,(270,617),'PROMPT → EDIT',inter(22),'#48286c',anchor='ma')
 elif i==6:
  label(d,'REVIEW YOUR STORY');z=ease(u/.8)
  # Moving actual project footage is the storyboard's playable preview.
  fs=sorted((OUT/'source-frames'/'6').glob('*.jpg'))
  if fs:
   shot=Image.open(fs[min(len(fs)-1,int(u*fps))]).convert('RGB')
   shot=ImageOps.fit(shot,(262,345));px=139+int(14*math.sin(u*1.1));py=243+int(7*math.sin(u*1.4))
   rr(d,(px-7,py-7,px+269,py+352),23,'#ffdfbc');im.paste(shot,(px,py));d=ImageDraw.Draw(im)
  for k in range(3):
   x=45+k*150;y=625+int(8*math.sin(t*2+k));rr(d,(x,y,x+138,y+70),16,'#fff0db');rr(d,(x+8,y+8,x+48,y+60),10,['#8e68d1','#68cbd2','#ffaf8f'][k]);txt(d,(x+54,y+22),['TEXT','ORB','CHART'][k],inter(16),'#4b317a')
  rr(d,(48,720,492,742),10,'#2a1955');rr(d,(52,724,52+int(432*progress),738),7,'#64eee0')
 else:
  label(d,'YOUR IDEAS.');rr(d,(79,264,461,687),28,'#ffd4aa'); small=ImageOps.fit(art,(350,385));im.paste(small,(95,280));d=ImageDraw.Draw(im)
  rr(d,(126,674,415,729),18,'#fff2da');txt(d,(270,683),'MORE MOTION',inter(24),'#4b287c',anchor='ma')
 # Real, silent source-project video demonstrations, animated inside the designed scene.
 # These are gallery clips from the ContentSkills repository, not claims of our own test run.
 if i in (0,1,2,3,4,5,7):
  directory=OUT/'source-frames'/str(i)
  frames=sorted(directory.glob('*.jpg'))
  if frames:
   index=min(len(frames)-1,int(u*fps))
   clip=Image.open(frames[index]).convert('RGB')
   clip=ImageOps.fit(clip,(290,420),method=Image.Resampling.LANCZOS)
   px=125+int(9*math.sin(t*.65));py=270+int(8*math.cos(t*.8))
   d=ImageDraw.Draw(im);rr(d,(px-8,py-8,px+298,py+428),22,'#ffdbb9')
   im.paste(clip,(px,py));d=ImageDraw.Draw(im)
   rr(d,(px+8,py+10,px+125,py+36),10,'#3b246c');txt(d,(px+16,py+13),'SOURCE DEMO',inter(12),'#fff7e4')
 caption(im,t)
 # persistent small brand wordmark at edge, not covering main art
 d=ImageDraw.Draw(im);txt(d,(W-40,110),'HYPELESS',inter(15),'#efe2fc',anchor='ra')
 return im

OUT.mkdir(parents=True,exist_ok=True);ff=imageio_ffmpeg.get_ffmpeg_exe();output=OUT/'claude-video-effects-01.mp4'
# Tail holds a brief established-brand card after the approved narration.
tail=1.5;frames=math.ceil((duration+tail)*fps)
cmd=[ff,'-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(fps),'-i','-','-i',str(VO),'-vf','scale=1080:1920:flags=lanczos','-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-af','apad','-t',str(duration+tail),'-movflags','+faststart',str(output)]
p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
for n in range(frames):
 t=n/fps
 if t>=duration:
  im=bg.copy();d=ImageDraw.Draw(im);backdrop(d,t);im.paste(logo,(234,353),logo);d=ImageDraw.Draw(im);txt(d,(270,458),'HYPELESS',anton(68),'#fff0da',anchor='ma');txt(d,(270,552),'TOOLS, MINUS THE HYPE.',inter(20),'#baf5f5',anchor='ma')
 else:im=make(t)
 p.stdin.write(im.tobytes())
 if n%240==0:print('render',n,'/',frames,flush=True)
p.stdin.close();code=p.wait()
if code:raise SystemExit(code)
print('RENDERED',output,flush=True)
