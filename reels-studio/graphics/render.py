"""Render a scene document to MP4: deterministic frame capture (Playwright) piped into ffmpeg.

Frame t is drawn by window.setTime(t). Output is reproducible for the same inputs.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from . import TEMPLATES

ROOT = Path(__file__).resolve().parent.parent

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


# Lesson 27 (2026-11-13): the fonts were never loading. `templates/_base/fonts/` shipped Inter,
# Anton and JetBrains Mono, but build_stage_html injected no @font-face, so every stack fell
# through to the box default (DejaVu Sans) and `document.fonts.check()` still answered true —
# it reports a usable match, not the requested face. Measured proof: Inter, Anton and DejaVu
# all rendered "WHO IS BEATING" at 942–943px. That is why no short ever matched a reference's
# type. The faces are now injected, and the alias names cover the stacks the templates already
# ask for ("SF Mono", "Helvetica Neue"), so every existing template is fixed without edits.
_FONT_FACES = (
    # (file, family as written, extra css)
    ("Inter.ttf", "Inter", "font-weight: 100 900; font-style: normal;"),
    ("Anton.ttf", "Anton", "font-weight: 400;"),
    ("JetBrainsMono.ttf", "JetBrains Mono", "font-weight: 100 800;"),
)
_FONT_ALIASES = {"SF Mono": "JetBrainsMono.ttf", "Helvetica Neue": "Inter.ttf"}


def _font_face_css() -> str:
    base = TEMPLATES / "_base" / "fonts"
    if not base.is_dir():
        return ""
    out = []
    for fname, family, extra in _FONT_FACES:
        f = base / fname
        if f.exists():
            out.append(f"@font-face{{font-family:'{family}';src:url('{f.resolve().as_uri()}') "
                       f"format('truetype');{extra}font-display:block;}}")
    for alias, fname in _FONT_ALIASES.items():
        f = base / fname
        if f.exists():
            out.append(f"@font-face{{font-family:'{alias}';src:url('{f.resolve().as_uri()}') "
                       f"format('truetype');font-weight:100 900;font-display:block;}}")
    return "\n".join(out)


def _caption_data(doc: dict) -> dict:
    """Give the shared caption layer what it needs: per-scene words and the word to light up.

    A template engine draws the scene; it does not decide what the caption says or which word is
    yellow. Doing that here means all seven templates get identical, correct captions.
    """
    out = dict(doc)
    scenes = []
    for s in doc.get("scenes", []):
        s2 = dict(s)
        s2["cue_word"] = s.get("cue_word") or s.get("cue") and None
        scenes.append(s2)
    out["scenes"] = scenes
    out.setdefault("caption_words", 4)
    return out


def _shared_js() -> str:
    """The house layer: caption, handle, outro. One file for every template, so brand cannot drift."""
    out = []
    for f in (TEMPLATES / "shared.js", TEMPLATES.parent / "outro.js"):
        if f.exists():
            out.append(f.read_text(encoding="utf-8"))
        else:
            raise FileNotFoundError(f"house layer missing: {f}")
    return "\n".join(out)


def build_stage_html(doc: dict) -> str:
    d = template_dir(doc.get("template"))
    shared = TEMPLATES / "shared.css"
    css = (shared.read_text(encoding="utf-8") + "\n" if shared.exists() else "") + (d / "stage.css").read_text(encoding="utf-8")
    js = (d / "engine.js").read_text(encoding="utf-8")
    motion = (TEMPLATES / "motion.js").read_text(encoding="utf-8")
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
    doc = _caption_data(doc)
    data = json.dumps(doc, ensure_ascii=False).replace("</", "<\\/")
    # Film grain is a full-frame tiled feTurbulence: beautiful, but it defeats x264 (a 45 s short
    # encoded to 544 MB at crf 22). At 0.10 the texture still reads and the file compresses 10x.
    css += "\n#postfx .grain { opacity: 0.10 !important; }\n"
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<style>{_font_face_css()}\n{css}</style></head><body><div id='stage'><div id='postfx'>"
        "<div class='vign'></div><div class='htone'></div><div class='grain'></div>"
        "</div></div>"
        f"<script>window.DATA={data};</script>{vend_scripts}<script>{motion}</script><script>{js}</script>"
        f"<script>{_shared_js()}</script></body></html>"
    )


def _ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg  # pip fallback, same binary the QA gate uses
    return imageio_ffmpeg.get_ffmpeg_exe()


def render(doc: dict, audio: Path, out: Path, work: Path, duration_s: float,
           fps: int = FPS, crf: int = 20, preset: str = "medium") -> dict:
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
         "-i", "-", "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p",
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
            # Gate: the requested faces must actually be the rendered faces. document.fonts.check()
            # is useless here (it answers true for any fallback), so load each face explicitly,
            # wait for fonts.ready, then compare widths against a never-defined family. On the
            # unprefixed build these were all identical, which is how 27 shorts shipped in DejaVu.
            fonts_ok = page.evaluate("""async () => {
              const want = ['Inter', 'JetBrains Mono', 'Anton'];
              for (const f of want) {
                try { await document.fonts.load('900 100px "' + f + '"'); } catch (e) {}
              }
              await document.fonts.ready;
              const c = document.createElement('canvas').getContext('2d');
              const probe = 'WHO IS BEATING HANDGLAB 0123';
              const w = (f) => { c.font = '900 100px ' + f; return c.measureText(probe).width; };
              const generic = w('__never_defined_face__');
              const out = {};
              for (const f of want) out[f] = Math.abs(w('"' + f + '"') - generic) > 1;
              // Anton and Inter must not render identically either, or one file shadows the other.
              out['distinct'] = Math.abs(w('"Anton"') - w('"Inter"')) > 1;
              return out;
            }""")
            missing = [k for k, v in fonts_ok.items() if not v]
            if missing:
                raise RuntimeError(
                    f"font gate: {missing} did not load as distinct faces — the render would fall "
                    f"back to the box default and ship the wrong typeface; refusing to encode")
            # Gate: the house caption band is reserved. No scene element may enter it, or the
            # caption sits on top of the beat's own type (which is exactly what shipped once).
            collisions = page.evaluate("""() => {
              const CAP_TOP = 1210, out = [];
              document.querySelectorAll('.scene').forEach(function (sc) {
                if (sc.style.display === 'none') return;
                sc.querySelectorAll('*').forEach(function (e) {
                  const cs = getComputedStyle(e);
                  if (cs.display === 'none' || cs.visibility === 'hidden') return;
                  if (parseFloat(cs.opacity) < 0.15) return;
                  if (e.closest('#postfx') || e.classList.contains('ng-grid')) return;
                  const r = e.getBoundingClientRect();
                  if (r.height < 4 || r.width < 4) return;
                  if (r.bottom > CAP_TOP + 40) {
                    out.push({cls: e.className, bottom: Math.round(r.bottom)});
                  }
                });
              });
              return out;
            }""")
            if collisions:
                listing = "; ".join(f"{c['cls']} bottom={c['bottom']}" for c in collisions[:6])
                raise RuntimeError(
                    f"caption-band gate: {len(collisions)} element(s) run into the house caption "
                    f"band (y>=1210): {listing}")
            # Gate: the house layer is on screen. The caption/outro contract is browser state, so
            # it has to be proven here — before a single frame is encoded — not guessed from a
            # still afterwards. Enabled by render(local_preview_render.py --house-gate) or HOUSEGATE=1.
            if os.environ.get("HOUSE_GATE") == "1":
                import subprocess as _sp
                gate = _sp.run([sys.executable, str(ROOT / "tools" / "house_gate.py"), str(html)],
                               cwd=str(ROOT), capture_output=True, text=True)
                print(gate.stdout.strip(), flush=True)
                if gate.returncode != 0:
                    raise RuntimeError("house gate failed — refusing to encode a short whose caption "
                                       "or outro breaks the house contract")
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
