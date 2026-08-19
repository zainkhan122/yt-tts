#!/usr/bin/env python3
"""make_short.py — build a 9:16 YouTube Short from a finished long-form video.

R21: Shorts are REPURPOSED from existing long-forms only (hook segment or the
R12 midpoint interrupt), 30-45s, keep word-synced captions + R20 audio balance.

USAGE:
  PIPE_VIDEO=/home/user/videos/video_013 python3 tools/make_short.py hook     [--dur 40]
  PIPE_VIDEO=/home/user/videos/video_013 python3 tools/make_short.py midpoint [--dur 40]

Design (vertical, professional blur-fill):
  - pulls only the parts (chunks) the segment needs from the repo into /tmp
  - caption-free video (parts are pre-caption) + voice-only wav
  - blur-fill 1080x1920: blurred/darkened 16:9 as bg, clean 1080x608 fg centered
  - BIG word-wrapped captions re-rendered at 9:16 (top area, white + black stroke)
  - R20 audio: voice polish + pad 0.55 + sidechain 0.05:3 + loudnorm -16 LUFS
  - end CTA "FULL VIDEO ON CHANNEL" in the last 3s
  - pushes vault/video_NNN/shorts/<name>.mp4 via git_push.py
"""
import json, math, os, re, subprocess, sys, time

sys.path.insert(0, "/home/user/tools")

BASE   = os.environ.get("PIPE_VIDEO", "/home/user/videos/video_013")
NAME   = os.path.basename(BASE)
SB     = os.path.join(BASE, "storyboard.json")
REPO   = "zainkhan122/yt-tts"
REPO_BASE = "vault/" + NAME
FONT   = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
CHUNK  = 26
FPS    = 30
CAP_HOLD = 2.6
W, H   = 1080, 1920
FG_H   = 608          # 16:9 foreground height at 1080 wide
FG_Y   = (H - FG_H) // 2

TOKEN = open(os.path.expanduser("~/secrets/github_pat.txt")).read().strip()

def run(args, check=True):
    r = subprocess.run(args, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError("CMD FAILED: " + " ".join(args)[:140] + "\n" + r.stderr[-1500:])
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
    CACHE = os.path.expanduser("~/.cache/kokoro")
    os.makedirs(CACHE, exist_ok=True)
    model, voices = f"{CACHE}/kokoro-v0_19.onnx", f"{CACHE}/voices-v1.0.bin"
    if not os.path.exists(model):
        run(["curl", "-sL", "--max-time", "550", "-o", model,
             "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/kokoro-v0_19.onnx"])
    if not os.path.exists(voices):
        run(["curl", "-sL", "--max-time", "120", "-o", voices,
             "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"])

def synth_cta(text, path):
    """Spoken end-CTA in the SAME locked voice (af_heart) as the long-form (R5)."""
    import numpy as np
    import soundfile as sf
    from kokoro_onnx import Kokoro
    CACHE = os.path.expanduser("~/.cache/kokoro")
    ko = Kokoro(f"{CACHE}/kokoro-v0_19.onnx", f"{CACHE}/voices-v1.0.bin")
    s, sr = ko.create(text, voice="af_heart", speed=1.0, lang="en-us")
    sf.write(path, s, sr)
    return len(s) / sr

def pull_raw(repo_path, local):
    os.makedirs(os.path.dirname(local), exist_ok=True)
    import urllib.request
    req = urllib.request.Request(f"https://raw.githubusercontent.com/{REPO}/main/{repo_path}",
                                 headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=300) as r, open(local, "wb") as f:
        f.write(r.read())

def beats_timeline(beats):
    """absolute start time of each beat; returns list of starts + total dur."""
    starts, t = [], 0.0
    for b in beats:
        starts.append(t)
        t += b.get("beat_len", b.get("v_dur", b.get("beat_dur", 0.0)))
    return starts, t

def pick_segment(beats, kind, target):
    starts, total = beats_timeline(beats)
    N = len(beats)
    def end_of(i):
        return starts[i] + beats[i].get("beat_len", beats[i].get("v_dur", beats[i].get("beat_dur", 0.0)))
    if kind == "hook":
        a = 0
        b = 0
        while b < N and end_of(b) <= target:
            b += 1
        # ensure at least ~30s if target not reached (shouldn't happen)
        if b < N and end_of(b) - starts[0] < 30:
            b += 1
    elif kind == "midpoint":
        mid = N // 2
        mid_t = starts[mid]
        want_start = max(0.0, mid_t - target * 0.45)
        a = 0
        while a < N and starts[a] < want_start:
            a += 1
        b = a
        seg_start = starts[a]
        while b < N and end_of(b) - seg_start <= target:
            b += 1
        if b < N and end_of(b) - seg_start < 30:
            b += 1
    else:
        raise SystemExit("kind must be hook|midpoint")
    a = max(0, a); b = min(N, b)
    seg_start = starts[a]
    seg_dur = end_of(b - 1) - seg_start
    return a, b, seg_start, seg_dur

def wrap(disp, maxchars=16):
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
    lines = wrap(disp, 16)
    pngs = []
    for i, ln in enumerate(lines):
        fs = int(min(84, 1000 / (len(ln) * 0.62)))
        p = f"{path}.{i}.png"
        run(["magick", "-background", "none", "-font", FONT, "-pointsize", str(fs),
             "-fill", "white", "-stroke", "black", "-strokewidth", "6", "label:" + ln,
             "-trim", "+repage", p])
        pngs.append(p)
    if len(pngs) == 1:
        run(["magick", pngs[0], path])
    else:
        run(["magick", "-background", "none"] + pngs + ["-gravity", "north", "-smush", "14",
             "-append", path])
    for p in pngs:
        os.remove(p)
    return path

def dur_of(p):
    r = subprocess.run([ff(), "-i", p], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", r.stderr)
    h, mi, s = m.groups(); return int(h) * 3600 + int(mi) * 60 + float(s)

def main():
    bootstrap()
    seg_kind = sys.argv[1] if len(sys.argv) > 1 else "hook"
    target = 40.0
    if "--dur" in sys.argv:
        target = float(sys.argv[sys.argv.index("--dur") + 1])
    target = max(30.0, min(target, 45.0))
    if not os.path.exists(SB):
        pull_raw(f"{REPO_BASE}/storyboard.json", SB)
    beats = json.load(open(SB))
    a, b, seg_start, seg_dur = pick_segment(beats, seg_kind, target)
    print(f"segment [{seg_kind}] beats {a}..{b-1}  start={seg_start:.2f}s  dur={seg_dur:.2f}s")

    # ---- spoken end-CTA (af_heart) — every Short stands alone, so the voice
    #      itself asks the viewer to watch the full video ----
    CTA_TEXT = "Watch the full video on this channel."
    CTA_DELAY_END = 0.15          # gap between CTA voice end and short end
    FADE_D = 1.6                  # narration fade-out length into the CTA
    cta_dur = None

    # work entirely in /tmp (never bloats the workspace snapshot)
    work = f"/tmp/short_make/{NAME}"
    if os.path.isdir(work):
        import shutil; shutil.rmtree(work)
    os.makedirs(work)

    # synthesize the spoken CTA now so its real duration drives the timing
    cta_wav = f"{work}/cta.wav"
    cta_dur = synth_cta(CTA_TEXT, cta_wav)
    cta_start = max(seg_dur - cta_dur - CTA_DELAY_END, 0.0)
    fade_st = max(cta_start - 0.4, 0.0)   # narration fades just before the CTA voice
    print(f"voice CTA: {cta_dur:.2f}s @ {cta_start:.2f}s (fade narration from {fade_st:.2f}s)")

    # pull the parts (chunks) this segment spans; the concat of those parts
    # starts at the first pulled chunk's first beat, so rebase seg_start to it.
    need_chunks = sorted({i // CHUNK for i in range(a, b)})
    starts, _total = beats_timeline(beats)
    local_start = seg_start - starts[need_chunks[0] * CHUNK]
    vparts, aparts = [], []
    for k in need_chunks:
        vp, ap = f"{work}/part_{k:02d}.mp4", f"{work}/part_{k:02d}.wav"
        pull_raw(f"{REPO_BASE}/part_{k:02d}.mp4", vp)
        pull_raw(f"{REPO_BASE}/part_{k:02d}.wav", ap)
        vparts.append(vp); aparts.append(ap)
    print(f"pulled parts {need_chunks}")

    # concat video (copy) + audio (pcm) for the needed chunks
    vlist = f"{work}/vlist.txt"
    with open(vlist, "w") as f:
        for vp in vparts:
            f.write(f"file '{vp}'\n")
    vfull = f"{work}/vfull.mp4"
    run([ff(), "-y", "-f", "concat", "-safe", "0", "-i", vlist, "-c", "copy", vfull])
    afull = f"{work}/afull.wav"
    acmd = [ff(), "-y"]
    for ap in aparts:
        acmd += ["-i", ap]
    acmd += ["-filter_complex",
             "".join(f"[{i}:a]" for i in range(len(aparts))) + f"concat=n={len(aparts)}:v=0:a=1[aout]",
             "-map", "[aout]", "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", afull]
    run(acmd)

    # ---- vertical blur-fill video ----
    vseg = f"{work}/vseg.mp4"
    vf = (f"[0:v]split=2[bgs][fgs];"
          f"[bgs]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
          f"gblur=sigma=18,eq=brightness=-0.32[bg];"
          f"[fgs]scale={W}:{FG_H}:flags=lanczos,setsar=1,"
          f"eq=contrast=1.03:saturation=1.06,vignette=PI/5,"
          f"fade=t=in:st=0:d=0.4,fade=t=out:st={seg_dur-0.6:.2f}:d=0.6[fg];"
          f"[bg][fg]overlay=x=(W-w)/2:y={FG_Y},setsar=1[base]")
    run([ff(), "-y", "-ss", f"{local_start:.3f}", "-t", f"{seg_dur:.3f}", "-i", vfull,
         "-filter_complex", vf, "-map", "[base]", "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "23", "-pix_fmt", "yuv420p", "-r", str(FPS), "-an", vseg])

    # ---- captions (word-synced, big 9:16) ----
    caps = []
    for i in range(a, b):
        if beats[i].get("caption"):
            rel = (beats[i].get("cap_start", 0.0)) + (sum(
                beats[j].get("beat_len", beats[j].get("v_dur", beats[j].get("beat_dur", 0.0)))
                for j in range(a, i)))
            if 0 <= rel < cta_start - 0.3:
                caps.append((rel, beats[i]["caption"][1]))
    print(f"captions in segment: {len(caps)}")
    cur = vseg
    args = [ff(), "-y", "-i", cur]
    fi = 0
    for rel, disp in caps:
        png = f"{work}/scap_{fi:03d}.png"
        render_caption(disp, png)
        hold = min(CAP_HOLD, seg_dur - rel - 0.05)
        args += ["-itsoffset", f"{rel:.3f}", "-loop", "1", "-framerate", "30", "-t", f"{hold:.2f}", "-i", png]
        fi += 1
    # end CTA (text overlay, aligned with the spoken CTA)
    cta = f"{work}/cta.png"
    run(["magick", "-background", "none", "-font", FONT, "-pointsize", "62",
         "-fill", "white", "-stroke", "black", "-strokewidth", "6",
         "label:\u25b6  FULL VIDEO ON CHANNEL", "-trim", "+repage", cta])
    cta_hold = min(cta_dur + 0.4, seg_dur - cta_start - 0.03)
    args += ["-itsoffset", f"{cta_start:.3f}", "-loop", "1", "-framerate", "30", "-t", f"{cta_hold:.2f}", "-i", cta]
    fc = []
    last = "0:v"
    for j in range(fi + 1):
        if j < fi:
            ypos = "H*0.22"
        else:
            ypos = f"H-180"
        fc.append(f"[{j+1}:v]format=rgba[c{j}]")
        fc.append(f"[{last}][c{j}]overlay=x=(W-w)/2:y={ypos}:shortest=0:eof_action=pass[o{j}]")
        last = f"o{j}"
    vcap = f"{work}/vcap.mp4"
    args += ["-filter_complex", ";".join(fc), "-map", f"[{last}]",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
             "-r", str(FPS), "-an", vcap]
    run(args)
    cur = vcap

    # ---- audio: R20 chain + spoken CTA ----
    # narration fades out into the CTA; pad ducks under BOTH narration and the
    # CTA voice (the sidechain key is narration+CTA) so the CTA is never buried.
    aseg = f"{work}/aseg.wav"
    run([ff(), "-y", "-ss", f"{local_start:.3f}", "-t", f"{seg_dur:.3f}", "-i", afull,
         "-c:a", "pcm_s16le", aseg])
    pad = f"{work}/pad.wav"
    subprocess.run([sys.executable, "/home/user/tools/make_pad.py", f"{seg_dur:.1f}", pad], check=True)
    cta_delay_ms = int(cta_start * 1000)
    amix = f"{work}/amix.m4a"
    run([ff(), "-y", "-i", aseg, "-i", pad, "-i", cta_wav, "-filter_complex",
         "[0:a]afade=t=out:st={fade_st:.2f}:d={fade_d:.2f},"
         "highpass=f=80,equalizer=f=8000:t=q:w=1:g=2,"
         "acompressor=threshold=-18dB:ratio=2.5:attack=5:release=80,"
         "aformat=channel_layouts=stereo,asplit=2[voice][voice2];"
         "[2:a]highpass=f=80,equalizer=f=8000:t=q:w=1:g=2,"
         "acompressor=threshold=-18dB:ratio=2.5:attack=5:release=80,"
         "adelay={cta_delay_ms}:all=1,aformat=channel_layouts=stereo,asplit=2[cta][cta2];"
         "[1:a]volume=0.55,afade=t=in:st=0:d=3,afade=t=out:st={pad_out:.2f}:d=3[pd];"
         "[voice][cta]amix=inputs=2:duration=first:normalize=0[key];"
         "[pd][key]sidechaincompress=threshold=0.05:ratio=3:attack=15:release=250[duck];"
         "[voice2][cta2][duck]amix=inputs=3:duration=first:normalize=0,"
         "loudnorm=I=-16:TP=-1.5:LRA=11[aout]".format(fade_st=fade_st, fade_d=FADE_D,
                                                      cta_delay_ms=cta_delay_ms,
                                                      pad_out=max(seg_dur - 3, 1)),
         "-map", "[aout]", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
         "-t", f"{seg_dur:.2f}", amix])

    # ---- mux ----
    os.makedirs(f"{BASE}/shorts", exist_ok=True)
    out_name = f"short_{seg_kind}.mp4"
    out = f"{work}/{out_name}"
    run([ff(), "-y", "-i", cur, "-i", amix, "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-c:a", "copy", "-t", f"{seg_dur:.2f}", out])

    # ---- verify ----
    r = subprocess.run([ff(), "-i", out], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", r.stderr)
    d = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    ok_dim = re.search(r"1080x1920", r.stderr) is not None
    ok_fps = re.search(r"30 fps", r.stderr) is not None
    ok_aud = "aac" in r.stderr
    print(f"short built: {out}  dur={d:.2f}s  {1080}x{1920 if ok_dim else '?'} fps=30 aud={ok_aud}")
    if not (ok_dim and ok_fps and ok_aud and 28 <= d <= 47):
        raise SystemExit("SHORT VERIFY FAILED")

    # ---- push ----
    subprocess.run([sys.executable, "/home/user/tools/git_push.py",
                    f"{NAME} {seg_kind} short",
                    f"{REPO_BASE}/shorts/{out_name}", out], check=True)
    # local copy for preview
    import shutil
    shutil.copyfile(out, f"{BASE}/shorts/{out_name}")
    shutil.rmtree(work, ignore_errors=True)
    print(f"pushed + saved {BASE}/shorts/{out_name}")
    # print caption schedule
    for rel, disp in caps:
        print(f"  {disp:32s} @ {rel:6.2f}s")

if __name__ == "__main__":
    main()
