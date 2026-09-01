#!/usr/bin/env python3
"""Native 9:16 short. L5 max 6.5s. NO legal overlay.
Usage: python3 tools/cut_short.py SHORT_DIR VOICE BROLL_DIR OUT.mp4
"""
from __future__ import annotations
import json, random, subprocess, sys
from pathlib import Path

EP = Path(sys.argv[1])
VOICE = Path(sys.argv[2])
B = Path(sys.argv[3])
OUT = Path(sys.argv[4])
WORK = Path("/tmp/cut_short")
WORK.mkdir(parents=True, exist_ok=True)
W, H, FPS = 720, 1280, 24
MAX_SHOT = 6.5


def ff():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def run(args):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("FAIL\n" + (r.stderr or "")[-900:])
    return r


def dur(p):
    err = subprocess.run([ff(), "-i", str(p)], capture_output=True, text=True).stderr
    for line in err.splitlines():
        if "Duration" in line and "N/A" not in line:
            hms = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = hms.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 0.0


def grade(shot_len):
    fo = max(shot_len - 0.22, 0.4)
    return (
        f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS},"
        f"eq=brightness='0.012*sin(2*PI*t/4.8)':contrast=1.06:saturation=0.94,"
        f"vignette=PI/5.8,noise=alls=4:allf=t,"
        f"fade=t=in:st=0:d=0.18,fade=t=out:st={fo:.2f}:d=0.20,format=yuv420p"
    )


def main():
    T = dur(VOICE)
    videos = sorted(B.glob("*.mp4"))
    stills = sorted((EP / "assets").glob("*.jpg")) if (EP / "assets").exists() else []
    n = len(videos) + len(stills)
    need = T / MAX_SHOT
    print(f"T={T:.1f} video={len(videos)} still={len(stills)} need≥{need:.0f}")
    if n < need - 1:
        sys.exit(f"L5 FAIL: {n} unique assets cannot fill {T:.0f}s")
    vlen = min(MAX_SHOT, max(4.0, T / max(n, 1)))
    rng = random.Random(sum(ord(c) for c in str(OUT)) & 0xFFFFFFFF)
    seq, t, used = [], 0.0, set()
    while t < T - 0.25:
        unused = [p for p in videos if str(p) not in used]
        if not unused:
            extra = T - t
            if extra > 0.4 and seq:
                room = MAX_SHOT - seq[-1]["len"]
                if room > 0.3:
                    take = min(extra, room)
                    seq[-1]["len"] = round(seq[-1]["len"] + take, 3)
                    t += take
                if t < T - 0.5:
                    sys.exit(f"L5 FAIL: ran out of unique shots at t={t:.1f}/{T:.1f}")
            break
        rng.shuffle(unused)
        clip = unused[0]
        src_d = dur(clip)
        sl = min(vlen, MAX_SHOT, T - t, max(src_d - 0.15, 0.5))
        if sl < 2.0:
            used.add(str(clip))
            continue
        seq.append({"kind": "video", "src": str(clip), "len": round(sl, 3), "t": round(t, 2)})
        used.add(str(clip))
        t += sl
    print(f"SEQ {len(seq)} t={t:.1f} max={max(s['len'] for s in seq):.2f}")
    paths = []
    for i, s in enumerate(seq):
        dest = WORK / f"s{i:03d}.mp4"
        print(f"  {i:03d} {s['len']:.2f}s {Path(s['src']).name}", flush=True)
        # NO -stream_loop. Shot must fit inside the source.
        run([ff(), "-y", "-i", str(s["src"]), "-t", f"{s['len']:.3f}",
             "-vf", grade(s["len"]), "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
             "-pix_fmt", "yuv420p", "-r", str(FPS), "-an", str(dest)])
        paths.append(dest)
    lst = WORK / "vlist.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in paths))
    silent = WORK / "silent.mp4"
    run([ff(), "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
         "-pix_fmt", "yuv420p", "-r", str(FPS), "-an", str(silent)])
    run([ff(), "-y", "-i", str(silent), "-i", str(VOICE),
         "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "96k",
         "-t", f"{T:.3f}", "-movflags", "+faststart", str(OUT)])
    print("SHORT", OUT, round(OUT.stat().st_size / 1e6, 1), "MB")
    for p in WORK.glob("s*.mp4"):
        p.unlink()
    silent.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
