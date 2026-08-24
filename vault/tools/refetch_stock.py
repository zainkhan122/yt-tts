#!/usr/bin/env python3
"""refetch_stock.py — API-frugal stock refetcher for /tmp/stockN dirs.

Usage: python3 tools/refetch_stock.py VIDEO_DIR STOCK_DIR

Reads VIDEO_DIR/stock_manifest.json (query -> files).
- If VIDEO_DIR/stock_urls.json missing/incomplete: searches Pexels ONCE to
  harvest direct CDN URLs per file (34 calls) and saves the map.
- Then downloads any missing files by URL (ZERO API calls) — re-runnable
  as often as needed (git_push frees /tmp/stock* on big pushes).
"""
import json, os, sys, time
sys.path.insert(0, "/home/user/tools")
import stock_fetch

VDIR, STOCK = sys.argv[1], sys.argv[2]
MAN = os.path.join(VDIR, "stock_manifest.json")
URLS = os.path.join(VDIR, "stock_urls.json")
os.makedirs(STOCK, exist_ok=True)
manifest = json.load(open(MAN))
need = {f for m in manifest.values() for f in m["files"]}
missing = sorted(f for f in need if not os.path.exists(os.path.join(STOCK, f)))

urlmap = {}
if os.path.exists(URLS):
    urlmap = json.load(open(URLS))

if missing:
    unharvested = [f for f in missing if f not in urlmap]
    if unharvested:
        print(f"harvesting URLs via API for {len(unharvested)} files ...")
        for q, m in manifest.items():
            for f in m["files"]:
                if f in urlmap or f not in unharvested:
                    continue
                try:
                    if m["kind"] == "video":
                        vid = f.split("pexels_v")[1].split(".")[0]
                        data = stock_fetch.get(
                            f"https://api.pexels.com/videos/videos/{vid}",
                            stock_fetch.load_key())
                        files = [x for x in data.get("video_files", [])
                                 if x.get("width", 0) >= 1280
                                 and x.get("width", 0) >= x.get("height", 0)]
                        files.sort(key=lambda x: -x.get("width", 0))
                        files = [x for x in files if x.get("width", 0) <= 1920] or files
                        if files:
                            urlmap[f] = files[0]["link"]
                    else:
                        pid = f.split("pexels_p")[1].split(".")[0]
                        data = stock_fetch.get(
                            f"https://api.pexels.com/v1/photos/{pid}",
                            stock_fetch.load_key())
                        src = data.get("src", {})
                        urlmap[f] = (src.get("large2x") or src.get("large")
                                     or src.get("original"))
                except Exception as e:
                    print(f"  harvest failed {f}: {e}")
                time.sleep(0.15)
        json.dump(urlmap, open(URLS, "w"), indent=1)
    ok = 0
    for f in missing:
        u = urlmap.get(f)
        if not u:
            print(f"  NO URL for {f}"); continue
        p = os.path.join(STOCK, f)
        try:
            stock_fetch.download(u, p); ok += 1
        except Exception as e:
            print(f"  dl failed {f}: {e}")
    print(f"downloaded {ok}/{len(missing)} missing files")
else:
    print("stock dir complete — nothing to do")
have = sum(1 for f in need if os.path.exists(os.path.join(STOCK, f)))
print(f"stock: {have}/{len(need)} files on disk")
