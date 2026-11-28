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
# Photographic assets are AI-generated illustrations, never presented as real clients.
from PIL import ImageOps,ImageFilter
photos={n:ImageOps.fit(Image.open(R/'captures/ai-business-realistic'/f'{n}.png').convert('RGB'),(600,1066),method=Image.Resampling.LANCZOS) for n in ('workshop','workflow','build','creator')}
def bg(t,kind):
 name='workshop' if kind in (0,6,7,14) else ('workflow' if kind in (1,2,3,4,5,-1) else ('build' if kind in (8,12,13) else 'creator'))
 src=photos[name];x=int(30+20*math.sin(t*.48));y=int(50+25*math.cos(t*.36));im=src.crop((x,y,x+540,y+960));shade=Image.new('RGB',(W,H),'#102b2a');return Image.blend(im,shade,.38)
def header(d,no,title):
 rr(d,(25,48,515,191),16,'#163b37');txt(d,(42,63),'HYPELESS  /  SOLO AI BUSINESS',f15,'#aad9c3');txt(d,(42,91),title,f39,'#fffaf2');rr(d,(42,150,135,157),3,'#f4ac84');
 if no is not None:rr(d,(439,61,497,105),13,'#e6735e');txt(d,(468,69),f'{no:02}',f29,'white','ma')
 txt(d,(42,169),'ILLUSTRATED EXAMPLE • AI-GENERATED VISUALS',f12,'#b2cfc1')
def box(d,x,y,w,h,fill='#fffaf4'):
 rr(d,(x+7,y+9,x+w+7,y+h+9),16,'#263b37');rr(d,(x,y,x+w,y+h),16,fill)
def bar(d,x,y,w,col='#dae5dc'):
 rr(d,(x,y,x+w,y+6),3,col)
def mini_profile(d,x,y,c='#e7755e'):
 d.ellipse((x,y,x+22,y+22),fill=c);rr(d,(x-4,y+25,x+26,y+43),8,c)
def action_card(d,kind,p):
 a=e(p/.52);b=e((p-.35)/.55);top=247;bottom=504
 data=[
 ('TEAM TRAINING','New team needs AI skills','SESSION PLAN','Live workshop + practice'),
 ('CONTENT SERVICE','Client notes and ideas','SOCIAL POST','A polished post draft'),
 ('SEARCH VISIBILITY','A business page needs clarity','SEARCH PREVIEW','A clearer page summary'),
 ('AD CREATIVE TEST','Two creative directions','TEST SETUP','Compare A and B'),
 ('AUTOMATE WORKFLOW','A new enquiry arrives','NEXT ACTION','Route it to the right inbox'),
 ('CUSTOMER SUPPORT','A customer asks a question','DRAFT REPLY','A helpful response to review'),
 ('RECURRING SERVICE','Deliver a weekly update','WEEKLY REPORT','A repeatable client deliverable'),
 ('AI ADOPTION ADVICE','Review team workflows','ACTION ROADMAP','Prioritized next steps'),
 ('CLIENT SOFTWARE','A client needs a booking tool','CLIENT APP','A usable booking prototype'),
 ('BUILD AN AUDIENCE','Publish a useful tutorial','MEDIA KIT','An audience for sponsors to assess'),
 ('DIGITAL PRODUCT','Create a practical guide','PRODUCT PAGE','A digital resource for sale'),
 ('COMMUNITY / NEWSLETTER','Write a useful update','SUBSCRIBER SPACE','A place to discuss or read'),
 ('WHITE-LABEL SOFTWARE','Use licensed reseller software','BRANDED APP','Your own brand on a product'),
 ('BUILD YOUR OWN APP','Turn a problem into a prototype','WORKING APP','Test it with real users')]
 left_title,left_sub,right_title,right_sub=data[kind];box(d,40,top,460,193);txt(d,(57,top+14),'01  /  THE WORK',f12,'#77948b');txt(d,(57,top+36),left_title,f23,C['ink']);
 # A moving cursor and concrete input demonstrate the work instead of a stationary icon.
 rr(d,(57,top+74,482,top+146),10,'#eef3ea');txt(d,(70,top+91),left_sub,f15,C['ink']);
 typing=max(1,int(320*a));rr(d,(70,top+124,70+typing,top+128),2,C['teal']);cursor(d,450-25*a,top+125)
 # Action travels from work to output; the second window slides into place.
 barx=262;d.line((barx,top+200,barx,top+200+int(38*b)),fill='#f3c16b',width=5)
 if b>.5:d.polygon([(252,top+225),(272,top+225),(262,top+238)],fill='#f3c16b')
 yy=bottom+int((1-b)*35);box(d,40,yy,460,222);txt(d,(57,yy+12),'02  /  THE RESULT',f12,'#77948b');txt(d,(57,yy+32),right_title,f23,C['ink']);txt(d,(57,yy+62),right_sub,f15,'#537268')
 if kind in (0,7):
  for k,label in enumerate((['Intro & goals','Guided exercise','Team Q&A'] if kind==0 else ['Find bottlenecks','Choose pilot','Review results'])):
   z=e((p-.38-k*.1)/.34);rr(d,(65,yy+97+k*31,65+int(18*z),yy+115+k*31),5,['#e4745d','#77bda2','#e2b44e'][k]);txt(d,(96,yy+98+k*31),label,f15,C['ink'])
 elif kind in (1,3):
  for k in range(2):
   x=62+k*199;rr(d,(x,yy+96,x+185,yy+185),10,['#e9b6a1','#a2d0b2'][k]);
   if kind==1:
    txt(d,(x+12,yy+106),'TIPS FOR YOUR DAY' if k==0 else '3-MINUTE RESET',f12,'#24483e');bar(d,x+12,yy+135,120,'#f9f4e9');bar(d,x+12,yy+151,85,'#f9f4e9')
   else:
    txt(d,(x+12,yy+110),'CREATIVE A' if k==0 else 'CREATIVE B',f15,'#24483e');txt(d,(x+12,yy+143),'DRAFT',f12,'#44655a')
 elif kind==2:
  rr(d,(63,yy+99,475,yy+191),10,'#f0f4ec');txt(d,(75,yy+110),'YOUR SERVICE  |  YOUR CITY',f15,'#27575a');bar(d,75,yy+145,335,'#b6c6ba');bar(d,75,yy+160,255,'#c4d1c5')
 elif kind in (4,5,11):
  rr(d,(62,yy+100,475,yy+190),10,'#e9f2ea');txt(d,(75,yy+112),['NEW ENQUIRY → ROUTED','Hello! How can we help?','New post → members'][[4,5,11].index(kind)],f15,'#26483f');bar(d,75,yy+148,int(300*b),'#88bda5');
  if b>.75:check(d,449,yy+168,16)
 elif kind==6:
  for k in range(5):
   bh=int((20+10*k)*b);rr(d,(83+k*50,yy+179-bh,111+k*50,yy+179),5,['#84bda5','#e2b050','#e78268','#80b5ba','#529783'][k])
  txt(d,(348,yy+116),'WEEKLY',f15,C['ink']);txt(d,(348,yy+140),'REPORT',f15,C['ink'])
 elif kind in (8,12,13):
  rr(d,(83,yy+95,188,yy+202),10,'#254d49');rr(d,(91,yy+102,180,yy+194),7,'#fdf9f2');rr(d,(99,yy+115,172,yy+132),5,C['coral']);rr(d,(99,yy+142,172,yy+154),4,C['mint']);rr(d,(99,yy+163,150,yy+174),4,C['line']);txt(d,(215,yy+115),['BOOKING','YOUR BRAND','PROTOTYPE'][[8,12,13].index(kind)],f19,C['ink']);txt(d,(215,yy+149),'DESIGN → TEST',f15,'#78958b')
 elif kind==9:
  rr(d,(67,yy+104,203,yy+184),10,'#e9b6a1');d.polygon([(117,yy+121),(117,yy+164),(155,yy+143)],fill='white');
  for k in range(3):mini_profile(d,245+k*58,yy+119,['#e87961','#7fbda0','#6ca6ad'][k]);txt(d,(414,yy+151),'KIT',f15,C['ink'])
 elif kind==10:
  rr(d,(75,yy+98,160,yy+194),8,'#e6aa84');txt(d,(93,yy+113),'GUIDE',f15,C['ink']);bar(d,93,yy+148,47,'#fffaf1');rr(d,(183,yy+99,468,yy+193),10,'#f0f4ec');txt(d,(202,yy+110),'YOUR DIGITAL GUIDE',f15,C['ink']);rr(d,(204,yy+150,365,yy+180),8,C['teal']);txt(d,(284,yy+158),'PRODUCT LISTING',f12,'white','ma')
 txt(d,(270,768),'SIMULATED WORKFLOW • NO EARNINGS GUARANTEE',f12,'#f5f6ea','ma')

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
 z=max((i for i,x in enumerate(beats) if x['start']<=t),default=0);bt=beats[z];kind=bt['kind'];u=max(0,t-bt['start']);du=max(.12,bt['end']-bt['start']);p=clamp(u/du);a=e(p/.72);finish=e((p-.45)/.45);im=bg(t,kind);d=ImageDraw.Draw(im)
 if kind==-1:
  header(d,None,'PICK ONE IDEA')
  box(d,65,270,410,345);txt(d,(270,285),'14',ImageFont.truetype(str(fonts/'Anton.ttf'),165),C['coral'],'ma');txt(d,(270,470),'SOLO BUSINESS IDEAS',f29,C['ink'],'ma');txt(d,(270,540),'PICK ONE PROBLEM',f19,C['teal'],'ma')
 elif kind==14:
  header(d,None,'START WITH A PROBLEM');box(d,50,270,440,365);txt(d,(75,299),'CUSTOMER INTERVIEW',f19,C['ink']);rr(d,(75,350,465,410),10,'#e8f1e6');txt(d,(91,370),'What slows your team down?',f15,C['ink']);rr(d,(75,441,465,501),10,'#e8f1e6');txt(d,(91,461),'What would a solution be worth?',f15,C['ink']);rr(d,(75,537,75+int(390*a),575),10,C['teal']);txt(d,(270,546),'TEST THE OFFER',f15,'white','ma');txt(d,(270,694),'NO EARNINGS GUARANTEE',f15,'white','ma')
 else:
  header(d,kind+1,labels[kind]);action_card(d,kind,p)
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
out=D/'ai-business-ideas-realistic.mp4';assert not out.exists();body=S[-1]['start']
with tempfile.TemporaryDirectory(prefix='ai-business-actions-') as td:
 td=Path(td);bv=td/'body.mp4';cta=td/'cta.wav';tim=td/'cta.json';paced=td/'paced.wav';subprocess.run([FF,'-y','-loglevel','error','-i',str(D/'voice-handoff/voice.wav'),'-af',f'atempo={RATE}','-acodec','pcm_s16le',str(paced)],check=True);last=S[-1];j=dict(J);j['duration']=J['duration']-body;j['scenes']=[{'start':0,'end':last['end']-body,'words':[[w[0],w[1]-body,w[2]-body] for w in last['words']]}];tim.write_text(json.dumps(j));subprocess.run([FF,'-y','-loglevel','error','-ss',str(body),'-i',str(paced),'-acodec','pcm_s16le',str(cta)],check=True)
 cmd=[FF,'-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','540x960','-r',str(FPS),'-i','-','-i',str(paced),'-t',str(body),'-vf','scale=1080:1920:flags=lanczos','-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k',str(bv)]
 pr=subprocess.Popen(cmd,stdin=subprocess.PIPE)
 for n in range(math.ceil(body*FPS)):pr.stdin.write(frame(n/FPS).tobytes())
 pr.stdin.close();assert pr.wait()==0
 subprocess.run([sys.executable,str(R/'tools/append_house_outro.py'),'--input',str(bv),'--output',str(out),'--voice',str(cta),'--timings',str(tim),'--keyword','IDEAS','--body-seconds',str(body),'--prompt','for the list'],cwd=R,check=True)
 (D/'timing-manifest.json').write_text(json.dumps({'scenes':S,'outro_start':body,'beats':beats},indent=2)+'\n')
print('Finished render. Technical and full audiovisual review required; not scheduled.',flush=True)
