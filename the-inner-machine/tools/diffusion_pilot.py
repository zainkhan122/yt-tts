#!/usr/bin/env python3
"""Emit a Diffusion Studio JSX pilot from a beat manifest.

This is an authoring adapter, not the final renderer. It keeps our JSON manifest as
source-of-truth and emits explicit scene timing plus optional selective emphasis.
Run in an installed Diffusion Studio project with dapi open/export.
"""
import argparse,json
from pathlib import Path

def esc(s): return s.replace('\\','\\\\').replace('"','\\"')
def main():
 p=argparse.ArgumentParser();p.add_argument('manifest');p.add_argument('out');a=p.parse_args();m=json.loads(Path(a.manifest).read_text());shots=m[:3] if isinstance(m,list) else m['shots'][:3]
 t=0.;nodes=[]
 for i,s in enumerate(shots):
  dur=float(s.get('duration_s',4.0)); img=s.get('img') or s.get('image'); overlay=(s.get('overlay') or '').strip();
  nodes.append(f'        <image id="beat_{i+1:02d}" src="{esc(img)}" x={{0}} y={{0}} width={{1920}} height={{1080}} start={{{t:.3f}}} end={{{t+dur:.3f}}} />')
  if overlay:
   nodes.append(f'        <text id="emphasis_{i+1:02d}" width={{1920}} height={{1080}} textAlign="center" textBaseline="middle" fontSize={{112}} fontWeight="bold" color="#E0A458" start={{{t+dur*.35:.3f}}} end={{{t+dur*.75:.3f}}}>{esc(overlay)}</text>')
  t+=dur
 out='''/* @jsxImportSource @diffusionstudio/jsx */\n// Generated pilot: selective emphasis only; blank beats have no text node.\nexport default function VideoPilot() {\n  return (\n    <stage>\n      <scene name="Pilot" width={1920} height={1080} fill="#10122E" active>\n'''+"\n".join(nodes)+f'''\n        <audio id="narration" src="narration.wav" start={{0}} end={{{t:.3f}}} />\n      </scene>\n    </stage>\n  );\n}}\n'''
 Path(a.out).write_text(out);print(f'WROTE {a.out} duration={t:.3f}s beats={len(shots)}')
if __name__=='__main__':main()
