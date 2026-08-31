#!/usr/bin/env python3
"""plan_assets.py — R27 beat-need list. Type is free; meaning is not.

Usage:
  python3 tools/plan_assets.py VIDEO_DIR           # validate existing list
  python3 tools/plan_assets.py VIDEO_DIR --stub    # write a STUB from captions
                                                 # (kinds left as "object" — YOU
                                                 #  set diagram|motion|face)

Does NOT invent diagrams or stock quotas. It only checks that every need's
`start` stem exists in voiceover.txt and that images/ files exist when
present. Storyboard tag-hit is still pipeline.py's job.
"""
import json, os, re, sys

BASE = sys.argv[1]
stub = "--stub" in sys.argv
NEED = os.path.join(BASE, "beat_needs.json")
TXT = os.path.join(BASE, "voiceover.txt")
CFG = os.path.join(BASE, "storyboard_config.json")
IM = os.path.join(BASE, "images")

text = open(TXT, encoding="utf-8").read()
text = re.sub(r"\s+", " ", text).strip()
sents = [p.strip() for p in re.split(r"(?<=[.!?])\s+", text) if p.strip()]

KINDS = {"diagram", "object", "place", "motion", "face"}

def find_stem(stem):
    low = stem.lower()
    return next((i for i, s in enumerate(sents) if low in s.lower()), None)

if stub and not os.path.exists(NEED):
    cfg = json.load(open(CFG)) if os.path.exists(CFG) else {"captions": []}
    needs = []
    for (anchor, disp, style) in cfg.get("captions", []):
        i = find_stem(anchor)
        needs.append({
            "start": anchor,
            "kind": "object",
            "tags": [w.lower() for w in re.findall(r"[A-Za-z]{3,}", anchor)[:4]],
            "note": f"caption {disp!r} @beat {i} — SET kind (diagram|object|place|motion|face)",
        })
    json.dump({"needs": needs}, open(NEED, "w"), indent=1)
    print(f"STUB wrote {len(needs)} caption-derived needs -> {NEED}")
    print("Edit kinds/tags to match the SENTENCE, then generate stills in waves of 10.")
    sys.exit(0)

if not os.path.exists(NEED):
    print("WARN: no beat_needs.json — write one before the first image wave (R27).")
    print("  python3 tools/plan_assets.py", BASE, "--stub")
    sys.exit(0)

data = json.load(open(NEED))
needs = data.get("needs") or data
fails, warns = [], []
print(f"needs: {len(needs)}")
by_kind = {}
for n in needs:
    kind = n.get("kind", "?")
    by_kind[kind] = by_kind.get(kind, 0) + 1
    if kind not in KINDS:
        warns.append(f"unknown kind {kind!r} on {n.get('start','')[:40]!r} (allowed: {sorted(KINDS)})")
    stem = n.get("start") or ""
    i = find_stem(stem)
    if i is None:
        fails.append(f"start stem not in script: {stem!r}")
    else:
        print(f"  beat {i:3d} [{kind:7s}] tags={n.get('tags', [])}  {stem[:50]!r}")
    if not n.get("tags"):
        warns.append(f"no tags on {stem[:40]!r} — storyboard cannot tag-hit")

print("by kind:", by_kind)
if os.path.isdir(IM):
    imgs = [f for f in os.listdir(IM) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    print(f"images/ on disk: {len(imgs)}  (waves of 10 until >= unique needs, max_uses=2 covers rest)")

for w in warns:
    print("  WARN:", w)
if fails:
    print("FAILS:")
    for f in fails:
        print("  x", f)
    sys.exit(1)
print("beat_needs OK")
