#!/usr/bin/env python3
"""Original narration-synchronized visual stories for fourteen solo business ideas."""
import re,json,math,subprocess,sys,tempfile
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import imageio_ffmpeg
R=Path(__file__).resolve().parents[1];ID='ai-business-action-01';D=R/'renders'/ID;J=json.loads((D/'voice-handoff/timings.json').read_text());S=J['scenes'];assert J['engine']=='chatterbox' and J['overall_match']>=.95 and len(S)==10
RATE=1.06
for scene in S:
 scene['start']/=RATE;scene['end']/=RATE;scene['words']=[[w[0],w[1]/RATE,w[2]/RATE] for w in scene['words']]
J['duration']/=RATE
FF=imageio_ffmpeg.get_ffmpeg_exe();W,H=540,960;FPS=24;fonts=R/'templates/_base/fonts';f=lambda x:ImageFont.truetype(str(fonts/'Inter.ttf'),x);b=lambda x:ImageFont.truetype(str(fonts/'Anton.ttf'),x)
f12,f15,f19,f23,f29,f39,f48,f80=f(12),f(15),f(19),f(23),b(29),b(39),b(48),b(80)
C={'paper':'#fbf0dc','ink':'#224940','coral':'#e56955','yellow':'#f5bd59','green':'#8dc9a3','mint':'#c7e7c8','teal':'#438e7c','blue':'#7aaabc','dark':'#173d37','light':'#fffaf1','line':'#dfcfb8','pink':'#f7b0a1'}
cover=Image.open(R/'covers'/ID/'cover.jpg').convert('RGB').resize((W,H),Image.Resampling.LANCZOS)
def e(x):x=max(0,min(1,x));return 1-(1-x)**3
def clamp(x):return max(0,min(1,x))
def rr(d,b,r,fill,outline=None,width=1):d.rounded_rectangle(tuple(map(int,b)),int(r),fill=fill,outline=outline,width=width)
def txt(d,xy,s,ft,col=None,anchor=None):d.text(xy,str(s),font=ft,fill=col or C['ink'],anchor=anchor)
def line(d,coords,fill,w=4):d.line([tuple(map(int,p)) for p in coords],fill=fill,width=w,joint='curve')
def person(d,x,y,scale=1,col=None):
 col=col or C['teal'];r=18*scale;d.ellipse((x-r,y-r,x+r,y+r),fill=col);rr(d,(x-30*scale,y+24*scale,x+30*scale,y+76*scale),22*scale,col)
def sheet(d,x,y,w=140,h=185,col=None):
 rr(d,(x+6,y+8,x+w+6,y+h+8),13,'#d5cbb7');rr(d,(x,y,x+w,y+h),13,col or C['light']);rr(d,(x+17,y+25,x+w-17,y+35),5,C['mint']);rr(d,(x+17,y+55,x+w-35,y+63),4,C['line']);rr(d,(x+17,y+77,x+w-25,y+85),4,C['line']);
def phone(d,x,y,w=155,h=260):
 rr(d,(x+7,y+10,x+w+7,y+h+10),25,'#d5cbb7');rr(d,(x,y,x+w,y+h),25,C['dark']);rr(d,(x+8,y+11,x+w-8,y+h-10),18,C['light']);rr(d,(x+w*.36,y+15,x+w*.64,y+21),3,C['dark'])
def bubble(d,x,y,w,h,col=None):rr(d,(x,y,x+w,y+h),18,col or C['light']);d.polygon([(x+26,y+h-3),(x+21,y+h+15),(x+45,y+h-3)],fill=col or C['light'])
def check(d,x,y,r=22):
 d.ellipse((x-r,y-r,x+r,y+r),fill=C['teal']);line(d,[(x-r*.48,y),(x-r*.1,y+r*.36),(x+r*.55,y-r*.38)],'white',4)
def arrow(d,x1,y1,x2,y2,p=1,col=None):
 xx=x1+(x2-x1)*p;yy=y1+(y2-y1)*p;line(d,[(x1,y1),(xx,yy)],col or C['coral'],5)
 if p>.96:d.polygon([(x2,y2),(x2-14,y2-8),(x2-14,y2+8)],fill=col or C['coral'])
def cursor(d,x,y):d.polygon([(x,y),(x+3,y+24),(x+9,y+18),(x+14,y+29),(x+19,y+27),(x+14,y+15),(x+22,y+14)],fill=C['dark'],outline='white',width=2)
def spark(d,x,y,n=17,col=None):
 d.polygon([(x,y-n),(x+4,y-4),(x+n,y),(x+4,y+4),(x,y+n),(x-4,y+4),(x-n,y),(x-4,y-4)],fill=col or C['yellow'])
def header(d,no,title):
 txt(d,(38,73),'HYPELESS  /  SOLO AI BUSINESS',f15,C['teal']);txt(d,(38,112),title,f48,C['ink']);rr(d,(38,176,137,184),4,C['coral']);
 if no is not None:rr(d,(435,79,501,129),17,C['ink']);txt(d,(468,88),f'{no:02}',f29,'white','ma')
def bg(t):
 im=Image.new('RGB',(W,H),C['paper']);d=ImageDraw.Draw(im)
 d.ellipse((-270+int(20*math.sin(t)),240,100+int(20*math.sin(t)),610),fill='#f3debd');d.ellipse((450+int(20*math.cos(t)),350,690+int(20*math.cos(t)),680),fill='#f4d8bc')
 return im
def word_index(sc,needle,which=0):
 found=[w[1] for w in sc['words'] if re.sub('[^a-z]','',w[0].lower())==needle];return found[which] if len(found)>which else None
# Two narration-aligned actions per scene: split on the first word of each second sentence.
splits=[('turn',0),('test',0),('answer',0),('advise',0),('build',1),('run',0),('or',0)]
beats=[{'start':S[0]['start'],'end':S[0]['end'],'kind':-1,'scene':0}]
for k,(needle,occ) in enumerate(splits):
 sc=S[k+1];mid=word_index(sc,needle,occ);assert mid and sc['start']<mid<sc['end'],(k,needle,sc)
 beats.extend([{'start':sc['start'],'end':mid,'kind':2*k,'scene':k+1},{'start':mid,'end':sc['end'],'kind':2*k+1,'scene':k+1}])
beats.append({'start':S[8]['start'],'end':S[8]['end'],'kind':14,'scene':8})
labels=['TEACH A TEAM','MAKE CONTENT','IMPROVE SEARCH','TEST AD CREATIVE','AUTOMATE WORK','ANSWER CUSTOMERS','OWN AN OUTCOME','ADVISE ON AI','BUILD FOR A CLIENT','GROW AN AUDIENCE','SELL A PRODUCT','RUN A COMMUNITY','RESELL SOFTWARE','BUILD YOUR APP']
def frame(t,transition=True):
 if t<1/FPS:return cover.copy()
 z=max((i for i,x in enumerate(beats) if x['start']<=t),default=0);bt=beats[z];kind=bt['kind'];u=max(0,t-bt['start']);du=max(.12,bt['end']-bt['start']);p=clamp(u/du);a=e(p/.72);finish=e((p-.45)/.45);im=bg(t);d=ImageDraw.Draw(im)
 if kind==-1:
  header(d,None,'PICK ONE IDEA');txt(d,(270,235),'14',ImageFont.truetype(str(fonts/'Anton.ttf'),180),C['coral'],'ma');txt(d,(270,445),'REAL PROBLEMS',f39,C['ink'],'ma')
  for k in range(5):
   angle=t*1.4+k*math.tau/5;x=270+190*math.cos(angle);y=640+95*math.sin(angle);d.ellipse((x-22,y-22,x+22,y+22),fill=[C['green'],C['yellow'],C['coral'],C['blue'],C['teal']][k])
  txt(d,(270,750),'ONE PROBLEM  →  ONE OFFER',f19,C['ink'],'ma')
 elif kind==14:
  header(d,None,'START WITH A PROBLEM');bubble(d,65,270,220,115);txt(d,(92,296),'CLIENT NEED',f23);arrow(d,305,325,448,325,a)
  sheet(d,330,390,145,180);txt(d,(351,426),'OFFER',f23,C['ink']);check(d,430,535,22)
  x=75+int(190*a);person(d,x,505,.9,C['teal']);txt(d,(270,735),'TEST  →  LEARN  →  REFINE',f19,C['ink'],'ma');txt(d,(270,776),'NO INCOME GUARANTEE',f15,C['coral'],'ma')
 else:
  header(d,kind+1,labels[kind]); y=320+int(4*math.sin(t*2))
  if kind==0: # coach walks to team; lesson produces understanding
   rr(d,(80,y+30,415,y+220),18,C['dark']);txt(d,(110,y+52),'AI WORKSHOP',f23,'white');
   for k in range(3):rr(d,(115+k*80,y+110,165+k*80,y+120),5,[C['yellow'],C['green'],C['coral']][k])
   person(d,95+130*a,y+260,.8,C['coral']);person(d,350,y+260,.75,C['teal']);person(d,420,y+260,.75,C['blue']);
   if finish>.4:spark(d,385,y+225,18)
  elif kind==1: # idea becomes post delivered to phone
   d.ellipse((85,y+110,190,y+215),fill=C['yellow']);txt(d,(137,y+141),'IDEA',f23,C['dark'],'ma');phone(d,305,y+30,160,270);arrow(d,192,y+165,300,y+165,a)
   for k in range(3):
    yy=y+95+k*50-int((1-finish)*60);rr(d,(322,yy,447,yy+38),9,[C['pink'],C['mint'],C['blue']][k]);rr(d,(333,yy+10,410,yy+15),3,'white')
  elif kind==2: # page moves into search results
   sheet(d,55+95*a,y+120,125,165);arrow(d,210,y+200,290,y+200,a);rr(d,(293,y+76,475,y+275),15,C['light']);rr(d,(310,y+92,455,y+123),13,C['mint']);d.ellipse((318,y+99,330,y+111),outline=C['ink'],width=2);line(d,[(328,y+109),(334,y+115)],C['ink'],2)
   for k in range(3):rr(d,(310,y+145+k*38,455,y+165+k*38),6,C['green'] if k==0 and finish>.5 else '#e7e8d9')
  elif kind==3: # ad variants tested, comparison not fabricated numbers
   for k in range(2):
    x=52+k*155+int((k-.5)*20*(1-a));rr(d,(x,y+60,x+137,y+245),15,C['light']);rr(d,(x+12,y+76,x+125,y+168),10,[C['pink'],C['green']][k]);txt(d,(x+68,y+185),['AD A','AD B'][k],f19,C['ink'],'ma')
   rr(d,(370,y+80,475,y+245),15,C['dark']);txt(d,(422,y+100),'TEST',f19,'white','ma')
   for k in range(2):rr(d,(390+k*28,y+208-int((45+k*40)*finish),407+k*28,y+208),6,[C['yellow'],C['coral']][k])
  elif kind==4: # form → gear → task checked
   sheet(d,47,y+100,120,165);d.ellipse((222,y+140,310,y+228),fill=C['yellow']);
   for k in range(8):
    ang=t*3+k*math.tau/8;xx=266+49*math.cos(ang);yy=y+184+49*math.sin(ang);rr(d,(xx-7,yy-7,xx+7,yy+7),3,C['yellow'])
   d.ellipse((250,y+168,282,y+200),fill=C['paper']);sheet(d,370,y+100,120,165);arrow(d,170,y+185,220,y+185,a);arrow(d,313,y+185,363,y+185,finish)
   if finish>.5:check(d,431,y+230)
  elif kind==5: # incoming customer question → response
   bubble(d,45,y+50,245,105,C['light']);txt(d,(70,y+78),'QUESTION?',f23);person(d,420,y+45,.7,C['blue']);arrow(d,115,y+200,390,y+200,a)
   if finish>0:
    bubble(d,207,y+245-int(25*(1-finish)),270,105,C['mint']);txt(d,(232,y+275),'HELPFUL REPLY',f19)
  elif kind==6: # routine delivery: calendar → recurring report
   rr(d,(58,y+65,205,y+235),17,C['light']);rr(d,(58,y+65,205,y+105),15,C['coral']);txt(d,(131,y+122),'MON',f23,C['ink'],'ma');check(d,130,y+190)
   arrow(d,218,y+155,305,y+155,a);sheet(d,320,y+60,155,195);txt(d,(345,y+103),'REPORT',f23);line(d,[(345,y+220),(370,y+190),(393,y+205),(435,y+155)],C['teal'],5)
  elif kind==7: # audit becomes roadmap with moving cursor
   sheet(d,48,y+80,155,220);txt(d,(74,y+110),'AUDIT',f23);arrow(d,217,y+180,305,y+180,a);rr(d,(315,y+68,480,y+245),18,C['dark']);txt(d,(397,y+88),'PLAN',f23,'white','ma');
   for k in range(3):
    d.ellipse((337,y+140+k*29,351,y+154+k*29),fill=C['yellow'] if finish>k*.22 else '#557970');rr(d,(360,y+143+k*29,449,y+149+k*29),3,'#c3e0d1')
  elif kind==8: # client requirement transformed into working app
   bubble(d,50,y+72,195,100);txt(d,(70,y+101),'CLIENT NEED',f19);arrow(d,212,y+225,300,y+225,a);phone(d,310,y+40,145,260);rr(d,(329,y+115,435,y+150),8,C['mint']);rr(d,(329,y+162,435,y+195),8,C['pink']);
   if finish>.4:check(d,437,y+276,20)
  elif kind==9: # video reaches people; sponsor label appears, not income
   phone(d,60,y+70,150,250);d.polygon([(115,y+130),(115,y+205),(175,y+168)],fill=C['coral']);arrow(d,225,y+190,310,y+190,a)
   for k in range(3):person(d,310+k*70,y+150,.55,[C['teal'],C['coral'],C['blue']][k])
   if finish>.35:rr(d,(300,y+265,480,y+305),15,C['yellow']);txt(d,(390,y+274),'SPONSOR',f15,C['ink'],'ma')
  elif kind==10: # PDF is prepared then added to digital storefront
   sheet(d,53+85*a,y+75,145,205);txt(d,(125+85*a,y+132),'PDF',f39,C['coral'],'ma');arrow(d,215,y+185,320,y+185,a);rr(d,(335,y+100,480,y+265),15,C['light']);rr(d,(348,y+116,466,y+168),10,C['green']);txt(d,(408,y+198),'LISTED',f19,C['ink'],'ma')
  elif kind==11: # newsletter or community: message delivered to people
   rr(d,(52,y+80,235,y+210),15,C['light']);line(d,[(52,y+90),(143,y+153),(235,y+90)],C['coral'],5);arrow(d,245,y+150,325,y+150,a)
   for k in range(3):person(d,325+k*65,y+140,.52,[C['teal'],C['coral'],C['blue']][k]);
   if finish>.4:bubble(d,318,y+230,145,55,C['mint']);txt(d,(340,y+247),'COMMUNITY',f12)
  elif kind==12: # white label application -> brand, no sales promise
   phone(d,60,y+55,150,260);txt(d,(135,y+135),'APP',f29,C['ink'],'ma');arrow(d,220,y+180,318,y+180,a);phone(d,330,y+55,150,260);rr(d,(345,y+93,464,y+136),9,C['coral']);txt(d,(405,y+105),'YOUR BRAND',f12,'white','ma');
   if finish>.5:check(d,463,y+300,18)
  elif kind==13: # prototype becomes launched app
   rr(d,(55,y+85,210,y+250),18,C['light']);rr(d,(72,y+103,193,y+128),7,C['line']);rr(d,(72,y+142,123,y+215),7,C['line']);rr(d,(133,y+142,193,y+215),7,C['line']);arrow(d,222,y+175,310,y+175,a);phone(d,325,y+40,150,265);rr(d,(342,y+105,458,y+145),8,C['mint']);rr(d,(342,y+155,458,y+225),8,C['pink']);
   if finish>.4:spark(d,435,y+45,20)
  txt(d,(270,750),'EXAMPLE WORKFLOW  •  NO GUARANTEED RESULTS',f12,C['teal'],'ma')
 # Gentle camera movement supports, but does not replace, the animated objects above.
 scale=1.045+.025*(.5+.5*math.sin(t*1.2));ww=int(W*scale);hh=int(H*scale);zoom=im.resize((ww,hh),Image.Resampling.BILINEAR);xx=int((ww-W)*(.5+.4*math.sin(t)));yy=int((hh-H)*(.5+.4*math.cos(t)));xx=max(0,min(ww-W,xx));yy=max(0,min(hh-H,yy));im=zoom.crop((xx,yy,xx+W,yy+H));d=ImageDraw.Draw(im)
 if transition and z and u<.13:im=Image.blend(frame(max(1/FPS,bt['start']-.04),False),im,e(u/.13));d=ImageDraw.Draw(im)
 sc=S[bt['scene']];words=sc['words'];wi=next((i for i,w in enumerate(words) if w[1]<=t<w[2]+.02),None)
 if wi is not None:
  st=wi//3*3;ws=[x[0].upper() for x in words[st:st+3]];ft=f23;sz=[d.textlength(x,font=ft) for x in ws];gap=9;total=sum(sz)+gap*(len(sz)-1)
  if total>445:ft=f19;sz=[d.textlength(x,font=ft) for x in ws];total=sum(sz)+gap*(len(sz)-1)
  x=(W-total)/2;rr(d,(x-13,836,x+total+13,886),12,C['dark'])
  for k,v in enumerate(ws):txt(d,(x,847),v,ft,'#ffcd80' if st+k==wi else 'white');x+=sz[k]+gap
 return im
out=D/'ai-business-ideas-v2.mp4';assert not out.exists();body=S[-1]['start']
with tempfile.TemporaryDirectory(prefix='ai-business-actions-') as td:
 td=Path(td);bv=td/'body.mp4';cta=td/'cta.wav';tim=td/'cta.json';paced=td/'paced.wav';subprocess.run([FF,'-y','-loglevel','error','-i',str(D/'voice-handoff/voice.wav'),'-af',f'atempo={RATE}','-acodec','pcm_s16le',str(paced)],check=True);last=S[-1];j=dict(J);j['duration']=J['duration']-body;j['scenes']=[{'start':0,'end':last['end']-body,'words':[[w[0],w[1]-body,w[2]-body] for w in last['words']]}];tim.write_text(json.dumps(j));subprocess.run([FF,'-y','-loglevel','error','-ss',str(body),'-i',str(paced),'-acodec','pcm_s16le',str(cta)],check=True)
 cmd=[FF,'-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','540x960','-r',str(FPS),'-i','-','-i',str(paced),'-t',str(body),'-vf','scale=1080:1920:flags=lanczos','-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k',str(bv)]
 pr=subprocess.Popen(cmd,stdin=subprocess.PIPE)
 for n in range(math.ceil(body*FPS)):pr.stdin.write(frame(n/FPS).tobytes())
 pr.stdin.close();assert pr.wait()==0
 subprocess.run([sys.executable,str(R/'tools/append_house_outro.py'),'--input',str(bv),'--output',str(out),'--voice',str(cta),'--timings',str(tim),'--keyword','IDEAS','--body-seconds',str(body),'--prompt','for the list'],cwd=R,check=True)
 (D/'timing-manifest.json').write_text(json.dumps({'scenes':S,'outro_start':body,'beats':beats},indent=2)+'\n')
print('Finished render. Technical and full audiovisual review required; not scheduled.',flush=True)
