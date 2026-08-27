#!/usr/bin/env python3
"""check_script.py — F12 script gate for THRESHOLD.
Usage: python3 tools/check_script.py VIDEO_DIR [prev_voiceover.txt]
Digits ARE allowed (finance). Numbers should also appear in speakable form.
"""
import os, re, sys

BASE = sys.argv[1]
prev = sys.argv[2] if len(sys.argv) > 2 else None
path = f"{BASE}/voiceover.txt"
text = re.sub(r"\s+", " ", open(path, encoding="utf-8").read()).strip()
sents = [p.strip() for p in re.split(r"(?<=[.!?])\s+", text) if p.strip()]
N = len(sents)
fails = []
print(f"beats: {N} | est @2.3s: {N*2.3/60:.1f} min (target 8-11)")

if N < 80: fails.append(f"too short ({N} beats) for 8 min")
if N > 160: fails.append(f"too long ({N} beats)")

hook = " ".join(sents[:2])
print(f"HOOK: {hook[:120]}")
if len(sents) < 2: fails.append("need ≥2 sentences")
if re.match(r"^(hey|hi|hello|welcome|what's up)", sents[0], re.I):
    fails.append("hook is a greeting")
if "not financial advice" not in " ".join(sents[:4]).lower():
    fails.append("F28 spoken disclaimer not in first 4 sentences")

joined12 = " ".join(sents[:12]).lower()
if not re.search(r"\d|thousand|hundred|percent|dollar", joined12):
    fails.append("no number spoken in first ~60s")

closer = sents[-1]
print(f"CLOSER: {closer[:120]}")
if "?" not in closer:
    fails.append("closer is not a question (F12 comment-driving)")

if prev and os.path.exists(prev):
    old = open(prev, encoding="utf-8").read().lower()
    furniture = [
        "here's the truth nobody told you",
        "here's what's actually happening",
        "i'll see you in the next one",
        "let's get into it",
    ]
    for f in furniture:
        if f in text.lower() and f in old:
            fails.append(f"F12 signpost reused: {f}")

risky = []
for i, s in enumerate(sents):
    if re.search(r"[;{}<>]|https?://", s):
        risky.append(i)
if risky:
    fails.append(f"TTS-risky punctuation in beats {risky[:8]}")

print(f"hook S1: {sents[0][:70]}")
if fails:
    print("\nFAILS:")
    for f in fails: print("  x", f)
    sys.exit(1)
print("\nALL SCRIPT CHECKS PASS")
