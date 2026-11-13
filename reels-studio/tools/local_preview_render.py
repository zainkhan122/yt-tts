"""Render a graphics brief end to end on a laptop-class box: piper narration + the normal
graphics stage. Produces the same artifact the cloud pipeline does (1080x1920, 30 fps, AAC),
without torch/chatterbox.

    python3 tools/local_preview_render.py tool-seedance-01 --voice ~/.cache/piper/en_US-ryan-high.onnx

Why this exists: the production voice engine (chatterbox) needs a GPU box, so a plan could only
be checked by spending a cloud run. This renders the real stage against real narration locally,
so a bad beat, a NaN counter or a missing hero is caught before dispatch (lesson: gates that
never look at pixels pass bad video).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from graphics.render import render  # noqa: E402
from graphics.stage import plan_scenes, segments_from_timing  # noqa: E402

GAP_S = 0.28          # breath between scenes, same idea as the production flow cut
LEAD_IN_S = 0.45      # a beat of silence so the hook is not clipped


def _ffmpeg() -> str:
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:  # noqa: BLE001 - fall back to a system ffmpeg
        return shutil.which("ffmpeg") or "ffmpeg"


HOUSE_VOICE = "am_michael"     # config: the voice every shipped short uses
HOUSE_SPEED = 1.15


def narrate(lines: list[str], voice_path: Path, out_dir: Path) -> list[Path]:
    """One wav per scene, so scene boundaries are exact rather than guessed.

    Owner rule (2026-11-13): the voice is the house voice. Kokoro `am_michael` at 1.15 is what
    every shipped short uses, so a preview must not be narrated in some other engine's timbre —
    judging pacing and hook strength against the wrong voice is judging the wrong video.
    Piper stays available via --engine piper for a quick offline check.
    """
    if voice_path.suffix == ".onnx" and "kokoro" not in str(voice_path):
        from piper import PiperVoice
        voice = PiperVoice.load(str(voice_path))
        wavs = []
        for i, line in enumerate(lines):
            w = out_dir / f"line{i:02d}.wav"
            with wave.open(str(w), "wb") as fh:
                voice.synthesize_wav(line, fh)
            wavs.append(w)
        return wavs

    import numpy as np
    import soundfile as sf
    from kokoro_onnx import Kokoro

    # model weights live inside the workspace, not ~/.cache: ~/.cache is not persisted between
    # sessions, and a missing 325 MB model mid-render is a hard stop. models/ is gitignored.
    cands = [ROOT.parent / "models" / "kokoro", Path.home() / ".cache/kokoro"]
    cache = next((c for c in cands if (c / "kokoro-v1.0.onnx").exists()), cands[0])
    if not (cache / "kokoro-v1.0.onnx").exists():
        raise SystemExit(
            f"kokoro model not found. Fetch it once:\n"
            f"  mkdir -p {cands[0]} && cd {cands[0]}\n"
            f"  curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/"
            f"model-files-v1.0/kokoro-v1.0.onnx\n"
            f"  curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/"
            f"model-files-v1.0/voices-v1.0.bin")
    k = Kokoro(str(cache / "kokoro-v1.0.onnx"), str(cache / "voices-v1.0.bin"))
    wavs = []
    for i, line in enumerate(lines):
        samples, sr = k.create(line, voice=HOUSE_VOICE, speed=HOUSE_SPEED, lang="en-us")
        w = out_dir / f"line{i:02d}.wav"
        sf.write(str(w), np.asarray(samples, dtype="float32"), sr)
        wavs.append(w)
    return wavs


def concat(wavs: list[Path], out: Path) -> list[tuple[float, float]]:
    """Join the per-scene wavs with small gaps, return each scene's (start, end) in seconds."""
    ff = _ffmpeg()
    # All concat-demuxer inputs must share the voice format. Using a 22.05 kHz silence
    # before 24 kHz Kokoro clips makes ffmpeg interpret clip samples at the wrong rate,
    # stretching the narration and invalidating every scene span.
    with wave.open(str(wavs[0]), "rb") as source:
        rate = source.getframerate()
        channels = source.getnchannels()
    if channels != 1:
        raise ValueError("preview narration must be mono")
    for wav in wavs[1:]:
        with wave.open(str(wav), "rb") as source:
            if source.getframerate() != rate or source.getnchannels() != channels:
                raise ValueError("narration clips must share a sample rate and channel count")

    silence = ffmpeg_silence(ff, GAP_S, rate, out.parent / "gap.wav")
    lead = ffmpeg_silence(ff, LEAD_IN_S, rate, out.parent / "lead.wav")
    parts, spans, t = [lead], [], LEAD_IN_S
    for w in wavs:
        dur = wav_seconds(w)
        parts.append(w)
        spans.append((t, t + dur))
        t += dur + GAP_S
        parts.append(silence)
    # trim the trailing gap
    listfile = out.parent / "concat.txt"
    listfile.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
    subprocess.run([ff, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", str(listfile), "-ar", "48000", "-ac", "1", str(out)],
                   check=True, capture_output=True)
    return spans


def ffmpeg_silence(ff: str, secs: float, rate: int, path: Path) -> Path:
    subprocess.run([ff, "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    f"anullsrc=r={rate}:cl=mono", "-t", f"{secs:.3f}", str(path)],
                   check=True, capture_output=True)
    return path


def wav_seconds(path: Path) -> float:
    with wave.open(str(path), "rb") as fh:
        return fh.getnframes() / float(fh.getframerate())


def assign_words_to_spans(flat, spans):
    """Assign every aligned word at the midpoint of each gap between scene audio clips."""
    import bisect
    boundaries = [(spans[i][1] + spans[i + 1][0]) / 2 for i in range(len(spans) - 1)]
    buckets = [[] for _ in spans]
    for w, t0, t1 in flat:
        buckets[bisect.bisect_right(boundaries, (t0 + t1) / 2)].append([w, t0, t1])
    return buckets


def aligned_timings(vo_wav: Path, script: str, spans, lines, voice_path: Path) -> tuple[dict, list, list, str]:
    """Real word timings from the finished voice, via tools/align_words.py.

    The blind length-weighted split below was the reason captions drifted and cue words fired early.
    This runs whisper on the actual voice file and matches the result back onto our script tokens.
    If the match is poor the aligner says so and we fall back rather than shipping wrong timings.
    """
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        from align_words import align  # noqa: PLC0415

        doc = align(Path(vo_wav), script, model_size="base.en")
    except Exception as exc:  # noqa: BLE001 - a missing model must not kill a render
        print(f"align: unavailable ({exc}); falling back to a length-weighted split", flush=True)
        doc = None
    if not doc or doc["method"].startswith("length"):
        # fall back, but assign words to scenes by position so the cues still land roughly right
        timing, order, words = {}, [], []
        for scene, say, (a, b) in zip([{"id": f"s{i:02d}"} for i in range(len(lines))], lines, spans):
            wt = word_timings(say, a, b)
            timing[scene["id"]] = {"words": wt}
            order.append(scene["id"])
            words += wt
        return timing, order, words, doc["method"] if doc else "length-weighted"

    flat = doc["words"]
    print(f"align: {doc['method']}  match {doc['match']}  words {len(flat)}", flush=True)
    # The aligner emits the script's tokens in order. Narration is generated scene by scene,
    # so token ownership comes from the script, not estimated timestamps: this prevents a
    # whisper misalignment from moving a warning or a CTA into the wrong visual scene.
    from align_words import tokens
    expected = [tokens(line) for line in lines]
    if [w[0] for w in flat] != [w for group in expected for w in group]:
        raise ValueError("aligned script tokens do not match scene scripts")
    buckets = []
    offset = 0
    for group in expected:
        buckets.append(flat[offset:offset + len(group)])
        offset += len(group)
    timing, order = {}, []
    words: list[list] = []
    for i, sid in enumerate(f"s{k:02d}" for k in range(len(spans))):
        timing[sid] = {"words": buckets[i]}
        order.append(sid)
        words += buckets[i]
    assert len(words) == len(flat), f"aligner lost words: {len(words)} of {len(flat)}"
    return timing, order, words, doc["method"]


def word_timings(say: str, t0: float, t1: float) -> list[list]:
    """Distribute the spoken words across the scene's real audio span, weighting by length.

    The stage only needs this to fire cue words and to sync the word-by-word reveal, so a
    length-weighted distribution inside the true audio bounds is honest enough for a preview.
    """
    words = say.split()
    if not words:
        return []
    weights = [max(2, len(w)) for w in words]
    total = sum(weights)
    span = max(0.2, t1 - t0)
    out, t = [], t0
    for w, wt in zip(words, weights):
        d = span * wt / total
        out.append([w, round(t, 3), round(t + d, 3)])
        t += d
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("brief_id")
    ap.add_argument("--voice", default=str(Path.home() / ".cache/kokoro/kokoro-v1.0.onnx"),
                    help="kokoro onnx (house voice by default); pass a piper .onnx to fall back")
    ap.add_argument("--work", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--crf", type=int, default=20,
                    help="intermediate encode; ignored when --delivery-crf is set (the delivered "
                         "pass carries the quality, so there is no point paying for two)")
    ap.add_argument("--delivery-crf", type=int, default=25)
    ap.add_argument("--preset", default="veryfast", help="x264 preset for local preview (production default: medium)")
    ap.add_argument("--house-gate", action="store_true",
                    help="run tools/house_gate.py against the built stage before encoding; a broken "
                         "caption/outro contract fails the render instead of shipping")
    args = ap.parse_args()

    brief = json.loads((ROOT / "briefs" / f"{args.brief_id}.json").read_text(encoding="utf-8"))
    gdir = ROOT / brief["graphics"]["dir"]
    beats = json.loads((gdir / "beats.json").read_text(encoding="utf-8"))
    sheet = json.loads((gdir / "features.json").read_text(encoding="utf-8"))
    source = (gdir / "source.md").read_text(encoding="utf-8")

    # never /tmp: it is a small tmpfs here and 1600 frames fills it (screenshot then fails)
    default_work = ROOT / "renders" / args.brief_id / "work"
    default_work.parent.mkdir(parents=True, exist_ok=True)
    work = Path(args.work) if args.work else Path(tempfile.mkdtemp(
        prefix=f"gfx-{args.brief_id}-", dir=default_work.parent, ))
    work.mkdir(parents=True, exist_ok=True)
    out = Path(args.out) if args.out else ROOT / "renders" / args.brief_id / f"{args.brief_id}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)

    lines = [s["say"] for s in brief["scenes"]]
    t0 = time.time()
    wavs = narrate(lines, Path(args.voice), work)
    print(f"narrated {len(wavs)} scenes in {time.time() - t0:.1f}s", flush=True)

    voice_wav = work / "vo.wav"
    spans = concat(wavs, voice_wav)
    duration = wav_seconds(voice_wav)
    print(f"voiceover {duration:.2f}s", flush=True)

    ids = [scene["id"] for scene in brief["scenes"]]
    timing, _order, words, align_method = aligned_timings(
        voice_wav, " ".join(lines), spans, lines, Path(args.voice))
    # the brief's own scene ids are authoritative — the beat plan is keyed on them (rule B9)
    timing = {sid: timing[f"s{i:02d}"] for i, sid in enumerate(ids)}
    order = ids

    doc, phrases = plan_scenes(sheet, source, beats, segments_from_timing(timing, order),
                               duration, words)
    print(f"planned {len(doc['scenes'])} scenes: "
          f"{[s['archetype'] for s in doc['scenes']]}", flush=True)
    print(f"template: {doc.get('template')} (brief: {beats.get('template')})", flush=True)

    if args.house_gate:
        # render() builds stage.html itself, so the contract is checked there: pre-encode, and the
        # check aborts the encode rather than letting a broken caption/outro ship
        os.environ["HOUSE_GATE"] = "1"

    t1 = time.time()
    # ONE encode pass, at the delivered quality. The old path encoded at crf 20/medium and then
    # re-encoded the whole short at crf 26/slow: two x264 passes over ~2,400 frames, nine minutes
    # spent to produce a file whose quality came entirely from the second pass.
    info = render(doc, voice_wav, out, work, duration,
                  crf=args.delivery_crf or args.crf, preset=args.preset)
    print(f"rendered in {time.time() - t1:.1f}s -> {out} ({out.stat().st_size / 1e6:.1f} MB)", flush=True)
    (out.parent / f"{args.brief_id}.render.json").write_text(
        json.dumps({"brief": args.brief_id, "duration_s": round(duration, 3),
                    "scenes": [{"id": s["id"], "archetype": s["archetype"],
                                "t0": s["t0"], "t1": s["t1"]} for s in doc["scenes"]],
                    "render": info}, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
