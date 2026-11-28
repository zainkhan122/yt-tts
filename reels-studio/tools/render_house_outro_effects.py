import base64,subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright
import imageio_ffmpeg
r=Path(__file__).resolve().parents[1];o=r/'renders/claude-video-effects-01';o.mkdir(exist_ok=True)
def data(p):return 'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()
font=base64.b64encode((r/'graphics/templates/_base/fonts/Inter.ttf').read_bytes()).decode()
mono=base64.b64encode((r/'graphics/templates/_base/fonts/JetBrainsMono.ttf').read_bytes()).decode()
css=(r/'graphics/templates/shared.css').read_text();js=(r/'graphics/outro.js').read_text()
html='''<!doctype html><meta charset="UTF-8"><style>@font-face{font-family:Inter;src:url(data:font/ttf;base64,'''+font+''')}@font-face{font-family:'JetBrains Mono';src:url(data:font/ttf;base64,'''+mono+''')}*{box-sizing:border-box}html,body{margin:0;width:540px;height:960px;overflow:hidden}#stage{position:absolute;width:1080px;height:1920px;transform:scale(.5);transform-origin:0 0}'''+css+'''</style><div id="stage"></div><script>window.DATA={brand:{name:'Hypeless',handle:'@hypeless',logo:"'''+data(r/'brand/logo/yt-watermark-150.png')+'''",cta_button:'Follow'}};</script><script>'''+js+'''</script><script>let scene={headline:'MORE AI TOOLS',t0:0,payload:{keyword:'EFFECTS',prompt:'for the repo link'}};let ref=buildOutro(document.getElementById('stage'),scene);window.seek=(t)=>updateOutro(ref,scene,t,1.9);window.seek(0);</script>'''
(o/'house-outro.html').write_text(html)
ff=imageio_ffmpeg.get_ffmpeg_exe();temp=o/'house-outro.mp4';final=o/'claude-video-effects-final.mp4';src=o/'claude-video-effects-01.mp4'
# deterministic frame stepping, using the existing shared house outro component
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':540,'height':960},device_scale_factor=1);page.goto((o/'house-outro.html').as_uri());page.evaluate('document.fonts.ready');
 cmd=[ff,'-y','-loglevel','error','-f','image2pipe','-vcodec','png','-r','24','-i','-','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p',str(temp)]
 p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
 for i in range(46):page.evaluate('(t)=>window.seek(t)',i/24);p.stdin.write(page.screenshot(type='png'))
 p.stdin.close()
 if p.wait():raise RuntimeError('outro rendering failed')
 browser.close()
# retain narration exactly through its end; append actual house animation with silent tail
D=28.33
subprocess.run([ff,'-y','-loglevel','error','-i',str(src),'-i',str(temp),'-filter_complex',f'[0:v]trim=duration={D},setpts=PTS-STARTPTS,scale=1080:1920,fps=24[v0];[1:v]scale=1080:1920,fps=24,setpts=PTS-STARTPTS[v1];[v0][v1]concat=n=2:v=1:a=0[v];[0:a]atrim=duration={D},asetpts=PTS-STARTPTS,apad=pad_dur=1.9[a]','-map','[v]','-map','[a]','-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-t',str(D+1.9),'-movflags','+faststart',str(final)],check=True)
subprocess.run([ff,'-y','-loglevel','error','-i',str(final),'-frames:v','1',str(r/'covers/claude-video-effects-01/final-cover.png')],check=True)
print('Wrote',final,flush=True)
