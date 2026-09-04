#!/usr/bin/env python3
"""Fail-closed gate for selective kinetic emphasis overlays."""
import argparse,json,re,sys
p=argparse.ArgumentParser();p.add_argument('shots');p.add_argument('--max-overlays',type=int,default=15);a=p.parse_args();s=json.load(open(a.shots));e=[];over=[x for x in s if x.get('overlay','').strip()]
if len(over)>a.max_overlays:e.append(f'too many overlays: {len(over)} > {a.max_overlays}; kinetic emphasis must be selective')
for i,x in enumerate(over):
 t=x['overlay'].strip()
 if len(t.split())>3:e.append(f'beat {i+1}: overlay has more than 3 words: {t}')
 if re.search(r'[^A-Z0-9 ]',t):e.append(f'beat {i+1}: overlay contains punctuation or lowercase: {t}')
 if x.get('overlay')==x.get('text'):e.append(f'beat {i+1}: overlay duplicates narration')
r={'status':'pass' if not e else 'fail','beats':len(s),'overlay_beats':len(over),'text_free_beats':len(s)-len(over),'errors':e};print(json.dumps(r,indent=2));sys.exit(bool(e))
