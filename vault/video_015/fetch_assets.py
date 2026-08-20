#!/usr/bin/env python3
"""fetch_assets.py — Video 015 step (a): fetch stock + build assets.json.
Stock lives in /tmp/stock15 (NOT the workspace) so the 128MB snapshot cap is
never exceeded. RE-RUNNABLE: skips files already on disk; rebuilds assets.json
from what actually exists (deterministic Pexels filenames). Dedups by filename.
"""
import json, os, sys
sys.path.insert(0, "/home/user/tools")
import stock_fetch

BASE = os.path.dirname(os.path.abspath(__file__))
STOCK = "/tmp/stock15"
IMAGES = os.path.join(BASE, "images")
ASSETS = os.path.join(BASE, "assets.json")
MANIFEST = os.path.join(BASE, "stock_manifest.json")
os.makedirs(STOCK, exist_ok=True)

VIDEO_QUERIES = [
    ("rain window drops", 4),
    ("person alone rain", 4),
    ("lone figure walking away", 4),
    ("dark room window light", 4),
    ("storm clouds sky", 4),
    ("person sitting floor alone", 4),
    ("hand reaching out", 4),
    ("wet city street night", 4),
    ("phone on table dark", 4),
    ("clouds timelapse grey", 4),
    ("person looking out window", 4),
    ("door closing dark", 4),
    ("umbrella rain street", 4),
    ("empty hallway light", 4),
    ("candle wind flicker", 4),
    ("rain puddle reflection", 4),
]

PHOTO_QUERIES = [
    ("rain window drops", 6),
    ("person alone window light", 6),
    ("empty hallway light", 6),
    ("wet street reflection night", 6),
    ("storm clouds grey", 6),
    ("hand reaching light", 6),
    ("person sitting floor alone", 6),
    ("umbrella silhouette rain", 6),
    ("dark room light blind", 6),
    ("door half open light", 6),
    ("rain puddle reflection", 6),
    ("lone figure road", 6),
]

STOP = set("a an the of in on at to for and or with without is are be being".split())

def tags_of(query):
    t = set()
    for w in query.split():
        w = w.strip().lower()
        if w and w not in STOP:
            t.add(w)
    extra = {"rain": "storm", "alone": "lonely", "grey": "gray",
             "wet": "rain", "night": "dark", "hand": "reach",
             "window": "light", "door": "wall"}
    for w in list(t):
        if w in extra:
            t.add(extra[w])
    t.add("stock")
    return sorted(t)

manifest = {}
def names_only(saved):
    return [s[0] if isinstance(s, tuple) else s for s in saved]

for q, n in VIDEO_QUERIES:
    print(f"\n== VIDEO: {q} ==")
    saved = stock_fetch.pexels_videos(q, n, STOCK)
    manifest[q] = {"kind": "video", "files": names_only(saved)}

for q, n in PHOTO_QUERIES:
    print(f"\n== PHOTO: {q} ==")
    saved = stock_fetch.pexels_photos(q, n, STOCK)
    manifest[q] = {"kind": "photo", "files": names_only(saved)}

json.dump(manifest, open(MANIFEST, "w"), indent=1)

AI_TAGS = {
    "img01": ["window", "rain", "face", "reflection", "grey", "alone"],
    "img02": ["umbrella", "rain", "street", "figure", "grey", "wet"],
    "img03": ["door", "locked", "wall", "brick", "storm"],
    "img04": ["floor", "sitting", "wall", "alone", "grey", "knees"],
    "img05": ["hands", "reach", "pull", "grey", "drama"],
    "img06": ["figure", "walking", "road", "wet", "behind", "grey"],
    "img07": ["phone", "table", "dark", "blinds", "grey"],
    "img08": ["mirror", "cracked", "face", "blur", "grey"],
    "img09": ["window", "light", "warm", "street", "rain", "dark"],
    "img10": ["ripples", "water", "rain", "abstract", "dark"],
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
        if f in seen:      # dedup: same clip returned by two queries
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
print(f"dedup removed {sum(len(v['files']) for v in manifest.values()) - len(seen)} duplicate fetches")
