#!/usr/bin/env python3
"""Local silent preview of a graphics brief, before the cloud render.

The cloud render is the only place the approved voice exists (Chatterbox), so this script fakes the
timing: it lays every spoken word out at a chosen rate and renders the same scene document the pipeline
would render. Purpose: look at the animation and at the cue-lock before spending a cloud render.

    python3 preview.py repo-unslop-02 --wpm 210 --out /var/tmp/unslop02-preview.mp4
"""
import argparse
import json
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from graphics.stage import plan_scenes  # noqa: E402
from graphics.render import render  # noqa: E402


def fake_timing(brief, wpm, gap=0.26):
    """One phrase per brief scene, words spread at `wpm`, a short gap between scenes."""
    per_word = 60.0 / wpm
    t = 0.12
    timing, order = {}, []
    for sc in brief["scenes"]:
        words = []
        for w in str(sc["say"]).split():
            words.append([w, round(t, 3), round(t + per_word, 3)])
            t += per_word
        timing[sc["id"]] = {"words": words, "text": sc["say"]}
        order.append(sc["id"])
        t += gap
    return timing, order, t


def silent_wav(path, seconds, sr=24000):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(b"\x00\x00" * int(seconds * sr))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vid")
    ap.add_argument("--wpm", type=float, default=210.0)
    ap.add_argument("--out", default=None)
    ap.add_argument("--stills", default=None, help="write three stills as <dir>/still-<t>.jpg")
    a = ap.parse_args()

    gdir = ROOT / "briefs" / "graphics" / a.vid
    brief = json.loads((ROOT / "briefs" / f"{a.vid}.json").read_text(encoding="utf-8"))
    sheet = json.loads((gdir / "features.json").read_text(encoding="utf-8"))
    source = (gdir / "source.md").read_text(encoding="utf-8")
    beats = json.loads((gdir / "beats.json").read_text(encoding="utf-8"))
    timing, order, duration = fake_timing(brief, a.wpm)
    from graphics.stage import flatten_words, segments_from_timing
    words = flatten_words(timing, order)
    phrases = segments_from_timing(timing, order)
    events = {"press": round(duration - 1.6, 3), "endcard_keyword": round(duration - 2.4, 3)}
    doc, phrases = plan_scenes(sheet, source, beats, phrases, duration, words, events=events)
    print("template:", doc.get("template"), "| scenes:", len(doc["scenes"]), "| duration:", round(duration, 2))

    out = Path(a.out or f"/var/tmp/{a.vid}-preview.mp4")
    work = Path("/var/tmp") / f"{a.vid}-preview"
    work.mkdir(parents=True, exist_ok=True)
    wav = work / "silent.wav"
    silent_wav(wav, duration + 0.4)
    info = render(doc, wav, out, work, duration)
    print(json.dumps({k: info[k] for k in info if k in ("frames", "fps", "duration_s", "seconds")}, indent=1))
    print("->", out)

    if a.stills:
        sd = Path(a.stills)
        sd.mkdir(parents=True, exist_ok=True)
        from playwright.sync_api import sync_playwright
        from graphics.render import build_stage_html, W, H
        html = work / "stage.html"
        html.write_text(build_stage_html(doc), encoding="utf-8")
        with sync_playwright() as p:
            br = p.chromium.launch(args=["--no-sandbox", "--font-render-hinting=none"])
            page = br.new_page(viewport={"width": W, "height": H})
            page.goto(html.as_uri())
            page.wait_for_function("window.ready === true", timeout=30000)
            for t in [0.9, 3.4, 7.2, 15.0, 25.5, 33.0, 37.6, 43.0, duration - 1.2]:
                page.evaluate(f"window.setTime({t:.3f})")
                page.screenshot(path=str(sd / f"still-{t:05.1f}.jpg"), type="jpeg", quality=92)
            br.close()
        print("stills ->", sd)


if __name__ == "__main__":
    main()
