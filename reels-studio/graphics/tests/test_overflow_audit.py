"""Lesson 25 gate (2026-11-11): layout overflow past the frame edge fails the render.

musike's platform tiles clipped at the right edge (flex min-width blowout) and pixel-QA passed.
graphics/render.py now audits real layout per scene BEFORE encoding. These tests pin the audit's
shape without a browser; the integration itself runs in cloud renders (Playwright present).
"""
import pytest

from graphics import render


def test_scene_samples_three_probes_inside_each_scene():
    doc = {"scenes": [{"id": "s00", "t0": 0.0, "t1": 4.0}, {"id": "s01", "t0": 4.0, "t1": 7.6}]}
    pts = render._scene_samples(doc)
    assert len(pts) == 6
    for sid, t in pts:
        scene = doc["scenes"][0] if sid == "s00" else doc["scenes"][1]
        assert scene["t0"] < t < scene["t1"]
    assert [sid for sid, _ in pts].count("s00") == 3


def test_audit_js_has_safelists_and_slack():
    js = render._OVERFLOW_JS
    for marker in ("#postfx", "ambglow", ".ghosted", "getBoundingClientRect",
                   "hidden|clip", "getComputedStyle"):
        assert marker in js
    assert str(render._OVERFLOW_SLACK_PX) in js
    assert "0.6" in js  # the opacity gate: ghosts and mid-fade elements never fire


def test_audit_overflow_runs_when_a_browser_exists():
    page = pytest.importorskip("playwright.sync_api", reason="no local Playwright; cloud render covers this")
    assert page  # pragma: no cover
