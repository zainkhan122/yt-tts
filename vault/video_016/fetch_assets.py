#!/usr/bin/env python3
"""fetch_assets.py — Video 016 step (a): fetch stock + build assets.json.
Stock lives in /tmp/stock16 (NOT the workspace) so the 128MB snapshot cap is
never exceeded. RE-RUNNABLE: skips files already on disk; rebuilds assets.json
from what actually exists (deterministic Pexels filenames). Dedups by filename.
Theme: cognitive drain / ember-dusk. Landscape (long-form).
"""
import json, os, sys
sys.path.insert(0, "/home/user/tools")
import stock_fetch

BASE = os.path.dirname(os.path.abspath(__file__))
STOCK = "/tmp/stock16"
IMAGES = os.path.join(BASE, "images")
ASSETS = os.path.join(BASE, "assets.json")
MANIFEST = os.path.join(BASE, "stock_manifest.json")
os.makedirs(STOCK, exist_ok=True)

VIDEO_QUERIES = [
    ("tired person eyes closed", 4),
    ("person walking road dusk", 4),
    ("candle flame dark", 4),
    ("city street dusk lights", 4),
    ("person lying bed awake", 4),
    ("empty office evening", 4),
    ("sunset silhouette field", 4),
    ("person rubbing eyes tired", 4),
    ("hands typing laptop night", 4),
    ("night sky stars timelapse", 4),
    ("train window reflection", 4),
    ("match burning close up", 4),
    ("hourglass sand dark", 4),
    ("lamp light dark room", 4),
    ("person staring window evening", 4),
    ("water surface dark ripples", 4),
]

PHOTO_QUERIES = [
    ("exhausted woman face", 6),
    ("tired man eyes closed", 6),
    ("candle burning dark", 6),
    ("burnt match stick", 6),
    ("hourglass dark background", 6),
    ("empty office night", 6),
    ("dusk city street lights", 6),
    ("person lying in bed ceiling", 6),
    ("window reflection evening", 6),
    ("long empty road dusk", 6),
    ("clock close up dark", 6),
    ("coffee cup dark table", 6),
    ("desk notes writing lamp", 6),
    ("silhouette sunset field", 6),
    ("person massaging temples", 6),
    ("notebook pen dark table", 6),
    ("dark water surface", 6),
    ("light through blinds dark room", 6),
]

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
    "img01": ["face", "tired", "eyes", "forehead", "hand", "ember", "exhausted"],
    "img02": ["candle", "flame", "dark", "table", "burning", "low", "fire"],
    "img03": ["figure", "walking", "road", "dusk", "sky", "alone", "evening"],
    "img04": ["desk", "tired", "sitting", "head", "window", "evening", "lamp", "exhausted"],
    "img05": ["hands", "eyes", "rubbing", "tired", "dark", "face"],
    "img06": ["clockwork", "gears", "mechanism", "machine", "brass", "glow", "clock"],
    "img07": ["bed", "lying", "awake", "night", "ceiling", "blinds", "light", "dark"],
    "img08": ["water", "deep", "underwater", "light", "dark", "swimmer"],
    "img09": ["train", "window", "reflection", "empty", "dusk", "interior", "city"],
    "img10": ["match", "burnt", "ember", "fire", "macro", "row"],
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
open(os.path.join(BASE, ".fetch_done"), "w").write("done")
