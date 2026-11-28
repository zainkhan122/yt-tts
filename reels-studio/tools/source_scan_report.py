#!/usr/bin/env python3
"""Build a source-by-source audit from recent_social_scan.py JSON (read-only)."""
import argparse, json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('--output',required=True);p.add_argument('--recent',type=int,default=10);a=p.parse_args()
j=json.loads(Path(a.input).read_text());lines=[f"# Source audit — {j['target_date']} ({j['target_timezone']})",'',f"Scan machine clock: {j['observed_at_utc']}. Target UTC window: {j['target_start_utc']} to {j['target_end_utc_exclusive']} (exclusive).",'','**Clock warning:** The scan host clock must be checked against the trusted current date. A calendar-day match does not prove a video was already public at the real current time.','', 'Counts and metrics are observations from the scan, not historical counts. Unknown publication times remain unknown; no match does not mean no posts. Listings may be truncated.','', '## Source coverage','', '| Platform | Source | Listed | Exact target-day matches | Undated | Limit hit | Errors |','|---|---|---:|---:|---:|---|---:|']
for r in j['results']:
 posts=r['posts'];lines.append(f"| {r['type']} | {r['source']} | {len(posts)} | {sum(x.get('target_day_status')=='match' for x in posts)} | {sum(not x.get('published_utc') for x in posts)} | {'yes' if r['limit_reached'] else 'no'} | {len(r['errors'])} |")
lines+=['','## Exact target-day matches','']
for r in j['results']:
 for q in r['posts']:
  if q.get('target_day_status')=='match':
   title=(q.get('title') or '[untitled]').replace('|','\\|').replace('\n',' ')
   lines.append(f"- **{r['source']}** — {q['published_target_timezone']} — [{title}]({q['url']}) — views {q.get('views') if q.get('views') is not None else 'unknown'}; likes {q.get('likes') if q.get('likes') is not None else 'unknown'}; duration {q.get('duration_seconds') if q.get('duration_seconds') is not None else 'unknown'} seconds; timestamp: {q.get('timestamp_source')}.")
lines+=['','## Recent listings by source','',f'First {a.recent} entries per source as returned by the platform. These are **not necessarily from the target day**; missing timestamps are explicitly marked unknown. Full metadata for every retrieved entry is in the JSON file.','']
for r in j['results']:
 lines += [f"### {r['type']} · {r['source']}",'']
 if not r['posts']: lines.append('No entries retrieved; see errors in JSON.')
 for q in r['posts'][:a.recent]:
  title=(q.get('title') or '[untitled]').replace('\n',' ');stamp=q.get('published_target_timezone') or 'publication timestamp unknown';lines.append(f"- [{title}]({q['url']}) — {stamp}; views: {q.get('views') if q.get('views') is not None else 'unknown'}; likes: {q.get('likes') if q.get('likes') is not None else 'unknown'}; duration: {q.get('duration_seconds') if q.get('duration_seconds') is not None else 'unknown'} seconds.")
 lines.append('')
Path(a.output).write_text('\n'.join(lines),encoding='utf-8')
