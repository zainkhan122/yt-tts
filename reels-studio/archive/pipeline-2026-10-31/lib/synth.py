"""
Royalty-free music + SFX engine (numpy/scipy, fully deterministic per seed).

Why synthesize instead of downloading "free" music?
  * zero licensing / Content ID risk on every platform (YouTube, TikTok, Reels, FB),
  * the beat grid is known exactly, so cuts and hits can land on beats,
  * every video gets a different key / progression / groove (seeded) -> no two
    uploads share the same bed (helps against "repetitive / template" signals).
It is simple production music, not a hit record. For bigger moments swap in a
licensed track (see the report) or add a trending sound inside the app.
"""
import numpy as np
from scipy.signal import butter, sosfilt

SR = 48000

# chord tones as MIDI numbers (A3 = 57), bass root as MIDI (A1 = 33)
PROGRESSIONS = {
    "minor_pop": [(33, [57, 60, 64]), (29, [53, 57, 60]), (36, [55, 60, 64]), (31, [55, 59, 62])],  # Am F C G
    "uplift":    [(36, [55, 60, 64]), (31, [55, 59, 62]), (33, [57, 60, 64]), (29, [53, 57, 60])],  # C G Am F
    "dark":      [(33, [57, 60, 64]), (33, [57, 60, 65]), (29, [53, 57, 60]), (28, [56, 59, 64])],  # Am Am(b6) F E
    "chill":     [(26, [53, 57, 60, 62]), (31, [53, 55, 59, 62]), (36, [55, 59, 60, 64]), (33, [55, 57, 60, 64])],  # Dm7 G7 Cmaj7 Am7
}

STYLES = {
    #            kick    clap   hats  arp    pad    bass  swing keys  arp_lvl
    "pulse":     dict(kick="four", clap=True, hats=8, arp=True, pad=0.085, bass=0.42, swing=0.0, keys=False, arp_level=0.32),
    "tension":   dict(kick="half", clap=False, hats=8, arp=True, pad=0.11, bass=0.40, swing=0.0, keys=False, arp_level=0.18),
    "cinematic": dict(kick="half", clap=True, hats=4, arp=True, pad=0.13, bass=0.30, swing=0.0, keys=False, arp_level=0.26),
    "chill":     dict(kick="half", clap=True, hats=8, arp=False, pad=0.10, bass=0.30, swing=0.14, keys=True, arp_level=0.0),
}


# ----------------------------------------------------------------- helpers
def tvec(dur):
    return np.arange(int(round(dur * SR))) / SR


def norm(x, peak=1.0):
    m = float(np.max(np.abs(x))) or 1.0
    return x / m * peak


def _sos(kind, f, order=2):
    return butter(order, f, btype=kind, fs=SR, output="sos")


def band(x, lo, hi, order=2):
    return sosfilt(_sos("band", [lo, hi], order), x)


def hp(x, f, order=2):
    return sosfilt(_sos("high", f, order), x)


def lp(x, f, order=2):
    return sosfilt(_sos("low", f, order), x)


def place(buf, clip, at, gain=1.0):
    i = int(round(at * SR))
    if i >= len(buf) or i < 0:
        return
    n = min(len(clip), len(buf) - i)
    if buf.ndim == 2 and clip.ndim == 1:
        buf[i:i + n] += clip[:n, None] * gain
    else:
        buf[i:i + n] += clip[:n] * gain


def mhz(m, shift=0):
    return 440.0 * 2 ** ((m + shift - 69) / 12)


def saw(freq, t, voices=3, detune_cents=9, max_h=24, phase_seed=0.0):
    out = np.zeros_like(t)
    for v in range(voices):
        cents = (v - (voices - 1) / 2) * detune_cents
        f = freq * 2 ** (cents / 1200)
        nh = int(max(1, min(max_h, 9000 // f)))
        for h in range(1, nh + 1):
            out += np.sin(2 * np.pi * f * h * t + (v + 1) * 1.31 * h + phase_seed) / h
    return out / voices


# ----------------------------------------------------------------- drums
class Drums:
    def __init__(self, rng):
        self.rng = rng

    def kick(self):
        t = tvec(0.42)
        f = 44 + 125 * np.exp(-t * 32)
        body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.0)
        click = band(self.rng.standard_normal(len(t)), 1500, 6000) * np.exp(-t * 700) * 0.6
        return np.tanh(2.4 * (body + click)) / np.tanh(2.4)

    def clap(self):
        t = tvec(0.32)
        n = len(t)
        noise = norm(band(self.rng.standard_normal(n), 900, 3800))
        env = np.zeros(n)
        for k, off in enumerate((0.0, 0.010, 0.021)):
            i = int(off * SR)
            env[i:] += np.exp(-(t[i:] - off) * 190) * (0.75 if k < 2 else 1.0)
        i = int(0.021 * SR)
        env[i:] += np.exp(-(t[i:] - 0.021) * 15) * 0.38
        body = np.sin(2 * np.pi * 185 * t) * np.exp(-t * 32) * 0.35
        return norm(noise * env + body)

    def hat(self, open_=False):
        t = tvec(0.28 if open_ else 0.055)
        x = norm(hp(self.rng.standard_normal(len(t)), 7200, order=4))
        return x * np.exp(-t * (13 if open_ else 75))

    def crash(self):
        t = tvec(2.2)
        x = norm(hp(self.rng.standard_normal(len(t)), 4200, order=2))
        return x * np.exp(-t * 2.3) * (1 - np.exp(-t * 400))


def _in_windows(tt, windows):
    return any(a - 1e-6 <= tt < b - 1e-6 for a, b in windows)


def music(duration, bpm=110, style="pulse", progression="minor_pop", key=0, seed=1,
          breaks=(), hits=()):
    """Stereo music bed (n, 2) float. `breaks`: [(t0, t1)] windows with drums+bass+arp
    muted (tension under a countdown); `hits`: times for a crash accent."""
    st = STYLES[style]
    prog = PROGRESSIONS[progression]
    rng = np.random.default_rng(seed)
    dr = Drums(rng)
    beat = 60.0 / bpm
    bar = beat * 4
    n = int(round(duration * SR))
    t = np.arange(n) / SR
    L = np.zeros(n)
    R = np.zeros(n)
    nbeats = int(duration / beat) + 1
    brk = np.zeros(n, dtype=bool)
    for a, b in breaks:
        brk[int(max(0, a) * SR):int(min(duration, b) * SR)] = True

    # kick + sidechain envelope
    k = dr.kick()
    kick_times = []
    for b in range(nbeats):
        tb = b * beat
        if st["kick"] == "half" and b % 2 == 1:
            continue
        if _in_windows(tb, breaks):
            continue
        kick_times.append(tb)
        place(L, k, tb, 0.95)
        place(R, k, tb, 0.95)
    side = np.ones(n)
    for kt in kick_times:
        i = int(kt * SR)
        seg = t[i:] - kt
        side[i:] = np.minimum(side[i:], 1 - 0.7 * np.exp(-seg / 0.085))

    if st["clap"]:
        c = dr.clap()
        for b in range(nbeats):
            tb = b * beat
            if b % 4 in (1, 3) and not _in_windows(tb, breaks):
                place(L, c, tb, 0.5)
                place(R, c, tb, 0.5)

    # hats (8ths or quarters), optional swing on the off-8ths
    hc, ho = dr.hat(False), dr.hat(True)
    step = beat / 2 if st["hats"] == 8 else beat
    for e in range(int(duration / step) + 1):
        te = e * step
        off = (e % 2 == 1) and st["hats"] == 8
        if off:
            te += st["swing"] * step
        if _in_windows(te, breaks):
            continue
        g = 0.19 if off else 0.10
        place(L, hc, te, g * 0.8)
        place(R, hc, te, g)
        if off and e % 8 == 7:
            place(L, ho, te, 0.08)
            place(R, ho, te, 0.11)

    cr = dr.crash()
    for at in [0.0, *hits]:
        if 0 <= at < duration:
            place(L, cr, at, 0.24)
            place(R, cr, at, 0.24)

    # harmony
    shift = int(key)
    bass = np.zeros(n)
    padL = np.zeros(n)
    padR = np.zeros(n)
    arp = np.zeros(n)
    keys = np.zeros(n)
    nbars = int(np.ceil(duration / bar))
    rot = int(rng.integers(0, 4))  # seeded arp pattern rotation
    for bi in range(nbars):
        root, chord = prog[bi % len(prog)]
        t0 = bi * bar
        i0 = int(t0 * SR)
        i1 = min(n, int((t0 + bar) * SR))
        if i0 >= n:
            break
        tt = t[i0:i1] - t0
        att = 1 - np.exp(-tt / 0.2)
        rel = np.clip((bar - tt) / 0.12, 0, 1)
        for j, m in enumerate(chord):
            f = mhz(m, shift)
            padL[i0:i1] += saw(f, tt, voices=3, detune_cents=11, max_h=20, phase_seed=j) * att * rel
            padR[i0:i1] += saw(f * 1.0015, tt, voices=3, detune_cents=13, max_h=20, phase_seed=j + 3) * att * rel
        fr = mhz(root, shift)
        pulses = 8 if style != "chill" else 4
        for e in range(pulses):
            te = e * bar / pulses
            msk = (tt >= te) & (tt < te + bar / pulses)
            local = tt[msk] - te
            decay = 6.5 if pulses == 8 else 3.0
            env = np.exp(-local * decay) * (1 - np.exp(-local * 300))
            sub = np.sin(2 * np.pi * fr * local)
            up = saw(fr * 2, local, voices=1, max_h=10)
            bass[i0:i1][msk] += (0.85 * sub + 0.35 * up) * env
        if st["arp"] and t0 >= bar:
            tones = [mhz(m, shift) * 2 for m in chord] + [mhz(chord[1], shift) * 4]
            for s in range(16):
                ts = s * beat / 4
                msk = (tt >= ts) & (tt < ts + beat / 4)
                local = tt[msk] - ts
                f = tones[(s * 3 + bi + rot) % len(tones)]
                env = np.exp(-local * 22) * (1 - np.exp(-local * 900))
                arp[i0:i1][msk] += (np.sin(2 * np.pi * f * local) + 0.25 * np.sin(4 * np.pi * f * local)) * env
        if st["keys"]:
            for at in (0.0, beat * 1.5, beat * 2.5):
                msk = tt >= at
                local = tt[msk] - at
                env = np.exp(-local * 2.6) * (1 - np.exp(-local * 400))
                for m in chord:
                    f = mhz(m, shift) * 2
                    keys[i0:i1][msk] += (np.sin(2 * np.pi * f * local) + 0.18 * np.sin(6 * np.pi * f * local)) * env * 0.22

    padL = lp(padL, 1500)
    padR = lp(padR, 1500)
    bass = lp(bass, 900)
    keys = lp(keys, 3000)
    rhythm = np.where(brk, 0.0, 1.0)
    rhythm = np.convolve(rhythm, np.ones(480) / 480, mode="same")  # 10 ms de-click
    pad_lvl = st["pad"] * np.where(brk, 1.25, 1.0)
    L += side * (st["bass"] * bass * rhythm + pad_lvl * padL + st["arp_level"] * arp * rhythm + keys)
    R += side * (st["bass"] * bass * rhythm + pad_lvl * padR + st["arp_level"] * 0.85 * arp * rhythm + keys)
    mix = np.stack([L, R], axis=1)
    mix = np.tanh(1.3 * mix) / np.tanh(1.3)
    fade = int(0.6 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
    return norm(mix, 0.89)


# ----------------------------------------------------------------- SFX
def sfx_kit(seed=7):
    rng = np.random.default_rng(seed)

    def impact():
        t = tvec(1.6)
        f = 28 + 62 * np.exp(-t * 6)
        boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.4)
        crack = lp(rng.standard_normal(len(t)), 3500) * np.exp(-t * 22) * 0.9
        return norm(np.tanh(2.0 * (boom + crack)), 0.95)

    def whoosh(dur=0.55):
        t = tvec(dur)
        n = len(t)
        noise = rng.standard_normal(n)
        out = np.zeros(n)
        block = 512
        for i in range(0, n, block):
            p = i / n
            center = 450 + 2400 * np.sin(np.pi * min(1.0, p * 1.15)) ** 1.5
            seg = noise[max(0, i - 2048):i + block]
            y = band(seg, center * 0.6, min(center * 1.6, SR / 2 - 100))[-(min(block, n - i)):]
            out[i:i + len(y)] = y
        return norm(out * np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2.2, 0.9)

    def pop():
        t = tvec(0.13)
        f = 420 + 650 * np.exp(-t * 55)
        return norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 42), 0.85)

    def click():
        t = tvec(0.06)
        x = band(rng.standard_normal(len(t)), 1800, 7000) * np.exp(-t * 260)
        x += np.sin(2 * np.pi * 2300 * t) * np.exp(-t * 160) * 0.5
        return norm(x, 0.8)

    def tick(high=True):
        t = tvec(0.09)
        f = 2100 if high else 1500
        x = np.sin(2 * np.pi * f * t) * np.exp(-t * 90) + band(rng.standard_normal(len(t)), 2500, 8000) * np.exp(-t * 400) * 0.4
        return norm(x, 0.8)

    def bell(f0, dur=1.2):
        t = tvec(dur)
        parts = [(1.0, 1.0, 3.2), (2.0, 0.35, 5.0), (2.76, 0.45, 6.5), (5.4, 0.18, 10.0)]
        x = sum(a * np.sin(2 * np.pi * f0 * r * t) * np.exp(-t * d) for r, a, d in parts)
        return x * (1 - np.exp(-t * 600))

    def correct():
        buf = np.zeros(int(1.3 * SR))
        place(buf, bell(mhz(88)), 0.0, 0.7)    # E6
        place(buf, bell(mhz(95)), 0.11, 0.8)   # B6
        return norm(buf, 0.8)

    def wrong():
        t = tvec(0.32)
        x = np.sign(np.sin(2 * np.pi * 150 * t)) * 0.5 + np.sin(2 * np.pi * 75 * t)
        return norm(lp(x, 1200) * np.exp(-t * 7) * (1 - np.exp(-t * 300)), 0.6)

    def riser(dur=1.8):
        t = tvec(dur)
        n = len(t)
        noise = rng.standard_normal(n)
        out = np.zeros(n)
        block = 1024
        for i in range(0, n, block):
            seg = noise[max(0, i - 4096):i + block]
            y = hp(seg, 300 + 7000 * (i / n) ** 2)[-(min(block, n - i)):]
            out[i:i + len(y)] = y
        tone = np.sin(2 * np.pi * np.cumsum(220 * (8 ** (t / dur))) / SR) * 0.35
        x = (norm(out) * 0.8 + tone) * (t / dur) ** 2.2
        x[-int(0.008 * SR):] *= np.linspace(1, 0, int(0.008 * SR))
        return norm(x, 0.85)

    def sparkle(dur=0.9):
        buf = np.zeros(int(dur * SR))
        for k in range(11):
            at = 0.03 + k * 0.065 + rng.uniform(-0.015, 0.015)
            t = tvec(0.18)
            place(buf, np.sin(2 * np.pi * rng.uniform(2600, 5200) * t) * np.exp(-t * 30), at, 0.5 * (1 - k / 14))
        return norm(buf, 0.6)

    def typing(dur=1.2):
        buf = np.zeros(int(dur * SR))
        tt = 0.02
        while tt < dur - 0.06:
            t = tvec(0.05)
            key = band(rng.standard_normal(len(t)), 2000, 6500) * np.exp(-t * 420)
            thock = np.sin(2 * np.pi * (160 + rng.uniform(-20, 20)) * t) * np.exp(-t * 140) * 0.6
            place(buf, norm(key + thock), tt, rng.uniform(0.45, 0.9))
            tt += rng.uniform(0.065, 0.13)
        return norm(buf, 0.75)

    return {
        "impact": impact(), "whoosh": whoosh(), "pop": pop(), "click": click(),
        "tick": tick(True), "tock": tick(False), "correct": correct(), "wrong": wrong(),
        "riser": riser(), "sparkle": sparkle(), "ding": norm(bell(mhz(84)), 0.8), "typing": typing(),
    }
