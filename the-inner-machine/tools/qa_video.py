#!/usr/bin/env python3
"""Machine-readable final QA. Requires ffprobe; never trusts human-readable ffmpeg output."""
import argparse,json,os,subprocess,sys,hashlib,shutil,re

def probe(path):
 exe=shutil.which('ffprobe')
 if exe:
  r=subprocess.run([exe,'-v','error','-show_streams','-show_format','-of','json',path],capture_output=True,text=True)
  if r.returncode: raise RuntimeError(r.stderr[-500:])
  return json.loads(r.stdout)
 # imageio-ffmpeg often ships ffmpeg but not ffprobe in the sandbox. Keep the
 # gate fail-closed while providing a structured fallback from ffmpeg's probe.
 import imageio_ffmpeg
 r=subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-i',path],capture_output=True,text=True)
 text=r.stderr
 m=re.search(r'Duration: ([0-9:.]+)',text)
 dur=0.0
 if m:
  h,mi,se=m.group(1).split(':'); dur=float(h)*3600+float(mi)*60+float(se)
 streams=[]
 vm=re.search(r'Stream #.*Video: ([^, ]+).*?(\d{2,5})x(\d{2,5}).*?(\d+(?:\.\d+)?) fps',text)
 if vm: streams.append({'codec_type':'video','codec_name':vm.group(1),'width':int(vm.group(2)),'height':int(vm.group(3)),'r_frame_rate':str(vm.group(4))+'/1','sample_aspect_ratio':'1:1'})
 am=re.search(r'Stream #.*Audio: ([^, ]+)',text)
 if am: streams.append({'codec_type':'audio','codec_name':am.group(1)})
 if not streams: raise RuntimeError('could not parse ffmpeg probe output')
 return {'streams':streams,'format':{'duration':dur,'probe_fallback':True}}
def main():
 p=argparse.ArgumentParser(); p.add_argument('video'); p.add_argument('--kind',choices=['long','short'],default='long'); p.add_argument('--report',default=None); a=p.parse_args()
 errors=[]; warnings=[]
 try: x=probe(a.video)
 except Exception as e: print('FAIL:',e); return 1
 vs=[s for s in x['streams'] if s['codec_type']=='video']; au=[s for s in x['streams'] if s['codec_type']=='audio']
 if len(vs)!=1: errors.append(f'expected one video stream, got {len(vs)}')
 if len(au)!=1: errors.append(f'expected one audio stream, got {len(au)}')
 if vs:
  v=vs[0]; w,h=int(v.get('width',0)),int(v.get('height',0)); fps=v.get('r_frame_rate','')
  if a.kind=='long' and not (w>h and w/h>1.7): errors.append(f'long output is not 16:9 landscape: {w}x{h}')
  if a.kind=='short' and not (h>w and h/w>1.7): errors.append(f'short output is not 9:16 portrait: {w}x{h}')
  if v.get('sample_aspect_ratio') not in (None,'1:1'): errors.append('SAR is not 1:1')
  if fps not in ('30/1','24/1','25/1'): errors.append(f'unsupported fps {fps}')
 if au and au[0].get('codec_name') not in ('aac','opus','vorbis'): warnings.append('audio codec is unusual for YouTube delivery')
 dur=float(x.get('format',{}).get('duration',0) or 0)
 if dur < 30: errors.append(f'output is suspiciously short: {dur:.2f}s')
 result={'status':'pass' if not errors else 'fail','file':os.path.abspath(a.video),'kind':a.kind,'duration_s':dur,'streams':x.get('streams',[]),'errors':errors,'warnings':warnings}
 out=a.report or a.video+'.qa_report.json'; json.dump(result,open(out,'w'),indent=2)
 print(json.dumps({'status':result['status'],'duration_s':dur,'errors':errors,'warnings':warnings},indent=2))
 return 0 if not errors else 1
if __name__=='__main__': sys.exit(main())
