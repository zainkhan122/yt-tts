#!/usr/bin/env python3
"""fetch_assets.py — Video 017: fetch stock + build assets.json.
Stock lives in /tmp/stock17. Theme: helper persona / listener. Warm interior.
"""
import json, os, sys
sys.path.insert(0, "/home/user/tools")
import stock_fetch

BASE = os.path.dirname(os.path.abspath(__file__))
STOCK = "/tmp/stock17"
IMAGES = os.path.join(BASE, "images")
ASSETS = os.path.join(BASE, "assets.json")
MANIFEST = os.path.join(BASE, "stock_manifest.json")
os.makedirs(STOCK, exist_ok=True)

VIDEO_QUERIES = [
    ("person listening conversation cafe", 4),
    ("empty armchair living room", 4),
    ("phone on table night", 4),
    ("coffee cup table cafe", 4),
    ("rain window night city", 4),
    ("hands holding comfort", 4),
    ("empty kitchen chair table", 4),
    ("desk lamp dark room", 4),
    ("person talking on phone evening", 4),
    ("waiting room chairs", 4),
    ("woman sitting alone cafe window", 4),
    ("group conversation party", 4),
    ("old letters on desk", 4),
    ("mask still life", 4),
    ("train window night", 4),
    ("person staring out window interior", 4),
]

PHOTO_QUERIES = [
    ("woman listening face", 6),
    ("empty armchair", 6),
    ("smartphone nightstand", 6),
    ("two coffee cups table", 6),
    ("theater mask still life", 6),
    ("rain window city night", 6),
    ("holding hands close up", 6),
    ("empty dining chair", 6),
    ("leather journal desk lamp", 6),
    ("cafe interior warm light", 6),
    ("person on phone silhouette", 6),
    ("waiting room empty chairs", 6),
    ("stacked letters paper", 6),
    ("vintage rotary phone", 6),
    ("wooden table lamp interior", 6),
    ("friends talking cafe", 6),
    ("lonely figure window", 6),
    ("notebook pen dark table", 6),
]

STOP = set("a an the of in on at to for and or with without is are be being".split())

def tags_of(query):
    t = set()
    for w in query.split():
        w = w.strip().lower()
        if w and w not in STOP:
            t.add(w)
    extra = {
        "listening": "listener", "listener": "listening", "cafe": "coffee",
        "coffee": "cafe", "phone": "call", "call": "phone", "chair": "armchair",
        "armchair": "chair", "window": "rain", "rain": "window", "hands": "holding",
        "letters": "journal", "journal": "letters", "night": "evening",
        "evening": "night", "person": "people", "mask": "persona",
        "waiting": "chairs", "conversation": "talking", "talking": "conversation",
    }
    for w in list(t):
        if w in extra:
            t.add(extra[w])
    t.add("stock")
    return sorted(t)

manifest = {}
def names_only(saved):
    return [s[0] if isinstance(s, tuple) else s for s in saved]

for q, n in VIDEO_QUERIES:
    print(f"\n== VIDEO: {q} ==", flush=True)
    saved = stock_fetch.pexels_videos(q, n, STOCK)
    manifest[q] = {"kind": "video", "files": names_only(saved)}

for q, n in PHOTO_QUERIES:
    print(f"\n== PHOTO: {q} ==", flush=True)
    saved = stock_fetch.pexels_photos(q, n, STOCK)
    manifest[q] = {"kind": "photo", "files": names_only(saved)}

json.dump(manifest, open(MANIFEST, "w"), indent=1)

AI_TAGS = {
    "img01": ["face", "listening", "eyes", "woman", "lamp", "listener", "calm"],
    "img02": ["armchair", "waiting", "chairs", "empty", "room", "interior"],
    "img03": ["phone", "contacts", "night", "table", "call", "empty"],
    "img04": ["coffee", "cups", "cafe", "table", "two", "gift"],
    "img05": ["mask", "persona", "ceramic", "table", "listener", "face"],
    "img06": ["window", "rain", "city", "night", "reflection", "urban"],
    "img07": ["hands", "holding", "comfort", "listening", "care"],
    "img08": ["valve", "pipe", "one-way", "brass", "abstract", "metal"],
    "img09": ["chair", "kitchen", "family", "empty", "assigned", "childhood"],
    "img10": ["journal", "letters", "desk", "closed", "known", "writing"],
}

assets = {}
for i in range(1, 11):
    k = f"img{i:02d}"
    p = os.path.join(IMAGES, f"{k}.jpg")
    if os.path.exists(p):
        assets[k] = [p, "photo", AI_TAGS[k]]

qtags = {}
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
        qtags[f] = tags_of(q)
        if m["kind"] == "video":
            k = f"sv{vi:02d}"; vi += 1
            assets[k] = [p, "video", qtags[f]]
        else:
            k = f"sp{pi:02d}"; pi += 1
            assets[k] = [p, "photo", qtags[f]]

json.dump(assets, open(ASSETS, "w"), indent=1)
kinds = {}
for v in assets.values():
    kinds[v[1]] = kinds.get(v[1], 0) + 1
print(f"\n=== assets.json built: {len(assets)} total ({kinds}) ===")
open(os.path.join(BASE, ".fetch_done"), "w").write("done")
