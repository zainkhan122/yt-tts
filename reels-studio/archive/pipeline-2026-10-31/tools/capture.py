#!/usr/bin/env python3
"""
Capture kit: turn a tool's site / GitHub repo into a curated, credited asset pack for a video.

  python3 tools/capture.py universal-modder --url https://github.com/rehan-remade/universal-modder
  python3 tools/capture.py my-tool --url https://tool.site --repo owner/name

Steps (heavy files stay in /var/tmp/reels/captures/<id>/, the curated pack goes to captures/<id>/):
  1. `hyperframes capture`: screenshots, page images/SVGs/logos, fonts, design tokens, embedded videos
  2. tools/capture_extra.cjs: mobile full-page (phone mockups), desktop full-page @2x + REGION MAP
     (real positions of the Star button, About box, README images/headings/code) so the camera can zoom and
     the cursor can click on real page elements
  3. official demo media (GIF/MP4 on the page) -> sharp H.264 MP4 (lanczos 2x for small GIFs)
  4. facts from the GitHub API (stars, forks, licence, created) -> manifest.json with credit lines
  5. preview contact sheet -> captures/<id>/contact.jpg
Asset policy: PHASES.md (own captures + makers' official media, credited; never other creators' clips).
"""
import argparse
import time
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
Image.MAX_IMAGE_PIXELS = 200_000_000


def env():
    e = dict(os.environ)
    e.update(HYPERFRAMES_NO_TELEMETRY="1", HYPERFRAMES_NO_UPDATE_CHECK="1", DO_NOT_TRACK="1", CI="1", NO_COLOR="1")
    e["PATH"] = "/usr/local/bin:" + e.get("PATH", "")
    return e


def run(cmd, **kw):
    print("  $", " ".join(map(str, cmd))[:160])
    return subprocess.run(cmd, check=True, env=env(), **kw)


def gh_facts(repo):
    h = {"Accept": "application/vnd.github+json", "User-Agent": "reels-studio"}
    import sys as _s; _s.path.insert(0, str(ROOT)); from lib.secrets import gh_token
    tok = gh_token() or ""
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    with urllib.request.urlopen(urllib.request.Request(f"https://api.github.com/repos/{repo}", headers=h), timeout=30) as r:
        d = json.load(r)
    return {"repo": repo, "stars": d["stargazers_count"], "forks": d["forks_count"], "watchers": d["subscribers_count"],
            "license": (d.get("license") or {}).get("spdx_id"), "created": d["created_at"][:10], "pushed": d["pushed_at"][:10],
            "description": d.get("description"), "topics": d.get("topics", []), "homepage": d.get("homepage"),
            "fetched": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}


def to_jpeg(src, dst, width=None, q=88):
    im = Image.open(src).convert("RGB")
    if width and im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(dst, "JPEG", quality=q, optimize=True, progressive=True)
    return im.size


def media_to_mp4(src, dst):
    """GIF/WebM/MP4 -> H.264 yuv420p MP4; small sources are upscaled 2x with lanczos + light sharpening."""
    w = int(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width", "-of", "csv=p=0", str(src)],
                           capture_output=True, text=True).stdout.strip() or 0)
    vf = "hqdn3d=1.5:1.5:6:6,scale=trunc(iw*2/2)*2:trunc(ih*2/2)*2:flags=lanczos,unsharp=5:5:0.4" if 0 < w < 720 else "scale=trunc(iw/2)*2:trunc(ih/2)*2"
    run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-vf", vf + ",fps=30", "-c:v", "libx264", "-preset", "slow", "-crf", "21",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", str(dst)])


def contact_sheet(files, dst, cols=4, cell=(420, 300)):
    files = [f for f in files if f.suffix.lower() in (".jpg", ".jpeg", ".png")]
    rows = (len(files) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell[0], rows * (cell[1] + 28)), (24, 24, 27))
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype(str(ROOT / "templates/_base/fonts/Inter.ttf"), 16)
    except OSError:
        font = ImageFont.load_default()
    for i, f in enumerate(files):
        im = Image.open(f).convert("RGB")
        im.thumbnail((cell[0] - 16, cell[1] - 8))
        x, y = (i % cols) * cell[0], (i // cols) * (cell[1] + 28)
        sheet.paste(im, (x + 8, y + 28))
        d.text((x + 8, y + 6), f.name[:44], fill=(230, 230, 235), font=font)
    sheet.save(dst, "JPEG", quality=85)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id")
    ap.add_argument("--url", required=True, help="tool site or GitHub repo URL")
    ap.add_argument("--repo", help="owner/name (auto-detected from a github.com URL)")
    ap.add_argument("--reuse-site", help="existing `hyperframes capture` dir (skip step 1)")
    ap.add_argument("--reuse-extra", help="existing capture_extra output dir (skip step 2)")
    a = ap.parse_args()
    repo = a.repo or (re.match(r"https://github\.com/([^/]+/[^/#?]+)", a.url).group(1) if "github.com/" in a.url else None)
    if repo and repo.startswith("http"):  # accept a full URL for --repo too
        repo = re.match(r"https?://github\.com/([^/]+/[^/#?]+)", repo).group(1)
    heavy = Path("/var/tmp/reels/captures") / a.id
    heavy.mkdir(parents=True, exist_ok=True)
    pack = ROOT / "captures" / a.id
    pack.mkdir(parents=True, exist_ok=True)

    site = Path(a.reuse_site) if a.reuse_site else heavy / "site"
    if not a.reuse_site:
        print("1/5 hyperframes capture")
        run(["hyperframes", "capture", a.url, "-o", str(site), "--skip-vision", "--max-screenshots", "12", "--json"],
            stdout=subprocess.DEVNULL, cwd=str(heavy))
    extra = Path(a.reuse_extra) if a.reuse_extra else heavy / "extra"
    def grab_extra():  # one capture_extra pass; a crash/timeout counts as a failed attempt
        try:
            run(["node", str(ROOT / "tools/capture_extra.cjs"), a.url, str(extra)], stdout=subprocess.DEVNULL)
            return json.loads((extra / "extra.json").read_text())
        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as e:
            print(f"   capture_extra failed: {type(e).__name__}")
            return {}

    if a.reuse_extra:
        ex = json.loads((extra / "extra.json").read_text())
    else:
        print("2/5 mobile + desktop full-page + region map")
        is_gh = "github.com/" in a.url
        ok = lambda e: bool(e) and (not is_gh or e.get("regions", {}).get("repo_title"))
        ex = grab_extra()
        for attempt in (1, 2, 3):  # GitHub sometimes serves a 504/429 page or times out: never ship it
            if ok(ex):
                break
            print(f"   bad capture (error page / timeout); retry {attempt}/3 in 20 s")
            time.sleep(20)
            ex = grab_extra()
        if not ok(ex):
            raise SystemExit("capture failed: page kept erroring/timing out. Nothing saved; try later.")

    print("3/5 curate images + official media")
    files, credits = {}, []
    src = f"{repo} (GitHub)" if repo else a.url
    size = to_jpeg(extra / "desktop-full.png", pack / "desktop-full.jpg", width=1920, q=86)  # 1.5 px per CSS px
    files["desktop_full"] = {"file": "desktop-full.jpg", "px": size, "css_width": 1280, "scale": 1.5, "kind": "own capture"}
    size = to_jpeg(extra / "desktop-viewport.png", pack / "desktop-top.jpg", q=92)  # crisp @2x header (Star/Fork/About)
    files["desktop_top"] = {"file": "desktop-top.jpg", "px": size, "css_width": 1280, "scale": 2, "kind": "own capture"}
    size = to_jpeg(extra / "mobile-full.png", pack / "mobile-full.jpg", width=1075, q=86)
    files["mobile_full"] = {"file": "mobile-full.jpg", "px": size, "css_width": 430, "scale": 2.5, "kind": "own capture"}
    credits.append(f"Screens: own capture of {a.url} on {dt.date.today().isoformat()}")
    assets = site / "assets"
    for p in sorted(assets.glob("*")):
        low = p.name.lower()
        if p.suffix.lower() in (".gif", ".mp4", ".webm") and p.stat().st_size > 200_000:
            out = pack / (p.stem + ".mp4")
            media_to_mp4(p, out)
            files["media_" + p.stem] = {"file": out.name, "kind": "official demo media", "source": src}
        elif p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp") and p.stat().st_size > 40_000 and not low.startswith(("glow", "icon", "contact-sheet")):
            shutil.copy2(p, pack / p.name)
            files["img_" + p.stem] = {"file": p.name, "kind": "official image", "source": src}
        elif low.startswith(("logo", "favicon")) and p.suffix.lower() == ".svg":
            shutil.copy2(p, pack / p.name)
            files["logo_" + p.stem] = {"file": p.name, "kind": "logo", "source": src}
    if any(v["kind"].startswith("official") for v in files.values()):
        credits.append(f"Demo media and images: {src}, credited on screen")

    print("4/5 facts")
    facts = gh_facts(repo) if repo else {}
    if facts:
        credits.append(f"Stats: GitHub API {facts['fetched']}: {facts['stars']:,} stars, {facts['forks']:,} forks, licence {facts['license']}")
    manifest = {"id": a.id, "url": a.url, "captured": dt.date.today().isoformat(), "facts": facts, "files": files,
                "regions_css": ex.get("regions", {}), "region_note": "page CSS px at 1280-wide desktop layout; multiply by files.*.scale for image px",
                "credits": credits, "policy": "own captures + makers' official media, credited; never other creators' clips (PHASES.md)"}
    (pack / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False))

    print("5/5 contact sheet")
    previews = [pack / v["file"] for v in files.values() if (pack / v["file"]).suffix.lower() in (".jpg", ".png")]
    for v in files.values():  # first frame of each clip
        if v["file"].endswith(".mp4"):
            fr = heavy / (Path(v["file"]).stem + "-frame.jpg")
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "4", "-i", str(pack / v["file"]), "-frames:v", "1", str(fr)], check=False)
            if fr.exists():
                previews.append(fr)
    contact_sheet(previews, pack / "contact.jpg")
    total = sum(f.stat().st_size for f in pack.glob("*"))
    print(f"pack -> {pack.relative_to(ROOT.parent)}  ({len(files)} files, {total / 1e6:.1f} MB, {len(manifest['regions_css'])} regions)")


if __name__ == "__main__":
    main()
