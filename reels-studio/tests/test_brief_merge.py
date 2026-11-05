"""Regenerating a brief must keep operator decisions (renderer, voice seed, review, status)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import brief_from_plan as bfp  # noqa: E402


def test_no_existing_brief_returns_generated():
    gen = {"id": "x", "scenes": []}
    assert bfp.merge_brief(None, gen) == gen


def test_operator_fields_survive_regeneration():
    existing = {"id": "x", "renderer": "graphics", "graphics": {"engine": "v2"}, "voice_seed": 0,
                "status": "approved", "review": {"reviewer": "owner"}, "qa_gates": True,
                "notes": "keep me", "scenes": [{"id": "old"}]}
    gen = {"id": "x", "scenes": [{"id": "new"}], "status": "draft", "review": {"reviewer": "agent"},
           "seo": {"youtube": {"title": "t"}}}
    out = bfp.merge_brief(existing, gen)
    assert out["renderer"] == "graphics" and out["graphics"] == {"engine": "v2"}
    assert out["voice_seed"] == 0 and out["notes"] == "keep me"
    assert out["status"] == "approved" and out["review"] == {"reviewer": "owner"}
    assert out["scenes"] == [{"id": "new"}]          # copy and scenes come from the plan
    assert out["seo"] == {"youtube": {"title": "t"}}


def test_generated_keys_win_except_kept_ones():
    existing = {"scenes": [{"id": "old"}], "title": "old title"}
    gen = {"scenes": [{"id": "new"}], "title": "new title"}
    out = bfp.merge_brief(existing, gen)
    assert out["title"] == "new title" and out["scenes"] == [{"id": "new"}]
