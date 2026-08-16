#!/usr/bin/env python3
"""stock_fetch.py — pull FREE stock media (Pexels photos/videos + Openverse photos)
directly into the workspace. No API key required (Pexels may rate-limit; a free key
makes it rock solid).

USAGE:
  python3 tools/stock_fetch.py pexels-video "rain window night" --n 3 --out stock
  python3 tools/stock_fetch.py pexels-photo "lonely fog forest" --n 6 --out stock
  python3 tools/stock_fetch.py openverse "lonely person silhouette" --n 6 --out stock

OPTIONAL (recommended for reliability):
  Put your FREE Pexels API key (https://www.pexels.com/api/) in a file:
      echo "YOUR_KEY" > ~/.pexels_key
"""
import urllib.request, json, os, sys, time, argparse

PEXELS_KEY_FILE = os.path.expanduser("~/.pexels_key")

def get(url, key=None, tries=4):
    h = {"User-Agent": "Mozilla/5.0 (stock_fetch)"}
    if key:
        h["Authorization"] = key
    last = None
    for a in range(tries):
        req = urllib.request.Request(url, headers=h)
        try:
            return json.load(urllib.request.urlopen(req, timeout=30))
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (403, 429):
                time.sleep(4 * (a + 1))
                continue
            raise
    raise last

def download(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})
    with urllib.request.urlopen(req, timeout=90) as r, open(path, "wb") as f:
        f.write(r.read())
    return os.path.getsize(path)

def load_key():
    if os.path.exists(PEXELS_KEY_FILE):
        return open(PEXELS_KEY_FILE).read().strip()
    return None

def pexels_videos(query, n, out):
    key = load_key()
    data = get(f"https://api.pexels.com/videos/search?query={urllib.parse.quote(query)}&per_page={max(n*3,6)}&orientation=landscape", key)
    saved = []
    for v in data.get("videos", []):
        if len(saved) >= n:
            break
        files = [f for f in v.get("video_files", []) if f.get("width", 0) >= 1280 and f.get("height", 0) <= f.get("width", 0)]
        files.sort(key=lambda f: f.get("width", 0))
        if not files:
            continue
        f = files[0]
        name = f"pexels_v{v['id']}.mp4"
        p = os.path.join(out, name)
        if not os.path.exists(p):
            download(f["link"], p)
        saved.append((name, f"{f['width']}x{f['height']}", v.get("duration")))
        print(f"  [video] {name}  {f['width']}x{f['height']}  {v.get('duration')}s")
    return saved

def pexels_photos(query, n, out):
    key = load_key()
    data = get(f"https://api.pexels.com/v1/search?query={urllib.parse.quote(query)}&per_page={max(n*2,8)}&orientation=landscape", key)
    saved = []
    for ph in data.get("photos", []):
        if len(saved) >= n:
            break
        if ph.get("width", 0) < ph.get("height", 0):
            continue
        url = ph["src"].get("large2x") or ph["src"].get("large") or ph["src"]["original"]
        name = f"pexels_p{ph['id']}.jpg"
        p = os.path.join(out, name)
        if not os.path.exists(p):
            download(url, p)
        saved.append(name)
        print(f"  [photo] {name}")
    return saved

def openverse(query, n, out):
    data = get(f"https://api.openverse.org/v1/images/?q={urllib.parse.quote(query)}&page_size={n}&license_type=commercial")
    saved = []
    for r in data.get("results", []):
        url = r.get("url")
        if not url:
            continue
        ext = ".jpg"
        if url.lower().endswith(".png"):
            ext = ".png"
        name = f"ov_{r['id'][:8]}{ext}"
        p = os.path.join(out, name)
        if not os.path.exists(p):
            try:
                download(url, p)
            except Exception as e:
                print(f"  skip {name}: {e}")
                continue
        saved.append(name)
        lic = r.get("license", "")
        print(f"  [photo] {name}  (license: {lic}, by {r.get('creator','?')})")
    return saved

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", choices=["pexels-video", "pexels-photo", "openverse"])
    ap.add_argument("query")
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--out", default="stock")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    print(f"searching {a.source}: '{a.query}' -> {a.out}/")
    try:
        if a.source == "pexels-video":
            pexels_videos(a.query, a.n, a.out)
        elif a.source == "pexels-photo":
            pexels_photos(a.query, a.n, a.out)
        else:
            openverse(a.query, a.n, a.out)
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("\n⚠️  Pexels returned 401 (rate limit / needs key).")
            print("    Free fix: get a key at https://www.pexels.com/api/ (2 min) then:")
            print('    echo "YOUR_KEY" > ~/.pexels_key')
        else:
            print("HTTP error:", e.code)
        sys.exit(1)
    print("done.")

if __name__ == "__main__":
    import urllib.parse
    main()
