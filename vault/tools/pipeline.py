#!/usr/bin/env python3
"""pipeline.py — ROBUST multi-session video builder for The Deeper Mind.
Follows MASTER_RULES.md.  Set target via env PIPE_VIDEO.
Caption sync: captions applied at FINALIZE on the absolute shared timeline
(video & audio both use per-beat beat_dur) => zero cumulative drift.
"""
import json, math, os, re, sys, subprocess, time, zipfile, urllib.request, urllib.error

BASE   = os.environ.get("PIPE_VIDEO", "/home/user/videos/video_001")
NAME   = os.path.basename(BASE)
TXT    = os.path.join(BASE, "voiceover.txt")
SB     = os.path.join(BASE, "storyboard.json")
STATE  = os.path.join(BASE, "state.json")
ASSETS_JSON = os.path.join(BASE, "assets.json")
CFG    = os.path.join(BASE, "storyboard_config.json")
FONT   = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
CACHE  = os.path.expanduser("~/.cache/kokoro")
MODEL  = os.path.join(CACHE, "kokoro-v0_19.onnx")
VOICES = os.path.join(CACHE, "voices-v1.0.bin")
REPO   = "zainkhan122/yt-tts"
REPO_BASE = "vault/" + NAME
CHUNK  = 26
FPS    = 30
GAP    = 0.20
SPLIT_GAP = 0.12
CAP_HOLD  = 2.6
VOICE  = "af_heart"
SPEED  = 1.0
VOICE_MODEL_URL  = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/kokoro-v0_19.onnx"
VOICE_VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"

MOTIONS = [
    ("zin",  1.00, 1.38, 0.50, 0.50, 0.50, 0.50),
    ("zout", 1.30, 1.02, 0.50, 0.50, 0.50, 0.50),
    ("panlr",1.22, 1.22, 0.00, 0.50, 1.00, 0.50),
    ("panrl",1.22, 1.22, 1.00, 0.50, 0.00, 0.50),
    ("diag", 1.04, 1.34, 0.15, 0.20, 0.75, 0.55),
    ("settle",1.45, 1.00, 0.50, 0.50, 0.50, 0.50),
]

def run(args, check=True):
    r = subprocess.run(args, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError("CMD FAILED: " + " ".join(args)[:120] + "\n" + r.stderr[-1200:])
    return r

def ff():
    return subprocess.check_output(["python3","-c","import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"]).decode().strip()

def load_state():
    return json.load(open(STATE)) if os.path.exists(STATE) else {}
def save_state(s):
    json.dump(s, open(STATE, "w"), indent=1)

# ---- ROBUST DOWNLOAD: exponential backoff + retries for 429/5xx/network errors ----
MAX_RETRIES = 8
BASE_BACKOFF = 3.0   # seconds; grows exponentially (3, 6, 12, 24, ...)

def download(url, path, retries=MAX_RETRIES):
    import http.client
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=300) as r, open(path, "wb") as f:
                f.write(r.read())
            return True
        except urllib.error.HTTPError as e:
            last = e
            # 429 rate-limit, 5xx server errors, 403 (Pexels-style throttle) -> retry
            if e.code in (429, 500, 502, 503, 504, 403):
                wait = BASE_BACKOFF * (2 ** attempt)
                print(f"  ⏳ {e.code} on {url[:70]}... retry {attempt+1}/{retries} in {wait:.0f}s")
                time.sleep(wait)
                continue
            raise
        except (urllib.error.URLError, http.client.RemoteDisconnected,
                ConnectionResetError, TimeoutError, OSError) as e:
            last = e
            wait = BASE_BACKOFF * (2 ** attempt)
            print(f"  ⏳ net error ({e.__class__.__name__}) on {url[:70]}... retry {attempt+1}/{retries} in {wait:.0f}s")
            time.sleep(wait)
            continue
    raise RuntimeError(f"download failed after {retries} tries: {url[:80]} -> {last}")

def pull_raw(repo_path, local, ref="main"):
    os.makedirs(os.path.dirname(local), exist_ok=True)
    download(f"https://raw.githubusercontent.com/{REPO}/{ref}/{repo_path}", local)

def bootstrap():
    import importlib
    for mod, pkg in [("kokoro_onnx","kokoro-onnx"),("soundfile","soundfile"),("imageio_ffmpeg","imageio-ffmpeg")]:
        try:
            importlib.import_module(mod)
        except ImportError:
            run([sys.executable,"-m","pip","install","--quiet",pkg], check=False)
    os.makedirs(CACHE, exist_ok=True)
    if not os.path.exists(MODEL):
        run(["curl","-sL","--max-time","550","-o",MODEL,VOICE_MODEL_URL])
    if not os.path.exists(VOICES):
        run(["curl","-sL","--max-time","120","-o",VOICES,VOICE_VOICES_URL])
    print("bootstrap OK:", ff())

# ---------------- storyboard ----------------
def load_cfg():
    assets = json.load(open(ASSETS_JSON))
    cfg = json.load(open(CFG))
    return assets, cfg["sections"], cfg["captions"], cfg.get("max_uses", 2)

def sentences():
    text = open(TXT, encoding="utf-8").read()
    text = re.sub(r"\s+", " ", text).strip()
    return [p.strip() for p in re.split(r"(?<=[.!?])\s+", text) if p.strip()]

def build_storyboard():
    ASSETS, SECTIONS, CAPTIONS, MAX_USES = load_cfg()
    sents = sentences()
    N = len(sents)
    # preserve timings (cap_start/beat_len) from existing storyboard by sentence text
    old = {}
    if os.path.exists(SB):
        try:
            for ob in json.load(open(SB)):
                for k in ("cap_start", "beat_len", "v_dur", "beat_dur"):
                    if k in ob:
                        old.setdefault(ob["sentence"], {})[k] = ob[k]
        except Exception:
            pass
    section_of, cur = [], 0
    for s in sents:
        for si in range(cur, len(SECTIONS)):
            st = SECTIONS[si].get("start")
            if st is not None and st in s:
                cur = si
        section_of.append(cur)
    import random, hashlib
    rng = random.Random(hashlib.md5(NAME.encode()).hexdigest())  # deterministic per video
    usage = {}
    chunk_usage = {}   # asset -> set of chunk indices where it's already used
    last_use = {}      # asset -> last beat index it was used (for reuse distance)
    used_caps = set()
    beats = []
    prev_asset = None
    prev_motion = None
    def tags_of(a):
        v = ASSETS[a]
        return [t for t in (v[2] if len(v) > 2 else [])]
    def tag_hit(a, low):
        return sum(1 for t in tags_of(a) if t in low)
    for i, s in enumerate(sents):
        si = section_of[i]
        chunk = i // CHUNK
        low = s.lower()
        def tier(a):
            # 0=unused+tag match, 1=unused, 2=used-once+tag, 3=used-once, 4=at cap
            u = usage.get(a, 0)
            th = tag_hit(a, low)
            if u == 0 and th > 0: return 0
            if u == 0: return 1
            if u < MAX_USES and th > 0: return 2
            if u < MAX_USES: return 3
            return 4
        # GLOBAL pool (all assets, not section-locked). Constraints: not prev,
        # not already used in this chunk, under max uses.
        cands = [a for a in ASSETS
                 if a != prev_asset
                 and chunk not in chunk_usage.get(a, set())
                 and usage.get(a, 0) < MAX_USES]
        if not cands:
            cands = [a for a in ASSETS if a != prev_asset and usage.get(a, 0) < MAX_USES]
        if not cands:
            cands = [a for a in ASSETS if a != prev_asset]
        # shuffle BEFORE the stable sort => random order within equal keys (no pattern)
        rng.shuffle(cands)
        # sort: best tier first; within tier, oldest last-use first (max reuse distance)
        cands.sort(key=lambda a: (tier(a), last_use.get(a, -1), usage.get(a, 0)))
        asset = cands[0]
        usage[asset] = usage.get(asset, 0) + 1
        chunk_usage.setdefault(asset, set()).add(chunk)
        last_use[asset] = i
        prev_asset = asset
        # randomized motion, never repeating the previous motion
        m = MOTIONS[rng.randrange(len(MOTIONS))]
        while m is prev_motion:
            m = MOTIONS[rng.randrange(len(MOTIONS))]
        prev_motion = m
        cap = None
        for (anchor, disp, style) in CAPTIONS:
            if disp in used_caps:
                continue
            if anchor.lower() in low:
                cap = (anchor, disp, style)
                used_caps.add(disp)
                break
        b = {"sentence": s, "asset": asset,
             "motion": m, "caption": cap}
        # carry over timings preserved from the previous storyboard
        for k, v in old.get(s, {}).items():
            b[k] = v
        beats.append(b)
    json.dump(beats, open(SB, "w"), indent=1)
    st = load_state(); st["total_beats"] = N; save_state(st)
    over = {a: c for a, c in usage.items() if c > MAX_USES}
    missing = sorted({b["asset"] for b in beats if not os.path.exists(ASSETS[b["asset"]][0])})
    if missing:
        print("MISSING ASSET FILES — restore before rendering:")
        for a in missing:
            print(f"  {a} -> {ASSETS[a][0]}")
        sys.exit(1)
    distinct = len(usage)
    frac = distinct / len(ASSETS) if ASSETS else 0
    print(f"storyboard: {N} beats; captioned: {sum(1 for b in beats if b['caption'])}; "
          f"assets used: {distinct}/{len(ASSETS)} ({frac*100:.0f}%); over-cap: {over if over else 'none'}; all files present")

def chunk_range(k):
    N = len(json.load(open(SB)))
    return k*CHUNK, min((k+1)*CHUNK, N)
def n_chunks():
    N = len(json.load(open(SB)))
    return (N + CHUNK - 1)//CHUNK

def make_caption(disp, style, path):
    safe = disp.replace("'", "\u2019")
    if style == "pop":
        fs = int(min(110, 1560/(len(safe)*0.62)))
        run(["magick","-background","none","-font",FONT,"-pointsize",str(fs),
             "-fill","#E8C766","-stroke","black","-strokewidth","8","label:"+safe,
             "-trim","+repage",path])
    else:
        fs = int(min(46 if style=="caption" else 58, 1500/(len(safe)*0.62)))
        tmp = path + ".t.png"
        run(["magick","-background","none","-font",FONT,"-pointsize",str(fs),
             "-fill","white" if style=="caption" else "#E8C766","-stroke","black","-strokewidth","3",
             "label:"+safe,"-trim","+repage",tmp])
        w,h = map(int, subprocess.check_output(["identify","-format","%w %h",tmp]).split())
        pad=26; bw,bh=w+2*pad,h+2*pad
        run(["magick","-size",f"{bw}x{bh}","xc:none","-fill","rgba(0,0,0,0.55)",
             "-draw",f"roundrectangle 0,0 {bw-1},{bh-1} 24,24",tmp,"-gravity","center","-composite",path])
        os.remove(tmp)
    return path

def zip_files(zip_path, files):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as z:
        for name, local in files:
            z.write(local, arcname=name)
def unzip_to(zip_path, dest):
    os.makedirs(dest, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(dest)

# ---------------- tts (word-sync split) ----------------
def _tts_one(ko, sf, np, beats, i, w):
    bt = beats[i]
    sentence = bt["sentence"]
    anchor = bt["caption"][0] if bt["caption"] else None
    idx = sentence.lower().find(anchor.lower()) if anchor else -1
    if idx > 0:
        pre = sentence[:idx].strip()
        post = sentence[idx:].strip()
        s_pre = s_post = None
        sr = 24000
        if pre:
            s_pre, sr = ko.create(pre, voice=VOICE, speed=SPEED, lang="en-us")
        if post:
            s_post, sr2 = ko.create(post, voice=VOICE, speed=SPEED, lang="en-us")
            sr = sr2
        pre_dur = (len(s_pre)/sr) if s_pre is not None else 0.0
        gap = np.zeros(int(SPLIT_GAP*sr), dtype=np.float32)
        segs = []
        if s_pre is not None:
            segs += [s_pre, gap]
        if s_post is not None:
            segs.append(s_post)
        audio = np.concatenate(segs) if segs else None
        if audio is not None:
            sf.write(w, audio, sr)
        bt["cap_start"] = round(pre_dur + SPLIT_GAP, 3)
    else:
        s, sr = ko.create(sentence, voice=VOICE, speed=SPEED, lang="en-us")
        sf.write(w, s, sr)
        bt["cap_start"] = 0.0
        if bt["caption"] and idx == -1:
            print(f"  WARN beat {i}: anchor {anchor!r} not found in: {sentence[:60]}")

def tts_all():
    bootstrap()
    import numpy as np
    import soundfile as sf
    from kokoro_onnx import Kokoro
    ko = Kokoro(MODEL, VOICES)
    beats = json.load(open(SB)); N = len(beats)
    st = load_state(); st.setdefault("tts_done", [])
    for k in range(n_chunks()):
        if k in st["tts_done"]:
            continue
        a, b = chunk_range(k)
        wavs = []
        for i in range(a, b):
            w = f"{BASE}/beat_{i:03d}.wav"
            os.makedirs(os.path.dirname(w), exist_ok=True)
            if not os.path.exists(w):
                try:
                    _tts_one(ko, sf, np, beats, i, w)
                except Exception as e:
                    print(f"beat {i} TTS FAILED: {e}")
            if os.path.exists(w):
                wavs.append((f"beat_{i:03d}.wav", w))
        if wavs:
            zp = f"{BASE}/audio_chunk_{k:02d}.zip"
            zip_files(zp, wavs)
            subprocess.run([sys.executable, "/home/user/tools/vault_push.py", REPO,
                f"{NAME} audio chunk {k}", f"{REPO_BASE}/audio_chunk_{k:02d}.zip", zp], check=True)
            for _, w in wavs: os.remove(w)
            os.remove(zp)
        st["tts_done"].append(k); save_state(st)
        json.dump(beats, open(SB, "w"), indent=1)
        print(f"tts chunk {k} pushed ({a}-{b})")
    subprocess.run([sys.executable, "/home/user/tools/vault_push.py", REPO,
        f"{NAME} storyboard caption timings",
        f"{REPO_BASE}/storyboard.json", SB, f"{REPO_BASE}/state.json", STATE], check=True)
    print("tts_all done. caption start times:")
    for i, b in enumerate(beats):
        if b["caption"]:
            print(f"  beat {i:3d}  +{b['cap_start']:5.2f}s  {b['caption'][1]}")

def ensure_wavs(k):
    a, b = chunk_range(k)
    if all(os.path.exists(f"{BASE}/beat_{i:03d}.wav") for i in range(a, b)):
        return
    zp = f"{BASE}/audio_chunk_{k:02d}.zip"
    if not os.path.exists(zp):
        pull_raw(f"{REPO_BASE}/audio_chunk_{k:02d}.zip", zp)
    unzip_to(zp, BASE)
    os.remove(zp)

# ---------------- render (visuals only; stores beat_dur) ----------------
def dur_of(path):
    r = subprocess.run([ff(), "-i", path], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", r.stderr)
    if not m:
        raise RuntimeError("no duration: " + path)
    h, mi, s = m.groups(); return int(h)*3600+int(mi)*60+float(s)

def render_chunk(k):
    bootstrap()
    ASSETS, _, _, _ = load_cfg()
    beats = json.load(open(SB)); N = len(beats)
    a, b = chunk_range(k)
    ensure_wavs(k)
    vbeats = []
    failed = 0
    for i in range(a, b):
        vout = f"{BASE}/vbeat_{i:03d}.mp4"
        if os.path.exists(vout):
            try:
                dur_of(vout); vbeats.append((f"vbeat_{i:03d}.mp4", vout)); continue
            except Exception:
                os.remove(vout)
        try:
            _render_one(ASSETS, beats, i, vout)
            dur_of(vout)
            vbeats.append((f"vbeat_{i:03d}.mp4", vout))
        except Exception as e:
            failed += 1
            print(f"beat {i} FAILED: {e}")
    json.dump(beats, open(SB, "w"), indent=1)
    subprocess.run([sys.executable, "/home/user/tools/vault_push.py", REPO,
        f"{NAME} storyboard beat durations (chunk {k})", f"{REPO_BASE}/storyboard.json", SB], check=True)
    if failed:
        print(f"render chunk {k}: {failed} FAILED — not marked done")
        return
    if vbeats:
        zp = f"{BASE}/video_chunk_{k:02d}.zip"
        zip_files(zp, vbeats)
        # chunk zips can exceed the Git Data API blob ceiling (~40MB) -> native git
        subprocess.run([sys.executable, "/home/user/tools/git_push.py",
                        f"{NAME} video chunk {k}", f"{REPO_BASE}/video_chunk_{k:02d}.zip", zp], check=True)
        for _, v in vbeats: os.remove(v)
        os.remove(zp)
        st = load_state(); st.setdefault("render_done", []).append(k); save_state(st)
        print(f"render chunk {k} pushed ({a}-{b})")
    else:
        print(f"render chunk {k}: nothing new")

def _render_one(ASSETS, beats, i, vout):
    import soundfile as sf
    bt = beats[i]
    wav = f"{BASE}/beat_{i:03d}.wav"
    with sf.SoundFile(wav) as f:
        wav_samples, sr = f.frames, f.samplerate
    wav_dur = wav_samples / sr
    # FRAME-EXACT beat length: pad to whole frames (1 frame = sr/FPS samples).
    # Video AND audio both use beat_len => sample-exact A/V + caption sync.
    frame_samples = sr / FPS
    beat_samples = math.ceil((wav_samples + GAP * sr) / frame_samples) * frame_samples
    beat_len = beat_samples / sr
    Nf = int(round(beat_samples / frame_samples))
    bt["beat_len"] = beat_len
    bt["beat_dur"] = beat_len
    v = ASSETS[bt["asset"]]
    path = v[0]; kind = v[1]
    if kind == "video":
        fc = ("[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=30,setsar=1,format=yuv420p,setpts=PTS-STARTPTS,"
              "eq=brightness='0.015*sin(2*PI*t/5)':saturation=1.06,"
              "vignette=PI/4.6,"
              "noise=alls=5:allf=t,"
              "fade=t=in:st=0:d=0.18[v]")
        args = [ff(), "-y", "-stream_loop", "-1", "-i", path]
    else:
        m = bt["motion"]
        name, zs, ze, px0, py0, px1, py1 = m
        if name == "settle":
            # fast push-in that settles: ease-out via sqrt
            z = f"{ze}+({zs}-{ze})*sqrt(max(0,1-on/{Nf}))"
            x = f"(iw-iw/zoom)*({px0}+({px1}-{px0})*on/{Nf})"
            y = f"(ih-ih/zoom)*({py0}+({py1}-{py0})*on/{Nf})"
        elif name == "diag":
            z = f"{zs}+({ze}-{zs})*on/{Nf}"
            x = f"(iw-iw/zoom)*({px0}+({px1}-{px0})*on/{Nf})"
            y = f"(ih-ih/zoom)*({py0}+({py1}-{py0})*on/{Nf})"
        else:
            z = f"{zs}+({ze}-{zs})*on/{Nf}"
            x = f"(iw-iw/zoom)*({px0}+({px1}-{px0})*on/{Nf})"
            y = f"(ih-ih/zoom)*({py0}+({py1}-{py0})*on/{Nf})"
        fc = (f"[0:v]scale=2560:1440:flags=lanczos,"
              f"zoompan=z='{z}':x='{x}':y='{y}':d={Nf}:s=1920x1080:fps={FPS},setsar=1,"
              f"eq=brightness='0.015*sin(2*PI*t/5)':saturation=1.06,"
              f"vignette=PI/4.6,"
              f"noise=alls=5:allf=t,"
              f"fade=t=in:st=0:d=0.18[v]")
        args = [ff(), "-y", "-i", path]
    args += ["-filter_complex", fc, "-map", "[v]", "-c:v","libx264","-preset","veryfast",
             "-crf","21","-pix_fmt","yuv420p","-r","30","-t",f"{beat_len:.6f}","-an",vout]
    run(args)
    bt["v_dur"] = round(dur_of(vout), 3)   # MEASURED video duration = master clock

# ---------------- assemble (per-beat pad = beat_dur) ----------------
def assemble_chunk(k):
    bootstrap()
    a, b = chunk_range(k)
    if not os.path.exists(SB):
        pull_raw(f"{REPO_BASE}/storyboard.json", SB)
    beats = json.load(open(SB))
    vz = f"{BASE}/video_chunk_{k:02d}.zip"
    az = f"{BASE}/audio_chunk_{k:02d}.zip"
    for zp, rp in [(vz,"video_chunk"),(az,"audio_chunk")]:
        if not os.path.exists(zp):
            pull_raw(f"{REPO_BASE}/{rp}_{k:02d}.zip", zp)
    unzip_to(vz, f"{BASE}/work_v"); unzip_to(az, f"{BASE}/work_a")
    with open(f"{BASE}/vlist.txt","w") as f:
        for i in range(a, b):
            f.write(f"file '{BASE}/work_v/vbeat_{i:03d}.mp4'\n")
    partv = f"{BASE}/part_{k:02d}.mp4"
    # NO fps filter here (beats are exact 30fps via -t; fps=30 caused drift)
    run([ff(),"-y","-f","concat","-safe","0","-i",f"{BASE}/vlist.txt",
         "-vf","scale=1920:1080,setsar=1,format=yuv420p",
         "-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p","-an",partv])
    acmd = [ff(), "-y"]
    for i in range(a, b):
        acmd += ["-i", f"{BASE}/work_a/beat_{i:03d}.wav"]
    fc = []
    import soundfile as sf
    for i in range(a, b):
        with sf.SoundFile(f"{BASE}/work_a/beat_{i:03d}.wav") as f:
            wav_samples, sr = f.frames, f.samplerate
        wav_dur = wav_samples / sr
        bd = beats[i].get("beat_len") or beats[i].get("v_dur") or beats[i].get("beat_dur") or round((wav_dur + GAP) * FPS) / FPS
        pad = max(bd - wav_dur, 0.0)
        fc.append(f"[{i-a}:a]apad=pad_dur={pad:.6f}[a{i-a}]")
    fc.append("".join(f"[a{j}]" for j in range(b-a)) + f"concat=n={b-a}:v=0:a=1[aout]")
    parta = f"{BASE}/part_{k:02d}.wav"
    acmd += ["-filter_complex",";".join(fc),"-map","[aout]","-ar","48000","-ac","1","-c:a","pcm_s16le",parta]
    run(acmd)
    subprocess.run([sys.executable, "/home/user/tools/git_push.py",
        f"{NAME} parts chunk {k}",
        "--branch", f"parts/{NAME}-{k:02d}",
        f"{REPO_BASE}/part_{k:02d}.mp4", partv,
        f"{REPO_BASE}/part_{k:02d}.wav", parta], check=True)
    for p in [vz, az, partv, parta, f"{BASE}/vlist.txt"]:
        if os.path.exists(p): os.remove(p)
    subprocess.run(["rm","-rf",f"{BASE}/work_v",f"{BASE}/work_a"])
    st = load_state(); st.setdefault("assemble_done", []).append(k); save_state(st)
    print(f"assemble chunk {k} done + pushed")

# ---------------- finalize (captions on absolute timeline) ----------------
def finalize():
    bootstrap()
    nc = n_chunks()
    wd = f"{BASE}/work_f"
    os.makedirs(wd, exist_ok=True)
    for k in range(nc):
        for ext in ["mp4","wav"]:
            lp = f"{wd}/part_{k:02d}.{ext}"
            if not os.path.exists(lp):
                try:
                    pull_raw(f"{REPO_BASE}/part_{k:02d}.{ext}", lp,
                             ref=f"parts/{NAME}-{k:02d}")
                except Exception:
                    pull_raw(f"{REPO_BASE}/part_{k:02d}.{ext}", lp)
    if not os.path.exists(SB):
        pull_raw(f"{REPO_BASE}/storyboard.json", SB)
    beats = json.load(open(SB)); N = len(beats)
    afull = f"{wd}/audio_full.wav"
    if not os.path.exists(afull):
        acmd = [ff(), "-y"]
        for k in range(nc):
            acmd += ["-i", f"{wd}/part_{k:02d}.wav"]
        # NO loudnorm (it can shift timing). WAV concat = no priming = sample-exact.
        fc = "".join(f"[{k}:a]" for k in range(nc)) + f"concat=n={nc}:v=0:a=1[af]"
        acmd += ["-filter_complex", fc, "-map","[af]","-ar","48000","-ac","1","-c:a","pcm_s16le",afull]
        run(acmd)
    DUR = dur_of(afull)
    with open(f"{wd}/plist.txt","w") as f:
        for k in range(nc):
            f.write(f"file '{wd}/part_{k:02d}.mp4'\n")
    vfull = f"{wd}/video_nosound.mp4"
    run([ff(),"-y","-f","concat","-safe","0","-i",f"{wd}/plist.txt","-c","copy",vfull])
    # PASS 1: grade + fades (video only)
    graded = f"{wd}/graded.mp4"
    run([ff(),"-y","-i",vfull,"-vf",
         f"eq=contrast=1.03:saturation=1.06,vignette=PI/4.6,fade=t=in:st=0:d=0.4,fade=t=out:st={DUR-0.8:.2f}:d=0.8",
         "-c:v","libx264","-preset","ultrafast","-crf","22","-pix_fmt","yuv420p","-threads","2","-an",graded])
    # absolute caption times on the MEASURED video timeline (v_dur = master clock)
    captions = []
    t = 0.0
    for i in range(N):
        if beats[i].get("caption"):
            captions.append((i, t + beats[i].get("cap_start", 0.0), beats[i]["caption"]))
        t += beats[i].get("beat_len", beats[i].get("v_dur", beats[i].get("beat_dur", 0.0)))
    # PASS 2: overlay captions in BATCHES via -itsoffset (3s clips, memory-frugal)
    BATCH = 5
    cur = graded
    for bi in range(0, len(captions), BATCH):
        group = captions[bi:bi+BATCH]
        args = [ff(), "-y", "-i", cur]
        for j, (i, abs_t, cap) in enumerate(group):
            png = f"{wd}/cap_{bi+j:03d}.png"
            make_caption(cap[1], cap[2], png)
            hold = min(CAP_HOLD, max(DUR - abs_t - 0.05, 1.0))
            args += ["-itsoffset", f"{abs_t:.3f}", "-loop","1","-framerate","30","-t",f"{hold:.2f}","-i",png]
        parts = []
        last = "0:v"
        for j, (i, abs_t, cap) in enumerate(group):
            ypos = "H*0.30" if cap[2] == "pop" else "H-h-120"
            parts.append(f"[{j+1}:v]format=rgba[c{j}]")
            parts.append(f"[{last}][c{j}]overlay=x=(W-w)/2:y={ypos}:shortest=0:eof_action=pass[o{j}]")
            last = f"o{j}"
        fc = ";".join(parts)
        outb = f"{wd}/ov_{bi:03d}.mp4" if bi + BATCH < len(captions) else f"{wd}/overlaid.mp4"
        args += ["-filter_complex", fc, "-map", f"[{last}]",
                 "-c:v","libx264","-preset","ultrafast","-crf","22","-pix_fmt","yuv420p","-threads","2","-an",outb]
        run(args)
        cur = outb
        for j in range(len(group)):
            p = f"{wd}/cap_{bi+j:03d}.png"
            if os.path.exists(p): os.remove(p)
        print(f"overlay batch {bi//BATCH + 1} done ({len(group)} captions)")
    # PASS 3: ambient music bed (R14) + voice polish + sidechain ducking, then mux
    # generate a scored pad (chord progression, stereo) -> duck under the voice
    pad = f"{wd}/pad.wav"
    if not os.path.exists(pad):
        subprocess.run([sys.executable, "/home/user/tools/make_pad.py", f"{DUR:.1f}", pad], check=True)
    mixed = f"{wd}/audio_mixed.m4a"
    run([ff(),"-y","-i",afull,"-i",pad,
         "-filter_complex",
         # VOICE: de-rumble -> presence EQ -> light compression -> stereo -> asplit
         # (asplit is REQUIRED: a filter output feeding two consumers needs a fan-out)
         "[0:a]highpass=f=80,equalizer=f=8000:t=q:w=1:g=2,"
         "acompressor=threshold=-18dB:ratio=2.5:attack=5:release=80,"
         "aformat=channel_layouts=stereo,asplit=2[voice][voice2];"
         # PAD: level + fades, then DUCK under the voice (sidechain compression)
         # (v2 balance, user-approved 2026-08-19: pad 0.55 + gentle duck 0.05:3)
         "[1:a]volume=0.55,afade=t=in:st=0:d=4,afade=t=out:st={:.2f}:d=6[pd];"
         "[pd][voice]sidechaincompress=threshold=0.05:ratio=3:attack=15:release=250[duck];"
         "[voice2][duck]amix=inputs=2:duration=first:normalize=0,"
         "loudnorm=I=-16:TP=-1.5:LRA=11[aout]".format(max(DUR-6, 1)),
         "-map","[aout]","-c:a","aac","-b:a","160k","-ar","48000","-ac","2","-t",f"{DUR:.2f}",mixed])
    out = f"{BASE}/final.mp4"
    run([ff(),"-y","-i",cur,"-i",mixed,
         "-map","0:v","-map","1:a","-c:v","copy","-c:a","copy","-threads","2","-t",f"{DUR:.2f}",out])
    print("final built:", out, "duration:", round(DUR,1))
    # SIZE GUARD (R10): GitHub hard limit = 100MB per file. Escalate crf until
    # under LIMIT_MB (a single crf 26 pass left 6:38 videos at 110MB — rejected).
    LIMIT_MB = 95
    for crf in (26, 28, 30, 32):
        sz = os.path.getsize(out) / 1e6
        if sz <= LIMIT_MB:
            break
        print(f"final {sz:.1f}MB > {LIMIT_MB}MB limit — re-encoding lean (crf {crf})")
        lean = f"{wd}/final_lean.mp4"
        run([ff(), "-y", "-i", out, "-c:v", "libx264", "-preset", "veryfast",
             "-crf", str(crf), "-pix_fmt", "yuv420p", "-c:a", "copy", "-threads", "2", lean])
        os.replace(lean, out)
        print(f"shrunk to {os.path.getsize(out)/1e6:.1f}MB")
    if os.path.getsize(out) / 1e6 > LIMIT_MB:
        raise SystemExit("FINAL STILL OVER 95MB EVEN AT crf 32 — abort, do not push")
    print("caption schedule (absolute seconds, hold %.1fs):" % CAP_HOLD)
    for (i, abs_t, cap) in captions:
        print(f"  {cap[1]:32s} @ {abs_t:6.2f}s")
    pairs = [f"{REPO_BASE}/final.mp4", out]
    for f in ["thumbnail.jpg","script.md","metadata.md","storyboard.json","assets.json","state.json"]:
        p = f"{BASE}/{f}"
        if os.path.exists(p):
            pairs += [f"{REPO_BASE}/{f}", p]
    subprocess.run([sys.executable, "/home/user/tools/git_push.py", f"{NAME} FINAL (word-synced captions)", *pairs], check=True)
    st = load_state(); st["finalize_done"] = True; save_state(st)
    print("finalize + push done")

def status():
    st = load_state()
    print(json.dumps(st, indent=1) if st else "no state yet")

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "bootstrap": bootstrap()
    elif cmd == "storyboard": build_storyboard()
    elif cmd == "tts": tts_all()
    elif cmd == "render": render_chunk(int(sys.argv[2]))
    elif cmd == "assemble": assemble_chunk(int(sys.argv[2]))
    elif cmd == "finalize": finalize()
    elif cmd == "status": status()
    else: print(__doc__)
