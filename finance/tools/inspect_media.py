#!/usr/bin/env python3
"""inspect.py — make video/image VISIBLE to the agent (and you).
Videos cannot be 'watched' as pixels by the model. This extracts stills
+ a contact sheet so we can read_file them and catch issues.

Usage:
  python3 tools/inspect.py VIDEO.mp4 [--times 0.3,2,5,8,12,16,20,24]
  python3 tools/inspect.py IMAGE.png
  python3 tools/inspect.py --sheet VIDEO.mp4   # 3x3 contact sheet only
Writes to previews/inspect/<stem>/
"""
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "previews" / "inspect"

def ff():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()

def run(args):
    r = subprocess.run(args, capture_output=True)
    if r.returncode != 0:
        raise SystemExit((r.stderr or b"")[-800:].decode("utf-8", "replace"))
    return r

def probe(path: Path):
    raw = subprocess.run(
        [ff(), "-i", str(path)], capture_output=True, text=True)
    err = raw.stderr or ""
    info = {"path": str(path), "bytes": path.stat().st_size, "log": []}
    for line in err.splitlines():
        if any(k in line for k in ("Duration", "Stream #", "Video:", "Audio:")):
            info["log"].append(line.strip())
    return info, err

def grab(video: Path, t: float, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    run([ff(), "-y", "-ss", f"{t:.3f}", "-i", str(video),
         "-frames:v", "1", "-q:v", "3", str(dest)])

def sheet(frames: list[Path], dest: Path, cols=3):
    from PIL import Image, ImageDraw, ImageFont
    if not frames:
        return
    ims = [Image.open(p).convert("RGB") for p in frames]
    w, h = 426, 240
    ims = [im.resize((w, h)) for im in ims]
    rows = (len(ims) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * w, rows * h + 8), (11, 31, 51))
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except Exception:
        font = ImageFont.load_default()
    for i, im in enumerate(ims):
        r, c = divmod(i, cols)
        canvas.paste(im, (c * w, r * h))
        draw.text((c * w + 6, r * h + 4), frames[i].stem,
                  fill=(244, 193, 93), font=font)
    dest.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(dest, quality=90)
    print("SHEET", dest)

def inspect_video(path: Path, times):
    stem = path.stem
    dest = OUT / stem
    dest.mkdir(parents=True, exist_ok=True)
    info, err = probe(path)
    (dest / "probe.txt").write_text("\n".join(info["log"]) + "\n\n" + err[-1500:])
    print("PROBE", path.name)
    for line in info["log"]:
        print(" ", line)
    frames = []
    for t in times:
        fp = dest / f"t{int(round(t * 10)):04d}.jpg"
        try:
            grab(path, t, fp)
            frames.append(fp)
            print(" FRAME", fp.name, fp.stat().st_size)
        except SystemExit as e:
            print(" skip", t, e)
    if frames:
        sheet(frames, dest / "CONTACT.jpg")
    (dest / "info.json").write_text(json.dumps(
        {"file": str(path), "times": times, "frames": [str(f) for f in frames]}, indent=2))
    return dest

def inspect_image(path: Path):
    dest = OUT / path.stem
    dest.mkdir(parents=True, exist_ok=True)
    from PIL import Image
    im = Image.open(path)
    print(f"IMAGE {path.name} {im.size} {im.mode}")
    # downscale copy for reading
    im2 = im.copy()
    im2.thumbnail((1280, 720))
    out = dest / "view.jpg"
    im2.convert("RGB").save(out, quality=90)
    print(" VIEW", out)
    return dest

if __name__ == "__main__":
    args = sys.argv[1:]
    times = [0.4, 2, 5, 8, 11, 14, 17, 20, 24, 28]
    if "--times" in args:
        i = args.index("--times")
        times = [float(x) for x in args[i + 1].split(",")]
        del args[i:i + 2]
    path = Path(args[-1])
    if path.suffix.lower() in {".mp4", ".mov", ".webm", ".mkv"}:
        inspect_video(path, times)
    else:
        inspect_image(path)
