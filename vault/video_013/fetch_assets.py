#!/usr/bin/env python3
"""fetch_assets.py — Video 013 step (a): fetch stock + build assets.json.
RE-RUNNABLE: skips files already downloaded; rebuilds assets.json from what
actually exists on disk (so a snapshot truncation is recovered by re-running).
"""
import json, os, sys
sys.path.insert(0, "/home/user/tools")
import stock_fetch

BASE = os.path.dirname(os.path.abspath(__file__))
STOCK = "/home/user/stock13"
IMAGES = os.path.join(BASE, "images")
ASSETS = os.path.join(BASE, "assets.json")
MANIFEST = os.path.join(BASE, "stock_manifest.json")
os.makedirs(STOCK, exist_ok=True)

# (query, count) for Pexels VIDEOS
VIDEO_QUERIES = [
    ("misty forest dawn", 4),
    ("sunrise timelapse", 3),
    ("clock time close up", 3),
    ("person silhouette sunrise", 4),
    ("old books library", 3),
    ("calm lake ripples", 3),
    ("city timelapse dawn", 4),
    ("person looking window thinking", 4),
    ("stars night sky timelapse", 3),
    ("candle flame dark", 3),
    ("child looking sky", 3),
    ("walking alone road mist", 3),
    ("elderly hands close up", 3),
    ("clouds timelapse sky", 3),
    ("hourglass sand time", 2),
    ("deep forest fog", 3),
]

PHOTO_QUERIES = [
    ("foggy mountain dawn", 6),
    ("old pocket watch", 5),
    ("antique books candle", 6),
    ("silhouette sunrise hill", 5),
    ("quiet empty room window light", 6),
    ("ancient tree mist", 5),
    ("calm lake mist morning", 6),
    ("stars night sky", 5),
    ("person profile window light", 5),
    ("chess pieces shadow", 5),
    ("ripples water abstract", 5),
]

STOP = set("a an the of in on at to for and or with without is are be being".split())

def tags_of(query):
    t = set()
    for w in query.split():
        w = w.strip().lower()
        if w and w not in STOP:
            t.add(w)
    # enrich with synonyms so tag-matching hits script keywords
    extra = {"timelapse": "time", "clock": "time", "watch": "time",
             "forest": "woods", "mist": "fog", "hands": "old",
             "silhouette": "figure", "library": "books"}
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
    print(f"   saved {len(saved)}")

for q, n in PHOTO_QUERIES:
    print(f"\n== PHOTO: {q} ==")
    saved = stock_fetch.pexels_photos(q, n, STOCK)
    manifest[q] = {"kind": "photo", "files": names_only(saved)}
    print(f"   saved {len(saved)}")

json.dump(manifest, open(MANIFEST, "w"), indent=1)

AI_TAGS = {
    "img01": ["child", "dawn", "field", "mist", "horizon", "alone", "watching"],
    "img02": ["watch", "time", "ancient", "frost", "old", "dawn"],
    "img03": ["tree", "roots", "ancient", "dawn", "mist", "old"],
    "img04": ["face", "eyes", "calm", "wisdom", "window", "light"],
    "img05": ["candle", "light", "dark", "quiet", "dawn"],
    "img06": ["path", "mist", "forest", "journey", "dawn"],
    "img07": ["hourglass", "sand", "time", "dawn", "window"],
    "img08": ["figure", "hill", "city", "watcher", "dawn", "silhouette"],
    "img09": ["books", "lamp", "wisdom", "room", "dawn", "old"],
    "img10": ["ripples", "water", "pattern", "abstract", "dawn", "dark"],
}

assets = {}
for i in range(1, 11):
    k = f"img{i:02d}"
    p = os.path.join(IMAGES, f"{k}.jpg")
    if os.path.exists(p):
        assets[k] = [p, "photo", AI_TAGS[k]]

# stock: map actual files on disk back to their query for tags
qtags = {}
for q, m in manifest.items():
    for f in m["files"]:
        qtags[f] = tags_of(q)

vi = 0
pi = 0
missing = []
for q, m in manifest.items():
    for f in m["files"]:
        p = os.path.join(STOCK, f)
        if not os.path.exists(p):
            missing.append(f)
            continue
        if m["kind"] == "video":
            k = f"sv{vi:02d}"; vi += 1
            assets[k] = [p, "video", qtags.get(f, ["stock"])]
        else:
            k = f"sp{pi:02d}"; pi += 1
            assets[k] = [p, "photo", qtags.get(f, ["stock"])]

json.dump(assets, open(ASSETS, "w"), indent=1)
kinds = {}
for v in assets.values():
    kinds[v[1]] = kinds.get(v[1], 0) + 1
print(f"\n=== assets.json built: {len(assets)} total ({kinds}) ===")
print(f"missing on disk (re-run to refetch): {len(missing)}")
for m in missing[:12]:
    print("   -", m)
