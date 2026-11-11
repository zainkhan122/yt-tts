"""Voice handoff between the cloud voice job and the render job.

The voice job synthesizes and runs the per-chunk alignment QA once, then writes:
  <dir>/vo.wav        the exact audio that passed QA
  <dir>/voice.json    timing, order, duration, engine, and the sha256 of vo.wav

The render job loads both and does not synthesize again. The audio it renders is the audio
that was checked. Pure Python (no TTS or audio dependencies), so it can be tested anywhere.
"""
import hashlib
import json
import shutil
from pathlib import Path

WAV, META = "vo.wav", "voice.json"
SCHEMA = 1


def _jsonable(obj):
    """Plain JSON types only. Unknown types raise, so nothing is silently stringified."""
    if obj is None or isinstance(obj, (bool, int, str)):
        return obj
    if isinstance(obj, float):
        return float(obj)
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if hasattr(obj, "item") and callable(obj.item):  # numpy scalars
        return _jsonable(obj.item())
    raise TypeError(f"voice handoff cannot store {type(obj).__name__}")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_handoff(directory, wav_path, *, timing, order, duration, engine, engine_detail=None) -> dict:
    d = Path(directory)
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy2(wav_path, d / WAV)
    meta = {
        "schema": SCHEMA,
        "engine": str(engine),
        # The full audit string ("chatterbox exag0.7 cfg0.4 ref michael-ref.wav, flow (...)"). The queue
        # gate reads this: a render that reused the handoff used to record only "chatterbox", so an
        # approved-voice render could not be queued at all (found 7 Nov 2026).
        "engine_detail": str(engine_detail if engine_detail is not None else engine),
        "duration": float(duration),
        "order": [str(x) for x in order],
        "timing": _jsonable(timing),
        "vo_sha256": sha256_file(d / WAV),
    }
    (d / META).write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return meta


def read_handoff(directory) -> dict:
    d = Path(directory)
    meta_path, wav = d / META, d / WAV
    if not meta_path.exists() or not wav.exists():
        raise ValueError(f"voice handoff missing in {d} (need {META} and {WAV})")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("schema") != SCHEMA:
        raise ValueError(f"voice handoff schema {meta.get('schema')!r} is not {SCHEMA}")
    got = sha256_file(wav)
    if got != meta.get("vo_sha256"):
        raise ValueError(f"voice handoff audio changed: sha256 {got[:12]} != recorded {str(meta.get('vo_sha256'))[:12]}")
    return {"engine": meta["engine"], "engine_detail": meta.get("engine_detail", meta["engine"]),
            "duration": meta["duration"], "order": meta["order"],
            "timing": meta["timing"], "wav": wav, "vo_sha256": meta["vo_sha256"]}
