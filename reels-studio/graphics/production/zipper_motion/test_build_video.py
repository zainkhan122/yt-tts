"""Exercise the actual procedural visuals used in the review video."""
import hashlib
from graphics.production.zipper_motion.build_video import draw_object,draw_channel,draw_reverse,partial

T={'focus_slider':1.86,'move_up':4.68,'lock':7.66,'channel_reveal':10.58,'enter':12.86,'merge':14.14,'exit':15.44,'down':18.06,'wedge':19.92,'separates':20.2,'glue':21.94,'magnets':22.7,'shape':23.76,'pressure':24.42,'connection':25.82}
def h(im):return hashlib.sha256(im.tobytes()).digest()
def test_actual_object_progresses_and_unzips():
    assert h(draw_object(5,T))!=h(draw_object(7,T))
    assert h(draw_reverse(18.5,T))!=h(draw_reverse(20.5,T))
def test_actual_diagram_progresses_with_spoken_events():
    assert h(draw_channel(12,T))!=h(draw_channel(14.5,T))!=h(draw_channel(16,T))
def test_actual_typography_changes_after_each_trigger():
    assert h(draw_reverse(22,T))!=h(draw_reverse(24,T))!=h(draw_reverse(26,T))
def test_path_progress_is_distance_based():
    p=partial([(0,0),(0,10),(10,10)],.75)
    assert p==[(0,0),(0,10),(5,10)]
