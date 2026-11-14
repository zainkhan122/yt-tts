"""Owner rule (30 Oct 2026): TOS, legal, licence and privacy are not reasons to exclude a topic."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import trend_radar  # noqa: E402


def test_only_content_flag_remains():
    assert set(trend_radar.RISK) == {"nsfw/uncensored"}


def test_tos_and_piracy_text_is_not_flagged():
    text = "free API key bypass, torrent repack, scrape instagram, undetectable stealth"
    assert not any(re.search(p, text, re.I) for p in trend_radar.RISK.values())


def test_gittrend_today_preserves_date_and_rank_deduplicates():
    html = '''<p>Ranked by star velocity<!-- --> · November 13, 2026</p>
      <a href="/repo/example/first">First</a><a href="/repo/example/first">dup</a>
      <a href="https://gittrend.io/repo/example/second">Second</a>'''
    snapshot = trend_radar.parse_gittrend_snapshot(html)
    assert snapshot['date'] == '2026-11-13'
    assert [(i['name'], i['rank']) for i in snapshot['items']] == [('example/first', 1), ('example/second', 2)]


def test_gittrend_undated_snapshot_is_not_given_a_fabricated_date():
    assert trend_radar.parse_gittrend_snapshot('<a href="/repo/a/b">repo</a>')['date'] is None
