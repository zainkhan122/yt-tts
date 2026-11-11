#!/usr/bin/env python3
"""Capture a product page with Playwright when the HyperFrames CLI is unavailable.

`tools/capture.py` drives `hyperframes capture` for step 1; that CLI only exists in the
render/prep environment. This fallback produces the same pack contract so a brief can be
captured from a laptop/agent sandbox and still render in the cloud:

  captures/<id>/desktop-top.jpg    viewport shot, 1280 CSS px wide @2x
  captures/<id>/desktop-full.jpg   full page, 1280 CSS px wide (scale from the image)
  captures/<id>/mobile.png         phone viewport (390 CSS px @2x), optional
  captures/<id>/demo.mp4           official demo media (GIF/MP4 on the page or --demo), H.264
  captures/<id>/manifest.json      files + regions_css (element boxes) + GitHub facts

  python3 tools/capture_pw.py <id> --url https://github.com/owner/repo [--repo owner/repo]
                             [--demo <url> ...] [--consent]

Facts (stars/forks/licence/created) come from the GitHub API using lib.secrets.gh_token();
never printed. Regions are CSS-pixel boxes of real page elements, measured live.
"""
import argparse
import datetime as dt
import json
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
Image = None

REGION_SELECTORS = {
    # GitHub repo page
    "repo_title": "strong[itemprop='name'] a, [itemprop='name'] a",
    "star_button": "#repo-stars-counter-star, a[href$='/stargazers']",
    "about": ".BorderGrid-cell p.f4.my-3, .BorderGrid-row .BorderGrid-cell p",
    "readme_image": "article img, .markdown-body img",
    "readme_heading": "article h1, article h2, .markdown-body h1",
    "readme_code": "article pre, .markdown-body pre",
    "tree": "[aria-labelledby='files']",
    # generic landing pages
    "hero": "h1",
    "hero_sub": "h1 ~ p, main p",
    "cta": "main a[href]:not([href='#']), button",
    "shot": "main img, img",
}

DEMO_SELECTORS = "article img[src$='.gif'], .markdown-body img[src$='.gif'], video source, video"


def ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def github_facts(repo):
    from lib.secrets import gh_token
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "reels-studio"}
    if gh_token():
        headers["Authorization"] = f"Bearer {gh_token()}"
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}", headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.load(r)
    return {"repo": repo, "stars": d["stargazers_count"], "forks": d["forks_count"],
            "license": (d.get("license") or {}).get("spdx_id"), "created": d["created_at"][:10],
            "description": d.get("description"), "homepage": d.get("homepage"),
            "fetched": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d (own browser capture)")}


def to_mp4(src, dst):
    subprocess.run([ffmpeg(), "-y", "-v", "error", "-i", str(src), "-vf",
                    "scale=trunc(iw/2)*2:trunc(ih/2)*2:flags=lanczos,fps=30",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", "-an", str(dst)], check=True)


def dismiss(page):
    labels = ["accept all cookies", "accept all", "accept cookies", "i agree", "got it", "okay", "agree"]
    try:
        page.evaluate("""(labels) => {
            const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 8 && r.height > 8; };
            const nodes = [...document.querySelectorAll("button, [role=button]")];
            const hit = nodes.map(e => ({e, t: (e.innerText||"").trim().toLowerCase()}))
              .filter(({e,t}) => vis(e) && labels.includes(t))[0];
            if (hit) hit.e.click();
        }""", labels)
    except Exception:
        pass


def capture(cid, url, repo=None, demos=(), consent=False, work=None, extra_regions=None, local_demo=None):
    global Image
    from PIL import Image as _Image
    Image = _Image
    from playwright.sync_api import sync_playwright

    out = Path(work or ROOT / "captures" / cid)
    out.mkdir(parents=True, exist_ok=True)
    files, regions = {}, {}
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=2)
        page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        try:
            page.wait_for_load_state("networkidle", timeout=20_000)
        except Exception:
            pass
        if consent:
            dismiss(page)
            page.wait_for_timeout(600)
        page.wait_for_timeout(1200)
        page.screenshot(path=str(out / "desktop-top.jpg"), type="jpeg", quality=88)
        files["desktop_top"] = {"file": "desktop-top.jpg", "kind": "own capture",
                                "css_width": 1280, "scale": 2}
        page.screenshot(path=str(out / "desktop-full.jpg"), type="jpeg", quality=86, full_page=True)
        with Image.open(out / "desktop-full.jpg") as im:
            full_w, full_h = im.size
        files["desktop_full"] = {"file": "desktop-full.jpg", "kind": "own capture",
                                 "css_width": 1280, "scale": round(full_w / 1280, 2)}
        for key, sel in {**REGION_SELECTORS, **(extra_regions or {})}.items():
            try:
                el = page.query_selector(sel)
                if not el:
                    continue
                box = el.bounding_box()
                scroll = page.evaluate("() => window.scrollY")
                if box and box["width"] > 2 and box["height"] > 2:
                    regions[key] = {"x": round(box["x"]), "y": round(box["y"] + scroll),
                                    "w": round(box["width"]), "h": round(box["height"])}
            except Exception:
                continue
        found = []
        for el in page.query_selector_all(DEMO_SELECTORS):
            try:
                src = el.get_attribute("src") or el.get_attribute("data-src")
                if src and src.lower().split("?")[0].endswith((".gif", ".mp4", ".webm")):
                    found.append(src)
            except Exception:
                continue
        mobile = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
        mobile.goto(url, wait_until="domcontentloaded", timeout=60_000)
        mobile.wait_for_timeout(1200)
        mobile.screenshot(path=str(out / "mobile.png"), type="png")
        files["mobile"] = {"file": "mobile.png", "kind": "own capture", "css_width": 390, "scale": 2}
        browser.close()

    if local_demo:
        dst = out / "demo.mp4"
        subprocess.run([ffmpeg(), "-y", "-v", "error", "-i", str(local_demo), "-an",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                        "-movflags", "+faststart", str(dst)], check=True)
        files["demo"] = {"file": "demo.mp4", "kind": "screen recording (own capture of the live app)"}
        demos = []
    demos = list(demos) + found
    for i, demo_url in enumerate(demos[:1]):
        demo_url = urllib.parse.urljoin(url, demo_url)
        suffix = Path(demo_url.split("?")[0]).suffix.lower()
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            urllib.request.urlretrieve(demo_url, tmp.name)
            src = Path(tmp.name)
        dst = out / "demo.mp4"
        to_mp4(src, dst)
        src.unlink(missing_ok=True)
        files["demo"] = {"file": "demo.mp4", "kind": "official demo media", "source": demo_url}
        break

    manifest = {"capture_id": cid, "url": url,
                "captured": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                "files": files, "regions_css": regions,
                "facts": github_facts(repo) if repo else {}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    for entry in files.values():
        entry["px"] = list(Image.open(out / entry["file"]).size) if entry["file"].endswith((".jpg", ".png")) else None
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    return manifest


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("id")
    ap.add_argument("--url", required=True)
    ap.add_argument("--repo")
    ap.add_argument("--demo", action="append", default=[])
    ap.add_argument("--consent", action="store_true")
    ap.add_argument("--region", action="append", default=[], metavar="NAME=CSS",
                    help="extra region: name=css selector (repeatable)")
    ap.add_argument("--demo-file", help="local screen recording to ship as demo.mp4")
    ap.add_argument("--no-github", action="store_true")
    args = ap.parse_args()
    extra = dict(r.split("=", 1) for r in args.region)
    m = capture(args.id, args.url, None if args.no_github else args.repo, args.demo, args.consent,
                extra_regions=extra, local_demo=args.demo_file)
    print(json.dumps({"capture": args.id, "files": list(m["files"]), "regions": list(m["regions_css"]),
                      "facts": m["facts"]}, indent=1))


if __name__ == "__main__":
    raise SystemExit(main())
