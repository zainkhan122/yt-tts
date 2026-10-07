#!/usr/bin/env python3
"""
Royalty-free audio kit for the viral-short demo.

Synthesizes (deterministically, seeded) a 120 BPM A-minor music bed with a
"drop", plus a set of social-video SFX (impact, whoosh, pop, click, typing,
ding, riser, sparkle). Everything is generated from scratch with numpy/scipy,
so there are no licensing questions and the beat grid is known exactly
(beat = 60 / BPM seconds), which lets the HyperFrames composition sync cuts
to the music without guessing.

Usage:
  python3 tools/synth_audio.py --out assets/audio --duration 23.5 --drop 16.0
"""
import argparse
import os

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

SR = 44100
RNG = np.random.default_rng(20261006)  # seeded -> identical output every run


# ----------------------------------------------------------------- helpers
def tvec(dur):
    return np.arange(int(round(dur * SR))) / SR


def norm(x, peak=1.0):
    m = np.max(np.abs(x)) or 1.0
    return x / m * peak


def band(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], btype="band", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, btype="high", fs=SR, output="sos"), x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, btype="low", fs=SR, output="sos"), x)


def place(buf, clip, at, gain=1.0):
    """Mix `clip` into `buf` starting at time `at` (seconds)."""
    i = int(round(at * SR))
    if i >= len(buf):
        return
    n = min(len(clip), len(buf) - i)
    if buf.ndim == 2 and clip.ndim == 1:
        buf[i : i + n] += clip[:n, None] * gain
    else:
        buf[i : i + n] += clip[:n] * gain


def note(name):
    """Note name like 'A2' / 'C#4' -> Hz (A4 = 440)."""
    names = {"C": -9, "C#": -8, "D": -7, "D#": -6, "E": -5, "F": -4,
             "F#": -3, "G": -2, "G#": -1, "A": 0, "A#": 1, "B": 2}
    pitch, octave = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((names[pitch] + (octave - 4) * 12) / 12)


def saw(freq, t, voices=3, detune_cents=9, max_h=36, phase_seed=0.0):
    """Band-limited-ish supersaw via additive synthesis (deterministic phases)."""
    out = np.zeros_like(t)
    for v in range(voices):
        cents = (v - (voices - 1) / 2) * detune_cents
        f = freq * 2 ** (cents / 1200)
        nh = int(max(1, min(max_h, 9000 // f)))
        for h in range(1, nh + 1):
            out += np.sin(2 * np.pi * f * h * t + (v + 1) * 1.31 * h + phase_seed) / h
    return out / voices


# ----------------------------------------------------------------- drums
def kick():
    t = tvec(0.42)
    f = 44 + 125 * np.exp(-t * 32)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.0)
    click = band(RNG.standard_normal(len(t)), 1500, 6000) * np.exp(-t * 700) * 0.6
    return np.tanh(2.4 * (body + click)) / np.tanh(2.4)


def clap():
    t = tvec(0.32)
    n = len(t)
    noise = norm(band(RNG.standard_normal(n), 900, 3800))
    env = np.zeros(n)
    for k, off in enumerate((0.0, 0.010, 0.021)):
        i = int(off * SR)
        env[i:] += np.exp(-(t[i:] - off) * 190) * (0.75 if k < 2 else 1.0)
    i = int(0.021 * SR)
    env[i:] += np.exp(-(t[i:] - 0.021) * 15) * 0.38
    body = np.sin(2 * np.pi * 185 * t) * np.exp(-t * 32) * 0.35
    return norm(noise * env + body)


def hat(open_=False):
    t = tvec(0.28 if open_ else 0.055)
    x = norm(hp(RNG.standard_normal(len(t)), 7200, order=4))
    return x * np.exp(-t * (13 if open_ else 75))


def crash():
    t = tvec(2.2)
    x = norm(hp(RNG.standard_normal(len(t)), 4200, order=2))
    return x * np.exp(-t * 2.3) * (1 - np.exp(-t * 400))


# ----------------------------------------------------------------- music bed
def music(duration, bpm, drop):
    beat = 60.0 / bpm
    bar = beat * 4
    n = int(round(duration * SR))
    L = np.zeros(n)
    R = np.zeros(n)
    t = np.arange(n) / SR

    progression = [  # Am - F - C - G (one chord per bar)
        ("A1", ["A3", "C4", "E4"]),
        ("F1", ["F3", "A3", "C4"]),
        ("C2", ["G3", "C4", "E4"]),
        ("G1", ["G3", "B3", "D4"]),
    ]

    # kick times + sidechain envelope
    kick_times = []
    k = kick()
    nbeats = int(duration / beat) + 1
    for b in range(nbeats):
        tb = b * beat
        # tension: drop the kick on the 2 beats right before the drop
        if drop - 2 * beat - 1e-6 <= tb < drop - 1e-6:
            continue
        kick_times.append(tb)
        place(L, k, tb, 0.95)
        place(R, k, tb, 0.95)
    side = np.ones(n)
    for kt in kick_times:
        i = int(kt * SR)
        seg = t[i:] - kt
        side[i:] = np.minimum(side[i:], 1 - 0.72 * np.exp(-seg / 0.085))

    # clap on 2 & 4, + snare roll into the drop
    c = clap()
    for b in range(nbeats):
        tb = b * beat
        if b % 4 in (1, 3) and not (drop - 2 * beat <= tb < drop):
            place(L, c, tb, 0.55)
            place(R, c, tb, 0.55)
    roll_start = drop - 2 * beat
    steps = 16
    for s in range(steps):
        ts = roll_start + s * (2 * beat / steps)
        g = 0.18 + 0.5 * (s / steps) ** 1.6
        place(L, c, ts, g)
        place(R, c, ts, g)

    # hats: closed 8ths (off-beats louder); open hats on off-beats after the drop
    hc, ho = hat(False), hat(True)
    for e in range(int(duration / (beat / 2)) + 1):
        te = e * beat / 2
        off = e % 2 == 1
        if te >= drop and off:
            place(L, ho, te, 0.16)
            place(R, ho, te, 0.22)
        else:
            g = 0.20 if off else 0.10
            place(L, hc, te, g * 0.8)
            place(R, hc, te, g)
    # 16th shuffle hats after the drop for lift
    for s in range(int((duration - drop) / (beat / 4)) + 1):
        ts = drop + s * beat / 4
        if s % 2 == 1:
            place(L, hc, ts, 0.07)
            place(R, hc, ts, 0.05)

    # crash on the drop and on the very first frame (hook energy)
    cr = crash()
    place(L, cr, 0.0, 0.22)
    place(R, cr, 0.0, 0.22)
    place(L, cr, drop, 0.30)
    place(R, cr, drop, 0.30)

    # harmonic layers, bar by bar
    bass = np.zeros(n)
    padL = np.zeros(n)
    padR = np.zeros(n)
    arp = np.zeros(n)
    nbars = int(np.ceil(duration / bar))
    for bi in range(nbars):
        root, chord = progression[bi % 4]
        t0 = bi * bar
        i0 = int(t0 * SR)
        i1 = min(n, int((t0 + bar) * SR))
        if i0 >= n:
            break
        tt = t[i0:i1] - t0
        # pad: soft supersaw chord, slow attack, low-passed later
        att = 1 - np.exp(-tt / 0.18)
        rel = np.clip((bar - tt) / 0.12, 0, 1)
        for j, nm in enumerate(chord):
            f = note(nm)
            padL[i0:i1] += saw(f, tt, voices=3, detune_cents=11, max_h=24, phase_seed=j) * att * rel
            padR[i0:i1] += saw(f * 1.0015, tt, voices=3, detune_cents=13, max_h=24, phase_seed=j + 3) * att * rel
        # bass: 8th-note pulses (sub sine + upper saw so phones can hear it)
        fr = note(root)
        for e in range(8):
            te = e * beat / 2
            m = (tt >= te) & (tt < te + beat / 2)
            local = tt[m] - te
            env = np.exp(-local * 6.5) * (1 - np.exp(-local * 300))
            sub = np.sin(2 * np.pi * fr * local)
            up = saw(fr * 2, local, voices=1, max_h=12)
            bass[i0:i1][m] += (0.85 * sub + 0.35 * up) * env
        # arp: 16th notes cycling chord tones one octave up (enters bar 2)
        if t0 >= bar:
            tones = [note(nm) * 2 for nm in chord] + [note(chord[1]) * 4]
            for s in range(16):
                ts = s * beat / 4
                m = (tt >= ts) & (tt < ts + beat / 4)
                local = tt[m] - ts
                f = tones[(s * 3 + bi) % len(tones)]
                env = np.exp(-local * 22) * (1 - np.exp(-local * 900))
                tone = np.sin(2 * np.pi * f * local) + 0.25 * np.sin(4 * np.pi * f * local)
                level = 0.55 if t0 + ts >= drop else 0.32
                arp[i0:i1][m] += tone * env * level

    padL = lp(padL, 1600)
    padR = lp(padR, 1600)
    bass = lp(bass, 900)
    # lift the pad a little after the drop
    lift = np.where(t >= drop, 1.25, 1.0)

    L += side * (0.42 * bass + 0.085 * padL * lift + 0.12 * arp)
    R += side * (0.42 * bass + 0.085 * padR * lift + 0.10 * arp)

    mix = np.stack([L, R], axis=1)
    mix = np.tanh(1.3 * mix) / np.tanh(1.3)  # gentle glue / soft clip
    return norm(mix, 0.89)


# ----------------------------------------------------------------- SFX
def sfx_impact():
    t = tvec(1.8)
    f = 28 + 62 * np.exp(-t * 6)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.4)
    crack = lp(RNG.standard_normal(len(t)), 3500) * np.exp(-t * 22) * 0.9
    tail = band(RNG.standard_normal(len(t)), 150, 900) * np.exp(-t * 3.2) * 0.35
    return norm(np.tanh(2.0 * (boom + crack + tail)), 0.95)


def sfx_whoosh(dur=0.62):
    t = tvec(dur)
    n = len(t)
    noise = RNG.standard_normal(n)
    out = np.zeros(n)
    block = 512
    for i in range(0, n, block):
        p = i / n
        center = 450 + 2400 * np.sin(np.pi * min(1.0, p * 1.15)) ** 1.5
        lo, hi = center * 0.6, min(center * 1.6, SR / 2 - 100)
        seg = noise[max(0, i - 2048) : i + block]
        y = band(seg, lo, hi)[-(min(block, n - i)) :]
        out[i : i + len(y)] = y
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2.2
    return norm(out * env, 0.9)


def sfx_pop():
    t = tvec(0.13)
    f = 420 + 650 * np.exp(-t * 55)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 42)
    return norm(x, 0.85)


def sfx_click():
    t = tvec(0.06)
    x = band(RNG.standard_normal(len(t)), 1800, 7000) * np.exp(-t * 260)
    x += np.sin(2 * np.pi * 2300 * t) * np.exp(-t * 160) * 0.5
    return norm(x, 0.8)


def sfx_typing(dur=1.7):
    buf = np.zeros(int(dur * SR))
    tt = 0.02
    while tt < dur - 0.06:
        t = tvec(0.05)
        key = band(RNG.standard_normal(len(t)), 2000, 6500) * np.exp(-t * 420)
        thock = np.sin(2 * np.pi * (160 + RNG.uniform(-20, 20)) * t) * np.exp(-t * 140) * 0.6
        place(buf, norm(key + thock), tt, RNG.uniform(0.45, 0.9))
        tt += RNG.uniform(0.065, 0.13)
    return norm(buf, 0.75)


def sfx_ding():
    t = tvec(1.4)
    f0 = note("C6")
    parts = [(1.0, 1.0, 3.2), (2.0, 0.35, 5.0), (2.76, 0.45, 6.5), (5.4, 0.18, 10.0)]
    x = sum(a * np.sin(2 * np.pi * f0 * r * t) * np.exp(-t * d) for r, a, d in parts)
    x *= 1 - np.exp(-t * 600)
    return norm(x, 0.8)


def sfx_riser(dur=2.0):
    t = tvec(dur)
    n = len(t)
    noise = RNG.standard_normal(n)
    out = np.zeros(n)
    block = 1024
    for i in range(0, n, block):
        cutoff = 300 + 7000 * (i / n) ** 2
        seg = noise[max(0, i - 4096) : i + block]
        y = hp(seg, cutoff)[-(min(block, n - i)) :]
        out[i : i + len(y)] = y
    f = 220 * (8 ** (t / dur))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.35
    env = (t / dur) ** 2.2
    x = (norm(out) * 0.8 + tone) * env
    x[-int(0.008 * SR) :] *= np.linspace(1, 0, int(0.008 * SR))
    return norm(x, 0.85)


def sfx_sparkle(dur=0.9):
    buf = np.zeros(int(dur * SR))
    for k in range(11):
        at = 0.03 + k * 0.065 + RNG.uniform(-0.015, 0.015)
        t = tvec(0.18)
        f = RNG.uniform(2600, 5200)
        place(buf, np.sin(2 * np.pi * f * t) * np.exp(-t * 30), at, 0.5 * (1 - k / 14))
    return norm(buf, 0.6)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="assets/audio")
    ap.add_argument("--duration", type=float, default=23.5)
    ap.add_argument("--bpm", type=float, default=120.0)
    ap.add_argument("--drop", type=float, default=16.0, help="seconds; snapped to the bar grid")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    bar = 4 * 60.0 / a.bpm
    drop = round(a.drop / bar) * bar  # keep the drop on a downbeat
    sf.write(os.path.join(a.out, "music.wav"), music(a.duration, a.bpm, drop), SR, subtype="PCM_16")
    kit = {
        "sfx-impact.wav": sfx_impact(),
        "sfx-whoosh.wav": sfx_whoosh(),
        "sfx-pop.wav": sfx_pop(),
        "sfx-click.wav": sfx_click(),
        "sfx-typing.wav": sfx_typing(),
        "sfx-ding.wav": sfx_ding(),
        "sfx-riser.wav": sfx_riser(),
        "sfx-sparkle.wav": sfx_sparkle(),
    }
    for name, x in kit.items():
        sf.write(os.path.join(a.out, name), x, SR, subtype="PCM_16")
    print(f"music: {a.duration}s @ {a.bpm} BPM, drop snapped to {drop:.2f}s; sfx: {', '.join(kit)}")


if __name__ == "__main__":
    main()
