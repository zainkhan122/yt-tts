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


def narrate(lines: list[str], voice_path: Path, out_dir: Path) -> list[Path]:
    """One wav per scene, so scene boundaries are exact rather than guessed."""
    from piper import PiperVoice

    voice = PiperVoice.load(str(voice_path))
    wavs = []
    for i, line in enumerate(lines):
        w = out_dir / f"line{i:02d}.wav"
        with wave.open(str(w), "wb") as fh:
            voice.synthesize_wav(line, fh)
        wavs.append(w)
    return wavs


def concat(wavs: list[Path], out: Path) -> list[tuple[float, float]]:
    """Join the per-scene wavs with small gaps, return each scene's (start, end) in seconds."""
    ff = _ffmpeg()
    probe = subprocess.run([ff, "-i", str(wavs[0]), "-f", "null", "-"],
                           capture_output=True, text=True, errors="replace")
    rate = 22050
    for tok in probe.stderr.split():
        if tok.startswith("22050") or tok.endswith("Hz,") and tok[:-3].isdigit():
            rate = int(tok.rstrip("Hz,"))
            break

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
    ap.add_argument("--voice", default=str(Path.home() / ".cache/piper/en_US-ryan-high.onnx"))
    ap.add_argument("--work", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--crf", type=int, default=20)
    ap.add_argument("--delivery-crf", type=int, default=25)
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

    timing, order, words = {}, [], []
    for scene, say, (a, b) in zip(brief["scenes"], lines, spans):
        wt = word_timings(say, a, b)
        timing[scene["id"]] = {"words": wt}
        order.append(scene["id"])
        words += wt

    doc, phrases = plan_scenes(sheet, source, beats, segments_from_timing(timing, order),
                               duration, words)
    print(f"planned {len(doc['scenes'])} scenes: "
          f"{[s['archetype'] for s in doc['scenes']]}", flush=True)

    t1 = time.time()
    info = render(doc, voice_wav, out, work, duration, crf=args.crf)
    # A second, slower pass at a smaller crf keeps the delivered file upload-sized without
    # softening the type: the stage is flat colour and text, so it survives this well.
    if args.delivery_crf:
        tmp = out.with_suffix(".delivery.mp4")
        subprocess.run([_ffmpeg(), "-y", "-loglevel", "error", "-i", str(out), "-c:v", "libx264",
                        "-preset", "slow", "-crf", str(args.delivery_crf), "-pix_fmt", "yuv420p",
                        "-c:a", "copy", "-movflags", "+faststart", str(tmp)],
                       check=True, capture_output=True)
        tmp.replace(out)
    print(f"rendered in {time.time() - t1:.1f}s -> {out} ({out.stat().st_size / 1e6:.1f} MB)", flush=True)
    (out.parent / f"{args.brief_id}.render.json").write_text(
        json.dumps({"brief": args.brief_id, "duration_s": round(duration, 3),
                    "scenes": [{"id": s["id"], "archetype": s["archetype"],
                                "t0": s["t0"], "t1": s["t1"]} for s in doc["scenes"]],
                    "render": info}, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
