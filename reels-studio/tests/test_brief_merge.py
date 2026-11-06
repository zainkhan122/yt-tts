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
    assert out["status"] == "draft" and out["review"]["reviewer"] is None
    assert out["scenes"] == [{"id": "new"}]          # copy and scenes come from the plan
    assert out["seo"] == {"youtube": {"title": "t"}}


def test_generated_keys_win_except_kept_ones():
    existing = {"scenes": [{"id": "old"}], "title": "old title"}
    gen = {"scenes": [{"id": "new"}], "title": "new title"}
    out = bfp.merge_brief(existing, gen)
    assert out["title"] == "new title" and out["scenes"] == [{"id": "new"}]


def test_unchanged_content_keeps_review():
    existing = {"scenes": [{"id": "a", "say": "hello"}], "status": "approved", "review": {"reviewer": "owner"}}
    out = bfp.merge_brief(existing, {"scenes": [{"id": "a", "say": "hello"}], "status": "draft", "review": {}})
    assert out["status"] == "approved" and out["review"] == {"reviewer": "owner"}


def test_graphics_brief_build_does_not_require_capture_cards(tmp_path, monkeypatch):
    import json
    plan = json.loads((ROOT / "videos/repo-agent-desktop-01/plan.json").read_text())
    (tmp_path / "briefs").mkdir()
    old = {"id": plan["id"], "renderer": "graphics", "graphics": {"dir": "briefs/graphics/example"},
           "status": "approved", "review": {"reviewer": "owner"}, "scenes": [{"say": "old"}]}
    (tmp_path / "briefs" / (plan["id"] + ".json")).write_text(json.dumps(old))
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan))
    monkeypatch.setattr(bfp, "ROOT", tmp_path)
    out = json.loads(bfp.build(plan_path).read_text())
    assert out["renderer"] == "graphics" and out["status"] == "draft"
    assert out["review"]["reviewer"] is None
    assert out["scenes"][0]["say"] == plan["question"]
    assert not (tmp_path / "captures").exists()
