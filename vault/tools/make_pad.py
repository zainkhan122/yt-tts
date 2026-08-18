#!/usr/bin/env python3
"""make_pad.py — generate a subtle ambient drone pad for under-voice music.
Usage: python3 tools/make_pad.py DUR_SECONDS OUTPUT.wav
Deterministic-ish: a soft low chord with slow movement, stereo, lowpassed.
"""
import subprocess, sys

def ff():
    return subprocess.check_output(["python3","-c","import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"]).decode().strip()

def main():
    dur = float(sys.argv[1])
    out = sys.argv[2]
    F = ff()
    fade_in = min(4, dur*0.1)
    fade_out = min(6, dur*0.15)
    # warm minor-ish chord: A1(55) + A2(110) + E3(164.81) + A3(220), detuned,
    # slow breathing LFO. Two channels slightly different for width.
    expr = (
        "(0.22*sin(2*PI*55*t)+0.18*sin(2*PI*110.3*t)+0.15*sin(2*PI*164.8*t)+0.10*sin(2*PI*220.6*t))*"
        "(0.65+0.35*sin(2*PI*0.06*t))"
    )
    expr2 = (
        "(0.22*sin(2*PI*55*t)+0.18*sin(2*PI*109.7*t)+0.15*sin(2*PI*165.2*t)+0.10*sin(2*PI*219.4*t))*"
        "(0.65+0.35*sin(2*PI*0.07*t+1.3))"
    )
    fc = f"aevalsrc={expr}|{expr2}:d={dur}"
    af = (f"lowpass=f=700,"
          f"afade=t=in:st=0:d={fade_in},"
          f"afade=t=out:st={dur-fade_out}:d={fade_out},"
          f"volume=0.9")
    subprocess.run([F,"-y","-f","lavfi","-i",fc,"-af",af,
                    "-ac","2","-ar","48000","-c:a","pcm_s16le",out], check=True)
    print("pad ->", out)

if __name__ == "__main__":
    main()
