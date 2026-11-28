"""Build review-only battery demo from Chatterbox handoff and explicit semantic plan.
AI-generated hero image is a manually supplied input; diagrams are procedural.
"""
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from graphics.production.blueprint import digest
from graphics.production.review_handoff import schedule_review
from graphics.production.layer_renderer import compile_timeline,render

D=Path(__file__).resolve().parent/'demo_assets';D.mkdir(exist_ok=True)
F='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def label(size):return ImageFont.truetype(F,size)
def transparent(name,w,h,draw):
    im=Image.new('RGBA',(w,h));draw(ImageDraw.Draw(im),w,h);im.save(D/(name+'.png'))
def assets():
    def bat(d,w,h):
        d.rounded_rectangle((7,7,w-8,h-8),radius=18,fill='#283e40',outline='#d8e5db',width=4)
        d.rounded_rectangle((23,27,w-24,h-26),radius=10,fill='#d3bc78',outline='#f5e8b0',width=2)
        d.rectangle((int(w*.43),0,int(w*.57),10),fill='#7ea8a5')
        d.text((35,70),'Li-ion',font=label(24),fill='#243c39');d.text((34,120),'BATTERY',font=label(16),fill='#38504a')
        d.line((34,157,w-35,157),fill='#789284',width=3)
        d.text((34,171),'CELL',font=label(13),fill='#49685d')
    transparent('battery_layer',180,250,bat)
    def bg(d,w,h):
        d.rectangle((0,0,w,h),fill='#102f32')
        for y in range(0,h,4):
            c=int(34+18*y/h);d.line((0,y,w,y),fill=(15,c,c+4),width=4)
        d.text((40,70),'INSIDE THE CELL',font=label(29),fill='#f2ebd9')
        d.text((40,115),'SIMPLIFIED CROSS-SECTION',font=label(14),fill='#9abbb1')
        d.text((40,820),'ILLUSTRATIVE  /  NOT TO SCALE',font=label(14),fill='#a3c5ba')
    transparent('cross_background',540,960,bg)
    def cross(d,w,h):
        d.rounded_rectangle((0,0,w-1,h-1),radius=22,fill='#e8e4ce',outline='#c1d6c6',width=3)
        d.rounded_rectangle((16,18,144,h-18),radius=12,fill='#cf8d6e')
        d.rounded_rectangle((w-145,18,w-16,h-18),radius=12,fill='#6a9ea8')
        d.rectangle((150,20,w-151,h-20),fill='#e9dcb4')
        d.text((24,34),'ELECTRODE',font=label(13),fill='#392d28');d.text((w-136,34),'ELECTRODE',font=label(13),fill='#15393e')
        for y in range(100,h-20,60):
            for x in (42,90,w-125,w-75):d.ellipse((x,y,x+14,y+14),fill='#f5e5c1')
    transparent('cross_section',470,360,cross)
    def ion(d,w,h):
        d.ellipse((1,1,w-2,h-2),fill='#f3c868',outline='#fff2ba',width=3);d.text((w//2-5,h//2-12),'+',font=label(20),fill='#634c26')
    transparent('ion',36,36,ion)
    def meter(d,w,h):
        d.rounded_rectangle((0,0,w-1,h-1),radius=10,fill='#294d4b',outline='#d4e6d7',width=2)
        d.text((15,13),'ENERGY',font=label(14),fill='#d8e8dc');d.rounded_rectangle((105,11,w-12,h-11),radius=5,fill='#122c2c')
    transparent('energy_meter',260,55,meter)
    def fill(d,w,h):d.rounded_rectangle((0,0,w-1,h-1),radius=5,fill='#7ed2a6')
    transparent('energy_fill',135,27,fill)
    def heading(d,w,h):
        d.rounded_rectangle((0,0,w-1,h-1),radius=12,fill=(21,48,46,225));d.text((18,11),'THE BATTERY INSIDE',font=label(21),fill='#f2f3e8')
    transparent('headline',270,50,heading)

def item(i,kind,desc):return {'id':i,'kind':kind,'description':desc,'reuse_of':None}
def event(i,phrase,asset,action,target,atype,dur):return {'id':i,'trigger_phrase':phrase,'occurrence':1,'action':action,'target':target,'animation_type':atype,'duration':dur,'camera':'hold','asset_id':asset,'transition':'cut'}
def beat(i,a,z,title,treat,subject,objects,asset_list,events):return {'id':i,'word_start':a,'word_end':z,'meaning':title,'visual_objective':title,'treatment':treat,'scene_description':title,'subject':subject,'objects':objects,'composition':'center','camera':'hold','transition':'cut','assets':asset_list,'events':events}
def make_plan():
    return {'beats':[
      beat('hero',0,3,'Reveal phone battery','product_visualization','smartphone',['phone','battery'],[item('photo','image','AI-generated phone photo'),item('battery-a','graphic','illustrated battery')],[event('push','smartphone','photo','Push camera toward phone','camera','camera_only',.8),event('reveal','battery','battery-a','Reveal the battery','battery','opacity',.4)]),
      beat('separate',3,10,'Separate battery and show energy','exploded_view','smartphone battery',['phone','battery','energy indicator'],[item('photo-b','image','same phone'),item('battery-b','graphic','battery'),item('meter','graphic','energy indicator')],[event('separate-cell','does','battery-b','Move battery out of phone','battery','position',1.0),event('meter-grow','power','meter','Energy indicator appears','meter','scale',.4)]),
      beat('chemistry',10,16,'Show ion movement in cell','scientific_visualization','battery cross-section',['electrodes','ions'],[item('cross','graphic','electrodes'),item('ion-a','graphic','ion'),item('ion-b','graphic','ion')],[event('ion-one','chemistry','ion-a','Move an ion between electrodes','ion a','position',1.2),event('ion-two','changing','ion-b','Move a second ion between electrodes','ion b','position',1.1)])]}
def layer(id,asset,x,y,w,h,z,opacity=1):return {'id':id,'asset':asset,'x':x,'y':y,'width':w,'height':h,'z':z,'opacity':opacity}
def motion(target,operation,a,b,easing='smooth'):return {'target':target,'operation':operation,'from':a,'to':b,'easing':easing}
def design():
    names=['smartphone','battery_layer','cross_background','cross_section','ion','energy_meter','energy_fill','headline'];a={n:{'path':str((D/(n+'.png')).resolve()),'sha256':digest(D/(n+'.png')),'type':'image'} for n in names}
    return {'assets':a,'beats':{
      'hero':{'transition':'cut','layers':[layer('photo','smartphone',270,480,540,960,0),layer('head','headline',270,130,270,50,1),layer('battery','battery_layer',270,490,135,188,2)],'events':{'push':motion('camera','camera',[1,0],[1.08,0]),'reveal':motion('battery','opacity',0,1)}},
      'separate':{'transition':'cut','layers':[layer('photo','smartphone',270,480,540,960,0),layer('head','headline',270,130,270,50,1),layer('battery','battery_layer',270,490,135,188,2),layer('meter','energy_meter',270,780,260,55,3),layer('charge','energy_fill',310,780,135,27,4)],'events':{'separate-cell':motion('battery','position',[270,490],[425,475]),'meter-grow':motion('charge','scale',1,.35)}},
      'chemistry':{'transition':'fade','layers':[layer('bg','cross_background',270,480,540,960,0),layer('electrodes','cross_section',270,460,470,360,1),layer('particle1','ion',135,420,36,36,2),layer('particle2','ion',135,510,36,36,3)],'events':{'ion-one':motion('particle1','position',[135,420],[398,420]),'ion-two':motion('particle2','position',[135,510],[398,510])}}}}

def main():
    assets();script=json.loads((D/'narration.json').read_text());handoff=json.loads((D/'timings.json').read_text());audio=D/'voice.wav';plan=make_plan();scheduled=schedule_review(audio,script,handoff,plan);layout=design();timeline=compile_timeline(scheduled,layout,audio)
    for name,obj in [('semantic-plan.json',plan),('scheduled-blueprint.json',scheduled),('layer-design.json',layout),('render-timeline.json',timeline)]: (D/name).write_text(json.dumps(obj,indent=2)+'\n')
    result=render(timeline,audio,D/'battery-demo.mp4',D/'render-cache',fps=24);print(json.dumps(result,indent=2))
if __name__=='__main__':main()
