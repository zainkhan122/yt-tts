"""Place the reviewed 9:16 cover in decoded video frame zero, without retiming audio.

A one-frame card avoids hiding the spoken hook; the moving scene begins on frame 1.
Platforms choose their own previews; embedding frame zero does not guarantee selection.
"""
from pathlib import Path
import subprocess
import tempfile
from PIL import Image, ImageChops, ImageStat


def embed(video, cover):
    video, cover = Path(video), Path(cover)
    with Image.open(cover) as image:
        if image.size != (1080, 1920):
            raise ValueError('Dedicated cover must be exactly 1080x1920')
    with tempfile.TemporaryDirectory(prefix='cover-frame-') as tmp:
        encoded=Path(tmp)/'with-cover.mp4'; frame=Path(tmp)/'frame.png'
        cmd=['ffmpeg','-y','-v','error','-i',str(video),'-loop','1','-framerate','30','-i',str(cover),
             '-filter_complex',"[0:v][1:v]overlay=0:0:shortest=1:enable='eq(n,0)'[v]",
             '-map','[v]','-map','0:a?','-c:v','libx264','-preset','medium','-crf','18',
             '-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',str(encoded)]
        subprocess.run(cmd,check=True,timeout=1800)
        subprocess.run(['ffmpeg','-y','-v','error','-i',str(encoded),'-frames:v','1',str(frame)],check=True,timeout=120)
        with Image.open(cover) as a, Image.open(frame) as b:
            a=a.convert('RGB').resize((270,480));b=b.convert('RGB').resize((270,480))
            mae=sum(ImageStat.Stat(ImageChops.difference(a,b)).mean)/3
        if mae > 10:
            raise RuntimeError(f'Decoded frame 0 differs from approved cover (mean error {mae:.2f})')
        video.write_bytes(encoded.read_bytes())
        return {'cover_frame':0,'decoded_mean_abs_rgb_error':round(mae,3),'cover_hold_seconds':round(1/30,4)}
