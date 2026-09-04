#!/usr/bin/env python3
"""Validate title/description/packaging basics before upload."""
import argparse,json,sys

def main():
 ap=argparse.ArgumentParser();ap.add_argument('metadata');ap.add_argument('--kind',choices=['auto','long','short'],default='auto');a=ap.parse_args();d=json.load(open(a.metadata));e=[];w=[]
 kind='short' if (a.kind=='short' or (a.kind=='auto' and 'shorts' in a.metadata.lower())) else 'long'
 required=('title_options','recommended_title','description','hashtags','tags','pinned_comment','disclosure','disclaimer')
 if kind=='long': required=required+('chapters',)
 for k in required:
  if not d.get(k): e.append('missing '+k)
 title=d.get('recommended_title','')
 if len(title)>60:e.append(f'title is {len(title)} chars (>60)')
 if len(d.get('description',''))<200:e.append('description under 200 characters')
 title_words=[x.lower().strip('?!.,') for x in title.split() if len(x.strip('?!.,'))>=5]
 if title_words and not any(x in d.get('description','').lower() for x in title_words):e.append('primary topic absent from description')
 if not (2<=len(d.get('hashtags',[]))<=5):e.append('hashtags must be 2–5')
 if len(d.get('tags',[]))>15:w.append('more than 15 backend tags; reduce unless necessary')
 if kind=='long' and len(d.get('chapters',[]))<3:e.append('fewer than 3 chapters')
 if kind=='short' and '#Shorts' not in d.get('hashtags',[]):e.append('Short metadata must include #Shorts')
 print(json.dumps({'status':'pass' if not e else 'fail','title':title,'title_chars':len(title),'description_chars':len(d.get('description','')),'errors':e,'warnings':w},indent=2));return 0 if not e else 1
if __name__=='__main__':sys.exit(main())
