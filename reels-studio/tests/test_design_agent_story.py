"""Design-agent storyboard contract; synthetic timings are not production voice approval."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from graphics.render import build_stage_html
from graphics.stage import plan_scenes, segments_from_timing, attach_evidence_images
from tools.align_words import tokens
from tools.local_preview_render import word_timings
from tools.house_gate import check

ROOT = Path(__file__).resolve().parents[1]


def storyboard(path):
    brief = json.loads((ROOT/'briefs/repo-design-agent-01.json').read_text())
    g = ROOT/brief['graphics']['dir']
    beats = json.loads((g/'beats.json').read_text())
    sheet = json.loads((g/'features.json').read_text())
    timing, all_words, t = {}, [], 0.0
    for scene in brief['scenes']:
        text = ' '.join(tokens(scene['say']))
        dur = len(text.split()) / 2.6
        words = word_timings(text, t, t + dur)
        timing[scene['id']] = {'words': words}
        all_words.extend(words); t += dur
    doc, _ = plan_scenes(sheet, (g/'source.md').read_text(), beats,
                         segments_from_timing(timing, [s['id'] for s in brief['scenes']]), t, all_words)
    attach_evidence_images(doc, brief['id'])
    path.write_text(build_stage_html(doc), encoding='utf-8')
    return doc


def test_story_chart_is_sourced_proportional_and_fires_on_speech(tmp_path):
    path = tmp_path/'stage.html'; doc = storyboard(path)
    assert check(path) == []
    with sync_playwright() as p:
        browser = p.chromium.launch(args=['--no-sandbox', '--allow-file-access-from-files'])
        page = browser.new_page(viewport={'width': 1080, 'height': 1920})
        errors = []; page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(path.as_uri()); page.wait_for_function('window.ready === true')
        s = next(x for x in doc['scenes'] if x['archetype'] == 'proof_chart')
        report = page.evaluate('window.__motionCueReports')[s['id']]
        assert all(r['matched'] for r in report)
        page.evaluate('(t)=>window.setTime(t)', report[1]['time'] - .01)
        assert float(page.locator('.scene:visible .da-bar.before').evaluate('(e)=>getComputedStyle(e).opacity')) == 0
        page.evaluate('(t)=>window.setTime(t)', report[2]['time'] + .6)
        bars = page.locator('.scene:visible .da-bar')
        widths = bars.evaluate_all('(els)=>els.map(e=>e.getBoundingClientRect().width)')
        assert abs(widths[1] / widths[0] - .0625) < .001
        assert '$8' in page.locator('.scene:visible').inner_text()
        assert '$0.50' in page.locator('.scene:visible').inner_text()
        assert "LANGCHAIN REPORTS" in page.locator('.scene:visible').inner_text()
        browser.close()
    assert not errors
