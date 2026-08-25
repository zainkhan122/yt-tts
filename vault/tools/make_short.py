#!/usr/bin/env python3
"""make_short.py v2 — build a NATIVE VERTICAL (1080x1920) YouTube Short from a
finished long-form video. (R21 revised 2026-08-20.)

Segments:
  hook    = the cold open (auto: beats 0.. until ~target length)
  payoff  = a self-contained setup -> tension -> payoff section (--beats A B)

Media: NATIVE VERTICAL — portrait stock clips fetched from Pexels
(orientation=portrait) + vertical AI images you generate into
{videos/NAME}/shorts_ai/ first. Reuses the long-form's script sentences,
word-synced caption timing (storyboard.json) and R20 audio balance.
Voice is re-synthesized with the LOCKED af_heart voice using the SAME
keyword-split as the long-form (deterministic), so caption timings stay valid
and the Short voice matches the full video. End CTA (text + spoken) is APPENDED
after the narration (never overlaps it).

Usage:
  PIPE_VIDEO=/home/user/videos/video_014 python3 tools/make_short.py hook \
      --queries "warm window light,person alone,hands together"
  PIPE_VIDEO=/home/user/videos/video_014 python3 tools/make_short.py payoff \
      --beats 140 168 --queries "window light,standing alone,writing journal"
"""
import json, math, os, re, subprocess, sys, time, random, hashlib, shutil

sys.path.insert(0, "/home/user/tools")
import stock_fetch  # noqa: E402  (provides pexels_videos(..., orientation="portrait"))

BASE   = os.environ.get("PIPE_VIDEO", "/home/user/videos/video_013")
NAME   = os.path.basename(BASE)
SB     = os.path.join(BASE, "storyboard.json")
REPO   = "zainkhan122/yt-tts"
REPO_BASE = "vault/" + NAME
FONT   = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
CACHE  = os.path.expanduser("~/.cache/kokoro")
MODEL  = os.path.join(CACHE, "kokoro-v0_19.onnx")
VOICES = os.path.join(CACHE, "voices-v1.0.bin")
VOICE  = "af_heart"
SPEED  = 1.0
W, H   = 1080, 1920
FPS    = 30
GAP    = 0.20          # gap appended to each beat's audio (matches long-form)
CAP_HOLD = 2.6
CTA_TEXT = "Watch the full video on this channel."
CTA_GAP  = 0.25        # silence between narration end and CTA voice
TAIL     = 0.25        # tail after the CTA voice
SPLIT_GAP = 0.12       # pause inserted at the caption keyword (matches pipeline)

MOTIONS = [
    ("zin",  1.00, 1.38, 0.50, 0.50, 0.50, 0.50),
    ("zout", 1.30, 1.02, 0.50, 0.50, 0.50, 0.50),
    ("panlr",1.22, 1.22, 0.00, 0.50, 1.00, 0.50),
    ("panrl",1.22, 1.22, 1.00, 0.50, 0.00, 0.50),
    ("diag", 1.04, 1.34, 0.15, 0.20, 0.75, 0.55),
    ("settle",1.45, 1.00, 0.50, 0.50, 0.50, 0.50),
]

DEFAULT_QUERIES = "foggy morning,window light,silhouette,calm hands,candle light"


def run(args, check=True):
    r = subprocess.run(args, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError("CMD FAILED: " + " ".join(args)[:140] + "\n" + r.stderr[-1600:])
    return r


def ff():
    return subprocess.check_output(["python3", "-c",
        "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"]).decode().strip()


def bootstrap():
    import importlib
    for mod, pkg in [("soundfile", "soundfile"), ("imageio_ffmpeg", "imageio-ffmpeg"),
                     ("numpy", "numpy"), ("kokoro_onnx", "kokoro-onnx")]:
        try:
            importlib.import_module(mod)
        except ImportError:
            run([sys.executable, "-m", "pip", "install", "--quiet", pkg], check=False)
    os.makedirs(CACHE, exist_ok=True)
    if not os.path.exists(MODEL):
        run(["curl", "-sL", "--max-time", "550", "-o", MODEL,
             "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/kokoro-v0_19.onnx"])
    if not os.path.exists(VOICES):
        run(["curl", "-sL", "--max-time", "120", "-o", VOICES,
             "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"])


def pull_raw(repo_path, local):
    os.makedirs(os.path.dirname(local), exist_ok=True)
    import urllib.request
    req = urllib.request.Request(f"https://raw.githubusercontent.com/{REPO}/main/{repo_path}",
                                 headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=300) as r, open(local, "wb") as f:
        f.write(r.read())


def synth_sentence(ko, np, sf, sentence, anchor, wav_out):
    """TTS one sentence, replicating the pipeline's keyword-split so cap_start is
    valid. Returns cap_start (seconds)."""
    idx = sentence.lower().find(anchor.lower()) if anchor else -1
    if idx > 0:
        pre, post = sentence[:idx].strip(), sentence[idx:].strip()
        s_pre = s_post = None
        sr = 24000
        if pre:
            s_pre, sr = ko.create(pre, voice=VOICE, speed=SPEED, lang="en-us")
        if post:
            s_post, sr2 = ko.create(post, voice=VOICE, speed=SPEED, lang="en-us")
            sr = sr2
        pre_dur = (len(s_pre) / sr) if s_pre is not None else 0.0
        gap = np.zeros(int(SPLIT_GAP * sr), dtype=np.float32)
        segs = []
        if s_pre is not None:
            segs += [s_pre, gap]
        if s_post is not None:
            segs.append(s_post)
        audio = np.concatenate(segs) if segs else None
        if audio is not None:
            sf.write(wav_out, audio, sr)
        return round(pre_dur + SPLIT_GAP, 3)
    s, sr = ko.create(sentence, voice=VOICE, speed=SPEED, lang="en-us")
    sf.write(wav_out, s, sr)
    return 0.0


def synth_voice(text, wav_out):
    import soundfile as sf
    from kokoro_onnx import Kokoro
    ko = Kokoro(MODEL, VOICES)
    s, sr = ko.create(text, voice=VOICE, speed=SPEED, lang="en-us")
    sf.write(wav_out, s, sr)
    del ko
    import gc; gc.collect()
    return len(s) / sr


def wrap(disp, maxchars=15):
    words, lines, cur = disp.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if len(trial) <= maxchars or not cur:
            cur = trial
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def render_caption(disp, path):
    lines = wrap(disp)
    pngs = []
    for i, ln in enumerate(lines):
        fs = int(min(80, 980 / (len(ln) * 0.62)))
        p = f"{path}.{i}.png"
        run(["magick", "-background", "none", "-font", FONT, "-pointsize", str(fs),
             "-fill", "white", "-stroke", "black", "-strokewidth", "6",
             "label:" + ln, "-trim", "+repage", p])
        pngs.append(p)
    if len(pngs) == 1:
        run(["magick", pngs[0], path])
    else:
        run(["magick", "-background", "none"] + pngs + ["-gravity", "north", "-smush", "14", "-append", path])
    for p in pngs:
        os.remove(p)
    return path


def fetch_portrait(queries, n_each, out):
    os.makedirs(out, exist_ok=True)
    media = []
    for q in queries:
        try:
            saved = stock_fetch.pexels_videos(q, n_each, out, orientation="portrait")
        except Exception as e:
            print(f"  fetch '{q}' failed: {e}")
            continue
        for s in saved:
            name = s[0] if isinstance(s, tuple) else s
            media.append((os.path.join(out, name), "video"))
    return media


def render_beat(media_path, kind, beat_len, motion, out):
    Nf = max(int(round(beat_len * FPS)), 1)
    if kind == "video":
        fc = ("[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
              "fps=30,setsar=1,format=yuv420p,setpts=PTS-STARTPTS,"
              "eq=brightness='0.015*sin(2*PI*t/5)':saturation=1.06,"
              "vignette=PI/4.6,"
              "fade=t=in:st=0:d=0.15[v]")
        args = [ff(), "-y", "-stream_loop", "-1", "-i", media_path]
    else:
        _name, zs, ze, px0, py0, px1, py1 = motion
        z = f"{zs}+({ze}-{zs})*on/{Nf}"
        x = f"(iw-iw/zoom)*({px0}+({px1}-{px0})*on/{Nf})"
        y = f"(ih-ih/zoom)*({py0}+({py1}-{py0})*on/{Nf})"
        fc = (f"[0:v]scale=1620:2880:flags=lanczos,"
              f"zoompan=z='{z}':x='{x}':y='{y}':d={Nf}:s=1080x1920:fps=30,setsar=1,"
              f"eq=brightness='0.015*sin(2*PI*t/5)':saturation=1.06,"
              f"vignette=PI/4.6,"
              f"fade=t=in:st=0:d=0.15[v]")
        args = [ff(), "-y", "-i", media_path]
    args += ["-filter_complex", fc, "-map", "[v]", "-c:v", "libx264", "-preset", "veryfast",
             "-threads", "1", "-crf", "23", "-pix_fmt", "yuv420p", "-r", "30",
             "-t", f"{beat_len:.6f}", "-an", out]
    run(args)


def dur_of(p):
    r = subprocess.run([ff(), "-i", p], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", r.stderr)
    h, mi, s = m.groups(); return int(h) * 3600 + int(mi) * 60 + float(s)


def main():
    bootstrap()
    args = sys.argv[1:]
    kind = args[0] if args else "hook"
    target = 36.0
    if "--dur" in args:
        target = float(args[args.index("--dur") + 1])
    queries = DEFAULT_QUERIES.split(",")
    if "--queries" in args:
        queries = [q.strip() for q in args[args.index("--queries") + 1].split(",") if q.strip()]
    pay_a = pay_b = None
    if "--beats" in args:
        pay_a = int(args[args.index("--beats") + 1])
        pay_b = int(args[args.index("--beats") + 2])
    skip = set()
    if "--skip" in args:
        skip = {int(x) for x in args[args.index("--skip") + 1].split(",") if x.strip()}
    if kind == "payoff" and pay_a is None:
        raise SystemExit("payoff requires --beats A B")

    if not os.path.exists(SB):
        pull_raw(f"{REPO_BASE}/storyboard.json", SB)
    beats = json.load(open(SB))
    N = len(beats)

    import numpy as np
    import soundfile as sf
    from kokoro_onnx import Kokoro
    ko = Kokoro(MODEL, VOICES)

    work = f"/tmp/short_make/{NAME}_{kind}"
    if os.path.isdir(work):
        shutil.rmtree(work)
    os.makedirs(work)

    # --- synthesize the spoken CTA first (its real duration drives the window) ---
    cta_wav = f"{work}/cta.wav"
    cta_dur = synth_voice(CTA_TEXT, cta_wav)
    ext = CTA_GAP + cta_dur + TAIL

    # --- choose the beat range ---
    if kind == "hook":
        a, b, acc = 0, 0, 0.0
        while b < N and acc < target - ext:
            acc += beats[b].get("beat_len") or beats[b].get("v_dur") or beats[b].get("beat_dur") or 3.0
            b += 1
    else:
        a, b = pay_a, min(pay_b, N)
    seg_beats = [bt for i, bt in enumerate(beats[a:b]) if (a + i) not in skip]
    print(f"segment [{kind}] beats {a}..{b-1} ({len(seg_beats)} beats"
          + (f", skipped {sorted(skip)})" if skip else "") + ")")

    # --- TTS every segment beat (replicating the keyword-split) ---
    cap_times = []   # (abs_time_in_segment, display)
    voice_parts = []
    for i, bt in enumerate(seg_beats):
        w = f"{work}/voice_{i:03d}.wav"
        anchor = bt["caption"][0] if bt.get("caption") else None
        cap_start = synth_sentence(ko, np, sf, bt["sentence"], anchor, w)
        d = dur_of(w)
        beat_len = d + GAP
        bt["_beat_len"] = beat_len
        bt["_cap_start"] = cap_start
        if bt.get("caption") and cap_start < beat_len - 0.1:
            cap_times.append((sum(x["_beat_len"] for x in seg_beats[:i]) + cap_start,
                              bt["caption"][1]))
        voice_parts.append(w)
    voice_dur = sum(bt["_beat_len"] for bt in seg_beats)
    cta_start = voice_dur + CTA_GAP
    total = voice_dur + ext
    print(f"voice_dur={voice_dur:.2f}s  CTA@{cta_start:.2f}s  total={total:.2f}s  captions={len(cap_times)}")

    # release Kokoro (325MB) before the render phase — 2GB RAM box
    del ko
    import gc; gc.collect()

    # --- media: portrait stock (fetched) + vertical AI images (you generated) ---
    stock_dir = f"/tmp/{NAME}_short"
    media = fetch_portrait(queries, 6, stock_dir)
    ai_dir = os.path.join(BASE, "shorts_ai")
    if os.path.isdir(ai_dir):
        for f in sorted(os.listdir(ai_dir)):
            if f.lower().endswith((".jpg", ".jpeg", ".png")):
                media.append((os.path.join(ai_dir, f), "photo"))
    if not media:
        raise SystemExit("no portrait media fetched — check Pexels key / queries")
    print(f"media pool: {len(media)} ({sum(1 for _, k in media if k=='video')} video, "
          f"{sum(1 for _, k in media if k=='photo')} AI)")

    rng = random.Random(hashlib.md5(NAME.encode()).hexdigest())
    videos = [m for m in media if m[1] == "video"]
    photos = [m for m in media if m[1] == "photo"]
    rng.shuffle(videos)
    rng.shuffle(photos)
    n = len(seg_beats)
    assign = [None] * n
    # spread the AI images evenly across the beats (no clumping, no fixed cycle)
    n_photo = min(len(photos), n // 2)
    positions = sorted({round(j * (n - 1) / max(n_photo, 1)) for j in range(n_photo)})
    pi = 0
    for pos in positions:
        if pi < len(photos):
            assign[pos] = photos[pi]; pi += 1
    # fill the rest with unique stock videos (pool >> beats -> zero repeats)
    vi = 0
    for i in range(n):
        if assign[i] is None:
            assign[i] = videos[vi % max(len(videos), 1)]; vi += 1
    used = [p for p, _ in assign]
    print(f"assign: {n} beats, {len(set(used))} distinct media, "
          f"{len(used) - len(set(used))} repeats, {pi} AI images used")

    # --- hand off RENDER + audio + mux to a FRESH interpreter ---
    # (2GB box: Kokoro's native memory is not reclaimed in-process, so any
    #  ffmpeg render alongside it OOMs. A fresh process has no Kokoro.)
    motions = [MOTIONS[rng.randrange(len(MOTIONS))] for _ in range(len(seg_beats))]
    manifest = {
        "work": work,
        "assign": [[p, k] for p, k in assign],
        "motions": motions,
        "voice_parts": voice_parts,
        "lens": [bt["_beat_len"] for bt in seg_beats],
        "voice_dur": voice_dur,
        "cta_wav": cta_wav,
        "cta_start": cta_start,
        "total": total,
        "ext": ext,
        "cap_times": cap_times,
        "base": BASE,
        "repo_base": REPO_BASE,
        "out_name": f"short_{kind}.mp4",
    }
    mp = f"{work}/manifest.json"
    json.dump(manifest, open(mp, "w"))
    # exec: REPLACE this process (frees Kokoro's native memory instantly) —
    # avoids the parent holding ~600MB while phase2's git push needs the RAM.
    os.execv(sys.executable, [sys.executable, os.path.abspath(__file__), "--phase", mp])


def phase2(mp):
    """Fresh-interpreter phase: render -> captions -> voice -> mix -> mux -> push."""
    import soundfile as sflib
    m = json.load(open(mp))
    work = m["work"]; voice_parts = m["voice_parts"]; lens = m["lens"]
    voice_dur = m["voice_dur"]; cta_wav = m["cta_wav"]; cta_start = m["cta_start"]
    total = m["total"]; cap_times = m["cap_times"]; ext = m["ext"]
    assign = [tuple(a) for a in m["assign"]]; motions = [tuple(x) for x in m["motions"]]
    BASE = m["base"]; REPO_BASE = m["repo_base"]; out_name = m["out_name"]
    NBEATS = len(voice_parts)
    cta_dur = total - voice_dur - CTA_GAP - TAIL

    # --- render each beat (vertical) ---
    for i in range(NBEATS):
        render_beat(assign[i][0], assign[i][1], lens[i], motions[i], f"{work}/vbeat_{i:03d}.mp4")
    with open(f"{work}/vlist.txt", "w") as f:
        for i in range(NBEATS):
            f.write(f"file '{work}/vbeat_{i:03d}.mp4'\n")
    vfull = f"{work}/vfull.mp4"
    run([ff(), "-y", "-f", "concat", "-safe", "0", "-i", f"{work}/vlist.txt", "-c", "copy", vfull])
    vpadded = f"{work}/vpadded.mp4"
    run([ff(), "-y", "-i", vfull, "-vf", f"tpad=stop_mode=clone:stop_duration={ext:.3f}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
         "-r", str(FPS), "-an", vpadded])

    # --- captions + CTA text overlay ---
    args2 = [ff(), "-y", "-i", vpadded]
    fi = 0
    for (rel, disp) in cap_times:
        png = f"{work}/cap_{fi:03d}.png"
        render_caption(disp, png)
        hold = min(CAP_HOLD, total - rel - 0.05)
        args2 += ["-itsoffset", f"{rel:.3f}", "-loop", "1", "-framerate", "30",
                  "-t", f"{hold:.2f}", "-i", png]
        fi += 1
    cta_png = f"{work}/cta.png"
    run(["magick", "-background", "none", "-font", FONT, "-pointsize", "62",
         "-fill", "white", "-stroke", "black", "-strokewidth", "6",
         "label:\u25b6  FULL VIDEO ON CHANNEL", "-trim", "+repage", cta_png])
    args2 += ["-itsoffset", f"{cta_start:.3f}", "-loop", "1", "-framerate", "30",
              "-t", f"{cta_dur + TAIL + 0.1:.2f}", "-i", cta_png]
    fc = []
    last = "0:v"
    for j in range(fi + 1):
        ypos = "H*0.22" if j < fi else "H-240"
        fc.append(f"[{j+1}:v]format=rgba[c{j}]")
        fc.append(f"[{last}][c{j}]overlay=x=(W-w)/2:y={ypos}:shortest=0:eof_action=pass[o{j}]")
        last = f"o{j}"
    vcap = f"{work}/vcap.mp4"
    args2 += ["-filter_complex", ";".join(fc), "-map", f"[{last}]",
              "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
              "-r", str(FPS), "-an", vcap]
    run(args2)

    vcmd = [ff(), "-y"]
    for w in voice_parts:
        vcmd += ["-i", w]
    fvoice = []
    for i in range(NBEATS):
        with sflib.SoundFile(voice_parts[i]) as f:
            wd = f.frames / f.samplerate
        fvoice.append(f"[{i}:a]apad=pad_dur={max(lens[i]-wd,0):.6f}[a{i}]")
    fvoice.append("".join(f"[a{j}]" for j in range(NBEATS)) +
                  f"concat=n={NBEATS}:v=0:a=1,afade=t=out:st={max(voice_dur-0.15,0):.2f}:d=0.15[vo]")
    voice_full = f"{work}/voice_full.wav"
    vcmd += ["-filter_complex", ";".join(fvoice), "-map", "[vo]",
             "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", voice_full]
    run(vcmd)

    pad = f"{work}/pad.wav"
    subprocess.run([sys.executable, "/home/user/tools/make_pad.py", f"{total:.1f}", pad], check=True)
    cta_ms = int(cta_start * 1000)
    amix = f"{work}/amix.m4a"
    run([ff(), "-y", "-i", voice_full, "-i", pad, "-i", cta_wav, "-filter_complex",
         "[0:a]highpass=f=80,equalizer=f=8000:t=q:w=1:g=2,"
         "acompressor=threshold=-18dB:ratio=2.5:attack=5:release=80,"
         "aformat=channel_layouts=stereo,asplit=2[voice][voice2];"
         "[2:a]highpass=f=80,equalizer=f=8000:t=q:w=1:g=2,"
         "acompressor=threshold=-18dB:ratio=2.5:attack=5:release=80,"
         f"adelay={cta_ms}:all=1,aformat=channel_layouts=stereo,asplit=2[cta][cta2];"
         "[1:a]volume=0.55,afade=t=in:st=0:d=3,afade=t=out:st={:.2f}:d=3[pd];"
         "[voice][cta]amix=inputs=2:duration=longest:normalize=0[key];"
         "[pd][key]sidechaincompress=threshold=0.05:ratio=3:attack=15:release=250[duck];"
         "[voice2][cta2][duck]amix=inputs=3:duration=longest:normalize=0,"
         "loudnorm=I=-16:TP=-1.5:LRA=11[aout]".format(max(total - 3, 1)),
         "-map", "[aout]", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
         "-t", f"{total:.2f}", amix])

    os.makedirs(f"{BASE}/shorts", exist_ok=True)
    out = f"{work}/{out_name}"
    run([ff(), "-y", "-i", f"{work}/vcap.mp4", "-i", amix, "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-c:a", "copy", "-t", f"{total:.2f}", out])

    r = subprocess.run([ff(), "-i", out], capture_output=True, text=True)
    mm = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", r.stderr)
    d = int(mm.group(1)) * 3600 + int(mm.group(2)) * 60 + float(mm.group(3))
    ok_dim = "1080x1920" in r.stderr
    ok_fps = "30 fps" in r.stderr
    ok_aud = "aac" in r.stderr
    print(f"short built: {out}  dur={d:.2f}s  dim={'1080x1920' if ok_dim else '?'} fps=30 aud={ok_aud}")
    if not (ok_dim and ok_fps and ok_aud and 25 <= d <= 50):
        raise SystemExit("SHORT VERIFY FAILED")

    # free /tmp before the git push (the clone + write-tree need several hundred MB)
    shutil.rmtree(f"/tmp/{os.path.basename(BASE)}_short", ignore_errors=True)
    subprocess.run([sys.executable, "/home/user/tools/git_push.py",
                    f"{os.path.basename(BASE)} {out_name} (vertical)",
                    f"{REPO_BASE}/shorts/{out_name}", out], check=True)
    shutil.copyfile(out, f"{BASE}/shorts/{out_name}")
    shutil.rmtree(work, ignore_errors=True)
    print(f"pushed + saved {BASE}/shorts/{out_name}")
    for (rel, disp) in cap_times:
        print(f"  {disp:32s} @ {rel:6.2f}s")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--phase":
        phase2(sys.argv[2])
    else:
        main()
