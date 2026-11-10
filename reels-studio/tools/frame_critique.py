#!/usr/bin/env python3
"""Frame critique — independent VLM review of a rendered short, via NVIDIA NIM free endpoints.

Owner rule (2026-11-10): after a render, cloud runs this so a vision model answers the questions
we keep missing ourselves — is the TOOL'S UI on screen, do the animations depict the domain, do
colours/type serve the claim — and then writes a scene-level rebuild spec for the specific tool.

  python3 tools/frame_critique.py <brief_id> --frames <dir> [--media <dir>] [--out <path>]

Inputs: sampled frames of OUR render (jpg/png), the tool's real UI media (captures), the brief's
hook/points copy, and the reference teardown when it exists. Output: markdown critique +
REBUILD SPEC (per-scene: what to animate, colours, typography, graphics).
Runs in the frame-critique workflow — NVIDIA_KEY is a GitHub Actions secret, never stored locally.
Stdlib only. Model cascade covers NIM free-tier churn; 408/429/5xx retried with backoff.
"""
import argparse
import base64
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://integrate.api.nvidia.com/v1/chat/completions"
PREFERRED = [  # known-good NIM vision models first; then whatever the live catalog offers
    "meta/llama-3.2-90b-vision-instruct",
    "meta/llama-3.2-11b-vision-instruct",
    "microsoft/phi-4-multimodal-instruct",
]
VISION_HINT = re.compile(r"vision|multimodal|[-_/]vl[-_/b]|vila|neva|cosmos|internvl|gemma", re.I)


def models(tok):
    try:
        req = urllib.request.Request("https://integrate.api.nvidia.com/v1/models",
                                     headers={"Authorization": f"Bearer {tok}"})
        have = {m["id"] for m in json.loads(urllib.request.urlopen(req, timeout=30).read())["data"]}
    except Exception:
        return PREFERRED
    live = [m for m in PREFERRED if m in have]
    extra = sorted(m for m in have if VISION_HINT.search(m) and m not in live)
    return live + extra[:8]
KEY_ENV = ("NVIDIA_KEY", "NVIDIA_API_KEY")


def key():
    for k in KEY_ENV:
        if os.environ.get(k):
            return os.environ[k].strip()
    raise SystemExit("frame_critique: NVIDIA_KEY/NVIDIA_API_KEY is not set (it lives in GH Actions secrets)")


def b64img(path):
    mime = "image/png" if str(path).lower().endswith(".png") else "image/jpeg"
    data = Path(path).read_bytes()
    if len(data) > 900_000:  # NIM rejects oversized images; frames are sampled small upstream
        raise SystemExit(f"frame too large: {path} ({len(data)//1024} KB) — sample smaller")
    return f"data:{mime};base64," + base64.b64encode(data).decode()


class CascadeSkip(Exception):
    """Model is unusable right now (gone from free tier, timed out, throttled) — try the next."""


def call(model, messages, tok, max_tokens=900, tries=3, timeout=150):
    body = json.dumps({"model": model, "messages": messages, "max_tokens": max_tokens,
                       "temperature": 0.2, "top_p": 0.9, "stream": False}).encode()
    for i in range(tries):
        req = urllib.request.Request(API, data=body, headers={
            "Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            if e.code in (400, 403, 404, 410, 422):
                raise CascadeSkip(f"{model}: HTTP {e.code}")
            if i < tries - 1:
                time.sleep(4 * (i + 1))
                continue
            raise CascadeSkip(f"{model}: HTTP {e.code} after retries")
        except (TimeoutError, urllib.error.URLError, OSError) as e:
            print(f"call: {model} network/timeout ({type(e).__name__}), retry {i+1}/{tries}", file=sys.stderr)
            if i < tries - 1:
                time.sleep(5 * (i + 1))
                continue
            raise CascadeSkip(f"{model}: {type(e).__name__} after retries")
    raise CascadeSkip(f"{model}: retries exhausted")


def call_vision(image, prompt, tok, max_tokens=900, model_list=None):
    """ONE image per request (the NIM free tier rejects multi-image payloads). First model that
    accepts wins; 404/410/403/400-with-text-only fall through to the next model."""
    content = ([{"type": "text", "text": prompt}] +
               ([{"type": "image_url", "image_url": {"url": b64img(image)}}] if image else []))
    last = None
    for m in (model_list or PREFERRED):
        try:
            return m, call(m, [{"role": "user", "content": content}], tok, max_tokens)
        except CascadeSkip as e:
            last = e
            print(f"cascade: {e}, trying next", file=sys.stderr)
    raise SystemExit(f"frame_critique: no vision model accepted the request ({last})")


def brief_context(brief_id):
    b = json.loads((ROOT / "briefs" / f"{brief_id}.json").read_text())
    hook = " ".join(str(b.get(k) or "") for k in ("hook", "heading"))
    lines = [s.get("say", "") for s in b.get("scenes", []) if s.get("say")]
    title = ((b.get("seo") or {}).get("youtube") or {}).get("title", "")
    return hook, title, lines


def teardown_excerpt(brief_id):
    b = json.loads((ROOT / "briefs" / f"{brief_id}.json").read_text())
    insp = b.get("inspiration") or {}
    if not insp:
        return ""
    td = (ROOT / "research" / "references"
          / f"{insp.get('platform')}-{insp.get('source')}-{insp.get('post_id')}" / "teardown.md")
    if not td.exists():
        return ""
    text = td.read_text(encoding="utf-8")
    keep = []
    for head in ("## What we take", "## What we avoid", "## Hook anatomy"):
        m = re.search(re.escape(head) + r"\n(.*?)(?=\n## |\Z)", text, re.S)
        if m:
            keep.append(head + "\n" + m.group(1).strip()[:1200])
    return "\n\n".join(keep)[:2600]


FRAME_PROMPT = ("Forensic motion-design read of ONE frame from a vertical short. Report tersely: "
                "layout grid & safe areas; text system (sizes, casing, letterspacing, weight); colour grade "
                "(dominant + accent approx hexes); surface treatment (grain/halftone/glow/blur); evidence of "
                "motion (trails, ghosting, mid-animation state, mid-crop); compositing depth (layers, shadows, "
                "parallax); and the single most premium-looking detail in the frame.")
STYLE_PROMPT = ("From these per-frame notes on ONE video plus its caption, reconstruct the motion stack: "
                "cut rhythm; transition types; easing feel (linear/spring/bounce); kinetic-type behaviour; "
                "particles/3D/camera moves; the signature move of this video. Name techniques precisely "
                "(motion-design vocabulary, not marketing words).")
INVENTORY = """OUR RENDER STACK (what exists today):
- HTML/CSS/JS scene templates composited in headless Chromium via Playwright (full keyframe/spring/3D-transform
  CSS + JS animation engine, canvas 2D), rendered per-scene by ffmpeg; three.min.js already vendored for real
  WebGL-style 3D in graphics/templates/photo-to-3d/vendor/.
- PIL drawn kit cards; ffmpeg compositing incl. filter graphs (minterpolate, xfade, zoompan); burned captions.
- TTS voice + word-timed subtitles.
- NOT in the stack: After Effects, Blender, character rigging, tracked/AI-generated footage.
"""


def external_run(a, tok):
    pack = json.loads(Path(a.frames_map).read_text())
    live = models(tok)
    print(f"external mode: {len(pack)} videos; live models: {' > '.join(live[:4])}…", flush=True)
    used, videos = {}, []
    for v in pack:
        notes = []
        for i, fr in enumerate(sorted(v["frames"])):
            m, note = call_vision(fr, FRAME_PROMPT, tok, max_tokens=380, model_list=live)
            used[m] = used.get(m, 0) + 1
            notes.append(f"- frame {i+1}: {note.strip()}")
            print(f"[{m}] {v['name']} frame {i+1}/{len(v['frames'])}", flush=True)
        m, style = call_vision(None, STYLE_PROMPT + "\n\nCAPTION: " + (v.get("caption") or "")[:400]
                               + "\n\nFRAME NOTES:\n" + "\n".join(notes)[:6000],
                               tok, max_tokens=520, model_list=live)
        used[m] = used.get(m, 0) + 1
        v["frames_notes"] = "\n".join(notes)
        v["style"] = style.strip()
        videos.append(v)
        print(f"[{m}] style read: {v['name']}", flush=True)

    master = ("You are a motion-design director auditing our production capability against a reference "
              "creator whose reels are 100% programmatic (Claude Code skill). Below: per-video style reads "
              "and sampled-frame forensics for their 5 most recent reels.\n\n"
              + INVENTORY + "\nREFERENCE VIDEOS:\n"
              + "\n\n".join(f"### {v['name']} — {(v.get('caption') or '')[:200]}\n{v['style']}"
                             + "\nframe forensics:\n" + v["frames_notes"][:2200] for v in videos)
              + """\n\nTASKS, in markdown:
## TECHNIQUE INVENTORY — every distinct animation/graphics technique observed across the 5 videos
(motion-design terms; note which videos used each).
## CAN WE MAKE IT — for every technique above: ALREADY (how, with our stack) / UPGRADE (small new
dependency or engine feature — name it) / NEW TOOL (nothing we have comes close — name the tool class).
## VISUAL-QUALITY BAR — the 5 concrete things that make these reels look premium that our current
renders lack (colour, easing, texture, timing, layering).
## PRIORITY UPGRADES — the 3 highest-leverage additions to our renderer to close the gap, ordered.
Imperative, blunt, no filler.""")
    m, master_md = call_vision(None, master, tok, max_tokens=1400, model_list=live)
    used[m] = used.get(m, 0) + 1
    today = dt.date.today().isoformat()
    doc = [f"# External frame analysis: {a.subject} — {today}", "",
           f"Models: {used}", ""]
    for v in videos:
        doc += [f"## {v['name']}", f"caption: {(v.get('caption') or '')[:300]}", "",
                "### style read", v["style"], "", "### frame forensics", v["frames_notes"], ""]
    doc += ["## Synthesis", master_md, ""]
    out = Path(a.out) if a.out else ROOT / "research" / "critiques" / f"{a.subject}-{today}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(doc), encoding="utf-8")
    print(f"critique -> {out.relative_to(ROOT)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("brief_id")
    ap.add_argument("--frames", default="", help="dir of sampled frames of OUR render")
    ap.add_argument("--media", default="", help="dir of the tool's real UI images (captures)")
    ap.add_argument("--out", default="")
    ap.add_argument("--external", action="store_true", help="analyse third-party reels instead of our render")
    ap.add_argument("--frames-map", default="", help="json: [{name, caption, frames:[paths]}]")
    ap.add_argument("--subject", default="", help="label for output doc, e.g. instagram-adilet.fndr")
    a = ap.parse_args()
    if a.external:
        external_run(a, key())
        return
    tok = key()
    frames = sorted(Path(a.frames).glob("*.jp*g")) or sorted(Path(a.frames).glob("*.png"))
    media = sorted(Path(a.media).glob("*.jp*g") ) if a.media else []
    frames, media = frames[:8], media[:3]
    if len(frames) < 3:
        raise SystemExit("need at least 3 sampled frames")
    hook, title, spoken = brief_context(a.brief_id)
    teardown = teardown_excerpt(a.brief_id)

    live = models(tok)
    print(f"frames={len(frames)} media={len(media)} live models: {' > '.join(live[:5])}{'…' if len(live)>5 else ''}", flush=True)
    notes, used = [], {}
    for i, f in enumerate(frames):
        m, note = call_vision(f, "This is ONE frame from a 50-second vertical Short advertising an "
                              "open-source tool. Answer tersely: (1) is any real product interface "
                              "visible? (2) what is literally on screen (shapes, text, imagery, motion "
                              "blur cues)? (3) does a viewer learn what the tool LOOKS like from this "
                              "frame? one-line verdict.", tok, max_tokens=320, model_list=live)
        used[m] = used.get(m, 0) + 1
        notes.append(f"frame {f.name}: {note.strip()}")
        print(f"[{m}] frame {i+1}/{len(frames)}", flush=True)
    per_frame = "\n".join(notes)

    vocab = []
    for f in media:
        m, note = call_vision(f, "Official interface screenshot of Musike, the tool the Short is about. "
                          "Describe the layout vocabulary we could RECREATE as original animation (never "
                          "paste the screenshot): panels, grids, controls, player bar, toggles, and the "
                          "colour/type personality a rebuild should keep. Concrete, terse.",
                          tok, max_tokens=380, model_list=live)
        vocab.append(f"{f.name}: {note.strip()}")
        print(f"[{m}] media {f.name}", flush=True)
    media_note = "\n".join(vocab)

    synthesis_prompt = f"""You are the art director for short-form tool videos.

CONTEXT
- Tool: Musike (open-source personal music player; server you run fetches streams; switches audio to video mid-song; runs on 8 platforms; library in an exportable file).
- Video title: {title}
- Hook question shown 0-3s: {hook}
- Spoken lines in order: {" / ".join(spoken)}
- Critic on our current render, first half: {per_frame}
- Tool UI vocabulary from its official screenshots: {media_note}
{f"- Reference teardown (a 3.5x outlier we take LEAD from, never copy): {teardown}" if teardown else ""}

TASK: write the REBUILD SPEC as markdown with these exact sections:
## VERDICT — 3 lines, what the current render does wrong, hardest truth first.
## SCENE SPEC — one bullet per scene (hook, 4 points, honesty beat, endcard). Per bullet: what DOMINATES the frame (must be the player's interface or a physical domain metaphor, not bare text), the animation (what MOVES, in 2-3 words), the one on-screen phrase, and why it matches the spoken line.
## COLOUR & TYPE — exact palette (hexes) drawn from the tool's own dark player personality + our accent; type scale rules.
## MOTION RULES — 4 rules so nothing is a static text card again (e.g. every scene has a state change visible within 1.5s).
Keep it under 500 words, imperative, no filler."""
    m4, spec = call_vision(None, synthesis_prompt, tok, max_tokens=1100, model_list=live)
    print(f"[model {m4}] synthesis done", flush=True)

    today = dt.date.today().isoformat()
    doc = (f"# Frame critique: {a.brief_id} — {today}\n\n"
           f"Models used: {used}; synthesis {m4}\n\n"
           f"## Critic: per-frame\n{per_frame}\n\n"
           f"## Tool UI vocabulary\n{media_note or '(no media supplied)'}\n\n{spec}\n")
    out = Path(a.out) if a.out else ROOT / "research" / "critiques" / f"{a.brief_id}-{today}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")
    print(f"critique -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
