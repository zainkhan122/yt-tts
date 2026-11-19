#!/usr/bin/env python3
"""Owner-approved direct Shorts: durable jobs, private-first delivery, safe retries.

One explicit submission reserves an exact asset, cover, brief and time. The cron
only resumes those reservations, never selects old queue entries automatically.
No Buffer writes. A conflicting Buffer/YouTube receipt stops the job.
"""
import argparse
import datetime as dt
import os
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from lib.secrets import redact
from tools.post.common import config, fingerprint, iso, load_json, now_utc, parse_time, valid_id
from tools.post.state import Journal
from tools.youtube.api import Deferred, Uncertain, YouTubeAPI, YouTubeError
from tools.youtube.direct_shorts import REMOTE, run, validate_request
from tools.youtube.metadata import get_video
from tools.youtube.runner import verify_publication
from tools import ship

JOB_FIELDS=('video_id','asset_digest','asset_size','asset_id','kit_asset_id','kit_digest',
            'brief_sha256','cover_sha256','approved_cover_sha','approved_panel_sha',
            'reviewed_at','expires_at','not_before','review','category','youtube_ai_generated','platforms','approval')


def pins(item):
    return fingerprint({k:item.get(k) for k in JOB_FIELDS})


def check_conflicts(vid, buffer_records, yt_data, *, existing_job=False):
    row=buffer_records.get(vid+':youtube') or {}
    if row and row.get('state') != 'deleted':
        raise ValueError('Existing Buffer YouTube receipt may publish or already be public; manual reconciliation required')
    for row in yt_data.get('enrichment',{}).values():
        if row.get('video_id')==vid:
            raise ValueError('Existing YouTube enrichment receipt; do not duplicate an older Short')
    record=yt_data.get('records',{}).get(vid)
    if record and not existing_job:
        raise ValueError('Existing direct YouTube receipt; do not create another video')


def check_time_conflicts(vid, due, buffer_records, yt_data):
    # Actual tracked channel schedules, not just the current candidate list.
    for key, row in buffer_records.items():
        if not key.endswith(':youtube') or key == vid+':youtube' or row.get('state') in {'deleted','cancelled','released'}:
            continue
        other=parse_time(row.get('due_at') or row.get('sent_at'))
        if other and abs((due-other).total_seconds()) < 1800:
            raise ValueError('YouTube slot conflicts with a tracked Buffer receipt')
    for other_id, row in yt_data.get('records',{}).items():
        if other_id == vid or row.get('state') in {'blocked','cancelled','publication_failed'}:
            continue
        other=parse_time(row.get('publish_at') or row.get('sent_at'))
        gap=1800 if row.get('kind') == 'direct_short' else 7200
        if other and abs((due-other).total_seconds()) < gap:
            raise ValueError('YouTube slot conflicts with another direct video')
    for other_id, job in yt_data.get('direct_short_jobs',{}).items():
        if other_id == vid or job.get('state') in {'cancelled','needs_review'}:
            continue
        other=parse_time(job.get('publish_at'))
        if other and abs((due-other).total_seconds()) < 1800:
            raise ValueError('YouTube slot conflicts with another reserved Short')


def reserve(item, brief, due, publications, journal, now, *, ship_errors=()):
    vid=valid_id(item['video_id'])
    if item.get('ship_legacy') or not item.get('approved_panel_sha'):
        raise ValueError('Current pinned panel approval is required; legacy exemptions cannot enter direct production')
    if ship_errors:
        raise ValueError('Ship approval gate failed: '+'; '.join(ship_errors))
    validate_request(item, brief, None, due, now)
    if due > now+dt.timedelta(days=14):
        raise ValueError('Schedule exceeds 14-day planning horizon')
    jobs=journal.data.setdefault('direct_short_jobs',{})
    existing=jobs.get(vid)
    check_conflicts(vid,publications.records,journal.data,existing_job=bool(existing))
    check_time_conflicts(vid,due,publications.records,journal.data)
    if existing:
        if existing.get('pins') != pins(item) or parse_time(existing.get('publish_at')) != due:
            raise ValueError('Existing direct job differs in approved pins/time; manual review required')
        return existing
    job={'video_id':vid,'pins':pins(item),'publish_at':iso(due),'state':'pending',
         'created_at':iso(now),'attempts':0}
    jobs[vid]=job
    journal.save('reserve approved direct Short '+vid)
    return job


def execute_job(job,item,brief,publications,journal,api,root_cfg,work,clock=now_utc):
    vid=job['video_id']
    if pins(item)!=job.get('pins'):
        raise ValueError('Approved queue pins changed after reservation; hold')
    check_conflicts(vid,publications.records,journal.data,existing_job=True)
    if job['state'] in {'sent','needs_review','cancelled'}:
        return job['state']
    if job['state'] == 'pending':
        check_time_conflicts(vid,parse_time(job['publish_at']),publications.records,journal.data)
    rec=journal.records.get(vid) or {}
    if job['state']=='scheduled':
        if not rec.get('youtube_id'):
            raise ValueError('Scheduled job missing YouTube receipt')
        video=get_video(api,rec['youtube_id'])
        verify_publication(rec,video,journal,clock=clock)
        if rec.get('state')=='sent':
            job.update(state='sent',sent_at=rec.get('sent_at'));journal.save('direct Short confirmed public '+vid)
        elif rec.get('state')=='publication_failed':
            job.update(state='needs_review',last_error=rec.get('last_error'));journal.save('direct Short publication failure '+vid)
        elif parse_time(video.get('status',{}).get('publishAt')) != parse_time(job['publish_at']):
            job.update(state='needs_review',last_error='YouTube schedule missing or changed');journal.save('direct Short schedule changed '+vid)
        return job['state']
    if parse_time(job.get('retry_at')) and parse_time(job['retry_at']) > clock():
        return 'retry_wait'
    due=parse_time(job['publish_at'])
    try:
        result=run(item,brief,None,due,api,journal,root_cfg,work,clock=clock)
        if result.get('state')!='scheduled':
            raise ValueError('Direct workflow did not confirm scheduling')
        job.update(state='scheduled',youtube_id=result['youtube_id'],scheduled_at=iso(clock()))
        job.pop('retry_at',None);job.pop('last_error',None);journal.save('direct Short job scheduled '+vid)
    except Deferred as exc:
        rec=journal.records.get(vid) or {}
        # Explicit rate/quota rejection means no session was accepted; unlike a
        # lost response it is safe to reserve a fresh session on a later run.
        if (rec.get('state') == 'session_start_uncertain' and not rec.get('session_ciphertext')
                and exc.code in {'RATE_LIMIT','QUOTA_EXCEEDED','QUOTA_BUDGET','UPLOAD_BUDGET','UPLOAD_LIMIT','TOKEN_RATE'}):
            rec['state']='queued'
        if exc.code in {'TRANSFER_RETRY','NO_PROGRESS','NETWORK','SERVER'}:
            job['attempts']=job.get('attempts',0)+1
            if job['attempts'] >= 4:
                job.update(state='needs_review',last_error=redact(str(exc)),error_code=exc.code)
                journal.save('direct Short retry cap '+vid)
                return job['state']
        job.update(state='pending',retry_at=iso(clock()+dt.timedelta(seconds=max(300,exc.wait_seconds))),
                   last_error=redact(str(exc)),error_code=exc.code)
        journal.save('direct Short deferred '+vid)
    except (Uncertain,YouTubeError,ValueError) as exc:
        job.update(state='needs_review',last_error=redact(str(exc)),error_code=getattr(exc,'code','VALIDATION'))
        journal.save('direct Short held for review '+vid)
    finally:
        shutil.rmtree(work,ignore_errors=True)
    return job['state']


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--mode',choices=['submit','resume','check'],required=True)
    ap.add_argument('--video-id');ap.add_argument('--publish-at')
    args=ap.parse_args()
    if args.mode=='check':
        print('Direct Shorts production entrypoint ready; no mutations made.')
        return 0
    if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('ALLOW_DIRECT_SHORT_MUTATIONS')!='true':
        raise SystemExit('Direct Shorts writes require the authorized Actions workflow')
    cfg,root_cfg=load_json(ROOT/'config/youtube.json'),config()
    if not cfg.get('enabled'):
        raise SystemExit('YouTube kill switch is off')
    publications=Journal(root_cfg,remote=True)
    journal=Journal(root_cfg,remote=True,path=ROOT/'tracker/youtube-publications.json',remote_path=REMOTE)
    items={i['video_id']:i for i in load_json(ROOT/'queue/publish.json')['items']}
    if args.mode=='submit':
        if not args.video_id or not args.publish_at: raise ValueError('Exactly one selected video and future timestamp are required')
        vid=valid_id(args.video_id)
        if vid not in items: raise ValueError('Selected video not in approved queue')
        item=items[vid];brief=load_json(ROOT/'briefs'/(vid+'.json'))
        due=parse_time(args.publish_at)
        if not due: raise ValueError('Timestamp must include a timezone')
        reserve(item,brief,due,publications,journal,now_utc(),ship_errors=ship.check(vid,root=ROOT))
        selected=[vid]
    else:
        if args.video_id or args.publish_at: raise ValueError('Resume only uses previously reserved jobs')
        selected=[k for k,v in journal.data.get('direct_short_jobs',{}).items() if v.get('state') in {'pending','scheduled'}]
    if not selected:
        print('No reserved direct Shorts to process.');return 0
    api=YouTubeAPI(cfg,journal);api.verify_channel()
    # Reconcile any scheduled jobs; process at most one pending job per invocation.
    pending_processed=False;failed=False
    for vid in selected:
        job=journal.data['direct_short_jobs'][vid]
        if job['state']=='pending' and pending_processed: continue
        if job['state']=='pending': pending_processed=True
        if vid not in items:
            job.update(state='needs_review',last_error='Approved queue item missing');journal.save('direct Short item missing');failed=True;continue
        item=items[vid]
        try:
            errors=ship.check(vid,root=ROOT)
            if errors: raise ValueError('Ship approval gate failed: '+'; '.join(errors))
            brief=load_json(ROOT/'briefs'/(vid+'.json'))
            state=execute_job(job,item,brief,publications,journal,api,root_cfg,Path(os.environ['RUNNER_TEMP'])/'direct-shorts'/vid)
            print(vid,state)
            if state=='needs_review':failed=True
        except ValueError as exc:
            job.update(state='needs_review',last_error=redact(str(exc)));journal.save('direct Short held '+vid)
            print(vid,'ERROR',redact(str(exc)));failed=True
        except Exception as exc:
            # Journal/network uncertainty: stop, never attempt another write here.
            print(vid,'ERROR',redact(str(exc)));return 1
    return 1 if failed else 0

if __name__=='__main__':sys.exit(main())
