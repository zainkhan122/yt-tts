#!/usr/bin/env python3
"""Fail-closed validation for The Inner Machine project packages."""
import argparse,json,os,sys

def fail(msg): print('FAIL:',msg); return 1

def main():
 p=argparse.ArgumentParser(); p.add_argument('project'); a=p.parse_args()
 base=os.path.dirname(os.path.abspath(a.project)); errs=[]
 try: c=json.load(open(a.project))
 except Exception as e: return fail(f'invalid JSON: {e}')
 for k in ('title','format','beats','voice'): 
  if k not in c: errs.append(f'missing {k}')
 f=c.get('format',{})
 if f.get('w',0) < f.get('h',0): errs.append('long-form must be landscape 16:9; portrait belongs only in shorts')
 if f.get('fps') not in (24,25,30): errs.append('fps must be 24, 25 or 30')
 beats=c.get('beats',[])
 if not 60 <= len(beats) <= 180: print(f'WARN: {len(beats)} beats; normal 6–9 minute package is usually substantially larger than a demo')
 seen=[]
 for i,b in enumerate(beats):
  for k in ('kf','narration','caption','motion'): 
   if not b.get(k): errs.append(f'beat {i}: missing {k}')
  if b.get('kf') and not os.path.exists(os.path.join(base,b['kf'])): errs.append(f'beat {i}: missing asset {b["kf"]}')
  if b.get('caption','') == c.get('title'): print(f'WARN: beat {i} caption repeats full title')
  seen.append(b.get('kf'))
  if i and b.get('kf') == beats[i-1].get('kf'): errs.append(f'beat {i}: consecutive asset reuse')
 if len(set(seen)) != len(seen): errs.append('asset reuse detected: every sentence beat requires its own distinct visual asset')
 if errs:
  for e in errs: print(' -',e)
  return 1
 print(f'PASS: {c["title"]} | landscape {f.get("w")}x{f.get("h")} @ {f.get("fps")}fps | {len(beats)} beats | {len(set(seen))} assets')
 return 0
if __name__=='__main__': sys.exit(main())
