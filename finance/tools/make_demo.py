#!/usr/bin/env python3
"""45s silent demo: stat card + growing bars + slope line + end card. Mux audio later."""
import json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import motion_kit as mk

OUT = ROOT / "output"
DEMO = OUT / "demo"
DEMO.mkdir(parents=True, exist_ok=True)
TOK = json.loads((ROOT / "brand/tokens.json").read_text())
C, CH = TOK["colors"], TOK["chart"]

def ff():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()

def run(args):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("CMD FAIL\n" + " ".join(args[:6]) + "\n" + (r.stderr or "")[-800:])
    return r

def grow_bars(dest: Path, n=36):
    plt, fp = mk._mpl()
    labels = ["$0", "$5k", "$20k", "$100k"]
    full = [0, 5, 20, 100]
    dest.mkdir(exist_ok=True)
    for i in range(n):
        t = (i + 1) / n
        ease = t * t * (3 - 2 * t)
        vals = [v * ease for v in full]
        fig, ax = plt.subplots(figsize=(12.8, 7.2))
        ax.bar(labels, vals, color=CH["bar"], width=0.62)
        ax.set_ylim(0, 110)
        ax.set_title("The ladder is not the flex. The slope is.", fontproperties=fp, fontsize=20, pad=14)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.yaxis.grid(True, linestyle="--", alpha=0.35)
        ax.set_axisbelow(True)
        if t > 0.55:
            ax.annotate("first threshold", xy=(2, 20), xytext=(1.15, 55),
                        color=C["gold"], fontsize=11,
                        arrowprops=dict(arrowstyle="->", color=C["gold"]))
        ax.text(0, -0.12, "Illustration, not a recommendation. Education only.",
                transform=ax.transAxes, fontsize=8, color=C["muted"])
        fig.tight_layout()
        fig.savefig(dest / f"f{i:03d}.png", bbox_inches="tight", pad_inches=0.3)
        plt.close()
    mp4 = dest / "grow.mp4"
    run([ff(), "-y", "-framerate", "18", "-i", str(dest / "f%03d.png"),
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", str(mp4)])
    return mp4

def still_clip(img: Path, seconds: float, out: Path, zoom=False):
    frames = max(int(seconds * 30), 2)
    vf = "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,format=yuv420p"
    if zoom:
        vf = ("scale=1400:788,zoompan=z='min(zoom+0.0008,1.08)':x='iw/2-(iw/zoom/2)':"
              "y='ih/2-(ih/zoom/2)':d=%d:s=1280x720:fps=30,format=yuv420p" % (frames + 8))
    run([ff(), "-y", "-loop", "1", "-i", str(img), "-vf", vf, "-t", f"{seconds:.2f}",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", str(out)])

def burn_captions(src: Path, dst: Path, cues):
    """cues = [(start, end, text)]"""
    font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    parts = []
    for i, (a, b, text) in enumerate(cues):
        safe = text.replace("'", "\u2019")
        parts.append(
            f"drawtext=fontfile={font}:text='{safe}':fontsize=42:fontcolor=white:"
            f"borderw=3:bordercolor=black:x=(w-text_w)/2:y=h-90:"
            f"enable='between(t,{a},{b})'"
        )
    vf = ",".join(parts)
    run([ff(), "-y", "-i", str(src), "-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p", str(dst)])

def concat(clips, out):
    lst = DEMO / "list.txt"
    lst.write_text("".join(f"file '{c}'\n" for c in clips))
    run([ff(), "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", str(out)])

def mux(video: Path, audio: Path, out: Path):
    run([ff(), "-y", "-i", str(video), "-i", str(audio),
         "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", str(out)])

def main():
    mk.stat(OUT / "demo_stat.png", "$20,000", "NOT RICH. THE FIRST TOOL.",
            "Education only. Not financial advice.")
    mk.line(OUT / "demo_slope.png", "After the threshold, time is invited to the meeting",
            [0, 0.2, 0.5, 1.2, 2.6, 4.8, 8.0],
            "Illustration of slope — not a projected return.")
    mk.stat(OUT / "demo_end.png", "THRESHOLD", "THE RULES OF MONEY, SHOWN.",
            "threshold  ·  education, not advice")

    grow = grow_bars(DEMO / "frames")
    c1 = DEMO / "s1.mp4"; still_clip(OUT / "demo_stat.png", 6.0, c1, zoom=True)
    c2 = DEMO / "s2.mp4"
    run([ff(), "-y", "-i", str(grow), "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,"
         "pad=1280:720:(ow-iw)/2:(oh-ih)/2,format=yuv420p", "-c:v", "libx264", str(c2)])
    c3 = DEMO / "s3.mp4"; still_clip(OUT / "demo_slope.png", 8.0, c3, zoom=True)
    c4 = DEMO / "s4.mp4"; still_clip(OUT / "demo_end.png", 5.0, c4, zoom=False)

    silent = OUT / "demo_silent.mp4"
    concat([c1, c2, c3, c4], silent)
    captioned = OUT / "demo_silent_captioned.mp4"
    burn_captions(silent, captioned, [
        (0.2, 5.5, "$20,000"),
        (6.0, 10.5, "THE LADDER"),
        (11.0, 14.0, "FIRST THRESHOLD"),
        (15.0, 22.0, "THE SLOPE"),
        (23.0, 28.0, "NOT FINANCIAL ADVICE"),
    ])
    # probe
    info = subprocess.check_output(
        [ff().replace("ffmpeg", "ffprobe") if False else ff(), "-i", str(captioned)],
        stderr=subprocess.STDOUT, text=True, errors="replace")
    # ffmpeg prints duration on stderr when used as probe; use identify via ffmpeg
    p = subprocess.run([ff(), "-i", str(captioned)], capture_output=True, text=True)
    print("DEMO", captioned)
    print((p.stderr or "")[-400:])
    print("bytes", captioned.stat().st_size)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "mux":
        mux(Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]))
    else:
        main()
