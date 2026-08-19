#!/usr/bin/env python3
"""remix_test.py — rebuild the video_test audio mix with tunable pad level + ducking,
then mux onto the existing video and print band measurements.

Usage: python3 tools/remix_test.py [PAD_VOL] [DUCK_RATIO] [DUCK_THRESH]
  PAD_VOL     linear gain on the pad (default 0.55)
  DUCK_RATIO  sidechain ratio (default 3, lower = less ducking)
  DUCK_THRESH sidechain threshold linear (default 0.05)
"""
import subprocess, sys, os, glob, re

BASE = "/home/user/videos/video_test"
WD = os.path.join(BASE, "remix")
os.makedirs(WD, exist_ok=True)

PAD_VOL = float(sys.argv[1]) if len(sys.argv) > 1 else 0.55
DUCK_RATIO = float(sys.argv[2]) if len(sys.argv) > 2 else 3
DUCK_THRESH = float(sys.argv[3]) if len(sys.argv) > 3 else 0.05

def ff():
    return subprocess.check_output(["python3","-c","import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"]).decode().strip()

def run(args):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        print("CMD FAILED:", " ".join(args)[:400])
        print(r.stderr[-2000:])
        raise SystemExit(1)
    return r

def dur_of(path):
    r = run([ff(), "-i", path, "-f", "null", "-"])
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", r.stderr)
    h, mnt, s = map(float, m.groups())
    return h*3600 + mnt*60 + s

F = ff()

VIDEO = os.path.join(BASE, "final.mp4")
VIDEO_DUR = dur_of(VIDEO)

# 1) concat the per-caption voice beats -> 48k mono, padded to video duration
beats = sorted(glob.glob(os.path.join(BASE, "beat_*.wav")))
voice = os.path.join(WD, "voice_full.wav")
acmd = [F, "-y"]
for b in beats:
    acmd += ["-i", b]
fc = "".join(f"[{k}:a]" for k in range(len(beats))) + f"concat=n={len(beats)}:v=0:a=1[cat];[cat]apad=whole_dur={VIDEO_DUR:.3f}[af]"
run(acmd + ["-filter_complex", fc, "-map", "[af]", "-ar", "48000", "-ac", "1",
            "-c:a", "pcm_s16le", voice])
DUR = dur_of(voice)
print(f"voice concat: {len(beats)} beats, padded to {DUR:.2f}s (video {VIDEO_DUR:.2f}s)")

# 2) pad
pad = os.path.join(WD, "pad.wav")
if not os.path.exists(pad):
    run([sys.executable, "/home/user/tools/make_pad.py", f"{DUR:.1f}", pad])

# 3) mix
mixed = os.path.join(WD, "audio_mixed.m4a")
run([F, "-y", "-i", voice, "-i", pad, "-filter_complex",
     "[0:a]highpass=f=80,equalizer=f=8000:t=q:w=1:g=2,"
     "acompressor=threshold=-18dB:ratio=2.5:attack=5:release=80,"
     "aformat=channel_layouts=stereo,asplit=2[voice][voice2];"
     f"[1:a]volume={PAD_VOL},afade=t=in:st=0:d=4,afade=t=out:st={max(DUR-6,1):.2f}:d=6[pd];"
     f"[pd][voice]sidechaincompress=threshold={DUCK_THRESH}:ratio={DUCK_RATIO}:attack=15:release=250[duck];"
     "[voice2][duck]amix=inputs=2:duration=first:normalize=0,"
     "loudnorm=I=-16:TP=-1.5:LRA=11[aout]",
     "-map", "[aout]", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
     "-t", f"{DUR:.2f}", mixed])

# 4) mux onto existing video (copy streams)
out = os.path.join(BASE, f"final_mix_{PAD_VOL:g}.mp4")
run([F, "-y", "-i", os.path.join(BASE, "final.mp4"), "-i", mixed,
     "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "copy",
     "-t", f"{DUR:.2f}", out])

def band(path, expr, label):
    r = run([F, "-i", path, "-map", "0:a", "-af", expr + ",volumedetect",
             "-f", "null", "-"])
    mv = re.search(r"mean_volume: (-?\d+\.?\d*) dB", r.stderr)
    print(f"  {label:34s} {mv.group(1) if mv else '?'} dB")

def loudness(path):
    r = run([F, "-i", path, "-map", "0:a", "-af", "ebur128", "-f", "null", "-"])
    all_i = re.findall(r"I:\s+(-?\d+\.?\d*) LUFS", r.stderr)
    all_lra = re.findall(r"LRA:\s+(-?\d+\.?\d*) LU", r.stderr)
    i = all_i[-1] if all_i else "?"
    lra = all_lra[-1] if all_lra else "?"
    print(f"  integrated {i} LUFS, LRA {lra} LU")

print(f"\n=== SOURCES (pad vol {PAD_VOL}, duck ratio {DUCK_RATIO}, thresh {DUCK_THRESH}) ===")
print("voice_full.wav:")
band(voice, "highpass=f=300,lowpass=f=3000", "speech band 300-3k")
print("pad.wav (pre-duck, post-gain):")
band(pad,  "highpass=f=60,lowpass=f=250", "low band 60-250")
band(pad,  "highpass=f=300,lowpass=f=3000", "speech band 300-3k")
print("\n=== NEW MIX ===")
loudness(mixed)
band(mixed, "highpass=f=60,lowpass=f=250", "low band 60-250 (pad presence)")
band(mixed, "highpass=f=800,lowpass=f=3000", "voice band 800-3k")
print("\n=== OLD MIX (final.mp4, for comparison) ===")
loudness(os.path.join(BASE, "final.mp4"))
band(os.path.join(BASE, "final.mp4"), "highpass=f=60,lowpass=f=250", "low band 60-250 (pad presence)")
band(os.path.join(BASE, "final.mp4"), "highpass=f=800,lowpass=f=3000", "voice band 800-3k")
print(f"\nWROTE: {out}")
