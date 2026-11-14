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
    for marker in ('da-artboard', 'da-swatches', 'da-proof-ui', 'da-chart'):
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


def test_product_proof_is_in_the_rendered_scene_not_just_the_brief():
    import json
    from graphics.stage import attach_evidence_images
    for short in ('repo-design-agent-01', 'tool-pika-flex-01'):
        brief = json.loads((ROOT/'briefs'/f'{short}.json').read_text())
        beats = json.loads((ROOT/'briefs'/'graphics'/short/'beats.json').read_text())
        refs = {s.get('image') for s in brief['scenes'] if s.get('type') == 'image'}
        proofs = [s.get('evidence_image') for s in beats['scenes'] if s.get('evidence_image')]
        assert proofs and set(proofs) <= refs
        for scene in beats['scenes']:
            if scene.get('evidence_image'):
                source = next(x for x in brief['scenes'] if x.get('image') == scene['evidence_image'])
                assert scene.get('evidence_focus') == source.get('focus') and len(source['focus']) >= 2
        doc = {'scenes': [{'evidence_image': n} for n in proofs]}
        attach_evidence_images(doc, short)
        assert all(s['evidence_data'].startswith('data:image/') for s in doc['scenes'])
