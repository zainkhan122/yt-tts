"""Cross-template storyboard smoke tests, using synthetic timings, not final narration."""
import json
from pathlib import Path

import pytest

from graphics.render import build_stage_html
from graphics.stage import plan_scenes, segments_from_timing
from tools.align_words import tokens
from tools.house_gate import check
from tools.local_preview_render import word_timings

ROOT = Path(__file__).resolve().parents[1]
BRIEFS = ['repo-sherlock-01', 'tool-claude-tokens-01', 'repo-musike-01',
          'repo-unslop-02', 'model-idol-01', 'explainer-negative-01', 'tool-seedance-01']


def stage_for(brief_id, path):
    brief = json.loads((ROOT/'briefs'/f'{brief_id}.json').read_text())
    graphics = ROOT / brief['graphics']['dir']
    beats = json.loads((graphics/'beats.json').read_text())
    sheet = json.loads((graphics/'features.json').read_text())
    source = (graphics/'source.md').read_text()
    timing, all_words, now = {}, [], 0.
    for scene in brief['scenes']:
        text = ' '.join(tokens(scene['say']))
        duration = max(2.5, len(text.split()) / 2.6)
        ws = word_timings(text, now, now + duration)
        timing[scene['id']] = {'words': ws}; all_words.extend(ws); now += duration
    order = [s['id'] for s in brief['scenes']]
    doc, _ = plan_scenes(sheet, source, beats, segments_from_timing(timing, order), now, all_words)
    path.write_text(build_stage_html(doc), encoding='utf-8')
    return doc


@pytest.mark.parametrize('brief_id', BRIEFS)
def test_storyboard_has_single_house_layer_and_clear_caption_band(tmp_path, brief_id):
    path = tmp_path/'stage.html'
    stage_for(brief_id, path)
    assert check(path) == []


def test_shared_cues_use_exact_multiword_match_and_report_fallback(tmp_path):
    from playwright.sync_api import sync_playwright
    path = tmp_path/'stage.html'
    stage_for('tool-seedance-01', path)
    with sync_playwright() as p:
        browser = p.chromium.launch(args=['--no-sandbox', '--allow-file-access-from-files'])
        page = browser.new_page(viewport={'width': 1080, 'height': 1920})
        page.goto(path.as_uri()); page.wait_for_function('window.ready === true')
        result = page.evaluate('''() => {
          let scene = {id:'test',t0:0,t1:8,words:[['turn',1,1.2],['it',1.2,1.3],['around',1.3,1.5],['turn',4,4.2],['around',4.2,4.4]]};
          let times = window.HouseMotion.cueTimes(['turn around','not spoken'],scene,2,{});
          return {times:times,report:window.__motionCueReports.test};
        }''')
        browser.close()
    assert result['times'][0] == 4
    assert result['report'][0]['matched'] is True
    assert result['report'][1]['matched'] is False
    assert 4 <= result['times'][1] < 8


def test_hyphenated_spoken_cue_is_tokenized(page_unused=None):
    # Tokenization is exercised in a real browser using the redline fixture.
    from playwright.sync_api import sync_playwright
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        path = Path(d)/"stage.html"
        stage_for('tool-claude-tokens-01', path)
        with sync_playwright() as p:
            b = p.chromium.launch(args=['--no-sandbox', '--allow-file-access-from-files'])
            page = b.new_page(viewport={'width':1080,'height':1920}); page.goto(path.as_uri())
            page.wait_for_function('window.ready === true')
            result = page.evaluate("""() => { let s={id:'hyphen',t0:0,t1:9,words:[['fifty',3,3.2],['four',3.2,3.4]]}; return {t:HouseMotion.cueTimes(['fifty-four'],s,1)[0], report:window.__motionCueReports.hyphen}; }""")
            b.close()
    assert result['t'] == 3 and result['report'][0]['matched']


@pytest.mark.parametrize('brief_id', BRIEFS)
def test_outro_keyword_matches_spoken_comment_cta(brief_id):
    import re
    brief = json.loads((ROOT/'briefs'/f'{brief_id}.json').read_text())
    beats = json.loads((ROOT/brief['graphics']['dir']/'beats.json').read_text())
    keyword = str(beats['scenes'][-1]['payload']['keyword'])
    say = brief['scenes'][-1]['say']
    assert re.search(r'\bcomment\s+["“\'‘]*' + re.escape(keyword) + r'\b', say, re.I), (brief_id, keyword, say)
