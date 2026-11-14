"""Lesson 24 (2026-11-11, owner): a template may NOT invent its own caption band or outro.

musike v1-v2 shipped grey lowercase captions and a custom green COMMENT button; the owner's
ruling is "keep our own style for text / outro". The house grammar is registered below as an
allow-list, and any new style must be added there deliberately, not slipped into a template.

The renderer has two tiers and each one owns exactly one caption band and one outro:

  * the HOUSE engine (the default template) draws its own: the highlight-chip caption band
    (`.caption` / `.cw-on`) and the house brand card (the real logo, never a text initial);
  * every PER-TOOL template gets the shared house layer instead — shared.js for the caption and
    outro.js for the brand card — so a tool cannot invent its own.

Both tiers therefore obey the ruling, and each is checked on its own terms. Static tests are not
visual approval: browser-level visibility is checked separately by house_gate.py.
"""
import json
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parents[1] / "templates"

# Registered kinetic-caption grammars: velocity-black/musike band (.cw.pk pink key words) and
# the highlight-chip variant (cw-on). Adding a third grammar is a doc'd decision, not an edit.
CAPTION_GRAMMARS = (".cw.pk", "cw-on")


def _template_dirs() -> list[Path]:
    return [d for d in sorted(TEMPLATES.iterdir()) if (d / "template.json").is_file()]


def test_the_house_engine_draws_the_house_caption_and_the_house_card():
    """The default template: one caption band, the registered grammar, the real brand."""
    css = (TEMPLATES / "stage.css").read_text(encoding="utf-8")
    assert ".caption" in css, "the house engine has no caption band"
    assert any(g in css for g in CAPTION_GRAMMARS), (
        f"house caption band uses an unregistered grammar — registered: {CAPTION_GRAMMARS}")
    eng = (TEMPLATES / "engine.js").read_text(encoding="utf-8")
    assert "ARCH.endcard" in eng, "the house engine has no endcard archetype"
    assert "brand" in eng, "the house card must render the injected brand block (D.brand)"


def test_shared_caption_is_injected_for_every_per_tool_template():
    from graphics.render import build_stage_html
    for tpl in _template_dirs():
        html = build_stage_html({"template": tpl.name, "scenes": [], "handle": "@test"})
        assert ".yt-cap" in html and ".yt-cap .cw.hit" in html, tpl.name
        assert "suppressTemplateCaptions" in html and "window.setTime" in html, tpl.name


def test_shared_outro_is_injected_for_every_per_tool_template():
    from graphics.render import build_stage_html
    for tpl in _template_dirs():
        html = build_stage_html({"template": tpl.name, "scenes": [], "handle": "@test"})
        for marker in ("yt-outro-logo", "yt-outro-name", "yt-outro-follow", "yt-outro-kw", "yt-outro-cursor"):
            assert marker in html, f"{tpl.name}: missing house outro {marker}"


def test_the_house_engine_is_not_given_the_shared_layer():
    """The house engine draws its own caption and its own card. Injecting the shared layer as well
    would put two captions on screen — the exact bug the shared layer exists to prevent."""
    from graphics.render import build_stage_html
    html = build_stage_html({"template": "default", "scenes": [], "handle": "@test"})
    assert "yt-cap" not in html, "the house engine must not also mount the shared caption"
    assert "yt-outro" not in html, "the house engine must not also mount the shared outro"


def test_endcard_override_never_weakens_the_house_spec():
    for tpl in [TEMPLATES] + _template_dirs():
        cfg = tpl / "template.json"
        if not cfg.exists():
            continue
        spec = (json.loads(cfg.read_text(encoding="utf-8")).get("archetypes") or {}).get("endcard")
        if spec is None:
            continue
        assert "keyword" in (spec.get("req") or []), (
            f"{tpl.name}: endcard override drops the keyword requirement — the COMMENT keyword chip "
            "is part of the house outro")
