#!/usr/bin/env python3
"""Fresh public-page captures for shadow comparison. Run WITHOUT model/social keys.
No login, no site text edits, no invented UI. Capture failures are explicit holds.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.agent.evidence import safe_url
from tools.agent.openrouter_client import PilotBlocked
from tools.post.common import iso,now_utc,save_json


def clean_browser_env():
    keep=('PATH','HOME','LANG','LC_ALL','TMPDIR','DISPLAY','PLAYWRIGHT_BROWSERS_PATH','LD_LIBRARY_PATH')
    return {k:os.environ[k] for k in keep if k in os.environ}


def capture(case,work,browser):
    work=Path(work);assets=json.loads((work/'assets.json').read_text());captures=[]
    for source in case['sources']:
        if source['kind']!='primary_source':continue
        url=safe_url(source['url'],case['source_hosts'])
        context=browser.new_context(viewport={'width':1280,'height':900},device_scale_factor=1.5)
        page=context.new_page()
        try:
            # Block private/local requests even when initiated by page JavaScript.
            def route(req):
                p=urlparse(req.request.url)
                if p.scheme in ('data','blob'):req.continue_();return
                if p.scheme!='https' or not p.hostname or p.hostname in {'localhost','127.0.0.1','169.254.169.254'}:
                    req.abort();return
                req.continue_()
            page.route('**/*',route)
            page.goto(url,wait_until='domcontentloaded',timeout=45000)
            page.locator('h1').first.wait_for(timeout=15000)
            page.wait_for_timeout(1500)
            title=page.title()
            if any(x in title.lower() for x in ['access denied','just a moment','captcha']):raise PilotBlocked('Challenge page is not valid capture evidence')
            actual=safe_url(page.url,case['source_hosts'])
            for idx in range(min(2,page.locator('h1,h2').count())):
                element=page.locator('h1,h2').nth(idx);element.scroll_into_view_if_needed();page.wait_for_timeout(300)
                name=f'fresh-{source["id"]}-{idx}.jpg';path=work/'assets'/name
                page.screenshot(path=str(path),type='jpeg',quality=90)
                aid=f'fresh-{source["id"]}-{idx}'
                row={'id':aid,'file':name,'kind':'screenshot','digest':'sha256:'+hashlib.sha256(path.read_bytes()).hexdigest(),
                     'size_bytes':path.stat().st_size,'width':1920,'height':1350,'source_url':actual,'capture_date':iso(now_utc()),
                     'usage_basis':'Own public-page screenshot for non-publishing commentary comparison; no blanket rights grant.',
                     'description':title+'; actual page capture near '+element.inner_text()[:120],'newly_acquired_by_candidate':True}
                assets[aid]=row;captures.append(row)
        except Exception as exc:captures.append({'source_id':source['id'],'blocked':type(exc).__name__+': '+str(exc)[:180]})
        finally:context.close()
    save_json(work/'assets.json',assets);save_json(work/'fresh-captures.json',captures)
    return captures


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--work',required=True);a=ap.parse_args()
    if any(os.environ.get(k) for k in ['OPENROUTER_API_KEY','BUFFER_API_KEY','YOUTUBE_OAUTH_JSON']):
        raise SystemExit('Capture stage must not receive model/social credentials')
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage'],env=clean_browser_env())
        try:
            for path in sorted(Path(a.work).glob('*/case.json')):
                case=json.loads(path.read_text());rows=capture(case,path.parent,browser)
                print(case['id'],'fresh captures',sum('blocked' not in r for r in rows),flush=True)
        finally:browser.close()


if __name__=='__main__':main()
