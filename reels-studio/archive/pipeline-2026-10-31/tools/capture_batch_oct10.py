#!/usr/bin/env python3
"""Own-source browser captures for the 2026-10-10 batch. No logins/credentials.
Heavy intermediates live in /var/tmp; curated packs are archived before pruning.
"""
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.parse

import requests
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
SPECS=[
 ('news-haiku-55-01','https://www.anthropic.com/claude-haiku-5-5', [('pricing','h2','Pricing'),('performance','h2','Performance')]),
 ('news-gemini-agent-01','https://cloud.google.com/blog/products/ai-machine-learning/welcome-to-gemini-at-work-2026', [('agent','h3','Introducing the Gemini agent'),('governance','h3','Securing and governing agents')]),
 ('tool-mosa-01','https://getmosa.ai/', [('canvas','h2','Bring every piece'),('costs','h3','Predictable')]),
 ('tool-pomelli-01','https://blog.google/innovation-and-ai/models-and-research/google-labs/pomelli-photoshoot/', [('how','h2','Generate professional'),('edit','h3','Improved image generation')]),
 ('repo-whistle-01','https://cactuscompute.com/blog/whistle', [('benchmarks','h2','Benchmarks'),('start','h2','Get started')])]


def slug(value):return re.sub(r'[^a-z0-9]+','-',value.lower()).strip('-')[:40]


def register(m,path,kind,source,css_width=None):
    try:
        with Image.open(path) as im:px=list(im.size)
    except Exception:px=None
    data={'file':path.name,'kind':kind,'source':source}
    if px:data['px']=px
    if css_width:data.update(css_width=css_width,scale=px[0]/css_width)
    m['files'][path.stem]=data


def contact(pack):
    images=[p for p in pack.glob('*.jpg') if p.name!='contact.jpg'][:12]
    w,h=420,290
    out=Image.new('RGB',(w*3, (h+32)*((len(images)+2)//3)), '#10182b')
    d=ImageDraw.Draw(out)
    font=ImageFont.truetype(str(ROOT/'templates/_base/fonts/Inter.ttf'),15)
    for i,p in enumerate(images):
        with Image.open(p) as im:
            im=im.convert('RGB');im.thumbnail((w-12,h-8))
            x=(i%3)*w;y=(i//3)*(h+32)
            out.paste(im,(x+(w-im.width)//2,y+30))
            d.text((x+8,y+7),p.name[:45],font=font,fill='white')
    out.save(pack/'contact.jpg',quality=86)


def capture(browser,spec):
    vid,url,sections=spec
    pack=ROOT/'captures'/vid;pack.mkdir(parents=True,exist_ok=True)
    context=browser.new_context(viewport={'width':1280,'height':900},device_scale_factor=1.5)
    page=context.new_page()
    try:
        for n in range(3):
            try:
                page.goto(url,wait_until='domcontentloaded',timeout=45000)
                page.locator('h1').first.wait_for(timeout=15000)
                page.wait_for_timeout(2500)
                if any(t in page.title().lower() for t in ['access denied','just a moment','forbidden']):raise ValueError('blocked page')
                break
            except Exception:
                if n==2:raise
                time.sleep(3+n*3)
        for label in ['Decline','Reject all','Only necessary']:
            try:
                button=page.get_by_role('button',name=label,exact=True)
                if button.count() and button.first.is_visible():button.first.click(timeout=1500)
            except Exception:pass
        # Fonts/layout before camera-coordinate measurement.
        page.evaluate('document.fonts.ready')
        page.evaluate('window.scrollTo(0,0)');page.wait_for_timeout(500)
        m={'id':vid,'url':url,'captured':'2026-10-10','facts':{},'files':{},'regions_css':{},
           'credits':['Own page captures; original media belongs to the named product maker. Credits belong in descriptions, not on-screen.'],
           'policy':'Own captures and official-maker assets for commentary. No creator reuploads.'}
        page.screenshot(path=str(pack/'desktop-top.jpg'),type='jpeg',quality=91)
        register(m,pack/'desktop-top.jpg','own capture',url,1280)
        height=min(page.evaluate('document.documentElement.scrollHeight'),9000)
        import base64
        cdp=context.new_cdp_session(page)
        shot=cdp.send('Page.captureScreenshot',{'format':'jpeg','quality':87,'captureBeyondViewport':True,'clip':{'x':0,'y':0,'width':1280,'height':height,'scale':1}})
        (pack/'desktop-full.jpg').write_bytes(base64.b64decode(shot['data']))
        cdp.detach()
        register(m,pack/'desktop-full.jpg','own capture',url,1280)
        heads=page.locator('h1,h2,h3').evaluate_all('els=>els.map(e=>{let r=e.getBoundingClientRect();return {text:e.innerText,x:r.x+scrollX,y:r.y+scrollY,w:r.width,h:r.height}})')
        for h in heads:
            if h['w']>0 and h['y']+h['h']<=height:
                m['regions_css']['h_'+slug(h['text'])]={k:round(h[k]) for k in ['x','y','w','h']}
        # Standalone section shots never point a camera outside a captured image.
        for name,tag,text in sections:
            loc=page.locator(tag).filter(has_text=text)
            if not loc.count():continue
            loc.first.scroll_into_view_if_needed();page.wait_for_timeout(500)
            y=max(0,loc.first.evaluate('(e)=>e.getBoundingClientRect().top+scrollY')-50)
            page.evaluate('(y)=>window.scrollTo(0,y)',y);page.wait_for_timeout(400)
            page.screenshot(path=str(pack/('section-'+name+'.jpg')),type='jpeg',quality=92)
            register(m,pack/('section-'+name+'.jpg'),'own section capture',url,1280)
        # Tables are particularly important for accurately showing published prices.
        for i,table in enumerate(page.locator('table').all()[:3]):
            box=table.bounding_box()
            if box and box['width']>200 and box['height']<3000:
                table.screenshot(path=str(pack/f'table-{i}.jpg'),type='jpeg',quality=94)
                register(m,pack/f'table-{i}.jpg','own table capture',url)
        # Only sizable images from the maker's actual page; no outside stock searches.
        images=page.locator('img').evaluate_all('els=>els.map(e=>({src:e.currentSrc||e.src,alt:e.alt,w:e.naturalWidth,h:e.naturalHeight})).filter(x=>x.w>=650&&x.h>=250)')
        saved=0
        for im in images:
            if saved>=4 or not im['src'].startswith('https://'):continue
            try:
                r=requests.get(im['src'],timeout=25);r.raise_for_status()
                if len(r.content)>7_000_000:continue
                import io
                with Image.open(io.BytesIO(r.content)) as image:
                    image=image.convert('RGB');image.thumbnail((2000,2000));p=pack/f'official-{saved}.jpg';image.save(p,quality=92)
                register(m,p,'official-maker image',im['src']);m['files'][p.stem]['alt']=im['alt'];saved+=1
            except Exception:pass
        context.close()
        mcontext=browser.new_context(viewport={'width':430,'height':932},device_scale_factor=2)
        mobile=mcontext.new_page();mobile.goto(url,wait_until='domcontentloaded',timeout=45000);mobile.wait_for_timeout(2000)
        mobile.screenshot(path=str(pack/'mobile-top.jpg'),type='jpeg',quality=90)
        register(m,pack/'mobile-top.jpg','own mobile capture',url,430);mcontext.close()
        (pack/'manifest.json').write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n')
        contact(pack)
        print(vid,'captured',len(m['files']),'assets',flush=True)
    finally:
        try:context.close()
        except Exception:pass


def main():
    selected=set(sys.argv[1:])
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
        try:
            for spec in SPECS:
                if not selected or spec[0] in selected:capture(browser,spec)
        finally:browser.close()


if __name__=='__main__':main()
