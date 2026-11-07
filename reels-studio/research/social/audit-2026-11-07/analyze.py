#!/usr/bin/env python3
"""Frame + audio audit of a Short: 20 fps structural analysis, palette, captions, faces, audio bed, TTS rate."""
import json
import subprocess
import sys
from pathlib import Path

import cv2
import imageio_ffmpeg
import numpy as np

FF = imageio_ffmpeg.get_ffmpeg_exe()
FPS = 20
W = 270

cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
cascade_p = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")


def read_wav(mp4, out):
    subprocess.run([FF, "-y", "-v", "error", "-i", str(mp4), "-ac", "1", "-ar", "16000", str(out)], check=True)
    import soundfile as sf
    x, sr = sf.read(out, dtype="float32")
    return x, sr


def audio_stats(mp4, tmp):
    x, sr = read_wav(mp4, tmp / "a.wav")
    hop = int(0.02 * sr)
    n = len(x) // hop
    if n < 10:
        return {}
    rms = np.sqrt(np.mean(x[: n * hop].reshape(n, hop) ** 2, axis=1) + 1e-12)
    db = 20 * np.log10(rms + 1e-9)
    peak = float(np.max(np.abs(x)))
    loud = float(np.percentile(db, 90))
    floor = float(np.percentile(db, 5))
    # speech vs bed: frames above (floor + 12 dB) are speech-ish
    thr = max(floor + 12, loud - 35)
    speech = db > thr
    # silence runs
    runs, cur = [], 0
    for s in speech:
        if not s:
            cur += 1
        elif cur:
            runs.append(cur * 0.02)
            cur = 0
    if cur:
        runs.append(cur * 0.02)
    gaps = [r for r in runs if r >= 0.25]
    # spectral tilt / flatness for music detection
    win = int(0.04 * sr)
    step = int(0.02 * sr)
    cents, flat = [], []
    for i in range(0, max(1, len(x) - win), step * 4):
        seg = x[i:i + win] * np.hanning(win)
        if len(seg) < win:
            break
        sp = np.abs(np.fft.rfft(seg)) + 1e-9
        f = np.fft.rfftfreq(win, 1 / sr)
        cents.append(float((sp * f).sum() / sp.sum()))
        flat.append(float(np.exp(np.mean(np.log(sp))) / np.mean(sp)))
    # F0 by autocorrelation on voiced frames
    f0s = []
    for i in range(0, len(x) - 1024, 512):
        seg = x[i:i + 1024]
        if np.sqrt(np.mean(seg ** 2)) < 0.01:
            continue
        seg = seg - seg.mean()
        ac = np.correlate(seg, seg, "full")[1023:]
        if ac[0] <= 0:
            continue
        ac = ac / ac[0]
        lo, hi = int(sr / 320), int(sr / 70)
        seg_ac = ac[lo:hi]
        if not len(seg_ac):
            continue
        k = int(np.argmax(seg_ac)) + lo
        if seg_ac.max() > 0.3:
            f0s.append(sr / k)
    # energy transients (SFX / hits): onsets per minute
    d = np.diff(db)
    onsets = int(np.sum(d > 9))
    dur = len(x) / sr
    return {
        "duration_s": round(dur, 2),
        "loud_p90_dbfs": round(loud, 1),
        "floor_p05_dbfs": round(floor, 1),
        "silence_share": round(float(1 - speech.mean()), 3),
        "pauses_over_250ms_per_min": round(len(gaps) / (dur / 60), 1),
        "longest_pause_s": round(max(gaps) if gaps else 0.0, 2),
        "spectral_centroid_hz": round(float(np.median(cents)) if cents else 0, 0),
        "spectral_flatness": round(float(np.median(flat)) if flat else 0, 3),
        "f0_median_hz": round(float(np.median(f0s)) if f0s else 0, 1),
        "f0_iqr_hz": round(float(np.percentile(f0s, 75) - np.percentile(f0s, 25)) if f0s else 0, 1),
        "energy_onsets_per_min": round(onsets / (dur / 60), 1),
        "peak": round(peak, 3),
    }


def frames_stats(mp4):
    cap = cv2.VideoCapture(str(mp4))
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30
    n_src = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    h_src = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    w_src = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    step = max(1, round(src_fps / FPS))
    diffs, whites, bands, edges, faces, face_area = [], [], [], [], [], []
    pal_samples = []
    prev = None
    idx = 0
    times = []
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        if idx % step == 0:
            t = idx / src_fps
            times.append(t)
            h, w = fr.shape[:2]
            scale = W / w
            small = cv2.resize(fr, (W, int(h * scale)))
            g = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY).astype(np.float32)
            if prev is not None:
                diffs.append(float(np.mean(np.abs(g - prev))))
            prev = g
            hh = g.shape[0]
            white = (g > 225)
            whites.append(float(white.mean()))
            bands.append([round(float(white[int(hh * a):int(hh * b)].mean()), 3)
                          for a, b in ((0, .15), (.15, .40), (.40, .65), (.65, .85), (.85, 1.0))])
            edges.append(round(float((cv2.Canny(g.astype(np.uint8), 80, 160) > 0).mean()), 4))
            if len(times) % 5 == 0:
                gray8 = g.astype(np.uint8)
                hits = list(cascade.detectMultiScale(gray8, 1.15, 4, minSize=(24, 24)))
                if not hits:
                    hits = list(cascade_p.detectMultiScale(gray8, 1.15, 4, minSize=(24, 24)))
                faces.append(1 if hits else 0)
                if hits:
                    x, y, fw, fh = max(hits, key=lambda r: r[2] * r[3])
                    face_area.append((fw * fh) / (W * hh))
            if len(times) % 20 == 0:
                pal_samples.append(cv2.resize(fr, (48, 85)))
        idx += 1
    cap.release()
    diffs = np.array(diffs)
    cut_thr = 22.0
    cuts = int(np.sum(diffs > cut_thr))
    dur = (n_src / src_fps) if src_fps else (len(times) / FPS)
    # palette
    if pal_samples:
        arr = np.concatenate([s.reshape(-1, 3) for s in pal_samples]).astype(np.float32)
        crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 12, 1.0)
        _, labels, centers = cv2.kmeans(arr, 5, None, crit, 3, cv2.KMEANS_PP_CENTERS)
        counts = np.bincount(labels.flatten(), minlength=5)
        order = np.argsort(-counts)
        palette = [{"rgb": [int(v) for v in centers[i][::-1]], "share": round(float(counts[i] / counts.sum()), 3)}
                   for i in order]
    else:
        palette = []
    chromatic = 0.0
    if pal_samples:
        sample = np.concatenate([s.reshape(-1, 3) for s in pal_samples]).reshape(-1, 1, 3).astype(np.uint8)
        hsv = cv2.cvtColor(sample, cv2.COLOR_BGR2HSV).reshape(-1, 3)
        chromatic = float(np.mean(hsv[:, 1] / 255.0))
    sat = round(float(np.mean([max(c["rgb"]) - min(c["rgb"]) for c in palette])) / 255, 3) if palette else 0
    return {
        "src_fps": round(src_fps, 2), "resolution": f"{w_src}x{h_src}", "sampled_frames": len(times),
        "duration_s": round(dur, 2),
        "cuts": cuts, "cuts_per_min": round(cuts / (dur / 60), 1) if dur else 0,
        "mean_shot_s": round(dur / max(1, cuts + 1), 2),
        "motion_energy": round(float(np.mean(diffs)), 2),
        "static_share": round(float(np.mean(diffs < 1.0)), 3),
        "hard_cut_share_of_changes": round(float(np.sum(diffs > cut_thr) / max(1, np.sum(diffs > 3))), 3),
        "white_share": round(float(np.mean(whites)), 3),
        "band_white": [round(float(np.mean([b[i] for b in bands])), 3) for i in range(5)],
        "edge_density": round(float(np.mean(edges)), 4),
        "face_frame_share": round(float(np.mean(faces)), 3) if faces else 0.0,
        "face_area_median": round(float(np.median(face_area)), 3) if face_area else 0.0,
        "palette": palette,
        "palette_max_chroma": sat,
    }


def main(mp4, out_json, model=None):
    mp4 = Path(mp4)
    tmp = Path("/var/tmp/audit/tmp")
    tmp.mkdir(parents=True, exist_ok=True)
    a = audio_stats(mp4, tmp)
    r = {"file": mp4.name, **frames_stats(mp4), **a}
    if model is not None:
        import soundfile as sf
        wav, sr = sf.read(tmp / "a.wav", dtype="float32")
        segs, info = model.transcribe(wav, language="en", vad_filter=True, word_timestamps=True)
        words = []
        seg_list = []
        for s in segs:
            seg_list.append({"t0": round(s.start, 2), "t1": round(s.end, 2), "text": s.text.strip()})
            for w in (s.words or []):
                words.append([w.word.strip(), round(w.start, 2), round(w.end, 2)])
        speech_span = (words[-1][2] - words[0][1]) if words else 0
        r["transcript"] = seg_list
        r["words"] = len(words)
        r["speech_span_s"] = round(speech_span, 2)
        r["wpm"] = round(len(words) / speech_span * 60, 1) if speech_span > 1 else 0
        r["words_per_video_s"] = round(len(words) / r["duration_s"] * 60, 1) if r.get("duration_s") else 0
        r["first_word_at"] = words[0][1] if words else None
    Path(out_json).write_text(json.dumps(r, indent=1))
    return r


if __name__ == "__main__":
    from faster_whisper import WhisperModel
    model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
    for f in sys.argv[1:]:
        out = Path("/var/tmp/audit/meta") / (Path(f).stem + ".json")
        out.parent.mkdir(parents=True, exist_ok=True)
        r = main(f, out, model)
        print(f"{r['file'][:34]:36s} {r['duration_s']:>6}s cuts/min={r.get('cuts_per_min'):>5} shot={r.get('mean_shot_s'):>5}s "
              f"face={r.get('face_frame_share'):>4} wpm={r.get('wpm'):>6} static={r.get('static_share'):>5} white={r.get('white_share'):>5}")
