"""Guard against accidentally reverting the two commissioned shorts to copied layouts.
These structural checks are not a substitute for visual comparison or creative review.
"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

def template(name, file):
    return (ROOT / 'graphics' / 'templates' / name / file).read_text()

def test_pika_uses_reference_and_audio_visual_vocabulary():
    js = template('pika-flex', 'engine.js')
    for marker in ('pk-thumb', 'pk-film', 'pk-wave', 'pk-track'):
        assert marker in js
    assert 'ARCH.spec_plates' not in js
    assert 'CONCEPT ILLUSTRATION' in js

def test_design_agent_uses_brand_studio_vocabulary():
    js = template('design-agent', 'engine.js')
    for marker in ('da-artboard', 'da-swatches', 'da-flow', 'da-chart'):
        assert marker in js
    assert 'ARCH.spec_plates' not in js
    assert 'NOT A SLACK RECORDING' in js

def test_templates_have_distinct_implementations_and_reserve_house_outro():
    a, b = (template(x, 'engine.js') for x in ('pika-flex','design-agent'))
    assert a != b
    for s in (a,b):
        assert 'house-endcard-host' in s
        assert 'HouseMotion.cueTimes' in s
    for x in ('pika-flex','design-agent'):
        assert 'Seedance' not in json.loads(template(x, 'template.json'))['note']
