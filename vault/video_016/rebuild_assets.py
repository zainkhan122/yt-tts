#!/usr/bin/env python3
"""rebuild_assets.py — rebuild assets.json from stock_manifest.json + images/.
No API calls (deterministic re-derivation). Re-run after adding imgNN files."""
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
STOCK = "/tmp/stock16"
IMAGES = os.path.join(BASE, "images")
ASSETS = os.path.join(BASE, "assets.json")
MANIFEST = os.path.join(BASE, "stock_manifest.json")

STOP = set("a an the of in on at to for and or with without is are be being".split())

def tags_of(query):
    t = set()
    for w in query.split():
        w = w.strip().lower()
        if w and w not in STOP:
            t.add(w)
    extra = {"tired": "exhausted", "exhausted": "tired", "dusk": "evening",
             "evening": "dusk", "dark": "night", "night": "dark",
             "burning": "flame", "flame": "fire", "burnt": "fire",
             "lying": "bed", "bed": "lying", "eyes": "face", "face": "eyes",
             "person": "people", "walking": "walk", "street": "city",
             "writing": "notes", "notes": "writing", "awake": "bed"}
    for w in list(t):
        if w in extra:
            t.add(extra[w])
    t.add("stock")
    return sorted(t)

AI_TAGS = {
    "img01": ["face", "tired", "eyes", "forehead", "hand", "ember", "exhausted"],
    "img02": ["candle", "flame", "dark", "table", "burning", "low", "fire"],
    "img03": ["figure", "walking", "road", "dusk", "sky", "alone", "evening"],
    "img04": ["desk", "tired", "sitting", "head", "window", "evening", "lamp", "exhausted"],
    "img05": ["hands", "eyes", "rubbing", "tired", "dark", "face"],
    "img06": ["clockwork", "gears", "mechanism", "machine", "brass", "glow", "clock"],
    "img07": ["bed", "lying", "awake", "night", "ceiling", "blinds", "light", "dark"],
    "img08": ["water", "deep", "underwater", "light", "dark", "surface"],
    "img09": ["train", "window", "reflection", "empty", "dusk", "interior", "city"],
    "img10": ["match", "burnt", "ember", "fire", "macro", "row"],
}

manifest = json.load(open(MANIFEST))
assets = {}
for i in range(1, 11):
    k = f"img{i:02d}"
    p = os.path.join(IMAGES, f"{k}.jpg")
    if os.path.exists(p):
        assets[k] = [p, "photo", AI_TAGS[k]]
    else:
        print(f"  (missing AI image: {k})")

seen = set()
vi = pi = 0
for q, m in manifest.items():
    for f in m["files"]:
        if f in seen:
            continue
        seen.add(f)
        p = os.path.join(STOCK, f)
        if not os.path.exists(p):
            continue
        if m["kind"] == "video":
            k = f"sv{vi:02d}"; vi += 1
            assets[k] = [p, "video", tags_of(q)]
        else:
            k = f"sp{pi:02d}"; pi += 1
            assets[k] = [p, "photo", tags_of(q)]

json.dump(assets, open(ASSETS, "w"), indent=1)
kinds = {}
for v in assets.values():
    kinds[v[1]] = kinds.get(v[1], 0) + 1
print(f"assets.json rebuilt: {len(assets)} total ({kinds})")
