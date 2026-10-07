"""
Reels Studio pipeline: brief.json -> upload-ready vertical video (HyperFrames render) + post kit.

Stages (each one is visible in renders/<id>/manifest.json):
  1. segments   template.segments(brief) -> spoken lines (+ silent holds) with ids
  2. voice      Kokoro TTS per line (Apache-2.0, local)  OR  your own recordings (vo/<id>.wav)
  3. layout     exact start/end per line -> composition duration
  4. words      word timings: proportional estimate, refined with whisper.cpp
                (`hyperframes transcribe`) for English
  5. audio      seeded royalty-free music (lib/synth.py) ducked under the voice + SFX
                on template events, two-pass loudnorm to -14 LUFS / -1.5 dBTP
  6. build      templates/_base + templates/<name> -> HyperFrames project (index.html)
  7. gates      hyperframes lint + hyperframes check (runtime, layout, contrast)
  8. render     hyperframes render (headless Chrome + FFmpeg)
  9. qa + kit   ffprobe/ebur128 checks, cover, contact sheet, SRT, post.md, manifest
"""
import difflib
import hashlib
import importlib.util
import json
import math
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from . import synth

ROOT = Path(__file__).resolve().parent.parent
TPL_DIR = ROOT / "templates"
BASE_DIR = TPL_DIR / "_base"
OUT_DIR = ROOT / "renders"  # NOT "out": dirs named out/build/dist are excluded from workspace snapshots
WORK_ROOT = Path(os.environ.get("REELS_WORK", "/var/tmp/reels"))  # outside the saved workspace
HF_CACHE = Path.home() / ".cache" / "hyperframes"
KOKORO_MODEL = HF_CACHE / "tts" / "models" / "kokoro-v1.0.onnx"
KOKORO_VOICES = HF_CACHE / "tts" / "voices" / "voices-v1.0.bin"
FPS = 30
MIX_SR = 48000
FONT_FILES = {
    "Anton": ("Anton.ttf", "400"),
    "Inter": ("Inter.ttf", "100 900"),
    "JetBrains Mono": ("JetBrainsMono.ttf", "100 800"),
    "Noto Nastaliq Urdu": ("NotoNastaliqUrdu.ttf", "400 700"),
}


# ------------------------------------------------------------------ utils
def hf_env():
    env = dict(os.environ)
    env.update(HYPERFRAMES_NO_TELEMETRY="1", DO_NOT_TRACK="1", CI="1", NO_COLOR="1")
    env.setdefault("HYPERFRAMES_EXTRACT_CACHE_DIR", "/var/tmp/hf/cache")
    env.setdefault("TMPDIR", "/var/tmp/hf/tmp")
    env["PATH"] = "/usr/local/bin:" + env.get("PATH", "")
    for k in ("HYPERFRAMES_EXTRACT_CACHE_DIR", "TMPDIR"):
        os.makedirs(env[k], exist_ok=True)
    return env


def run(cmd, cwd=None, timeout=3600, log=None, check=True):
    t0 = time.time()
    p = subprocess.run([str(c) for c in cmd], cwd=cwd, env=hf_env(), capture_output=True, text=True, timeout=timeout)
    out = (p.stdout or "") + (p.stderr or "")
    if log:
        with open(log, "a", encoding="utf-8") as f:
            f.write(f"\n$ {' '.join(map(str, cmd))}\n{out}\n[exit {p.returncode}, {time.time() - t0:.1f}s]\n")
    if check and p.returncode != 0:
        raise RuntimeError(f"{cmd[0]} {cmd[1] if len(cmd) > 1 else ''} failed (exit {p.returncode}):\n{out[-3000:]}")
    return p, out, time.time() - t0


def say(msg):
    print(f"[reels] {msg}", flush=True)


def load_template(name):
    d = TPL_DIR / name
    if not (d / "template.py").exists():
        raise SystemExit(f"unknown template '{name}' (have: {', '.join(list_templates())})")
    spec = importlib.util.spec_from_file_location(f"vvs_tpl_{name.replace('-', '_')}", d / "template.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.DIR = d
    return mod


def list_templates():
    return sorted(p.name for p in TPL_DIR.iterdir() if (p / "template.py").exists())


def norm_word(w):
    return re.sub(r"[^\w]", "", w.lower())


def spoken_clean(text):
    """Strip emoji / symbols TTS should not read."""
    text = re.sub(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F]", "", text)
    return re.sub(r"\s+", " ", text).strip()


# ------------------------------------------------------------------ voice
def trim_silence(x, sr, floor_db=40, pad_in=0.03, pad_out=0.06):
    hop = max(1, int(sr * 0.01))
    n = len(x) // hop
    if n < 3:
        return x
    rms = np.sqrt(np.mean(x[: n * hop].reshape(n, hop) ** 2, axis=1)) + 1e-9
    db = 20 * np.log10(rms)
    on = np.where(db > db.max() - floor_db)[0]
    if not len(on):
        return x
    a = max(0, on[0] * hop - int(pad_in * sr))
    b = min(len(x), (on[-1] + 1) * hop + int(pad_out * sr))
    return x[a:b]


_KOKORO = None


def release_tts():
    """Free the Kokoro/ONNX model (~500 MB) once the voice exists. On a 2 GB box, Chrome + FFmpeg need
    that RAM during the render; holding it made renders crawl at ~40 MB free."""
    global _KOKORO
    _KOKORO = None
    import ctypes
    import gc
    gc.collect()
    try:
        ctypes.CDLL("libc.so.6").malloc_trim(0)  # hand freed heap back to the OS (glibc)
    except (OSError, AttributeError):
        pass


class KokoroVoice:
    """One shared Kokoro model; any number of (voice, lang) speakers. lang 'ur' = espeak-ng Urdu phonemizer
    (experimental: Kokoro has no Urdu voice, but a Hindi voice + Urdu phonemes measured 87% whisper char-match)."""
    def __init__(self, voice, speed, lang):
        global _KOKORO
        if not KOKORO_MODEL.exists():
            say("downloading Kokoro model via `hyperframes tts` (first run)...")
            run(["hyperframes", "tts", "warm up", "-o", "/tmp/reels-warmup.wav"])
        if _KOKORO is None:
            from kokoro_onnx import Kokoro
            _KOKORO = Kokoro(str(KOKORO_MODEL), str(KOKORO_VOICES))
        self.k = _KOKORO
        self.voice, self.speed, self.lang = voice, speed, lang

    def __call__(self, text):
        samples, sr = self.k.create(text, voice=self.voice, speed=self.speed, lang=self.lang)
        return trim_silence(np.asarray(samples, dtype=np.float32), sr), sr


def load_recording(path):
    """Your own voice: any format ffmpeg reads -> 24 kHz mono float, trimmed."""
    tmp = Path("/tmp") / (path.stem + "-24k.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(path), "-ac", "1", "-ar", "24000", str(tmp)], check=True)
    x, sr = sf.read(tmp, dtype="float32")
    return trim_silence(x, sr), sr


# ------------------------------------------------------------------ words
def syllables(w):
    core = re.sub(r"[^\w]", "", w.lower())
    if not core:
        return 0.5
    if core.isdigit():
        return 1.4 * len(core)
    groups = re.findall(r"[aeiouy]+", core)
    return max(1, len(groups) - (1 if core.endswith("e") and len(groups) > 1 else 0))


def words_proportional(text, start, end):
    ws = text.split()
    if not ws:
        return []
    weights = [syllables(w) + 0.35 for w in ws]
    pauses = [0.45 if re.search(r"[.!?]$", w) else 0.25 if re.search(r"[,;:]$", w) else 0 for w in ws]
    total = sum(weights) + sum(pauses[:-1])
    unit = (end - start) / total if total else 0
    out, t = [], start
    for w, wt, pz in zip(ws, weights, pauses):
        e = t + wt * unit
        out.append([w, round(t, 3), round(e, 3)])
        t = e + pz * unit
    out[-1][2] = round(end, 3)
    return out


def speech_regions(x, sr, floor_db=32, min_gap=0.07):
    """Voiced regions of a TTS line (seconds, relative to the clip)."""
    hop = max(1, int(sr * 0.01))
    n = len(x) // hop
    if n < 2:
        return [(0.0, len(x) / sr)]
    rms = np.sqrt(np.mean(x[: n * hop].reshape(n, hop) ** 2, axis=1)) + 1e-9
    db = 20 * np.log10(rms)
    sp = db > db.max() - floor_db
    regs, i = [], 0
    while i < n:
        if sp[i]:
            j = i
            while j < n and sp[j]:
                j += 1
            if regs and (i - regs[-1][1]) * 0.01 < min_gap:
                regs[-1][1] = j
            else:
                regs.append([i, j])
            i = j
        else:
            i += 1
    return [(a * hop / sr, b * hop / sr) for a, b in regs] or [(0.0, len(x) / sr)]


def words_waveform(text, audio, sr, start):
    """Word timings anchored to the line's real pauses: punctuation boundaries snap to the
    largest silent gaps, words inside a phrase share the voiced span by syllable weight."""
    ws = text.split()
    if not ws:
        return []
    regs = speech_regions(audio, sr)
    v0, v1 = regs[0][0], regs[-1][1]
    phrases, cur = [], []
    for w in ws:
        cur.append(w)
        if re.search(r"[.!?,;:]$", w):
            phrases.append(cur)
            cur = []
    if cur:
        phrases.append(cur)
    gaps = [(regs[k][1], regs[k + 1][0]) for k in range(len(regs) - 1)]
    need = len(phrases) - 1
    if need > 0 and len(gaps) >= need:
        chosen = sorted(sorted(gaps, key=lambda g: g[1] - g[0], reverse=True)[:need])
        spans, a = [], v0
        for g in chosen:
            spans.append((a, g[0]))
            a = g[1]
        spans.append((a, v1))
    else:  # not enough audible pauses: one span, punctuation gets a small share
        return words_proportional(text, round(start + v0, 3), round(start + v1, 3))
    out = []
    for ph, (a, b) in zip(phrases, spans):
        wts = [syllables(w) + 0.35 for w in ph]
        unit = (b - a) / (sum(wts) or 1)
        t = a
        for w, wt in zip(ph, wts):
            out.append([w, round(start + t, 3), round(start + t + wt * unit, 3)])
            t += wt * unit
    return out


def whisper_intelligibility(vo_path, timing, order, log):
    """QA, not timing: does whisper.cpp hear the words the script intended? (catches TTS slips)"""
    _, _, secs = run(["hyperframes", "transcribe", vo_path.name, "--model", "small.en", "--no-runtime-install"],
                     cwd=vo_path.parent, log=log)
    tr = json.loads((vo_path.parent / "transcript.json").read_text())
    heard = [norm_word(w["text"]) for w in tr if w.get("text", "").strip()]
    script = [norm_word(w[0]) for sid in order if timing[sid].get("lang", "en").startswith("en") for w in timing[sid]["words"]]
    # character-level comparison: "whisper dot C P P" vs "whisper.cpp", "twelve" vs "12" etc. should not count as misses
    num = {"zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8",
           "nine": "9", "ten": "10", "eleven": "11", "twelve": "12", "dot": "", "kilometres": "kilometers", "neighbours": "neighbors"}
    a = "".join(num.get(w, w) for w in script)
    b = "".join(num.get(w, w) for w in heard)
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    matched = sum(bl.size for bl in sm.get_matching_blocks())
    wsm = difflib.SequenceMatcher(a=script, b=heard, autojunk=False)
    missed = [script[i] for tag, i1, i2, _, _ in wsm.get_opcodes() if tag in ("replace", "delete") for i in range(i1, i2)]
    return matched, len(a), missed[:12], secs


def refine_with_whisper(vo_path, timing, order, log):
    """Snap word times to whisper.cpp word timestamps (English only)."""
    _, _, secs = run(["hyperframes", "transcribe", vo_path.name, "--model", "small.en", "--no-runtime-install"],
                     cwd=vo_path.parent, log=log)
    tr_path = vo_path.parent / "transcript.json"
    tr = json.loads(tr_path.read_text())
    wwords = [(w["text"], float(w["start"]), float(w["end"])) for w in tr if w.get("text", "").strip()]
    matched = total = 0
    for sid in order:
        s = timing[sid]
        if not s["words"]:
            continue
        cand = [w for w in wwords if s["start"] - 0.2 <= (w[1] + w[2]) / 2 <= s["end"] + 0.2]
        a = [norm_word(w[0]) for w in s["words"]]
        b = [norm_word(w[0]) for w in cand]
        sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
        for blk in sm.get_matching_blocks():
            for k in range(blk.size):
                i, j = blk.a + k, blk.b + k
                st = min(max(cand[j][1], s["start"]), s["end"])
                en = min(max(cand[j][2], st + 0.05), s["end"])
                s["words"][i][1], s["words"][i][2] = round(st, 3), round(en, 3)
                matched += 1
        total += len(a)
        for i in range(1, len(s["words"])):  # keep monotonic
            if s["words"][i][1] < s["words"][i - 1][1]:
                s["words"][i][1] = s["words"][i - 1][2]
    return matched, total, secs


# ------------------------------------------------------------------ audio
def env_follow(x, sr, attack=0.015, release=0.30):
    a = math.exp(-1.0 / (attack * sr))
    r = math.exp(-1.0 / (release * sr))
    hop = 48
    y = np.abs(x[: len(x) // hop * hop]).reshape(-1, hop).max(axis=1)
    out = np.zeros_like(y)
    prev = 0.0
    aa, rr = a ** hop, r ** hop
    for i, v in enumerate(y):
        prev = aa * prev + (1 - aa) * v if v > prev else rr * prev + (1 - rr) * v
        out[i] = prev
    full = np.repeat(out, hop) if len(out) else np.zeros(0)
    if len(full) < len(x):  # pad the tail (< hop samples) with the last envelope value
        full = np.concatenate([full, np.full(len(x) - len(full), full[-1] if len(full) else 0.0)])
    return full[: len(x)]


def active_rms(x, sr):
    hop = int(sr * 0.02)
    n = len(x) // hop
    if n == 0:
        return 1e-4
    r = np.sqrt(np.mean(x[: n * hop].reshape(n, hop) ** 2, axis=1))
    thr = r.max() * 10 ** (-35 / 20)
    act = r[r > thr]
    return float(np.sqrt(np.mean(act ** 2))) if len(act) else 1e-4


def loudnorm(inp, out, I=-14.0, TP=-1.5, LRA=11.0):
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(inp), "-af",
                        f"loudnorm=I={I}:TP={TP}:LRA={LRA}:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    js = json.loads(p.stderr[p.stderr.rfind("{"): p.stderr.rfind("}") + 1])
    af = (f"loudnorm=I={I}:TP={TP}:LRA={LRA}:measured_I={js['input_i']}:measured_TP={js['input_tp']}"
          f":measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(inp), "-af", af, "-ar", str(MIX_SR), "-ac", "2",
                    "-c:a", "pcm_s16le", str(out)], check=True)
    return js


def measure(path):
    p = subprocess.run(["ffmpeg", "-nostats", "-hide_banner", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    tail = p.stderr[p.stderr.rfind("Summary:"):]
    i = re.search(r"I:\s+(-?[\d.]+) LUFS", tail)
    pk = re.search(r"Peak:\s+(-?[\d.]+) dBFS", tail)
    return (float(i.group(1)) if i else None), (float(pk.group(1)) if pk else None)


# ------------------------------------------------------------------ job
class Job:
    def __init__(self, brief_path, quality="draft", crf=None, check=True, render=True, keep_work=False):
        self.brief_path = Path(brief_path).resolve()
        self.brief = json.loads(self.brief_path.read_text(encoding="utf-8"))
        self.id = self.brief["id"]
        self.tpl = load_template(self.brief["template"])
        self.quality, self.crf, self.do_check, self.do_render, self.keep_work = quality, crf, check, render, keep_work
        self.work = WORK_ROOT / self.id
        self.proj = self.work / "project"
        self.out = OUT_DIR / self.id
        self.log = self.work / "build.log"
        self.manifest = {"id": self.id, "template": self.brief["template"], "brief": str(self.brief_path.relative_to(ROOT)) if ROOT in self.brief_path.parents else str(self.brief_path), "stages": {}}

    def stage(self, name, **info):
        self.manifest["stages"][name] = info
        say(f"{name}: " + ", ".join(f"{k}={v}" for k, v in info.items() if not isinstance(v, (list, dict))))

    # 1-3 -------------------------------------------------------------
    def voice_and_layout(self):
        b = self.brief
        segs = self.tpl.segments(b)
        lang = b.get("lang", "en-us")
        voice_cfg = b.get("voice", self.tpl.DEFAULTS.get("voice", "af_heart"))
        speed = float(b.get("speed", self.tpl.DEFAULTS.get("speed", 1.0)))
        t0 = time.time()
        clips = []
        if voice_cfg == "files":  # own-voice mode: brief_dir/vo/<segment-id>.(wav|mp3|m4a)
            vo_dir = self.brief_path.parent / b.get("vo_dir", "vo")
            for s in segs:
                if not s.get("text"):
                    clips.append((None, 24000))
                    continue
                f = next((vo_dir / f"{s['id']}{ext}" for ext in (".wav", ".mp3", ".m4a", ".ogg") if (vo_dir / f"{s['id']}{ext}").exists()), None)
                if not f:
                    raise SystemExit(f"own-voice mode: missing recording {vo_dir}/{s['id']}.wav")
                clips.append(load_recording(f))
            engine = "own recordings"
        else:
            speakers = {}
            for s in segs:
                key = (s.get("voice", voice_cfg), s.get("lang", lang), float(s.get("speed", speed)))
                if key not in speakers:
                    speakers[key] = KokoroVoice(key[0], key[2], key[1])  # (voice, speed, lang)
                clips.append(speakers[key](spoken_clean(s["text"])) if s.get("text") else (None, 24000))
            engine = " + ".join(f"kokoro {v} x{sp} ({l})" for v, l, sp in speakers)
        # layout
        lead, tail = b.get("lead_in", 0.25), b.get("tail", 0.6)
        t = lead
        timing, order = {}, []
        seg_audio = {}
        sr = 24000
        pieces = []
        for s, (audio, csr) in zip(segs, clips):
            t += s.get("pre", 0.0)
            if audio is None:
                dur = float(s.get("hold", 0.0))
            else:
                if csr != sr:
                    audio = resample_poly(audio, sr, csr).astype(np.float32)
                dur = len(audio) / sr
                pieces.append((t, audio))
                seg_audio[s["id"]] = audio
            timing[s["id"]] = {"start": round(t, 3), "end": round(t + dur, 3), "text": s.get("text", ""),
                               "caption": bool(s.get("caption", False)) and bool(s.get("text")), "words": [],
                               "lang": s.get("lang", lang)}
            order.append(s["id"])
            t += dur + s.get("post", 0.18)
        D = math.ceil((t + tail) * FPS) / FPS
        vo = np.zeros(int(round(D * sr)) + 1, dtype=np.float32)
        for at, a in pieces:
            i = int(round(at * sr))
            vo[i:i + len(a)] += a[: max(0, len(vo) - i)]
        self.work.mkdir(parents=True, exist_ok=True)
        self.vo_path = self.work / "vo.wav"
        sf.write(self.vo_path, vo, sr, subtype="PCM_16")
        for sid in order:
            s = timing[sid]
            if s["text"]:
                s["words"] = words_waveform(spoken_clean(s["text"]), seg_audio[sid], sr, s["start"])
        self.timing, self.order, self.D, self.vo = timing, order, D, vo
        self.stage("voice", engine=engine, lines=sum(1 for s in segs if s.get("text")), duration=f"{D:.2f}s", secs=round(time.time() - t0, 1))

    # 4 ---------------------------------------------------------------
    def word_timings(self):
        self.stage_note = "timings anchored to each line's waveform pauses"
        lang = self.brief.get("lang", "en-us")
        if not lang.startswith("en") or self.brief.get("whisper_qa", True) is False:
            self.stage("words", method="waveform-anchored", whisper_qa="skipped (non-English or disabled)")
            return
        try:
            m, n, missed, secs = whisper_intelligibility(self.vo_path, self.timing, self.order, self.log)
            self.stage("words", method="waveform-anchored", whisper_char_match=f"{100 * m / max(1, n):.1f}%",
                       word_diffs=" ".join(missed) or "-", secs=round(secs, 1))
        except Exception as e:
            self.stage("words", method="waveform-anchored", whisper_qa=f"unavailable: {str(e)[:120]}")

    # 5 ---------------------------------------------------------------
    def audio(self):
        b = self.brief
        seed = int(b.get("seed", int(hashlib.md5(self.id.encode()).hexdigest()[:8], 16) % 100000))  # stable per video id
        self.seed = seed
        events = self.tpl.events(b, self.timing, self.D) if hasattr(self.tpl, "events") else {}
        self.events = events
        mcfg = dict(self.tpl.music(b, self.timing, self.D, events))
        mcfg.update(b.get("music", {}))
        mcfg.setdefault("seed", seed)
        if "key" not in mcfg:
            mcfg["key"] = int(np.random.default_rng(seed).integers(-3, 4))
        n = int(round(self.D * MIX_SR))
        vo = resample_poly(self.vo, 2, 1).astype(np.float64)[:n]
        vo = np.pad(vo, (0, max(0, n - len(vo))))
        vo *= 10 ** (-20 / 20) / active_rms(vo, MIX_SR)  # voice ~ -20 dBFS RMS before mastering
        music = synth.music(self.D + 0.05, **mcfg)[:n]
        music *= 10 ** (-27 / 20) / max(1e-6, float(np.sqrt(np.mean(music ** 2))))
        env = env_follow(vo, MIX_SR)
        env = np.clip(env / (np.percentile(env[env > 1e-4], 90) if np.any(env > 1e-4) else 1), 0, 1)
        duck = 10 ** ((-9.0 * env) / 20)  # music dips ~9 dB under speech, comes back in pauses
        mix = music * duck[:, None] + vo[:, None]
        kit = synth.sfx_kit(seed)
        sfx_list = self.tpl.sfx(b, self.timing, self.D, events)
        for name, at, gain in sfx_list:
            if name in kit and 0 <= at < self.D:
                synth.place(mix, kit[name], at, gain * 0.32)
        self.proj.mkdir(parents=True, exist_ok=True)
        (self.proj / "assets").mkdir(exist_ok=True)
        raw = self.work / "mix-raw.wav"
        sf.write(raw, np.clip(mix, -1, 1).astype(np.float32), MIX_SR, subtype="FLOAT")
        ln = loudnorm(raw, self.proj / "assets" / "mix.wav")
        I, pk = measure(self.proj / "assets" / "mix.wav")
        self.stage("audio", music=f"{mcfg.get('style')}/{mcfg.get('progression')} {mcfg.get('bpm')}bpm key{mcfg['key']:+d} seed{seed}",
                   sfx=len(sfx_list), loudness=f"{I} LUFS", peak=f"{pk} dBFS")
        self.music_cfg = mcfg

    # 6 ---------------------------------------------------------------
    def build(self):
        b = self.brief
        urdu = bool(b.get("urdu")) or self.tpl.DEFAULTS.get("urdu", False)
        fonts_dir = self.proj / "assets" / "fonts"
        fonts_dir.mkdir(parents=True, exist_ok=True)
        css = []
        emoji = Path("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf")  # flags / emoji (apt fonts-noto-color-emoji)
        if emoji.exists():
            shutil.copy2(emoji, fonts_dir / emoji.name)
            css.append('@font-face { font-family: "Noto Color Emoji"; src: url("assets/fonts/NotoColorEmoji.ttf") format("truetype"); }')
        else:
            css.append('@font-face { font-family: "Noto Color Emoji"; src: local("Noto Color Emoji"), local("Apple Color Emoji"), local("Segoe UI Emoji"); }')
        for fam, (fn, wght) in FONT_FILES.items():  # every family named in CSS gets an explicit @font-face (lint rule)
            src = BASE_DIR / "fonts" / fn
            if src.exists():
                shutil.copy2(src, fonts_dir / fn)
                css.append(f'@font-face {{ font-family: "{fam}"; src: url("assets/fonts/{fn}") format("truetype"); font-weight: {wght}; font-style: normal; }}')
        brand = {"handle": "@yourhandle", "name": "Your Channel", "tagline": "", **b.get("brand", {})}
        data = {
            "id": self.id, "duration": self.D, "fps": FPS, "seed": self.seed, "lang": b.get("lang", "en-us"), "urdu": urdu,
            "brand": brand, "segs": self.timing, "order": self.order, "events": self.events,
            "captions": {**self.tpl.DEFAULTS.get("captions", {}), **b.get("captions", {})},
            "content": b.get("content", {}),
        }
        if hasattr(self.tpl, "data"):
            data["extra"] = self.tpl.data(b, self.timing, self.D, self.events)
        rep = {
            "{{LANG}}": b.get("lang", "en")[:2], "{{TITLE}}": re.sub(r"[<>&\"]", "", b.get("title", self.id)),
            "{{PRESET}}": b.get("style", self.tpl.DEFAULTS.get("style", "neon")), "{{D}}": f"{self.D:g}",
            "{{FONTS_CSS}}": "\n".join(css),
            "{{BASE_CSS}}": (BASE_DIR / "base.css").read_text(), "{{SCENE_CSS}}": (self.tpl.DIR / "scene.css").read_text(),
            "{{SCENE_HTML}}": (self.tpl.DIR / "scene.html").read_text(),
            "{{BASE_JS}}": (BASE_DIR / "base.js").read_text(), "{{SCENE_JS}}": (self.tpl.DIR / "scene.js").read_text(),
            "{{DATA_JSON}}": json.dumps(data, ensure_ascii=False).replace("</", "<\\/"),
        }
        html = (BASE_DIR / "base.html").read_text()
        for k in ["{{FONTS_CSS}}", "{{BASE_CSS}}", "{{SCENE_CSS}}", "{{SCENE_HTML}}", "{{BASE_JS}}", "{{SCENE_JS}}", "{{DATA_JSON}}", "{{LANG}}", "{{TITLE}}", "{{PRESET}}", "{{D}}"]:
            html = html.replace(k, rep[k])
        (self.proj / "index.html").write_text(html, encoding="utf-8")
        (self.proj / "hyperframes.json").write_text(json.dumps({
            "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
            "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"},
            "media": {"autoProxy": True}}, indent=2))
        (self.proj / "meta.json").write_text(json.dumps({"id": self.id, "name": b.get("title", self.id)}, indent=2))
        self.stage("build", project=str(self.proj), html_kb=round(len(html.encode()) / 1024, 1))

    # 7-8 -------------------------------------------------------------
    def gates_and_render(self):
        _, out, secs = run(["hyperframes", "lint", "."], cwd=self.proj, log=self.log, check=False)
        m = re.search(r"(\d+)\s+error\(s\),\s+(\d+)\s+warning\(s\)", out)
        errs, warns = (int(m.group(1)), int(m.group(2))) if m else (None, None)
        self.stage("lint", errors=errs, warnings=warns)
        if errs:
            raise SystemExit(f"lint errors - see {self.log}")
        if self.do_check:
            p, out, secs = run(["hyperframes", "check", "."], cwd=self.proj, log=self.log, check=False)
            self.stage("check", ok=p.returncode == 0, secs=round(secs, 1), summary=out.strip().splitlines()[-1][:160] if out.strip() else "")
            if p.returncode != 0:
                raise SystemExit(f"hyperframes check failed - see {self.log}")
        if not self.do_render:
            return None
        mp4 = self.work / "video.mp4"
        cmd = ["hyperframes", "render", ".", "--output", str(mp4), "--fps", str(FPS), "--quality", self.quality]
        if self.crf:
            cmd += ["--crf", str(self.crf)]
        _, out, secs = run(cmd, cwd=self.proj, log=self.log)
        self.stage("render", secs=round(secs, 1), mb=round(mp4.stat().st_size / 1e6, 2), quality=self.quality, crf=self.crf)
        return mp4

    # 9 ---------------------------------------------------------------
    def qa_and_kit(self, mp4):
        self.out.mkdir(parents=True, exist_ok=True)
        final = self.out / f"{self.id}.mp4"
        shutil.copy2(mp4, final)
        pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(final)],
                                       capture_output=True, text=True).stdout)
        v = next(s for s in pr["streams"] if s["codec_type"] == "video")
        a = next((s for s in pr["streams"] if s["codec_type"] == "audio"), None)
        I, pk = measure(final)
        D = float(pr["format"]["duration"])
        checks = {
            "1080x1920": (v["width"], v["height"]) == (1080, 1920),
            "30fps": v.get("r_frame_rate") == "30/1",
            "h264+aac": v["codec_name"] == "h264" and a is not None and a["codec_name"] == "aac",
            "duration_matches": abs(D - self.D) < 0.1,
            "loudness_-14±1": I is not None and abs(I + 14) <= 1.0,
            "peak<=-1dBFS": pk is not None and pk <= -1.0,
        }
        cover_t = self.events.get("cover", 1.0)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{cover_t:.2f}", "-i", str(final), "-frames:v", "1", "-q:v", "3", str(self.out / "cover.jpg")], check=True)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(final), "-vf", f"fps=12/{D:.3f},scale=270:-2,tile=6x2:margin=6:padding=6:color=0x111111",
                        "-frames:v", "1", "-q:v", "4", str(self.out / "contact.jpg")], check=True)
        self.write_srt()
        self.write_post(D)
        shutil.copy2(self.proj / "index.html", self.out / "composition.html")
        self.manifest["qa"] = {"duration": round(D, 3), "frames": int(v.get("nb_frames", 0) or 0), "video": f"{v['codec_name']} {v['width']}x{v['height']} {v.get('r_frame_rate')}",
                               "audio": f"{a['codec_name']} {a.get('sample_rate')}Hz {a.get('channels')}ch" if a else None,
                               "loudness_lufs": I, "peak_dbfs": pk, "size_mb": round(final.stat().st_size / 1e6, 2), "checks": checks}
        self.manifest["timing"] = {sid: {k: self.timing[sid][k] for k in ("start", "end", "text")} for sid in self.order}
        self.manifest["music"] = self.music_cfg
        self.manifest["sources"] = self.brief.get("sources", [])
        (self.out / "manifest.json").write_text(json.dumps(self.manifest, indent=2, ensure_ascii=False))
        bad = [k for k, ok in checks.items() if not ok]
        self.stage("qa", passed=f"{len(checks) - len(bad)}/{len(checks)}", failed=",".join(bad) or "-", out=str(self.out.relative_to(ROOT.parent)))

    def write_srt(self):
        def ts(t):
            ms = int(round(t * 1000))
            return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
        cues, n = [], 0
        for sid in self.order:
            ws = self.timing[sid]["words"]
            for i in range(0, len(ws), 7):
                chunk = ws[i:i + 7]
                n += 1
                cues.append(f"{n}\n{ts(chunk[0][1])} --> {ts(chunk[-1][2] + 0.15)}\n{' '.join(w[0] for w in chunk)}\n")
        (self.out / "captions.srt").write_text("\n".join(cues), encoding="utf-8")

    def write_post(self, D):
        b, p = self.brief, self.brief.get("post", {})
        lines = [f"# Post kit: {b.get('title', self.id)}", "",
                 f"**Video:** `{self.id}.mp4` ({D:.1f} s, 1080x1920, H.264/AAC, -14 LUFS). **Cover frame:** `cover.jpg`. **Subtitles:** `captions.srt`.", ""]
        if p.get("titles"):
            lines += ["## Title / hook options (test one per platform, never re-upload the same file twice on one channel)"] + [f"- {t}" for t in p["titles"]] + [""]
        if p.get("caption"):
            lines += ["## Caption", "", p["caption"], ""]
        if p.get("hashtags"):
            lines += ["## Hashtags (3-5 max; topical beats generic)", "", " ".join(p["hashtags"]), ""]
        if p.get("pinned_comment"):
            lines += ["## Pinned comment", "", p["pinned_comment"], ""]
        voice = b.get("voice", self.tpl.DEFAULTS.get("voice"))
        lines += ["## Disclosure & credits", "",
                  ("- Voice: your own recording." if voice == "files" else
                   f"- Voice: synthetic narration (Kokoro TTS `{voice}`). Generic TTS narration of animated graphics is not a 'realistic' depiction, so YouTube/TikTok AI labels are not mandatory; adding \"AI voice\" to the description is a cheap trust win."),
                  "- Music & SFX: generated by this pipeline (no third-party rights, no Content ID risk)."]
        for s in b.get("sources", []):
            lines.append(f"- Source: {s}")
        lines += ["", "## Before you post (human checklist)", "",
                  "- [ ] Facts double-checked against the listed sources (you are the editor, not the template).",
                  "- [ ] Hook works with sound OFF (first frame text) and sound ON (first spoken words).",
                  "- [ ] This video adds something a viewer can't get from the last 5 uploads (new data, new angle, new joke).",
                  "- [ ] Posted natively per platform (no TikTok watermark on Reels/Shorts)."]
        (self.out / "post.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ---------------------------------------------------------------
    def run_all(self):
        t0 = time.time()
        if self.work.exists():
            shutil.rmtree(self.work)
        self.work.mkdir(parents=True)
        self.voice_and_layout()
        release_tts()
        self.word_timings()
        self.audio()
        self.build()
        mp4 = self.gates_and_render()
        if mp4:
            self.qa_and_kit(mp4)
        self.manifest["total_secs"] = round(time.time() - t0, 1)
        if mp4:
            (self.out / "manifest.json").write_text(json.dumps(self.manifest, indent=2, ensure_ascii=False))
        say(f"done in {time.time() - t0:.0f}s -> {self.out if mp4 else self.proj}")
        if mp4 and not self.keep_work:
            shutil.rmtree(self.work, ignore_errors=True)
        return self.manifest
