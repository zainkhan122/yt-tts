#!/usr/bin/env python3
"""
Align `hyperframes transcribe` word timestamps to the canonical display script
and snap them to the real speech segments found in the voiceover waveform.

Why: whisper's word boundaries drift around pauses (a sentence-final word can
be stamped inside the following silence). Speech/silence segmentation of the
actual audio is exact, so we use it to clamp words to where speech really is:
  * a word whose start falls in a silence gap starts when speech resumes;
  * a word whose end falls in a gap ends when speech stops;
  * a word lying entirely inside a gap belongs to the left phrase if it ends a
    sentence (punctuation), otherwise to the right phrase.
Display text comes from the script (casing, "MP4", "AI", numerals), timing from
whisper + the waveform. Output: assets/captions.json (words + karaoke groups).
"""
import json
import re
import sys

import numpy as np
import soundfile as sf

DISPLAY = (
    "Stop editing videos by hand. HyperFrames turns plain HTML into real video. "
    "Write the code. Hit render. Get an MP4. Over 57,000 stars on GitHub. "
    "Almost 400 ready-made blocks. Captions, charts, transitions. "
    "And your AI agent can write it all for you. One template. 100 videos. "
    "Follow for more tools like this."
).split()


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def speech_gaps(wav, min_gap=0.09, floor_db=38):
    x, sr = sf.read(wav)
    if x.ndim > 1:
        x = x.mean(axis=1)
    hop = int(0.01 * sr)
    n = len(x) // hop
    rms = np.sqrt(np.mean(x[: n * hop].reshape(n, hop) ** 2, axis=1))
    db = 20 * np.log10(rms + 1e-9)
    speech = db > db.max() - floor_db
    gaps, i = [], 0
    while i < n:
        if not speech[i]:
            j = i
            while j < n and not speech[j]:
                j += 1
            if (j - i) / 100 >= min_gap and i > 0 and j < n:
                gaps.append((i / 100, j / 100))
            i = j
        else:
            i += 1
    return gaps, n / 100


def main(transcript, wav, out):
    raw = json.load(open(transcript))
    # merge spelled-out acronyms whisper split ("A," + "I." -> "AI")
    merged = []
    for w in raw:
        t = w["text"].strip()
        if merged and norm(merged[-1]["text"]) == "a" and norm(t) == "i":
            merged[-1] = {"text": "AI", "start": merged[-1]["start"], "end": w["end"]}
            continue
        merged.append({"text": t, "start": float(w["start"]), "end": float(w["end"])})
    if len(merged) != len(DISPLAY):
        sys.exit(f"token count mismatch: transcript {len(merged)} vs display {len(DISPLAY)}")

    gaps, total = speech_gaps(wav)
    words = []
    for disp, w in zip(DISPLAY, merged):
        s, e = w["start"], w["end"]
        for g0, g1 in gaps:
            if g0 <= s and e <= g1:  # entirely inside a silence
                if re.search(r"[.,!?]$", disp):
                    e, s = g0, min(s, g0 - 0.12)
                else:
                    s, e = g1, max(e, g1 + 0.12)
            if g0 < s < g1:
                s = g1
            if g0 < e < g1:
                e = g0
        words.append({"text": disp, "start": round(s, 3), "end": round(max(e, s + 0.06), 3)})
    # monotonic, non-overlapping
    for a, b in zip(words, words[1:]):
        if b["start"] < a["start"] + 0.04:
            b["start"] = round(a["start"] + 0.04, 3)
        a["end"] = round(min(a["end"], b["start"]), 3)

    # karaoke groups: <= 3 words / 18 chars, break after punctuation
    groups, cur = [], []
    for i, w in enumerate(words):
        cur.append(i)
        text = " ".join(words[k]["text"] for k in cur)
        nxt = words[i + 1] if i + 1 < len(words) else None
        gap = (nxt["start"] - w["end"]) if nxt else 9
        if re.search(r"[.,!?]$", w["text"]) or len(cur) == 3 or len(text) > 14 or gap > 0.25:
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)

    # rebalance: a group too short to read either merges into the previous
    # group (if it fits on a line) or steals the previous group's last word
    def chars(g):
        return len(" ".join(words[k]["text"] for k in g))

    def dur(g):
        return words[g[-1]]["end"] - words[g[0]]["start"]

    i = 1
    while i < len(groups):
        g, prev = groups[i], groups[i - 1]
        open_prev = not re.search(r"[.,!?]$", words[prev[-1]]["text"])
        if dur(g) < 0.42 and open_prev:
            if chars(prev + g) <= 18:
                groups[i - 1] = prev + g
                groups.pop(i)
                continue
            if len(prev) > 1:
                groups[i - 1], groups[i] = prev[:-1], [prev[-1]] + g
        i += 1

    out_groups = [
        {"start": words[g[0]]["start"], "end": words[g[-1]]["end"], "words": g} for g in groups
    ]
    json.dump({"words": words, "groups": out_groups, "gaps": gaps, "duration": total},
              open(out, "w"), indent=1)
    for g in out_groups:
        print(f'{g["start"]:6.2f}-{g["end"]:6.2f}  ' + " ".join(words[k]["text"] for k in g["words"]))


if __name__ == "__main__":
    main(*(sys.argv[1:4] if len(sys.argv) > 3 else
           ("assets/audio/transcript.json", "assets/audio/vo.wav", "assets/captions.json")))
