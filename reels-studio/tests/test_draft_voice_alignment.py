import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from draft_voice import mapped

def test_real_matched_word_times_and_interpolation():
    got=mapped(['Turn','a','stream'],[('turn',.1,.3),('stream',.6,.9)],2,3)
    assert got[0]==['Turn',2.1,2.3]
    assert got[2]==['stream',2.6,2.9]
    assert 2.3 <= got[1][1] < got[1][2] <= 2.6

def test_all_unmatched_remains_monotonic():
    got=mapped(['one','two'],[],1,2)
    assert got[0][1]==1 and got[1][2]==2
