#!/usr/bin/env python3
"""qa_pack.py — R26 TRAFFIC QUALITY GATE checker.
Usage: python3 tools/qa_pack.py VIDEO_DIR [primary_keyword]
Reads VIDEO_DIR/metadata.md (+ voiceover.txt if present) and enforces the
2026 pack standards: title length/keyword position, description keyword
first-sentence + length + chapters, hashtag count 3-5 + first-3 strength,
tags budget, hook length, spoken-keyword-in-first-60s (approx: first 12
sentences). Exit 1 on any FAIL; WARNs don't block."""
import os, re, sys

VD = sys.argv[1]
SHORTS = "--shorts" in sys.argv
argv = [a for a in sys.argv[1:] if a != "--shorts"]
kw = argv[1].lower() if len(argv) > 1 else None
# Shorts profile: titles <=50, desc >=15 words (Shorts descriptions are
# scanned but don't need 200), 3-5 hashtags incl #Shorts (mandatory —
# Shorts discovery leans harder on topic tags). 2026 research-backed.
TMAX = 50 if SHORTS else 60
WMIN = 15 if SHORTS else 200
md = open(f"{VD}/metadata.md", encoding="utf-8").read()
fails, warns = [], []

# --- TITLE ---
m = re.search(r"^## TITLE.*?\*\*(.+?)\*\*", md, re.S | re.M)
title = m.group(1).strip() if m else ""
if not title:
    fails.append("no TITLE section found")
L = len(title)
print(f"TITLE: {title!r} ({L} chars)")
if L > TMAX: fails.append(f"title {L} chars > {TMAX}")
if L < 15: warns.append("title very short")
if kw:
    pos = title.lower().split()[:5]
    if kw not in " ".join(pos):
        warns.append(f"keyword {kw!r} not in first 5 title words")

# --- DESCRIPTION ---
m = re.search(r"## DESCRIPTION.*?\n(.*?)(?=\n## |\Z)", md, re.S)
desc = m.group(1).strip() if m else ""
if not desc: fails.append("no DESCRIPTION section")
body = re.sub(r"#\w+", "", desc)                     # strip hashtags for word count
words = len(body.split())
first150 = re.sub(r"\s+", " ", body)[:150].strip()
print(f"DESC: {words} words | first 150: {first150[:90]!r}...")
if words < WMIN: fails.append(f"description {words} words < {WMIN}")
if kw and kw not in first150.lower():
    fails.append(f"primary keyword {kw!r} NOT in first 150 chars (search snippet)")
if not SHORTS and not re.search(r"\d{1,2}:\d{2}", desc): warns.append("no chapters/timestamps found")
if SHORTS and "#shorts" not in desc.lower(): fails.append("Shorts description missing #Shorts")

# --- HASHTAGS ---
tags_in_desc = re.findall(r"#\w+", desc)
n = len(tags_in_desc)
print(f"HASHTAGS: {n} -> {tags_in_desc[:6]}")
if n == 0: warns.append("no hashtags")
if 6 <= n <= 15: warns.append(f"{n} hashtags (6-15 = diluted; use 3-5)")
if n > 15: fails.append(f"{n} hashtags > 15 — YouTube ignores ALL")
if n and not SHORTS and not any(t.lower() in ("#infj", "#intj", "#infp", "#intp", "#psychology") for t in tags_in_desc[:3]):
    warns.append("first 3 hashtags (shown above title) lack the niche audience tag")

# --- TAGS (backend) ---
m = re.search(r"## TAGS\n(.*?)(?=\n## |\Z)", md, re.S)
if m:
    taglist = [t.strip() for t in m.group(1).strip().split(",") if t.strip()]
    budget = sum(len(t) for t in taglist) + len(taglist) - 1
    print(f"TAGS: {len(taglist)} tags, {budget}/500 chars | first: {taglist[0] if taglist else '-'}")
    if taglist and kw and kw not in taglist[0].lower():
        warns.append("exact primary keyword not first in TAGS")
    if budget > 500: fails.append(f"tags {budget} chars > 500 budget")
else:
    warns.append("no backend TAGS section")

# --- SCRIPT (optional) ---
vp = f"{VD}/voiceover.txt"
if os.path.exists(vp):
    text = re.sub(r"\s+", " ", open(vp, encoding="utf-8").read()).strip()
    sents = [p.strip() for p in re.split(r"(?<=[.!?])\s+", text) if p.strip()]
    hook = " ".join(sents[:2])
    print(f"HOOK (first 2 sents, {len(hook)} chars): {hook[:80]!r}")
    if len(hook) > 220: warns.append("hook longer than ~2 spoken breaths")
    if kw and not SHORTS and kw not in " ".join(sents[:12]).lower():
        warns.append(f"keyword {kw!r} not spoken in first ~12 sentences (60s window)")

print()
for w in warns: print("  WARN:", w)
for f in fails: print("  FAIL:", f)
if fails:
    print("❌ PACK BLOCKED — fix FAILs before upload"); sys.exit(1)
print("✅ PACK PASSES R26" + (f" ({len(warns)} warnings)" if warns else ""))
