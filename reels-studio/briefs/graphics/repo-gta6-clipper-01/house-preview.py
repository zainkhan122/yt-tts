import base64, io,json,subprocess,math,os,hashlib,urllib.request
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
import imageio_ffmpeg
root=Path('.'); cap=root/'captures/repo-gta6-clipper-01';out=root/'renders/repo-gta6-clipper-01';out.mkdir(exist_ok=True,parents=True)
# Restore pinned repository media locally; no creator footage is uploaded by the voice workflow.
media_hashes={'short-kaicenat.webp':'3d6310acf8c912eb495b97c566b4f0834687a8cbb1c9ccd7746cdf239affa52b','home.png':'a413f92ff1344a3d91b8c5cecdcd3cb62a66292573d439f11906c8f4f0ee85de','one-short.png':'4c1a73ff4bd3e0fef3a749c963d524ddd320408cf508058476a7b533cf09154b'}
cap.mkdir(parents=True,exist_ok=True)
base='https://gitlab.com/nocodehack.io/gta6-clipper/-/raw/9a96d6f3d71010a94b482eb1cbde1caf9d5d72ce/docs/img/'
for name,expected in media_hashes.items():
    f=cap/name
    if not f.exists():
        req=urllib.request.Request(base+name,headers={'User-Agent':'Hypeless-review/1.0'})
        with urllib.request.urlopen(req,timeout=60) as r: blob=r.read(12000000)
        if hashlib.sha256(blob).hexdigest()!=expected: raise SystemExit('Pinned media digest mismatch: '+name)
        f.write_bytes(blob)
    if hashlib.sha256(f.read_bytes()).hexdigest()!=expected: raise SystemExit('Local pinned media digest mismatch: '+name)
def data(path):
 p=Path(path);return 'data:image/'+('jpeg' if p.suffix.lower() in ['.jpg','.jpeg'] else p.suffix[1:])+';base64,'+base64.b64encode(p.read_bytes()).decode()
imgs=[]
a=Image.open(cap/'short-kaicenat.webp')
for n in range(0,a.n_frames,2):
 a.seek(n);b=io.BytesIO();a.convert('RGB').save(b,format='JPEG',quality=80);imgs.append('data:image/jpeg;base64,'+base64.b64encode(b.getvalue()).decode())
screens={n:data(cap/(n+'.png')) for n in ['home','one-short']}
script=['Turn a long stream into vertical clips without scrubbing the whole thing. Meet GTA Six Clipper.','Give it a stream or video link. It transcribes locally and looks for peaks in chat and loudness.','Those signals help pick moments. You can add an AI pass, but you do not have to.','It cuts the clip, puts the streamer above the game, and adds a hook and word by word captions.','Review each short before sharing. You can adjust the edit, and the original stays intact.','The tool is free, but optional services may cost money. Get the creator\'s permission before posting their footage.','Want the repo? Comment CLIP and follow Hypeless for more tools, minus the hype.']
durs=[5.2,6.1,5.5,6.2,5.2,6.3,5.2]; t=0;sc=[]
for i,(txt,d) in enumerate(zip(script,durs)):
 words=txt.split(); ws=[];weights=[max(1,len(w.strip('.,'))**.65) for w in words]; total=sum(weights);pos=t+.2
 for w,weight in zip(words,weights):
  dur=(d-.4)*weight/total;ws.append([w,pos,pos+dur]);pos+=dur
 sc.append(dict(id='s'+str(i),t0=t,t1=t+d,text=txt,words=ws,archetype='endcard' if i==6 else 'gta',headline='YOUR CALL',payload={'keyword':'CLIP','prompt':'for the repo link'}));t+=d
voice_file=out/'voice-handoff'/'voice.wav'
timings_file=out/'voice-handoff'/'timings.json'
if voice_file.exists() and timings_file.exists():
    real=json.loads(timings_file.read_text())
    assert real['engine']=='chatterbox' and real['profile']=='option-3' and real['overall_match']>=.95
    for i,item in enumerate(real['scenes']):
        sc[i]['t0']=item['start']; sc[i]['t1']=item['end']; sc[i]['words']=item['words']
    for i in range(len(sc)-1): sc[i]['t1']=sc[i+1]['t0']
    t=real['duration']; sc[-1]['t1']=t
D={'handle':'@hypeless','template':'gta6-clipper','caption_words':3,'scenes':sc,'brand':{'name':'Hypeless','handle':'@hypeless','logo':data('brand/logo/yt-watermark-150.png'),'cta_button':'Follow'}}
css=(root/'graphics/templates/shared.css').read_text(); shared=(root/'graphics/templates/shared.js').read_text();outro=(root/'graphics/outro.js').read_text();font=base64.b64encode((root/'graphics/templates/_base/fonts/Anton.ttf').read_bytes()).decode()
html='''<!doctype html><meta charset="UTF-8"><style>@font-face{font-family:Anton;src:url(data:font/ttf;base64,'''+font+''')}*{box-sizing:border-box}html,body{margin:0;width:540px;height:960px;overflow:hidden;background:#ea8e8f}#stage{width:1080px;height:1920px;position:absolute;transform:scale(.5);transform-origin:0 0;overflow:hidden;font-family:Arial,sans-serif}.scene{position:absolute;inset:0;display:none}.base{position:absolute;inset:0;background:linear-gradient(145deg,#fed19c,#f38299 58%,#a76ac3)}.base:after{content:"";position:absolute;width:1150px;height:1150px;border-radius:50%;background:#8fe0d5;left:-500px;top:520px;opacity:.35}.label{position:absolute;top:220px;left:60px;font:700 26px Arial;letter-spacing:4px;color:#29214a}.headline{position:absolute;top:340px;left:60px;right:60px;color:#272143;font:400 104px/1.02 Anton;letter-spacing:1px}.headline em{font-style:normal;color:#fff;text-shadow:0 4px 0 #7b4164}.zone{position:absolute;left:60px;right:60px;top:620px;height:900px}.shot{position:absolute;object-fit:cover;border:12px solid #fff;box-shadow:0 18px 45px #5f345177;border-radius:25px}.tag{position:absolute;bottom:80px;left:60px;right:60px;text-align:center;color:#312341;font:700 23px Arial}.badge{position:absolute;background:#fff0bc;color:#332447;font:700 25px Arial;border-radius:18px;padding:18px 24px}.screen{position:absolute;width:940px;border:10px solid white;border-radius:25px;box-shadow:0 18px 45px #5f345177}.bars{position:absolute;top:380px;left:35px;width:780px;height:175px;display:flex;gap:15px;align-items:end}.bar{width:38px;border-radius:8px 8px 0 0;background:#ffd60a;transform-origin:bottom}.rail{position:absolute;height:58px;left:40px;right:40px;background:#d7d2ed;border-radius:12px}.selected{position:absolute;background:#ffd60a;border-radius:10px;height:58px}.card{position:absolute;background:#fff;border-radius:24px;padding:32px;color:#2d264b;font:700 31px Arial;box-shadow:0 12px 25px #4c214433}.yt-outro-title,.yt-outro-name{font-family:Anton,Arial!important}.yt-handle{color:#3b244e!important;z-index:10}.credit{position:absolute;bottom:210px;left:70px;right:70px;font:700 20px Arial;color:#362d50;text-align:center}.draft{position:absolute;bottom:32px;left:0;right:0;text-align:center;color:#3b294a;font:700 18px Arial;letter-spacing:1px;z-index:999}.yt-cap{z-index:110}.yt-cap.outro-caption{top:1500px}
'''+css+'''</style><div id="stage"><div class="scene" data-scene="s0"><div class="base"></div><div class="label">GTA 6 CLIPPER</div><div class="headline">YOUR STREAM<br><em>TO A SHORT</em></div><div class="zone"><img id="vid0" class="shot" style="left:250px;top:0px;width:460px;height:818px"><div class="badge" style="left:0;top:120px">STREAM</div><div class="badge" style="right:0;top:570px">9:16 SHORT</div></div><div class="credit">REPO SAMPLE • KAI CENAT • CREATOR RETAINS RIGHTS</div></div>
<div class="scene" data-scene="s1"><div class="base"></div><div class="label">01 / FIND THE MOMENT</div><div class="headline">CHAT + AUDIO<br><em>FIND PEAKS</em></div><div class="zone"><img class="screen" id="screen-home" style="top:10px"><div class="card" style="top:340px;left:0;width:940px;height:290px">CHAT ACTIVITY<div class="bars" style="top:80px;left:40px" id="bars"></div></div></div><div class="credit">REPOSITORY UI • CHART IS ILLUSTRATIVE, NOT DATA</div></div>
<div class="scene" data-scene="s2"><div class="base"></div><div class="label">02 / PICK A MOMENT</div><div class="headline">PICK THE<br><em>HIGHLIGHT</em></div><div class="zone"><img id="vid2" class="shot" style="width:300px;height:534px;left:30px;top:10px"><div class="card" style="left:370px;top:100px;width:480px">Chat + loudness<br><br>Optional AI pass</div><div class="rail" style="top:750px"><div id="selection" class="selected" style="left:25%;width:0"></div></div></div><div class="credit">REPO SAMPLE • KAI CENAT • CREATOR RETAINS RIGHTS</div></div>
<div class="scene" data-scene="s3"><div class="base"></div><div class="label">03 / MAKE THE SHORT</div><div class="headline">STREAMER + GAME<br><em>ONE VERTICAL CLIP</em></div><div class="zone"><img id="vid3" class="shot" style="width:420px;height:748px;left:250px;top:0"><div class="badge" style="left:0;top:80px">FACE CAM</div><div class="badge" style="right:0;top:450px">GAME</div></div><div class="credit">REPO SAMPLE • KAI CENAT • CREATOR RETAINS RIGHTS</div></div>
<div class="scene" data-scene="s4"><div class="base"></div><div class="label">04 / REVIEW</div><div class="headline">YOU CONTROL<br><em>THE FINAL CUT</em></div><div class="zone"><img class="screen" id="screen-edit" style="top:20px"><div class="card" style="left:90px;top:500px;width:780px">Adjust the edit. Original stays.</div></div><div class="credit">OFFICIAL REPOSITORY SCREENSHOT</div></div>
<div class="scene" data-scene="s5"><div class="base"></div><div class="label">05 / THE CATCH</div><div class="headline">CHECK BEFORE<br><em>YOU SHARE</em></div><div class="zone"><div class="card" style="left:15px;top:100px;width:910px">Optional AI and publishing services may cost money.</div><div class="card" style="left:15px;top:340px;width:910px">Get the creator’s permission to post their footage.</div></div><div class="credit">FAN-MADE TOOL • NOT AFFILIATED WITH ROCKSTAR</div></div><div class="scene" data-scene="s6"><div class="base"></div></div><div class="draft">' + ('REVIEW DRAFT • RIGHTS CLEARANCE REQUIRED' if voice_file.exists() else 'SILENT PREVIEW • CAPTION TIMING IS PROVISIONAL') + '</div></div>
<script>window.DATA='''+json.dumps(D)+''';const frames='''+json.dumps(imgs)+''';const pics='''+json.dumps(screens)+''';document.querySelector('#screen-home').src=pics.home;document.querySelector('#screen-edit').src=pics['one-short'];const heights=[38,76,53,90,57,109,72,155,99,83,120,70,54,43,85,55];document.querySelector('#bars').innerHTML=heights.map(h=>'<div class="bar" style="height:'+h+'px"></div>').join('');window.setTime=function(t){let s=DATA.scenes.find(x=>t>=x.t0&&t<x.t1)||DATA.scenes.at(-1);document.querySelectorAll('.scene').forEach(x=>x.style.display=x.dataset.scene===s.id?'block':'none');let u=(t-s.t0)/(s.t1-s.t0);let n=Math.floor(t*12)%frames.length;['vid0','vid2','vid3'].forEach(id=>document.getElementById(id).src=frames[n]);document.querySelectorAll('.bar').forEach((e,i)=>e.style.transform='scaleY('+Math.max(.03,Math.min(1,(u*2.5-i*.04)))+')');document.querySelector('#selection').style.width=(Math.min(1,u*2)*40)+'%';let scene=document.querySelector('[data-scene="'+s.id+'"]');if(scene&&s.archetype!=='endcard'){let zone=scene.querySelector('.zone');if(zone){zone.style.transform='translateY('+Math.round((1-Math.min(1,u*4))*35)+'px)';let pic=zone.querySelector('.screen');if(pic)pic.style.transform='translateX('+Math.round(12*Math.sin(u*Math.PI))+'px) scale('+(1+.025*u)+')';let cards=zone.querySelectorAll('.card');cards.forEach((card,i)=>{let v=Math.max(0,Math.min(1,(u-i*.25)*4));card.style.opacity=v;card.style.transform='translateY('+Math.round((1-v)*35)+'px)';});}}};</script><script>'''+outro+'''</script><script>'''+shared+'''</script>'''
(out/'house-preview.html').write_text(html)
ff=imageio_ffmpeg.get_ffmpeg_exe();target=out/('gta6-clipper-narrated-review.mp4' if voice_file.exists() else 'gta6-clipper-repo-media-preview.mp4');fps=15
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,args=['--no-sandbox','--allow-file-access-from-files']);page=browser.new_page(viewport={'width':540,'height':960},device_scale_factor=1);page.goto((out/'house-preview.html').resolve().as_uri());page.evaluate('document.fonts.ready');page.evaluate('window.setTime(0)');page.screenshot(path=str(out/'house-preview-frame-zero.png'))
 proc=subprocess.Popen([ff,'-y','-loglevel','error','-f','image2pipe','-vcodec','mjpeg','-r',str(fps),'-i','-','-vf','scale=1080:1920:flags=lanczos','-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-movflags','+faststart',str(target)],stdin=subprocess.PIPE)
 for n in range(math.ceil(t*fps)):
  page.evaluate('(t)=>window.setTime(t)',n/fps)
  proc.stdin.write(page.screenshot(type='jpeg',quality=88))
 proc.stdin.close();code=proc.wait();browser.close()
 if code:raise SystemExit(code)
if voice_file.exists():
    silent=target.with_name('temp-silent.mp4'); target.rename(silent)
    subprocess.run([ff,'-y','-loglevel','error','-i',str(silent),'-i',str(voice_file),'-c:v','copy','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',str(target)],check=True)
    silent.unlink()
    subprocess.run([ff,'-y','-loglevel','error','-i',str(target),'-frames:v','1',str(out/'narrated-frame-zero.png')],check=True)
print('rendered',target,'seconds',t)
