"""COVER-RULES.md as code. A cover that breaks a rule must fail here, not at review."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import cover_rules as cr  # noqa: E402


def concept(text, layout, media=None):
    return {"text": text, "layout": layout,
            "media": media or {"kind": "designed", "file": "d.png", "design": "laptop with browser and editor, agent on the left"}}


GOOD = [concept("CAN AI RUN YOUR PC?", "bleed"),
        concept("GET YOUR GUIDE TO INSTALL", "window"),
        concept("NOW AI RUNS YOUR PC", "split")]


def test_headline_four_to_five_words_all_caps():
    assert cr.headline_problems("CAN AI RUN YOUR PC?") == []
    assert cr.headline_problems("AI RUNS YOUR PC")  == []  # 4 words
    assert cr.headline_problems("Can AI run your PC?")   # not all caps
    assert cr.headline_problems("CAN AI RUN")            # 3 words
    assert cr.headline_problems("CAN AI RUN YOUR PC RIGHT NOW")  # 6 words
    assert cr.headline_problems("CAN AI RUN YOUR #1 PC")  # hashtag/emoji-like symbol


def test_three_concepts_distinct_layouts_required():
    assert cr.concepts_problems(GOOD) == []
    assert cr.concepts_problems(GOOD[:1])                       # one concept fails
    assert cr.concepts_problems([GOOD[0], GOOD[0], GOOD[2]])    # repeated layout/headline fails


def test_tool_media_needs_a_real_file_big_enough(tmp_path):
    from PIL import Image
    Image.new("RGB", (640, 320)).save(tmp_path / "small.png")
    Image.new("RGB", (1280, 640)).save(tmp_path / "big.png")
    assert cr.media_problems({"kind": "tool_media", "file": "small.png"}, tmp_path)
    assert cr.media_problems({"kind": "tool_media", "file": "big.png"}, tmp_path) == []
    assert cr.media_problems({"kind": "tool_media", "file": "absent.png"}, tmp_path)


def test_designed_media_needs_a_note_and_a_file(tmp_path):
    from PIL import Image
    Image.new("RGB", (1200, 1200)).save(tmp_path / "d.png")
    assert cr.media_problems({"kind": "designed", "file": "d.png", "design": "laptop with browser and editor windows"}, None, tmp_path) == []
    assert cr.media_problems({"kind": "designed", "file": "gone.png", "design": "laptop with browser and editor windows"}, None, tmp_path)
    assert cr.media_problems({"kind": "designed", "design": "laptop with browser and editor windows"})


def test_plan_cover_text_must_be_one_of_the_concepts():
    plan = {"id": "x", "cover": {"text": "NOT IN LIST HERE", "concepts": GOOD}}
    assert any("must be the headline" in p for p in cr.plan_cover_problems(plan))
    plan["cover"]["text"] = GOOD[1]["text"]
    assert cr.plan_cover_problems(plan) == []
