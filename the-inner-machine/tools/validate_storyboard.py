#!/usr/bin/env python3
"""Fail-closed storyboard gate for one sentence/one visual beat."""
import argparse,json,os,sys

def main():
 p=argparse.ArgumentParser(); p.add_argument('shots'); p.add_argument('--assets',required=True); a=p.parse_args(); errs=[]
 shots=json.load(open(a.shots)); manifest=json.load(open(a.assets)); amap={x['path']:x for x in manifest['assets']}
 if not shots: errs.append('empty storyboard')
 ids=[]; uses={}
 for i,s in enumerate(shots):
  for k in ('kf','caption','narration','motion','sentence_id'):
   if not s.get(k): errs.append(f'beat {i}: missing {k}')
  if s.get('sentence_id') in ids: errs.append(f'beat {i}: duplicate sentence_id')
  ids.append(s.get('sentence_id'))
  if s.get('kf') not in amap: errs.append(f'beat {i}: asset absent from manifest: {s.get("kf")}')
  else:
   f=os.path.join(os.path.dirname(a.assets),s['kf'])
   if not os.path.exists(f): errs.append(f'beat {i}: asset file missing: {s["kf"]}')
  uses[s.get('kf')]=uses.get(s.get('kf'),0)+1
  if i and s.get('kf')==shots[i-1].get('kf'): errs.append(f'beat {i}: consecutive asset reuse')
  if i and s.get('motion')==shots[i-1].get('motion'): errs.append(f'beat {i}: repeated motion')
 if len(ids)!=len(set(ids)): errs.append('sentence IDs are not unique')
 for k,n in uses.items():
  if n>1: errs.append(f'asset reused across sentence beats ({n} uses; required 1): {k}')
 unused=[k for k in amap if k not in uses]
 if unused: errs.append('manifest assets unused: '+', '.join(unused))
 result={'status':'pass' if not errs else 'fail','beats':len(shots),'unique_assets':len(uses),'max_asset_uses':max(uses.values()) if uses else 0,'unused_assets':unused,'errors':errs}
 out=os.path.join(os.path.dirname(a.shots),'storyboard_qa.json'); json.dump(result,open(out,'w'),indent=2)
 print(json.dumps(result,indent=2)); return 0 if not errs else 1
if __name__=='__main__': sys.exit(main())
