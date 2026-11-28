"""Explicitly authorized browser interaction recording, not screenshot animation.

The caller supplies site, selectors, actions, and observable postconditions;
this is not a generic autonomous browser agent. Screens can contain sensitive
information; use only approved demo sites and review artifacts before sharing.
"""
from __future__ import annotations
import json, time, hashlib
from pathlib import Path
from urllib.parse import urlsplit

class ScreenDemoError(RuntimeError):pass

def _loc(page,frame_url,selector):
    frames=[f for f in page.frames if frame_url in f.url]
    if len(frames)!=1:raise ScreenDemoError('Frame missing or ambiguous')
    loc=frames[0].locator(selector)
    if loc.count()!=1:raise ScreenDemoError('Target missing or ambiguous')
    return loc

def record(url,actions,output,*,allowed_hosts,viewport=(1280,900)):
    from playwright.sync_api import sync_playwright
    parsed=urlsplit(url)
    if parsed.scheme!='https' or parsed.hostname not in allowed_hosts:raise ScreenDemoError('Site not explicitly authorized')
    if not actions or len(actions)>20:raise ScreenDemoError('One to twenty actions required')
    output=Path(output);output.mkdir(parents=True,exist_ok=True);receipt={'source_url':url,'mode':'real_browser_demo','scope':'demo data; not a physical device','actions':[],'status':'running'}
    with sync_playwright() as p:
        browser=p.chromium.launch(args=['--no-sandbox']);ctx=browser.new_context(viewport={'width':viewport[0],'height':viewport[1]},record_video_dir=str(output),record_video_size={'width':viewport[0],'height':viewport[1]})
        page=ctx.new_page();page.goto(url,wait_until='domcontentloaded',timeout=60000);page.wait_for_timeout(2500);start=time.monotonic();video=page.video
        try:
            for i,a in enumerate(actions):
                if set(a)!={'operation','frame_url','selector','destination','value','observe_selector','observe_attribute','expected_before','expected_after'}:raise ScreenDemoError('Invalid action schema')
                if a['operation'] not in {'click','fill','drag','navigate'}:raise ScreenDemoError('Unsupported operation')
                target=_loc(page,a['frame_url'],a['selector']);watch=_loc(page,a['frame_url'],a['observe_selector']);before=watch.get_attribute(a['observe_attribute'])
                if before!=a['expected_before']:raise ScreenDemoError('Unexpected before state')
                box=target.bounding_box()
                if not box or not target.is_visible():raise ScreenDemoError('Target not visible')
                pt={'x':box['x']+box['width']/2,'y':box['y']+box['height']/2}
                page.screenshot(path=str(output/f'{i:02d}-before.png'));page.mouse.move(pt['x'],pt['y'],steps=12);page.wait_for_timeout(350);at=time.monotonic()-start
                if a['operation']=='click':page.mouse.click(pt['x'],pt['y'])
                elif a['operation']=='fill':target.fill(a['value'])
                elif a['operation']=='drag':
                    dest=_loc(page,a['frame_url'],a['destination']);end=dest.bounding_box()
                    if not end:raise ScreenDemoError('Drag destination is not visible')
                    page.mouse.down();page.mouse.move(end['x']+end['width']/2,end['y']+end['height']/2,steps=25);page.mouse.up()
                else:
                    dest=urlsplit(a['destination'])
                    if dest.scheme!='https' or dest.hostname not in allowed_hosts:raise ScreenDemoError('Navigation host not authorized')
                    page.goto(a['destination'],wait_until='domcontentloaded',timeout=60000)
                page.wait_for_timeout(900);after=_loc(page,a['frame_url'],a['observe_selector']).get_attribute(a['observe_attribute']);page.screenshot(path=str(output/f'{i:02d}-after.png'))
                if after!=a['expected_after'] or after==before:raise ScreenDemoError('Expected state transition not observed')
                receipt['actions'].append({'operation':a['operation'],'time_from_page_ready_s':round(at,3),'cursor':pt,'before':before,'after':after,'verified':True,'before_image':f'{i:02d}-before.png','after_image':f'{i:02d}-after.png'})
            page.wait_for_timeout(800);receipt['status']='observed'
        finally:
            ctx.close();browser.close()
            if video:
                src=Path(video.path());target=output/'recording.webm'
                if src!=target:src.replace(target)
                receipt['recording']=str(target);receipt['sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
            (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt
