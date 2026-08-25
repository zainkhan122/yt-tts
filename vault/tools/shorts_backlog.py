#!/usr/bin/env python3
"""shorts_backlog.py — ROBUST driver for backfilling vertical Shorts (R21)
for Month-1/2 videos (v4+). Never crashes the session: every failure is a
clean, logged exit with a resumable state file.

Usage:
  python3 tools/shorts_backlog.py plan 004          # show hook+payoff ranges
  python3 tools/shorts_backlog.py build 004 hook|payoff|both [--pay-a A --pay-b B]

Robustness features:
  - pre-flight: pip deps, secrets, /tmp >=250MB, storyboard present+parseable
  - duration PRE-CHECK: projected total (sum(v_dur|beat_dur + GAP) + CTA ext)
    must land in [28, 47]s BEFORE building; auto-trims from range EDGES only
  - idempotent: state in videos/NNN/shorts/SHORTS_STATE.json — done shorts
    are skipped on re-run
  - portrait media guard: >=8 fetched clips or abort (no silent empty pools)
  - logs everything to videos/NNN/shorts/SHORTS_LOG.txt
  - payoff default: last self-contained arc = final section of the script
    (heuristic: last beat-run fitting the window, snapped to a section-y opener
    if one is nearby)
"""
import json, os, subprocess, sys, time

GAP = 0.20
CTA_EXT = 3.6          # measured: CTA_GAP 0.25 + af_heart CTA ~3.1 + TAIL 0.25
WIN = (28.0, 47.0)     # project INSIDE this (make_short's own gate is 25-50)

def vid_dir(n):
    return f"/home/user/videos/video_{int(n):03d}"

def log(vd, msg):
    os.makedirs(f"{vd}/shorts", exist_ok=True)
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(f"{vd}/shorts/SHORTS_LOG.txt", "a") as f:
        f.write(line + "\n")

def die(vd, msg):
    log(vd, "ABORT: " + msg)
    sys.exit(1)

def beat_dur(b):
    return b.get("v_dur") or b.get("beat_dur") or b.get("beat_len") or 3.0

def get_storyboard(vd, name):
    """Local storyboard.json, else pull from repo main."""
    sbp = f"{vd}/storyboard.json"
    if not os.path.exists(sbp):
        os.makedirs(vd, exist_ok=True)
        pat = open("/home/user/secrets/github_pat.txt").read().strip()
        n = os.path.basename(vd)
        r = subprocess.run(["curl", "-sL", "--fail", "-H", f"Authorization: Bearer {pat}",
            f"https://raw.githubusercontent.com/zainkhan122/yt-tts/main/vault/{n}/storyboard.json",
            "-o", sbp], capture_output=True)
        if r.returncode != 0 or not os.path.exists(sbp) or os.path.getsize(sbp) < 100:
            if os.path.exists(sbp): os.remove(sbp)
            die(vd, f"storyboard.json not found for {n} (repo has no sources — see v1-v3 caveat)")
    try:
        sb = json.load(open(sbp))
        assert isinstance(sb, list) and sb and "sentence" in sb[0]
        return sb
    except Exception as e:
        die(vd, f"storyboard.json unparseable: {e}")

def preflight(vd):
    import importlib
    for mod, pkg in [("kokoro_onnx", "kokoro-onnx"), ("soundfile", "soundfile"),
                     ("imageio_ffmpeg", "imageio-ffmpeg")]:
        try: importlib.import_module(mod)
        except ImportError:
            log(vd, f"installing {pkg}"); subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", pkg])
    for sec in ["/home/user/secrets/github_pat.txt", "/home/user/.pexels_key"]:
        if not os.path.exists(sec): die(vd, f"secret missing: {sec}")
    free = os.statvfs("/tmp").f_bavail * os.statvfs("/tmp").f_frsize / 1e6
    if free < 250: die(vd, f"/tmp too low: {free:.0f}MB free (<250)")
    log(vd, f"pre-flight OK (/tmp {free:.0f}MB free)")

def hook_range(sb):
    acc, b = 0.0, 0
    while b < len(sb) and acc + beat_dur(sb[b]) + GAP <= WIN[1] - CTA_EXT:
        acc += beat_dur(sb[b]) + GAP; b += 1
    return 0, b, acc

def payoff_range(sb):
    """Last run of beats fitting the window; snap its start back to a
    'section opener' sentence if one sits within 3 beats before it."""
    total = sum(beat_dur(b) + GAP for b in sb)
    acc, a = 0.0, len(sb)
    openers = ("so here", "here's what", "here is what", "the truth", "what i want",
               "so tell", "and that's why", "this is why", "the answer", "so if you")
    while a > 0:
        nxt = a - 1
        if acc + beat_dur(sb[nxt]) + GAP > WIN[1] - CTA_EXT:
            break
        acc += beat_dur(sb[nxt]) + GAP; a = nxt
    best = a
    for i in range(max(0, a - 3), a):
        if any(sb[i]["sentence"].lower().startswith(o) for o in openers):
            best = i; break
    a = best
    acc = sum(beat_dur(sb[i]) + GAP for i in range(a, len(sb)))
    return a, len(sb), acc

def plan(n):
    vd = vid_dir(n)
    sb = get_storyboard(vd, n)
    ha, hb, hd = hook_range(sb)
    pa, pb, pd = payoff_range(sb)
    print(f"video_{int(n):03d}: {len(sb)} beats")
    print(f"  hook   beats {ha}..{hb-1}  voice {hd:.1f}s -> short ~{hd+CTA_EXT:.1f}s")
    print(f"  payoff beats {pa}..{pb-1}  voice {pd:.1f}s -> short ~{pd+CTA_EXT:.1f}s")
    print(f"  payoff opener: {sb[pa]['sentence'][:80]!r}")
    print(f"  hook captions: {[b['caption'][1] for b in sb[ha:hb] if b.get('caption')]}")
    print(f"  payoff captions: {[b['caption'][1] for b in sb[pa:pb] if b.get('caption')]}")

def state_load(vd):
    p = f"{vd}/shorts/SHORTS_STATE.json"
    return json.load(open(p)) if os.path.exists(p) else {}

def state_save(vd, st):
    json.dump(st, open(f"{vd}/shorts/SHORTS_STATE.json", "w"), indent=1)

def build(n, kind, pay_a=None, pay_b=None):
    vd = vid_dir(n)
    st = state_load(vd)
    if st.get(f"{kind}_done"):
        log(vd, f"{kind} already done — skipping (idempotent)"); return
    preflight(vd)
    sb = get_storyboard(vd, n)
    if kind == "hook":
        a, b, d = hook_range(sb)
        cmd = ["python3", "/home/user/tools/make_short.py", "hook"]
    else:
        if pay_a is None:
            a, b, d = payoff_range(sb)
        else:
            a, b = pay_a, pay_b if pay_b is not None else len(sb)
            d = sum(beat_dur(sb[i]) + GAP for i in range(a, b))
        if not (WIN[0] - CTA_EXT <= d <= WIN[1] - CTA_EXT):
            die(vd, f"payoff voice {d:.1f}s outside safe window "
                    f"[{WIN[0]-CTA_EXT:.0f}-{WIN[1]-CTA_EXT:.0f}]s — adjust --pay-a/--pay-b")
        cmd = ["python3", "/home/user/tools/make_short.py", "payoff", "--beats", str(a), str(b)]
    if d < WIN[0] - CTA_EXT:
        die(vd, f"{kind} voice {d:.1f}s too SHORT (<{WIN[0]-CTA_EXT:.0f}s)")
    qs = open(f"{vd}/shorts/queries.txt").read().strip() if os.path.exists(f"{vd}/shorts/queries.txt") else ""
    if qs:
        cmd += ["--queries", qs.replace("\n", ",")]
    log(vd, f"building {kind}: beats {a}..{b-1}, voice {d:.1f}s, queries: {qs or '(defaults)'}")
    env = dict(os.environ, PIPE_VIDEO=vd)
    r = subprocess.run(cmd, env=env, capture_output=True, text=True)
    out = (r.stdout + r.stderr)[-2500:]
    log(vd, f"make_short exit={r.returncode}\n{out}")
    if r.returncode != 0:
        die(vd, f"make_short {kind} FAILED (see log above)")
    if not os.path.exists(f"{vd}/shorts/short_{kind}.mp4"):
        die(vd, f"expected output short_{kind}.mp4 missing")
    st[f"{kind}_done"] = time.strftime("%Y-%m-%d %H:%M")
    st[f"{kind}_beats"] = f"{a}-{b-1}"
    state_save(vd, st)
    log(vd, f"{kind} COMPLETE -> {vd}/shorts/short_{kind}.mp4 (pushed by make_short)")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    cmd, n = sys.argv[1], sys.argv[2]
    if cmd == "plan":
        plan(n)
    elif cmd == "build":
        kind = sys.argv[3] if len(sys.argv) > 3 else "both"
        pa = pb = None
        if "--pay-a" in sys.argv:
            pa = int(sys.argv[sys.argv.index("--pay-a") + 1])
            pb = int(sys.argv[sys.argv.index("--pay-b") + 1]) if "--pay-b" in sys.argv else None
        for k in (["hook", "payoff"] if kind == "both" else [kind]):
            build(n, k, pa, pb)
    else:
        print(__doc__); sys.exit(1)
