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

# Lesson 25 (2026-11-11): musike's platform tiles blew past the right frame edge (flex min-width
# blowout on .mk-pane) and every QA gate passed because they measure pixels, not layout. The owner
# caught it by eye. This audit measures the REAL layout per scene — clipping-ancestor-aware, so
# marquee/ghost/overflow-hidden tricks don't false-fire (ghosted scene furniture and postfx are
# excluded by class/id, low-opacity elements by the 0.6 gate) — and fails BEFORE encoding.
_OVERFLOW_SLACK_PX = 28
_OVERFLOW_MIN_OPACITY = 0.6
_OVERFLOW_JS = """() => {
  const W = %d, H = %d, SLACK = %d, MINOP = %f, out = [];
  document.querySelectorAll('#stage *').forEach(function (e) {
    if (e.closest('#postfx') || e.id === 'ambglow' || e.closest('.ghosted')) return;
    const cs = getComputedStyle(e);
    if (cs.display === 'none' || cs.visibility === 'hidden') return;
    let op = parseFloat(cs.opacity);
    let cl = null, ct = null, cr = null, cb = null;
    let p = e.parentElement;
    while (p && p.id !== 'stage') {
      const pcs = getComputedStyle(p), po = parseFloat(pcs.opacity);
      if (!isNaN(po)) op *= po;
      if (/(hidden|clip)/.test(String(pcs.overflowX) + ' ' + String(pcs.overflowY))) {
        const pr = p.getBoundingClientRect();
        cl = cl === null ? pr.left : Math.max(cl, pr.left);
        ct = ct === null ? pr.top : Math.max(ct, pr.top);
        cr = cr === null ? pr.right : Math.min(cr, pr.right);
        cb = cb === null ? pr.bottom : Math.min(cb, pr.bottom);
      }
      p = p.parentElement;
    }
    if (isNaN(op) || op < MINOP) return;   // fades/slide-ins rise past the gate only when visible
    const er = e.getBoundingClientRect();
    const l = cl === null ? er.left : Math.max(er.left, cl);
    const t = ct === null ? er.top : Math.max(er.top, ct);
    const r = cr === null ? er.right : Math.min(er.right, cr);
    const b = cb === null ? er.bottom : Math.min(er.bottom, cb);
    if (r - l < 40 || b - t < 24) return;  // cursors, dots, icons are not layout
    const over = Math.min(Math.min(l, W - r), Math.min(t, H - b));
    if (over < -SLACK) {
      const cls = (e.className && e.className.baseVal !== undefined) ? e.getAttribute('class') : e.className;
      out.push({cls: String(cls || e.tagName).slice(0, 60), rect: [l, t, r, b].map(Math.round)});
    }
  });
  return out.slice(0, 12);
}""" % (W, H, _OVERFLOW_SLACK_PX, _OVERFLOW_MIN_OPACITY)


def _scene_samples(doc: dict) -> list[tuple[str, float]]:
    """Three probe times per scene: post-fade entry, mid, and pre-exit (where blowouts live)."""
    out = []
    for s in doc.get("scenes", []):
        t0, t1 = float(s["t0"]), float(s["t1"])
        for x in (t0 + 0.45, (t0 + t1) / 2, t1 - 0.35):
            out.append((str(s.get("id", "?")), max(t0 + 0.05, min(x, t1 - 0.05))))
    return out


def audit_overflow(page, doc: dict) -> list[dict]:
    """Elements visibly past the frame edge at any probe time. Empty list = layout clean."""
    bad = []
    for sid, t in _scene_samples(doc):
        page.evaluate(f"window.setTime({t:.4f})")
        for v in page.evaluate(_OVERFLOW_JS):
            v["scene"], v["t"] = sid, t
            bad.append(v)
    uniq = {}
    for v in bad:  # same element across probe times = one violation
        uniq.setdefault((v["scene"], v["cls"]), v)
    return list(uniq.values())



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
    # Film grain is a full-frame tiled feTurbulence: beautiful, but it defeats x264 (a 45 s short
    # encoded to 544 MB at crf 22). At 0.10 the texture still reads and the file compresses 10x.
    css += "\n#postfx .grain { opacity: 0.10 !important; }\n"
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
            bad = audit_overflow(page, doc)
            if bad:
                listing = "; ".join(f"{v['scene']} <{v['cls']}> rect={v['rect']} t={v['t']:.2f}s" for v in bad[:6])
                raise RuntimeError(
                    f"edge overflow audit (lesson 25): {len(bad)} element(s) more than "
                    f"{_OVERFLOW_SLACK_PX}px past the {W}x{H} frame: {listing}")
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
