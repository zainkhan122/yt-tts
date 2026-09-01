#!/usr/bin/env python3
"""Long-form cut.
L5: no shot > 6.5s. NEVER loop a clip (shot <= source minus 0.15s).
Vary length. At most 2 videos in a row. Do not sit two near-ID lives adjacent.
Usage: python3 tools/cut_long.py EPISODE_DIR VOICE.m4a [BROLL_DIR]
"""
from __future__ import annotations
import json, random, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EP = Path(sys.argv[1])
VOICE = Path(sys.argv[2])
A = EP / "assets"
B = Path(sys.argv[3]) if len(sys.argv) > 3 else (EP / "broll")
ART = EP / "artifacts"
WORK = Path("/tmp/cut_long")
WORK.mkdir(parents=True, exist_ok=True)
W, H, FPS = 1280, 720, 24
MAX_SHOT = 6.5
MIN_SHOT = 4.2
LENGTHS = (4.4, 5.0, 5.6, 6.3, 4.7, 5.3, 6.0, 4.9, 5.8, 6.4)

MOTIONS = [
    ("zin", 1.00, 1.16, 0.50, 0.50, 0.50, 0.50),
    ("zout", 1.16, 1.02, 0.50, 0.50, 0.50, 0.50),
    ("panlr", 1.10, 1.10, 0.14, 0.50, 0.86, 0.50),
    ("panrl", 1.10, 1.10, 0.86, 0.50, 0.14, 0.50),
    ("diag", 1.04, 1.14, 0.20, 0.24, 0.70, 0.56),
    ("settle", 1.18, 1.03, 0.50, 0.50, 0.50, 0.50),
]


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


def live_num(p: Path) -> int | None:
    m = re.search(r"live_(\d+)", p.name)
    return int(m.group(1)) if m else None


def grade(shot_len):
    fo = max(shot_len - 0.22, 0.4)
    return (
        f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS},"
        f"eq=brightness='0.010*sin(2*PI*t/5.1)':contrast=1.05:saturation=0.95,"
        f"vignette=PI/5.4,noise=alls=3:allf=t,"
        f"fade=t=in:st=0:d=0.14,fade=t=out:st={fo:.2f}:d=0.18,format=yuv420p"
    )


def x264():
    return ["-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
            "-pix_fmt", "yuv420p", "-r", str(FPS), "-an"]


def encode_video(src, dest, shot_len, ss=0.0):
    # NO -stream_loop. Ever.
    run([ff(), "-y", "-ss", f"{ss:.3f}", "-i", str(src), "-t", f"{shot_len:.3f}",
         "-vf", grade(shot_len)] + x264() + [str(dest)])


def encode_still(src, dest, shot_len, motion):
    name, zs, ze, px0, py0, px1, py1 = motion
    Nf = int(round(shot_len * FPS))
    zexpr = f"{zs}+({ze}-{zs})*on/{Nf}"
    x = f"(iw-iw/zoom)*({px0}+({px1}-{px0})*on/{Nf})"
    y = f"(ih-ih/zoom)*({py0}+({py1}-{py0})*on/{Nf})"
    fo = max(shot_len - 0.22, 0.4)
    vf = (
        f"scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1,"
        f"zoompan=z='{zexpr}':x='{x}':y='{y}':d={Nf}:s={W}x{H}:fps={FPS},"
        f"eq=contrast=1.05:saturation=0.95,vignette=PI/5.4,noise=alls=4:allf=t,"
        f"fade=t=in:st=0:d=0.14,fade=t=out:st={fo:.2f}:d=0.18,format=yuv420p"
    )
    run([ff(), "-y", "-loop", "1", "-i", str(src), "-vf", vf, "-frames:v", str(Nf)]
        + x264() + [str(dest)])


def main():
    T = dur(VOICE)
    videos = sorted(B.glob("*.mp4"))
    stills = sorted(A.glob("*.jpg")) + sorted(A.glob("*.png"))
    stills += sorted(ART.glob("*.jpg")) + sorted(ART.glob("*.png"))
    stills = [p for p in stills if "thumb" not in p.name.lower()]
    vmeta = []
    for p in videos:
        d = dur(p)
        if d < MIN_SHOT - 0.4:
            print("skip short clip", p.name, d)
            continue
        vmeta.append({"kind": "video", "src": p, "dur": d, "num": live_num(p)})
    print(f"T={T:.1f} video={len(vmeta)} still={len(stills)}")
    vcap = sum(min(MAX_SHOT, max(MIN_SHOT, m["dur"] - 0.18)) for m in vmeta)
    scap = len(stills) * 5.4
    print(f"capacity video={vcap:.0f}s still={scap:.0f}s")
    if vcap + scap < T - 2:
        sys.exit(f"L5 FAIL: {vcap+scap:.0f}s of unique (no-loop) picture < {T:.0f}s. Fetch more/longer B-roll.")

    rng = random.Random(13)
    rng.shuffle(vmeta)
    still_pool = [{"kind": "still", "src": p, "dur": 99.0, "num": None} for p in stills]
    rng.shuffle(still_pool)

    seq, t, prev_m = [], 0.0, None
    # If this film has a thumb object on disk, open on it (2–4.7s). Not a 10s ritual.
    open_still = EP / "thumb_base.jpg"
    if open_still.exists():
        seq.append({"kind": "still", "src": str(open_still), "len": 4.6, "t": 0.0,
                    "motion": MOTIONS[0]})
        t = 4.6
        prev_m = MOTIONS[0]
        still_pool = [s for s in still_pool if Path(s["src"]).resolve() != open_still.resolve()]
    s_i = 0
    v_run = 0
    last_num = None
    li = 0

    def motion():
        nonlocal prev_m
        c = [m for m in MOTIONS if m is not prev_m]
        prev_m = rng.choice(c)
        return prev_m

    def take_video():
        if not vmeta:
            return None
        for k in range(min(8, len(vmeta))):
            n = vmeta[k]["num"]
            if last_num is not None and n is not None and abs(n - last_num) <= 2:
                continue
            return vmeta.pop(k)
        return vmeta.pop(0)

    while t < T - 0.2:
        want_still = (v_run >= 2 or (seq and seq[-1]["kind"] == "video" and rng.random() < 0.35))
        item = None
        if want_still and s_i < len(still_pool):
            item = still_pool[s_i]
            s_i += 1
            v_run = 0
        else:
            item = take_video()
            if item is None and s_i < len(still_pool):
                item = still_pool[s_i]
                s_i += 1
                v_run = 0
            elif item is None:
                break
            else:
                v_run += 1
                last_num = item.get("num")
        target = LENGTHS[li % len(LENGTHS)]
        li += 1
        if item["kind"] == "video":
            max_take = max(MIN_SHOT - 0.2, item["dur"] - 0.18)
            sl = min(target, MAX_SHOT, max_take)
            leftover = item["dur"] - sl
            ss = 0.0
            if leftover > 0.6:
                ss = round(rng.uniform(0.0, min(leftover - 0.1, 1.8)), 3)
                sl = min(sl, item["dur"] - ss - 0.12)
        else:
            sl = min(target, MAX_SHOT)
        if t + sl > T:
            sl = max(T - t, 2.0)
            if item["kind"] == "video" and sl > item["dur"] - 0.12:
                sl = max(item["dur"] - 0.12, 2.0)
        rec = {"kind": item["kind"], "src": str(item["src"]), "len": round(sl, 3),
               "t": round(t, 2)}
        if item["kind"] == "still":
            rec["motion"] = motion()
        else:
            rec["ss"] = ss
        seq.append(rec)
        t += sl

    if t < T - 0.25:
        extra = T - t
        for s in reversed(seq):
            if extra <= 0.08:
                break
            if s["kind"] != "still":
                continue
            room = MAX_SHOT - s["len"]
            if room < 0.2:
                continue
            take = min(extra, room)
            s["len"] = round(s["len"] + take, 3)
            extra -= take
            t += take
        if extra < T and extra > 0:
            print(f"tail leftover after still-extend {extra:.2f}s")
    if t < T - 0.8:
        sys.exit(f"L5 FAIL: ran out of unique shots at t={t:.1f}/{T:.1f} (no looping). Fetch more/longer B-roll.")

    (WORK / "seq.json").write_text(json.dumps(seq, indent=1))
    (EP / "seq.json").write_text(json.dumps(seq, indent=1))
    lens = [s["len"] for s in seq]
    print(f"SEQ {len(seq)} t={t:.1f} min={min(lens):.2f} max={max(lens):.2f} uniq_lens={len(set(round(x,1) for x in lens))}")
    if max(lens) > MAX_SHOT + 0.05:
        sys.exit("L5 FAIL: a shot exceeds 6.5s")

    paths = []
    for i, s in enumerate(seq):
        dest = WORK / f"s{i:03d}.mp4"
        print(f"  {i:03d} {s['kind']:6} {s['len']:.2f}s ss={s.get('ss',0):.2f} {Path(s['src']).name}", flush=True)
        if s["kind"] == "still":
            encode_still(Path(s["src"]), dest, s["len"], s["motion"])
        else:
            encode_video(Path(s["src"]), dest, s["len"], s.get("ss", 0.0))
        paths.append(dest)

    lst = WORK / "vlist.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in paths))
    silent = WORK / "silent.mp4"
    run([ff(), "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
         "-pix_fmt", "yuv420p", "-r", str(FPS), "-an", str(silent)])
    tmp = Path("/tmp/cut_picture.mp4")
    run([ff(), "-y", "-i", str(silent), "-i", str(VOICE),
         "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "copy",
         "-t", f"{T:.3f}", "-movflags", "+faststart", str(tmp)])
    print("PICTURE", tmp, round(tmp.stat().st_size / 1e6, 1), "MB")
    for p in WORK.glob("s*.mp4"):
        p.unlink()
    silent.unlink(missing_ok=True)
    print("NEXT: stamp_caps.py", tmp, VOICE)


if __name__ == "__main__":
    main()
