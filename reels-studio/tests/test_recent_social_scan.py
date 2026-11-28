import datetime as dt
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import recent_social_scan as s
UTC=dt.timezone.utc
NOW=dt.datetime(2026,11,23,20,tzinfo=UTC)

def test_no_invented_timestamp():
    for v in [None,'2026-11-23','2026-11-23T12:00:00','garbage']:
        assert s.classify(v,NOW,24)=='unknown'

def test_rolling_and_future():
    assert s.classify('2026-11-22T20:00:00Z',NOW,24)=='recent'
    assert s.classify('2026-11-22T19:59:59Z',NOW,24)=='outside_window'
    assert s.classify('2026-11-23T21:00:00Z',NOW,24)=='future_or_clock_error'

def test_timezone_conversion():
    assert s.parse_exact('2026-11-23T10:00:00-05:00').hour==15

def test_date_provenance_and_no_fallback_to_scan_time(monkeypatch):
    monkeypatch.setattr(s,'run_json',lambda args,timeout=45: {'entries':[{'id':'a','title':'A'},{'id':'b','timestamp':1795446000}],'channel_id':'UC123'})
    monkeypatch.setattr(s,'atom_dates',lambda c:{'a':'2026-11-23T15:00:00Z'})
    r=s.one({'type':'youtube','handle':'h','url':'https://youtube.com/@h','tabs':'shorts'},'yt-dlp',20,NOW,24,False,None)
    assert r['posts'][0]['timestamp_source']=='youtube_atom_published'
    assert r['posts'][0]['published_new_york']=='2026-11-23T10:00:00-05:00'
    assert r['posts'][1]['timestamp_source']=='yt_dlp_flat_timestamp'

def test_unknown_is_quarantined_and_limit_signalled(monkeypatch):
    monkeypatch.setattr(s,'run_json',lambda args,timeout=45: {'entries':[{'id':'a','upload_date':'20261123'}]})
    r=s.one({'type':'tiktok','handle':'h','url':'https://tiktok.com/@h'},'yt-dlp',1,NOW,24,False,None)
    assert r['posts'][0]['published_utc'] is None
    assert r['posts'][0]['window_status']=='unknown'
    assert r['limit_reached']

def test_relative_date_uses_requested_timezone_and_reference():
    from zoneinfo import ZoneInfo
    stamp=dt.datetime(2026,1,1,1,tzinfo=UTC)
    target,reference,source=s.resolve_target_date('yesterday',stamp,ZoneInfo('America/New_York'))
    assert str(reference)=='2025-12-31' and str(target)=='2025-12-30' and source=='host_clock'
    target,reference,source=s.resolve_target_date('yesterday',stamp,ZoneInfo('Asia/Karachi'),'2026-11-27')
    assert str(target)=='2026-11-26' and source=='user_supplied'
    assert str(s.resolve_target_date('2024-02-29',stamp,ZoneInfo('Asia/Karachi'))[0])=='2024-02-29'
