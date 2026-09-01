#!/usr/bin/env python3
"""Script gate. Fence + uniqueness. No required intro/outro shape.
Usage: python3 tools/check_script.py EPISODE_DIR
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = Path(sys.argv[1])
text_raw = (BASE / "voiceover.txt").read_text(encoding="utf-8")
text = re.sub(r"\s+", " ", text_raw).strip()
sents = [p.strip() for p in re.split(r"(?<=[.!?])\s+", text) if p.strip()]
fails, warns = [], []
words = text.split()
print(f"sentences {len(sents)} | words {len(words)} | est min {len(words)/150:.1f}")

LEGAL = (
    "not investment advice", "not financial advice", "not financial, tax",
    "this is education, not", "education, not investment", "education, not advice",
    "education only", "not a recommendation to buy", "not tax advice",
)
low = text.lower()
for d in LEGAL:
    if d in low:
        fails.append(f"L1: legal phrase in voiceover: {d!r} — description last block only")

first = sents[0] if sents else ""
print("S1:", first[:110])
if re.match(r"^(hey|hi|hello|welcome)", first, re.I):
    fails.append("hook is a greeting")

# Company should appear early — warn, don't force sentence-one stamp
head = " ".join(sents[:4]).lower()
if len(words) > 80 and not re.search(r"[A-Z][a-zA-Z]{2,}", first):
    warns.append("S1 has no proper name — check the company is identifiable in the first seconds")

CANNED = (
    "we show the death",
    "we do not sell a pick",
    "people did not stop",
    "stay with that",
    "if you want the next collapse",
    "this is education, not",
    "every date you hear is on the public record",
)
this_canned = [c for c in CANNED if c in low]

def sibling_voiceovers():
    out = []
    ep = ROOT / "episodes"
    if not ep.exists():
        return out
    for d in ep.iterdir():
        if not d.is_dir() or d.resolve() == BASE.resolve():
            continue
        # skip shorts packs
        if "shorts" in d.parts:
            continue
        vp = d / "voiceover.txt"
        if vp.exists():
            out.append((d.name, re.sub(r"\s+", " ", vp.read_text(encoding="utf-8")).strip().lower()))
    return out

def norm_head(s, n=10):
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", s.lower()).split()[:n])

sibs = sibling_voiceovers() if BASE.parent.name == "episodes" else []
s1n = norm_head(first, 9)
for name, body in sibs:
    s0 = re.split(r"(?<=[.!?])\s+", body.strip())
    if not s0:
        continue
    if s1n and s1n == norm_head(s0[0], 9):
        fails.append(f"L2: S1 is the same shape as {name!r}")
    for c in this_canned:
        if c in body:
            fails.append(f"L2: canned line {c!r} also in {name!r} — write a closer this film earned")
            break
    # last 30 words overlap
    a = set(low.split()[-30:])
    b = set(body.split()[-30:])
    if a and b and len(a & b) / len(a | b) > 0.55:
        fails.append(f"L2: closer too similar to {name!r}")

# question closer is optional
if sents and not any("?" in s for s in sents[-8:]):
    warns.append("no question in the closer — fine if the last beat is a sourced fact")

sm = json.loads((ROOT / "reusable/speak_map.json").read_text())
print("L7 speak_map will rewrite:", [r["from"] for r in sm.get("replacements", [])])

if fails:
    print("\nFAILS:")
    for f in fails:
        print("  x", f)
    sys.exit(1)
for w in warns:
    print("  WARN:", w)
print("ALL SCRIPT CHECKS PASS")
