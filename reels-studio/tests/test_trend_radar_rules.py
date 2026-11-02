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
