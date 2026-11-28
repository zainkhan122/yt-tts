"""Interactive-agent-directed, review-only zipper illustration.
Runs strict alignment in this process before the semantic scheduler and render.
It is a topic-specific illustration, not an autonomous general visual planner.
"""
import json,math,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from graphics.production.alignment import run_alignment,FasterWhisperBackend,require_verified
from graphics.production.scheduler import schedule
from graphics.production.layer_renderer import _ease
from graphics.media import ffmpeg_exe
D=Path(__file__).resolve().parent
S=2;W,H=1080,1920;FPS=24
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
F={n:ImageFont.truetype(bold if b else font,n*S) for n,b in [(12,1),(13,1),(14,0),(15,1),(16,0),(18,1),(20,1),(24,1),(28,1),(34,1),(43,1)]}
def ft(n,b=1): return F[n] if n in F else ImageFont.truetype(bold if b else font,n*S)
def xy(v):return tuple(round(x*S) for x in v)
def rect(d,box,fill,rad=0,outline=None,width=1):d.rounded_rectangle(xy(box),radius=round(rad*S),fill=fill,outline=outline,width=width*S)
def line(d,pts,fill,width=1,joint='curve'):d.line([xy(p) for p in pts],fill=fill,width=width*S,joint=joint)
def text(d,pos,s,size,fill,anchor=None):d.text(xy(pos),s,font=ft(size),fill=fill,anchor=anchor,stroke_width=0)
def ease(a,b,t):return _ease((t-a)/max(.00001,b-a),'smooth')
def item(id,desc):return {'id':id,'kind':'procedural graphic','description':desc,'reuse_of':None}
def ev(id,trigger,asset,action):return {'id':id,'trigger_phrase':trigger,'occurrence':1,'action':action,'target':asset,'animation_type':'position','duration':.04,'camera':'hold','asset_id':asset,'transition':'cut'}
def beat(id,a,z,meaning,assets,events,treat):return {'id':id,'word_start':a,'word_end':z,'meaning':meaning,'visual_objective':meaning,'treatment':treat,'scene_description':meaning,'subject':'zipper mechanism','objects':['slider','teeth'],'composition':'large central illustrated mechanism with a high contrast editorial heading','camera':'hold','transition':'cut','assets':assets,'events':events}
def plan():
 return {'beats':[
 beat('object',0,30,'A slider moves upward and guides two rows of teeth into a locked chain',[item('zip','A procedural illustration of the zipper teeth and slider')],[ev('focus_slider','slider is a tiny mechanical guide','zip','Highlight the slider as its role is introduced'),ev('move_up','pull it upward','zip','Move the slider upward and progressively join the teeth'),ev('lock','lock into a continuous chain','zip','Emphasize the connected zipper teeth')],'product_visualization'),
 beat('channel',30,57,'Two tracks merge into one inside a Y shaped channel',[item('channel_art','A simplified cutaway of the slider channel and tracks')],[ev('channel_reveal','y shaped channel','channel_art','Reveal the Y shaped internal guide'),ev('enter','enter at the bottom','channel_art','Animate two track paths into the channel'),ev('merge','merge in the middle','channel_art','Join both track paths in the middle'),ev('exit','leave as one connected line','channel_art','Trace the joined path out of the channel')],'process_animation'),
 beat('reverse',57,81,'Pulling down separates the teeth and shows a reversible connection',[item('reverse_art','A procedural illustration of the zipper separating and kinetic phrases')],[ev('down','pull the slider back down','reverse_art','Move the slider down and separate the rows'),ev('wedge','wedge separates those teeth','reverse_art','Highlight the wedge separating the teeth'),ev('separates','separates those teeth','reverse_art','Emphasize the separated teeth'),ev('glue','no glue','reverse_art','Reveal the words no glue'),ev('magnets','no magnets','reverse_art','Reveal the words no magnets'),ev('shape','shape','reverse_art','Emphasize the word shape'),ev('pressure','pressure','reverse_art','Emphasize the word pressure'),ev('connection','reversible connection','reverse_art','Emphasize the reversible connection')],'kinetic_typography')]}

def makebg():
 im=Image.new('RGB',(W,H)); pix=im.load()
 # Scanline gradient with softly lit radial pool, rendered once.
 d=ImageDraw.Draw(im)
 for y in range(H):
  v=y/H; col=(round(13+8*v),round(25+13*v),round(33+15*v));d.line((0,y,W,y),fill=col)
 return im
BG=makebg()
def base(kicker,title,subtitle):
 im=BG.copy();d=ImageDraw.Draw(im)
 rect(d,(27,43,513,917),None,23,'#526667',1)
 text(d,(48,75),kicker,12,'#e0a670'); text(d,(48,112),title,34,'#f6efe4')
 text(d,(48,165),subtitle,14,'#aab9b9');line(d,[(48,199),(492,199)],'#44595d',1)
 text(d,(48,880),'ILLUSTRATED MECHANICS',12,'#819797');text(d,(492,880),'THE ZIPPER',12,'#819797',anchor='ra')
 return im,d

def pill(d,x,y,w,title,color='#dcb282'):
 rect(d,(x,y,x+w,y+30),'#263d42',15,'#50676a',1);text(d,(x+13,y+8),title,12,color)

def zipper(d,slider,accent=False,focus=False,wedge=False):
 # Track spreads ahead of slider; each tooth's position is an independent function
 # of the slider crossing it, not a zoom or an image substitution.
 ys=list(range(275,706,19))
 def gap(y): return 2+52*_ease((slider-y+13)/39,'smooth')
 left=[(270-gap(y)-20,y) for y in ys]; right=[(270+gap(y)+20,y) for y in ys]
 line(d,left,'#425d60',62);line(d,right,'#425d60',62)
 line(d,left,'#77908c',45);line(d,right,'#77908c',45)
 line(d,[(x-16,y) for x,y in left],'#a3afa3',2);line(d,[(x+16,y) for x,y in right],'#a3afa3',2)
 for y in ys:
  g=gap(y)
  for side in (-1,1):
   cx=270+side*(g+7)
   # Teeth overlap by alternating half pitches once assembled.
   cy=y+(5 if side==1 else 0)
   rect(d,(cx-12,cy-7,cx+12,cy+7),'#504f49',5)
   rect(d,(cx-11,cy-8,cx+10,cy+5),'#c6bda9',5)
   line(d,[(cx-7,cy-5),(cx+6,cy-5)],'#eee1c7',1)
 # Solid, dimensional slider body and pull tab.
 sy=slider
 if focus:rect(d,(214,sy-49,326,sy+67),None,25,'#edbd85',3)
 rect(d,(228,sy-36,315,sy+62),'#182a2c',18)
 d.polygon([xy((232,sy-37)),xy((308,sy-37)),xy((319,sy+28)),xy((302,sy+53)),xy((238,sy+53)),xy((221,sy+28))],fill='#a48b6b',outline='#ebd5b2',width=3*S)
 line(d,[(237,sy-25),(300,sy-25)],'#f1e2c6',3)
 rect(d,(247,sy-3,293,sy+19),'#4d524f',10, '#e8d1aa',2)
 rect(d,(255,sy+7,285,sy+95),'#988362',12,'#edd6ac',2)
 rect(d,(264,sy+68,276,sy+82),'#344449',5)
 if wedge:
  d.polygon([xy((270,sy-28)),xy((259,sy-5)),xy((281,sy-5))],fill='#f5c381')
  line(d,[(336,sy-19),(300,sy-19)],'#edbd85',2);text(d,(343,sy-27),'WEDGE',12,'#f1c393')
 if accent:
  line(d,[(359,sy+15),(337,sy+15)],'#efc58e',2);text(d,(365,sy+7),'SLIDER',12,'#e9c38e')

def draw_object(t,T):
 im,d=base('01  /  HOW IT WORKS','THE ZIPPER','A small guide joins two rows of teeth')
 start=T['move_up'];finish=T['lock']+.30
 slider=668-326*ease(start,finish,t)
 zipper(d,slider,t>=T['focus_slider'],focus=T['focus_slider']<=t<T['move_up'])
 if t>=T['move_up']:
  p=ease(start,start+.5,t);line(d,[(431,655),(431,655-130*p)],'#e8b783',4)
  if p>.35:d.polygon([xy((421,655-130*p+14)),xy((431,655-130*p)),xy((441,655-130*p+14))],fill='#e8b783')
 if t>=T['lock']:pill(d,163,782,214,'TEETH INTERLOCK')
 else:pill(d,171,782,199,'TWO ROWS  /  ONE SLIDER')
 return im

def partial(points,p):
 lengths=[math.dist(a,b) for a,b in zip(points,points[1:])];left=sum(lengths)*max(0,min(1,p));out=[points[0]]
 for a,b,L in zip(points,points[1:],lengths):
  if left>=L:out.append(b);left-=L
  else:
   q=left/L if L else 0;out.append((a[0]+(b[0]-a[0])*q,a[1]+(b[1]-a[1])*q));break
 return out

def draw_channel(t,T):
 im,d=base('02  /  INSIDE THE SLIDER','THE Y CHANNEL','Simplified cutaway · not to scale')
 # Dim silhouette gives anatomical continuity; colored lines explain motion.
 d.polygon([xy(p) for p in [(170,270),(370,270),(391,663),(332,729),(208,729),(149,663)]],fill='#384f50',outline='#b9c8b7',width=3*S)
 rect(d,(193,293,347,690),'#20383c',29,'#748e87',2)
 A=[(165,678),(205,590),(270,480)];B=[(375,678),(335,590),(270,480)];C=[(270,480),(270,320)]
 for pts in (A,B,C):line(d,pts,'#738c83' if t>=T['channel_reveal'] else '#455f60',12)
 t0=T['enter'];tm=T['merge'];te=T['exit']
 p=ease(t0,tm+.2,t)
 for pts,col in ((A,'#efb17f'),(B,'#7dc5ba')):
  seg=partial(pts,p)
  if len(seg)>1:line(d,seg,col,7)
 p2=ease(te,te+.65,t)
 seg=partial(C,p2)
 if len(seg)>1:line(d,seg,'#ece1b5',7)
 if t>=tm:rect(d,(262,472,278,488),'#f7e5bb',8)
 pill(d,125,759,130,'TWO IN', '#efb17f');pill(d,282,759,132,'ONE OUT','#dfe8cf')
 return im

def pop_text(im,x,y,label,size,color,start,t):
 if t<start:return
 p=ease(start,start+.32,t)
 f=ft(size); box=f.getbbox(label); layer=Image.new('RGBA',(box[2]+12*S, (box[3]-box[1])+12*S))
 ld=ImageDraw.Draw(layer);ld.text((4*S,3*S-box[1]),label,font=f,fill=color)
 alpha=layer.getchannel('A').point(lambda value:round(value*p));layer.putalpha(alpha)
 im.paste(layer,xy((x-18*(1-p)-4,y-3)),layer)

def draw_reverse(t,T):
 im,d=base('03  /  THE REVERSE','PULL TO RELEASE','The guide separates the same teeth')
 slider=342+326*ease(T['down'],T['separates']+.55,t)
 zipper(d,slider,False,wedge=T['wedge']<=t<T['glue'])
 if t>=T['glue']:
  # Replace the detailed view with a statement card; text emphasis follows words.
  rect(d,(55,280,485,741),'#142b31',30,'#6a807b',2)
  pop_text(im,78,319,'NO GLUE',28,'#aebfba',T['glue'],t)
  pop_text(im,78,370,'NO MAGNETS',28,'#aebfba',T['magnets'],t)
  pop_text(im,78,458,'SHAPE',43,'#f3c190',T['shape'],t)
  pop_text(im,78,521,'PRESSURE',43,'#94d0c0',T['pressure'],t)
  if t>=T['connection']:
   line(d,[(78,604),(450,604)],'#587a77',2);pop_text(im,78,628,'REVERSIBLE',24,'#f4ecdc',T['connection'],t);pop_text(im,78,662,'CONNECTION',24,'#f4ecdc',T['connection']+.15,t)
 else:pill(d,178,782,185,'TEETH SEPARATE' if t>=T['separates'] else 'RELEASE THE TEETH')
 return im

def render():
 audio=D/'voice.wav';transcript=' '.join(json.loads((D/'narration.json').read_text()))
 print('Executing strict small.en alignment...',flush=True)
 alignment=run_alignment(audio,transcript,FasterWhisperBackend('small.en'));report=require_verified(alignment,audio,transcript)
 (D/'alignment-executed.json').write_text(json.dumps(report,indent=2))
 direction=plan()
 first=schedule(audio,transcript,alignment,direction)
 T={e['id']:e['audio_time'] for b in first['beats'] for e in b['events']}
 durations={'focus_slider':T['move_up']-T['focus_slider'],'move_up':T['lock']+.30-T['move_up'],
  'enter':T['merge']+.20-T['enter'],'exit':.65,'down':T['separates']+.55-T['down'],
  'wedge':T['glue']-T['wedge'],'glue':.32,'magnets':.32,'shape':.32,'pressure':.32,'connection':.47}
 for b in direction['beats']:
  for e in b['events']:e['duration']=durations.get(e['id'],.04)
 scheduled=schedule(audio,transcript,alignment,direction);(D/'scheduled.json').write_text(json.dumps(scheduled,indent=2))
 T={e['id']:e['audio_time'] for b in scheduled['beats'] for e in b['events']};dur=report['audio_duration']
 (D/'visual-events.json').write_text(json.dumps({'note':'Interactive agent-directed subject-specific procedural illustration. Events are scheduler word starts; animation end times derive from adjacent semantic events.','events':T},indent=2))
 print('Strict alignment passed, word-triggered events:',T,flush=True)
 ff=ffmpeg_exe();vid=D/'visual-silent.mp4';out=D/'zipper-review.mp4';count=round(dur*FPS)
 proc=subprocess.Popen([ff,'-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-threads','2','-preset','veryfast','-crf','19','-pix_fmt','yuv420p',str(vid)],stdin=subprocess.PIPE,stderr=subprocess.PIPE)
 a=scheduled['beats'][1]['start'];b=scheduled['beats'][2]['start']
 try:
  for i in range(count):
   t=i/FPS
   if abs(t-a)<.22:
    f=ease(a-.22,a+.22,t);im=Image.blend(draw_object(t,T),draw_channel(t,T),f)
   elif abs(t-b)<.22:
    f=ease(b-.22,b+.22,t);im=Image.blend(draw_channel(t,T),draw_reverse(t,T),f)
   elif t<a:im=draw_object(t,T)
   elif t<b:im=draw_channel(t,T)
   else:im=draw_reverse(t,T)
   proc.stdin.write(im.tobytes())
   if i%120==0:print('Frame',i,'/',count,flush=True)
  proc.stdin.close();err=proc.stderr.read();rc=proc.wait()
  if rc:raise RuntimeError(err.decode(errors='replace'))
 except BaseException:
  proc.kill();proc.wait();raise
 subprocess.run([ff,'-y','-v','error','-i',str(vid),'-i',str(audio),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-t',str(dur),'-movflags','+faststart',str(out)],check=True)
 print('Rendered',out,'frames',count,'duration',dur,flush=True)
if __name__=='__main__':render()
