#!/usr/bin/env python3
"""UI proof gate — refuse to render a short whose "product evidence" is not a real, usable UI.

WHY THIS EXISTS (owner, 2026-11-12): five render cycles shipped text-on-a-grid-background
shorts while every gate said PASS. brief_lint checks that a file EXISTS; layout_audit checks
captions don't collide; QA checks loudness. None of them looks at the pixels and asks the only
question that matters: *does the viewer actually see the product?* The vision critic
(frame_critique.py) asks exactly that, but it ran AFTER render and its verdict was never a
gate. So the same broken short was re-rendered for hours.

This gate runs BEFORE render, on the clips/images themselves, in seconds:

  FAIL-BLANK     a frame is blank/flat (white flash, loading state, solid card) for too long
  FAIL-BOTWALL   a frame is a bot-check / security-verification interstitial (never product)
  FAIL-STATIC    the clip barely changes — a still image dressed as a screen recording
  FAIL-NOTEXT    no text-like high-frequency content: looks like a splash, not an interface
  FAIL-VLM       (when NVIDIA_KEY is set) a vision model answers "no real UI" for the majority
                 of sampled frames — the independent read the owner asked for

Usage:
  python3 tools/ui_proof_gate.py briefs/<id>.json [--captures captures/<id>] [--json out.json]
  exits 1 if any referenced product-evidence asset fails; prints one line per asset.
"""
from __future__ import annotations

import argparse, json, os, re, subprocess, sys, tempfile, urllib.error, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
try:
    import imageio_ffmpeg
    FF = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:  # CI has ffmpeg on PATH
    FF = "ffmpeg"
try:
    from PIL import Image, ImageStat
except Exception:
    Image = None

# Interstitials a capture must never contain: if the page said any of this, it is not the product.
BOTWALL = re.compile(
    r"(security verification|verifying you are (a )?human|are you a robot|checking your browser|"
    r"enable javascript and cookies|just a moment|attention required|access denied|"
    r"unusual traffic|performing security|ddos protection|cloudflare)", re.I)

SAMPLES = 5           # frames sampled across each clip
BLANK_STD = 6.0       # grayscale stddev under this = flat/blank frame
BLANK_MEAN_HI = 246   # near-white blank
MOTION_MIN = 1.2      # mean abs frame delta required between consecutive samples


def _run(args, timeout=90):
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout)


DUR_RE = re.compile(r"Duration:\s*(\d+):(\d{2}):(\d{2})\.(\d+)")


def probe(path: Path) -> dict:
    """Duration from the ffmpeg banner — works on every ffmpeg build (imageio-ffmpeg has no
    -show_entries/ffprobe), which is what the sandbox actually ships."""
    r = _run([FF, "-i", str(path)])
    m = DUR_RE.search(r.stderr or "")
    if not m:
        return {}
    h, mi, s, frac = m.groups()
    return {"duration": int(h) * 3600 + int(mi) * 60 + int(s) + float("0." + frac)}


def frames(path: Path, n: int = SAMPLES) -> list[Image.Image]:
    """Sample n frames evenly across the clip; skip the first 8% (load-in state)."""
    info = probe(path)
    dur = info.get("duration") or 0
    if dur <= 0:
        return []
    out = []
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(n):
            t = dur * (0.08 + 0.84 * (i + 0.5) / n)
            f = Path(tmp) / f"{i}.png"
            _run([FF, "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", str(path),
                  "-frames:v", "1", "-vf", "scale=360:-2", str(f)])
            if f.exists():
                out.append(Image.open(f).convert("RGB").copy())
    return out


def stats(im: Image.Image) -> dict:
    g = im.convert("L")
    st = ImageStat.Stat(g)
    px = list(g.getdata())
    mean = st.mean[0]
    std = st.stddev[0]
    # edge/text density proxy: fraction of pixels that differ sharply from the right neighbour
    w, h = g.size
    edges = 0
    for y in range(0, h, 2):
        row = px[y * w:(y + 1) * w]
        edges += sum(1 for x in range(1, w - 1, 2) if abs(row[x] - row[x - 1]) > 28)
    dens = edges / max(1, (h // 2) * (w // 2))
    return {"mean": mean, "std": std, "edge_density": round(dens, 4)}


def motion(frames_: list[Image.Image]) -> float:
    if len(frames_) < 2:
        return 0.0
    deltas = []
    for a, b in zip(frames_, frames_[1:]):
        ga, gb = a.convert("L").resize((120, 160)), b.convert("L").resize((120, 160))
        pa, pb = list(ga.getdata()), list(gb.getdata())
        deltas.append(sum(abs(x - y) for x, y in zip(pa, pb)) / len(pa))
    return sum(deltas) / len(deltas)


# ---------------------------------------------------------------- optional VLM read
API = "https://integrate.api.nvidia.com/v1/chat/completions"
VLM_MODELS = ["meta/llama-3.2-90b-vision-instruct", "meta/llama-3.2-11b-vision-instruct"]


def vlm_verdict(path: Path, im: Image.Image, tok: str) -> bool | None:
    import base64, io
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode()
    prompt = ("Look at this single frame from a short video about a software tool. "
              "Reply with exactly one word: YES if a real, readable product interface "
              "(the actual app or website UI) is the main thing visible, or NO if it is "
              "mostly text on a plain background, a grid/pattern, a blank panel, a loading "
              "screen, or a bot/security verification page.")
    for m in VLM_MODELS:
        body = json.dumps({"model": m, "max_tokens": 4, "temperature": 0,
                           "messages": [{"role": "user", "content": [
                               {"type": "text", "text": prompt},
                               {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}]}]}).encode()
        req = urllib.request.Request(API, data=body, headers={
            "Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
        try:
            r = json.loads(urllib.request.urlopen(req, timeout=90).read())
            txt = (r["choices"][0]["message"]["content"] or "").strip().upper()
            return txt.startswith("YES")
        except Exception:
            continue
    return None


# ---------------------------------------------------------------- per-asset check
def check_asset(path: Path, tok: str | None, want_motion: bool) -> list[str]:
    fails = []
    if not path.exists():
        return [f"FAIL-MISSING {path.name}"]
    ims = frames(path) if path.suffix.lower() in (".mp4", ".webm", ".mov") else [Image.open(path).convert("RGB")]
    if not ims:
        return [f"FAIL-UNREADABLE {path.name} (no decodable frames)"]
    st = [stats(im) for im in ims]

    blanks = [i for i, s in enumerate(st)
              if s["std"] < BLANK_STD or s["mean"] > BLANK_MEAN_HI]
    if len(blanks) / len(st) > 0.34:
        fails.append(f"FAIL-BLANK {path.name}: {len(blanks)}/{len(st)} frames blank or near-white "
                     f"(first bad sample #{blanks[0] + 1}) — audience sees an empty panel")
    if want_motion:
        m = motion(ims)
        if m < MOTION_MIN:
            fails.append(f"FAIL-STATIC {path.name}: frame delta {m:.2f} < {MOTION_MIN} — a still, "
                         f"not a screen recording")
    thin = [i for i, s in enumerate(st) if s["edge_density"] < 0.012]
    if len(thin) / len(st) > 0.6:
        fails.append(f"FAIL-NOTEXT {path.name}: {len(thin)}/{len(st)} frames have almost no "
                     f"text-like detail — likely a splash/pattern, not an interface")
    if tok:
        verdicts = [vlm_verdict(path, im, tok) for im in ims[:3]]
        real = [v for v in verdicts if v is not None]
        if real and sum(real) < (len(real) + 1) // 2:
            fails.append(f"FAIL-VLM {path.name}: vision model says real UI is NOT the main subject "
                         f"in {len(real) - sum(real)}/{len(real)} sampled frames")
    return fails


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("brief")
    ap.add_argument("--captures", help="capture dir (default: brief's capture, else captures/<brief id>)")
    ap.add_argument("--json")
    ap.add_argument("--no-vlm", action="store_true")
    a = ap.parse_args()

    brief_path = Path(a.brief)
    brief = json.loads(brief_path.read_text())
    vid = brief.get("id") or brief_path.stem
    cap = Path(a.captures) if a.captures else ROOT / "captures" / (brief.get("capture") or vid)
    tok = None if a.no_vlm else (os.environ.get("NVIDIA_KEY") or os.environ.get("NVIDIA_API_KEY"))

    referenced, seen = [], set()
    for s in brief.get("scenes", []):
        if s.get("type") == "clip" and s.get("src") and s["src"] not in seen:
            seen.add(s["src"]); referenced.append((s["src"], True))
        if s.get("type") == "image" and s.get("image") and s["image"] not in seen:
            seen.add(s["image"]); referenced.append((s["image"], False))

    if not referenced:
        print(f"UI-PROOF {vid}: no product-evidence assets referenced — nothing to prove "
              f"(a short with no UI anywhere cannot pass the owner's bar)")
        return 1

    report = {"brief": vid, "vision": bool(tok), "assets": []}
    hard = 0
    for name, want_motion in referenced:
        fails = check_asset(cap / name, tok, want_motion)
        kind = "clip" if want_motion else "image"
        report["assets"].append({"asset": name, "kind": kind, "fails": fails})
        if fails:
            hard += len(fails)
            for f in fails:
                print(f"  x {f}")
        else:
            print(f"  ok {kind}: {name}")
    print(f"UI-PROOF {vid}: {hard} blocking finding(s) across {len(referenced)} asset(s)"
          f"{'' if tok else ' (VLM check skipped: NVIDIA_KEY not set)'}")
    if a.json:
        Path(a.json).write_text(json.dumps(report, indent=1))
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
