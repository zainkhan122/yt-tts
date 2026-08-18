#!/usr/bin/env python3
"""make_pad.py — generate a subtle, SCORED ambient music bed for under-voice use.
Chord progression (Am -> F -> C -> G, ~14s per chord, looping), slow breathing
LFO, gentle reverb, stereo. Deterministic — same duration => same bed.

Usage: python3 tools/make_pad.py DUR_SECONDS OUTPUT.wav
"""
import subprocess, sys, os

# chord -> list of (frequency, gain). Warm low pad voicing.
CHORDS = {
    "Am": [(110.00, 0.22), (164.81, 0.16), (220.00, 0.12), (329.63, 0.07)],
    "F":  [(87.31, 0.22), (130.81, 0.16), (174.61, 0.12), (261.63, 0.07)],
    "C":  [(130.81, 0.22), (196.00, 0.16), (261.63, 0.12), (392.00, 0.07)],
    "G":  [(98.00, 0.22), (146.83, 0.16), (196.00, 0.12), (293.66, 0.07)],
}
ORDER = ["Am", "F", "C", "G"]
SEG = 14.0   # seconds per chord

def ff():
    return subprocess.check_output(["python3","-c","import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"]).decode().strip()

def chord_expr(name, detune):
    parts = []
    for freq, gain in CHORDS[name]:
        f = freq * (1.0 + detune)
        parts.append(f"{gain}*sin(2*PI*{f}*t)")
    expr = "+".join(parts)
    # slow breathing amplitude LFO
    return f"({expr})*(0.60+0.40*sin(2*PI*0.07*t+{detune*40:.2f}))"

def main():
    dur = float(sys.argv[1]); out = sys.argv[2]
    F = ff()
    outdir = os.path.dirname(os.path.abspath(out))
    tmpdir = os.path.join(outdir, ".padparts")
    os.makedirs(tmpdir, exist_ok=True)
    parts = []
    idx = 0; t = 0.0
    while t < dur:
        seg_dur = min(SEG, dur - t)
        name = ORDER[idx % len(ORDER)]
        exprL = chord_expr(name, 0.0)
        exprR = chord_expr(name, 0.003)
        fc = f"aevalsrc={exprL}|{exprR}:d={seg_dur}"
        fade_out_st = max(seg_dur - 1.5, 0.5)
        af = (f"lowpass=f=900,"
              f"afade=t=in:st=0:d=1.5,afade=t=out:st={fade_out_st:.2f}:d=1.5")
        p = f"{tmpdir}/seg_{idx:03d}.wav"
        subprocess.run([F,"-y","-f","lavfi","-i",fc,"-af",af,
                        "-ac","2","-ar","48000","-c:a","pcm_s16le",p],
                       check=True, capture_output=True)
        parts.append(p)
        idx += 1; t += seg_dur
    with open(f"{tmpdir}/list.txt","w") as f:
        for p in parts:
            f.write(f"file '{p}'\n")
    # concat + short "room" reverb (25ms/50ms taps) + truncate to EXACT duration
    subprocess.run([F,"-y","-f","concat","-safe","0","-i",f"{tmpdir}/list.txt",
                    "-af","aecho=0.9:0.35:1200|2400:0.30|0.18",
                    "-t",f"{dur:.3f}",
                    "-ac","2","-ar","48000","-c:a","pcm_s16le",out],
                   check=True, capture_output=True)
    for p in parts:
        os.remove(p)
    os.remove(f"{tmpdir}/list.txt")
    os.rmdir(tmpdir)
    print("pad ->", out)

if __name__ == "__main__":
    main()
