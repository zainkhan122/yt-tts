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
    env.update(HYPERFRAMES_NO_TELEMETRY="1", HYPERFRAMES_NO_UPDATE_CHECK="1", DO_NOT_TRACK="1", CI="1", NO_COLOR="1")  # no silent self-upgrade (it once jumped 0.8.137 -> 0.8.140)
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


# ---- display vs spoken text: "{GTA V|GTA Five}" is SHOWN as "GTA V" (captions/SRT) but SPOKEN as "GTA Five" ----
MARKUP = re.compile(r"\{([^{}|]+)\|([^{}]+)\}")


def _glue_markup(text):
    """Punctuation touching a markup group belongs to both halves: '{GTA V|GTA Five},' -> '{GTA V,|GTA Five,}'."""
    text = re.sub(r"\{([^{}|]+)\|([^{}]+)\}([^\s{}]+)", lambda m: "{" + m[1] + m[3] + "|" + m[2] + m[3] + "}", text)
    return re.sub(r"([^\s{}]+)\{([^{}|]+)\|([^{}]+)\}", lambda m: "{" + m[1] + m[2] + "|" + m[1] + m[3] + "}", text)


def apply_lexicon(text, lex):
    """Channel lexicon (display word -> pronunciation) becomes markup, whole words only, never inside existing markup."""
    lex = {k: v for k, v in (lex or {}).items() if k and v and k != v and not k.startswith("_")}
    if not lex:
        return text
    pat = re.compile(r"(?<![\w])(" + "|".join(re.escape(k) for k in sorted(lex, key=len, reverse=True)) + r")(?![\w])")
    return "".join(part if part.startswith("{") else pat.sub(lambda m: "{" + m[1] + "|" + lex[m[1]] + "}", part)
                   for part in re.split(r"(\{[^{}]*\})", text))


def parse_markup(text):
    """-> (display_text, spoken_text, groups) ; groups = [(display_words, n_spoken_words)] in reading order."""
    text = _glue_markup(text)
    groups, disp, spk, pos = [], [], [], 0
    for m in MARKUP.finditer(text):
        pre = text[pos:m.start()]
        groups += [([w], len(spoken_clean(w).split())) for w in pre.split()]
        d, s = m[1].strip(), m[2].strip()
        groups.append((d.split(), len(spoken_clean(s).split())))
        disp.append(pre + d)
        spk.append(pre + s)
        pos = m.end()
    tail = text[pos:]
    groups += [([w], len(spoken_clean(w).split())) for w in tail.split()]
    disp.append(tail)
    spk.append(tail)
    return re.sub(r"\s+", " ", "".join(disp)).strip(), re.sub(r"\s+", " ", "".join(spk)).strip(), groups


def map_display_words(groups, spoken_words):
    """Spread spoken-word timings onto display words ('five thousand' -> '5,000' spans both)."""
    out, i = [], 0
    for disp, n in groups:
        if n == 0:  # emoji-only token: not spoken, not captioned
            continue
        span = spoken_words[i:i + n]
        i += n
        if not span:
            break
        if len(disp) == len(span):
            out += [[d, w[1], w[2]] for d, w in zip(disp, span)]
        else:
            t0, t1 = span[0][1], span[-1][2]
            step = (t1 - t0) / max(1, len(disp))
            out += [[d, round(t0 + k * step, 3), round(t0 + (k + 1) * step, 3)] for k, d in enumerate(disp)]
    return out


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


def _trim_memory():
    """Return freed heap pages (Kokoro/onnxruntime arenas) to the OS so the renderer's Chrome gets the RAM."""
    import gc
    gc.collect()
    try:
        import ctypes
        ctypes.CDLL("libc.so.6").malloc_trim(0)
    except Exception:
        pass


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


# "Creator mic" presets: +0.4 semitone lift (duration kept via atempo), de-mud, presence + air, punchy compression
VOICE_FX = {
    # "maxhype" = most enthusiastic: +1.1 st lift, max presence/air, 4.5:1 punch (+ stronger per-line accents)
    "maxhype": ("asetrate={sr}*1.0656,aresample={sr},atempo=0.93844,equalizer=f=180:t=q:w=1:g=-2,"
                "equalizer=f=3200:t=q:w=1.0:g=4.5,highshelf=f=9000:g=3.5,acompressor=threshold=0.07:ratio=4.5:attack=3:release=60:makeup=2.2"),
    # "hype" = more enthusiastic: +0.8 st lift, stronger presence/air, harder compression (+ per-line accents below)
    "hype": ("asetrate={sr}*1.0473,aresample={sr},atempo=0.95484,equalizer=f=180:t=q:w=1:g=-2,"
             "equalizer=f=3200:t=q:w=1.0:g=4,highshelf=f=9000:g=3,acompressor=threshold=0.08:ratio=4:attack=3:release=70:makeup=2"),
    "energetic": ("asetrate={sr}*1.0234,aresample={sr},atempo=0.97714,equalizer=f=180:t=q:w=1:g=-1.5,"
                  "equalizer=f=3200:t=q:w=1.0:g=3,highshelf=f=9000:g=2.5,acompressor=threshold=0.1:ratio=3:attack=4:release=80:makeup=1.6"),
}


def pitch_accent(a, sr, semitones):
    """Duration-preserving pitch lift for ONE spoken line (enthusiasm = wider melody across lines)."""
    if not semitones or a is None:
        return a
    k = 2 ** (semitones / 12)
    tin, tout = Path("/tmp/acc-in.wav"), Path("/tmp/acc-out.wav")
    sf.write(tin, a, sr, subtype="FLOAT")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(tin), "-af", f"asetrate={sr}*{k:.5f},aresample={sr},atempo={1 / k:.5f}",
                    "-ar", str(sr), "-ac", "1", str(tout)], check=True)
    out, _ = sf.read(tout, dtype="float32")
    return out[:len(a)] if len(out) >= len(a) else np.pad(out, (0, len(a) - len(out)))


MELODY = {"maxhype": 1.45}  # intonation expansion per preset (1.0 = natural). Channel config may override via "melody".


def expand_melody(a, sr, factor):
    """Widen the pitch contour of ONE line around its median (Praat PSOLA, duration-preserving).
    Excited presenters swing pitch more inside each sentence; factor 1.45 = 45% wider swings in semitone space."""
    if a is None or not factor or abs(factor - 1.0) < 0.01:
        return a
    try:
        import parselmouth
        from parselmouth.praat import call
    except ImportError:
        print("[reels] praat-parselmouth missing: melody expansion skipped (pip install praat-parselmouth)")
        return a
    snd = parselmouth.Sound(np.asarray(a, dtype=np.float64), sampling_frequency=sr)
    try:
        pitch = snd.to_pitch(0.01, 75, 600)
        med = call(pitch, "Get quantile", 0, 0, 0.5, "Hertz")
        if not med or med != med:  # unvoiced line
            return a
        manip = call(snd, "To Manipulation", 0.01, 75, 600)
        tier = call(manip, "Extract pitch tier")
        call(tier, "Formula", f"{med:.3f} * (self / {med:.3f}) ^ {factor}")
        call([tier, manip], "Replace pitch tier")
        out = call(manip, "Get resynthesis (overlap-add)").values[0].astype(np.float32)
    except Exception as e:  # never fail a render over styling
        print(f"[reels] melody expansion skipped: {e}")
        return a
    return out[:len(a)] if len(out) >= len(a) else np.pad(out, (0, len(a) - len(out)))


def hype_accents(texts, scale=1.0):
    """Semitone lift per spoken line: hook highest, '!' lines lifted, '?' lines rise a little, others alternate.
    scale 1.0 = 'hype', 1.7 = 'maxhype' (wider melody = more enthusiasm)."""
    out, n = [], 0
    for t in texts:
        if not t:
            out.append(0.0)
            continue
        s = t.strip()
        out.append(round(scale * (0.6 if n == 0 else 0.4 if s.endswith("!") else 0.26 if s.endswith("?") else (0.22 if n % 2 else 0.0)), 2))
        n += 1
    return out


def apply_voice_fx(vo, sr, preset):
    if not preset or preset not in VOICE_FX:
        return vo
    tin, tout = Path("/tmp/vofx-in.wav"), Path("/tmp/vofx-out.wav")
    sf.write(tin, vo, sr, subtype="FLOAT")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(tin), "-af", VOICE_FX[preset].format(sr=sr), "-ar", str(sr), "-ac", "1", str(tout)], check=True)
    out, _ = sf.read(tout, dtype="float32")
    out = out[:len(vo)] if len(out) >= len(vo) else np.pad(out, (0, len(vo) - len(out)))  # exact same length = same timing
    peak = float(np.max(np.abs(out))) or 1.0
    return out / peak * 0.99 if peak > 0.99 else out


class KokoroVoice:
    """One shared Kokoro model; any number of (voice, lang) speakers. lang 'ur' = espeak-ng Urdu phonemizer
    (experimental: Kokoro has no Urdu voice, but a Hindi voice + Urdu phonemes measured 87% whisper char-match)."""
    def __init__(self, voice, speed, lang, blend=None):
        global _KOKORO
        if not KOKORO_MODEL.exists():
            say("downloading Kokoro model via `hyperframes tts` (first run)...")
            run(["hyperframes", "tts", "warm up", "-o", "/tmp/reels-warmup.wav"])
        if _KOKORO is None:
            from kokoro_onnx import Kokoro
            _KOKORO = Kokoro(str(KOKORO_MODEL), str(KOKORO_VOICES))
        self.k = _KOKORO
        self.voice, self.speed, self.lang = voice, speed, lang
        if blend:  # e.g. {"af_bella": 0.25} -> 75% voice + 25% af_bella style vector (brighter, same identity)
            style = (1 - sum(blend.values())) * self.k.get_voice_style(voice)
            for name, w in blend.items():
                style = style + w * self.k.get_voice_style(name)
            self.voice = style.astype(np.float32)

    def __call__(self, text):
        samples, sr = self.k.create(text, voice=self.voice, speed=self.speed, lang=self.lang)
        return trim_silence(np.asarray(samples, dtype=np.float32), sr), sr


_CHATTERBOX = None


class ChatterboxVoice:
    """APPROVED CHANNEL VOICE (owner, 2026-10-09: voice-lab option 3 = sample 8-chatterbox-michael-flow).
    Resemble AI Chatterbox (MIT) cloning our Kokoro am_michael reference clip (brand/voice/michael-ref.wav) with
    exaggeration 0.7 / cfg 0.4, read in long chunks (flow). CPU torch; installed by cloud/setup-render.sh.
    Seeded per chunk, so the same brief renders the same take."""
    def __init__(self, cfg):
        global _CHATTERBOX
        import torch
        from chatterbox.tts import ChatterboxTTS
        if _CHATTERBOX is None:
            _CHATTERBOX = ChatterboxTTS.from_pretrained(device="cpu")
        self.m, self.torch, self.cfg = _CHATTERBOX, torch, cfg
        ref = ROOT / cfg["ref_wav"]
        if not ref.exists():  # rebuild it exactly like the approved voice-lab take (Kokoro 0.6.1, same text, same trim)
            ref.parent.mkdir(parents=True, exist_ok=True)
            rk = cfg.get("ref_kokoro", {"voice": "am_michael", "speed": 1.0, "lang": "en-us"})
            kv = KokoroVoice(rk["voice"], rk["speed"], rk["lang"])
            x, sr = kv.k.create(cfg["ref_text"], voice=rk["voice"], speed=rk["speed"], lang=rk["lang"])
            x = np.asarray(x, dtype=np.float32)
            idx = np.where(np.abs(x) > 0.01)[0]
            if len(idx):
                x = x[max(0, idx[0] - int(0.02 * sr)): min(len(x), idx[-1] + int(0.06 * sr))]
            sf.write(ref, x, sr, subtype="PCM_16")
            say(f"approved voice reference was missing: rebuilt {ref.name} from Kokoro ({len(x) / sr:.1f}s)")
        self.exag, self.cfgw = float(cfg.get("exaggeration", 0.7)), float(cfg.get("cfg", 0.4))
        self.m.prepare_conditionals(str(ref), exaggeration=self.exag)
        self.name = f"chatterbox exag{self.exag} cfg{self.cfgw} ref {Path(cfg['ref_wav']).name}"

    def __call__(self, text, seed=0):
        self.torch.manual_seed(int(seed))
        wav = self.m.generate(text, exaggeration=self.exag, cfg_weight=self.cfgw)
        x = wav.squeeze().detach().cpu().numpy().astype(np.float32)
        sr = int(getattr(self.m, "sr", 24000))
        if sr != 24000:
            x = resample_poly(x, 24000, sr).astype(np.float32)
        return trim_silence(x, 24000), 24000


class PreviewVoice:
    """LOCAL LAYOUT PREVIEW ONLY (REELS_VOICE_PREVIEW=kokoro): Kokoro reads the same flow chunks so timing/lint can be
    checked in a small sandbox. Never publishable: the approved-voice QA gate fails on it."""
    def __init__(self, voice, speed, lang):
        self.k = KokoroVoice(voice, speed, lang)
        self.name = f"PREVIEW kokoro {voice} x{speed}"

    def __call__(self, text, seed=0):
        return self.k(text)


def split_sentences(text, limit):
    sents = re.split(r"(?<=[.!?])\s+", text.strip())
    out, cur = [], ""
    for snt in sents:
        if cur and len(cur) + 1 + len(snt) > limit:
            out.append(cur)
            cur = snt
        else:
            cur = (cur + " " + snt).strip()
    if cur:
        out.append(cur)
    return out


def _rms_frames(x, sr, hop=0.01):
    h = max(1, int(sr * hop))
    n = len(x) // h
    return np.sqrt(np.mean(x[: n * h].reshape(n, h) ** 2, axis=1) + 1e-12) if n else np.zeros(1), h


def quietest_cut(x, sr, a, b):
    """Sample index of the quietest 10 ms frame between times a and b (a scene boundary inside a flow chunk)."""
    rms, h = _rms_frames(x, sr)
    i0, i1 = max(0, int(a * sr) // h), min(len(rms) - 1, int(b * sr) // h)
    if i1 <= i0:
        return int(round(b * sr))
    k = i0 + int(np.argmin(rms[i0:i1 + 1]))
    return k * h + h // 2


def transcribe_words(wav_path, log):
    """[(norm_word, start, end)] via hyperframes transcribe (whisper.cpp small.en, word timestamps)."""
    run(["hyperframes", "transcribe", wav_path.name, "--model", os.environ.get("REELS_WHISPER_MODEL", "small.en"), "--no-runtime-install"], cwd=wav_path.parent, log=log)
    tr = json.loads((wav_path.parent / "transcript.json").read_text())
    return [(norm_word(w["text"]), float(w.get("start", 0)), float(w.get("end", w.get("start", 0)))) for w in tr
            if w.get("text", "").strip() and norm_word(w["text"])]


NUMWORDS = {"zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8",
            "nine": "9", "ten": "10", "point": "", "dot": ""}


def melody_st(x, sr, words=None):
    """Pitch range (semitones, p10-p90 of voiced frames, speaker-adaptive bounds): the 'liveliness' of a take.
    Approved option-3 sample measured 14.4 st; flat Kokoro 7.6-9.6 (research/voice/voice-study.md)."""
    try:
        import parselmouth
        from parselmouth.praat import call
        snd = parselmouth.Sound(x.astype(np.float64), sampling_frequency=sr)
        f = snd.to_pitch_ac(time_step=0.01, pitch_floor=60, pitch_ceiling=500).selected_array["frequency"]
        v = f[f > 0]
        if len(v) < 30:
            return 0.0
        lo, hi = max(50.0, 0.75 * np.percentile(v, 25)), min(600.0, 1.5 * np.percentile(v, 75))
        pt = call(snd.to_pitch_ac(time_step=0.01, pitch_floor=lo, pitch_ceiling=hi), "Kill octave jumps")
        f, ft = pt.selected_array["frequency"], pt.xs()
        ok = (f >= lo * 0.9) & (f <= hi * 1.1)
        if words:  # only inside spoken words (breaths/creaks between words inflate the range)
            inw = np.zeros_like(ok)
            for _, a, b in words:
                inw |= (ft >= a) & (ft <= b)
            if (ok & inw).sum() >= 30:
                ok &= inw
        v = f[ok]
        if len(v) < 30:
            return 0.0
        st = 12 * np.log2(v / np.median(v))
        return float(np.percentile(st, 90) - np.percentile(st, 10))
    except Exception:
        return 99.0  # no Praat: never block on it


def align_chunk(x, sr, seg_texts, work, log, display_texts=None):
    """Where does each scene line start inside one flow chunk? Returns (cut sample indices between lines, char match 0-1).
    whisper word timestamps + difflib alignment to the known script; cuts land on the quietest frame between the
    previous line's last word and the next line's first word. Falls back to proportional cuts if whisper fails."""
    total = len(x) / sr
    ref, owner = [], []
    for k, t in enumerate(seg_texts):
        for w in t.split():
            if norm_word(w):
                ref.append(norm_word(w))
                owner.append(k)
    try:
        wav = work / "flow-chunk.wav"
        sf.write(wav, x, sr, subtype="PCM_16")
        hyp = transcribe_words(wav, log)
    except Exception:
        hyp = []
    hb = "".join(NUMWORDS.get(w[0], w[0]) for w in hyp)

    def cmatch(words):  # character match; whisper writes numbers/brands as DISPLAYED ("435 MB"), so try both forms
        ra = "".join(NUMWORDS.get(w, w) for w in words)
        return sum(bl.size for bl in difflib.SequenceMatcher(a=ra, b=hb, autojunk=False).get_matching_blocks()) / max(1, len(ra))
    match = cmatch(ref)
    if display_texts:
        match = max(match, cmatch([norm_word(w) for t in display_texts for w in t.split() if norm_word(w)]))
    sm = difflib.SequenceMatcher(a=ref, b=[w[0] for w in hyp], autojunk=False)
    m = {}
    for bl in sm.get_matching_blocks():
        for i in range(bl.size):
            m[bl.a + i] = bl.b + i
    cuts = []
    chars = [len(t) for t in seg_texts]
    for k in range(1, len(seg_texts)):
        first = owner.index(k)
        prev_last = first - 1
        nxt = next((i for i in range(first, len(ref)) if i in m), None)
        prv = next((i for i in range(prev_last, -1, -1) if i in m), None)
        prop = sum(chars[:k]) / max(1, sum(chars)) * total
        if nxt is not None and prv is not None and hyp:
            a, b = hyp[m[prv]][2], hyp[m[nxt]][1]
            if nxt != first:  # first word of the line not heard: back off proportionally
                b = max(a, b - 0.25 * (nxt - first))
            if b - a < 0.02:
                a, b = max(0.0, b - 0.12), b + 0.05
        else:
            a, b = max(0.0, prop - 0.3), min(total, prop + 0.3)
        cuts.append(quietest_cut(x, sr, a, b))
    cuts = sorted(max(1, min(len(x) - 1, c)) for c in cuts)
    return cuts, match, hyp


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
        # each punctuation boundary takes the pause nearest to where the syllable count says it should fall
        # (longer pauses preferred); picking the globally largest gaps can starve a phrase (seen with am_michael)
        wts = [sum(syllables(w) + 0.35 for w in ph) for ph in phrases]
        total, acc, chosen, after = sum(wts) or 1.0, 0.0, [], v0
        longest = max(g[1] - g[0] for g in gaps) or 1e-3
        for k in range(need):
            acc += wts[k]
            expect = v0 + (v1 - v0) * acc / total
            cands = [g for g in gaps if g[0] > after + 0.05 and g not in chosen]
            if len(cands) < need - k:
                chosen = None
                break
            g = min(cands[:len(cands) - (need - k - 1)],
                    key=lambda g: abs((g[0] + g[1]) / 2 - expect) - 0.35 * (v1 - v0) / len(phrases) * (g[1] - g[0]) / longest)
            chosen.append(g)
            after = g[1]
        if chosen:
            spans, a = [], v0
            for g in chosen:
                spans.append((a, g[0]))
                a = g[1]
            spans.append((a, v1))
            # sanity: a phrase squeezed below 30% of its syllable share means the pauses lied -> proportional timing
            if any((b_ - a_) < 0.3 * (v1 - v0) * w / total for (a_, b_), w in zip(spans, wts)):
                chosen = None
        if not chosen:
            return words_proportional(text, round(start + v0, 3), round(start + v1, 3))
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
    _, _, secs = run(["hyperframes", "transcribe", vo_path.name, "--model", os.environ.get("REELS_WHISPER_MODEL", "small.en"), "--no-runtime-install"],
                     cwd=vo_path.parent, log=log)
    tr = json.loads((vo_path.parent / "transcript.json").read_text())
    heard = [norm_word(w["text"]) for w in tr if w.get("text", "").strip()]
    # character-level comparison: "whisper dot C P P" vs "whisper.cpp", "twelve" vs "12" etc. should not count as misses.
    # Compare against BOTH the spoken form ("thirty-seven hundred", "git hub") and the display form ("3,700", "GitHub")
    # and keep the better score: whisper writes numbers and brand names the way they are displayed.
    num = {"zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8",
           "nine": "9", "ten": "10", "eleven": "11", "twelve": "12", "dot": "", "kilometres": "kilometers", "neighbours": "neighbors"}
    b = "".join(num.get(w, w) for w in heard)
    best = None
    for key in ("spoken_words", "words"):
        script = [norm_word(w[0]) for sid in order if timing[sid].get("lang", "en").startswith("en")
                  for w in (timing[sid].get(key) or timing[sid]["words"])]
        a = "".join(num.get(w, w) for w in script)
        sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
        matched = sum(bl.size for bl in sm.get_matching_blocks())
        if best is None or matched / max(1, len(a)) > best[0] / max(1, best[1]):
            wsm = difflib.SequenceMatcher(a=script, b=heard, autojunk=False)
            missed = [script[i] for tag, i1, i2, _, _ in wsm.get_opcodes() if tag in ("replace", "delete") for i in range(i1, i2)]
            best = (matched, len(a), missed[:12])
    return best[0], best[1], best[2], secs


def refine_with_whisper(vo_path, timing, order, log):
    """Snap word times to whisper.cpp word timestamps (English only)."""
    _, _, secs = run(["hyperframes", "transcribe", vo_path.name, "--model", os.environ.get("REELS_WHISPER_MODEL", "small.en"), "--no-runtime-install"],
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


def normalize_mp4_audio(mp4, I=-14.0, TP=-1.5, tol=0.5):
    """Final loudness guard: if the rendered MP4 is off target, limit + two-pass linear loudnorm the AUDIO only
    (video stream copied, no re-render). Returns (before, after) integrated LUFS."""
    before, pk = measure(mp4)
    if before is not None and abs(before - I) <= tol and (pk is None or pk <= TP + 0.4):
        return before, before
    lim = "alimiter=limit=0.79:attack=4:release=60:level=disabled"  # ~-2 dBFS ceiling makes room for linear gain
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(mp4), "-af",
                        f"{lim},loudnorm=I={I}:TP={TP}:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True)
    js = json.loads(p.stderr[p.stderr.rfind("{"): p.stderr.rfind("}") + 1])
    af = (f"{lim},loudnorm=I={I}:TP={TP}:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}"
          f":measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    vdur = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=duration", "-of", "csv=p=0",
                           str(mp4)], capture_output=True, text=True).stdout.strip()
    tmp = Path(mp4).with_name(Path(mp4).stem + ".norm.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(mp4), "-map", "0:v:0", "-map", "0:a:0", "-c:v", "copy", "-af", af,
                    "-ar", "48000", "-ac", "2", "-c:a", "aac", "-b:a", "192k"] + (["-t", vdur] if vdur else []) +
                   ["-movflags", "+faststart", str(tmp)], check=True)  # -t: AAC padding must not lengthen the file
    tmp.replace(mp4)
    after, _ = measure(mp4)
    return before, after


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
        # channel defaults (config/channel.json): brand, voice, speed, lang, style. The brief wins on any key it sets
        chan_path = ROOT / "config" / "channel.json"
        if chan_path.exists():
            chan = json.loads(chan_path.read_text(encoding="utf-8"))
            for k in ("voice", "speed", "lang", "style", "voice_fx", "voice_blend", "tts"):
                if k in chan and k not in self.brief:
                    self.brief[k] = chan[k]
            if "brand" in chan:
                self.brief["brand"] = {**chan["brand"], **self.brief.get("brand", {})}
            if "lexicon" in chan:
                self.brief["lexicon"] = {**chan["lexicon"], **self.brief.get("lexicon", {})}
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
        lex = b.get("lexicon", {})
        for s in segs:  # display vs spoken (markup + channel lexicon); TTS only ever sees the spoken form
            if s.get("text"):
                s["display"], s["spoken"], s["_groups"] = parse_markup(apply_lexicon(s["text"], lex if s.get("lang", b.get("lang", "en-us")).startswith("en") else {}))
        lang = b.get("lang", "en-us")
        voice_cfg = b.get("voice", self.tpl.DEFAULTS.get("voice", "af_heart"))
        speed = float(b.get("speed", self.tpl.DEFAULTS.get("speed", 1.0)))
        t0 = time.time()
        clips = []
        post_override = {}
        tts = b.get("tts") or {}
        self.voice_engine = "kokoro"
        if voice_cfg != "files" and tts.get("engine") == "chatterbox":
            clips, post_override, engine = self.flow_voice(segs, tts, lang, voice_cfg, speed)
        elif voice_cfg == "files":  # own-voice mode: brief_dir/vo/<segment-id>.(wav|mp3|m4a)
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
            self.voice_engine = "own recordings"
        else:
            speakers = {}
            for s in segs:
                key = (s.get("voice", voice_cfg), s.get("lang", lang), float(s.get("speed", speed)))
                if key not in speakers:
                    speakers[key] = KokoroVoice(key[0], key[2], key[1], blend=b.get("voice_blend") if key[0] == voice_cfg else None)  # (voice, speed, lang)
                clips.append(speakers[key](spoken_clean(s["spoken"])) if s.get("text") else (None, 24000))
            engine = " + ".join(f"kokoro {v} x{sp} ({l})" for v, l, sp in speakers)
            if b.get("voice_fx") in ("hype", "maxhype"):  # enthusiasm: per-line melody accents (duration-preserving, timing unchanged)
                acc = hype_accents([s.get("display") for s in segs], 1.7 if b.get("voice_fx") == "maxhype" else 1.0)
                mel = b.get("melody", MELODY.get(b.get("voice_fx"), 1.0))
                clips = [((pitch_accent(expand_melody(a, rate, mel), rate, acc[i]) if a is not None else a), rate) for i, (a, rate) in enumerate(clips)]
                engine += " + hype accents" + (f" + melody x{mel}" if mel != 1.0 else "")
        # layout
        lead, tail = b.get("lead_in", 0.25), b.get("tail", 0.6)
        t = lead
        timing, order = {}, []
        seg_audio = {}
        sr = 24000
        pieces = []
        for s, (audio, csr) in zip(segs, clips):
            t += post_override.get("pre:" + s["id"], s.get("pre", 0.0))
            if audio is None:
                dur = float(s.get("hold", 0.0))
            else:
                if csr != sr:
                    audio = resample_poly(audio, sr, csr).astype(np.float32)
                dur = len(audio) / sr
                pieces.append((t, audio))
                seg_audio[s["id"]] = audio
            timing[s["id"]] = {"start": round(t, 3), "end": round(t + dur, 3), "text": s.get("display", s.get("text", "")),
                               "spoken": s.get("spoken", ""), "_groups": s.get("_groups", []),
                               "caption": bool(s.get("caption", False)) and bool(s.get("text")), "words": [],
                               "lang": s.get("lang", lang)}
            order.append(s["id"])
            t += dur + post_override.get(s["id"], s.get("post", 0.18))
        D = math.ceil((t + tail) * FPS) / FPS
        vo = np.zeros(int(round(D * sr)) + 1, dtype=np.float32)
        for at, a in pieces:
            i = int(round(at * sr))
            vo[i:i + len(a)] += a[: max(0, len(vo) - i)]
        self.work.mkdir(parents=True, exist_ok=True)
        if voice_cfg != "files":
            vo = apply_voice_fx(vo, sr, b.get("voice_fx"))  # e.g. "energetic" (channel default); own recordings stay untouched
        self.vo_path = self.work / "vo.wav"
        sf.write(self.vo_path, vo, sr, subtype="PCM_16")
        for sid in order:
            s = timing[sid]
            groups = s.pop("_groups", [])
            if s["text"] and sid in seg_audio:
                s["spoken_words"] = words_waveform(spoken_clean(s["spoken"] or s["text"]), seg_audio[sid], sr, s["start"])
                s["words"] = map_display_words(groups, s["spoken_words"]) if groups else s["spoken_words"]
        self.timing, self.order, self.D, self.vo = timing, order, D, vo
        self.stage("voice", engine=engine, lines=sum(1 for s in segs if s.get("text")), duration=f"{D:.2f}s", secs=round(time.time() - t0, 1))

    def flow_voice(self, segs, tts, lang, voice_cfg, speed):
        """Approved voice, read in FLOW: consecutive scene lines are spoken in one chunk (<= chunk_chars), then cut back into
        scenes at the quietest point between lines, so every scene still has its own audio + word timings.
        Measured 2026-10-09: creators ~1.5 pauses/min vs 19-23 for line-by-line synthesis."""
        try:
            voice = ChatterboxVoice(tts)
            self.voice_engine = "chatterbox"
        except ImportError:
            if os.environ.get("REELS_VOICE_PREVIEW") != "kokoro":
                raise SystemExit("The approved channel voice is Chatterbox (voice-lab option 3) but chatterbox-tts is not installed. "
                                 "Cloud renders install it (cloud/setup-render.sh). Local layout check only: REELS_VOICE_PREVIEW=kokoro")
            voice = PreviewVoice(voice_cfg, speed, lang)
            self.voice_engine = "kokoro-preview"
        limit, gap = int(tts.get("chunk_chars", 280)), float(tts.get("join_gap", 0.06))
        base_seed = int(tts.get("seed", 7)) + int(hashlib.md5(self.id.encode()).hexdigest()[:6], 16) % 10000 \
            + 10007 * int(self.brief.get("voice_seed", 0))  # brief "voice_seed": N picks a different (still seeded) take
        tries, min_match = 1 + int(tts.get("max_retries", 2)), float(tts.get("min_match", 0.92))
        min_mel, mels = float(tts.get("min_melody_st", 10.0)), []
        texts = [spoken_clean(s["spoken"]) if s.get("text") else None for s in segs]
        chunks, cur = [], []
        for i, s in enumerate(segs):
            if texts[i] is None:
                if cur:
                    chunks.append(cur)
                    cur = []
                continue
            prev = segs[cur[-1]] if cur else None
            joined = " ".join(texts[j] for j in cur + [i])
            if cur and (len(joined) > limit or s.get("pre", 0.0) > 0.15 or (prev is not None and prev.get("post", 0.18) >= 0.5)):
                chunks.append(cur)
                cur = []
            cur.append(i)
        if cur:
            chunks.append(cur)
        clips = [(None, 24000)] * len(segs)
        posts, worst, retried = {}, 1.0, 0
        cdir = self.work / "flow"
        cdir.mkdir(parents=True, exist_ok=True)
        for ci, idx in enumerate(chunks):
            seg_texts = [texts[i] for i in idx]
            best = None
            for attempt in range(tries):
                seed = base_seed + 1000 * ci + 97 * attempt
                if len(idx) == 1 and len(seg_texts[0]) > limit:  # one long line: sentence sub-chunks, tiny joins
                    parts = []
                    for sub in split_sentences(seg_texts[0], limit):
                        a, _ = voice(sub, seed)
                        parts += [a, np.zeros(int(gap * 24000), np.float32)]
                    x = np.concatenate(parts[:-1])
                else:
                    x, _ = voice(" ".join(seg_texts), seed)
                cuts, match, heard = align_chunk(x, 24000, seg_texts, cdir, self.log, [segs[i].get("display") or texts[i] for i in idx])
                mel = melody_st(x, 24000, heard)
                score = (match >= min_match, mel if match >= min_match else match)
                if best is None or score > best[3]:
                    best = (x, cuts, match, score, mel)
                if self.voice_engine == "kokoro-preview" or (match >= min_match and mel >= min_mel):
                    break
                retried += 1
            x, cuts, match, _, mel = best
            worst = min(worst, match)
            mels.append(round(mel, 1))
            bounds = [0] + cuts + [len(x)]
            for j, i in enumerate(idx):
                piece = x[bounds[j]:bounds[j + 1]]
                clips[i] = (piece if len(piece) else np.zeros(240, np.float32), 24000)
                posts[segs[i]["id"]] = 0.0
            last = segs[idx[-1]]
            posts[last["id"]] = last.get("post", 0.18) if last.get("post", 0.18) >= 0.5 else gap
        for s in segs:  # template default gaps (0.06-0.08 s before each line) would re-insert silence at every cut
            if s.get("text") and s.get("pre", 0.0) <= 0.1:
                posts["pre:" + s["id"]] = 0.0
        self.flow_stats = {"chunks": len(chunks), "worst_chunk_match": round(worst, 3), "retries": retried, "melody_st": mels}
        return clips, posts, f"{voice.name}, flow ({len(chunks)} chunks, worst match {worst:.0%}, melody {mels} st, retries {retried})"

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
            try:  # whole-voiceover delivery reading (same method as tools/voice_study.py): approved sample = 13.6 st
                tr = json.loads((self.vo_path.parent / "transcript.json").read_text())
                ws = [(w.get("text", ""), float(w["start"]), float(w.get("end", w["start"]))) for w in tr if w.get("text", "").strip()]
                if ws:
                    mel = melody_st(self.vo.astype(np.float32), 24000, ws)
                    wpm = round(len(ws) / max(1e-3, ws[-1][2] - ws[0][1]) * 60)
                    self.manifest["voice_quality"] = {"melody_st": round(mel, 1), "wpm": wpm, "approved_sample_melody_st": 13.6}
                    self.stage("voice_quality", melody_st=round(mel, 1), wpm=wpm, note="flat take? set brief voice_seed" if mel < 12 else "ok")
            except Exception as e:
                self.stage("voice_quality", error=str(e)[:80])
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
            "{{MEDIA_HTML}}": "",
            "{{LANG}}": b.get("lang", "en")[:2], "{{TITLE}}": re.sub(r"[<>&\"]", "", b.get("title", self.id)),
            "{{PRESET}}": b.get("style", self.tpl.DEFAULTS.get("style", "neon")), "{{D}}": f"{self.D:g}",
            "{{FONTS_CSS}}": "\n".join(css),
            "{{BASE_CSS}}": (BASE_DIR / "base.css").read_text(), "{{SCENE_CSS}}": self._scene_part("scene.css"),
            "{{SCENE_HTML}}": self._scene_part("scene.html"),
            "{{BASE_JS}}": (BASE_DIR / "base.js").read_text(), "{{SCENE_JS}}": self._scene_part("scene.js"),
            "{{DATA_JSON}}": json.dumps(data, ensure_ascii=False).replace("</", "<\\/"),
        }
        if hasattr(self.tpl, "assets"):  # captures / official media the template needs, copied into the project
            n_assets = 0
            for src, name in self.tpl.assets(b):
                dst = self.proj / "assets" / name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                n_assets += 1
            self.manifest["assets"] = n_assets
        # timed media (<video> clips): static DOM, direct children of #root (never nested in a timed element)
        rep["{{MEDIA_HTML}}"] = self.tpl.html(b, self.timing, self.D, self.events) if hasattr(self.tpl, "html") else ""
        rep["{{SCENE_HTML}}"] = self._scene_part("scene.html")
        rep["{{SCENE_CSS}}"] = self._scene_part("scene.css")
        rep["{{SCENE_JS}}"] = self._scene_part("scene.js")
        html = (BASE_DIR / "base.html").read_text()
        for k in ["{{FONTS_CSS}}", "{{BASE_CSS}}", "{{SCENE_CSS}}", "{{MEDIA_HTML}}", "{{SCENE_HTML}}", "{{BASE_JS}}", "{{SCENE_JS}}", "{{DATA_JSON}}", "{{LANG}}", "{{TITLE}}", "{{PRESET}}", "{{D}}"]:
            html = html.replace(k, rep[k])
        (self.proj / "index.html").write_text(html, encoding="utf-8")
        (self.proj / "hyperframes.json").write_text(json.dumps({
            "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
            "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"},
            "media": {"autoProxy": True}}, indent=2))
        (self.proj / "meta.json").write_text(json.dumps({"id": self.id, "name": b.get("title", self.id)}, indent=2))
        self.stage("build", project=str(self.proj), html_kb=round(len(html.encode()) / 1024, 1))

    def _scene_part(self, name):
        """Template file, prefixed by its shared engine (template.SHARED = '_spotlight' -> templates/_spotlight/<name>)."""
        parts = []
        shared = getattr(self.tpl, "SHARED", None)
        for d in ([TPL_DIR / shared] if shared else []) + [self.tpl.DIR]:
            if (d / name).exists():
                parts.append((d / name).read_text())
        return "\n".join(parts)

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
        lb, la = normalize_mp4_audio(final)  # renderer can shift loudness (seen: -14.3 mix -> -15.3 in MP4 with am_michael)
        if lb != la:
            self.stage("loudness_fix", before=f"{lb} LUFS", after=f"{la} LUFS")
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
        need = (self.brief.get("tts") or {}).get("engine")
        if need and self.brief.get("voice") != "files":  # owner rule 2026-10-09: every published video uses the approved voice
            checks["approved_voice"] = getattr(self, "voice_engine", None) == need
        cover_t = self.events.get("cover", 1.0)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{cover_t:.2f}", "-i", str(final), "-frames:v", "1", "-q:v", "3", str(self.out / "cover.jpg")], check=True)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(final), "-vf", f"fps=12/{D:.3f},scale=270:-2,tile=6x2:margin=6:padding=6:color=0x111111",
                        "-frames:v", "1", "-q:v", "4", str(self.out / "contact.jpg")], check=True)
        self.write_srt()
        self.write_post(D)
        if getattr(self, "vo_path", None) and Path(self.vo_path).exists():  # clean voice track (QA, remixes, voice studies)
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(self.vo_path), "-c:a", "libmp3lame", "-b:a", "96k",
                            str(self.out / "voiceover.mp3")], check=False)
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
        if "approved_voice" in bad:
            raise SystemExit(f"QA: not the approved channel voice (got {getattr(self, 'voice_engine', None)}, need {need}): refusing to ship")

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
        if b.get("credits_on_screen"):  # name kept for old briefs; shown ONLY in text, never on screen
            lines.append(f"- Media credit (put in the description): {b['credits_on_screen']}")
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
        _trim_memory()
        self.word_timings()
        self.audio()
        self.build()
        _trim_memory()
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
