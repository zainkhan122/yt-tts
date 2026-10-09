#!/usr/bin/env python3
"""
Voice study: HOW the reference creators say their scripts (delivery), not just what they say.

The agent cannot hear, so it "listens" by measurement:
  1. audio only (yt-dlp; YouTube via the tv_embedded client), 16 kHz mono
  2. word-level transcript with timings (whisper.cpp, -ml 1 -sow)
  3. prosody per word (Praat via parselmouth): pitch peak in semitones vs the speaker's median, loudness peak in dB
  4. delivery metrics: pitch range + movement, loudness range, speed + speed variation between phrases, pauses,
     stressed words (pitch AND/OR loudness jump vs the neighbouring words), phrase endings (rise / fall)
  5. script-for-the-ear metrics: words per sentence, questions, "you", numbers, contractions

  python3 tools/voice_study.py --account https://www.tiktok.com/@dr_cintas --top 2 --latest 12
  python3 tools/voice_study.py --url https://www.youtube.com/shorts/abc --url https://www.tiktok.com/@u/video/1
  python3 tools/voice_study.py --file /var/tmp/final/tool-muse-01.mp4 --label "ours: tool-muse-01"
  python3 tools/voice_study.py --report            # rebuild research/voice/voice-study.md from all saved results

Public repo policy (same as social_scan): audio is deleted after analysis; full word timings stay in
research/voice/raw/ (git-ignored); git gets metrics, the stressed-word list and a <=20-word excerpt.
"""
import argparse
import datetime as dt
import json
import re
import statistics as stats
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
import social_scan as ss  # noqa: E402  (WHISPER, MODELS, TMP, list_account)

OUT = ROOT / "research/voice"
RAW = OUT / "raw"
TMP = Path("/var/tmp/voice-study")
FUNC = set("""a an the and or but so to of in on at for with from by is are was were be been it its it's this that these those
i you your we our they their he she his her them me my as if then than just not no do does did can could will would
there here what which who how when where why all any some more most very really about into over up out off""".split())


# ------------------------------------------------------------------ fetch + transcribe
def fetch(url):
    TMP.mkdir(parents=True, exist_ok=True)
    extra = ["--extractor-args", "youtube:player_client=tv_embedded"] if ("youtube.com" in url or "youtu.be" in url) else []
    cmd = ["yt-dlp", "--no-warnings", "-q", *extra, "-f", "ba/b", "-x", "--audio-format", "wav", "--write-info-json",
           "-o", str(TMP / "%(extractor_key)s-%(id)s.%(ext)s"), "--print", "after_move:filepath", url]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if p.returncode != 0 or not p.stdout.strip():
        raise RuntimeError((p.stderr or "download failed").strip()[-300:])
    wav = Path(p.stdout.strip().splitlines()[-1])
    info_path = wav.with_suffix(".info.json")
    info = json.loads(info_path.read_text()) if info_path.exists() else {}
    info_path.unlink(missing_ok=True)
    return wav, info


def to_wav(path):
    TMP.mkdir(parents=True, exist_ok=True)
    out = TMP / (Path(path).stem + "-src.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(path), "-vn", str(out)], check=True)
    return out


_SEP = None


def separate(wav):
    """Vocals only (UVR MDX-Net via audio-separator, CPU): music beds fool pitch tracking, so creators' mixes are
    measured on the isolated voice. Returns the vocals WAV (or the input if separation is unavailable)."""
    global _SEP
    try:
        from audio_separator.separator import Separator
    except Exception:
        print("    (no vocal separation: pip install torch --index-url https://download.pytorch.org/whl/cpu && pip install 'audio-separator[cpu]')")
        return wav
    if _SEP is None:
        _SEP = Separator(output_dir=str(TMP), output_format="WAV", output_single_stem="Vocals",
                         model_file_dir=str(Path.home() / ".cache/voice-study/uvr"), log_level=40,
                         mdx_params={"hop_length": 1024, "segment_size": 64, "overlap": 0.25, "batch_size": 1, "enable_denoise": False})
        _SEP.load_model(model_filename="UVR-MDX-NET-Voc_FT.onnx")
    outs = _SEP.separate(str(wav))
    voc = [TMP / Path(o).name for o in outs if "Vocals" in Path(o).name]
    return voc[0] if voc else wav


def head16(src, max_sec, sep):
    """First max_sec seconds -> (optional vocal separation) -> 16 kHz mono for whisper + VAD + Praat."""
    head = src.with_name(src.stem + "-head.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-t", str(max_sec), "-ar", "44100", str(head)], check=True)
    voc = separate(head) if sep else head
    out = src.with_name(src.stem + "-16k.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(voc), "-ac", "1", "-ar", "16000", str(out)], check=True)
    for f in {head, voc} - {out}:
        Path(f).unlink(missing_ok=True)
    return out


def words_of(wav, model="base.en", max_sec=75):
    """Word list [(word, t0, t1)] from whisper.cpp (one word per segment), first max_sec seconds of a 16 kHz mono WAV."""
    m = ss.MODELS / f"ggml-{model}.bin"
    if not m.exists():
        m.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["curl", "-fsSL", "-o", str(m), f"https://huggingface.co/ggerganov/whisper.cpp/resolve/main/{m.name}"], check=True)
    clip = wav
    prefix = clip.with_suffix("")
    subprocess.run([str(ss.WHISPER), "-m", str(m), "-f", str(clip), "-t", "2", "-l", "en", "-ml", "1", "-sow",
                    "-bs", "1", "-bo", "1", "-oj", "-of", str(prefix), "-np"], check=True, capture_output=True, timeout=900)
    data = json.loads(prefix.with_suffix(".json").read_text())
    prefix.with_suffix(".json").unlink(missing_ok=True)
    out = []
    for s in data.get("transcription", []):
        w = s["text"].strip()
        if not w or not re.search(r"[A-Za-z0-9]", w):
            if out and w:  # glue trailing punctuation to the previous word
                out[-1] = (out[-1][0] + w, out[-1][1], out[-1][2])
            continue
        out.append((w, s["offsets"]["from"] / 1000, s["offsets"]["to"] / 1000))
    return out, clip


# ------------------------------------------------------------------ prosody
def syllables(word):
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return max(1, len(re.sub(r"\D", "", word)))  # digits: roughly one syllable each
    n = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and n > 1 and not w.endswith("le"):
        n -= 1
    return max(1, n)


VAD_URL = "https://github.com/snakers4/silero-vad/raw/master/src/silero_vad/data/silero_vad.onnx"


def vad_runs(clip):
    """Speech runs [(t0, t1)] from Silero VAD (ONNX, 32 ms chunks): separates voice from music beds, so pauses are real."""
    import onnxruntime as ort
    import soundfile as sf
    model = Path.home() / ".cache/voice-study/silero_vad.onnx"
    if not model.exists():
        model.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["curl", "-fsSL", "-o", str(model), VAD_URL], check=True)
    x, sr = sf.read(str(clip), dtype="float32")
    if x.ndim > 1:
        x = x.mean(axis=1)
    sess = ort.InferenceSession(str(model), providers=["CPUExecutionProvider"])
    state = np.zeros((2, 1, 128), dtype=np.float32)
    ctx = np.zeros((1, 64), dtype=np.float32)
    probs = []
    for i in range(0, len(x) - 512 + 1, 512):
        chunk = np.concatenate([ctx, x[i:i + 512][None, :]], axis=1).astype(np.float32)
        out, state = sess.run(None, {"input": chunk, "state": state, "sr": np.array(16000, dtype=np.int64)})
        ctx = chunk[:, -64:]
        probs.append(float(out[0][0]))
    sp = np.array(probs) > 0.5
    runs, start = [], None
    for k, v in enumerate(sp):
        t = k * 0.032
        if v and start is None:
            start = t
        if not v and start is not None:
            runs.append((start, t))
            start = None
    if start is not None:
        runs.append((start, len(sp) * 0.032))
    merged = []  # gaps < 150 ms are not pauses
    for a, b in runs:
        if merged and a - merged[-1][1] < 0.15:
            merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))
    return [(round(a, 3), round(b, 3)) for a, b in merged if b - a >= 0.06]


def prosody(clip, words, runs=None):
    import parselmouth
    from parselmouth.praat import call
    snd = parselmouth.Sound(str(clip))
    pp = snd.to_pitch_ac(time_step=0.01, pitch_floor=60, pitch_ceiling=500)
    p1, t1s = pp.selected_array["frequency"], pp.xs()
    sp1 = np.ones_like(t1s, dtype=bool)
    if runs:  # speaker bounds from VAD speech frames only (music beds would drag them)
        sp1 = np.zeros_like(t1s, dtype=bool)
        for a, b in runs:
            sp1 |= (t1s >= a) & (t1s <= b)
    v1 = p1[(p1 > 0) & sp1]
    if len(v1) < 20:
        return None
    q25, q75 = np.percentile(v1, 25), np.percentile(v1, 75)
    floor, ceil = max(50.0, 0.75 * q25), min(600.0, 1.5 * q75)  # Hirst & De Looze speaker-adaptive bounds
    pitch = snd.to_pitch_ac(time_step=0.01, pitch_floor=floor, pitch_ceiling=ceil)
    pitch = call(pitch, "Kill octave jumps")
    f0, ft = pitch.selected_array["frequency"].copy(), pitch.xs()
    f0[~np.isfinite(f0) | (f0 < floor * 0.9) | (f0 > ceil * 1.1)] = 0.0  # unvoiced / out-of-speaker-range frames
    inten = snd.to_intensity(time_step=0.01, minimum_pitch=70)
    db, it = inten.values[0], inten.xs()
    inside = np.zeros_like(ft, dtype=bool)
    for _, a, b in words:
        inside |= (ft >= a) & (ft <= b)
    if runs:  # only frames the VAD calls speech
        spm = np.zeros_like(ft, dtype=bool)
        for a, b in runs:
            spm |= (ft >= a) & (ft <= b)
        inside &= spm
    f0[~inside] = 0.0
    voiced = inside & (f0 > 0)
    if voiced.sum() < 20:
        return None
    med = float(np.median(f0[voiced]))
    st_all = 12 * np.log2(np.where(f0 > 0, f0, med) / med)
    per = []
    for w, a, b in words:
        m = (ft >= a) & (ft <= b) & (f0 > 0)
        mi = (it >= a) & (it <= b)
        p = float(np.percentile(st_all[m], 90)) if m.sum() >= 2 else None
        e = float(np.max(db[mi])) if mi.sum() else None
        per.append({"w": w, "t0": round(a, 2), "t1": round(b, 2), "st": None if p is None else round(p, 2),
                    "db": None if e is None else round(e, 1), "syl": syllables(w)})
    # stressed words: pitch and/or loudness clearly above the neighbouring words (local median of +-4 words)
    for i, x in enumerate(per):
        nb = per[max(0, i - 4): i] + per[i + 1: i + 5]
        sts = [y["st"] for y in nb if y["st"] is not None]
        dbs = [y["db"] for y in nb if y["db"] is not None]
        dp = (x["st"] - stats.median(sts)) if (x["st"] is not None and sts) else 0.0
        dl = (x["db"] - stats.median(dbs)) if (x["db"] is not None and dbs) else 0.0
        rate = lambda y: (y["t1"] - y["t0"]) / y["syl"]
        drs = [rate(y) for y in nb if y["t1"] > y["t0"]]
        dr = (rate(x) / stats.median(drs)) if (drs and x["t1"] > x["t0"] and stats.median(drs) > 0) else 1.0
        x["dp"], x["dl"], x["dr"] = round(dp, 2), round(dl, 2), round(dr, 2)
        x["stress"] = bool((dp >= 2.0 and (dr >= 1.15 or dl >= 2.0)) or dp >= 3.0 or (dl >= 4.0 and dp >= 1.0))
    # frame-level movement: semitone change per 100 ms over consecutive voiced frames
    v = np.where(voiced)[0]
    steps = [abs(st_all[j] - st_all[j - 1]) for j in v[1:] if voiced[j - 1]]
    lm = np.zeros_like(it, dtype=bool)
    for a, b in (runs or [(words[0][1], words[-1][2])]):
        lm |= (it >= a) & (it <= b)
    loud = db[lm & (it >= words[0][1] - 0.2) & (it <= words[-1][2] + 0.2)]
    return {"median_hz": round(med), "range_st": round(float(np.percentile(st_all[voiced], 90) - np.percentile(st_all[voiced], 10)), 1),
            "sd_st": round(float(np.std(st_all[voiced])), 2), "move_st_100ms": round(float(np.mean(steps)) * 10, 2) if steps else 0.0,
            "loud_range_db": round(float(np.percentile(loud, 90) - np.percentile(loud, 10)), 1) if len(loud) else 0.0}, per


def delivery(per, runs=None):
    n = len(per)
    span = per[-1]["t1"] - per[0]["t0"] if n else 1
    if runs:
        runs = [r for r in runs if r[1] > per[0]["t0"] - 0.3 and r[0] < per[-1]["t1"] + 0.3]
        pauses = [runs[i][0] - runs[i - 1][1] for i in range(1, len(runs))]
        phrases = []
        for a, b in runs:  # words whose midpoint falls inside the speech run
            ph = [x for x in per if a - 0.05 <= (x["t0"] + x["t1"]) / 2 <= b + 0.05]
            if ph:
                phrases.append((ph, b - a))
        rates = [sum(x["syl"] for x in ph) / max(0.25, dur) for ph, dur in phrases if len(ph) >= 3]
        phrases = [ph for ph, _ in phrases]
    else:
        gaps = [(per[i]["t0"] - per[i - 1]["t1"]) for i in range(1, n)]
        pauses = [g for g in gaps if g >= 0.15]
        phrases, cur = [], [per[0]] if n else []
        for i in range(1, n):
            if gaps[i - 1] >= 0.15:
                phrases.append(cur)
                cur = []
            cur.append(per[i])
        if cur:
            phrases.append(cur)
        rates = [sum(x["syl"] for x in ph) / max(0.25, ph[-1]["t1"] - ph[0]["t0"]) for ph in phrases if len(ph) >= 3]
    ends = []
    for ph in phrases:
        sts = [x["st"] for x in ph if x["st"] is not None]
        if len(sts) >= 3:
            ends.append(sts[-1] - stats.mean(sts[:-1]))
    stressed = [x for x in per if x.get("stress")]
    content = [x["w"].strip(".,!?;:\"'").lower() for x in stressed if x["w"].strip(".,!?;:\"'").lower() not in FUNC]
    return {"words": n, "wpm": round(n / span * 60) if span else 0,
            "syl_per_s": round(stats.mean(rates), 2) if rates else None,
            "speed_var_pct": round(stats.pstdev(rates) / stats.mean(rates) * 100) if len(rates) >= 3 else None,
            "pauses_per_min": round(len(pauses) / span * 60, 1) if span else 0,
            "pause_mean_s": round(stats.mean(pauses), 2) if pauses else 0,
            "stress_pct": round(len(stressed) / n * 100) if n else 0,
            "stressed_words": content[:14],
            "end_rise_pct": round(sum(1 for e in ends if e > 1.5) / len(ends) * 100) if ends else None,
            "end_fall_pct": round(sum(1 for e in ends if e < -1.5) / len(ends) * 100) if ends else None}


def script_stats(per):
    text = " ".join(x["w"] for x in per)
    sents = [s for s in re.split(r"(?<=[.?!])\s+", text) if re.search(r"\w", s)]
    lens = [len(re.findall(r"[\w'’-]+", s)) for s in sents]
    nw = max(1, len(per))
    low = text.lower()
    return {"words_per_sentence": round(stats.mean(lens), 1) if lens else None,
            "sentence_len_sd": round(stats.pstdev(lens), 1) if len(lens) > 1 else None,
            "questions_per_100w": round(text.count("?") / nw * 100, 1),
            "you_per_100w": round(len(re.findall(r"\byou(r|'re|'ll)?\b", low)) / nw * 100, 1),
            "numbers_per_100w": round(len(re.findall(r"\d|\b(one|two|three|four|five|six|seven|eight|nine|ten|hundred|thousand|million|billion)\b", low)) / nw * 100, 1),
            "contractions_pct": round(len(re.findall(r"\b\w+['’](s|re|ll|ve|d|t|m)\b", low)) / nw * 100, 1),
            "excerpt": " ".join(text.split()[:20])}


# ------------------------------------------------------------------ run + report
def study(label, src, info, url, sep=True, max_sec=45):
    wav = head16(Path(src), max_sec, sep)
    words, clip = words_of(wav)
    if len(words) < 25:
        raise RuntimeError(f"only {len(words)} words: music-only or no speech")
    try:
        runs = vad_runs(clip)
    except Exception as ex:  # VAD optional: fall back to word gaps
        print(f"    (VAD unavailable: {str(ex)[:80]})")
        runs = None
    res = prosody(clip, words, runs)
    if not res:
        raise RuntimeError("no voiced speech found")
    glob, per = res
    row = {"label": label, "url": url, "views": info.get("view_count"), "duration": info.get("duration"),
           "studied": dt.date.today().isoformat(), **glob, **delivery(per, runs), **script_stats(per)}
    RAW.mkdir(parents=True, exist_ok=True)
    key = re.sub(r"[^\w-]+", "-", label)[:60]
    (RAW / f"{key}.json").write_text(json.dumps({"row": row, "words": per}, ensure_ascii=False))
    for f in {Path(src), Path(wav), Path(clip)}:
        f.unlink(missing_ok=True)
    row["separated"] = bool(sep)
    return row


METRICS = [("range_st", "pitch range (semitones)"), ("sd_st", "pitch variation SD (st)"), ("move_st_100ms", "pitch movement (st / 100 ms)"),
           ("loud_range_db", "loudness range (dB)"), ("wpm", "words per minute"), ("speed_var_pct", "speed change between phrases (%)"),
           ("pauses_per_min", "pauses per minute (>=150 ms)"), ("pause_mean_s", "average pause (s)"), ("stress_pct", "stressed words (%)"),
           ("end_fall_pct", "phrases ending with a pitch fall (%)"), ("end_rise_pct", "phrases ending with a pitch rise (%)"),
           ("words_per_sentence", "words per sentence"), ("questions_per_100w", "questions per 100 words"),
           ("you_per_100w", "'you' per 100 words"), ("contractions_pct", "contractions per 100 words")]


def report():
    rows = [json.loads(f.read_text())["row"] for f in sorted(RAW.glob("*.json"))]
    ours = [r for r in rows if r["label"].startswith("ours")]
    them = [r for r in rows if not r["label"].startswith("ours")]

    def med(rs, k):
        v = [r.get(k) for r in rs if isinstance(r.get(k), (int, float))]
        return round(stats.median(v), 1) if v else None
    L = [f"# Voice study: how the reference creators deliver their scripts ({dt.date.today().isoformat()})", "",
         "Measured, not guessed: whisper.cpp word timings + Praat prosody (tools/voice_study.py). Audio deleted after analysis.", "",
         f"## Creators ({len(them)} videos) vs our current voice ({len(ours)} videos)", "",
         "| Metric | Creators (median) | Creators (range) | Ours (median) |", "|---|---|---|---|"]
    for k, name in METRICS:
        v = [r.get(k) for r in them if isinstance(r.get(k), (int, float))]
        rng = f"{min(v)}–{max(v)}" if v else ""
        L.append(f"| {name} | {med(them, k)} | {rng} | {med(ours, k)} |")
    L += ["", "## Per video", "", "| Video | Views | wpm | pitch range | movement | loud range | speed var | pauses/min | stressed % | stressed words (sample) |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for r in them + ours:
        L.append(f"| [{r['label']}]({r['url']}) | {r.get('views') or ''} | {r['wpm']} | {r['range_st']} | {r['move_st_100ms']} | {r['loud_range_db']} | "
                 f"{r.get('speed_var_pct')} | {r['pauses_per_min']} | {r['stress_pct']} | {', '.join(r['stressed_words'][:8])} |")
    L += ["", "## Hook excerpts (first 20 words)", ""] + [f"- **{r['label']}**: \"{r['excerpt']}\"" for r in them]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "voice-study.md").write_text("\n".join(L) + "\n")
    print(f"-> research/voice/voice-study.md ({len(them)} creator videos, {len(ours)} ours)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--account", action="append", default=[])
    ap.add_argument("--latest", type=int, default=12)
    ap.add_argument("--top", type=int, default=2, help="most-viewed N of the latest per account")
    ap.add_argument("--url", action="append", default=[])
    ap.add_argument("--file", action="append", default=[])
    ap.add_argument("--label", default=None)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--no-separate", action="store_true", help="skip vocal separation (clean voice files)")
    a = ap.parse_args()
    jobs = [(None, u) for u in a.url]
    for acc in a.account:
        try:
            items = ss.list_account(acc, a.latest, None)
        except SystemExit as ex:
            print(f"  ✗ {acc}: {ex}")
            continue
        items = sorted(items, key=lambda e: -(e["views"] or 0))[: a.top]
        jobs += [(acc.rstrip("/").split("/")[-1].replace("@", "") , e["url"]) for e in items]
    for who, u in jobs:
        try:
            wav, info = fetch(u)
            handle = who or info.get("uploader") or info.get("channel") or info.get("uploader_id") or "video"
            label = f"{str(handle).lstrip('@')} {info.get('id', '')}".strip()
            r = study(label, wav, info, u, sep=not a.no_separate)
            print(f"  ✓ {label}: wpm {r['wpm']}, pitch range {r['range_st']} st, stressed {r['stress_pct']}%, speed var {r['speed_var_pct']}%")
        except Exception as ex:
            print(f"  ✗ {u}: {str(ex)[:160]}")
    for f in a.file:
        try:
            r = study(a.label or f"ours: {Path(f).stem}", to_wav(f), {}, f"file:{Path(f).name}", sep=not a.no_separate)
            print(f"  ✓ {r['label']}: wpm {r['wpm']}, pitch range {r['range_st']} st, stressed {r['stress_pct']}%, speed var {r['speed_var_pct']}%")
        except Exception as ex:
            print(f"  ✗ {f}: {str(ex)[:160]}")
    if a.report or jobs or a.file:
        report()


if __name__ == "__main__":
    main()
