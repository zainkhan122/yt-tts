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
from .visual_language import language_for, palette_for


ROOT = Path(__file__).resolve().parents[1]
LOGO = ROOT / "brand" / "logo" / "avatar-1080.png"  # the same file the template end-card uses


def brand_block() -> dict:
    """Who the end-card is about: real logo (inline data URI), name, handle, tagline, button label.

    Owner rule (2026-10-18): the card shows the real brand logo, never a text initial.
    """
    cfg_path = ROOT / "config" / "channel.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8-sig")) if cfg_path.exists() else {}
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


def build_doc(sheet: dict, beats: dict, phrases: list[dict]) -> dict:
    """The scene document: the beats joined to the phrase timing, plus the visual language.

    Shared by the pipeline adapter and the CLI so a clip built from the command line looks exactly
    like the same clip built by the pipeline: the tool's category decides the accent pair, the
    per-tool template is selected, and the end-card gets the real brand block.
    """
    doc = {"width": 1080, "height": 1920, "handle": beats.get("handle", ""), "scenes": scene_list(beats, phrases)}
    lang = language_for(sheet.get("tool"))
    doc["category"] = lang["category"]
    doc["palette"] = palette_for(sheet.get("tool"))
    doc["plates"] = lang.get("plates") or []
    if beats.get("template"):
        doc["template"] = beats["template"]  # per-tool template: its own archetypes, css and engine
    if any(s.get("archetype") == "endcard" for s in doc["scenes"]):
        doc["brand"] = brand_block()
    return doc


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
    doc = build_doc(sheet, beats, phrases)
    if any(s.get("archetype") == "endcard" for s in doc["scenes"]):
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


def attach_evidence_images(doc: dict, capture_id: str) -> None:
    """Embed only safe, locally captured stills; missing or escaping media fails closed.

    Upstream feature, kept in the house engine: a scene may carry an `evidence_image` (a still
    captured from the tool itself). Nothing is fetched from the network here, and a path that
    escapes the capture folder, or a file that is missing, stops the render instead of silently
    shipping a broken frame.
    """
    import base64
    import re
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", capture_id):
        raise ValueError("invalid evidence capture id")
    cap = (Path(__file__).resolve().parents[1] / "captures" / capture_id).resolve()
    for scene in doc.get("scenes", []):
        name = scene.get("evidence_image")
        if not name:
            continue
        if not isinstance(name, str) or Path(name).name != name or Path(name).suffix.lower() not in (".jpg", ".jpeg", ".png"):
            raise ValueError("unsafe evidence image")
        path = (cap / name).resolve()
        if not path.is_relative_to(cap) or not path.is_file():
            raise FileNotFoundError(f"evidence image unavailable: {capture_id}/{name}")
        mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
        scene["evidence_data"] = f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def attach_evidence_clips(doc: dict, capture_id: str, work: Path | None = None, fps: float = 4.0,
                          width: int = 882, height: int | None = 406) -> None:
    """Play a captured screen recording as the scene's product proof.

    A scene may carry an `evidence_clip` (a real recording of the tool's own page). The frames are
    cut locally by ffmpeg and written next to the stage file, so the stage HTML references them
    instead of carrying megabytes of base64. A path that escapes the capture folder, a missing
    file, or a clip with no readable frame stops the render instead of shipping a page with a hole
    in it.

    The frames are cut at `fps` in the recording's own order: the shot plays the product the way a
    person recorded it, instead of holding one still screenshot (the owner's bar: no full static
    screenshot held over a second).
    """
    import re
    from .media import clip_duration, cut_clip_frames
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", capture_id):
        raise ValueError("invalid evidence capture id")
    cap = (Path(__file__).resolve().parents[1] / "captures" / capture_id).resolve()
    for scene in doc.get("scenes", []):
        name = scene.get("evidence_clip")
        if not name:
            continue
        if not isinstance(name, str) or Path(name).name != name or Path(name).suffix.lower() not in (".mp4", ".webm", ".mov"):
            raise ValueError("unsafe evidence clip")
        path = (cap / name).resolve()
        if not path.is_relative_to(cap) or not path.is_file():
            raise FileNotFoundError(f"evidence clip unavailable: {capture_id}/{name}")
        if work is None:
            # No stage directory to write into: keep the old in-memory path (a handful of stills).
            from .media import clip_frames
            frames = clip_frames(path)
            if not frames:
                raise RuntimeError(f"evidence clip has no readable frames: {capture_id}/{name}")
            import base64
            scene["evidence_frames"] = [f"data:image/jpeg;base64,{base64.b64encode(b).decode('ascii')}"
                                        for b in frames]
            scene["evidence_frame_count"] = len(frames)
            scene["evidence_fps"] = 0.0
            scene["evidence_duration"] = clip_duration(path)
            continue
        out_dir = work / "evidence" / Path(name).stem
        files = cut_clip_frames(path, out_dir, fps=fps, width=width, height=height)
        if not files:
            raise RuntimeError(f"evidence clip has no readable frames: {capture_id}/{name}")
        rel = out_dir.relative_to(work).as_posix()
        # One cut per clip, shared by every scene that shows it.
        scene["evidence_frames"] = [f"{rel}/{f.name}" for f in files]
        scene["evidence_frame_count"] = len(files)
        scene["evidence_fps"] = fps
        scene["evidence_duration"] = clip_duration(path)


def require_house_outro_plan(doc: dict) -> None:
    """Enforce shared final endcard with timed spoken CTA, before a production render."""
    import re
    scenes = doc.get("scenes") or []
    if not scenes or scenes[-1].get("archetype") != "endcard":
        raise GraphicsError("house_outro", [{"rule":"H1", "detail":"final scene must be shared house endcard"}])
    end = scenes[-1]
    keyword = str((end.get("payload") or {}).get("keyword") or "")
    words = end.get("words") or []
    spoken = [re.sub(r"[^a-z0-9]", "", str(w[0]).lower()) for w in words]
    duration = float(end.get("t1", 0)) - float(end.get("t0", 0))
    if (not re.fullmatch(r"[A-Za-z0-9]{1,18}", keyword) or not words or duration < 4
            or any(x not in spoken for x in ("comment", keyword.lower(), "follow", "hypeless"))):
        raise GraphicsError("house_outro", [{"rule":"H2", "detail":"endcard needs >=4s, aligned spoken comment, keyword, follow and Hypeless"}])
    brand = doc.get("brand") or {}
    if not brand.get("logo") or brand.get("cta_button") != "Follow":
        raise GraphicsError("house_outro", [{"rule":"H3", "detail":"house logo and Follow button required"}])


def render_for_pipeline(graphics_dir: Path, timing: dict, order: list[str], vo_wav: Path,
                        out_mp4: Path, work: Path, duration: float, events: dict | None = None) -> dict:
    """graphics_dir holds features.json, beats.json and the README snapshot the sheet was built from."""
    sheet = json.loads((graphics_dir / "features.json").read_text(encoding="utf-8-sig"))
    source = (graphics_dir / "source.md").read_text(encoding="utf-8")
    beats = json.loads((graphics_dir / "beats.json").read_text(encoding="utf-8-sig"))
    words = flatten_words(timing, order)
    if not words:
        raise GraphicsError("words", [{"rule": "G0", "detail": "no word timings from the voice stage"}])
    phrases = segments_from_timing(timing, order)
    doc, phrases = plan_scenes(sheet, source, beats, phrases, duration, words, events=events)
    require_house_outro_plan(doc)
    work.mkdir(parents=True, exist_ok=True)
    attach_evidence_images(doc, graphics_dir.name)
    # The evidence frames are written next to the stage file, so they must exist before it is built.
    attach_evidence_clips(doc, graphics_dir.name, work=work)
    (work / "scenes.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    info = render(doc, vo_wav, out_mp4, work, duration)
    fallbacks = {s["id"]: s.get("fallback", []) for s in doc["scenes"] if s.get("fallback")}
    info.update({"phrases": len(phrases), "scenes": len(doc["scenes"]), "cue_fallbacks": fallbacks,
                 "script_sha256": script_fingerprint(words)})
    return info
