"""Review-only integration of actual web demo, generated still and motion graphics.
The edit is manually directed; provider-automated semantic mode selection is not claimed.
"""
import copy,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from graphics.production.blueprint import digest
from graphics.production.layer_renderer import compile_timeline,render
D=Path(__file__).resolve().parent;ROOT=D.parents[2];SOURCE=ROOT/'graphics/production/acceptance_phonebox_long';LIVE=ROOT/'graphics/production/phonebox_live';ART=ROOT/'graphics/production/multimode_art'
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def text_layer(name,lines,w=1000,h=180,color='#fff9ee',bg=None):
    im=Image.new('RGBA',(w,h));d=ImageDraw.Draw(im)
    if bg:d.rounded_rectangle((1,1,w-2,h-2),20,fill=bg)
    for i,(s,size) in enumerate(lines):d.text((24,14+i*58),s,font=ImageFont.truetype(FONT,size),fill=color)
    im.save(D/(name+'.png'))
def make_assets():
    text_layer('intro-title',[('OLD PHONE, NEW PURPOSE',48),('A DESK PANEL FOR YOUR PC',33)],bg=(16,55,56,230))
    text_layer('intro-note',[('AI-GENERATED ILLUSTRATION',24)],w=760,h=60,bg=(16,55,56,240))
    text_layer('music-title',[('MUSIC CONTROLS',48),('LIVE BROWSER DEMO • SAMPLE DATA',26)],bg=(16,55,56,255))
    text_layer('stats-title',[('YOUR SYSTEM AT A GLANCE',43),('SCREEN CAPTURE • EXAMPLE DATA',26)],bg=(16,55,56,255))
    text_layer('editor-title',[('CUSTOMIZE YOUR DASHBOARD',40),('ILLUSTRATED WIDGET DRAG',27)],bg=(16,55,56,255))
    text_layer('conn-title',[('CONNECT THE TWO',48),('USB OR PAIRED WI-FI',31)],bg=(16,55,56,255))
    text_layer('conn-note',[('ILLUSTRATION • NOT A LIVE CONNECTION',23)],w=930,h=60,bg=(16,55,56,255))
    text_layer('setup-title',[('PHONE APP + DESKTOP AGENT',40),('BOTH NEED TO RUN',30)],bg=(16,55,56,255))
    text_layer('permissions',[('FEATURES DEPEND ON SETUP',36),('AND PERMISSIONS',34)],w=950,h=150,bg=(16,55,56,255))
    im=Image.new('RGBA',(960,680));d=ImageDraw.Draw(im);f=ImageFont.truetype(FONT,31)
    d.rounded_rectangle((50,120,330,570),42,fill='#e6eee4',outline='#80bca8',width=8);d.rounded_rectangle((82,160,298,530),26,fill='#284d4b');d.text((112,300),'PHONE',font=f,fill='#f8f4e8')
    d.rounded_rectangle((620,150,910,440),25,fill='#e4ece5',outline='#80bca8',width=8);d.rounded_rectangle((650,180,880,400),12,fill='#284d4b');d.text((668,280),'COMPUTER',font=ImageFont.truetype(FONT,25),fill='#f8f4e8');d.rectangle((735,440,795,515),fill='#e4ece5');d.rounded_rectangle((690,510,840,535),8,fill='#e4ece5')
    d.line((330,335,620,335),fill='#f0bc77',width=10);d.text((415,285),'USB',font=f,fill='#fff5e6');d.arc((345,90,625,410),200,340,fill='#7ac5aa',width=9);d.text((405,150),'WI-FI',font=f,fill='#e8f4ec');im.save(D/'connection-diagram.png')
    im=Image.new('RGBA',(50,50));d=ImageDraw.Draw(im);d.ellipse((3,3,47,47),fill='#ffd078',outline='#fff7dc',width=3);im.save(D/'packet.png')
    im=Image.new('RGB',(1080,1920),'#102e30');im.save(D/'background.png')

def asset(path,kind='image'):return {'path':str(path.resolve()),'sha256':digest(path),'type':kind}
def layer(id,asset,x,y,w,h,z=0,opacity=1):return {'id':id,'asset':asset,'x':x,'y':y,'width':w,'height':h,'z':z,'opacity':opacity}
def motion(target,op,frm,to):return {'target':target,'operation':op,'from':frm,'to':to,'easing':'smooth'}

def main():
    make_assets();base=json.loads((SOURCE/'scheduled.json').read_text());audio=SOURCE/'voice-pace-0.97.wav'
    # The prior scheduled semantic events are reused. Add an explicitly timed illustrative Wi-Fi packet.
    conn=next(x for x in base['beats'] if x['id']=='connection');conn['events'].append({'id':'wifi-packet','audio_time':15.02,'duration':.75,'beat_relative_time':15.02-conn['start']})
    assets={'art':asset(ART/'phone-desk.png'),'play':asset(D/'playback-demo.mp4','video'),'stats':asset(SOURCE/'stats.png'),'editor':asset(SOURCE/'editor.png'),'widget':asset(SOURCE/'widget.png'),'cursor':asset(SOURCE/'cursor.png')}
    for n in ['intro-title','intro-note','music-title','stats-title','editor-title','conn-title','conn-note','setup-title','permissions','connection-diagram','packet','background']:assets[n]=asset(D/(n+'.png'))
    layouts={
      'intro':{'transition':'cut','layers':[layer('img','art',270,480,540,960),layer('title','intro-title',270,180,500,90,3),layer('note','intro-note',270,825,380,30,4)],'events':{'show-dashboard':motion('img','scale',1,1.06)}},
      'media':{'transition':'cut','layers':[layer('bg','background',270,480,540,960),layer('label','music-title',270,175,500,90,3),layer('clip','play',270,455,510,319,2)],'events':{'focus-music':motion('clip','scale',.94,1)}},
      'stats':{'transition':'cut','layers':[layer('bg','background',270,480,540,960),layer('label','stats-title',270,175,500,90,3),layer('stat','stats',270,470,520,233,2)],'events':{'show-stats':motion('stat','position',[270,560],[270,470])}},
      'editor':{'transition':'cut','layers':[layer('bg','background',270,480,540,960),layer('label','editor-title',270,175,500,90,3),layer('edit','editor',270,470,520,242,2),layer('widget','widget',180,482,125,78,4),layer('cursor','cursor',170,490,38,45,5)],'events':{'drag-widget':motion('widget','position',[180,482],[338,500]),'drag-cursor':motion('cursor','position',[170,490],[328,510])}},
      'connection':{'transition':'cut','layers':[layer('bg','background',270,480,540,960),layer('title','conn-title',270,175,500,90,3),layer('diagram','connection-diagram',270,470,480,340,1),layer('usb','packet',200,467,25,25,4),layer('wifi','packet',185,410,25,25,4),layer('note','conn-note',270,805,465,30,5)],'events':{'usb-highlight':motion('usb','position',[200,467],[350,467]),'wifi-packet':motion('wifi','position',[185,410],[355,410])}},
      'setup':{'transition':'cut','layers':[layer('bg','background',270,480,540,960),layer('title','setup-title',270,175,500,90,3),layer('diagram','connection-diagram',270,460,480,340,1),layer('permissions','permissions',270,745,475,75,4)],'events':{'dashboard-stack':motion('diagram','scale',.83,1),'editor-stack':motion('permissions','opacity',0,1)}}}
    design={'assets':assets,'beats':layouts};timeline=compile_timeline(base,design,audio)
    (D/'mode-plan.json').write_text(json.dumps({'status':'review-only; mode choices hand-directed','beats':[{'beat':'intro','mode':'ai_visual','evidence':'interactive AI-generated still, not image-to-video'},{'beat':'media','mode':'screen_demo','evidence':'public PhoneBox demo, real click in synthetic data'},{'beat':'stats','mode':'screen_demo','evidence':'static prior demo capture, not action recording'},{'beat':'editor','mode':'motion_graphics','evidence':'labelled illustrative widget drag'},{'beat':'connection','mode':'motion_graphics','evidence':'illustrative connections, not actual hardware'},{'beat':'setup','mode':'motion_graphics','evidence':'illustrative components and permission dependency'}]},indent=2)+'\n')
    (D/'timeline.json').write_text(json.dumps(timeline,indent=2)+'\n');r=render(timeline,audio,D/'integrated-review.mp4',D/'render-cache',fps=24,native=True);print(json.dumps(r,indent=2))
if __name__=='__main__':main()
