#!/usr/bin/env python3
"""Voice audition across FREE TTS engines (runs on GitHub Actions: 4 vCPU / 16 GB, free for public repos).

  python tts_audition.py run <engine> --out DIR     # engine: chatterbox | turbo | qwen3 | orpheus | edge
  python tts_audition.py score --in DIR --out DIR   # UTMOS naturalness (1-5) + whisper clarity + MP3s + results.md
  python tts_audition.py inputs                     # (sandbox) Kokoro reference clip + current-voice baselines

Every engine reads the SAME script so the comparison is fair. Licenses (commercial use OK unless noted):
chatterbox/turbo/nano = MIT (Resemble AI, outputs carry an inaudible PerTh watermark), qwen3 = Apache-2.0,
orpheus = Apache-2.0 weights (Llama-3.2 base), kokoro = Apache-2.0, edge = Microsoft online voices: free but
unofficial endpoint (not a licensed API; can break or be blocked).
"""
import argparse
import gc
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
INPUTS = HERE / "inputs"
LINES = ["Okay, this is wild!",
         "Someone just put Minecraft inside GTA Five, and an AI agent built the whole thing.",
         "The best part?",
         "It's completely free, and it hit almost five thousand GitHub stars in one week!"]
SCRIPT = " ".join(LINES)
REF_TEXT = ("Hey friends, welcome back! Today I have three free AI tools that honestly blew my mind, "
            "and the last one is my absolute favorite.")
QWEN_DESIGN = ("Female voice, mid-twenties, bright, warm and friendly American accent. An enthusiastic tech YouTuber "
               "revealing exciting AI news: energetic, upbeat and fast-paced, smiling while she talks, with lively "
               "intonation and crisp, clear articulation.")
QWEN_RYAN = "Speak with genuine excitement and enthusiasm, upbeat and energetic, like a tech YouTuber revealing something amazing."
LICENSE = {"chatterbox": "MIT", "turbo": "MIT", "nano": "MIT", "qwen3": "Apache-2.0", "orpheus": "Apache-2.0 (Llama-3.2 base)",
           "edge": "free, unofficial Microsoft endpoint", "kokoro": "Apache-2.0"}


def _save(out, name, wav, sr, secs, engine, params):
    import soundfile as sf
    wav = np.asarray(wav, dtype=np.float32).squeeze()
    sf.write(out / f"{name}.wav", wav, sr)
    meta = {"name": name, "engine": engine, "license": LICENSE.get(engine, "?"), "params": params,
            "gen_seconds": round(secs, 1), "audio_seconds": round(len(wav) / sr, 2), "sr": sr}
    (out / f"{name}.json").write_text(json.dumps(meta, indent=1))
    print(f"[ok] {name}: {meta['audio_seconds']}s audio in {meta['gen_seconds']}s", flush=True)


def _ref_wav(tmp):
    """Chatterbox wants a WAV reference; the repo stores FLAC (smaller)."""
    import soundfile as sf
    a, sr = sf.read(INPUTS / "af_heart_ref.flac", dtype="float32")
    p = Path("/tmp") / "af_heart_ref.wav"
    sf.write(p, a, sr)
    return str(p)


def _threads():
    import torch
    torch.set_num_threads(os.cpu_count() or 4)
    try:  # Chatterbox embeds an inaudible PerTh watermark; keep it, but never let a broken import kill the run
        import perth
        if perth.PerthImplicitWatermarker is None:
            print("[warn] PerTh watermarker unavailable (pkg_resources missing?) -> DummyWatermarker", flush=True)
            perth.PerthImplicitWatermarker = perth.DummyWatermarker
    except ImportError:
        pass
    return torch


def run_chatterbox(out):
    torch = _threads()
    from chatterbox.tts import ChatterboxTTS
    m = ChatterboxTTS.from_pretrained(device="cpu")
    ref = _ref_wav(out)
    for name, kw in [("chatterbox-natural", dict(exaggeration=0.5, cfg_weight=0.5)),
                     ("chatterbox-energetic", dict(exaggeration=0.8, cfg_weight=0.3)),
                     ("chatterbox-afheart-energetic", dict(audio_prompt_path=ref, exaggeration=0.75, cfg_weight=0.35))]:
        t = time.time()
        torch.manual_seed(7)
        wav = m.generate(SCRIPT, **kw)
        _save(out, name, wav.cpu().numpy(), m.sr, time.time() - t, "chatterbox",
              {k: (v if k != "audio_prompt_path" else "af_heart_ref") for k, v in kw.items()})
    os.remove(ref)


def run_chatterbox_sweep(out):
    """af_heart timbre with stronger Chatterbox emotion (exaggeration) to add energy WITHOUT DSP artifacts."""
    torch = _threads()
    from chatterbox.tts import ChatterboxTTS
    m = ChatterboxTTS.from_pretrained(device="cpu")
    ref = _ref_wav(out)
    for name, kw in [("chatterbox-afheart-exag1.0", dict(exaggeration=1.0, cfg_weight=0.3)),
                     ("chatterbox-afheart-exag1.3", dict(exaggeration=1.3, cfg_weight=0.25))]:
        t = time.time()
        torch.manual_seed(7)
        wav = m.generate(SCRIPT, audio_prompt_path=ref, **kw)
        _save(out, name, wav.cpu().numpy(), m.sr, time.time() - t, "chatterbox", {**kw, "voice": "af_heart_ref"})
    os.remove(ref)


def run_turbo(out):
    torch = _threads()
    from chatterbox.tts_turbo import ChatterboxTurboTTS
    ref = _ref_wav(out)
    for nano in (False, True):
        try:
            m = ChatterboxTurboTTS.from_pretrained(device="cpu", nano=nano) if nano else ChatterboxTurboTTS.from_pretrained(device="cpu")
        except TypeError:
            print("[skip] this chatterbox build has no Nano model", flush=True)
            continue
        tag = "nano" if nano else "turbo"
        jobs = [(f"{tag}-default", {})] + ([] if nano else [(f"{tag}-afheart", {"audio_prompt_path": ref})])
        for name, kw in jobs:
            t = time.time()
            torch.manual_seed(7)
            wav = m.generate(SCRIPT, **kw)
            _save(out, name, wav.cpu().numpy(), m.sr, time.time() - t, tag,
                  {"voice": "af_heart_ref" if kw else "built-in default"})
        del m
        gc.collect()
    os.remove(ref)


def run_qwen3(out):
    torch = _threads()
    from qwen_tts import Qwen3TTSModel
    from huggingface_hub import constants
    for repo, name, call in [
        ("Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign", "qwen3-designed-female",
         lambda m: m.generate_voice_design(text=SCRIPT, language="English", instruct=QWEN_DESIGN)),
        ("Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice", "qwen3-ryan-excited",
         lambda m: m.generate_custom_voice(text=SCRIPT, language="English", speaker="Ryan", instruct=QWEN_RYAN)),
    ]:
        m = Qwen3TTSModel.from_pretrained(repo, device_map="cpu", dtype=torch.float32)
        t = time.time()
        torch.manual_seed(7)
        wavs, sr = call(m)
        _save(out, name, wavs[0], sr, time.time() - t, "qwen3",
              {"model": repo.split("/")[1], "instruct": QWEN_DESIGN if "Design" in repo else QWEN_RYAN})
        del m
        gc.collect()
        # free disk between the two 4.5 GB checkpoints
        shutil.rmtree(Path(constants.HF_HUB_CACHE) / ("models--" + repo.replace("/", "--")), ignore_errors=True)


def run_orpheus(out):
    from orpheus_cpp import OrpheusCpp
    o = OrpheusCpp(verbose=False, lang="en", n_threads=os.cpu_count() or 4)
    for name, voice in [("orpheus-tara", "tara"), ("orpheus-leo", "leo")]:
        t = time.time()
        sr, s = o.tts(SCRIPT, options={"voice_id": voice})
        s = np.asarray(s).squeeze()
        _save(out, name, s.astype(np.float32) / (32768.0 if s.dtype == np.int16 else 1.0), sr, time.time() - t,
              "orpheus", {"voice": voice, "quant": "Q4_K_M gguf (llama.cpp)"})


def run_edge(out):
    import asyncio
    import edge_tts
    for name, voice in [("edge-ava", "en-US-AvaMultilingualNeural"), ("edge-emma", "en-US-EmmaMultilingualNeural"),
                        ("edge-andrew", "en-US-AndrewMultilingualNeural")]:
        t = time.time()
        asyncio.run(edge_tts.Communicate(SCRIPT, voice, rate="+8%").save(str(out / f"{name}.mp3")))
        meta = {"name": name, "engine": "edge", "license": LICENSE["edge"], "params": {"voice": voice, "rate": "+8%"},
                "gen_seconds": round(time.time() - t, 1)}
        (out / f"{name}.json").write_text(json.dumps(meta, indent=1))
        print(f"[ok] {name}", flush=True)


# ---------------------------------------------------------------- scoring

def _ffmpeg():
    exe = shutil.which("ffmpeg")
    if not exe:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
    return exe


def _decode16k(p):
    raw = subprocess.run([_ffmpeg(), "-v", "error", "-i", str(p), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def _norm_words(s):
    import re
    s = s.lower().replace("gta 5", "gta five").replace("5,000", "five thousand").replace("5000", "five thousand")
    s = s.replace("it's", "it is").replace("mod pack", "modpack")
    return re.sub(r"[^a-z ]", " ", s).split()


def score(indir, out):
    import torch
    import jiwer
    from faster_whisper import WhisperModel
    indir, out = Path(indir), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    files = sorted([p for p in indir.rglob("*") if p.suffix in (".wav", ".mp3", ".flac")])
    files += sorted(INPUTS.glob("kokoro-*.flac"))
    utmos = torch.hub.load("tarepan/SpeechMOS:v1.2.0", "utmos22_strong", trust_repo=True)
    asr = WhisperModel("small.en", device="cpu", compute_type="int8")
    ref = " ".join(_norm_words(SCRIPT))
    rows = []
    for p in files:
        name = p.stem
        meta = {}
        for cand in (p.with_suffix(".json"), INPUTS / f"{name}.json"):
            if cand.exists():
                meta = json.loads(cand.read_text())
        w = _decode16k(p)
        with torch.no_grad():
            mos = float(utmos(torch.from_numpy(w).unsqueeze(0), 16000).item())
        segs, _ = asr.transcribe(w, language="en", beam_size=1)
        heard = " ".join(s.text.strip() for s in segs)
        wer = jiwer.wer(ref, " ".join(_norm_words(heard)))
        dur = len(w) / 16000
        subprocess.run([_ffmpeg(), "-y", "-v", "error", "-i", str(p), "-af", "loudnorm=I=-15:TP=-1.5", "-ac", "1",
                        "-ar", "24000", "-b:a", "96k", str(out / f"{name}.mp3")], check=True)
        rows.append({"name": name, "engine": meta.get("engine", "kokoro" if name.startswith("kokoro") else "?"),
                     "license": meta.get("license", LICENSE.get("kokoro") if name.startswith("kokoro") else "?"),
                     "utmos": round(mos, 2), "wer_pct": round(100 * wer, 1), "seconds": round(dur, 1),
                     "wpm": round(len(SCRIPT.split()) / dur * 60), "gen_seconds": meta.get("gen_seconds"),
                     "params": meta.get("params", {}), "heard": heard})
        print(f"{name:32s} UTMOS {mos:4.2f}  WER {100 * wer:5.1f}%  {dur:4.1f}s", flush=True)
    rows.sort(key=lambda r: -r["utmos"])
    (out / "results.json").write_text(json.dumps(rows, indent=1))
    md = ["# Voice audition results", "", f"Script: \"{SCRIPT}\"", "",
          "UTMOS = predicted human naturalness rating (1-5; real human speech typically 4.0-4.5). WER = words whisper got wrong.", "",
          "| # | sample | engine | UTMOS | WER | sec | wpm | gen time (4 vCPU) | license |", "|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        md.append(f"| {i} | {r['name']} | {r['engine']} | {r['utmos']} | {r['wer_pct']}% | {r['seconds']} | {r['wpm']} | "
                  f"{r['gen_seconds'] if r['gen_seconds'] is not None else '-'} s | {r['license']} |")
    (out / "results.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


# ---------------------------------------------------------------- sandbox inputs (Kokoro)

def make_inputs():
    import soundfile as sf
    sys.path.insert(0, str(HERE.parent))
    from lib import pipeline
    INPUTS.mkdir(exist_ok=True)
    spk = pipeline.KokoroVoice("af_heart", 1.0, "en-us")
    a, sr = spk(REF_TEXT)
    sf.write(INPUTS / "af_heart_ref.flac", np.asarray(a, dtype=np.float32), sr)
    (INPUTS / "af_heart_ref.txt").write_text(REF_TEXT + "\n")
    # baselines: raw Kokoro (no processing) and the current channel default (maxhype chain), same script as the cloud
    for name, speed, fx in [("kokoro-raw", 1.1, None), ("kokoro-maxhype", 1.33, "maxhype")]:
        spk = pipeline.KokoroVoice("af_heart", speed, "en-us")
        acc = pipeline.hype_accents(LINES, 1.7) if fx else [0] * len(LINES)
        chunks = []
        for line, semis in zip(LINES, acc):
            a, sr = spk(line)
            a = np.asarray(a, dtype=np.float32)
            if fx:
                a = pipeline.pitch_accent(pipeline.expand_melody(a, sr, pipeline.MELODY.get(fx, 1.0)), sr, semis)
            chunks += [a, np.zeros(int(0.12 * sr), dtype=np.float32)]
        vo = np.concatenate(chunks)
        if fx:
            vo = pipeline.apply_voice_fx(vo, sr, fx)
        sf.write(INPUTS / f"{name}.flac", vo, sr)
        (INPUTS / f"{name}.json").write_text(json.dumps({"name": name, "engine": "kokoro", "license": LICENSE["kokoro"],
                                                          "params": {"voice": "af_heart", "speed": speed, "fx": fx or "none"},
                                                          "gen_seconds": None}, indent=1))
        print(f"[ok] {name}: {len(vo) / sr:.1f}s")
    pipeline.release_tts()


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("engine", choices=["chatterbox", "chatterbox_sweep", "turbo", "qwen3", "orpheus", "edge"])
    r.add_argument("--out", default="out")
    s = sub.add_parser("score")
    s.add_argument("--in", dest="indir", default="samples")
    s.add_argument("--out", default="results")
    sub.add_parser("inputs")
    a = ap.parse_args()
    if a.cmd == "run":
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        globals()[f"run_{a.engine}"](out)
        if not any(out.glob("*.wav")) and not any(out.glob("*.mp3")):
            raise SystemExit("no audio produced")
    elif a.cmd == "score":
        score(a.indir, a.out)
    else:
        make_inputs()


if __name__ == "__main__":
    main()
