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

def test_main_passes_log_path_and_writes_checked_handoff(tmp_path,monkeypatch):
    import json
    import numpy as np
    import draft_voice as m
    class Voice:
        model_revision='test-revision'
        def __init__(self,cfg): pass
        def __call__(self,text,seed=0): return np.ones(24000,dtype='float32')*.01,24000
    def aligned(audio,sr,lines,work,log):
        assert isinstance(log,Path)
        words=' '.join(lines).split()
        return [],1.,[(m.norm_word(w),i/len(words),(i+1)/len(words)) for i,w in enumerate(words)]
    monkeypatch.setattr(m,'ChatterboxVoice',Voice)
    monkeypatch.setattr(m,'align_chunk',aligned)
    monkeypatch.setattr(m,'melody_st',lambda *args: 14.)
    script=tmp_path/'script.json';script.write_text(json.dumps(['Turn a stream into a short.']))
    monkeypatch.setattr(sys,'argv',['draft_voice','--script',str(script),'--out',str(tmp_path/'out')])
    m.main()
    d=json.loads((tmp_path/'out/timings.json').read_text())
    assert d['overall_match']==1 and d['profile']=='option-3' and (tmp_path/'out/voice.wav').is_file()
