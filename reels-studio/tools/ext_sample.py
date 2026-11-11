#!/usr/bin/env python3
"""Download + frame-sample third-party reels for the frame-critique external mode.

Usage: ext_sample.py "<url1> <url2> ..."  (space-separated, max 5)
Accepts canonical reel links (resolved with yt-dlp) or bare adilet-CDN asset ids
(rebuilt into full URLs) / direct mp4 urls. Writes /tmp/ext/frames.json describing
{name, caption, frames[]} per video so frame_critique.py --external can consume it.
"""
import json, os, re, subprocess, sys, urllib.request

CDN = "https://scontent.cdninstagram.com/o1/v/t2/f2/m86/{}.mp4"
OUT = "/tmp/ext"
FF = subprocess.run(["python3", "-c", "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"],
                    capture_output=True, text=True).stdout.strip()


def fetch(i, u):
    src = f"{OUT}/v{i}-src.mp4"
    if "instagram.com/reel" in u or "instagram.com/p/" in u or "tiktok.com" in u or "youtube.com/shorts" in u:
        subprocess.run(["yt-dlp", "--no-warnings", "-f", "best[ext=mp4]/best", "--write-info-json",
                        "-o", f"{OUT}/v{i}.%(ext)s", u], check=True)
        os.replace(f"{OUT}/v{i}.mp4", src)
    else:
        if not u.startswith("http"):
            u = CDN.format(u)  # bare adilet CDN asset id
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as r, open(src, "wb") as f:
            f.write(r.read())
    return src


def sample(i, src):
    p = subprocess.run([FF, "-i", src], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", p.stderr)
    dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    d = f"{OUT}/frames-{i}"
    os.makedirs(d, exist_ok=True)
    for j, t in enumerate([0.3, dur * .25, dur * .5, dur * .75, dur * .95]):
        subprocess.run([FF, "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", src,
                        "-frames:v", "1", "-vf", "scale=512:-1", "-q:v", "4", f"{d}/f{j+1}.jpg"], check=True)
    print(f"v{i}: {dur:.1f}s, 5 frames", flush=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    urls = sys.argv[1].split()[:5]
    pack = []
    for i, u in enumerate(urls, 1):
        src = fetch(i, u)
        sample(i, src)
        cap = ""
        for cand in (f"{OUT}/v{i}.info.json", f"{OUT}/v{i}-src.info.json"):
            if os.path.exists(cand):
                try: cap = json.load(open(cand)).get("description", "")
                except Exception: cap = ""
        pack.append({"name": f"video-{i}", "caption": cap,
                     "frames": sorted(os.path.join(d := f"{OUT}/frames-{i}", f) for f in os.listdir(d))})
    json.dump(pack, open(f"{OUT}/frames.json", "w"))
    print(json.dumps([{k: v[k] for k in ("name",)} | {"frames": len(v["frames"])} for v in pack]))


if __name__ == "__main__":
    main()
