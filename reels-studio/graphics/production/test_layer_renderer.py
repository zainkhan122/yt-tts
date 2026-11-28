"""Layer renderer tests: synthetic fixtures, not the acceptance demonstration."""
import copy,subprocess,wave
from pathlib import Path
import pytest
from PIL import Image
from graphics.media import ffmpeg_exe,clip_duration
from graphics.production.blueprint import digest
from graphics.production.layer_renderer import compile_timeline,draw_frame,render,RenderError

def setup(tmp):
    audio=tmp/'voice.wav'
    with wave.open(str(audio),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(8000);f.writeframes(b'\0\0'*8000)
    bg=tmp/'bg.png';fg=tmp/'fg.png';Image.new('RGB',(60,80),'blue').save(bg);Image.new('RGBA',(20,20),(255,0,0,128)).save(fg)
    s={'audio_sha256':digest(audio),'audio_duration':1.,'beats':[{'id':'one','start':0.,'end':1.,'events':[{'id':'move','audio_time':.1,'duration':.4,'beat_relative_time':.1}]}]}
    assets={p.stem:{'path':str(p),'sha256':digest(p),'type':'image'} for p in (bg,fg)}
    layers=[{'id':'back','asset':'bg','x':270,'y':480,'width':540,'height':960,'z':0,'opacity':1},{'id':'front','asset':'fg','x':270,'y':480,'width':100,'height':100,'z':1,'opacity':1}]
    design={'assets':assets,'beats':{'one':{'layers':layers,'events':{'move':{'target':'front','operation':'position','from':[270,480],'to':[330,480],'easing':'linear'}},'transition':'cut'}}}
    return audio,s,design

def test_event_timing_transparency_and_multiple_layers(tmp_path):
    audio,s,d=setup(tmp_path);t=compile_timeline(s,d,audio);imgs={'bg':Image.open(d['assets']['bg']['path']).convert('RGBA'),'fg':Image.open(d['assets']['fg']['path']).convert('RGBA')}
    im=draw_frame(t['beats'][0],.1,imgs);p=im.getpixel((270,480));assert p[0]>100 and p[2]>100
    assert draw_frame(t['beats'][0],.5,imgs).getpixel((270,480))==(0,0,255)
    assert t['beats'][0]['events'][0]['start']==.1

def test_reject_bad_operations_time_and_assets(tmp_path):
    audio,s,d=setup(tmp_path);bad=copy.deepcopy(d);bad['beats']['one']['events']['move']['operation']='warp'
    with pytest.raises(RenderError,match='Unsupported'):compile_timeline(s,bad,audio)
    s['beats'][0]['events'][0]['duration']=2
    with pytest.raises(RenderError,match='outside'):compile_timeline(s,d,audio)
    s['beats'][0]['events'][0]['duration']=.4;Path(d['assets']['fg']['path']).write_bytes(b'bad')
    with pytest.raises(RenderError,match='changed'):compile_timeline(s,d,audio)
    d['assets']['fg']['sha256']=digest(d['assets']['fg']['path'])
    with pytest.raises(RenderError,match='Invalid image'):compile_timeline(s,d,audio)

def test_real_mp4_integration_and_cache(tmp_path):
    audio,s,d=setup(tmp_path);timeline=compile_timeline(s,d,audio);out=tmp_path/'out.mp4';work=tmp_path/'work'
    one=render(timeline,audio,out,work,fps=5);clip=Path(one['clips'][0]);before=clip.stat().st_mtime_ns
    assert abs(clip_duration(out)-1)<.22
    r=subprocess.run([ffmpeg_exe(),'-v','error','-xerror','-i',str(out),'-f','null','-'],capture_output=True);assert r.returncode==0
    info=subprocess.run([ffmpeg_exe(),'-i',str(out)],capture_output=True,text=True).stderr;assert '1080x1920' in info and 'Audio:' in info
    render(timeline,audio,out,work,fps=5);assert clip.stat().st_mtime_ns==before
    render(timeline,audio,out,work,fps=5,force=True);assert clip.stat().st_mtime_ns>before
    Path(d['assets']['fg']['path']).write_bytes(b'broken')
    with pytest.raises(RenderError,match='Asset changed'):render(timeline,audio,out,work,fps=5)

def test_video_assets_and_failure(tmp_path):
    audio,s,d=setup(tmp_path);vid=tmp_path/'v.mp4'
    subprocess.run([ffmpeg_exe(),'-v','error','-f','lavfi','-i','color=red:s=40x40:r=5:d=1','-c:v','libx264','-pix_fmt','yuv420p',str(vid)],check=True)
    d['assets']['bg']={'path':str(vid),'sha256':digest(vid),'type':'video'};timeline=compile_timeline(s,d,audio);out=tmp_path/'video.mp4';render(timeline,audio,out,tmp_path/'work',fps=5);assert out.exists()
    vid.write_bytes(b'bad video');d['assets']['bg']['sha256']=digest(vid)
    with pytest.raises(RenderError,match='Invalid video'):compile_timeline(s,d,audio)

def test_fps_rejected(tmp_path):
    a,s,d=setup(tmp_path);t=compile_timeline(s,d,a)
    with pytest.raises(RenderError,match='FPS'):render(t,a,tmp_path/'x.mp4',tmp_path/'work',fps=0)

def test_cache_corruption_reports_failure(tmp_path):
    audio,s,d=setup(tmp_path);t=compile_timeline(s,d,audio);work=tmp_path/'work';out=tmp_path/'x.mp4'
    result=render(t,audio,out,work,fps=5);Path(result['clips'][0]).write_bytes(b'bad')
    with pytest.raises(RenderError,match='Cached clip'):render(t,audio,out,work,fps=5)
    render(t,audio,out,work,fps=5,force=True);assert out.exists()

def test_native_pixel_compositing(tmp_path):
    a,s,d=setup(tmp_path);t=compile_timeline(s,d,a);imgs={'bg':Image.open(d['assets']['bg']['path']).convert('RGBA'),'fg':Image.open(d['assets']['fg']['path']).convert('RGBA')}
    assert draw_frame(t['beats'][0],.1,imgs,pixel_ratio=2).size==(1080,1920)
    out=tmp_path/'native.mp4';render(t,a,out,tmp_path/'native',fps=3,native=True);assert out.exists()

def test_reveal_mask_clips_without_squashing():
    from PIL import Image
    from graphics.production.layer_renderer import draw_frame
    img=Image.new('RGBA',(100,100),(255,0,0,255))
    layer={'id':'a','asset':'a','x':100,'y':100,'width':100,'height':100,'z':0,'opacity':1}
    event={'target':'a','operation':'reveal_x','from':0.,'to':1.,'start':0.,'end':1.,'easing':'linear'}
    frame=draw_frame({'layers':[layer],'events':[event],'transition':'cut','start':0.,'end':2.},.5,{'a':img})
    assert frame.getpixel((70,100))==(255,0,0)
    assert frame.getpixel((130,100))==(17,28,31)
