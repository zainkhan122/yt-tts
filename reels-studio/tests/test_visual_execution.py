"""Provider tests are fakes; no external generation service is called."""
import copy, subprocess
from pathlib import Path
import pytest
from PIL import Image
from graphics.production.providers import VisualCapabilities,VisualProvider,VisualRegistry
from graphics.production.execution import build_execution,ExecutionError
from graphics.production.assets import AssetStore,AssetError,RetryableAssetError
from graphics.production.continuity import Continuity
from graphics.production.compatibility import to_render_instructions,CompatibilityError,LEGACY_RENDERER
from graphics.media import ffmpeg_exe

def cap(**changes):
    d=dict(identity='fake',model='fake-model',operations=frozenset({'image','video','image_to_video','programmatic_motion'}),treatments=frozenset({'product_visualization','process_animation'}),input_formats=frozenset({'png','jpg'}),output_formats=frozenset({'png','mp4'}),max_width=512,max_height=512,max_duration=5,image_to_video=True,reference_images=True,subject_consistency='reference_based',transparency=True,camera_motion=frozenset({'hold'}),object_motion=True,configured=True,authorization='not_required',availability='available');d.update(changes);return VisualCapabilities(**d)

class Fake:
    def __init__(self,fail=0):self.calls=0;self.fail=fail;self.last=None
    def generate(self,request,out):
        self.calls+=1;self.last=request
        if self.calls<=self.fail:raise RetryableAssetError('retryable')
        if request['format']=='png':Image.new('RGB',(request['width'],request['height']),'red').save(out)
        else:subprocess.run([ffmpeg_exe(),'-y','-v','error','-f','lavfi','-i',f"color=red:s={request['width']}x{request['height']}:r=25:d={request['duration']}",'-c:v','libx264','-pix_fmt','yuv420p',str(out)],check=True)

def reg(c=None,a=None):
    r=VisualRegistry();r.register(VisualProvider(c or cap(),a or Fake()));return r

def blueprint():
    return {'audio_sha256':'a'*64,'beats':[{'id':'b1','start':0.,'end':2.,'treatment':'product_visualization','subject':'object','objects':['shell'],'assets':[{'id':'a1','kind':'image','description':'object on desk','reuse_of':None}],'events':[{'id':'e1','asset_id':'a1','audio_time':.2,'duration':.8,'action':'show object','animation_type':'still','camera':'hold','transition':'cut'}]}]}

def getjob(registry=None):return build_execution(blueprint(),registry or reg(),{'product_visualization':[{'provider':'fake','operation':'image'}]},width=100,height=100)['jobs'][0]

def test_discovery_and_legacy_api():
    r=reg(cap(configured=False));assert r.discover('image')==[('fake','unconfigured')];assert r.discover('unknown')==[('fake','unsupported')]
    with pytest.raises(ValueError):r.get('fake','image')
    r=reg(cap(authorization='unknown'));assert r.discover('image')[0][1]=='authorization_unknown'
    r=reg(cap(availability='unavailable'));assert r.discover('image')[0][1]=='unavailable'

def test_fallback_requires_approval_and_object_motion():
    r=reg();b=blueprint();b['beats'][0]['treatment']='exploded_view';b['beats'][0]['events'][0]['animation_type']='explode'
    policy={'exploded_view':[{'provider':'fake','operation':'image','deviation':'stylized'}, {'provider':'fake','operation':'programmatic_motion','deviation':'schematic'}]}
    with pytest.raises(ExecutionError):build_execution(b,r,policy,width=100,height=100)
    j=build_execution(b,r,policy,width=100,height=100,allow_deviation=True)['jobs'][0];assert j['operation']=='programmatic_motion' and j['deviation']=='schematic'

def test_asset_generation_cache_force_and_integrity(tmp_path):
    fake=Fake();r=reg(a=fake);store=AssetStore(tmp_path,r);job=getjob(r)
    x=store.generate(job,prompt='red object',fmt='png'); y=store.generate(job,prompt='red object',fmt='png');assert fake.calls==1 and x['content_hash']==y['content_hash']
    z=store.generate(job,prompt='red object',fmt='png',force=True);assert fake.calls==2 and z['beat_id']=='b1'
    Path(z['file_path']).write_bytes(b'bad');store.generate(job,prompt='red object',fmt='png');assert fake.calls==3

def test_reference_and_continuity(tmp_path):
    fake=Fake();r=reg(a=fake);s=AssetStore(tmp_path,r);job=getjob(r);first=s.generate(job,prompt='one',fmt='png')
    job2={**job,'asset_id':'a2','event_id':'e2','reference_asset':'a1'};c=Continuity('subject','same shape','studio','soft','blue','steady',('a1',)).to_dict()
    with pytest.raises(AssetError):s.generate(job2,prompt='two',fmt='png',continuity=c)
    second=s.generate(job2,prompt='two',fmt='png',reference_records=[first],continuity=c)
    assert second['reference_assets'][0]['content_hash']==first['content_hash'] and second['continuity']['subject_id']=='subject'
    assert fake.last['references'][0]['path']==first['file_path']
    Path(first['file_path']).write_bytes(b'damaged')
    with pytest.raises(AssetError):s.generate(job2,prompt='two',fmt='png',reference_records=[first])

def test_retry_and_invalid_output(tmp_path):
    fake=Fake(fail=1);r=reg(a=fake);s=AssetStore(tmp_path,r,retries=1);s.generate(getjob(r),prompt='x',fmt='png');assert fake.calls==2
    class Broken:
        def generate(self,request,out):out.write_bytes(b'not an image')
    r=reg(a=Broken());s=AssetStore(tmp_path/'other',r)
    with pytest.raises(AssetError):s.generate(getjob(r),prompt='x',fmt='png')

def test_video_asset_and_compatibility(tmp_path):
    r=reg();b=blueprint();b['beats'][0]['events'][0]['animation_type']='move';ex=build_execution(b,r,{'product_visualization':[{'provider':'fake','operation':'video'}]},width=100,height=100)
    j=ex['jobs'][0];s=AssetStore(tmp_path,r)
    with pytest.raises(AssetError,match='actual video'):s.generate(j,prompt='move',fmt='png')
    rec=s.generate(j,prompt='move',fmt='mp4');assert rec['media_type']=='video/mp4'
    with pytest.raises(CompatibilityError,match='b1/e1'):to_render_instructions(ex,[rec],renderer=LEGACY_RENDERER)
    contract={'formats':{'mp4'},'operations':{'video'},'animation_types':{'move'},'transitions':{'cut'},'camera':{'hold'}}
    assert to_render_instructions(ex,[rec],renderer=contract)[0]['start']==.2

def test_reuse_preserves_content_and_associations(tmp_path):
    fake=Fake();r=reg(a=fake);s=AssetStore(tmp_path,r);j=getjob(r);first=s.generate(j,prompt='object',fmt='png')
    second=s.reuse({**j,'asset_id':'a2','beat_id':'b2','event_id':'e2','reference_asset':'a1'},first)
    assert fake.calls==1 and second['generation_status']=='reused' and second['content_hash']==first['content_hash'] and second['beat_id']=='b2'

def test_unsupported_camera_and_reference_capabilities():
    r=reg(cap(camera_motion=frozenset()));
    with pytest.raises(ExecutionError,match='camera'):getjob(r)
    r=reg(cap(reference_images=False,subject_consistency='none'))
    b=blueprint();b['beats'].append(copy.deepcopy(b['beats'][0]));b['beats'][1].update(id='b2',start=2.,end=4.);b['beats'][1]['assets'][0].update(id='a2',reuse_of='a1');b['beats'][1]['events'][0].update(id='e2',asset_id='a2',audio_time=2.2)
    with pytest.raises(ExecutionError,match='reference'):build_execution(b,r,{'product_visualization':[{'provider':'fake','operation':'image'}]},width=100,height=100)
