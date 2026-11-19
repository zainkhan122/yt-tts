"""The topic sheet: every registered source, a rolling 24 h window, consensus dedup, no repeats."""
import csv
import datetime as dt
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import todays_topics as TT  # noqa: E402

NOW = dt.datetime(2026, 11, 14, 12, 0, tzinfo=dt.timezone.utc)


def _row(source, source_type, post_id, title, hours_ago, platform=None):
    pub = (NOW - dt.timedelta(hours=hours_ago)).isoformat(timespec="seconds")
    return {"platform": platform or source_type, "source": source, "source_type": source_type,
            "post_id": post_id, "url": f"https://example.com/{post_id}", "published": pub,
            "title": title, "views": "1000", "likes": "", "comments": "", "shares": "", "saves": "",
            "duration": "", "first_seen": pub, "last_seen": pub}


@pytest.fixture()
def sheet(tmp_path, monkeypatch):
    rows = [
        _row("chan-a", "tiktok", "p1", "Look at github.com/acme/demo-tool today", 2),
        _row("chan-b", "youtube", "p2", "Also github.com/acme/demo-tool is wild", 5),
        _row("feed-x", "rss", "p3", "A fresh launch of acme/other-tool", 3),
        _row("gittrend", "web", "p4", "acme/demo-tool", 1),
        _row("chan-c", "tiktok", "p5", "Old news about acme/older-tool", 30),   # outside the window
    ]
    posts = tmp_path / "posts.csv"
    with posts.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    registry = [
        {"type": "tiktok", "handle": "chan-a", "url": "u", "tabs": "", "focus": "", "why_follow": "",
         "priority": "daily", "language": "en", "added": "2026-01-01", "status": "active"},
        {"type": "youtube", "handle": "chan-b", "url": "u", "tabs": "shorts", "focus": "", "why_follow": "",
         "priority": "daily", "language": "en", "added": "2026-01-01", "status": "active"},
        {"type": "rss", "handle": "feed-x", "url": "u", "tabs": "", "focus": "", "why_follow": "",
         "priority": "daily", "language": "en", "added": "2026-01-01", "status": "active"},
        {"type": "web", "handle": "gittrend", "url": "u", "tabs": "", "focus": "", "why_follow": "",
         "priority": "daily", "language": "en", "added": "2026-01-01", "status": "active"},
        {"type": "tiktok", "handle": "chan-c", "url": "u", "tabs": "", "focus": "", "why_follow": "",
         "priority": "daily", "language": "en", "added": "2026-01-01", "status": "active"},
    ]
    import sources
    import topics_covered
    monkeypatch.setattr(TT, "POSTS", posts)
    monkeypatch.setattr(TT, "OUT_DIR", tmp_path / "out")
    monkeypatch.setattr(sources, "load", lambda: registry)
    monkeypatch.setattr(topics_covered, "rebuild", lambda: {"acmeoldertool": {"status": "covered", "videos": ["v1"]}})
    monkeypatch.setattr(TT, "parse_ts", lambda raw: _fixed_parse(raw))
    return tmp_path


def _fixed_parse(raw):
    if not raw:
        return None
    t = dt.datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def test_sheet_covers_every_registered_source(sheet):
    import sources
    assert TT.main(["--hours", "24"], now=NOW) == 0
    md = (sheet / "out" / f"daily-{NOW.date().isoformat()}.md").read_text(encoding="utf-8")
    for handle in ("chan-a", "chan-b", "feed-x", "gittrend", "chan-c"):
        assert handle in md, handle


def test_only_items_inside_the_rolling_window_are_listed(sheet):
    TT.main(["--hours", "24"], now=NOW)
    payload = json.loads((sheet / "out" / f"daily-{NOW.date().isoformat()}.json").read_text(encoding="utf-8"))
    names = [t["name"] for t in payload["topics"]]
    assert "acme/older-tool" not in " ".join(names)


def test_the_same_topic_from_two_sources_is_one_row_with_two_sources(sheet):
    TT.main(["--hours", "24"], now=NOW)
    payload = json.loads((sheet / "out" / f"daily-{NOW.date().isoformat()}.json").read_text(encoding="utf-8"))
    demo = [t for t in payload["topics"] if "demo-tool" in t["name"]]
    assert len(demo) == 1, demo
    assert demo[0]["consensus"] == 3, demo[0]      # tiktok + youtube + gittrend


def test_a_covered_topic_is_never_recommended(sheet):
    TT.main(["--hours", "24"], now=NOW)
    payload = json.loads((sheet / "out" / f"daily-{NOW.date().isoformat()}.json").read_text(encoding="utf-8"))
    assert all(not t["covered"] for t in payload["topics"])
    assert not any("older-tool" in t["name"] for t in payload["topics"])


def test_a_legacy_date_only_stamp_still_parses():
    assert TT.parse_ts("2026-11-14") is not None
    assert TT.parse_ts("") is None
    assert TT.parse_ts("not a date") is None


def test_own_channel_analytics_changes_the_real_sheet_order(sheet, monkeypatch):
    import selection_analytics
    import trend_radar
    monkeypatch.setattr(trend_radar, 'gittrend_snapshot', lambda n: {})
    rows = [dict(video_id=k, views=v, age_hours=36, taken_at='2026-11-05T12:00:00Z') for k,v in [
        ('repo-coop-anything-01',100),('news-gemini-agent-01',80),('repo-whatsapp-mcp-01',60),
        ('x',20),('y',20),('z',20),('w',20)]]
    monkeypatch.setattr(selection_analytics, 'load_rows', lambda now: rows)
    items = [_row('chan-a','tiktok','1','acme/agent-desktop',2),
             _row('chan-b','youtube','2','acme/unmatched-widget',2)]
    with TT.POSTS.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=items[0].keys());writer.writeheader();writer.writerows(items)
    assert TT.main(['--hours','24'],now=NOW)==0
    out=json.loads((sheet/'out'/f'daily-{NOW.date().isoformat()}.json').read_text())['topics']
    assert out[0]['name']=='acme/agent-desktop'
    assert out[0]['selection_score']['analytics']['adjustment'] > 0
    assert out[1]['selection_score']['analytics']['status']=='insufficient evidence'
