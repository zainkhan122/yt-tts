from PIL import Image
import pytest
from graphics.production.vector_motion import path_part,state,draw_shapes,MotionError

def test_path_reveals_by_distance():
    assert path_part([(0,0),(0,10),(10,10)],.75)==[(0,0),(0,10),(5,10)]
    assert path_part([(0,0),(0,10)],0)==[(0,0),(0,0)]

def test_word_timed_state_has_eased_motion_and_hold():
    n={'id':'x'};events=[{'node':'x','property':'offset','from':[0,10],'to':[0,0],'t0':1.,'t1':3.}]
    assert state(n,events,.5)['offset']==[0,10]
    assert state(n,events,2)['offset']==[0,5]
    assert state(n,events,4)['offset']==[0,0]

def test_real_path_render_reveals_instead_of_scaling():
    n={'id':'p','size':[100,20],'shapes':[{'kind':'path','points':[[0,10],[99,10]],'width':4,'fill':'#ffffff'}]}
    im=draw_shapes(n,.5)
    assert im.getpixel((30,20))[3]>0 and im.getpixel((170,20))[3]==0

def test_reject_clipped_text():
    n={'size':[40,40],'shapes':[{'kind':'text','text':'TOO LONG','size':22,'at':[0,0],'fill':'#ffffff'}]}
    with pytest.raises(MotionError,match='bounds'):draw_shapes(n)

def test_rect_reveal_masks_real_pixels():
    from graphics.production.vector_motion import prepare,render_frame
    s={'eyebrow':'TEST','title':'TEST','subtitle':'TEST','nodes':[{'id':'box','pos':[100,300],'size':[100,40],'shapes':[{'kind':'rect','box':[0,0,99,39],'fill':'#ff0000'}]}], 'compiled_events':[{'node':'box','property':'reveal','from':0,'to':1,'t0':0.,'t1':1.}]}
    prepare([s]);im=render_frame(s,.5)
    assert im.getpixel((220,620))[:3]==(255,0,0)
    assert im.getpixel((380,620))[:3]!=(255,0,0)

def test_word_caption_changes_at_real_cues():
    from graphics.production.vector_motion import caption_frame
    words=[{'text':'select','start':1.,'end':1.3},{'text':'cells','start':1.3,'end':1.7}]
    a=caption_frame(Image.new('RGB',(1080,1920)),words,1.1)
    b=caption_frame(Image.new('RGB',(1080,1920)),words,1.4)
    assert a.tobytes()!=b.tobytes()
