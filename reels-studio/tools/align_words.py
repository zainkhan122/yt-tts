#!/usr/bin/env python3
"""Align spoken audio to words, so captions and beats land on the actual voice.

    python3 tools/align_words.py renders/<id>/work/vo.wav --text "the exact script" --out work/words.json

Why this exists: there was no aligner. Every "word timing" in a body was a blind linear split of
the scene duration by character count. That is why captions drift, why a cue word fires early, and
why beats feel out of step with the voice. The skill's rule is a visual event every 1.5-2.5 s *on
the spoken word* — that is impossible without real timings.

faster-whisper (CTranslate2, CPU) returns word-level timestamps. Two guards:

  * the recognizer's words are matched back onto OUR script tokens, so a misheard word cannot
    invent a caption that was never spoken;
  * when the recognizer and the script disagree badly (< min_match), the aligner falls back to a
    length-weighted split and SAYS SO, instead of silently shipping wrong timings.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
from pathlib import Path

_TOKEN = re.compile(r"[a-z0-9']+")


def tokens(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def _load_mono(path: Path):
    """Decode with soundfile and hand faster-whisper a raw array.

    faster-whisper's own decoder goes through PyAV, and current faster-whisper passes a
    `metadata_errors=` kwarg that the installed PyAV build rejects. Decoding ourselves removes the
    dependency on that pairing, and we already require soundfile for the voice stage.
    """
    import numpy as np
    import soundfile as sf

    x, sr = sf.read(str(path), dtype="float32", always_2d=False)
    if getattr(x, "ndim", 1) > 1:
        x = x.mean(axis=1)
    if sr != 16000:
        # faster-whisper resamples arrays itself only for its own loader, so resample here
        n = int(round(len(x) * 16000 / sr))
        idx = np.linspace(0, len(x) - 1, n)
        x = np.interp(idx, np.arange(len(x)), x).astype("float32")
    return np.ascontiguousarray(x)


def align(wav, script: str, model_size: str = "base.en", min_match: float = 0.75) -> dict:
    from faster_whisper import WhisperModel

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    audio = _load_mono(Path(wav)) if not hasattr(wav, "ndim") else wav
    segments, info = model.transcribe(audio, word_timestamps=True, language="en",
                                      vad_filter=False, beam_size=5)
    heard: list[tuple[str, float, float]] = []
    for seg in segments:
        for w in (seg.words or []):
            heard.append((w.word.strip(), float(w.start), float(w.end)))

    want = tokens(script)
    got = [tokens(h[0]) for h in heard]
    flat_got: list[str] = []
    owner: list[int] = []          # which recognised word each flat token came from
    for i, toks in enumerate(got):
        for t in toks:
            flat_got.append(t)
            owner.append(i)

    # monotonic alignment of our script tokens onto what was heard
    sm = difflib.SequenceMatcher(a=want, b=flat_got, autojunk=False)
    spoken: list[list] = [None] * len(want)          # type: ignore[list-item]
    matched = 0
    for a0, b0, size in sm.get_matching_blocks():
        for k in range(size):
            wi = a0 + k
            gi = b0 + k
            heard_i = owner[gi]
            spoken[wi] = [want[wi], heard[heard_i][1], heard[heard_i][2]]
            matched += 1

    ratio = matched / max(1, len(want))
    method = "whisper-word"
    if ratio < min_match:
        # do not ship timings we do not trust
        method = f"length-weighted (whisper match {ratio:.2f} < {min_match})"
        total = heard[-1][2] if heard else 0.0
        weights = [max(2, len(w)) for w in want]
        span = sum(weights)
        t = 0.0
        for i, w in enumerate(want):
            d = total * weights[i] / span
            spoken[i] = [w, round(t, 3), round(t + d, 3)]
            t += d
    else:
        # fill any unmatched script words by interpolating between matched neighbours
        i = 0
        while i < len(want):
            if spoken[i] is not None:
                i += 1
                continue
            j = i
            while j < len(want) and spoken[j] is None:
                j += 1
            before = spoken[i - 1][2] if i > 0 else (heard[0][1] if heard else 0.0)
            after = spoken[j][2] if j < len(want) and spoken[j] else (heard[-1][2] if heard else before + 0.3)
            n = j - i
            step = max(0.06, (after - before) / max(1, n))
            for k in range(n):
                t0 = before + k * step
                spoken[i + k] = [want[i + k], round(t0, 3), round(t0 + step, 3)]
            i = j

    return {"method": method, "match": round(ratio, 3), "model": model_size,
            "words": [[w[0], w[1], w[2]] for w in spoken if w]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("wav", type=Path)
    ap.add_argument("--text", required=True)
    ap.add_argument("--text-file", type=Path)
    ap.add_argument("--model", default="base.en")
    ap.add_argument("--min-match", type=float, default=0.75)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    script = a.text_file.read_text(encoding="utf-8") if a.text_file else a.text
    doc = align(a.wav, script, a.model, a.min_match)
    print(f"align: {doc['method']}  match {doc['match']}  words {len(doc['words'])}")
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(doc, indent=1) + "\n")
        print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
