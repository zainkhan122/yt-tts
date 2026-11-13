"""Lesson 24 (2026-11-11, owner): a template may NOT invent its own caption band or outro.

musike v1-v2 shipped grey lowercase captions and a custom green COMMENT button; the owner's
ruling is "keep our own style for text / outro". The house grammar is registered below as an
allow-list, and any new style must be added there deliberately, not slipped into a template.

Shared captions and outro are injected into every built stage. These tests verify that
injection and the required endcard payload; browser-level visibility is checked separately by
house_gate.py. Passing static tests is not visual approval.
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


def test_shared_caption_is_injected_for_every_template():
    from graphics.render import build_stage_html
    for tpl in _templates():
        html = build_stage_html({"template": "default" if tpl == TEMPLATES else tpl.name,
                                 "scenes": [], "handle": "@test"})
        assert ".yt-cap" in html and ".yt-cap .cw.hit" in html, tpl.name
        assert "suppressTemplateCaptions" in html and "window.setTime" in html, tpl.name


def test_shared_outro_is_injected_for_every_template():
    from graphics.render import build_stage_html
    for tpl in _templates():
        html = build_stage_html({"template": "default" if tpl == TEMPLATES else tpl.name,
                                 "scenes": [], "handle": "@test"})
        for marker in ("yt-outro-logo", "yt-outro-name", "yt-outro-follow", "yt-outro-kw", "yt-outro-cursor"):
            assert marker in html, f"{tpl.name}: missing house outro {marker}"


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
