#!/usr/bin/env python3
"""fetch_assets.py — Video 014 step (a): fetch stock + build assets.json.
Stock lives in /tmp/stock14 (NOT the workspace) so the 128MB snapshot cap is
never exceeded. RE-RUNNABLE: skips files already on disk; rebuilds assets.json
from what actually exists (deterministic Pexels filenames).
"""
import json, os, sys
sys.path.insert(0, "/home/user/tools")
import stock_fetch

BASE = os.path.dirname(os.path.abspath(__file__))
STOCK = "/tmp/stock14"
IMAGES = os.path.join(BASE, "images")
ASSETS = os.path.join(BASE, "assets.json")
MANIFEST = os.path.join(BASE, "stock_manifest.json")
os.makedirs(STOCK, exist_ok=True)

VIDEO_QUERIES = [
    ("person apologizing sorry", 4),
    ("sad woman window", 4),
    ("warm cozy room lamp", 4),
    ("golden hour window light", 4),
    ("person thinking alone", 4),
    ("hands folded lap", 4),
    ("empty chair room", 4),
    ("tea cup window sill", 4),
    ("doorway silhouette light", 4),
    ("two people cafe talking", 4),
    ("city crowd blur", 4),
    ("person walking alone street", 4),
    ("sunset room shadow", 4),
    ("woman looking down sad", 4),
    ("candle warm light", 4),
    ("person reading alone", 4),
    ("child drawing table", 4),
    ("rain window reflection", 4),
]

PHOTO_QUERIES = [
    ("person looking down sad", 6),
    ("warm lamp cozy room", 6),
    ("empty chair window light", 6),
    ("window light portrait", 6),
    ("hands together gentle", 6),
    ("cozy kitchen morning light", 6),
    ("person alone crowd", 6),
    ("tea cup warm", 6),
    ("mirror reflection room", 6),
    ("doorway light home", 6),
    ("sunset silhouette person", 6),
    ("old letters handwriting", 6),
]

STOP = set("a an the of in on at to for and or with without is are be being".split())

def tags_of(query):
    t = set()
    for w in query.split():
        w = w.strip().lower()
        if w and w not in STOP:
            t.add(w)
    extra = {"lamp": "light", "cozy": "warm", "sorry": "apology",
             "sad": "sorrow", "window": "light", "crowd": "room"}
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
    "img01": ["table", "kitchen", "morning", "warm", "light", "quiet"],
    "img02": ["hands", "lap", "gentle", "warm", "still"],
    "img03": ["chair", "window", "empty", "golden", "room"],
    "img04": ["doorway", "figure", "small", "backlight", "warm"],
    "img05": ["tea", "cup", "window", "cozy", "steam"],
    "img06": ["face", "down", "shadow", "lamp", "warm"],
    "img07": ["flowers", "wilting", "table", "warm"],
    "img08": ["drawing", "child", "desk", "alone", "warm"],
    "img09": ["chairs", "empty", "room", "warm"],
    "img10": ["mirror", "reflection", "room", "warm", "dim"],
}

assets = {}
for i in range(1, 11):
    k = f"img{i:02d}"
    p = os.path.join(IMAGES, f"{k}.jpg")
    if os.path.exists(p):
        assets[k] = [p, "photo", AI_TAGS[k]]

qtags = {}
for q, m in manifest.items():
    for f in m["files"]:
        qtags[f] = tags_of(q)

vi = pi = 0
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
