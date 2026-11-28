"""Small, opt-in procedural battery renderer with independently cached beat clips.

The drawings are schematic, not photorealistic, and not a general 3D renderer.
"""
import hashlib, json, math, os, subprocess, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from lib.cover_frame import _ffmpeg
from .blueprint import validate

FPS=24; W=540; H=960

def frame(b,t):
    im=Image.new('RGB',(W,H),'#e8eee7');d=ImageDraw.Draw(im)
    beat=b['animations'][0]; k=beat['kind']; p=max(0,min(1,(t-beat['start'])/max(.001,beat['end']-beat['start'])))
    font=ImageFont.truetype('DejaVuSans-Bold.ttf',24);sm=ImageFont.truetype('DejaVuSans.ttf',16)
    d.text((40,82),b['visual_objective'],font=font,fill='#193d39')
    if k=='phone_explode':
        shift=int(110*p);d.rounded_rectangle((143-shift,270,397-shift,720),30,fill='#38585a',outline='#162c30',width=5)
        d.rounded_rectangle((157-shift,284,383-shift,706),23,fill='#bbc9c1')
        d.rounded_rectangle((190,365,350,635),12,fill='#caba7d',outline='#435854',width=5);d.text((205,475),'BATTERY',font=sm,fill='#263a39')
        d.rounded_rectangle((143+shift,270,397+shift,720),30,outline='#1c383c',width=8)
    elif k=='battery_charge':
        d.rounded_rectangle((72,310,468,650),18,fill='#315858');d.rectangle((96,337,210,624),fill='#db9a71');d.rectangle((330,337,444,624),fill='#84a8ad');d.rectangle((215,337,325,624),fill='#f6e9c4')
        d.rounded_rectangle((118,740,422,790),8,outline='#284b43',width=4);d.rectangle((124,746,124+int(285*(1-.55*p)),784),fill='#5c9c78');d.text((118,805),'ILLUSTRATIVE ENERGY STATE',font=sm,fill='#294b43')
    elif k=='ion_flow':
        d.rectangle((25,270,143,720),fill='#d68966');d.rectangle((397,270,515,720),fill='#73a5ad');d.rectangle((143,270,397,720),fill='#f7e9ca')
        for i in range(12):
            x=150+((i*63+p*240)%240);y=305+(i%6)*65;d.ellipse((x,y,x+15,y+15),fill='#db864c')
        d.text((160,760),'ION MOVEMENT',font=sm,fill='#294b43')
    else: raise ValueError('Unsupported object animation '+k)
    d.text((40,900),'SCHEMATIC • NOT TO SCALE',font=sm,fill='#526f65')
    if k=='phone_explode':
        # Optical push supports, but does not substitute for, casing separation.
        scale=1+.10*p; sw=int(W*scale);sh=int(H*scale)
        big=im.resize((sw,sh),Image.Resampling.LANCZOS)
        im=big.crop(((sw-W)//2,(sh-H)//2,(sw-W)//2+W,(sh-H)//2+H))
    return im

def render(bp,audio,work,out,cover=None,force=()):
    validate(bp,audio);work=Path(work);work.mkdir(parents=True,exist_ok=True);out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    state={'audio_sha256':bp['audio_sha256'],'beats':{},'status':'running'}
    statepath=work/'state.json'
    def save():
        temp=statepath.with_suffix('.tmp');temp.write_text(json.dumps(state,indent=2));os.replace(temp,statepath)
    save();clips=[];ff=_ffmpeg();frames_total=round(bp['audio_duration']*FPS); previous=0
    if cover:
        with Image.open(cover) as c:
            if c.size!=(W,H):raise ValueError('Cover must match render dimensions')
            from PIL import ImageChops
            if ImageChops.difference(c.convert('RGB'),frame(bp['beats'][0],0)).getbbox():
                raise ValueError('Cover must be generated from the opening composition')
    for beat in bp['beats']:
        if beat['overlays'] or beat['sound_effects'] or beat['transition']!='cut' or len(beat['animations'])!=1:
            raise ValueError('Prototype supports one animation, cuts, and no overlays or effects; unsupported instructions cannot be silently ignored')
        end=round(beat['end']*FPS);count=end-previous
        if count<1:raise ValueError('Beat shorter than a frame')
        # timing, render version and cover are included in key; unchanged beat files are reused.
        payload={'beat':beat,'frames':count,'fps':FPS,'renderer':'battery-v1','cover':hashlib.sha256(Path(cover).read_bytes()).hexdigest() if cover and previous==0 else None}
        key=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest();clip=work/(beat['id']+'-'+key[:16]+'.mp4');clips.append(clip)
        state['beats'][beat['id']]={'status':'rendering','cache_key':key};save()
        if not clip.exists() or beat['id'] in force:
            tmp=clip.with_name(clip.stem+'.tmp.mp4')
            try:
                cmd=[ff,'-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p',str(tmp)]
                proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
                try:
                    for i in range(count):
                        t=(previous+i)/FPS
                        image=Image.open(cover).convert('RGB') if cover and previous==0 and i==0 else frame(beat,t)
                        proc.stdin.write(image.tobytes())
                    proc.stdin.close();err=proc.stderr.read();rc=proc.wait()
                    if rc:raise RuntimeError(err.decode(errors='replace'))
                except BaseException:
                    proc.kill();proc.wait();raise
                os.replace(tmp,clip)
            except BaseException as exc:
                tmp.unlink(missing_ok=True);state['beats'][beat['id']]={'status':'failed','error':str(exc)};state['status']='failed';save();raise
        state['beats'][beat['id']]={'status':'complete','cache_key':key,'path':str(clip)};save();previous=end
    with tempfile.TemporaryDirectory(prefix='beat-join-',dir=work) as td:
        listing=Path(td)/'list.txt';listing.write_text(''.join("file '"+str(c.resolve()).replace("'","'\\''")+"'\n" for c in clips))
        tmp=Path(td)/'output.mp4'
        subprocess.run([ff,'-y','-loglevel','error','-f','concat','-safe','0','-i',str(listing),'-i',str(audio),'-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-t',str(bp['audio_duration']),'-movflags','+faststart',str(tmp)],check=True)
        os.replace(tmp,out)
    state['status']='complete';state['frames']=frames_total;save();return out
