"""Render a scene document to MP4: deterministic frame capture (Playwright) piped into ffmpeg.

Frame t is drawn by window.setTime(t). Output is reproducible for the same inputs.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from . import TEMPLATES

FPS = 30
W, H = 1080, 1920


def template_dir(name: str | None = None) -> Path:
    """A brief may name its own per-tool template directory under graphics/templates/.

    The default template is the two files at the templates root. A template is a directory holding
    `stage.css`, `engine.js` and `template.json` (which declares its own archetypes). This is the
    per-tool animation tier: the vocabulary belongs to the tool, not to the pipeline.
    """
    if not name or name == "default":
        return TEMPLATES
    d = TEMPLATES / name
    if not (d / "engine.js").exists():
        raise FileNotFoundError(f"unknown graphics template {name!r} (expected {d})")
    return d


def build_stage_html(doc: dict) -> str:
    d = template_dir(doc.get("template"))
    shared = TEMPLATES / "shared.css"
    css = (shared.read_text(encoding="utf-8") + "\n" if shared.exists() else "") + (d / "stage.css").read_text(encoding="utf-8")
    js = (d / "engine.js").read_text(encoding="utf-8")
    vend_scripts = ""
    shared_vend = TEMPLATES / "vendor"     # renderer-wide libs (gsap): every template gets pro easing
    if shared_vend.is_dir():
        for lib in ("gsap.min.js",):
            if (shared_vend / lib).exists():
                vend_scripts += f"<script src='{shared_vend.resolve().as_uri()}/{lib}'></script>"
    vend = d / "vendor"
    if vend.is_dir():
        doc = dict(doc, vendor_url=vend.resolve().as_uri())
        for lib in ("three.min.js", "GLTFLoader.legacy.js"):
            if (vend / lib).exists():
                vend_scripts += f"<script src='{vend.resolve().as_uri()}/{lib}'></script>"
    data = json.dumps(doc, ensure_ascii=False).replace("</", "<\\/")
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<style>{css}</style></head><body><div id='stage'><div id='postfx'>"
        "<div class='vign'></div><div class='htone'></div><div class='grain'></div>"
        "</div></div>"
        f"<script>window.DATA={data};</script>{vend_scripts}<script>{js}</script></body></html>"
    )


def _ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg  # pip fallback, same binary the QA gate uses
    return imageio_ffmpeg.get_ffmpeg_exe()


def render(doc: dict, audio: Path, out: Path, work: Path, duration_s: float,
           fps: int = FPS, crf: int = 20) -> dict:
    from playwright.sync_api import sync_playwright

    work.mkdir(parents=True, exist_ok=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    html = work / "stage.html"
    html.write_text(build_stage_html(doc), encoding="utf-8")
    silent = work / "silent.mp4"
    ff = _ffmpeg()
    n_frames = int(round(duration_s * fps))

    enc = subprocess.Popen(
        [ff, "-y", "-loglevel", "error", "-f", "image2pipe", "-c:v", "mjpeg", "-framerate", str(fps),
         "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p",
         "-movflags", "+faststart", str(silent)],
        stdin=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox", "--font-render-hinting=none",
                                              "--allow-file-access-from-files"])
            page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
            page.goto(html.as_uri())
            page.wait_for_function("window.ready === true", timeout=30000)
            for f in range(n_frames):
                t = f / fps
                page.evaluate(f"window.setTime({t:.4f})")
                enc.stdin.write(page.screenshot(type="jpeg", quality=95))
            browser.close()
        enc.stdin.close()
        rc = enc.wait(timeout=600)
        if rc != 0:
            raise RuntimeError(f"ffmpeg encode failed: {enc.stderr.read().decode(errors='replace')[-400:]}")
    finally:
        if enc.poll() is None:
            enc.kill()

    # Mux the TTS track; video is copied, audio is trimmed to the scene span.
    mux = subprocess.run(
        [ff, "-y", "-loglevel", "error", "-i", str(silent), "-i", str(audio), "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", f"{duration_s:.3f}", "-movflags", "+faststart",
         str(out)],
        capture_output=True, text=True, timeout=600,
    )
    if mux.returncode != 0 or not out.exists():
        raise RuntimeError(f"mux failed: {mux.stderr[-400:]}")
    return {"frames": n_frames, "fps": fps, "duration_s": duration_s, "out": str(out),
            "html": str(html)}
