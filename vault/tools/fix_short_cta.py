#!/usr/bin/env python3
"""fix_short_cta.py — patch an EXISTING Short with a proper end-CTA.

Adds BOTH:
  1. a prominent text CTA  (dark scrim bar + white text, bottom of 9:16 frame)
  2. a spoken CTA          (af_heart — same locked voice as the long-form, R5)

The narration/music bed fades to a low floor under the spoken CTA.
Used to recover Shorts whose CTA was missing/faint, or to re-cut CTAs.

Usage:
  python3 tools/fix_short_cta.py IN.mp4 OUT.mp4 ["Watch the full video on this channel."]
"""
import os, re, subprocess, sys

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def run(args, check=True):
    r = subprocess.run(args, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError("CMD FAILED: " + " ".join(args)[:140] + "\n" + r.stderr[-1500:])
    return r

def ff():
    return subprocess.check_output(["python3", "-c",
        "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"]).decode().strip()

def dur_of(p):
    r = subprocess.run([ff(), "-i", p], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", r.stderr)
    h, mi, s = m.groups(); return int(h) * 3600 + int(mi) * 60 + float(s)

def synth_cta(text, path):
    import numpy as np
    import soundfile as sf
    from kokoro_onnx import Kokoro
    CACHE = os.path.expanduser("~/.cache/kokoro")
    ko = Kokoro(f"{CACHE}/kokoro-v0_19.onnx", f"{CACHE}/voices-v1.0.bin")
    s, sr = ko.create(text, voice="af_heart", speed=1.0, lang="en-us")
    sf.write(path, s, sr)
    return len(s) / sr

def main():
    inp = sys.argv[1]
    out = sys.argv[2]
    text = sys.argv[3] if len(sys.argv) > 3 else "Watch the full video on this channel."
    DUR = dur_of(inp)
    work = os.path.dirname(out) or "."

    # ---- spoken CTA ----
    cta_wav = os.path.join(work, ".cta_voice.wav")
    cta_dur = synth_cta(text, cta_wav)
    cta_start = max(DUR - cta_dur - 0.2, 0.0)
    fade_st = max(cta_start - 0.5, 0.0)
    fade_d = 1.0
    cta_delay_ms = int(cta_start * 1000)
    print(f"DUR={DUR:.2f}s  cta_voice={cta_dur:.2f}s @ {cta_start:.2f}s  fade_st={fade_st:.2f}s")

    # ---- text CTA: dark rounded scrim + white bold text ----
    txt_png = os.path.join(work, ".cta_text.png")
    run(["magick", "-background", "none", "-font", FONT, "-pointsize", "64",
         "-fill", "white", "-stroke", "black", "-strokewidth", "6",
         "label:\u25b6  FULL VIDEO ON CHANNEL", "-trim", "+repage", txt_png])
    w = int(subprocess.check_output(["magick", "identify", "-format", "%w", txt_png]))
    h = int(subprocess.check_output(["magick", "identify", "-format", "%h", txt_png]))
    cta_png = os.path.join(work, ".cta_bar.png")
    run(["magick", "-size", f"{w+90}x{h+56}", "xc:none",
         "-fill", "rgba(0,0,0,0.72)",
         "-draw", f"roundrectangle 0,0 {w+89},{h+55} 28,28",
         txt_png, "-gravity", "center", "-composite", cta_png])
    print(f"text CTA bar: {w+90}x{h+56}")

    hold = min(cta_dur + 0.5, DUR - cta_start - 0.03)
    # ---- one-pass: video overlay (re-encode) + audio mix ----
    run([ff(), "-y", "-i", inp, "-i", cta_wav,
         "-loop", "1", "-framerate", "30", "-t", f"{hold:.2f}", "-i", cta_png,
         "-filter_complex",
         f"[0:v][2:v]overlay=x=(W-w)/2:y=H-240:enable='between(t,{cta_start:.3f},{cta_start+hold:.3f})'[v];"
         f"[0:a]volume='1-0.7*clip((t-{fade_st:.3f})/{fade_d:.3f},0,1)':eval=frame[old];"
         "[1:a]highpass=f=80,equalizer=f=8000:t=q:w=1:g=2,"
         "acompressor=threshold=-18dB:ratio=2.5:attack=5:release=80,"
         "volume=2.2,"
         f"adelay={cta_delay_ms}:all=1[cta];"
         "[old][cta]amix=inputs=2:duration=first:normalize=0,"
         "loudnorm=I=-16:TP=-1.5:LRA=11[aout]",
         "-map", "[v]", "-map", "[aout]",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p", "-r", "30",
         "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
         "-t", f"{DUR:.2f}", out])
    os.remove(cta_wav); os.remove(txt_png); os.remove(cta_png)
    print("patched ->", out, f"({os.path.getsize(out)/1e6:.1f}MB)")

if __name__ == "__main__":
    main()
