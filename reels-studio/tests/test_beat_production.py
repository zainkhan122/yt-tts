import json,math,struct,wave
from pathlib import Path
import pytest
from PIL import Image,ImageChops
from graphics.production.blueprint import bind,battery_specs,BlueprintError,validate,auto_groups
from graphics.production.providers import Provider,Registry
from graphics.production.render import render,frame

@pytest.fixture
def project(tmp_path):
    audio=tmp_path/'audio.wav'
    # Synthetic silence solely exercises timeline plumbing, not speech alignment accuracy.
    with wave.open(str(audio),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(8000);w.writeframes(b'\0\0'*32000)
    text="Your smartphone battery doesn't simply run out of power. Its chemistry is changing every second.".split()
    words=[[x,round(.1+i*.23,3),round(.25+i*.23,3)] for i,x in enumerate(text)]
    groups=[3,6,6]
    b=bind(audio,words,groups,battery_specs(words,groups),method='forced-alignment')
    return audio,b

def test_timing_and_object_motion(project):
    audio,b=project
    assert len(b['beats'])==3
    assert [x['animations'][0]['kind'] for x in b['beats']]==['phone_explode','battery_charge','ion_flow']
    assert b['beats'][-1]['end']==4
    for beat in b['beats']:
        e=beat['animations'][0]; assert e['start']==beat['words'][e['word_index']][1]
        assert ImageChops.difference(frame(beat,e['start']),frame(beat,(e['start']+e['end'])/2)).getbbox()
        assert beat['assets'][0]['kind']=='programmatic_motion'

def test_mutation_and_bad_timing_rejected(project):
    audio,b=project
    b['beats'][0]['animations'][0]['start']+=.1
    with pytest.raises(BlueprintError):validate(b,audio)
    b['beats'][0]['animations'][0]['start']-=.1
    with audio.open('ab') as f:f.write(b'changed')
    with pytest.raises(BlueprintError,match='changed'):validate(b,audio)

def test_fallback_rejected(project):
    audio,b=project;words=[w for x in b['beats'] for w in x['words']]
    with pytest.raises(BlueprintError,match='estimated'):bind(audio,words,[3,6,6],battery_specs(words,[3,6,6]),method='length-weighted')

def test_capability_fail_closed():
    r=Registry();r.register(Provider('x',frozenset({'image'}),object()))
    with pytest.raises(ValueError):r.require('x','video')

def test_render_reuse_and_force(project,tmp_path):
    audio,b=project;work=tmp_path/'job';out=tmp_path/'out.mp4';cover=tmp_path/'cover.png'
    # Opening cover comes from the first scene itself.
    frame(b['beats'][0],0).save(cover)
    render(b,audio,work,out,cover)
    state=json.loads((work/'state.json').read_text());paths=[Path(v['path']) for v in state['beats'].values()];times=[p.stat().st_mtime_ns for p in paths]
    render(b,audio,work,out,cover,force=['beat-002']);times2=[p.stat().st_mtime_ns for p in paths]
    assert times[0]==times2[0] and times[1]!=times2[1] and times[2]==times2[2]
    assert out.exists() and state['status']=='complete'
    from lib.cover_frame import _ffmpeg
    import subprocess
    decoded=tmp_path/'decoded.png';subprocess.run([_ffmpeg(),'-y','-v','error','-i',str(out),'-frames:v','1',str(decoded)],check=True)
    from PIL import ImageStat
    with Image.open(cover) as a,Image.open(decoded) as z:
        assert sum(ImageStat.Stat(ImageChops.difference(a.convert('RGB'),z.convert('RGB'))).mean)/3<10
