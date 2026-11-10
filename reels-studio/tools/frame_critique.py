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
MODELS = [  # NIM free-tier vision models, most capable first; 404/permission → next
    "meta/llama-3.2-90b-vision-instruct",
    "meta/llama-3.2-11b-vision-instruct",
    "microsoft/phi-4-multimodal-instruct",
    "nvidia/vila",
]
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


def call(model, messages, tok, max_tokens=900, tries=4):
    body = json.dumps({"model": model, "messages": messages, "max_tokens": max_tokens,
                       "temperature": 0.2, "top_p": 0.9, "stream": False}).encode()
    for i in range(tries):
        req = urllib.request.Request(API, data=body, headers={
            "Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read())["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            if e.code in (404, 403):
                raise  # model gone from free tier — caller falls back to next model
            if e.code in (408, 409, 425, 429, 500, 502, 503, 504) and i < tries - 1:
                time.sleep(4 * (i + 1))
                continue
            raise
    raise RuntimeError("retries exhausted")


def call_vision(images, prompt, tok, max_tokens=900):
    """First model in the cascade that accepts the payload wins; name returned with the text."""
    content = [{"type": "text", "text": prompt}]
    content += [{"type": "image_url", "image_url": {"url": b64img(p)}} for p in images]
    last = None
    for m in MODELS:
        try:
            out = call(m, [{"role": "user", "content": content}], tok, max_tokens)
            return m, out
        except urllib.error.HTTPError as e:
            last = e
            print(f"cascade: {m} -> HTTP {e.code}, trying next", file=sys.stderr)
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("brief_id")
    ap.add_argument("--frames", required=True, help="dir of sampled frames of OUR render")
    ap.add_argument("--media", default="", help="dir of the tool's real UI images (captures)")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    tok = key()
    frames = sorted(Path(a.frames).glob("*.jp*g")) or sorted(Path(a.frames).glob("*.png"))
    media = sorted(Path(a.media).glob("*.jp*g") ) if a.media else []
    frames, media = frames[:8], media[:3]
    if len(frames) < 3:
        raise SystemExit("need at least 3 sampled frames")
    hook, title, spoken = brief_context(a.brief_id)
    teardown = teardown_excerpt(a.brief_id)

    print(f"frames={len(frames)} media={len(media)} model cascade: {' > '.join(MODELS)}", flush=True)
    m1, per_frame = call_vision(
        frames[:4],
        "These are frames sampled from the first half of a 50-second TikTok/YouTube-Shorts video "
        "advertising an open-source tool. Be blunt and specific. For the set: (1) Is the tool's actual "
        "product UI visible anywhere? (2) What is literally on screen — describe shapes, text, motion "
        "cues. (3) What is visually dominant — interface, or typography on a background? (4) one line "
        "verdict on whether a viewer learns what the tool LOOKS like.",
        tok, max_tokens=700)
    print(f"[model {m1}] first-half critique done", flush=True)
    m2, per_frame2 = call_vision(
        frames[4:],
        "These are frames from the SECOND half of the same Short. (1) Is any real product interface "
        "shown? (2) describe what changes visually frame to frame (any animation?). (3) verdict on "
        "visual variety and on-screen evidence for the claims being made.",
        tok, max_tokens=700)
    print(f"[model {m2}] second-half critique done", flush=True)

    media_note = ""
    if media:
        m3, media_note = call_vision(
            media,
            "These are official interface screenshots of the open-source tool the Short is about "
            "(Musike). Describe the layout vocabulary we could RECREATE as original animation "
            "(never paste the screenshot): panels, grids, controls, the player bar, toggles — and the "
            "colour/type personality a rebuild should keep. Be concrete and terse.",
            tok, max_tokens=700)
        print(f"[model {m3}] tool-UI vocabulary done", flush=True)

    synthesis_prompt = f"""You are the art director for short-form tool videos.

CONTEXT
- Tool: Musike (open-source personal music player; server you run fetches streams; switches audio to video mid-song; runs on 8 platforms; library in an exportable file).
- Video title: {title}
- Hook question shown 0-3s: {hook}
- Spoken lines in order: {" / ".join(spoken)}
- Critic on our current render, first half: {per_frame}
- Critic on second half: {per_frame2}
- Tool UI vocabulary from its official screenshots: {media_note}
{f"- Reference teardown (a 3.5x outlier we take LEAD from, never copy): {teardown}" if teardown else ""}

TASK: write the REBUILD SPEC as markdown with these exact sections:
## VERDICT — 3 lines, what the current render does wrong, hardest truth first.
## SCENE SPEC — one bullet per scene (hook, 4 points, honesty beat, endcard). Per bullet: what DOMINATES the frame (must be the player's interface or a physical domain metaphor, not bare text), the animation (what MOVES, in 2-3 words), the one on-screen phrase, and why it matches the spoken line.
## COLOUR & TYPE — exact palette (hexes) drawn from the tool's own dark player personality + our accent; type scale rules.
## MOTION RULES — 4 rules so nothing is a static text card again (e.g. every scene has a state change visible within 1.5s).
Keep it under 500 words, imperative, no filler."""
    m4, spec = call_vision([], synthesis_prompt, tok, max_tokens=1100)
    print(f"[model {m4}] synthesis done", flush=True)

    today = dt.date.today().isoformat()
    doc = (f"# Frame critique: {a.brief_id} — {today}\n\n"
           f"Models: {m1} / {m2} / {m3 if media else '-'} / {m4}\n\n"
           f"## Critic: first half\n{per_frame}\n\n## Critic: second half\n{per_frame2}\n\n"
           f"## Tool UI vocabulary\n{media_note or '(no media supplied)'}\n\n{spec}\n")
    out = Path(a.out) if a.out else ROOT / "research" / "critiques" / f"{a.brief_id}-{today}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")
    print(f"critique -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
