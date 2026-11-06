"""Draft plan remains bound to the written narration and its README snapshot."""
import json
from pathlib import Path
from graphics.stage import flatten_words, segments_from_timing, plan_scenes

ROOT = Path(__file__).resolve().parents[2]


def test_desktop_draft_is_grounded_and_cue_bound():
    p = ROOT / "briefs/graphics/repo-agent-desktop-01"
    brief = json.loads((ROOT / "briefs/repo-agent-desktop-01.json").read_text())
    plan = json.loads((ROOT / "videos/repo-agent-desktop-01/plan.json").read_text())
    lines = [plan["question"], *(point["spoken"] for point in plan["points"]), plan["catch"], plan["cta"]]
    assert lines == [s["say"] for s in brief["scenes"]]
    timing, order, t = {}, [], 0.2
    for scene in brief["scenes"]:
        words = []
        for word in scene["say"].split():
            words.append([word, round(t, 3), round(t + 0.22, 3)])
            t += 0.3
        timing[scene["id"]] = {"words": words}
        order.append(scene["id"])
        t += 0.15
    doc, _ = plan_scenes(json.loads((p / "features.json").read_text()), (p / "source.md").read_text(),
                         json.loads((p / "beats.json").read_text()), segments_from_timing(timing, order),
                         t + 0.2, flatten_words(timing, order))
    assert not {s["id"]: s["fallback"] for s in doc["scenes"] if s["fallback"]}
    assert doc["scenes"][0]["archetype"] == "desktop_action"
    assert doc["handle"] == json.loads((ROOT / "config/channel.json").read_text())["brand"]["handle"]
    assert 100 <= len(" ".join(lines).split()) <= 125
    assert brief["review"]["reviewed_at"] is None


def test_cli_enforces_script_fingerprint(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from graphics import cli
    p = ROOT / "graphics/fixtures/craft-anything"
    words = json.loads((p / "words.json").read_text())
    words[0][0] = "changed"
    f = tmp_path / "words.json"
    f.write_text(json.dumps(words))
    args = SimpleNamespace(sheet=str(p / "features.json"), source=str(p / "source.md"),
                           words=str(f), beats=str(p / "beats.json"), duration=None)
    _, violations, code = cli._plan(args)
    assert code == 3 and any(v.rule == "B0" for v in violations)
