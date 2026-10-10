#!/usr/bin/env python3
"""Record the actual on-device Whistle sandbox using OUR approved narration file.
Never uses a user's microphone. Keep the transcript + timings as evidence.
"""
import json,time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=Path('/var/tmp/hypeless-whistle-demo');OUT.mkdir(exist_ok=True)
AUDIO='/var/tmp/hypeless-oct10-sources/demo-input.wav'
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream','--use-file-for-fake-audio-capture='+AUDIO])
 context=browser.new_context(viewport={'width':1280,'height':900},permissions=['microphone'],record_video_dir=str(OUT),record_video_size={'width':1280,'height':900})
 page=context.new_page();began=time.monotonic();events={}
 page.goto('https://cactuscompute.com/blog/whistle',wait_until='domcontentloaded',timeout=45000);page.wait_for_timeout(1800)
 start=page.get_by_role('button',name='Start recording',exact=True)
 start.scroll_into_view_if_needed()
 page.evaluate('window.scrollBy(0, -150)');page.wait_for_timeout(500)
 events['start_click']=time.monotonic()-began
 start.click()
 stop=page.get_by_role('button',name='Stop recording',exact=True)
 stop.wait_for(state='visible',timeout=60000)
 events['recording']=time.monotonic()-began
 print('Recording own Option-3 demo audio',flush=True)
 page.wait_for_timeout(9000)
 stop.click();events['stop_click']=time.monotonic()-began
 print('Stopped recording; waiting for on-device result',flush=True)
 page.wait_for_timeout(15000)
 # Save the real sandbox text, not an invented transcription.
 sandbox=page.get_by_text('Whistle sandbox',exact=True).locator('..').locator('..')
 text=sandbox.inner_text();print('Actual sandbox output:',text[:2000],flush=True)
 events['result']=time.monotonic()-began
 page.screenshot(path=str(OUT/'result.jpg'),type='jpeg',quality=94)
 page.wait_for_timeout(7000)
 raw_video=page.video.path()
 context.close();browser.close()
 (OUT/'evidence.json').write_text(json.dumps({'events_seconds':events,'source':'https://cactuscompute.com/blog/whistle','input':'8-second excerpt of our approved Option-3 Claude voiceover; fake-audio capture, not a user microphone','sandbox_text':text,'raw_video':str(raw_video)},indent=2)+'\n')
 print('Evidence saved',OUT,flush=True)
