"""Review-only layer compositor: scheduled events -> Pillow frames -> FFmpeg.

Local files only; transparent PNG, JPEG and MP4. No provider API or publishing.
Coordinates are in 540x960 design units, output is encoded at 1080x1920.
"""
from __future__ import annotations
import hashlib,json,math,os,re,subprocess,tempfile
from pathlib import Path
from PIL import Image
from graphics.media import ffmpeg_exe,clip_duration
from .blueprint import digest,duration as wav_duration

class RenderError(ValueError):pass
W,H=540,960
OPS={'position','scale','rotation','opacity','camera','reveal_x','reveal_y'}
EASING={'linear','smooth','ease_in','ease_out'}

def number(x):return type(x) in (float,int) and math.isfinite(x)
def _pair(v):return isinstance(v,list) and len(v)==2 and all(number(x) for x in v)

def compile_timeline(scheduled, design, audio):
    """Translate scheduled event IDs to executable transforms; reject omission or drift."""
    if digest(audio)!=scheduled.get('audio_sha256'):raise RenderError('Audio digest mismatch')
    D=wav_duration(audio)
    if abs(D-scheduled.get('audio_duration',-1))>.001:raise RenderError('Audio duration mismatch')
    if not isinstance(design,dict) or set(design)!={'assets','beats'}:raise RenderError('Invalid design')
    assets=design['assets']; beats=scheduled['beats']; layouts=design['beats']
    if set(layouts)!={b['id'] for b in beats}:raise RenderError('Beat/layout mismatch')
    if not isinstance(assets,dict) or not assets:raise RenderError('Assets missing')
    checked={}
    for aid,a in assets.items():
        if not isinstance(aid,str) or not re.fullmatch(r'[A-Za-z0-9_-]+',aid):raise RenderError('Unsafe asset ID')
        if not isinstance(a,dict) or set(a)!={'path','sha256','type'} or a['type'] not in {'image','video'}:raise RenderError('Invalid asset '+aid)
        p=Path(a['path'])
        if not p.is_file() or digest(p)!=a['sha256']:raise RenderError('Missing or changed asset '+aid)
        if a['type']=='image':
            try:
                with Image.open(p) as im:
                    if im.format not in {'PNG','JPEG'} or im.width*im.height>24_000_000:raise RenderError('Unsupported image '+aid)
                    im.verify()
            except OSError as exc:raise RenderError('Invalid image '+aid) from exc
        else:
            if clip_duration(p)<=0:raise RenderError('Invalid video '+aid)
            probe=subprocess.run([ffmpeg_exe(),'-v','error','-xerror','-i',str(p),'-map','0:v:0','-f','null','-'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=120)
            if probe.returncode:raise RenderError('Invalid video '+aid)
        checked[aid]=dict(a)
    out=[];previous=0
    for b in beats:
        if abs(b['start']-previous)>.001 or not b['end']>b['start']:raise RenderError('Beat boundaries must be contiguous')
        d=layouts[b['id']]
        if set(d)!={'layers','events','transition'} or d['transition'] not in {'cut','fade'}:raise RenderError('Invalid transition or layout '+b['id'])
        layers=d['layers'];ids=set()
        for l in layers:
            if set(l)!={'id','asset','x','y','width','height','z','opacity'} or l['id'] in ids or l['asset'] not in checked:raise RenderError('Invalid layer '+b['id'])
            if not all(number(l[k]) for k in ('x','y','width','height','z','opacity')) or l['width']<=0 or l['height']<=0 or not 0<=l['opacity']<=1:raise RenderError('Invalid layer bounds')
            ids.add(l['id'])
        assigned=d['events'];evts=b['events']
        if set(assigned)!={e['id'] for e in evts}:raise RenderError('All scheduled events require executable instructions')
        compiled=[]
        for e in evts:
            v=assigned[e['id']];op=v.get('operation')
            if set(v)!={'target','operation','from','to','easing'} or op not in OPS or v['easing'] not in EASING:raise RenderError('Unsupported event '+e['id'])
            if (op=='camera' and v['target']!='camera') or (op!='camera' and v['target'] not in ids):raise RenderError('Invalid event target '+e['id'])
            if op in {'position','camera'}:
                if not _pair(v['from']) or not _pair(v['to']):raise RenderError('Position/camera values must be pairs')
                if op=='camera' and (v['from'][0]<=0 or v['to'][0]<=0):raise RenderError('Camera scale must be positive')
            elif not number(v['from']) or not number(v['to']):raise RenderError('Animation values must be finite')
            if op=='scale' and (v['from']<=0 or v['to']<=0):raise RenderError('Scale must be positive')
            if op in {'opacity','reveal_x','reveal_y'} and not all(0<=v[k]<=1 for k in ('from','to')):raise RenderError('Opacity/reveal must be within zero and one')
            t=e['audio_time'];end=t+e['duration']
            if not all(number(x) for x in (t,end)) or t<b['start'] or end>b['end']+1e-6 or end<=t or abs(e['beat_relative_time']-(t-b['start']))>.001:raise RenderError('Event outside beat '+e['id'])
            compiled.append({**v,'event_id':e['id'],'start':t,'end':end})
        out.append({'id':b['id'],'start':b['start'],'end':b['end'],'layers':layers,'events':compiled,'transition':d['transition']});previous=b['end']
    if abs(previous-D)>.001:raise RenderError('Timeline does not cover narration')
    return {'audio_sha256':scheduled['audio_sha256'],'duration':D,'assets':checked,'beats':out}

def _ease(t,kind):
    t=max(0,min(1,t))
    if kind=='smooth':return t*t*(3-2*t)
    if kind=='ease_in':return t*t
    if kind=='ease_out':return 1-(1-t)**2
    return t

def _val(event,t):
    f=_ease((t-event['start'])/(event['end']-event['start']),event['easing']);a=event['from'];b=event['to']
    return [x+(y-x)*f for x,y in zip(a,b)] if isinstance(a,list) else a+(b-a)*f

def draw_frame(beat,t,images,video_frames=None,*,pixel_ratio=1):
    if pixel_ratio not in (1,2):raise RenderError('Unsupported pixel ratio')
    rw,rh=W*pixel_ratio,H*pixel_ratio
    canvas=Image.new('RGBA',(rw,rh),(17,28,31,255));camera=[1,0]
    for l in sorted(beat['layers'],key=lambda x:x['z']):
        x,y=l['x'],l['y'];scale=1.;rotation=0.;opacity=l['opacity'];reveal_x=1.;reveal_y=1.
        for e in beat['events']:
            if e['operation']=='camera':camera=_val(e,t);continue
            if e['target']!=l['id']:continue
            v=_val(e,t)
            if e['operation']=='position':x,y=v
            elif e['operation']=='scale':scale=v
            elif e['operation']=='rotation':rotation=v
            elif e['operation']=='opacity':opacity=v
            elif e['operation']=='reveal_x':reveal_x=v
            elif e['operation']=='reveal_y':reveal_y=v
        img=(video_frames or {}).get(l['asset'],images.get(l['asset']))
        if img is None:raise RenderError('No decoded layer '+l['asset'])
        img=img.resize((max(1,round(l['width']*scale*pixel_ratio)),max(1,round(l['height']*scale*pixel_ratio))),Image.Resampling.LANCZOS).convert('RGBA')
        if reveal_x<1 or reveal_y<1:
            from PIL import ImageDraw, ImageChops
            mask=Image.new('L',img.size,0)
            if reveal_x>0 and reveal_y>0:
                ImageDraw.Draw(mask).rectangle((0,0,max(0,round(img.width*reveal_x)-1),max(0,round(img.height*reveal_y)-1)),fill=255)
            img.putalpha(ImageChops.multiply(img.getchannel('A'),mask))
        if rotation:img=img.rotate(rotation,resample=Image.Resampling.BICUBIC,expand=True)
        if opacity<1:img.putalpha(img.getchannel('A').point(lambda v:round(v*opacity)))
        canvas.alpha_composite(img,(round(x*pixel_ratio-img.width/2),round(y*pixel_ratio-img.height/2)))
    scale,vertical=camera
    if scale!=1 or vertical!=0:
        sw,sh=round(rw*scale),round(rh*scale);canvas=canvas.resize((sw,sh),Image.Resampling.LANCZOS);canvas=canvas.crop(((sw-rw)//2,(sh-rh)//2+round(vertical*pixel_ratio),(sw+rw)//2,(sh+rh)//2+round(vertical*pixel_ratio)))
    if beat['transition']=='fade':
        # Fade through a dark teal midpoint at the boundary; no time is inserted.
        alpha=max(0,1-min((t-beat['start'])/.16,(beat['end']-t)/.16,1))
        if alpha:canvas=Image.blend(canvas,Image.new('RGBA',(rw,rh),(17,28,31,255)),alpha)
    return canvas.convert('RGB')

def render(timeline,audio,out,work,*,fps=24,force=False,native=False):
    if type(fps)!=int or not 1<=fps<=60:raise RenderError('FPS must be 1..60')
    if digest(audio)!=timeline['audio_sha256']:raise RenderError('Audio changed')
    pixel_ratio=2 if native else 1
    work=Path(work);work.mkdir(parents=True,exist_ok=True);out=Path(out);out.parent.mkdir(parents=True,exist_ok=True);clips=[];ff=ffmpeg_exe();last=0
    for beat in timeline['beats']:
        count=round(beat['end']*fps)-last
        if count<1:raise RenderError('Beat shorter than one frame')
        assets={l['asset']:timeline['assets'][l['asset']] for l in beat['layers']}
        for aid,a in assets.items():
            if not Path(a['path']).is_file() or digest(a['path'])!=a['sha256']:raise RenderError('Asset changed: '+aid)
        key=hashlib.sha256(json.dumps({'beat':beat,'assets':assets,'fps':fps,'version':4,'native':native},sort_keys=True).encode()).hexdigest();clip=work/(key+'.mp4');clips.append(clip)
        if clip.exists() and not force:
            probe=subprocess.run([ff,'-v','error','-xerror','-i',str(clip),'-map','0:v:0','-f','null','-'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=120)
            if probe.returncode:raise RenderError('Cached clip failed decode; rerender with force')
        if not clip.exists() or force:
            with tempfile.TemporaryDirectory(prefix='render-beat-',dir=work) as tmp:
                td=Path(tmp);images={};vids={}
                for aid,a in assets.items():
                    if digest(a['path'])!=a['sha256']:raise RenderError('Asset changed: '+aid)
                    if a['type']=='image':
                        with Image.open(a['path']) as im:images[aid]=im.convert('RGBA')
                    else:
                        folder=td/aid;folder.mkdir();r=subprocess.run([ff,'-y','-v','error','-i',a['path'],'-vf',f'fps={fps},scale={W*pixel_ratio}:{H*pixel_ratio}:force_original_aspect_ratio=decrease','-frames:v',str(count),str(folder/'%06d.png')],capture_output=True,timeout=180)
                        if r.returncode:raise RenderError('Video decode failed: '+aid)
                        files=sorted(folder.glob('*.png'))
                        if len(files)<count:raise RenderError('Video shorter than beat: '+aid)
                        vids[aid]=files
                target=td/'clip.mp4';proc=subprocess.Popen([ff,'-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W*pixel_ratio}x{H*pixel_ratio}','-r',str(fps),'-i','-','-an','-vf',('null' if native else 'scale=1080:1920:flags=lanczos'),'-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p',str(target)],stdin=subprocess.PIPE,stderr=subprocess.PIPE)
                try:
                    for i in range(count):
                        vf={}
                        for aid,files in vids.items():
                            with Image.open(files[i]) as im:vf[aid]=im.convert('RGBA')
                        proc.stdin.write(draw_frame(beat,(last+i)/fps,images,vf,pixel_ratio=pixel_ratio).tobytes())
                    proc.stdin.close();err=proc.stderr.read();rc=proc.wait()
                    if rc:raise RenderError('FFmpeg encode failed: '+err.decode(errors='replace')[-500:])
                except BaseException:
                    proc.kill();proc.wait();raise
                os.replace(target,clip)
        clipsize=clip.stat().st_size
        if clipsize==0:raise RenderError('Empty cached clip')
        last+=count
    with tempfile.TemporaryDirectory(prefix='render-join-',dir=work) as tmp:
        td=Path(tmp);listing=td/'clips.txt';listing.write_text(''.join("file '"+str(p.resolve()).replace("'","'\\''")+"'\n" for p in clips));target=td/'joined.mp4'
        r=subprocess.run([ff,'-y','-v','error','-f','concat','-safe','0','-i',str(listing),'-i',str(audio),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-t',str(timeline['duration']),'-movflags','+faststart',str(target)],capture_output=True,timeout=300)
        if r.returncode:raise RenderError('FFmpeg mux failed: '+r.stderr.decode(errors='replace')[-500:])
        os.replace(target,out)
    return {'output':str(out),'duration':timeline['duration'],'fps':fps,'frames':last,'clips':[str(x) for x in clips]}
