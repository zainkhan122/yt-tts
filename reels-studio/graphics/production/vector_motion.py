"""Topic-neutral native vector motion for word-aligned review renders.

A visual director supplies declarative shapes and cue phrases; no subject-specific
artwork or semantic inference is embedded here. Timing is scheduled by the
existing strict alignment and semantic scheduler. This does not assess quality.
"""
from __future__ import annotations
import math,subprocess,json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageChops
from .alignment import tokens,require_verified
from .scheduler import schedule
from .layer_renderer import _ease
from graphics.media import ffmpeg_exe

S=2;W,H=1080,1920
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
class MotionError(ValueError):pass

def xy(p):return tuple(round(x*S) for x in p)
def font(size,bold=True):return ImageFont.truetype(BOLD if bold else FONT,round(size*S))
def path_part(points,p):
    lengths=[math.dist(a,b) for a,b in zip(points,points[1:])];remaining=sum(lengths)*max(0,min(1,p));out=[points[0]]
    for a,b,length in zip(points,points[1:],lengths):
        if length==0:continue
        if remaining>=length:out.append(b);remaining-=length
        else:
            q=remaining/length;out.append((a[0]+(b[0]-a[0])*q,a[1]+(b[1]-a[1])*q));break
    return out

def _phrase(words,phrase,a,z,after=None):
    t=tokens(phrase);matches=[i for i in range(a,z-len(t)+1) if [w['text'] for w in words[i:i+len(t)]]==t and (after is None or i>=after)]
    if len(matches)!=1:raise MotionError(f'Cue must match exactly once in beat: {phrase!r}, found {len(matches)}')
    return matches[0],matches[0]+len(t)-1

def compile_story(story,audio,transcript,alignment):
    """Compile a director's vector scene data to the existing semantic scheduler."""
    report=require_verified(alignment,audio,transcript);words=report['words'];cursor=0;beats=[]
    if not story.get('scenes'):raise MotionError('Scenes required')
    for n,s in enumerate(story['scenes']):
        count=len(tokens(s['narration']));a,z=cursor,cursor+count;cursor=z
        if [w['text'] for w in words[a:z]]!=tokens(s['narration']):raise MotionError('Scene text differs from actual transcript')
        ids=[x['id'] for x in s['nodes']]
        if not ids or len(set(ids))!=len(ids):raise MotionError('Unique vector nodes required')
        # Readability gate for this vector format; not a substitute for human review.
        for node in s['nodes']:
            if any(sh['kind']=='text' and sh['size']<18 for sh in node['shapes']):raise MotionError('Text below 18 design pixels is rejected')
        if not s.get('events'):raise MotionError('No animated events in beat')
        if not any(e.get('property') in {'offset','rotation','reveal'} for e in s['events']):
            raise MotionError('Beat must contain independent movement or a progressive reveal; opacity/scale alone is not enough')
        events=[];assets=[]
        for i,node in enumerate(s['nodes']):assets.append({'id':f's{n}_{node["id"]}','kind':'vector','description':f'Illustrated element {node["id"]} in the current scene','reuse_of':None})
        for j,e in enumerate(s['events']):
            if e['node'] not in ids or e['property'] not in {'offset','opacity','scale','rotation','reveal'}:raise MotionError('Unknown node or animation property')
            if e['from']==e['to']:raise MotionError('No-op animation is not a meaningful event')
            values=(e['from'],e['to'])
            if e['property']=='offset':
                if any(not isinstance(v,list) or len(v)!=2 or not all(type(x) in (int,float) and math.isfinite(x) for x in v) for v in values):raise MotionError('Offset must be a finite pair')
            elif any(type(v) not in (int,float) or not math.isfinite(v) for v in values):raise MotionError('Motion values must be finite numbers')
            if e['property'] in {'opacity','reveal'} and any(not 0<=v<=1 for v in values):raise MotionError('Opacity and reveal must be in [0,1]')
            if e['property']=='scale' and any(v<=0 or v>4 for v in values):raise MotionError('Invalid scale')
            i,_=_phrase(words,e['start'],a,z);_,endword=_phrase(words,e['end'],a,z,after=i)
            start=words[i]['start'];end=words[endword]['end']
            if end<=start:raise MotionError('Nonpositive word-anchored animation')
            eid=f's{n}_e{j}';e['_id']=eid
            events.append({'id':eid,'trigger_phrase':e['start'],'occurrence':1,'action':e.get('action','Animate the specified scene element'),'target':e['node'],'animation_type':e['property'],'duration':end-start,'camera':'hold','asset_id':f's{n}_{e["node"]}','transition':'cut'})
        beats.append({'id':f's{n}','word_start':a,'word_end':z,'meaning':s['meaning'],'visual_objective':s['meaning'],'treatment':s['treatment'],'scene_description':s['meaning'],'subject':s['subject'],'objects':[x['id'] for x in s['nodes']],'composition':'Large independent objects with readable typography in a native vertical frame','camera':'hold','transition':'cut','assets':assets,'events':events})
    if cursor!=len(words):raise MotionError('Scenes must partition full narration')
    scheduled=schedule(audio,transcript,alignment,{'beats':beats})
    compiled=[]
    for scene,beat in zip(story['scenes'],scheduled['beats']):
        byid={x['id']:x for x in beat['events']};events=[]
        for e in scene['events']:
            x=byid[e['_id']];events.append({**e,'t0':x['audio_time'],'t1':x['end_time']})
        for node in scene['nodes']:
            for prop in ('offset','opacity','scale','rotation','reveal'):
                seq=sorted((e for e in events if e['node']==node['id'] and e['property']==prop),key=lambda e:e['t0'])
                if any(x['t1']>y['t0']+1e-6 for x,y in zip(seq,seq[1:])):raise MotionError('Overlapping property motions')
        compiled.append({**scene,'start_time':beat['start'],'end_time':beat['end'],'compiled_events':events})
    return report,scheduled,compiled

def interp(a,b,p):
    if isinstance(a,list):return [x+(y-x)*p for x,y in zip(a,b)]
    return a+(b-a)*p

def state(node,events,t):
    values={'offset':[0,0],'opacity':1,'scale':1,'rotation':0,'reveal':1}
    for prop in values:
        seq=sorted((e for e in events if e['node']==node['id'] and e['property']==prop),key=lambda e:e['t0'])
        if seq:
            values[prop]=seq[0]['from']
            for e in seq:
                if t<e['t0']:break
                values[prop]=interp(e['from'],e['to'],_ease((t-e['t0'])/(e['t1']-e['t0']),e.get('easing','smooth')))
    return values

def draw_shapes(node,reveal=1):
    w,h=xy(node['size']);im=Image.new('RGBA',(w,h));d=ImageDraw.Draw(im)
    for sh in node['shapes']:
        k=sh['kind'];fill=sh.get('fill');out=sh.get('outline');width=round(sh.get('width',1)*S)
        if k=='rect':d.rounded_rectangle(xy(sh['box']),radius=round(sh.get('radius',0)*S),fill=fill,outline=out,width=width)
        elif k=='ellipse':d.ellipse(xy(sh['box']),fill=fill,outline=out,width=width)
        elif k=='polygon':d.polygon([xy(x) for x in sh['points']],fill=fill,outline=out,width=width)
        elif k=='path':
            pp=path_part(sh['points'],reveal)
            if len(pp)>1 and reveal>0:
                d.line([xy(x) for x in pp],fill=fill,width=width,joint='curve')
                if sh.get('head'):
                    a,b=pp[-2],pp[-1];angle=math.atan2(b[1]-a[1],b[0]-a[0]);L=sh.get('head_size',14);ang=.55
                    p1=(b[0]-L*math.cos(angle-ang),b[1]-L*math.sin(angle-ang));p2=(b[0]-L*math.cos(angle+ang),b[1]-L*math.sin(angle+ang))
                    d.polygon([xy(b),xy(p1),xy(p2)],fill=fill)
        elif k=='image':
            source=Path(sh['path'])
            if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest()!=sh['sha256']:raise MotionError('Image asset missing or changed')
            with Image.open(source) as img:
                img=img.convert('RGBA').resize(xy(sh['size']),Image.Resampling.LANCZOS)
                im.alpha_composite(img,xy(sh.get('at',[0,0])))
        elif k=='text':
            f=font(sh['size'],sh.get('bold',True));box=d.textbbox(xy(sh['at']),sh['text'],font=f)
            if box[0]<0 or box[1]<0 or box[2]>w or box[3]>h:raise MotionError('Text exceeds its node bounds: '+sh['text'])
            d.text(xy(sh['at']),sh['text'],font=f,fill=fill)
        else:raise MotionError('Unknown shape '+str(k))
    return im

def header(scene,bg):
    im=bg.copy();d=ImageDraw.Draw(im)
    d.rounded_rectangle(xy((24,38,516,922)),radius=44,outline='#516b70',width=2)
    d.text(xy((44,67)),scene['eyebrow'],font=font(18),fill='#edbb87')
    d.text(xy((44,109)),scene['title'],font=font(34),fill='#f8f1e6')
    d.text(xy((44,164)),scene['subtitle'],font=font(20,False),fill='#b5c7c6')
    d.line([xy((44,202)),xy((496,202))],fill='#536d70',width=2)
    d.text(xy((44,880)),'ILLUSTRATED EXPLANATION',font=font(18),fill='#a3b9b5')
    return im

def make_background():
    im=Image.new('RGBA',(W,H));d=ImageDraw.Draw(im)
    for y in range(H):
        v=y/H;d.line((0,y,W,y),fill=(round(13+7*v),round(25+12*v),round(33+14*v),255))
    return im

def prepare(compiled):
    bg=make_background()
    for scene in compiled:
        scene['_bg']=header(scene,bg)
        scene['_neutral']=bg.convert('RGB')
        for node in scene['nodes']:
            if not any(x['kind']=='path' for x in node['shapes']):node['_sprite']=draw_shapes(node)

def render_frame(scene,t):
    canvas=scene['_bg'].copy()
    for node in sorted(scene['nodes'],key=lambda n:n.get('z',0)):
        st=state(node,scene['compiled_events'],t)
        if st['opacity']<=0 or st['scale']<=0:continue
        sprite=node.get('_sprite')
        if sprite is None:sprite=draw_shapes(node,st['reveal'])
        elif st['opacity']<1:sprite=sprite.copy()
        if node.get('_sprite') is not None and st['reveal']<1:
            sprite=sprite.copy();mask=Image.new('L',sprite.size,0)
            if st['reveal']>0:ImageDraw.Draw(mask).rectangle((0,0,max(0,round(sprite.width*st['reveal'])-1),sprite.height-1),fill=255)
            sprite.putalpha(ImageChops.multiply(sprite.getchannel('A'),mask))
        if st['scale']!=1:
            sprite=sprite.resize((max(1,round(sprite.width*st['scale'])),max(1,round(sprite.height*st['scale']))),Image.Resampling.LANCZOS)
        if st['rotation']:sprite=sprite.rotate(st['rotation'],Image.Resampling.BICUBIC,expand=True)
        if st['opacity']<1:
            sprite=sprite.copy();sprite.putalpha(sprite.getchannel('A').point(lambda p:round(p*max(0,min(1,st['opacity'])))))
        px,py=node['pos'];ox,oy=st['offset'];x=round((px+ox)*S+(node['size'][0]*S-sprite.width)/2);y=round((py+oy)*S+(node['size'][1]*S-sprite.height)/2)
        canvas.alpha_composite(sprite,(x,y))
    return canvas.convert('RGB')

def caption_frame(im,words,t):
    if not words:return im
    candidates=[i for i,w in enumerate(words) if w['start']<=t]
    if not candidates:return im
    i=candidates[-1];start=(i//4)*4;group=words[start:start+4]
    labels=[w['text'].upper() for w in group];f=font(22);d=ImageDraw.Draw(im)
    widths=[d.textlength(x,font=f) for x in labels];space=d.textlength(' ',font=f);total=sum(widths)+space*(len(widths)-1)
    if total>900:
        f=font(18);widths=[d.textlength(x,font=f) for x in labels];space=d.textlength(' ',font=f);total=sum(widths)+space*(len(widths)-1)
    x=(1080-total)/2; d.rounded_rectangle((max(40,int(x-24)),1590,min(1040,int(x+total+24)),1662),radius=18,fill='#102b2d')
    for j,label in enumerate(labels):
        d.text((int(x),1598),label,font=f,fill='#f0bc8b' if start+j==i else '#f4f6ed');x+=widths[j]+space
    return im

def render(compiled,audio,duration,out,*,fps=24,words=None,cover=None):
    prepare(compiled);out=Path(out);silent=out.with_name(out.stem+'-silent.mp4');count=round(duration*fps);ff=ffmpeg_exe();cover_image=Image.open(cover).convert('RGB') if cover else None
    if cover_image is not None and cover_image.size!=(W,H):raise MotionError('Cover must be 1080x1920')
    proc=subprocess.Popen([ff,'-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(fps),'-i','-','-an','-c:v','libx264','-threads','2','-preset','veryfast','-crf','19','-pix_fmt','yuv420p',str(silent)],stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        for i in range(count):
            t=i/fps;idx=max(k for k,s in enumerate(compiled) if s['start_time']<=t)
            # Fade through background, rather than overlapping unreadable headings.
            sc=compiled[idx];im=render_frame(sc,t);fade=.18
            if idx and t<sc['start_time']+fade:im=Image.blend(sc['_neutral'],im,_ease((t-sc['start_time'])/fade,'smooth'))
            if idx<len(compiled)-1 and t>sc['end_time']-fade:im=Image.blend(sc['_neutral'],im,_ease((sc['end_time']-t)/fade,'smooth'))
            if words:im=caption_frame(im,words,t)
            if i==0 and cover_image is not None:im=cover_image
            proc.stdin.write(im.tobytes())
            if i%120==0:print(f'frame {i}/{count}',flush=True)
        proc.stdin.close();err=proc.stderr.read();ret=proc.wait()
        if ret:raise MotionError('Encode failed: '+err.decode(errors='replace')[-1000:])
    except BaseException:
        proc.kill();proc.wait();raise
    subprocess.run([ff,'-y','-v','error','-i',str(silent),'-i',str(audio),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-t',str(duration),'-movflags','+faststart',str(out)],check=True)
    return {'output':str(out),'frames':count,'duration':duration,'fps':fps}
