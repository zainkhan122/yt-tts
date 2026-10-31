#!/usr/bin/env python3
"""Motion graphic for claude-mem: record -> compress -> recall, drawn as a loop.

Writes an RGBA frame sequence (1080x300) for the diagram band, then composes a
1080x1920 reel clip with the tool's OWN animation (cm-preview.mp4, scaled to full frame width,
the diagram below it) above the diagram. Vector text stays crisp; the tool
media keeps its native pixels.

Usage: python3 tools/motion/claude_mem_loop.py
Output: captures/repo-claude-mem-01/loop-scene.mp4 (1080x1920, 30 fps)
"""
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
CAP = ROOT / "captures" / "repo-claude-mem-01"
FONT = ROOT / "templates" / "_base" / "fonts" / "Anton.ttf"
FF = "/home/user/.local/lib/python3.13/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
FPS = 30
PERIOD = 3.0                       # one full loop, seconds
DUR = 21.1                         # the tool's own animation length
N = round(DUR * FPS)
ACCENT = (250, 204, 21)
BLUE = (56, 189, 248)
WHITE = (255, 255, 255)
MUTED = (150, 160, 180)
BAND_H = 300
NODES = [("RECORD", "each session"), ("COMPRESS", "decisions, fixes"), ("RECALL", "next session")]
XS = [200, 540, 880]
CY = 120


def font(size):
    return ImageFont.truetype(str(FONT), size)


def frame(i, tmp):
    t = (i / FPS) % PERIOD / PERIOD            # 0..1 across the loop
    im = Image.new("RGBA", (1080, BAND_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # path
    d.line((XS[0], CY, XS[-1], CY), fill=(255, 255, 255, 60), width=6)
    # pulse position: 0-0.5 travels record->compress, 0.5-1 compress->recall, then holds
    seg = min(1.0, t * 2) if t < 0.5 else 1.0
    if t < 0.5:
        px = XS[0] + (XS[1] - XS[0]) * min(1.0, t * 2)
        active = 0
    else:
        px = XS[1] + (XS[2] - XS[1]) * min(1.0, (t - 0.5) * 2)
        active = 1
    if t >= 0.85:                       # short hold at RECALL, then reset
        active = 2
        px = XS[2]
    d.line((XS[0], CY, px, CY), fill=ACCENT, width=6)
    # nodes
    for k, (x, (name, sub)) in enumerate(zip(XS, NODES)):
        lit = k <= active
        glow = 22 if k == active else 0
        if glow:
            d.ellipse((x - 46 - glow, CY - 46 - glow, x + 46 + glow, CY + 46 + glow), fill=(250, 204, 21, 60))
        d.ellipse((x - 46, CY - 46, x + 46, CY + 46), fill=(15, 20, 32, 255),
                  outline=ACCENT if lit else (255, 255, 255, 90), width=5)
        d.text((x, CY), str(k + 1), font=font(44), fill=ACCENT if lit else MUTED, anchor="mm")
        d.text((x, CY + 80), name, font=font(44), fill=WHITE if lit else MUTED, anchor="mm")
        d.text((x, CY + 124), sub, font=font(30), fill=MUTED, anchor="mm")
    # travelling dot
    d.ellipse((px - 11, CY - 11, px + 11, CY + 11), fill=BLUE)
    im.save(tmp / f"f{i:04d}.png")


def main():
    tmp = CAP / "_loop_frames"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    for i in range(N):
        frame(i, tmp)

    bg = Image.new("RGB", (1080, 1920), (11, 15, 26))
    bg.save(tmp / "bg.png")
    out = CAP / "loop-scene.mp4"
    cmd = [
        FF, "-y", "-loglevel", "error",
        "-loop", "1", "-framerate", str(FPS), "-i", str(tmp / "bg.png"),
        "-i", str(CAP / "cm-preview.mp4"),
        "-framerate", str(FPS), "-i", str(tmp / "f%04d.png"),
        "-filter_complex",
        "[1:v]scale=1080:608:flags=lanczos,fps=30[t];"
        "[0:v][t]overlay=0:470:shortest=1[a];"
        "[a][2:v]overlay=0:1120:shortest=1,format=yuv420p[v]",
        "-map", "[v]", "-t", f"{DUR}", "-r", str(FPS),
        "-c:v", "libx264", "-crf", "18", "-preset", "medium", str(out),
    ]
    subprocess.run(cmd, check=True)
    shutil.rmtree(tmp)
    print("wrote", out.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
