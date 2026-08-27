#!/usr/bin/env python3
"""render_thumb.py — F8 compositor (no-face).
Usage: python3 tools/render_thumb.py BASE.png OUT.jpg "LINE ONE" "LINE TWO" [pointsize]
"""
import os, subprocess, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
TMP = os.path.join(ROOT, "previews")
os.makedirs(TMP, exist_ok=True)

BASE, OUT, L1, L2 = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
FS = int(sys.argv[5]) if len(sys.argv) > 5 else 108
X, GAP, Y2 = 56, 16, 72
GOLD = "#F4C15D"

def run(args):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("MAGICK FAILED:\n" + (r.stderr or "")[-600:])

def label(text, path, fill, stroke_w):
    args = ["magick", "-background", "none", "-font", FONT, "-pointsize", str(FS), "-fill", fill]
    if stroke_w:
        args += ["-stroke", "#000000", "-strokewidth", str(stroke_w)]
    args += ["label:" + text, "-trim", "+repage", path]
    run(args)
    w, h = map(int, subprocess.check_output(["identify", "-format", "%w %h", path]).split())
    return w, h

w1, h1 = label(L1, f"{TMP}/l1.png", "#FFFFFF", 8)
w2, h2 = label(L2, f"{TMP}/l2.png", GOLD, 8)
label(L1, f"{TMP}/g1.png", "rgba(255,255,255,0.45)", 0)
label(L2, f"{TMP}/g2.png", "rgba(244,193,93,0.45)", 0)
run(["magick", f"{TMP}/g1.png", "-blur", "0x12", f"{TMP}/g1.png"])
run(["magick", f"{TMP}/g2.png", "-blur", "0x12", f"{TMP}/g2.png"])
print(f"'{L1}' {w1}x{h1} | '{L2}' {w2}x{h2} (limit 1150)")
assert w1 <= 1150 and w2 <= 1150, "F8 text too wide — shrink pointsize"

W = int(subprocess.check_output(["identify", "-format", "%w", BASE]).decode())
H = int(subprocess.check_output(["identify", "-format", "%h", BASE]).decode())
run(["magick", BASE,
     "(", "-size", f"{W}x{int(H*0.42)}", "gradient:rgba(11,31,51,0.92)-rgba(11,31,51,0)", "-flip", ")",
     "-gravity", "South", "-composite", f"{TMP}/scrim.png"])

Y1 = Y2 + h2 + GAP
cur = f"{TMP}/scrim.png"
for img, y in [(f"{TMP}/g2.png", Y2), (f"{TMP}/g1.png", Y1),
               (f"{TMP}/l2.png", Y2), (f"{TMP}/l1.png", Y1)]:
    nxt = f"{TMP}/step.png"
    run(["magick", cur, img, "-gravity", "SouthWest",
         "-geometry", f"+{X}+{y}", "-composite", nxt])
    cur = nxt
run(["magick", cur, "-resize", "1280x720!", "-quality", "92", OUT])
print("DONE", OUT)
