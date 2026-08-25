#!/usr/bin/env python3
"""render_thumb16.py v2 — thumbnail compositor (R8).
Fixes: (a) geometry applied per -composite operator (v1 lost line 2),
(b) glow drawn at 50% alpha WITHOUT stroke (v1 glow was a solid white ghost),
(c) magick via argv list only (the proven make_caption pattern)."""
import subprocess

TH = "/home/user/thumbnails"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
BASE = f"{TH}/video_016_base.jpg"
OUT  = f"{TH}/video_016_cover.jpg"
L1, L2 = "NOT LAZY.", "DEPLETED."
FS, X, GAP, Y2 = 118, 56, 18, 96

def run(args):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("MAGICK FAILED:\n" + r.stderr[-600:])

def label(text, path, fill, stroke_w):
    args = ["magick", "-background", "none", "-font", FONT, "-pointsize", str(FS),
            "-fill", fill]
    if stroke_w:
        args += ["-stroke", "#000000", "-strokewidth", str(stroke_w)]
    args += ["label:" + text, "-trim", "+repage", path]
    run(args)
    w, h = map(int, subprocess.check_output(
        ["identify", "-format", "%w %h", path]).split())
    return w, h

w1, h1 = label(L1, f"{TH}/l1.png", "#FFFFFF", 9)
w2, h2 = label(L2, f"{TH}/l2.png", "#FFFFFF", 9)
label(L1, f"{TH}/g1.png", "rgba(255,255,255,0.5)", 0)
label(L2, f"{TH}/g2.png", "rgba(255,255,255,0.5)", 0)
run(["magick", f"{TH}/g1.png", "-blur", "0x14", f"{TH}/g1.png"])
run(["magick", f"{TH}/g2.png", "-blur", "0x14", f"{TH}/g2.png"])
print(f"'{L1}' {w1}x{h1} | '{L2}' {w2}x{h2} (limit 1150)")
assert w1 <= 1150 and w2 <= 1150

Y1 = Y2 + h2 + GAP

# scrim
run(["magick", BASE,
     "(", "-size", "1280x320", "gradient:rgba(0,0,0,0.88)-rgba(0,0,0,0)", "-flip", ")",
     "-gravity", "South", "-composite",
     "(", "-size", "720x500", "gradient:rgba(0,0,0,0.55)-rgba(0,0,0,0)", ")",
     "-gravity", "SouthWest", "-composite",
     f"{TH}/scrim.png"])

# sequential composites: geometry as operator setting, one overlay at a time
cur = f"{TH}/scrim.png"
for img, y in [(f"{TH}/g2.png", Y2), (f"{TH}/g1.png", Y1),
               (f"{TH}/l2.png", Y2), (f"{TH}/l1.png", Y1)]:
    nxt = f"{TH}/step.png"
    run(["magick", cur, img, "-gravity", "SouthWest",
         "-geometry", f"+{X}+{y}", "-composite", nxt])
    cur = nxt
run(["magick", cur, "-quality", "92", OUT])

# objective verification
for name, y, w, h in [(L1, Y1, w1, h1), (L2, Y2, w2, h2)]:
    top = 720 - y - h
    cov = subprocess.check_output(
        ["magick", OUT, "-crop", f"{w}x{h}+{X}+{top}", "-colorspace", "gray",
         "-threshold", "92%", "-format", "%[fx:mean]", "info:"]).decode()
    print(f"  coverage '{name}': {cov}")
print("DONE", OUT)
