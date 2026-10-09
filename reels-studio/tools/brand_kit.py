#!/usr/bin/env python3
"""Hypeless brand kit: logo, profile pictures, banners and copy-paste profile text.

  python3 tools/brand_kit.py            rebuild brand/ (images + README.md + brand-kit.html)
  python3 tools/brand_kit.py --check    only check brand/profiles.json against platform limits
  python3 tools/brand_kit.py --publish  rebuild + upload hypeless-brand-kit.zip to GitHub release "brand"

Sources of truth: brand/profiles.json (all account text + limits) and MARK below (logo geometry,
measured from the design the user picked on 2026-10-09). Everything else in brand/ is generated.
"""
from __future__ import annotations

import argparse
import base64
import html
import io
import json
import math
import subprocess
import sys
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "brand"
FONTS = ROOT / "templates" / "_base" / "fonts"
RAW = "https://raw.githubusercontent.com/zainkhan122/yt-tts/main/reels-studio/brand"
RELEASE_TAG = "brand"
ZIP_NAME = "hypeless-brand-kit.zip"
ZIP_URL = f"https://github.com/zainkhan122/yt-tts/releases/download/{RELEASE_TAG}/{ZIP_NAME}"

YELLOW, SKY, MIDNIGHT, INK, MUTED = "#FFD60A", "#38BDF8", "#050B1F", "#F5F7FF", "#8FA3C7"
SOFT = "#B8C6E3"

# Logo in a 1000 x 1000 box: two yellow stems + a floating sky-blue minus as the H crossbar
# ("AI tools, minus the hype"). Circle-safe: the farthest corner sits at 84% of the radius.
MARK = [(206.5, 200, 118, 600, YELLOW), (675.5, 200, 118, 600, YELLOW), (360.5, 450, 279, 100, SKY)]
MARK_R = 13
MARK_X0, MARK_Y0, MARK_W, MARK_H = 206.5, 200, 587, 600


def rgba(h: str, a: int = 255) -> tuple:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a


# ---------------------------------------------------------------- vector logo
def mark_svg(bg: str | None = MIDNIGHT, corner: float = 0, tight: bool = False) -> str:
    box = f"{MARK_X0} {MARK_Y0} {MARK_W} {MARK_H}" if tight else "0 0 1000 1000"
    w, h = (MARK_W, MARK_H) if tight else (1000, 1000)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{box}" width="{w}" height="{h}">',
             "<title>Hypeless</title>"]
    if bg:
        parts.append(f'<rect width="1000" height="1000" rx="{corner}" fill="{bg}"/>')
    for x, y, rw, rh, c in MARK:
        parts.append(f'<rect x="{x}" y="{y}" width="{rw}" height="{rh}" rx="{MARK_R}" fill="{c}"/>')
    return "".join(parts) + "</svg>\n"


# ---------------------------------------------------------------- raster helpers
def paint(w: int, h: int, shapes: list, bg: str | None = None, ss: int = 4) -> Image.Image:
    """Rounded rectangles (x0, y0, x1, y1, radius, colour) in output px; supersampled + premultiplied."""
    big = Image.new("RGBA", (w * ss, h * ss), rgba(bg) if bg else (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    for x0, y0, x1, y1, r, c in shapes:
        d.rounded_rectangle([round(x0 * ss), round(y0 * ss), round(x1 * ss) - 1, round(y1 * ss) - 1],
                            radius=max(0, round(r * ss)), fill=rgba(c))
    return big.convert("RGBa").resize((w, h), Image.LANCZOS).convert("RGBA")


def mark_shapes(ox: float, oy: float, size: float, tight: bool = False) -> list:
    """Logo rectangles in a square box of `size` px, or (tight) a box whose height is `size` px."""
    s, bx, by = (size / MARK_H, MARK_X0, MARK_Y0) if tight else (size / 1000, 0, 0)
    return [(ox + (x - bx) * s, oy + (y - by) * s, ox + (x - bx + w) * s, oy + (y - by + h) * s,
             MARK_R * s, c) for x, y, w, h, c in MARK]


def mark_image(height: int) -> Image.Image:
    """Transparent, tightly cropped mark of the given pixel height."""
    return paint(round(height * MARK_W / MARK_H), height, mark_shapes(0, 0, height, tight=True))


def font(name: str, size: float, weight: int | None = None) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(FONTS / f"{name}.ttf"), max(1, round(size)))
    if weight is not None:
        try:
            f.set_variation_by_axes([min(32, max(14, round(size))), weight])  # Inter: [opsz, wght]
        except Exception:
            pass
    return f


def cap_height(f) -> float:
    return -f.getbbox("H", anchor="ls")[1]


def font_for_cap(name: str, cap: float, weight: int | None = None):
    size = cap * 1.4
    for _ in range(3):
        size *= cap / cap_height(font(name, size, weight))
    return font(name, size, weight)


def runs_width(runs: list, f, track: float = 0.0) -> float:
    n = sum(len(t) for t, _ in runs)
    if not track:
        return sum(f.getlength(t) for t, _ in runs)
    return sum(f.getlength(ch) for t, _ in runs for ch in t) + track * (n - 1)


def draw_runs(img: Image.Image, x: float, baseline: float, runs: list, f, track: float = 0.0) -> float:
    d = ImageDraw.Draw(img)
    for text, col in runs:
        if not track:
            d.text((x, baseline), text, font=f, fill=rgba(col), anchor="ls")
            x += f.getlength(text)
            continue
        for ch in text:
            d.text((x, baseline), ch, font=f, fill=rgba(col), anchor="ls")
            x += f.getlength(ch) + track
    return x


def backdrop(w: int, h: int, glows: list, grid: int = 64, grid_alpha: float = 0.04) -> Image.Image:
    """Midnight base, soft centre lift, coloured glows, a fading tech grid, light dither (no banding)."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    base = np.array(rgba(MIDNIGHT)[:3], np.float32)
    img = np.broadcast_to(base, (h, w, 3)).copy()
    d = np.sqrt(((xx - w / 2) / (0.60 * w)) ** 2 + ((yy - h / 2) / (0.60 * h)) ** 2)
    lift = np.clip(1 - d, 0, 1) ** 1.5
    img += lift[..., None] * (np.array([13, 27, 62], np.float32) - base)
    for gx, gy, gr, col, k in glows:
        g = np.exp(-(((xx - gx) ** 2 + (yy - gy) ** 2) / (gr * gr)) * 2.0) * k
        img = img * (1 - g[..., None]) + np.array(rgba(col)[:3], np.float32) * g[..., None]
    if grid:
        lines = (((xx - w / 2) % grid) < 1.0) | (((yy - h / 2) % grid) < 1.0)
        a = lines * grid_alpha * np.clip(1.1 - d, 0, 1)
        img = img * (1 - a[..., None]) + 255.0 * a[..., None]
    img += np.random.default_rng(7).uniform(-0.6, 0.6, img.shape).astype(np.float32)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


PROMISE = [("✓ ", YELLOW), ("What it does", SOFT), ("      ✓ ", YELLOW), ("What it costs", SOFT),
           ("      ✓ ", YELLOW), ("The catch", SOFT)]
TAGLINE = [("AI TOOLS, ", INK), ("MINUS THE HYPE.", YELLOW)]


def lockup(cap: float, tagline: bool = True, promise: bool = True) -> Image.Image:
    """Mark + HYPELESS (+ tagline, + promise) as one transparent layer; mark height = text stack height."""
    ft = font_for_cap("Anton", cap)
    tcap, pcap = cap * 0.27, cap * 0.18
    fg, fp = font_for_cap("Inter", tcap, 700), font_for_cap("Inter", pcap, 500)
    ttrack, gtrack = cap * 0.035, tcap * 0.14
    gap1, gap2 = cap * 0.30, cap * 0.27
    stack = cap + (gap1 + tcap if tagline else 0) + (gap2 + pcap if promise else 0)
    mark = mark_image(round(stack))
    gx = round(cap * 0.50)
    widths = [runs_width([("HYPELESS", INK)], ft, ttrack)]
    if tagline:
        widths.append(runs_width(TAGLINE, fg, gtrack))
    if promise:
        widths.append(runs_width(PROMISE, fp))
    layer = Image.new("RGBA", (mark.width + gx + math.ceil(max(widths)) + 4, mark.height), (0, 0, 0, 0))
    layer.alpha_composite(mark, (0, 0))
    x, b = mark.width + gx, cap
    draw_runs(layer, x, b, [("HYPELESS", INK)], ft, ttrack)
    if tagline:
        b += gap1 + tcap
        draw_runs(layer, x, b, TAGLINE, fg, gtrack)
    if promise:
        b += gap2 + pcap
        draw_runs(layer, x, b, PROMISE, fp)
    return layer


def fit_lockup(max_w: float, max_h: float, cap: float = 180, **kw) -> Image.Image:
    lay = lockup(cap, **kw)
    s = min(max_w / lay.width, max_h / lay.height)
    return lockup(cap * s * 0.995, **kw)


def place(canvas: Image.Image, layer: Image.Image, cx: float, cy: float) -> None:
    canvas.alpha_composite(layer, (round(cx - layer.width / 2), round(cy - layer.height / 2)))


# ---------------------------------------------------------------- assets
def build_images() -> dict:
    (BRAND / "logo").mkdir(parents=True, exist_ok=True)
    (BRAND / "banners").mkdir(parents=True, exist_ok=True)
    out = {}

    def save(img: Image.Image, rel: str, **kw) -> None:
        p = BRAND / rel
        if p.suffix == ".jpg":
            img.convert("RGB").save(p, quality=kw.get("q", 95), subsampling=0, optimize=True, progressive=True)
        else:
            img.save(p, optimize=True)
        out[rel] = img

    (BRAND / "logo" / "hypeless-mark.svg").write_text(mark_svg(MIDNIGHT))
    (BRAND / "logo" / "hypeless-mark-transparent.svg").write_text(mark_svg(None, tight=True))
    (BRAND / "logo" / "hypeless-app-icon.svg").write_text(mark_svg(MIDNIGHT, corner=225))

    save(paint(1080, 1080, mark_shapes(0, 0, 1080), bg=MIDNIGHT, ss=3), "logo/avatar-1080.png")
    save(mark_image(1024), "logo/mark-transparent-1024.png")
    wm = paint(150, 150, [(0, 0, 150, 150, 34, MIDNIGHT)] + mark_shapes(0, 0, 150), ss=8)
    save(wm, "logo/yt-watermark-150.png")

    lk = lockup(220, promise=False)
    pad = 120
    dark = Image.new("RGBA", (lk.width + 2 * pad, lk.height + 2 * pad), rgba(MIDNIGHT))
    dark.alpha_composite(lk, (pad, pad))
    save(dark, "logo/lockup-dark.png")
    save(lk, "logo/lockup-transparent.png")

    # YouTube: 2560x1440; every device shows the centre 1546x423, desktop the 2560x423 band.
    W, H = 2560, 1440
    yt = backdrop(W, H, [(W * 0.36, H / 2, 520, YELLOW, 0.025), (W * 0.70, H / 2, 640, SKY, 0.06)])
    place(yt, fit_lockup(1546 - 150, 423 - 96), W / 2, H / 2)
    save(yt, "banners/youtube-banner-2560x1440.jpg")

    # X: 1500x500; the round avatar covers the bottom-left, so content sits centre-right.
    W, H = 1500, 500
    xh = backdrop(W, H, [(W * 0.62, H * 0.46, 420, SKY, 0.07), (W * 0.30, H * 0.40, 300, YELLOW, 0.015)], grid=48)
    tf = font_for_cap("Anton", 74)
    lf = font_for_cap("Inter", 17, 800)
    pf = font_for_cap("Inter", 22, 500)
    label = [("HYPELESS", SKY)]
    lw, tw, pw = runs_width(label, lf, 17 * 0.32), runs_width(TAGLINE, tf, 74 * 0.02), runs_width(PROMISE, pf)
    cx, top = 840, 150
    draw_runs(xh, cx - lw / 2, top + 17, label, lf, 17 * 0.32)
    draw_runs(xh, cx - tw / 2, top + 17 + 34 + 74, TAGLINE, tf, 74 * 0.02)
    draw_runs(xh, cx - pw / 2, top + 17 + 34 + 74 + 40 + 22, PROMISE, pf)
    save(xh, "banners/x-header-1500x500.jpg")

    # Facebook: 1640x720 upload; desktop shows 1640x624, phones 1280x720 -> safe 1280x624 in the centre.
    W, H = 1640, 720
    fb = backdrop(W, H, [(W * 0.36, H / 2, 380, YELLOW, 0.025), (W * 0.68, H / 2, 460, SKY, 0.06)], grid=56)
    place(fb, fit_lockup(1100, 300), W / 2, H / 2 - 20)
    save(fb, "banners/facebook-cover-1640x720.jpg")
    return out


# ---------------------------------------------------------------- text checks + pages
def u16(s: str) -> int:
    return max(len(s), len(s.encode("utf-16-le")) // 2)


def check(profiles: dict) -> list:
    problems = []
    for key in profiles["order"]:
        p = profiles["platforms"][key]
        for f in p["fields"]:
            lim = f.get("limit")
            if lim and u16(f["value"]) > lim:
                problems.append(f"{p['title']} / {f['label']}: {u16(f['value'])} > {lim}")
        for rel, _ in p["upload"]:
            if not (BRAND / rel).exists():
                problems.append(f"{p['title']}: missing file {rel}")
    return problems


def data_uri(img: Image.Image, max_w: int, fmt: str = "JPEG") -> str:
    im = img.convert("RGB") if fmt == "JPEG" else img
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, fmt, **({"quality": 86} if fmt == "JPEG" else {"optimize": True}))
    return f"data:image/{fmt.lower()};base64," + base64.b64encode(buf.getvalue()).decode()


def build_readme(pr: dict) -> str:
    b = pr["brand"]
    L = ["# Hypeless brand kit", "",
         f"**{b['name']}** · {b['handle']} · *{b['tagline']}* · {b['promise']}", "",
         f"One-click download of everything: [{ZIP_NAME}]({ZIP_URL})  ·  visual version: `brand-kit.html`", "",
         "Generated by `python3 tools/brand_kit.py` from `profiles.json` (edit that file, never this one).", "",
         "## Create the accounts in this order", ""]
    L += [f"{i}. {s}" for i, s in enumerate(pr["setup_order"], 1)]
    L += ["", "## Files", "", "| File | Use |", "|---|---|",
          "| `logo/avatar-1080.png` | Profile picture on every platform (circle-safe) |",
          "| `banners/youtube-banner-2560x1440.jpg` | YouTube banner (text inside the 1546×423 safe area) |",
          "| `banners/x-header-1500x500.jpg` | X header |",
          "| `banners/facebook-cover-1640x720.jpg` | Facebook Page cover (safe on desktop and phones) |",
          "| `logo/yt-watermark-150.png` | YouTube video watermark |",
          "| `logo/hypeless-mark.svg` · `-transparent.svg` · `-app-icon.svg` | Vector logo (any size) |",
          "| `logo/mark-transparent-1024.png` · `lockup-*.png` | Logo for overlays, website, thumbnails |", ""]
    for key in pr["order"]:
        p = pr["platforms"][key]
        L += [f"## {p['title']}", "", "**Upload:** " + " · ".join(f"`{f}` → {w}" for f, w in p["upload"]), ""]
        for f in p["fields"]:
            lim = f.get("limit")
            count = f" ({u16(f['value'])}/{lim})" if lim else ""
            L += [f"**{f['label']}**{count}", "```", f["value"], "```"]
        L += ["", "**Settings**", ""] + [f"- {s}" for s in p["settings"]] + [""]
    L += ["## Colours and fonts", "", " · ".join(f"{k} `{v}`" for k, v in b["colors"].items()),
          "", " · ".join(f"{k}: {v}" for k, v in b["fonts"].items()), ""]
    return "\n".join(L)


CSS = """
*{box-sizing:border-box}body{margin:0;background:#050B1F;color:#F5F7FF;font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
.wrap{max-width:1060px;margin:0 auto;padding:28px 18px 60px}h1{font-size:28px;margin:0}h2{font-size:20px;margin:0 0 12px}
.hero{display:flex;gap:18px;align-items:center;margin-bottom:22px}.hero img{width:84px;height:84px;border-radius:50%}
.sub{color:#8FA3C7}.y{color:#FFD60A}.btn{display:inline-block;background:#FFD60A;color:#050B1F;font-weight:700;border-radius:10px;padding:9px 16px;text-decoration:none;border:0;cursor:pointer}
.card{background:#0B1430;border:1px solid #1A2752;border-radius:16px;padding:18px;margin:16px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}.asset img{width:100%;border-radius:10px;display:block}
.asset .cap{font-size:13px;color:#8FA3C7;margin-top:6px}.asset b{color:#F5F7FF}.stage{position:relative}
.safe{position:absolute;border:2px dashed #FFD60A;border-radius:4px;pointer-events:none}.band{position:absolute;left:0;right:0;border-top:1px dashed #38BDF8;border-bottom:1px dashed #38BDF8;pointer-events:none}
.avatars{display:flex;gap:14px;align-items:end}.avatars img{border-radius:50%}
.f{margin:12px 0}.f .lab{display:flex;justify-content:space-between;font-size:13px;color:#8FA3C7;margin-bottom:4px}.ok{color:#4ADE80}.bad{color:#F87171}
textarea{width:100%;background:#050B1F;color:#F5F7FF;border:1px solid #22325F;border-radius:10px;padding:10px;font:14px/1.45 ui-monospace,Menlo,Consolas,monospace;resize:vertical}
.row{display:flex;gap:8px;align-items:flex-start}.row textarea{flex:1}.cp{flex:none;background:#1A2752;color:#F5F7FF;border:0;border-radius:10px;padding:10px 12px;cursor:pointer;font-weight:600}
.cp.done{background:#FFD60A;color:#050B1F}ul,ol{padding-left:20px;margin:6px 0}li{margin:4px 0}.sw{display:inline-flex;align-items:center;gap:8px;margin:4px 14px 4px 0}
.sw i{width:22px;height:22px;border-radius:6px;display:inline-block;border:1px solid #22325F}nav a{color:#38BDF8;margin-right:14px;text-decoration:none;font-weight:600}
"""

JS = """
function cp(id,btn){var t=document.getElementById(id);t.focus();t.select();var ok=function(){btn.textContent='Copied';btn.classList.add('done');setTimeout(function(){btn.textContent='Copy';btn.classList.remove('done')},1400)};
try{navigator.clipboard.writeText(t.value).then(ok,function(){document.execCommand('copy');ok()})}catch(e){try{document.execCommand('copy');ok()}catch(e2){}}}
"""


def build_html(pr: dict, imgs: dict) -> str:
    e = html.escape
    b = pr["brand"]
    av = data_uri(imgs["logo/avatar-1080.png"], 320, "PNG")
    yt = data_uri(imgs["banners/youtube-banner-2560x1440.jpg"], 1280)
    xh = data_uri(imgs["banners/x-header-1500x500.jpg"], 1000)
    fb = data_uri(imgs["banners/facebook-cover-1640x720.jpg"], 1000)
    wm = data_uri(imgs["logo/yt-watermark-150.png"], 150, "PNG")
    lk = data_uri(imgs["logo/lockup-dark.png"], 900)
    nav = " ".join(f'<a href="#{k}">{e(pr["platforms"][k]["title"])}</a>' for k in pr["order"])
    H = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
         f"<title>Hypeless brand kit</title><style>{CSS}</style></head><body><div class='wrap'>",
         f"<div class='hero'><img src='{av}' alt=''><div><h1>Hypeless brand kit</h1>"
         f"<div class='sub'>{e(b['handle'])} · <span class='y'>{e(b['tagline'])}</span> · {e(b['promise'])}</div></div></div>",
         f"<p><a class='btn' href='{ZIP_URL}'>Download everything (.zip)</a> &nbsp;<span class='sub'>Full-size files are also in the repo under reels-studio/brand/.</span></p>",
         f"<nav>{nav}</nav>",
         "<div class='card'><h2>1 · Create the accounts in this order</h2><ol>"
         + "".join(f"<li>{e(s)}</li>" for s in pr["setup_order"]) + "</ol></div>",
         "<div class='card'><h2>2 · Images to upload</h2><div class='grid'>",
         f"<div class='asset'><div class='avatars'><img src='{av}' width='120' height='120' alt=''><img src='{av}' width='64' height='64' alt=''>"
         f"<img src='{av}' width='36' height='36' alt=''></div><div class='cap'><b>avatar-1080.png</b>: profile picture on all 5 platforms (shown here in the circle crop at real sizes)</div></div>",
         f"<div class='asset'><img src='{wm}' style='width:90px;border-radius:0' alt=''><div class='cap'><b>yt-watermark-150.png</b>: YouTube video watermark</div></div>",
         "</div><div class='asset' style='margin-top:14px'><div class='stage'>"
         f"<img src='{yt}' alt=''><div class='band' style='top:35.31%;height:29.37%'></div>"
         "<div class='safe' style='left:19.8%;top:35.31%;width:60.39%;height:29.37%'></div></div>"
         "<div class='cap'><b>youtube-banner-2560x1440.jpg</b>: yellow box = visible on every device (phones), blue band = desktop, whole image = TV</div></div>",
         f"<div class='grid' style='margin-top:14px'><div class='asset'><img src='{xh}' alt=''><div class='cap'><b>x-header-1500x500.jpg</b>: X header (bottom-left left clear for the round avatar)</div></div>",
         f"<div class='asset'><div class='stage'><img src='{fb}' alt=''><div class='safe' style='left:10.98%;top:6.67%;width:78.05%;height:86.67%'></div></div>"
         "<div class='cap'><b>facebook-cover-1640x720.jpg</b>: Facebook Page cover (yellow box = safe on desktop + phones)</div></div></div>",
         f"<div class='asset' style='margin-top:14px'><img src='{lk}' alt='' style='max-width:520px'><div class='cap'><b>lockup-dark.png / lockup-transparent.png</b>: logo + name for websites, thumbnails, link pages</div></div>",
         "</div>"]
    n = 0
    for key in pr["order"]:
        p = pr["platforms"][key]
        H.append(f"<div class='card' id='{key}'><h2>{e(p['title'])}</h2>")
        H.append("<div class='sub'>Upload: " + " · ".join(f"<b>{e(Path(f).name)}</b> → {e(w)}" for f, w in p["upload"]) + "</div>")
        for f in p["fields"]:
            n += 1
            lim = f.get("limit")
            c = u16(f["value"])
            cnt = f"<span class='{'ok' if c <= lim else 'bad'}'>{c} / {lim}</span>" if lim else ""
            rows = min(14, f["value"].count("\n") + 1 + len(f["value"]) // 95)
            H.append(f"<div class='f'><div class='lab'><span>{e(f['label'])}</span>{cnt}</div><div class='row'>"
                     f"<textarea id='t{n}' rows='{rows}' readonly>{e(f['value'])}</textarea>"
                     f"<button class='cp' onclick=\"cp('t{n}',this)\">Copy</button></div></div>")
        H.append("<div class='f'><div class='lab'><span>Settings</span></div><ul>" + "".join(f"<li>{e(s)}</li>" for s in p["settings"]) + "</ul></div></div>")
    H.append("<div class='card'><h2>Colours and fonts</h2>"
             + "".join(f"<span class='sw'><i style='background:{v}'></i>{e(k)} <code>{v}</code></span>" for k, v in b["colors"].items())
             + "<p class='sub'>" + " · ".join(f"{e(k)}: {e(v)}" for k, v in b["fonts"].items()) + " (both free, OFL)</p></div>")
    H.append(f"</div><script>{JS}</script></body></html>")
    return "".join(H)


def build_zip() -> Path:
    zp = Path("/var/tmp") / ZIP_NAME
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(BRAND.rglob("*")):
            if p.is_file():
                z.write(p, Path("hypeless-brand-kit") / p.relative_to(BRAND))
    return zp


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--publish", action="store_true")
    a = ap.parse_args()
    pr = json.loads((BRAND / "profiles.json").read_text())
    if a.check:
        probs = check(pr)
        print("\n".join(probs) or "profiles.json: all fields within platform limits")
        return 1 if probs else 0
    imgs = build_images()
    probs = check(pr)
    if probs:
        print("LIMIT PROBLEMS:\n" + "\n".join(probs))
        return 1
    (BRAND / "README.md").write_text(build_readme(pr))
    (BRAND / "brand-kit.html").write_text(build_html(pr, imgs))
    for rel in sorted(imgs):
        print(f"  {rel:42s} {imgs[rel].width}x{imgs[rel].height}  {(BRAND / rel).stat().st_size / 1024:7.1f} KB")
    print("  README.md, brand-kit.html written; all text within platform limits")
    if a.publish:
        zp = build_zip()
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "publish_release.py"), "--tag", RELEASE_TAG,
                            "--replace", str(zp)], cwd=ROOT)
        zp.unlink(missing_ok=True)
        return r.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
