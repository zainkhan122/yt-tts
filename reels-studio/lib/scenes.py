"""Scene manifest + single-scene rebuild logic (pure, import-light).

A published video is not one indivisible artifact: it is a list of scenes with exact
start/end times (see pipeline stage 3). This module defines the durable per-scene
record that makes one scene repairable without touching the others, and the decision
logic behind `reels.py rebuild`:

  * scene record  - id, type, window, narration digest, visual spec digest, word
                    timings, referenced assets (name + digest). Written into
                    renders/<id>/manifest.json and shipped in the kit.
  * plan_rebuild  - given the previous manifest and the new brief, decide what can be
                    rebuilt and refuse what cannot. Narration is the boundary: the
                    spoken text determines the audio timeline, and the audio is reused
                    bit-for-bit from the published MP4, so ANY narration change means
                    a full render, not a rebuild.
  * frame_drift   - per-sample comparison used to prove that unchanged scenes stayed
                    unchanged after a rebuild (re-encode tolerance, not exact bytes).

Pure functions only (stdlib + PIL for images), no numpy/soundfile: the post.yml and
youtube.yml safety suites run without the heavy render dependencies and still get the
unit tests for this module.
"""
import hashlib
import json

NARRATION_CHANGED = "narration-changed"
UNKNOWN_SCENE = "unknown-scene"
PREV_MANIFEST_MISSING = "previous-render-has-no-scene-manifest"

# Rebuild verification tolerances. The rebuilt video is re-encoded (same settings) and
# re-rendered by a browser, so byte equality is not achievable; unchanged scenes must
# instead stay visually identical within encoder noise. Measured on the 2026-10-12
# validation rebuild (tool-ltx25-01): see the receipt for the recorded drift values.
FRAME_MAD_LIMIT = 2.0      # mean absolute per-channel difference, 0-255 scale
FRAME_HEAVY_LIMIT = 0.03   # share of pixels differing by more than 8/255
DURATION_TOL_SECS = 0.06


def sha_bytes(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sha_text(text):
    return sha_bytes((text or "").encode("utf-8"))


def sha_obj(obj):
    return sha_text(json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")))


def sha_file(path, _cache={}):
    path = str(path)
    if path not in _cache:
        _cache[path] = sha_bytes(open(path, "rb").read())
    return _cache[path]


def narration_digest(spoken_text):
    """Digest of the spoken form of a scene line (display markup and lexicon applied).

    Only the narration matters here: a change means different audio, a different
    timeline, and therefore a full render.
    """
    return sha_text(spoken_text or "")


def spec_digest(scene):
    """Digest of the visual/authoring spec of one scene (everything except narration)."""
    return sha_obj(scene or {})


def scene_record(index, scene_id, scene_type, window, narration, spec, words, assets, text=None, caption=None, spoken=None):
    """One entry of manifest['scenes'] - the unit a rebuild repairs and verifies."""
    start, end = window
    record = {
        "index": index,
        "id": scene_id,
        "type": scene_type,
        "start": round(start, 3),
        "end": round(end, 3),
        "duration": round(end - start, 3),
        "text": text if text is not None else (spec or {}).get("say", ""),
        "spoken": spoken if spoken is not None else (spec or {}).get("say", ""),
        "caption": bool(caption),
        "narration_sha256": narration_digest(narration),
        "spec_sha256": spec_digest(spec) if spec is not None else None,
        "words": words or [],
        "assets": assets or [],
    }
    if spec is not None:
        record["say"] = spec.get("say", "")
    return record


def changed_scenes(prev_scenes, new_specs, new_narration):
    """Split the difference between a published manifest and the current brief.

    Returns (visual_changes, narration_changes, unknown) - scene ids. `unknown` are
    brief scenes that do not exist in the published manifest (a new scene changes the
    timeline shape: that is a full render, not a rebuild).
    """
    prev = {s["id"]: s for s in prev_scenes}
    visual, narration, unknown = [], [], []
    for scene_id, spec in new_specs.items():
        old = prev.get(scene_id)
        if old is None:
            unknown.append(scene_id)
            continue
        if narration_digest(new_narration.get(scene_id, "")) != old.get("narration_sha256"):
            narration.append(scene_id)
        elif spec_digest(spec) != old.get("spec_sha256"):
            visual.append(scene_id)
    return sorted(visual), sorted(narration), sorted(unknown)


def plan_rebuild(prev_manifest, new_specs, new_narration, requested):
    """Decide the effective rebuild set, or refuse with a machine-readable reason.

    `requested` is what the operator asked to re-render; every scene whose visual spec
    changed is added automatically so the published video can never disagree with the
    brief. Refusals (narration change, new scene, unknown id, no manifest) mean the
    caller must run a full render (`reels.py cloud`) instead.
    """
    scenes = (prev_manifest or {}).get("scenes") or []
    if not scenes:
        return {"ok": False, "reason": PREV_MANIFEST_MISSING}
    ids = {s["id"] for s in scenes}
    unknown_requested = [s for s in requested if s not in ids]
    if unknown_requested:
        return {"ok": False, "reason": UNKNOWN_SCENE, "scenes": unknown_requested}
    visual, narration, unknown = changed_scenes(scenes, new_specs, new_narration)
    if narration or unknown:
        return {"ok": False, "reason": NARRATION_CHANGED, "scenes": sorted(set(narration) | set(unknown)),
                "detail": "spoken text or scene list changed: audio is reused bit-for-bit, so this needs a full render"}
    effective = sorted(set(requested) | set(visual))
    return {"ok": True, "effective": effective, "visual_changes": visual, "requested": sorted(requested)}


def frame_drift(a_png, b_png):
    """Compare two frames of the same size: mean absolute difference + heavy-pixel share.

    PIL only (no numpy): the post.yml/youtube.yml safety suites run without the render
    dependency set, and these numbers are what the rebuild verification gate reads.
    """
    from PIL import Image, ImageChops, ImageStat
    a = Image.open(a_png).convert("RGB")
    b = Image.open(b_png).convert("RGB")
    if a.size != b.size:
        return {"match": False, "detail": f"frame size changed {a.size} -> {b.size}"}
    diff = ImageChops.difference(a, b)
    per_channel = diff.split()
    worst = per_channel[0]
    for channel in per_channel[1:]:
        worst = ImageChops.lighter(worst, channel)  # per-pixel maximum channel difference
    mean_abs = ImageStat.Stat(worst).mean[0]
    hist = worst.histogram()
    total = a.size[0] * a.size[1]
    heavy = sum(hist[9:]) / total
    return {"match": True, "mean_abs": round(mean_abs, 3), "heavy_ratio": round(heavy, 5), "n_pixels": total}


def frames_verdict(drifts, mad_limit=FRAME_MAD_LIMIT, heavy_limit=FRAME_HEAVY_LIMIT):
    """A rebuild passes when every unchanged-scene sample is within encoder-noise limits."""
    bad = [d for d in drifts if not d.get("match") or d.get("mean_abs", 1e9) > mad_limit or d.get("heavy_ratio", 1) > heavy_limit]
    worst = max((d.get("mean_abs", 0.0) for d in drifts), default=0.0)
    return {"ok": not bad, "samples": len(drifts), "worst_mean_abs": round(worst, 3),
            "failed": [d.get("at") for d in bad]}


def duration_verdict(prev_duration, new_duration, tol=DURATION_TOL_SECS):
    delta = abs(float(new_duration) - float(prev_duration))
    return {"ok": delta <= tol, "delta": round(delta, 4), "prev": prev_duration, "new": new_duration}


def sample_times(scenes, rebuilt_ids, per_scene=3):
    """Sample points inside scenes that were NOT rebuilt (25%, 50%, 75% of each window)."""
    rebuilt = set(rebuilt_ids)
    times = []
    for scene in scenes:
        if scene["id"] in rebuilt or scene.get("duration", 0) < 0.4:
            continue
        for frac in [0.25, 0.5, 0.75][:per_scene]:
            times.append(round(scene["start"] + scene["duration"] * frac, 3))
    return times
