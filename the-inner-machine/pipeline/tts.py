#!/usr/bin/env python3
"""Kokoro TTS wrapper (offline). Voice locked via config; default bm_george.

Self-healing: auto-downloads the int8 model + voices bin to ~/.cache/kokoro on
first use, so the pipeline survives a full sandbox wipe. Atomic (.part -> rename)
so a half-download never poisons the cache. Override paths with KOKORO_MODEL /
KOKORO_VOICES. This module is independent of any other pipeline in the repo.
"""
import os, urllib.request

CACHE = os.path.expanduser("~/.cache/kokoro")
_BASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1"
MODEL_URL = f"{_BASE}/kokoro-v1.0.int8.onnx"
VOICES_URL = f"{_BASE}/voices-v1.0.bin"
MODEL = os.environ.get("KOKORO_MODEL", os.path.join(CACHE, "kokoro-v1.0.int8.onnx"))
VOICES = os.environ.get("KOKORO_VOICES", os.path.join(CACHE, "voices-v1.0.bin"))
_k = None


def _ensure(path, url, min_bytes):
    """Download `url` to `path` if missing/truncated. Atomic + idempotent."""
    if os.path.exists(path) and os.path.getsize(path) >= min_bytes:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".part"
    print(f"[tts] downloading {os.path.basename(path)} (~{min_bytes//1_000_000}MB+) ...", flush=True)
    try:
        urllib.request.urlretrieve(url, tmp)
        got = os.path.getsize(tmp)
        if got < min_bytes:
            raise RuntimeError(f"download truncated: {got} bytes < {min_bytes}")
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def _engine():
    global _k
    if _k is None:
        _ensure(MODEL, MODEL_URL, 50_000_000)    # int8 onnx ~109MB
        _ensure(VOICES, VOICES_URL, 20_000_000)  # voices bin ~27MB
        from kokoro_onnx import Kokoro
        _k = Kokoro(MODEL, VOICES)
    return _k


def lang_of(voice):
    """bm_*/bf_* are the British voices; everything else is US English."""
    return "en-gb" if voice[0] == "b" else "en-us"


def synth(text, voice="bm_george", speed=1.0, out=None):
    import soundfile as sf
    k = _engine()
    a, sr = k.create(text, voice=voice, speed=speed, lang=lang_of(voice))
    if out:
        sf.write(out, a, sr)
    return a, sr
