import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
TOOL=ROOT/'tools/one_go_review.py'

class ReviewCoverPreflight(unittest.TestCase):
    def test_requires_cover_and_art_before_any_voice_dispatch(self):
        p=subprocess.run([sys.executable,str(TOOL),'--id','demo','--script','x','--renderer','x'],capture_output=True,text=True)
        self.assertNotEqual(p.returncode,0)
        self.assertIn('--cover',p.stderr)
        self.assertIn('--art',p.stderr)
    def test_rejects_missing_cover_before_voice_dispatch(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            d=Path(tmp); script=d/'script.json';script.write_text('["Hello"]')
            renderer=d/'renderer.py';renderer.write_text('pass')
            p=subprocess.run([sys.executable,str(TOOL),'--id','demo','--script',str(script),'--renderer',str(renderer),'--video',str(d/'out.mp4'),'--cover',str(d/'missing.jpg'),'--art',str(d/'missing.png')],capture_output=True,text=True)
            self.assertNotEqual(p.returncode,0)
            self.assertIn('valid purpose-made art and cover required',p.stderr)
    def test_rejects_existing_output(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            d=Path(tmp); script=d/'script.json';script.write_text('["Hello"]')
            renderer=d/'renderer.py';renderer.write_text('pass');out=d/'out.mp4';out.write_bytes(b'old')
            cover=d/'cover.jpg';art=d/'art.png'
            Image.new('RGB',(1080,1920),'white').save(cover);Image.new('RGB',(10,10),'red').save(art)
            p=subprocess.run([sys.executable,str(TOOL),'--id','demo','--script',str(script),'--renderer',str(renderer),'--video',str(out),'--cover',str(cover),'--art',str(art)],capture_output=True,text=True)
            self.assertNotEqual(p.returncode,0);self.assertIn('output video already exists',p.stderr);self.assertEqual(out.read_bytes(),b'old')
if __name__=='__main__': unittest.main()
