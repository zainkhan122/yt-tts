"""Creative gates enforce measurable rules without pretending to score taste."""
from pathlib import Path
from PIL import Image
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import cover_lab
import cover_rules
import video_plan


def test_cover_layouts_use_safe_band_and_measured_contrast(tmp_path):
    vid = "demo-01"
    source = tmp_path / "covers" / vid
    source.mkdir(parents=True)
    texts = ["CAN AI CLICK YOUR APPS?", "YOUR APPS HAVE HIDDEN REFS", "WHEN THE REF GOES STALE"]
    concepts = []
    for n, (layout, text) in enumerate(zip(cover_rules.LAYOUTS, texts)):
        f = f"visual-{n}.png"
        Image.new("RGB", (1200, 900), (32 + n*20, 80, 90)).save(source / f)
        concepts.append({"layout": layout, "text": text, "media": {"kind": "designed", "file": f,
                         "design": "The actual workflow of this desktop tool."}})
    brief = {"id": vid, "treatment": {"cover_concepts": concepts}}
    _, report = cover_lab.make_concepts(brief, tmp_path / "output", root=tmp_path)
    assert cover_lab.audit(report) == []
    assert all(cover_rules.SAFE_TOP <= c["text_box"][1] < c["text_box"][3] <= cover_rules.SAFE_BOTTOM for c in report)
    assert cover_lab.FONT.name == "Inter.ttf"


def test_problem_hook_and_sourced_numbers_are_not_automatically_rejected():
    import json
    p = json.loads((ROOT / "videos/repo-agent-desktop-01/plan.json").read_text())
    p["question"] = "Stop guessing where your agent should click."
    p["points"][0]["spoken"] = "Install it with 1 command."
    issues = [msg for status, msg in video_plan.check(p) if status == "BLOCK"]
    assert not any("viewer-first hook" in x or "digits" in x for x in issues)
