#!/usr/bin/env python3
"""Append the reusable narrated house end card to a finished portrait edit.

Requires house-voice WAV and its aligned timings generated for the CTA. Example:
python tools/append_house_outro.py --input render.mp4 --output review.mp4 --voice voice.wav --timings timings.json --keyword EFFECTS --body-seconds 28.33
This renders the shared stage-level house component (YOUR CALL, logo, follow,
comment chip, cursor), house captions and aligned speech. It does not publish.
"""
import argparse,base64,hashlib,json,math,re,subprocess,tempfile
from pathlib import Path
import imageio_ffmpeg
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
def uri(path,kind): return 'data:'+kind+';base64,'+base64.b64encode(path.read_bytes()).decode()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['input','output','voice','timings']:p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--keyword',required=True);p.add_argument('--body-seconds',required=True,type=float);a=p.parse_args()
 if not re.fullmatch(r'[A-Za-z0-9]{1,18}',a.keyword) or a.body_seconds<=0:p.error('invalid keyword or body duration')
 d=json.loads(a.timings.read_text());assert d.get('engine')=='chatterbox' and d.get('overall_match',0)>=.95
 words=[w for s in d['scenes'] for w in s['words']];assert words and any(a.keyword.lower() in w[0].lower() for w in words)
 duration=max(float(d['duration']),max(w[2] for w in words))+.12
 spoken=' '.join(str(w[0]).lower().strip('.,!?') for w in words)
 if duration < 4 or not all(x in spoken.split() for x in ['comment','follow','hypeless',a.keyword.lower()]):raise SystemExit('House CTA must include spoken comment, keyword, follow, Hypeless and last at least four seconds')
 data={'handle':'@hypeless','caption_words':3,'brand':{'name':'Hypeless','handle':'@hypeless','logo':uri(ROOT/'brand/logo/avatar-1080.png','image/png'),'cta_button':'Follow'},'scenes':[{'id':'outro','archetype':'endcard','headline':'YOUR CALL','t0':0,'t1':duration,'words':words,'payload':{'keyword':a.keyword,'prompt':'for the repo link'},'ev':{'press':next((w[1] for w in words if w[0].lower().strip('.,!?')=='follow'),duration*.48)}}]}
 css=(ROOT/'graphics/templates/shared.css').read_text();outro=(ROOT/'graphics/outro.js').read_text();shared=(ROOT/'graphics/templates/shared.js').read_text()
 fonts=''.join('@font-face{font-family:"'+family+'";src:url("'+uri(ROOT/path,'font/ttf')+'")}' for family,path in [('Inter','graphics/templates/_base/fonts/Inter.ttf'),('JetBrains Mono','graphics/templates/_base/fonts/JetBrainsMono.ttf'),('Anton','templates/_base/fonts/Anton.ttf')])
 html='<!doctype html><meta charset="utf-8"><style>'+fonts+'*{box-sizing:border-box}html,body{margin:0;width:540px;height:960px;overflow:hidden}#stage{position:absolute;width:1080px;height:1920px;transform:scale(.5);transform-origin:0 0}'+css+'</style><div id="stage"></div><script>window.DATA='+json.dumps(data).replace('</','<\\/')+';window.setTime=function(t){};</script><script>'+outro+'</script><script>'+shared+'</script>'
 ff=imageio_ffmpeg.get_ffmpeg_exe();a.output.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory() as td:
  h=Path(td)/'stage.html';h.write_text(html);v=Path(td)/'outro.mp4'
  with sync_playwright() as pw:
   browser=pw.chromium.launch(headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':540,'height':960});page.goto(h.as_uri());page.evaluate('document.fonts.ready')
   process=subprocess.Popen([ff,'-y','-loglevel','error','-f','image2pipe','-vcodec','png','-r','30','-i','-','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p',str(v)],stdin=subprocess.PIPE)
   for i in range(math.ceil(duration*30)):
    page.evaluate('(t)=>window.setTime(t)',i/30);process.stdin.write(page.screenshot(type='png'))
   process.stdin.close();assert process.wait()==0;browser.close()
  filt=f'[0:v]trim=duration={a.body_seconds},setpts=PTS-STARTPTS,scale=1080:1920,fps=30[v0];[1:v]scale=1080:1920,fps=30,setpts=PTS-STARTPTS[v1];[v0][v1]concat=n=2:v=1:a=0[v];[0:a]atrim=duration={a.body_seconds},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo[a0];[2:a]aresample=48000,aformat=channel_layouts=stereo,apad=pad_dur=0.15,atrim=duration={duration},asetpts=PTS-STARTPTS[a1];[a0][a1]concat=n=2:v=0:a=1,loudnorm=I=-14.5:TP=-1.5:LRA=11[a]'
  subprocess.run([ff,'-y','-loglevel','error','-i',str(a.input),'-i',str(v),'-i',str(a.voice),'-filter_complex',filt,'-map','[v]','-map','[a]','-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(a.output)],check=True)
 marker={'contract':'house-outro-assembly-v1','video_sha256':'sha256:'+hashlib.sha256(a.output.read_bytes()).hexdigest(),'voice_sha256':'sha256:'+hashlib.sha256(a.voice.read_bytes()).hexdigest(),'keyword':a.keyword.upper(),'outro_start':a.body_seconds,'outro_duration':duration,'note':'Assembly provenance, not audiovisual review or owner approval.'}
 a.output.with_suffix(a.output.suffix+'.outro-assembly.json').write_text(json.dumps(marker,indent=2)+'\n')
 print(f'Wrote {a.output}; narrated outro {duration:.2f}s. Review and QA required; no publishing.')
if __name__=='__main__':main()
