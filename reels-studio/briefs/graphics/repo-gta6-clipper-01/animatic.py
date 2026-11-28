from PIL import Image,ImageDraw,ImageFont
import math, subprocess, imageio_ffmpeg
from pathlib import Path
O=Path('renders/repo-gta6-clipper-01');O.mkdir(parents=True,exist_ok=True)
W,H=540,960; FPS=15
sans='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'; regular='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
F=lambda n: ImageFont.truetype(sans,n)
R=lambda n: ImageFont.truetype(regular,n)
white='#f7f7fa';ink='#18213b'; lime='#e8ff5d';pink='#ff6f91'; cyan='#70e9f4';navy='#23274b'
lines=[('STREAM TO','SHORT','Turn a long stream into vertical clips.','No endless scrubbing.'),('FIND THE','MOMENT','A stream link becomes a transcript.','Chat and loudness help find peaks.'),('PICK A','HIGHLIGHT','Signals suggest a moment.','An AI pass is optional.'),('BUILD THE','SHORT','Streamer above, game below.','Add a hook and captions.'),('YOU ARE','THE EDITOR','Review and adjust every Short.','The original stays intact.'),('CHECK THE','CATCH','Optional services may cost money.','Get permission to use footage.'),('TOOLS, MINUS','THE HYPE','Want the repo? Comment CLIP.','Follow @hypeless.')]
durs=[4.5,5,4.5,5,5,5,4.5]; boundaries=[0]
for x in durs:boundaries.append(boundaries[-1]+x)
def ease(x):
 x=max(0,min(1,x));return x*x*(3-2*x)
def rr(d,box,fill,r=14,outline=None,width=2):d.rounded_rectangle(box,radius=r,fill=fill,outline=outline,width=width)
def text(d,xy,s,font,fill=white):d.text(xy,s,font=font,fill=fill)
def frame(t):
 idx=next((i for i in range(len(durs)) if t<boundaries[i+1]),len(durs)-1); u=(t-boundaries[idx])/durs[idx]; p=ease(min(1,u*3)); a,b,c,e=lines[idx]
 im=Image.new('RGB',(W,H),'#713e8b' if idx%2==0 else '#1e7185');d=ImageDraw.Draw(im)
 # rich editorial field, no black
 d.polygon([(0,0),(540,0),(540,960),(0,960)],fill=['#954b76','#247d88','#6652a2','#b15f48','#477ca4','#a86275','#685599'][idx])
 d.ellipse((-170,-180,430,340),fill=['#f2a3a6','#74ced3','#bf9ada','#f6af84','#9fc8d8','#efb9a4','#b29bd3'][idx]);d.rectangle((0,820,540,960),fill=navy)
 text(d,(32,27),'HYPELESS  /  EXPLAINED',F(14),ink)
 text(d,(32,170),a,F(43),ink);text(d,(32,221),b,F(56),ink)
 text(d,(34,290),'ILLUSTRATION • NOT GAME FOOTAGE',F(11),ink)
 if idx==0:
  rr(d,(28,385,350,595),'#e4e4f3',18); rr(d,(44,400,334,548),'#595aa7',9)
  d.polygon([(44,523),(120,459),(190,516),(257,438),(334,512),(334,548),(44,548)],fill='#b99ddd')
  d.ellipse((64,413,119,468),fill=lime);d.rectangle((48,565,322,574),fill='#abb0d0');d.rectangle((48,565,48+int(270*p),574),fill=pink)
  xx=int(360-45*(1-p));rr(d,(xx,365,xx+150,667),navy,18);rr(d,(xx+10,375,xx+140,657),'#f7a289',12)
  d.rectangle((xx+18,390,xx+132,470),fill='#598ac1');d.ellipse((xx+55,402,xx+94,441),fill=lime)
  d.rectangle((xx+18,478,xx+132,600),fill='#5cb6a5');text(d,(xx+28,608),'CLIP!',F(17),ink)
 elif idx==1:
  rr(d,(28,365,512,694),'#eef5f4',18);text(d,(48,383),'STREAM SIGNALS',F(20),ink)
  d.line((55,500,485,500),fill='#a9bcc7',width=2)
  points=[]
  for x in range(75,480,4):
   z=(x-75)/400; spike=math.exp(-((z-.68)/.06)**2); amp=8+8*math.sin(z*31+t*3)+65*spike
   points.append((x,500-amp*math.sin(z*64)))
  d.line(points[:max(2,int(len(points)*p))],fill='#e26383',width=4)
  for n in range(16):
   h=(12+(n*17%33)+(100 if n in (10,11) else 0))*ease((u*3-n*.035));x=55+n*26
   rr(d,(x,659-h,x+15,659),cyan if n not in (10,11) else pink,4)
  text(d,(48,435),'LOUDNESS',F(14),ink);text(d,(48,578),'CHAT ACTIVITY',F(14),ink)
 elif idx==2:
  rr(d,(35,390,505,665),'#f2ebff',20);text(d,(55,410),'SOURCE TIMELINE',F(18),ink)
  rr(d,(55,462,485,510),'#949bc8',7);rr(d,(int(220+70*p),455,int(335+70*p),517),lime,8)
  rr(d,(75,570,230,625),'#e2d4f7',10); text(d,(100,585),'SIGNALS',F(17),ink)
  rr(d,(290,570,467,625),pink,10);text(d,(306,585),'AI OPTIONAL',F(15),ink)
  d.line((230,598,290,598),fill=ink,width=4)
 elif idx==3:
  rr(d,(139,365,401,720),navy,25); rr(d,(151,377,389,708),'#f8e4d0',15)
  y=int(420-30*p); rr(d,(163,y,377,y+96),'#6d8bc2',9);d.ellipse((237,y+13,299,y+75),fill=lime)
  text(d,(173,y+69),'STREAMER',F(12),white)
  yy=int(470+35*p);rr(d,(163,yy,377,yy+125),'#58a99b',9);d.polygon([(170,yy+108),(220,yy+54),(270,yy+92),(335,yy+30),(372,yy+73),(372,yy+120)],fill='#9fe1b1')
  text(d,(178,yy+5),'GAME',F(12),ink);text(d,(175,yy+100),'THAT WAS',F(19),white);text(d,(205,yy+125),'CLOSE!',F(21),lime)
 elif idx==4:
  rr(d,(28,385,512,680),'#f2f4ff',18);text(d,(49,405),'REVIEW YOUR CLIP',F(20),ink)
  rr(d,(50,452,490,500),'#adb2d5',8);end=int(450-75*p);rr(d,(95,452,end,500),'#7bcfc5',8);d.line((end,438,end,515),fill=pink,width=5)
  text(d,(50,522),'ORIGINAL KEPT',F(17),ink);rr(d,(50,567,490,583),'#c6cadb',6)
  rr(d,(125,610,415,657),lime,12);text(d,(151,621),'REVIEW → APPROVE',F(16),ink)
 elif idx==5:
  rr(d,(35,391,505,514),'#fff3dd',18);text(d,(58,412),'OPTIONAL SERVICES',F(20),ink);text(d,(58,447),'May cost money',R(19),ink)
  rr(d,(35,540,505,679),'#e7f9f0',18);text(d,(58,562),'CREATOR RIGHTS',F(20),ink);text(d,(58,599),'Get permission before posting',R(18),ink)
 else:
  rr(d,(55,400,485,674),'#f4d9d4',24);text(d,(81,435),'@HYPELESS',F(34),ink);text(d,(81,498),'WHAT IT DOES.',F(23),ink);text(d,(81,537),'WHAT IT COSTS.',F(23),ink);text(d,(81,576),'THE CATCH.',F(23),ink)
 text(d,(28,839),c,F(19),white);text(d,(28,876),e,F(18),lime);text(d,(28,925),'SILENT ANIMATIC • VOICE NOT YET RECORDED',F(11),'#cdd3ec')
 return im
ff=imageio_ffmpeg.get_ffmpeg_exe(); target=O/'gta6-clipper-silent-animatic.mp4'
cmd=[ff,'-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-vf','scale=1080:1920:flags=lanczos','-c:v','libx264','-preset','veryfast','-crf','23','-pix_fmt','yuv420p','-movflags','+faststart',str(target)]
p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
for i in range(round(boundaries[-1]*FPS)):p.stdin.write(frame(i/FPS).tobytes())
p.stdin.close();ret=p.wait()
if ret:raise SystemExit(ret)
subprocess.run([ff,'-y','-loglevel','error','-i',str(target),'-frames:v','1',str(O/'frame-zero.png')],check=True)
print('saved',target,'duration',boundaries[-1])
