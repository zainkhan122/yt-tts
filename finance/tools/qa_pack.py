#!/usr/bin/env python3
"""qa_pack.py — F26 traffic quality gate.
Usage: python3 tools/qa_pack.py VIDEO_DIR [primary_keyword] [--shorts]
"""
import os, re, sys

args = [a for a in sys.argv[1:] if a != "--shorts"]
SHORTS = "--shorts" in sys.argv
VD = args[0]
kw = args[1].lower() if len(args) > 1 else None
TMAX = 50 if SHORTS else 60
WMIN = 15 if SHORTS else 200
NICHE = ("#personalfinance", "#networth", "#moneyrules", "#threshold",
         "#personalfinance", "#inflation", "#investing")

md = open(f"{VD}/metadata.md", encoding="utf-8").read()
fails, warns = [], []

m = re.search(r"^## TITLE.*?\*\*(.+?)\*\*", md, re.S | re.M)
title = m.group(1).strip() if m else ""
if not title:
    fails.append("no TITLE section found")
L = len(title)
print(f"TITLE: {title!r} ({L} chars)")
if L > TMAX: fails.append(f"title {L} chars > {TMAX}")
if L < 15: warns.append("title very short")
if kw:
    first5 = " ".join(title.lower().split()[:5])
    if kw not in first5 and kw not in title.lower():
        warns.append(f"keyword {kw!r} not in first 5 title words")

m = re.search(r"## DESCRIPTION.*?\n(.*?)(?=\n## |\Z)", md, re.S)
desc = m.group(1).strip() if m else ""
if not desc: fails.append("no DESCRIPTION section")
body = re.sub(r"#\w+", "", desc)
words = len(body.split())
first150 = re.sub(r"\s+", " ", body)[:150].strip()
print(f"DESC: {words} words | first 150: {first150[:90]!r}...")
if words < WMIN: fails.append(f"description {words} words < {WMIN}")
if kw and kw not in first150.lower():
    fails.append(f"primary keyword {kw!r} NOT in first 150 chars")
if not SHORTS and not re.search(r"\d{1,2}:\d{2}", desc):
    warns.append("no chapters/timestamps found")
if SHORTS and "#shorts" not in desc.lower():
    fails.append("Shorts description missing #Shorts")
if not SHORTS and "not financial advice" not in desc.lower() and "not financial, tax" not in desc.lower():
    fails.append("F28 disclaimer missing from description")

tags_in_desc = re.findall(r"#\w+", desc)
n = len(tags_in_desc)
print(f"HASHTAGS: {n} -> {tags_in_desc[:6]}")
if n == 0: warns.append("no hashtags")
if 6 <= n <= 15: warns.append(f"{n} hashtags (use 3-5)")
if n > 15: fails.append(f"{n} hashtags > 15 — YouTube ignores ALL")
if n and not SHORTS:
    first3 = [t.lower() for t in tags_in_desc[:3]]
    if not any(t in NICHE for t in first3):
        warns.append("first 3 hashtags lack niche tag (#personalfinance etc.)")

m = re.search(r"## TAGS\n(.*?)(?=\n## |\Z)", md, re.S)
if m:
    taglist = [t.strip() for t in m.group(1).strip().split(",") if t.strip()]
    budget = sum(len(t) for t in taglist) + max(len(taglist) - 1, 0)
    print(f"TAGS: {len(taglist)} tags, {budget}/500 | first: {taglist[0] if taglist else '-'}")
    if taglist and kw and kw not in taglist[0].lower():
        warns.append("exact primary keyword not first in TAGS")
    if budget > 500: fails.append(f"tags {budget} chars > 500")
else:
    warns.append("no backend TAGS section")

vp = f"{VD}/voiceover.txt"
if os.path.exists(vp):
    text = re.sub(r"\s+", " ", open(vp, encoding="utf-8").read()).strip()
    sents = [p.strip() for p in re.split(r"(?<=[.!?])\s+", text) if p.strip()]
    hook = " ".join(sents[:2])
    print(f"HOOK ({len(hook)} chars): {hook[:80]!r}")
    if len(hook) > 280: warns.append("hook longer than ~2 spoken breaths")
    if kw and not SHORTS and kw not in " ".join(sents[:12]).lower():
        warns.append(f"keyword {kw!r} not spoken in first ~12 sentences")

print()
for w in warns: print("  WARN:", w)
for f in fails: print("  FAIL:", f)
if fails:
    print("❌ PACK BLOCKED"); sys.exit(1)
print("✅ PACK PASSES F26" + (f" ({len(warns)} warnings)" if warns else ""))
