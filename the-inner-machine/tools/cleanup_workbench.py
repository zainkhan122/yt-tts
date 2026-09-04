#!/usr/bin/env python3
"""Clean temporary intermediates without deleting active episode media."""
import argparse,os,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--max-mb',type=int,default=100); a=ap.parse_args(); removed=[]
 protected_media={'.mp4','.jpg','.jpeg','.png'}
 for p in ROOT.rglob('*'):
  if not p.is_file(): continue
  is_render_work = any(str(q).endswith(('.mp4.work','.render_work')) for q in p.parents) or str(p).endswith('.mp4.work')
  is_active_media=p.suffix.lower() in protected_media and 'plan' in p.parts and not is_render_work
  if (p.suffix.lower() in {'.wav','.mp3','.m4a','.opus','.flac','.zip','.part'} or any(x in p.parts for x in {'.work','.render_work','__pycache__'}) or is_render_work) and not is_active_media:
   try: removed.append((p.stat().st_size,p)); p.unlink()
   except FileNotFoundError: pass
 for p in sorted(ROOT.rglob('__pycache__'),reverse=True):
  if p.is_dir(): shutil.rmtree(p,ignore_errors=True)
 size=sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())
 print(f'workspace={size/1024/1024:.1f}MB limit={a.max_mb}MB removed={len(removed)} files')
 if size>a.max_mb*1024*1024: raise SystemExit('FAIL: active media must be archived to the channel repo before heavy work')
 print('PASS: safe for heavy work')
if __name__=='__main__': main()
