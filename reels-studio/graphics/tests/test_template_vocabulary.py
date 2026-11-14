"""The lint vocabulary must match what each engine can actually draw.

A beat plan names its archetypes; the linter either allows them or refuses them. If the linter's
vocabulary is wider than the engine, a plan lints clean and then crashes on the first frame. If it
is narrower, a shipped brief is refused and the pipeline stalls. Both are regressions this test
catches at the source: the vocabulary is derived from the engine plus the template's declaration.

The house engine keeps the house archetypes. A per-tool engine draws its own scenes and never
reads window.HOUSE, so it must NOT claim a house archetype (B11 refuses it) — and it must accept
every archetype its own template.json declares.
"""
from pathlib import Path

from graphics.beats import (HOUSE_ARCHETYPES, archetypes, implemented_archetypes,
                             template_archetypes)

TEMPLATES = Path(__file__).resolve().parents[1] / "templates"


def _template_dirs() -> list[Path]:
    return [d for d in sorted(TEMPLATES.iterdir()) if (d / "template.json").is_file()]


def test_the_house_engine_keeps_the_house_vocabulary():
    house = set(archetypes("default"))
    assert HOUSE_ARCHETYPES <= house, "the house engine must be able to draw every house archetype"
    assert "endcard" in house


def test_every_template_accepts_every_archetype_it_declares():
    for tpl in _template_dirs():
        declared = template_archetypes(tpl.name)
        assert declared, f"{tpl.name}: template.json declares no archetype"
        missing = declared - set(archetypes(tpl.name))
        assert not missing, f"{tpl.name}: declared but not lintable: {sorted(missing)}"


def test_a_per_tool_engine_does_not_claim_the_house_archetypes():
    for tpl in _template_dirs():
        house_claims = HOUSE_ARCHETYPES & set(archetypes(tpl.name))
        assert not house_claims, (
            f"{tpl.name}: claims house archetypes it cannot draw: {sorted(house_claims)}")


def test_the_lintable_vocabulary_is_never_wider_than_the_engine():
    """Nothing may be lintable unless the engine implements it or the template declares it."""
    for tpl in _template_dirs():
        impl = implemented_archetypes(tpl.name)
        declared = template_archetypes(tpl.name)
        allowed = set(archetypes(tpl.name))
        # 'endcard' is the house outro: every template draws it through the shared layer.
        assert allowed <= (impl | declared | {"endcard"}), (
            f"{tpl.name}: lintable archetypes the engine cannot draw: "
            f"{sorted(allowed - (impl | declared | {'endcard'}))}")
