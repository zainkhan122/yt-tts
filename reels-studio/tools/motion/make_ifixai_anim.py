#!/usr/bin/env python3
"""Animated graphics for the iFixAi video: plan points that use visual kind "animation", and the catch.

Each graphic is a 1080x1920 clip (30 fps, 14 s) with its own heading, sub-line and motion. Every label
is read from videos/<id>/plan.json, so the wording stays the plan's. Nothing about the tool is written
here. No figures are drawn: the plan rule is no exact figures on screen.

Also writes captures/<id>/cover-hero.jpg: an own graphic (a crop of the point-1 findings card), replacing
the maker's chart, which carried a figure.

Outputs:
  captures/<id>/anim-point<n>.mp4   for each point with visual kind "animation"
  captures/<id>/anim-catch.mp4      for plan["catch_visual"]
  captures/<id>/cover-hero.jpg

Usage: python3 tools/motion/make_ifixai_anim.py videos/<id>/plan.json
"""
import json
import math
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
HEAD = ROOT / "templates" / "_base" / "fonts" / "Anton.ttf"
TEXT = ROOT / "templates" / "_base" / "fonts" / "Inter.ttf"
# Square canvas: the renderer shows square footage as a full 960-wide card (phone-tall footage is a narrow card).
W, H, FPS, DUR = 1080, 1080, 30, 14.0
SX, SY, SW, SH = 60, 320, 960, 700          # the graphic stage inside the canvas
BG_TOP, BG_BOT = (14, 20, 36), (9, 12, 22)
WHITE, MUTED, ACCENT = (255, 255, 255), (150, 160, 180), (250, 204, 21)
GREEN, BLUE, RED = (74, 222, 128), (96, 165, 250), (248, 113, 113)
CARD, DARK = (22, 28, 44), (11, 15, 26)


def font(path, size):
    return ImageFont.truetype(str(path), size)


def fit_head(text, width, start=124, minimum=60):
    size = start
    while size > minimum and font(HEAD, size).getlength(text) > width:
        size -= 4
    return font(HEAD, size), size


def wrap(text, fnt, width):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if fnt.getlength(t) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def prog(t, start, dur=0.6):
    return ease((t - start) / dur)


def layer(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def put(base, im, x, y, alpha=1.0):
    """Composite im onto the frame at stage offset (x, y), scaled by alpha (0..1)."""
    if alpha <= 0:
        return
    if alpha < 1:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    base.alpha_composite(im, (int(SX + x), int(SY + y)))


def card(w, h, fill=CARD, outline=None, width=4, radius=24):
    im = layer(w, h)
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=fill,
                                         outline=outline, width=width if outline else 0)
    return im


def text_img(s, fnt, fill):
    w = int(fnt.getlength(s)) + 4
    im = layer(w, fnt.size + 20)
    ImageDraw.Draw(im).text((0, 0), s, font=fnt, fill=fill + (255,))
    return im


def tick(d, cx, cy, r, color, p):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color + (255,))
    if p > 0.5:
        d.line((cx - r * 0.5, cy, cx - r * 0.1, cy + r * 0.45), fill=DARK + (255,), width=5)
        d.line((cx - r * 0.1, cy + r * 0.45, cx + r * 0.55, cy - r * 0.4), fill=DARK + (255,), width=5)


def arrow(base, p0, p1, t, color, grow=1.0, speed=150):
    """Arrow from p0 to p1 in stage coordinates. It draws in over `grow`, then dots flow along it."""
    im = layer(SW, SH)
    d = ImageDraw.Draw(im)
    x0, y0 = p0
    x1, y1 = p1
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    ex, ey = x0 + (x1 - x0) * grow, y0 + (y1 - y0) * grow
    d.line((x0, y0, ex, ey), fill=color + (255,), width=6)
    if grow >= 1.0:
        nx, ny = -uy, ux
        d.polygon([(x1, y1), (x1 - ux * 26 + nx * 14, y1 - uy * 26 + ny * 14),
                   (x1 - ux * 26 - nx * 14, y1 - uy * 26 - ny * 14)], fill=color + (255,))
        s = (t * speed) % 80
        k = 0
        while s + k * 80 < L - 30:
            dd = s + k * 80
            cx, cy = x0 + ux * dd, y0 + uy * dd
            d.ellipse((cx - 7, cy - 7, cx + 7, cy + 7), fill=color + (255,))
            k += 1
    put(base, im, 0, 0)


def pulse(t, period=2.0):
    return 0.5 + 0.5 * math.sin(2 * math.pi * t / period)


def background():
    bg = Image.new("RGB", (W, H), BG_TOP)
    d = ImageDraw.Draw(bg)
    for y in range(H):
        k = y / (H - 1)
        d.line((0, y, W, y), fill=tuple(round(BG_TOP[i] + (BG_BOT[i] - BG_TOP[i]) * k) for i in range(3)))
    return bg.convert("RGBA")


def header(base, title, sub):
    """Heading and sub-line drawn inside the clip (captions stay on, as the other scenes have them)."""
    hf, _ = fit_head(title, 960)
    d = ImageDraw.Draw(base)
    d.rectangle((60, 60, 260, 68), fill=ACCENT)
    d.text((60, 90), title, font=hf, fill=WHITE)
    sf = font(TEXT, 40)
    y = 90 + hf.size + 22
    for line in wrap(sub, sf, 960):
        d.text((60, y), line, font=sf, fill=MUTED)
        y += 50


def scene_point4(base, t):
    """Free to run yourself: your model keys and your machine, the engine runs on it."""
    p_m = prog(t, 0.3)
    m = card(600, 300, fill=CARD, outline=BLUE, width=4)
    md = ImageDraw.Draw(m)
    md.text((40, 30), "YOUR MACHINE", font=font(HEAD, 56), fill=MUTED + (255,))
    pill = card(520, 70, fill=DARK, outline=GREEN, width=4, radius=35)
    ImageDraw.Draw(pill).text((36, 16), "Open-source engine", font=font(TEXT, 40), fill=WHITE + (255,))
    m.alpha_composite(pill, (40, 150))
    scan_y = 40 + int(((t % 3.0) / 3.0) * 240)
    ImageDraw.Draw(m).line((20, scan_y, 580, scan_y), fill=GREEN + (120,), width=3)
    put(base, m, 180 + (1 - p_m) * 0, 40 + (1 - p_m) * 40, p_m)

    p_k = prog(t, 1.0)
    k = card(340, 110, fill=CARD, outline=ACCENT, width=4)
    ImageDraw.Draw(k).text((28, 34), "Your model keys", font=font(TEXT, 38), fill=WHITE + (255,))
    put(base, k, 0 - (1 - p_k) * 40, 448, p_k)

    grow = prog(t, 1.8, 0.8)
    arrow(base, (150, 448), (300, 348), t, ACCENT, grow=grow)

    p_b = prog(t, 2.6)
    b = card(960, 110, fill=CARD, outline=GREEN, width=4 + int(pulse(t) * 2), radius=55)
    bd = ImageDraw.Draw(b)
    bd.text((48, 30), "FREE", font=font(HEAD, 52), fill=GREEN + (255,))
    bd.text((220, 36), "your machine, your model keys", font=font(TEXT, 40), fill=WHITE + (255,))
    put(base, b, 0, 580 + (1 - p_b) * 30, p_b)


def scene_point5(base, t):
    """Side by side: the free engine on the left, the paid hosted tier on the right."""
    left = [("Runs on your machine", 1.0), ("Your own model keys", 1.6)]
    right = [("Hosted audits", 2.4), ("Reports", 3.0), ("Paid per agent", 3.6)]
    for col, (x, title, colr, items, label) in enumerate([
            (0, "FREE", GREEN, left, "Open-source engine"),
            (500, "PAID", BLUE, right, "Hosted audits and reports")]):
        p = prog(t, 0.2 + col * 0.25, 0.7)
        active = pulse(t - col * 1.5, 3.0)
        c = card(460, 520, fill=CARD, outline=colr, width=4 + int(active * 3), radius=28)
        cd = ImageDraw.Draw(c)
        cd.text((40, 34), title, font=font(HEAD, 110), fill=colr + (255,))
        for line_i, line in enumerate(wrap(label, font(TEXT, 40), 380)):
            cd.text((40, 170 + line_i * 48), line, font=font(TEXT, 40), fill=WHITE + (255,))
        for i, (txt, at) in enumerate(items):
            yy = 300 + i * 70
            q = prog(t, at, 0.4)
            tick(cd, 62, yy + 22, 20, colr, q)
            cd.text((100, yy), txt, font=font(TEXT, 30), fill=WHITE + (int(255 * q),))
        put(base, c, x, 40 + (1 - p) * 60, p)

    p_bar = prog(t, 4.2)
    bar = card(960, 120, fill=DARK, outline=ACCENT, width=3, radius=30)
    ImageDraw.Draw(bar).text((40, 40), "The engine is the free part.", font=font(TEXT, 42), fill=WHITE + (255,))
    put(base, bar, 0, 580 + (1 - p_bar) * 30, p_bar)


def scene_catch(base, t):
    """The catch: the agent connects to a free self-hosted engine, and hosted audits sit behind a paid tier."""
    p_a = prog(t, 0.2)
    a = card(440, 120, fill=CARD, outline=WHITE, width=3, radius=28)
    ImageDraw.Draw(a).text((40, 36), "Your agent", font=font(TEXT, 44), fill=WHITE + (255,))
    put(base, a, 260, 20 + (1 - p_a) * 30, p_a)

    arrow(base, (320, 140), (230, 300), t, GREEN, grow=prog(t, 1.0, 0.7))
    arrow(base, (640, 140), (730, 300), t, BLUE, grow=prog(t, 1.4, 0.7))

    p_l = prog(t, 1.6)
    l = card(440, 160, fill=CARD, outline=GREEN, width=4, radius=28)
    ld = ImageDraw.Draw(l)
    ld.text((36, 26), "Open-source engine", font=font(TEXT, 40), fill=WHITE + (255,))
    ld.text((36, 84), "FREE · your machine", font=font(TEXT, 32), fill=GREEN + (255,))
    put(base, l, 0, 300, p_l)

    p_r = prog(t, 2.2)
    r = card(440, 200, fill=CARD, outline=ACCENT, width=4 + int(pulse(t, 2.0) * 2), radius=28)
    rd = ImageDraw.Draw(r)
    rd.text((36, 26), "Hosted audits", font=font(TEXT, 40), fill=WHITE + (255,))
    rd.text((36, 84), "and reports", font=font(TEXT, 40), fill=WHITE + (255,))
    put(base, r, 520, 300, p_r)
    badge = card(200, 70, fill=ACCENT, radius=35)
    ImageDraw.Draw(badge).text((50, 8), "PAID", font=font(HEAD, 48), fill=DARK + (255,))
    bump = 1.0 + 0.04 * pulse(t, 1.6)
    badge = badge.resize((int(200 * bump), int(70 * bump)))
    put(base, badge, 520 + 440 - 200 * bump, 250 + (70 - 70 * bump) / 2, p_r)

    p_s = prog(t, 3.4)
    s = card(960, 120, fill=DARK, outline=GREEN, width=3, radius=30)
    ImageDraw.Draw(s).text((40, 40), "Self-hosted, with your own model keys.", font=font(TEXT, 40),
                           fill=WHITE + (255,))
    put(base, s, 0, 540 + (1 - p_s) * 30, p_s)


SCENES = {
    "point4": ("FREE TO RUN YOURSELF", scene_point4),
    "point5": ("FREE ENGINE, PAID AUDITS", scene_point5),
    "catch": ("THE CATCH", scene_catch),
}


def encode(out_path, title, sub, fn):
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16",
           "-preset", "medium", "-movflags", "+faststart", str(out_path)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    bg = background()
    n = round(DUR * FPS)
    for i in range(n):
        t = i / FPS
        frame = bg.copy()
        header(frame, title, sub)
        fn(frame, t)
        proc.stdin.write(frame.convert("RGB").tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise SystemExit(f"ffmpeg failed for {out_path}")


def build(plan_path):
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    vid = plan["id"]
    cap = ROOT / "captures" / vid
    cap.mkdir(parents=True, exist_ok=True)
    jobs = []
    for p in plan["points"]:
        vis = p.get("visual") or {}
        if vis.get("kind") == "animation":
            key = f"point{p['n']}"
            jobs.append((key, cap / vis["animation"], p["title"].upper(), p["sub"], SCENES[key][1]))
    cv = plan.get("catch_visual") or {}
    if cv.get("kind") == "animation":
        jobs.append(("catch", cap / cv["animation"], "THE CATCH", plan["catch_sub"], scene_catch))
    for key, out, title, sub, fn in jobs:
        encode(out, title, sub, fn)
        print("wrote", out.relative_to(ROOT), f"{DUR:.0f}s")
    # Cover hero: own graphic (crop of the point-1 findings card). No maker chart, no figure.
    src = Image.open(cap / "plan-1.jpg").convert("RGB")
    crop = src.crop((0, 360, W, 360 + 650)).resize((1321, 795), Image.LANCZOS)
    crop.save(cap / "cover-hero.jpg", quality=92)
    print("wrote", (cap / "cover-hero.jpg").relative_to(ROOT))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    build(sys.argv[1])
