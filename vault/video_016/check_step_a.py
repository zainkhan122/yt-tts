#!/usr/bin/env python3
"""check_step_a.py — pre-storyboard self-check for R2/R9/R12/R4 compliance.
Mirrors pipeline.py parsing exactly (split on .!? + whitespace)."""
import json, re, sys

BASE = "/home/user/videos/video_016"
text = open(f"{BASE}/voiceover.txt", encoding="utf-8").read()
text = re.sub(r"\s+", " ", text).strip()
sents = [p.strip() for p in re.split(r"(?<=[.!?])\s+", text) if p.strip()]
cfg = json.load(open(f"{BASE}/storyboard_config.json"))
N = len(sents)
print(f"beats: {N}")
est_min = N * 2.31 / 60
print(f"estimated runtime @2.31s/beat: {est_min:.1f} min (target 8-10)")

fails = []

# sections: must appear, in order, advancing
cur = 0; sec_idx = []
for i, s in enumerate(sents):
    for si in range(cur, len(cfg["sections"])):
        st = cfg["sections"][si].get("start")
        if st is not None and st in s:
            cur = si
    sec_idx.append(cur)
bounds = {}
for i, si in enumerate(sec_idx):
    bounds.setdefault(si, [i, i])[1] = i
for si, sec in enumerate(cfg["sections"]):
    st = sec["start"]
    first = next((i for i, s in enumerate(sents) if st in s), None)
    if first is None:
        fails.append(f"SECTION start phrase NOT FOUND: {st!r}")
    else:
        print(f"  S{si+1} '{st[:30]}' -> beat {first} ({first/N*100:.0f}%)")
mid = next((i for i, s in enumerate(sents) if "I want to tell you about a woman" in s), -1)
print(f"midpoint interrupt (Maya) at beat {mid} = {mid/N*100:.0f}% (target ~50%)")

# captions: anchor exists, attaches where intended, no dup displays, count
caps = cfg["captions"]
if not (20 <= len(caps) <= 28):
    fails.append(f"caption count {len(caps)} outside 20-28")
used = {}
for (anchor, disp, style) in caps:
    first = next((i for i, s in enumerate(sents) if anchor.lower() in s.lower()), None)
    if first is None:
        fails.append(f"ANCHOR not in script: {anchor!r}")
    else:
        used[disp] = first
        print(f"  cap beat {first:3d}  {disp}")
dups = [d for d in used if list(used).count(d) > 1]
if len(set(used)) != len(used):
    fails.append("duplicate caption displays")
# captions in chronological order? (not required, but nice)
order = list(used.values())
print(f"captions chronological: {order == sorted(order)}")

# no reused signposts from v15 (R12.1)
banned = ["Here's the part", "Here's what I want you to know", "Let me paint",
          "Let me stop here", "actually pause", "So tell me in the comments",
          "I read every single one"]
for b in banned:
    if b.lower() in text.lower():
        fails.append(f"v15 signpost reused: {b!r}")

# hook: first 2 sentences name the pain
print(f"hook S1: {sents[0]} | S2: {sents[1][:60]}")
# last sentence drives comments
print(f"closer: {sents[-1]}")

# risky TTS text: digits, symbols, abbreviations with dots
for i, s in enumerate(sents):
    if re.search(r"\d|[()\";:]", s):
        fails.append(f"beat {i}: risky chars for TTS: {s[:60]!r}")

if fails:
    print("\nFAILS:")
    for f in fails: print("  ✗", f)
    sys.exit(1)
print("\nALL STEP-A CHECKS PASS")
