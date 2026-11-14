"""Render a scene document to MP4: deterministic frame capture (Playwright) piped into ffmpeg.

Frame t is drawn by window.setTime(t). Output is reproducible for the same inputs.

Two rendering tiers, both first-class:

  * the HOUSE engine (the default template) — the house visual language: plates, the illustration
    stage, the charts, the house caption band and the house end-card. Its CSS is house.css and it
    draws its own caption, so the shared house layer is NOT injected here.
  * a PER-TOOL template (a directory under graphics/templates/) — the template's own engine and
    stage.css, with the shared house layer (shared.js caption + outro.js end-card), the
    deterministic narration cues (motion.js) and the real channel fonts injected as @font-face.

Keeping the tiers apart is the point. The house engine sets its own type in its own variables and
the per-tool engines set theirs; one stylesheet cannot serve both without one of them falling back
to a default font. Both tiers keep the hard gates: the faces must really load, no scene may run
into the caption band, and nothing may sit outside the frame.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from . import TEMPLATES

FPS = 30
W, H = 1080, 1920
ROOT = Path(__file__).resolve().parents[1]   # reels-studio/

# Lesson 25 (2026-11-11): musike's platform tiles blew past the right frame edge (flex min-width
# blowout on .mk-pane) and every QA gate passed because they measure pixels, not layout. The owner
# caught it by eye. This audit measures the REAL layout per scene — clipping-ancestor-aware, so
# marquee/ghost/overflow-hidden tricks don't false-fire (ghosted scene furniture, postfx and the
# ambient bleed glow are excluded by class/id, low-opacity elements by the 0.6 gate) — and fails
# BEFORE encoding.
_OVERFLOW_SLACK_PX = 28
_OVERFLOW_MIN_OPACITY = 0.6
_OVERFLOW_JS = """() => {
  const W = %d, H = %d, SLACK = %d, MINOP = %f, out = [];
  document.querySelectorAll('#stage *').forEach(function (e) {
    if (e.closest('#postfx') || e.id === 'ambglow' || e.classList.contains('glow') || e.closest('.ghosted')) return;
    /* the house ambient layers (sheen sweep, dust motes) are full-bleed by design — see house.css */
    if (e.classList.contains('house-sheen') || e.classList.contains('house-dust') || e.classList.contains('house-mote')) return;
    /* the scene wrap itself is the camera subject the ambient breath moves — also full-bleed by
     * design (HOUSE.ambient). Its CHILDREN are still audited, so real payload overflow is caught. */
    if (e.classList.contains('scene')) return;
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

    The default template is the house engine: the house stylesheet, the house stage and the house
    library. A template is a directory holding `stage.css`, `engine.js` and `template.json` (which
    declares its own archetypes). This is the per-tool animation tier: the vocabulary belongs to the
    tool, not to the pipeline.
    """
    if not name or name == "default":
        return TEMPLATES
    d = TEMPLATES / name
    if not (d / "engine.js").exists():
        raise FileNotFoundError(f"unknown graphics template {name!r} (expected {d})")
    return d


def is_house(doc: dict) -> bool:
    """True when the brief renders on the house engine (no per-tool template named)."""
    name = doc.get("template")
    return not name or name == "default"


# ---------------------------------------------------------------- fonts

# Lesson 27 (2026-11-13): the fonts were never loading. `templates/_base/fonts/` shipped Inter,
# Anton and JetBrains Mono, but build_stage_html injected no @font-face, so every stack fell
# through to the box default (DejaVu Sans) and `document.fonts.check()` still answered true —
# it reports a usable match, not the requested face. The faces are now injected, and the alias
# names cover the stacks the per-tool templates already ask for ("SF Mono", "Helvetica Neue"), so
# every existing template is fixed without edits.
_FONT_FACES = (
    # (file, family as written, extra css)
    ("Inter.ttf", "Inter", "font-weight: 100 900; font-style: normal;"),
    ("Anton.ttf", "Anton", "font-weight: 400;"),
    ("JetBrainsMono.ttf", "JetBrains Mono", "font-weight: 100 800;"),
)
_FONT_ALIASES = {"SF Mono": "JetBrainsMono.ttf", "Helvetica Neue": "Inter.ttf"}

FONT_FILES = ("Inter.ttf", "Anton.ttf", "JetBrainsMono.ttf", "NotoNastaliqUrdu.ttf")


def _font_dirs() -> list[Path]:
    """Where the channel fonts live. The pipeline keeps a copy; the templates keep their own."""
    return [ROOT / "templates" / "_base" / "fonts", TEMPLATES / "_base" / "fonts"]


def stage_fonts(work: Path) -> None:
    """Copy the channel fonts next to stage.html so the CSS can reference them by relative URL.

    Without this the whole graphics engine renders in the platform's default sans (DejaVu on the
    cloud runner). It is the single biggest reason these shorts did not look designed: real type in a
    house hierarchy is most of the difference between a template and a piece of art direction.
    """
    for src in _font_dirs():
        if not src.is_dir():
            continue
        dst = work / "fonts"
        dst.mkdir(parents=True, exist_ok=True)
        for name in FONT_FILES:
            f = src / name
            if f.exists():
                shutil.copy2(f, dst / name)
        return


def _font_face_css() -> str:
    """@font-face rules with absolute file URLs, for the per-tool tier.

    The per-tool stylesheets ask for "SF Mono" and "Helvetica Neue"; the alias rules point those at
    the real files so a template needs no edits of its own.
    """
    out = []
    for base in _font_dirs():
        if not base.is_dir():
            continue
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
        break
    return "\n".join(out)


# ---------------------------------------------------------------- the two tiers

def _caption_data(doc: dict) -> dict:
    """Give the shared caption layer what it needs: per-scene words and the word to light up.

    A template engine draws the scene; it does not decide what the caption says or which word is
    yellow. Doing that here means all per-tool templates get identical, correct captions.
    """
    out = dict(doc)
    scenes = []
    for s in doc.get("scenes", []):
        s2 = dict(s)
        s2["cue_word"] = s.get("cue_word") or (s.get("cue") and None)
        scenes.append(s2)
    out["scenes"] = scenes
    out.setdefault("caption_words", 4)
    return out


def _shared_js() -> str:
    """The house layer: caption, handle, outro. One file for every per-tool template, so brand
    cannot drift. The house engine does not use it — it draws its own caption and its own card."""
    out = []
    for f in (TEMPLATES / "shared.js", TEMPLATES.parent / "outro.js"):
        if f.exists():
            out.append(f.read_text(encoding="utf-8"))
        else:
            raise FileNotFoundError(f"house layer missing: {f}")
    return "\n".join(out)


def stage_vendor(template: str | None, work: Path) -> str:
    """Copy a template's vendor assets next to stage.html and return their RELATIVE url.

    Relative beats absolute: the same stage.html then works under file:// (the renderer) and under
    http:// (a human previewing it), with no cross-origin file access involved.
    """
    if not template or template == "default":
        return ""
    vend = TEMPLATES / template / "vendor"
    if not vend.is_dir():
        return ""
    dst = work / "vendor" / template
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(vend, dst)
    return f"vendor/{template}"


def _inline_js(path: Path) -> str:
    """A script as an inline <script> body, with any closing tag neutralised."""
    return path.read_text(encoding="utf-8").replace("</script", "<\\/script")


def build_stage_html(doc: dict, work: Path | None = None) -> str:
    """The stage document.

    Every script is INLINED, not linked: one self-contained file that cannot break on a path, on a
    file:// policy, or on a template that lives somewhere else on disk.
    """
    d = template_dir(doc.get("template"))
    house = is_house(doc)
    inline = ""
    shared_vend = TEMPLATES / "vendor"     # renderer-wide libs (gsap): every template gets pro easing
    if shared_vend.is_dir():
        gsap = shared_vend / "gsap.min.js"
        if gsap.exists():
            inline += "<script>" + _inline_js(gsap) + "</script>"

    if house:
        # The house engine: the house visual language (plates, illustration stage, charts, props)
        # and the house stylesheet, which carries the type variables the engine draws with.
        css_parts = []
        for name in ("house.css", "stage.css"):
            f = d / name
            if f.exists():
                css_parts.append(f.read_text(encoding="utf-8"))
        css = "\n".join(css_parts)
        house_js = TEMPLATES / "house.js"
        if house_js.exists():
            inline += "<script>" + _inline_js(house_js) + "</script>"
        js = (d / "engine.js").read_text(encoding="utf-8")
    else:
        # A per-tool template: the shared house caption/outro layer and the deterministic narration
        # cues, then the template's own engine.
        shared = TEMPLATES / "shared.css"
        css = (shared.read_text(encoding="utf-8") if shared.exists() else "")
        css += "\n" + _font_face_css() + "\n"
        css += (d / "stage.css").read_text(encoding="utf-8")
        motion = TEMPLATES / "motion.js"
        if motion.exists():
            inline += "<script>" + _inline_js(motion) + "</script>"
        js = (d / "engine.js").read_text(encoding="utf-8")
        doc = _caption_data(doc)

    vend = d / "vendor"
    if vend.is_dir():
        rel = stage_vendor(doc.get("template"), work) if work else ""
        if rel:
            doc = dict(doc, vendor_url=rel)
            for lib in ("three.min.js", "GLTFLoader.legacy.js"):
                if (vend / lib).exists():
                    inline += f"<script src='{rel}/{lib}'></script>"

    data = json.dumps(doc, ensure_ascii=False).replace("</", "<\\/")
    body = (f"<script>window.DATA={data};</script>{inline}<script>{js}</script>")
    if not house:
        # The house layer wraps the engine's setTime, so it is injected AFTER it.
        body += f"<script>{_shared_js()}</script>"
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<style>{css}</style></head><body><div id='stage'><div id='postfx'>"
        "<div class='vign'></div><div class='htone'></div><div class='grain'></div>"
        "</div></div>"
        f"{body}</body></html>"
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
    work = work.resolve()   # the stage URL is built with as_uri(), which needs an absolute path
    out = out.resolve()
    stage_fonts(work)
    html = work / "stage.html"
    html.write_text(build_stage_html(doc, work), encoding="utf-8")
    silent = work / "silent.mp4"
    ff = _ffmpeg()
    n_frames = int(round(duration_s * fps))
    house = is_house(doc)
    # The house caption band sits lower than the per-tool one; the gate must know which is which.
    cap_top = 1470 if house else 1210

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
            collisions = page.evaluate("""(CAP_TOP) => {
              const out = [];
              document.querySelectorAll('.scene').forEach(function (sc) {
                if (sc.style.display === 'none') return;
                sc.querySelectorAll('*').forEach(function (e) {
                  const cs = getComputedStyle(e);
                  if (cs.display === 'none' || cs.visibility === 'hidden') return;
                  if (parseFloat(cs.opacity) < 0.15) return;
                  if (e.closest('#postfx') || e.classList.contains('ng-grid')) return;
                  /* the house ambient layers are full-bleed by design */
                  if (e.classList.contains('house-sheen') || e.classList.contains('house-dust') ||
                      e.classList.contains('house-mote')) return;
                  const r = e.getBoundingClientRect();
                  if (r.height < 4 || r.width < 4) return;
                  if (r.bottom > CAP_TOP + 40) {
                    out.push({cls: String(e.className || e.tagName).slice(0, 60), bottom: Math.round(r.bottom)});
                  }
                });
              });
              return out;
            }""", cap_top)
            if collisions:
                listing = "; ".join(f"{c['cls']} bottom={c['bottom']}" for c in collisions[:6])
                raise RuntimeError(
                    f"caption-band gate: {len(collisions)} element(s) run into the house caption "
                    f"band (y>={cap_top}): {listing}")
            # Gate: the house layer is on screen. The caption/outro contract is browser state, so it
            # has to be proven here — before a single frame is encoded — not guessed from a
            # still afterwards. Enabled by render(local_preview_render.py --house-gate) or HOUSEGATE=1.
            if os.environ.get("HOUSE_GATE") == "1":
                import subprocess as _sp
                gate = _sp.run([sys.executable, str(ROOT / "tools" / "house_gate.py"), str(html)],
                               cwd=str(ROOT), capture_output=True, text=True)
                print(gate.stdout.strip(), flush=True)
                if gate.returncode != 0:
                    raise RuntimeError("house gate failed — refusing to encode a short whose caption "
                                       "or outro breaks the house contract")
            motion_fallbacks: list[tuple[str, str]] = []
            report_path = work / "motion-cues.json"
            if not house:
                motion_reports = page.evaluate("() => window.__motionCueReports || {}")
                report_path.write_text(json.dumps(motion_reports, indent=2), encoding="utf-8")
                motion_fallbacks = [(sid, row.get("phrase", "")) for sid, rows in motion_reports.items()
                                    for row in rows if not row.get("matched")]
                if motion_fallbacks:
                    print(f"WARNING: {len(motion_fallbacks)} narration cue fallback(s); "
                          f"review {report_path}", flush=True)
                    if os.environ.get("MOTION_CUES_STRICT") == "1":
                        raise RuntimeError("unmatched motion cues: review timing or disable MOTION_CUES_STRICT")
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
            "html": str(html), "motion_cues": str(report_path),
            "motion_cue_fallbacks": motion_fallbacks}
