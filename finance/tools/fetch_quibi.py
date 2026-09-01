#!/usr/bin/env python3
"""E02 Pexels VIDEO only. Phones / LA / TVs / commute. No TikTok/Quibi/Roku queries."""
import json, ssl, time, urllib.parse, urllib.request, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEY = (ROOT / "secrets/pexels_key.txt").read_text().strip()
OUT = ROOT / "episodes/Quibi Raised $1.75 Billion. It Lasted Six Months/broll"
OUT.mkdir(parents=True, exist_ok=True)
SEEN = OUT.parent / ".pexels_ids.json"
CTX = ssl.create_default_context()

QUERIES = [
    ("person using smartphone at night", 4),
    ("los angeles downtown night", 4),
    ("subway commute train", 3),
    ("living room watching television", 3),
    ("coffee shop laptop phone", 2),
    ("city street walking night", 3),
    ("empty subway car", 2),
    ("office night computers", 2),
    ("hdmi cable television", 2),
    ("rain window night", 2),
    ("hands holding phone dark", 3),
    ("hollywood hills night lights", 2),
    ("empty office chairs night", 2),
    ("bus window city", 2),
    ("scrolling smartphone close up", 3),
]

BAD = ("tiktok", "instagram", "netflix", "roku", "quibi", "youtube logo",
       "primark", "visa", "mastercard", "gym", "bowling")


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


def pick_file(video):
    files = video.get("video_files") or []
    scored = []
    for vf in files:
        w = vf.get("width") or 0
        h = vf.get("height") or 0
        if h > w:
            continue
        scored.append((abs(w - 1280), w, vf.get("link")))
    scored.sort()
    for _, w, link in scored:
        if link and w >= 640:
            return link, w
    return None, 0


def main():
    ids = set(json.loads(SEEN.read_text())) if SEEN.exists() else set()
    n = len(list(OUT.glob("live_*.mp4")))
    start = n
    for q, count in QUERIES:
        got = 0
        try:
            data = api(
                "https://api.pexels.com/videos/search?query="
                + urllib.parse.quote(q)
                + f"&per_page={min(count + 8, 15)}&orientation=landscape"
            )
        except Exception as e:
            print("FAIL", q, e)
            time.sleep(1)
            continue
        for v in data.get("videos") or []:
            if got >= count:
                break
            vid = v.get("id")
            if vid in ids or (v.get("duration") or 0) < 4:
                continue
            blob = " ".join(str(x or "") for x in (v.get("url"), (v.get("user") or {}).get("name"), q)).lower()
            if any(b in blob for b in BAD):
                continue
            link, w = pick_file(v)
            if not link:
                continue
            raw = Path("/tmp") / f"_q{vid}.mp4"
            clip = OUT / f"live_{n:02d}.mp4"
            try:
                download(link, raw)
                subprocess.run(
                    [ff(), "-y", "-ss", "0.5", "-i", str(raw), "-t", "5.05",
                     "-vf", "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,setsar=1",
                     "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                     "-pix_fmt", "yuv420p", "-an", "-r", "24", str(clip)],
                    capture_output=True, check=True,
                )
                raw.unlink(missing_ok=True)
                ids.add(vid)
                print("V", clip.name, clip.stat().st_size, q)
                n += 1
                got += 1
            except Exception as e:
                raw.unlink(missing_ok=True)
                clip.unlink(missing_ok=True)
                print("skip", e)
        time.sleep(0.3)
    SEEN.write_text(json.dumps(sorted(ids)))
    print("ADDED", n - start, "TOTAL", n, "MB",
          round(sum(p.stat().st_size for p in OUT.glob("*.mp4")) / 1e6, 1))


if __name__ == "__main__":
    main()
