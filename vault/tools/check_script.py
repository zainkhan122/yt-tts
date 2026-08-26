#!/usr/bin/env python3
"""check_script.py — generalized step-(a) self-check for a long-form script.
Usage: python3 tools/check_script.py VIDEO_DIR [banned_phrases.txt]
Mirrors pipeline.py parsing (split on .!? + whitespace). Verifies:
sections present+in-order, caption anchors attach to intended FIRST
occurrence, no duplicate displays, caption count 20-28, optional banned
signpost phrases (R12.1 — pass the previous video's voiceover.txt to catch
reused furniture), TTS-risky characters."""
import json, re, sys, os

BASE = sys.argv[1]
banned_file = sys.argv[2] if len(sys.argv) > 2 else None
text = open(f"{BASE}/voiceover.txt", encoding="utf-8").read()
text = re.sub(r"\s+", " ", text).strip()
sents = [p.strip() for p in re.split(r"(?<=[.!?])\s+", text) if p.strip()]
cfg = json.load(open(f"{BASE}/storyboard_config.json"))
N = len(sents)
fails = []
print(f"beats: {N} | est @2.31s/beat: {N*2.31/60:.1f} min (target 8-10)")

cur, sec_idx = 0, []
for s in sents:
    for si in range(cur, len(cfg["sections"])):
        st = cfg["sections"][si].get("start")
        if st is not None and st in s:
            cur = si
    sec_idx.append(cur)
mid_hint = None
for si, sec in enumerate(cfg["sections"]):
    first = next((i for i, s in enumerate(sents) if sec["start"] in s), None)
    if first is None:
        fails.append(f"SECTION not found: {sec['start']!r}")
    else:
        print(f"  S{si+1} '{sec['start'][:28]}' -> beat {first} ({first/N*100:.0f}%)")
        if abs(first/N - 0.5) < 0.05:
            mid_hint = first

caps = cfg["captions"]
if not (20 <= len(caps) <= 28):
    fails.append(f"caption count {len(caps)} outside 20-28")
seen = {}
for (anchor, disp, style) in caps:
    first = next((i for i, s in enumerate(sents) if anchor.lower() in s.lower()), None)
    if first is None:
        fails.append(f"ANCHOR not in script: {anchor!r}")
    else:
        if disp in seen:
            fails.append(f"duplicate caption {disp!r}")
        seen[disp] = first
order = list(seen.values())
print(f"captions: {len(caps)} | chronological: {order == sorted(order)}"
      + (f" | midpoint-ish section at beat {mid_hint}" if mid_hint else ""))

if banned_file and os.path.exists(banned_file):
    prev = open(banned_file, encoding="utf-8").read().lower()
    for line in set(l.strip().lower() for l in prev.splitlines() if len(l.strip()) > 12):
        if line and line in text.lower():
            fails.append(f"R12.1 signpost reused from previous video: {line[:60]!r}")

for i, s in enumerate(sents):
    if re.search(r"\d|[()\";:]", s):
        fails.append(f"beat {i}: risky chars for TTS: {s[:50]!r}")

print(f"hook S1: {sents[0][:70]}")
print(f"closer: {sents[-1][:70]}")
if fails:
    print("\nFAILS:")
    for f in fails: print("  x", f)
    sys.exit(1)
print("\nALL SCRIPT CHECKS PASS")
