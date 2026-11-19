import tempfile
import unittest
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw
from lib.cover_frame import embed

class CoverFrameTest(unittest.TestCase):
    def test_first_frame_is_cover_and_second_is_video(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);video=p/'video.mp4';cover=p/'cover.jpg';end=p/'second.png'
            im=Image.new('RGB',(1080,1920),'#f5e9d2'); ImageDraw.Draw(im).rectangle((80,100,950,500),fill='#553db9'); im.save(cover)
            subprocess.run(['ffmpeg','-y','-v','error','-f','lavfi','-i','color=c=blue:s=1080x1920:r=30:d=0.2','-c:v','libx264','-preset','ultrafast','-pix_fmt','yuv420p',str(video)],check=True)
            result=embed(video,cover);self.assertEqual(result['cover_frame'],0)
            subprocess.run(['ffmpeg','-y','-v','error','-i',str(video),'-vf','select=eq(n\\,1)','-frames:v','1',str(end)],check=True)
            with Image.open(end) as x:
                r,g,b=x.convert('RGB').getpixel((500,500));self.assertGreater(b,r+50)
    def test_rejects_wrong_cover_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'small.jpg';Image.new('RGB',(400,400)).save(p)
            with self.assertRaises(ValueError): embed(Path(tmp)/'v.mp4',p)
if __name__=='__main__': unittest.main()
