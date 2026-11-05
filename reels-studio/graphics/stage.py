"""Pipeline adapter: renders a Short's visuals from the voice's word timings.

Called by the production pipeline in place of the Hyperframes scene build when a brief sets
renderer = "graphics". Everything is fail-closed: a lint failure raises GraphicsError with the rule list,
and nothing is rendered.
"""
from __future__ import annotations

import json
from pathlib import Path

from .beats import lint_beats, scene_list, script_fingerprint
from .features import lint_feature_sheet
from .render import render
from .timing import chunk_phrases, close_gaps


class GraphicsError(RuntimeError):
    def __init__(self, stage: str, violations: list[dict]):
        super().__init__(f"graphics {stage} failed: " + "; ".join(f"{v['rule']} {v['detail']}" for v in violations))
        self.stage = stage
        self.violations = violations


def flatten_words(timing: dict, order: list[str]) -> list[list]:
    words: list[list] = []
    for sid in order:
        for w in timing[sid].get("words") or []:
            words.append([str(w[0]), round(float(w[1]), 3), round(float(w[2]), 3)])
    return words


def plan_scenes(sheet: dict, source_text: str, beats: dict, words: list[list], duration: float):
    f_viol = lint_feature_sheet(sheet, source_text)
    if f_viol:
        raise GraphicsError("feature_sheet", [v.as_dict() for v in f_viol])
    phrases = close_gaps(chunk_phrases(words), duration)
    b_viol = lint_beats(beats, phrases, sheet, script_fp=script_fingerprint(words))
    if b_viol:
        raise GraphicsError("beat_plan", [v.as_dict() for v in b_viol])
    doc = {"width": 1080, "height": 1920, "handle": beats.get("handle", ""), "scenes": scene_list(beats, phrases)}
    return doc, phrases


def render_for_pipeline(graphics_dir: Path, timing: dict, order: list[str], vo_wav: Path,
                        out_mp4: Path, work: Path, duration: float) -> dict:
    """graphics_dir holds features.json, beats.json and the README snapshot the sheet was built from."""
    sheet = json.loads((graphics_dir / "features.json").read_text(encoding="utf-8"))
    source = (graphics_dir / "source.md").read_text(encoding="utf-8")
    beats = json.loads((graphics_dir / "beats.json").read_text(encoding="utf-8"))
    words = flatten_words(timing, order)
    if not words:
        raise GraphicsError("words", [{"rule": "G0", "detail": "no word timings from the voice stage"}])
    doc, phrases = plan_scenes(sheet, source, beats, words, duration)
    work.mkdir(parents=True, exist_ok=True)
    (work / "scenes.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    info = render(doc, vo_wav, out_mp4, work, duration)
    fallbacks = {s["id"]: s.get("fallback", []) for s in doc["scenes"] if s.get("fallback")}
    info.update({"phrases": len(phrases), "scenes": len(doc["scenes"]), "cue_fallbacks": fallbacks,
                 "script_sha256": script_fingerprint(words)})
    return info
