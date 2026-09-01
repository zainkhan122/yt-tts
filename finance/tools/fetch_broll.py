#!/usr/bin/env python3
"""Pexels video (+ optional photos) into an outdir. Audio stripped.
Usage: python3 tools/fetch_broll.py PROFILE OUTDIR [target_n]
Profiles: moviepass | quibi | messenger | toysrus | vert_cinema | vert_phone | vert_news | vert_aisle
"""
import json, ssl, sys, time, urllib.parse, urllib.request, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEY = (ROOT / "secrets/pexels_key.txt").read_text().strip()
CTX = ssl.create_default_context()
PROFILE = sys.argv[1]
OUT = Path(sys.argv[2])
TARGET = int(sys.argv[3]) if len(sys.argv) > 3 else 60
OUT.mkdir(parents=True, exist_ok=True)
SEEN = OUT / ".pexels_ids.json"

PROFILES = {
    "moviepass": {
        "orientation": "landscape",
        "kind": "video",
        "queries": [
            ("empty movie theater", 6),
            ("cinema audience popcorn", 5),
            ("red theater seats", 5),
            ("film projector beam", 4),
            ("movie ticket stub", 3),
            ("new york city street night", 5),
            ("times square night", 4),
            ("people watching movie cinema", 4),
            ("box office cinema", 3),
            ("crowded movie theater", 4),
            ("dark cinema hallway", 3),
            ("popcorn machine cinema", 3),
            ("city rain window night", 3),
            ("startup office laptops", 3),
            ("smartphone in dark room", 4),
            ("people walking manhattan", 3),
            ("marquee lights cinema", 3),
            ("empty auditorium seats", 4),
            ("film reel close up", 2),
            ("coffee shop city", 2),
            ("subway new york", 3),
            ("city skyline dusk", 3),
            ("hands holding ticket", 3),
            ("dark empty street nyc", 3),
        ],
    },
    "quibi": {
        "orientation": "landscape",
        "kind": "video",
        "queries": [
            ("person using smartphone at night", 5),
            ("los angeles downtown night", 5),
            ("subway commute train", 4),
            ("living room watching television", 4),
            ("coffee shop laptop phone", 3),
            ("city street walking night", 4),
            ("empty subway car", 3),
            ("office night computers", 3),
            ("hands holding phone dark", 5),
            ("scrolling smartphone close up", 5),
            ("bus window city", 3),
            ("rain window night", 3),
            ("hollywood hills night lights", 3),
            ("empty office chairs night", 3),
            ("phone on table dark", 4),
            ("commuters looking at phones", 4),
            ("apartment window city night", 3),
            ("television living room dark", 3),
        ],
    },
    "vert_cinema": {
        "orientation": "portrait",
        "kind": "video",
        "queries": [
            ("movie theater seats", 4),
            ("popcorn cinema", 3),
            ("smartphone dark", 3),
            ("city night street", 3),
            ("empty theater", 3),
            ("ticket hand", 2),
        ],
    },
    "messenger": {
        "orientation": "landscape",
        "kind": "video",
        "queries": [
            ("empty office desks night", 6),
            ("newsroom computers", 5),
            ("person typing laptop office", 5),
            ("florida palm trees city", 3),
            ("email on laptop screen", 4),
            ("newspaper printing press", 3),
            ("office meeting empty chairs", 4),
            ("city skyline dusk office", 4),
            ("hands on keyboard close up", 4),
            ("server room lights", 3),
            ("coffee office late night", 4),
            ("open plan office walking", 4),
            ("phone notification dark", 3),
            ("rain window office", 3),
        ],
    },
    "vert_news": {
        "orientation": "portrait",
        "kind": "video",
        "queries": [
            ("empty office", 4),
            ("laptop email", 3),
            ("city night", 3),
            ("person typing", 3),
        ],
    },
    "vert_phone": {
        "orientation": "portrait",
        "kind": "video",
        "queries": [
            ("person using smartphone", 5),
            ("city night", 3),
            ("scrolling phone", 4),
            ("los angeles night", 3),
            ("commute train", 3),
            ("television dark room", 2),
        ],
    },
    "stills_cinema": {
        "orientation": "landscape",
        "kind": "photo",
        "queries": [
            ("empty movie theater", 6),
            ("cinema popcorn", 4),
            ("new york night", 4),
            ("red theater seats", 4),
            ("movie tickets", 3),
        ],
    },
    "stills_news": {
        "orientation": "landscape",
        "kind": "photo",
        "queries": [
            ("empty office desk", 6),
            ("laptop office night", 5),
            ("newspaper stack", 4),
            ("city office window", 5),
            ("keyboard close up", 4),
        ],
    },
    "stills_phone": {
        "orientation": "landscape",
        "kind": "photo",
        "queries": [
            ("smartphone dark table", 5),
            ("los angeles night skyline", 4),
            ("commute phone", 3),
            ("television living room", 3),
        ],
    },
    "toysrus": {
        "orientation": "landscape",
        "kind": "video",
        "queries": [
            ("empty supermarket aisle", 6),
            ("empty store shelves", 5),
            ("retail warehouse shelves", 5),
            ("shopping cart empty store", 4),
            ("big box store interior", 4),
            ("empty mall corridor", 4),
            ("store closing metal shutters", 3),
            ("cardboard boxes warehouse", 4),
            ("suburban shopping center", 4),
            ("empty parking lot retail", 3),
            ("fluorescent aisle supermarket", 4),
            ("cashier empty checkout", 3),
            ("forklift warehouse", 3),
            ("shopping bags retail", 3),
            ("abandoned store interior", 4),
            ("warehouse orange shelves", 3),
            ("going out of business store", 3),
            ("empty retail shelf", 3),
            ("grocery store aisle walking", 4),
            ("department store interior", 4),
            ("loading dock warehouse", 3),
            ("empty shopping mall", 4),
            ("store window night", 3),
        ],
    },
    "vert_aisle": {
        "orientation": "portrait",
        "kind": "video",
        "queries": [
            ("empty supermarket aisle", 5),
            ("empty store shelves", 4),
            ("shopping cart store", 3),
            ("warehouse shelves", 3),
            ("mall corridor empty", 3),
            ("store interior fluorescent", 3),
        ],
    },
    "stills_aisle": {
        "orientation": "landscape",
        "kind": "photo",
        "queries": [
            ("empty supermarket aisle", 6),
            ("empty store shelves", 5),
            ("warehouse aisle", 4),
            ("abandoned retail interior", 4),
            ("shopping cart aisle", 3),
        ],
    },
}

BAD = (
    "tiktok", "instagram", "netflix", "roku", "quibi", "youtube logo",
    "primark", "visa", "mastercard", "lingerie", "coupon", "kid",
    "pizza", "stock chart", "bitcoin", "forex",
)


def ff():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def api(url):
    req = urllib.request.Request(url, headers={"Authorization": KEY, "User-Agent": "public-record"})
    with urllib.request.urlopen(req, context=CTX, timeout=30) as r:
        return json.loads(r.read().decode())


def download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": "public-record"})
    with urllib.request.urlopen(req, context=CTX, timeout=90) as r, open(dest, "wb") as f:
        f.write(r.read())


def pick_file(video, portrait):
    files = video.get("video_files") or []
    scored = []
    for vf in files:
        w = vf.get("width") or 0
        h = vf.get("height") or 0
        if portrait and w > h:
            continue
        if (not portrait) and h > w:
            continue
        target = 720 if portrait else 1280
        scored.append((abs(w - target), w, vf.get("link")))
    scored.sort()
    for _, w, link in scored:
        if link and w >= 360:
            return link, w
    return None, 0


def main():
    cfg = PROFILES[PROFILE]
    portrait = cfg["orientation"] == "portrait"
    kind = cfg["kind"]
    ids = set(json.loads(SEEN.read_text())) if SEEN.exists() else set()
    existing = list(OUT.glob("live_*.mp4" if kind == "video" else "still_*.jpg"))
    n = len(existing)
    start = n
    print(f"profile {PROFILE} have {n} target {TARGET}", flush=True)
    for q, count in cfg["queries"]:
        if n >= TARGET:
            break
        got = 0
        try:
            if kind == "video":
                url = (
                    "https://api.pexels.com/videos/search?query="
                    + urllib.parse.quote(q)
                    + f"&per_page={min(count + 10, 20)}&orientation={cfg['orientation']}"
                )
            else:
                url = (
                    "https://api.pexels.com/v1/search?query="
                    + urllib.parse.quote(q)
                    + f"&per_page={min(count + 8, 20)}&orientation={cfg['orientation']}"
                )
            data = api(url)
        except Exception as e:
            print("FAIL", q, e, flush=True)
            time.sleep(1)
            continue
        items = data.get("videos") if kind == "video" else data.get("photos")
        for v in items or []:
            if got >= count or n >= TARGET:
                break
            vid = v.get("id")
            if vid in ids:
                continue
            blob = " ".join(str(x or "") for x in (v.get("url"), (v.get("user") or {}).get("name") or (v.get("photographer")), q)).lower()
            if any(b in blob for b in BAD):
                continue
            if kind == "video":
                if (v.get("duration") or 0) < 4:
                    continue
                link, w = pick_file(v, portrait)
                if not link:
                    continue
                raw = Path("/tmp") / f"_pex{vid}.mp4"
                clip = OUT / f"live_{n:02d}.mp4"
                try:
                    download(link, raw)
                    if portrait:
                        vf = "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setsar=1"
                    else:
                        vf = "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,setsar=1"
                    subprocess.run(
                        [ff(), "-y", "-ss", "0.4", "-i", str(raw), "-t", "7.80",
                         "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
                         "-pix_fmt", "yuv420p", "-an", "-r", "24", str(clip)],
                        capture_output=True, check=True,
                    )
                    raw.unlink(missing_ok=True)
                    ids.add(vid)
                    print("V", clip.name, clip.stat().st_size, q, flush=True)
                    n += 1
                    got += 1
                except Exception as e:
                    raw.unlink(missing_ok=True)
                    clip.unlink(missing_ok=True)
                    print("skip", e, flush=True)
            else:
                src = (v.get("src") or {})
                link = src.get("large") or src.get("original") or src.get("medium")
                if not link:
                    continue
                dest = OUT / f"still_{n:02d}.jpg"
                try:
                    download(link, dest)
                    ids.add(vid)
                    print("P", dest.name, dest.stat().st_size, q, flush=True)
                    n += 1
                    got += 1
                except Exception as e:
                    dest.unlink(missing_ok=True)
                    print("skip", e, flush=True)
        time.sleep(0.25)
    SEEN.write_text(json.dumps(sorted(ids)))
    print("ADDED", n - start, "TOTAL", n, "MB",
          round(sum(p.stat().st_size for p in OUT.glob("*") if p.suffix in {".mp4", ".jpg"}) / 1e6, 1))


if __name__ == "__main__":
    main()
