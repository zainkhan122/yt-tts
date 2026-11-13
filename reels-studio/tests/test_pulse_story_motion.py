"""Behavioral checks for the Seedance story's cue-bound charts and layout."""
import json
from pathlib import Path

import pytest

from graphics.render import build_stage_html

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def page(tmp_path_factory):
    from playwright.sync_api import sync_playwright

    beats = json.loads((ROOT / 'briefs/graphics/tool-seedance-01/beats.json').read_text())
    # Synthetic timestamps make the checks deterministic and independent of cached audio.
    words = [
        [['who', .2, .4]],
        [['leaderboard', 4.3, 4.5], ['seedance', 5., 5.2], ['veo', 7., 7.2]],
        [['two', 11., 11.2], ['k', 11.2, 11.4], ['fifteen', 13., 13.2], ['lip', 15., 15.2], ['sync', 15.2, 15.4]],
        [['free', 21., 21.2], ['fourteen', 23., 23.2]],
        [['china', 31., 31.2], ['self', 33., 33.2], ['reported', 33.2, 33.4], ['independent', 35., 35.2], ['prompts', 37., 37.2]],
        [['video', 41., 41.2]],
    ]
    spans = [(0, 4), (4, 10), (10, 20), (20, 30), (30, 40), (40, 45)]
    scenes = []
    for i, (beat, ws, (start, end)) in enumerate(zip(beats['scenes'], words, spans)):
        scenes.append({'id': f's{i:02}', 'archetype': beat['archetype'], 'headline': beat['headline'],
                       'payload': beat['payload'], 't0': start, 't1': end, 'words': ws, 'text': ' '.join(w[0] for w in ws)})
    path = tmp_path_factory.mktemp('pulse') / 'stage.html'
    path.write_text(build_stage_html({'template': 'pulse', 'handle': '@test', 'scenes': scenes,
                                      'brand': {'name': 'Test', 'handle': '@test'}}))
    with sync_playwright() as p:
        browser = p.chromium.launch(args=['--no-sandbox', '--allow-file-access-from-files'])
        tab = browser.new_page(viewport={'width':1080, 'height':1920})
        tab.goto(path.as_uri())
        tab.wait_for_function('window.ready === true')
        yield tab
        browser.close()


def probe(page, time, expression):
    page.evaluate('(t) => window.setTime(t)', time)
    return page.evaluate(expression)


def test_chart_bars_are_cue_bound_and_faithful(page):
    js = "() => [...document.querySelectorAll('[data-scene=s01] .track u')].map(e=>parseFloat(e.style.width))"
    assert probe(page, 4.8, js) == [0, 0]
    first = probe(page, 5.8, js)
    assert first[0] > 95 and first[1] == 0
    last = probe(page, 7.8, js)
    assert last[0] == 100 and abs(last[1] - 100 * 1226 / 1269) < 0.2


def test_multiword_cue_reveals_the_matching_plate(page):
    js = "() => [...document.querySelectorAll('[data-scene=s02] .pl-plate')].map(e=>parseFloat(e.style.opacity))"
    assert probe(page, 10.8, js) == [0, 0, 0]
    assert probe(page, 11.4, js)[0] == 1
    assert probe(page, 14., js)[1] == 1
    assert probe(page, 15.5, js)[2] == 1


def test_price_connector_between_choices(page):
    positions = probe(page, 24., """() => ['.pl-vspanel.l','.pl-vsmid','.pl-vspanel.r'].map(s=>{
       let b=document.querySelector('[data-scene=s03] '+s).getBoundingClientRect(); return (b.left+b.right)/2;
    })""")
    assert positions[0] < positions[1] < positions[2]


def test_catch_rows_follow_narration(page):
    js = "() => [...document.querySelectorAll('[data-scene=s04] .pl-vrow')].map(e=>parseFloat(e.style.opacity))"
    assert probe(page, 32., js)[0] == 1
    before = probe(page, 34., js)
    assert before[:2] == [1, 1] and before[2:] == [0, 0]
    assert probe(page, 38., js) == [1, 1, 1, 1]
