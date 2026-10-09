#!/usr/bin/env python3
"""
Voice lab: render the same script in several TTS engines/settings so the owner can LISTEN and pick.
Runs in GitHub Actions (.github/workflows/voice-lab.yml: 4 vCPU / 16 GB, CPU only), samples go to the
`voice-lab` release. Engines:
  kokoro      Kokoro-82M ONNX (current production voice), params: voice, speed
  chatterbox  Resemble AI Chatterbox (MIT), params: exaggeration (0.5 neutral .. 1.0 dramatic), cfg (pacing),
              ref = "kokoro:<voice>" (clone our current timbre from a Kokoro reference clip) or omitted (built-in voice)

  python3 voice-lab/lab.py voice-lab/script.json --out /tmp/lab
"""
import argparse
import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
import soundfile as sf

KOKORO_DIR = Path.home() / ".cache/kokoro"
KOKORO_FILES = {"kokoro-v1.0.onnx": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
                "voices-v1.0.bin": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"}
_K = None
_CB = None


def spoken(t):
    return re.sub(r"\{([^|}]*)\|([^}]*)\}", r"\2", t)


def kokoro():
    global _K
    if _K is None:
        KOKORO_DIR.mkdir(parents=True, exist_ok=True)
        for name, url in KOKORO_FILES.items():
            if not (KOKORO_DIR / name).exists():
                urllib.request.urlretrieve(url, KOKORO_DIR / name)
        from kokoro_onnx import Kokoro
        _K = Kokoro(str(KOKORO_DIR / "kokoro-v1.0.onnx"), str(KOKORO_DIR / "voices-v1.0.bin"))
    return _K


def chatterbox():
    global _CB
    if _CB is None:
        from chatterbox.tts import ChatterboxTTS
        _CB = ChatterboxTTS.from_pretrained(device="cpu")
    return _CB


def resample(x, sr, to=24000):
    if sr == to:
        return x
    import librosa
    return librosa.resample(x, orig_sr=sr, target_sr=to)


def trim(x, sr, thr=0.01):
    idx = np.where(np.abs(x) > thr)[0]
    if not len(idx):
        return x
    a, b = max(0, idx[0] - int(0.02 * sr)), min(len(x), idx[-1] + int(0.06 * sr))
    return x[a:b]


def say_kokoro(text, voice, speed):
    x, sr = kokoro().create(text, voice=voice, speed=speed, lang="en-us")
    return trim(resample(np.asarray(x, dtype=np.float32), sr), 24000)


def say_chatterbox(text, exaggeration, cfg, ref):
    m = chatterbox()
    kw = {"exaggeration": exaggeration, "cfg_weight": cfg}
    if ref:
        kw["audio_prompt_path"] = str(ref)
    wav = m.generate(text, **kw)
    x = wav.squeeze().detach().cpu().numpy().astype(np.float32)
    return trim(resample(x, m.sr), 24000)


def loudnorm(x, sr, target=-16.0):
    import pyloudnorm as pyln
    meter = pyln.Meter(sr)
    lufs = meter.integrated_loudness(x)
    y = pyln.normalize.loudness(x, lufs, target) if np.isfinite(lufs) else x
    peak = float(np.max(np.abs(y))) or 1.0
    return y / peak * 0.97 if peak > 0.97 else y


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("--out", default="/tmp/lab")
    ap.add_argument("--only", default=None, help="comma list of variant names")
    a = ap.parse_args()
    spec = json.loads(Path(a.script).read_text())
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    refs = {}
    report = []
    for v in spec["variants"]:
        if a.only and v["name"] not in a.only.split(","):
            continue
        lines = spec["scripts"][v["script"]]
        ref = None
        if v.get("ref", "").startswith("kokoro:"):
            rv = v["ref"].split(":", 1)[1]
            if rv not in refs:  # cloning reference: our current voice reading a lively passage at natural speed
                x = say_kokoro(spec["reference_text"], rv, 1.0)
                refs[rv] = out / f"ref-{rv}.wav"
                sf.write(refs[rv], x, 24000)
            ref = refs[rv]
        t0 = time.time()
        parts = []
        if v.get("flow"):  # one continuous read (creators: ~1.5 pauses/min): whole script, chunked only for engine limits
            text = " ".join(spoken(ln["text"] if isinstance(ln, dict) else ln) for ln in lines)
            sents = re.split(r"(?<=[.!?])\s+", text)
            limit = v.get("chunk_chars", 280 if v["engine"] == "chatterbox" else 1000)
            chunks, cur = [], ""
            for snt in sents:
                if cur and len(cur) + 1 + len(snt) > limit:
                    chunks.append(cur)
                    cur = snt
                else:
                    cur = (cur + " " + snt).strip()
            if cur:
                chunks.append(cur)
            lines = [{"text": c, "pause": v.get("join_gap", 0.06)} for c in chunks]
        for ln in lines:
            text = spoken(ln["text"] if isinstance(ln, dict) else ln)
            gap = (ln.get("pause", 0.22) if isinstance(ln, dict) else 0.22)
            if v["engine"] == "kokoro":
                x = say_kokoro(text, v.get("voice", "am_michael"), v.get("speed", 1.15))
            else:
                x = say_chatterbox(text, v.get("exaggeration", 0.5), v.get("cfg", 0.5), ref)
            parts += [x, np.zeros(int(gap * 24000), dtype=np.float32)]
        y = loudnorm(np.concatenate(parts), 24000)
        wav = out / f"{v['name']}.wav"
        sf.write(wav, y, 24000)
        mp3 = out / f"{v['name']}.mp3"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-c:a", "libmp3lame", "-b:a", "128k", str(mp3)], check=True)
        secs = len(y) / 24000
        report.append({"name": v["name"], "seconds": round(secs, 1), "render_s": round(time.time() - t0, 1), **{k: v[k] for k in v if k != "name"}})
        print(f"  ✓ {v['name']}: {secs:.1f} s audio in {time.time() - t0:.0f} s", flush=True)
    (out / "lab-report.json").write_text(json.dumps(report, indent=1))


if __name__ == "__main__":
    sys.exit(main())
