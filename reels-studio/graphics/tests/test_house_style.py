"""Lesson 24 (2026-11-11, owner): a template may NOT invent its own caption band or outro.

musike v1-v2 shipped grey lowercase captions and a custom green COMMENT button; the owner's
ruling is "keep our own style for text / outro". The house grammar is registered below as an
allow-list, and any new style must be added there deliberately, not slipped into a template.

Three checks per graphics template (the four template dirs + the default root pair):
1. captions exist and use a REGISTERED grammar (pink key words OR highlight-chip active word);
2. every endcard archetype reads the injected brand block (the house outro is about D.brand);
3. a per-template endcard override may not weaken the house spec (keyword stays required).
"""
import json
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parents[1] / "templates"

# Registered kinetic-caption grammars: velocity-black/musike band (.cw.pk pink key words) and
# the highlight-chip variant (cw-on). Adding a third grammar is a doc'd decision, not an edit.
CAPTION_GRAMMARS = (".cw.pk", "cw-on")


def _templates() -> list[Path]:
    dirs = [d for d in sorted(TEMPLATES.iterdir()) if (d / "template.json").is_file()]
    return [TEMPLATES] + dirs  # the default root pair obeys the same house rules


def test_captions_exist_and_use_a_registered_grammar():
    for tpl in _templates():
        css = (tpl / "stage.css").read_text(encoding="utf-8")
        assert ".caption" in css, f"{tpl.name}: no caption band at all"
        assert any(g in css for g in CAPTION_GRAMMARS), (
            f"{tpl.name}: caption band uses an unregistered grammar — registered: {CAPTION_GRAMMARS}")


def test_endcard_is_the_house_brand_outro():
    for tpl in _templates():
        eng = (tpl / "engine.js").read_text(encoding="utf-8")
        assert "ARCH.endcard" in eng, f"{tpl.name}: no endcard archetype"
        assert "brand" in eng, f"{tpl.name}: endcard must render the injected brand block (D.brand)"


def test_endcard_override_never_weakens_the_house_spec():
    for tpl in _templates():
        cfg = tpl / "template.json"
        if not cfg.exists():
            continue
        spec = (json.loads(cfg.read_text(encoding="utf-8")).get("archetypes") or {}).get("endcard")
        if spec is None:
            continue
        assert "keyword" in (spec.get("req") or []), (
            f"{tpl.name}: endcard override drops the keyword requirement — the COMMENT keyword chip "
            "is part of the house outro")
