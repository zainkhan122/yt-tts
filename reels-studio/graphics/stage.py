"""Pipeline adapter: renders a Short's visuals from the voice's word timings.

Called by the production pipeline in place of the Hyperframes scene build when a brief sets
renderer = "graphics". Everything is fail-closed: a lint failure raises GraphicsError with the rule list,
and nothing is rendered.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path

from .beats import Violation, lint_beats, scene_list, script_fingerprint
from .features import lint_feature_sheet
from .render import render
from .timing import close_gaps


ROOT = Path(__file__).resolve().parents[1]
LOGO = ROOT / "brand" / "logo" / "avatar-1080.png"  # the same file the template end-card uses


def brand_block() -> dict:
    """Who the end-card is about: real logo (inline data URI), name, handle, tagline, button label.

    Owner rule (2026-10-18): the card shows the real brand logo, never a text initial.
    """
    cfg_path = ROOT / "config" / "channel.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}
    b = cfg.get("brand") if isinstance(cfg.get("brand"), dict) else cfg
    out = {"name": b.get("name") or cfg.get("name") or "Hypeless",
           "handle": b.get("handle") or cfg.get("handle") or "",
           "tagline": b.get("tagline") or cfg.get("tagline") or "",
           "cta_button": b.get("cta_button") or "Follow"}
    if LOGO.exists():
        out["logo"] = "data:image/png;base64," + base64.b64encode(LOGO.read_bytes()).decode("ascii")
    return out


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


def segments_from_timing(timing: dict, order: list[str]) -> list[dict]:
    """One phrase per brief scene, in voice order. The scene's own words set its on-screen span."""
    segs = []
    for sid in order:
        ws = timing[sid].get("words") or []
        if not ws:
            raise GraphicsError("words", [{"rule": "G1", "detail": f"scene {sid} has no word timings"}])
        segs.append({"sid": sid, "text": " ".join(str(w[0]) for w in ws), "words": ws,
                     "t0": round(float(ws[0][1]), 3), "t1": round(float(ws[-1][2]), 3)})
    return segs


def plan_scenes(sheet: dict, source_text: str, beats: dict, phrases: list[dict], duration: float, words: list[list],
                events: dict | None = None):
    f_viol = lint_feature_sheet(sheet, source_text)
    if f_viol:
        raise GraphicsError("feature_sheet", [v.as_dict() for v in f_viol])
    phrases = close_gaps(phrases, duration)
    b_viol = lint_beats(beats, phrases, sheet, script_fp=script_fingerprint(words))
    # B9 each beat is bound to the brief scene it was written for (voice order must not drift).
    for k, (sc, ph) in enumerate(zip(beats.get("scenes", []), phrases)):
        if sc.get("scene_id") is not None and sc["scene_id"] != ph["sid"]:
            b_viol.append(Violation("B9", f"beat {k} is for scene {sc['scene_id']!r}, voice has {ph['sid']!r}"))
    if b_viol:
        raise GraphicsError("beat_plan", [v.as_dict() for v in b_viol])
    doc = {"width": 1080, "height": 1920, "handle": beats.get("handle", ""), "scenes": scene_list(beats, phrases)}
    if any(s.get("archetype") == "endcard" for s in doc["scenes"]):
        doc["brand"] = brand_block()
        _attach_events(doc, events or {})
    return doc, phrases


def _attach_events(doc: dict, events: dict) -> None:
    """Give the end-card the pipeline's own times: the click SFX fires at events["press"], so the
    cursor press on screen must fire at that exact number, not at a re-derived guess."""
    press = events.get("press")
    keyword = next((v for k, v in events.items() if k.endswith("_keyword")), None)
    for sc in doc["scenes"]:
        if sc.get("archetype") != "endcard":
            continue
        ev = {}
        if isinstance(press, (int, float)):
            ev["press"] = round(float(press), 3)
        if isinstance(keyword, (int, float)):
            ev["keyword"] = round(float(keyword) + 0.08, 3)  # the template shows the chip 80 ms after the word
            sc["cue"] = ev["keyword"]
        if "press" in ev:
            sc["cues"] = [ev["press"]]
        if ev:
            sc["ev"] = ev


def render_for_pipeline(graphics_dir: Path, timing: dict, order: list[str], vo_wav: Path,
                        out_mp4: Path, work: Path, duration: float, events: dict | None = None) -> dict:
    """graphics_dir holds features.json, beats.json and the README snapshot the sheet was built from."""
    sheet = json.loads((graphics_dir / "features.json").read_text(encoding="utf-8"))
    source = (graphics_dir / "source.md").read_text(encoding="utf-8")
    beats = json.loads((graphics_dir / "beats.json").read_text(encoding="utf-8"))
    words = flatten_words(timing, order)
    if not words:
        raise GraphicsError("words", [{"rule": "G0", "detail": "no word timings from the voice stage"}])
    phrases = segments_from_timing(timing, order)
    doc, phrases = plan_scenes(sheet, source, beats, phrases, duration, words, events=events)
    work.mkdir(parents=True, exist_ok=True)
    (work / "scenes.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    info = render(doc, vo_wav, out_mp4, work, duration)
    fallbacks = {s["id"]: s.get("fallback", []) for s in doc["scenes"] if s.get("fallback")}
    info.update({"phrases": len(phrases), "scenes": len(doc["scenes"]), "cue_fallbacks": fallbacks,
                 "script_sha256": script_fingerprint(words)})
    return info
