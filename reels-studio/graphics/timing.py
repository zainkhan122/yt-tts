"""Phrase chunker: word timings -> phrases. Deterministic, no LLM.

Input words: [[text, t_start, t_end], ...] (seconds, from the TTS aligner).
Output phrases: [{"i", "t0", "t1", "text", "words": [[text, t0, t1], ...]}]
"""
from __future__ import annotations

PUNCT_BREAK = (",", ".", "?", "!", ";", ":")


def chunk_phrases(words: list[list], *, max_s: float = 4.0, min_s: float = 1.2,
                  gap_s: float = 0.40) -> list[dict]:
    if not words:
        return []
    phrases: list[list[list]] = []
    cur: list[list] = []
    for idx, w in enumerate(words):
        if cur:
            prev = cur[-1]
            gap = w[1] - prev[2]
            span = w[2] - cur[0][1]
            if gap >= gap_s or span > max_s:
                phrases.append(cur)
                cur = []
        cur.append(w)
        dur = cur[-1][2] - cur[0][1]
        ends_clause = w[0].rstrip('"\')').endswith(PUNCT_BREAK)
        if ends_clause and dur >= min_s:
            phrases.append(cur)
            cur = []
    if cur:
        phrases.append(cur)

    # A trailing fragment shorter than min_s joins the previous phrase, unless that would exceed max_s.
    if len(phrases) > 1:
        last, prev = phrases[-1], phrases[-2]
        if last[-1][2] - last[0][1] < min_s and last[-1][2] - prev[0][1] <= max_s + min_s:
            phrases[-2] = prev + last
            phrases.pop()

    out = []
    for i, p in enumerate(phrases):
        out.append({
            "i": i,
            "t0": round(p[0][1], 3),
            "t1": round(p[-1][2], 3),
            "text": " ".join(w[0] for w in p),
            "words": p,
        })
    return out


def close_gaps(phrases: list[dict], total_s: float) -> list[dict]:
    """Extend each phrase to the next one's start so the timeline has no holes. First starts at 0,
    last ends at total_s. Word timings are kept as they are; only the visual window grows."""
    out = [dict(p) for p in phrases]
    for i, p in enumerate(out):
        p["t0"] = 0.0 if i == 0 else out[i - 1]["t1"]
        p["t1"] = out[i + 1]["t0"] if i + 1 < len(out) else round(total_s, 3)
    return out
