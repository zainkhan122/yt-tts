#!/usr/bin/env python3
"""Measure the cover against decoded video frame zero and bind design provenance.

Run after making purpose-made artwork, rendering a cover, embedding it at frame
zero, and inspecting both. This does not generate artwork or set a YouTube cover.
"""
import argparse,datetime,hashlib,io,json,re,subprocess,sys
from pathlib import Path
from PIL import Image,ImageChops,ImageStat
import imageio_ffmpeg
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return 'sha256:'+h.hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--id',required=True);p.add_argument('--video',type=Path,required=True);p.add_argument('--cover',type=Path,required=True);p.add_argument('--art',type=Path,required=True);p.add_argument('--headline',required=True)
 p.add_argument('--confirm-purpose-made',action='store_true',required=True)
 a=p.parse_args()
 if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{2,80}',a.id):p.error('bad id')
 if not a.headline.strip() or len(a.headline)>80:p.error('headline required')
 with Image.open(a.cover) as im:
  if im.size!=(1080,1920) or im.format not in ('JPEG','PNG'):raise SystemExit('Cover must be a 1080x1920 JPEG/PNG')
  cover=im.convert('RGB')
 with Image.open(a.art) as im: im.verify()
 proc=subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-i',str(a.video),'-frames:v','1','-f','image2pipe','-vcodec','png','-'],capture_output=True,check=True)
 frame=Image.open(io.BytesIO(proc.stdout)).convert('RGB')
 if frame.size!=cover.size:raise SystemExit('Video dimensions differ from cover')
 error=sum(ImageStat.Stat(ImageChops.difference(frame,cover)).mean)/3
 if error>6:raise SystemExit(f'Cover differs from decoded first frame (mean absolute RGB error {error:.2f})')
 rec={'contract':'dedicated-cover-v1','video_id':a.id,'video_sha256':digest(a.video),'cover_sha256':digest(a.cover),'art_sha256':digest(a.art),'source_kind':'purpose-made-for-this-video','headline':a.headline,'dimensions':[1080,1920],'frame_zero_verified':True,'frame_zero_mean_abs_rgb_error':round(error,3),'reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'note':'Source artwork was created specifically for this video; pixel check compares cover to decoded frame zero, not any platform thumbnail surface.'}
 out=ROOT/'research/production/cover-receipts'/(a.id+'.json');out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(rec,indent=2)+'\n');print('Saved',out,'frame-zero error',round(error,3))
if __name__=='__main__':main()
