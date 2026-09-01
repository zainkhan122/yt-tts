#!/usr/bin/env python3
"""Word-synced captions on E02 picture (no baked-in text to wipe)."""
from pathlib import Path
import shutil, subprocess
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

FF = imageio_ffmpeg.get_ffmpeg_exe()
SRC = Path("/tmp/e02_picture.mp4")
OUT = Path("/tmp/e02_final.mp4")
DEST = Path("/home/user/the-public-record/episodes/Quibi Raised $1.75 Billion. It Lasted Six Months") / "Quibi Raised $1.75 Billion. It Lasted Six Months.mp4"
WORK = Path("/tmp/e02caps")
WORK.mkdir(exist_ok=True)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
W, H = 1280, 720
T = 469.36

# Spoken-keyword starts from Vosk on this Kokoro bed.
CAPS = [
    ("QUIBI", 0.33),
    ("LOS ANGELES 2018", 2.85),
    ("$1.75 BILLION", 6.84),
    ("QUICK BITES", 54.42),
    ("$4.99", 118.56),
    ("PHONE ONLY", 191.43),
    ("TIKTOK WAS FREE", 207.96),
    ("WOULD YOU PAY", 222.66),
    ("DECEMBER 2020", 349.86),
    ("SIX MONTHS", 356.19),
    ("UNDER $100M", 390.39),
]


def holds(caps, default=2.6):
    out = []
    for i, (disp, t) in enumerate(caps):
        hold = default
        if i + 1 < len(caps):
            gap = caps[i + 1][1] - t
            if gap < default + 0.15:
                hold = max(1.15, gap - 0.15)
        out.append((disp, t, round(hold, 3)))
    return out


def make_cap(text, path):
    fnt = ImageFont.truetype(FONT, 44)
    im = Image.new("RGBA", (W, 110), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = (W - d.textlength(text, font=fnt)) / 2
    for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-3, -3), (3, 3)):
        d.text((x + dx, 28 + dy), text, font=fnt, fill=(0, 0, 0, 255))
    d.text((x, 28), text, font=fnt, fill=(244, 193, 93, 255))
    im.save(path)


def main():
    timed = holds(CAPS)
    print("CAPTIONS")
    for d, t, h in timed:
        print(f"  {t:7.2f}  {h:.2f}s  {d}")
    pngs = []
    for i, (disp, t, h) in enumerate(timed):
        p = WORK / f"c{i:02d}.png"
        make_cap(disp, p)
        pngs.append((p, t, h))
    cur = SRC
    BATCH = 6
    for bi in range(0, len(pngs), BATCH):
        group = pngs[bi:bi + BATCH]
        args = [FF, "-y", "-i", str(cur)]
        for p, t, h in group:
            args += ["-itsoffset", f"{t:.3f}", "-loop", "1", "-framerate", "24",
                     "-t", f"{h:.2f}", "-i", str(p)]
        parts = []
        last = "0:v"
        for j, _ in enumerate(group):
            parts.append(f"[{j+1}:v]format=rgba[c{j}]")
            parts.append(f"[{last}][c{j}]overlay=x=(W-w)/2:y=H-h-18:eof_action=pass[o{j}]")
            last = f"o{j}"
        out = WORK / f"ov_{bi:02d}.mp4"
        if bi + BATCH >= len(pngs):
            out = OUT
        args += ["-filter_complex", ";".join(parts),
                 "-map", f"[{last}]", "-map", "0:a:0",
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                 "-pix_fmt", "yuv420p", "-r", "24", "-c:a", "copy",
                 "-t", f"{T:.3f}", str(out)]
        print("batch", bi, "->", out)
        r = subprocess.run(args, capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(r.stderr[-1200:])
        if cur != SRC and cur.exists() and cur != out:
            cur.unlink()
        cur = out
    DEST.parent.mkdir(parents=True, exist_ok=True)
    if DEST.exists():
        DEST.unlink()
    shutil.copy2(OUT, DEST)
    print("FINAL", DEST, round(DEST.stat().st_size / 1e6, 1), "MB")


if __name__ == "__main__":
    main()
