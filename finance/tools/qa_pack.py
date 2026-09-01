#!/usr/bin/env python3
"""qa_pack.py — packaging gate (L3 L6 L8).
Usage: python3 tools/qa_pack.py VIDEO_DIR [keyword] [--shorts]
"""
import re, sys
from pathlib import Path

args = [a for a in sys.argv[1:] if a != "--shorts"]
SHORTS = "--shorts" in sys.argv
VD = Path(args[0])
kw = args[1].lower() if len(args) > 1 else None
TMAX = 50 if SHORTS else 60
WMIN = 15 if SHORTS else 200

LEGAL = (
    "not investment advice",
    "not financial advice",
    "not financial, tax",
    "this is education, not",
    "education, not investment",
    "education, not advice",
    "education only",
    "not a recommendation to buy",
)

md = (VD / "metadata.md").read_text(encoding="utf-8")
fails, warns = [], []

m = re.search(r"^## TITLE.*?\*\*(.+?)\*\*", md, re.S | re.M)
title = m.group(1).strip() if m else ""
if not title:
    fails.append("no TITLE")
print(f"TITLE: {title!r} ({len(title)} chars)")
if len(title) > TMAX:
    fails.append(f"title {len(title)} > {TMAX}")
if kw:
    first5 = " ".join(title.lower().split()[:5])
    if kw not in first5 and kw not in title.lower():
        warns.append(f"keyword {kw!r} not in first 5 title words")

tm = re.search(r"## THUMBNAIL.*?(\*\*(.+?)\*\*|:\s*\*\*(.+?)\*\*)", md, re.S)
thumb_line = ""
if tm:
    thumb_line = (tm.group(2) or tm.group(3) or "").strip()
if not thumb_line:
    m2 = re.search(r"## THUMBNAIL.*?\*\*([^*]+)\*\*", md, re.S)
    if m2:
        thumb_line = m2.group(1).strip()
if thumb_line and not SHORTS:
    tl = thumb_line.lower().strip()
    if tl == title.lower().strip():
        fails.append("P9 title equals thumb line")
    if f"({tl})" in title.lower() or f"[{tl}]" in title.lower():
        fails.append(f"P9 thumb line {thumb_line!r} stuffed into the title")

m = re.search(r"## DESCRIPTION.*?\n(.*?)(?=\n## |\Z)", md, re.S)
desc = m.group(1).strip() if m else ""
if not desc:
    fails.append("no DESCRIPTION")
body = re.sub(r"#\w+", "", desc)
words = len(body.split())
first150 = re.sub(r"\s+", " ", body)[:150].strip()
print(f"DESC: {words} words | first 150: {first150[:90]!r}...")
if words < WMIN:
    fails.append(f"description {words} < {WMIN}")
if kw and kw not in first150.lower():
    fails.append(f"primary keyword {kw!r} NOT in first 150 chars")
# longs: first sentence of description must not clone a sibling
if not SHORTS:
    ROOT = VD.resolve()
    while ROOT.name != "episodes" and ROOT.parent != ROOT:
        ROOT = ROOT.parent
    me_first = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", body))[0].lower()[:80]
    for d in (VD.resolve().parent).iterdir() if VD.parent.name == "episodes" else []:
        if not d.is_dir() or d.resolve() == VD.resolve():
            continue
        mp = d / "metadata.md"
        if not mp.exists():
            continue
        m2 = re.search(r"## DESCRIPTION.*?\n(.*?)(?=\n## |\Z)", mp.read_text(encoding="utf-8"), re.S)
        if not m2:
            continue
        sib = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", m2.group(1)))[0].lower()[:80]
        if me_first and sib and me_first == sib:
            fails.append(f"description S1 clones {d.name!r}")
if not SHORTS and not re.search(r"\d{1,2}:\d{2}", desc):
    warns.append("no chapters")
if SHORTS and "#shorts" not in desc.lower():
    fails.append("L6 Shorts description missing #Shorts")

# L8 disclaimer last — longs only. Shorts must have ZERO legal copy.
low = desc.lower()
has_disc = any(x in low for x in ("not financial advice", "not financial, tax", "not investment advice"))
if SHORTS:
    for d in LEGAL:
        if d in low:
            fails.append(f"L1 Shorts description contains legal phrase {d!r}")
elif not has_disc:
    fails.append("L8 disclaimer missing from description")
if has_disc and not SHORTS:
    if "not investment advice" not in desc[-500:].lower() and "not financial" not in desc[-500:].lower():
        fails.append("L8 disclaimer must be the LAST block of the description")
# legal must not appear in the first 400 chars of a long description (hook tax)
if has_disc and not SHORTS and any(x in first150.lower() for x in LEGAL):
    fails.append("L8 disclaimer leaked into the first 150 chars")
if not SHORTS and "subscribe" not in low and "@thepublicrecord" not in low:
    warns.append("L8 no subscribe / @thepublicrecord in description")

# pinned comment: no legal
pm = re.search(r"## PINNED COMMENT\n(.*?)(?=\n## |\Z)", md, re.S)
if pm:
    pin = pm.group(1).strip().lower()
    for d in LEGAL:
        if d in pin:
            fails.append(f"L1 pinned comment contains legal phrase {d!r}")

tags_in_desc = re.findall(r"#\w+", desc)
print(f"HASHTAGS: {len(tags_in_desc)} -> {tags_in_desc[:6]}")
if not tags_in_desc:
    warns.append("no hashtags")
if len(tags_in_desc) > 5 and not SHORTS:
    warns.append(f"{len(tags_in_desc)} hashtags (use 3–5)")

m = re.search(r"## TAGS\n(.*?)(?=\n## |\Z)", md, re.S)
if m:
    taglist = [t.strip() for t in m.group(1).strip().split(",") if t.strip()]
    budget = sum(len(t) for t in taglist) + max(len(taglist) - 1, 0)
    print(f"TAGS: {len(taglist)} tags, {budget}/500 | first: {taglist[0] if taglist else '-'}")
    if taglist and kw and kw not in taglist[0].lower():
        warns.append("exact primary keyword not first in TAGS")
    if budget > 500:
        fails.append(f"tags {budget} > 500")
else:
    warns.append("no TAGS section")

vp = VD / "voiceover.txt"
if vp.exists():
    text = re.sub(r"\s+", " ", vp.read_text(encoding="utf-8")).strip()
    sents = [p.strip() for p in re.split(r"(?<=[.!?])\s+", text) if p.strip()]
    hook = " ".join(sents[:2])
    print(f"HOOK ({len(hook)} chars): {hook[:80]!r}")
    if kw and not SHORTS and kw not in " ".join(sents[:8]).lower():
        warns.append(f"keyword {kw!r} not spoken early")
    tlow = text.lower()
    for d in LEGAL:
        if d in tlow:
            fails.append(f"L1 legal phrase in voiceover: {d!r}")

print()
for w in warns:
    print("  WARN:", w)
for f in fails:
    print("  FAIL:", f)
if fails:
    print("❌ PACK BLOCKED")
    sys.exit(1)
print("✅ PACK PASSES" + (f" ({len(warns)} warnings)" if warns else ""))
