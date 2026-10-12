"""Frame 0 must be the cover (owner report 2026-10-12: "plain frame 0 image which has Nothing on it").

Every platform that cannot take our uploaded cover image falls back to the video's FIRST frame
(Buffer previews it, Facebook Reels take it, YouTube Shorts show it until the custom thumbnail
lands). The theme hides .sp-heading/.sp-sub/.sp-imgcard/.sp-steps with CSS opacity:0 and fades them
in from 0.05 s, so a hook built from those types used to render an EMPTY frame 0 — clip hooks were
fine, which is why earlier batches looked correct.

This suite runs the REAL templates/_spotlight/scene.js (buildScene) in node with DOM mocks and
checks, per scene type:
  * as the hook (first scene): every cover-critical element carries inline opacity 1 -> visible at 0.0 s
  * as a later scene: no such override -> the staged fade-in is preserved
The CSS hiding table is read from the real scene.css, so a new hidden class cannot slip through.
Skips when node is unavailable.
"""
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCENES = {
    "clip": {"id": "hook", "type": "clip", "src": "demo.mp4", "in": 0, "out": 3,
             "headline": "NEW TAB, *WRITTEN BY AI*", "sub": "An AI homepage", "say": "Watch this."},
    "image": {"id": "hook", "type": "image", "img": {"file": "og.png"}, "heading": "A MODEL THAT *CANNOT RAMBLE*",
              "sub": "Probabilities, not text", "say": "Cloudflare Clef."},
    "stat": {"id": "hook", "type": "stat", "heading": "TWO DOLLARS *PER MILLION*",
             "stat": {"value": 2, "label": "per million tokens", "prefix": "$"}, "say": "Two dollars."},
    "page": {"id": "hook", "type": "page", "img": {"file": "desktop-top.jpg", "w": 1280, "h": 2400},
             "heading": "POST-TRAINED FROM *QWEN*", "url": "example.com", "say": "Here it is."},
    "scroll": {"id": "hook", "type": "scroll", "img": {"file": "desktop-top.jpg", "w": 1280, "h": 2400},
               "url": "example.com", "stops": [{"region": "a"}], "say": "Scroll down."},
    "steps": {"id": "hook", "type": "steps", "steps": ["Install the CLI", "Point it at your repo"],
              "say": "Two steps."},
    "terminal": {"id": "hook", "type": "terminal", "lines": ["npm i x"], "outputs": ["added 1 package"],
                 "title": "Terminal", "say": "One command."},
}
# class -> must be visible at frame 0 when the scene is the hook (see the CSS table check below)
COVER_ELEMENTS = {
    "clip": ["sp-headline", "sp-sub"],
    "image": ["sp-heading", "sp-imgcard"],
    "stat": ["sp-heading", "sp-stat"],
    "page": ["sp-heading", "sp-browser"],
    "scroll": ["sp-browser"],
    "steps": ["sp-heading", "sp-steps"],
    "terminal": ["sp-heading", "sp-term"],
}

HARNESS = r'''
const fs = require("fs");
const [cssPath, jsPath, payloadJson] = process.argv.slice(2);
const payload = JSON.parse(payloadJson);

// ---- theme: which classes are invisible by default (opacity: 0 in scene.css)
const css = fs.readFileSync(cssPath, "utf8").replace(/\/\*[\s\S]*?\*\//g, "");  // strip comments first
const hidden = new Set();
for (const m of css.matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
  if (!/opacity:\s*0\s*;/.test(m[2])) continue;
  for (const sel of m[1].split(",")) {
    const last = sel.trim().split(/[\s>+~]+/).pop() || "";
    const cls = last.match(/^\.([a-z0-9-]+)$/);
    if (cls) hidden.add(cls[1]);
  }
}

// ---- extract the real buildScene from scene.js
const src = fs.readFileSync(jsPath, "utf8");
const start = src.indexOf("async function buildScene(tl, A) {");
if (start < 0) { console.error("buildScene not found"); process.exit(2); }
let depth = 0, end = start;
for (let i = src.indexOf("{", start); i < src.length; i++) {
  if (src[i] === "{") depth++;
  else if (src[i] === "}") { depth--; if (depth === 0) { end = i + 1; break; } }
}
const body = src.slice(start, end);

// ---- DOM mocks
const created = [];
function mkNode(tag, cls, text) {
  const classes = String(cls || "").split(/\s+/).filter(Boolean);
  const el = {
    tag, class: classes.join(" "), classes, text: text || "", children: [], attrs: {}, style: {},
    cssHidden: classes.some((c) => hidden.has(c)),
    appendChild(c) { this.children.push(c); return c; },
    setAttribute(k, v) { this.attrs[k] = v; },
    getAttribute() { return null; },
    querySelector() { return null; },
    querySelectorAll() { return []; },
  };
  if (el.cssHidden) el.style.opacity = "0";   // what the browser computes before any tween
  created.push(el);
  return el;
}
const stage = mkNode("div", "stage");
globalThis.document = { createTextNode: (t) => ({ text: t }) };
const A = {
  D: 20,
  DATA: payload.data,
  mk: (tag, cls, parent, text) => { const el = mkNode(tag, cls, text); if (parent && parent.appendChild) parent.appendChild(el); return el; },
  $: (sel) => (sel === "#stage" ? stage : null),
  ev: (k, d) => (typeof d === "number" ? d : 0.8),
  fit: (el) => { el.scrollHeight = 40; return el; },
  endCard: () => {},
  countText: () => {},
  svg: (tag, attrs, parent) => { const el = mkNode(tag, ""); if (attrs) el.attrs = { ...attrs }; if (parent && parent.appendChild) parent.appendChild(el); return el; },
};
const tl = { fromTo: () => {}, set: () => {}, to: () => {} };

const buildFn = eval("(" + body + ")");
(async () => {
  await buildFn(tl, A);
  console.log(JSON.stringify(created.filter((e) => e.class).map((e) => ({ cls: e.class, inline: e.style.opacity === "1", hidden: e.cssHidden }))));
})().catch((e) => { console.error(e && e.stack ? e.stack : String(e)); process.exit(1); });
'''


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class Frame0CoverTests(unittest.TestCase):
    harness = ROOT / "tests/_frame0_harness.js"

    @classmethod
    def setUpClass(cls):
        cls.harness.write_text(HARNESS)

    @classmethod
    def tearDownClass(cls):
        cls.harness.unlink(missing_ok=True)

    def build(self, scene, first):
        scenes = [scene, {"id": "outro", "type": "endcard", "say": "Follow for more."}]
        if not first:
            scenes = [{"id": "opener", "type": "clip", "src": "d.mp4", "in": 0, "out": 2, "say": "First."}, scene]
        data = {"extra": {"scenes": scenes, "regions": {"a": {"x": 10, "y": 10, "w": 100, "h": 50}}, "facts": {}, "url": "example.com"},
                "captions": {"keywords": []}}
        payload = json.dumps({"data": data})
        out = subprocess.run(["node", str(self.harness), str(ROOT / "templates/_spotlight/scene.css"),
                              str(ROOT / "templates/_spotlight/scene.js"), payload],
                             capture_output=True, text=True, timeout=60)
        self.assertEqual(out.returncode, 0, out.stderr[-500:])
        return json.loads(out.stdout)

    def visible_at_zero(self, rows, cls):
        """Visible on frame 0: the theme does not hide it, or the builder forces inline opacity 1."""
        return any(cls in (r["cls"] or "").split() and (r["inline"] or not r["hidden"]) for r in rows)

    def forced_inline(self, rows, cls):
        return any(cls in (r["cls"] or "").split() and r["inline"] for r in rows)

    def test_every_scene_type_shows_its_cover_on_frame_zero(self):
        for typ, scene in SCENES.items():
            with self.subTest(scene_type=typ):
                rows = self.build(scene, first=True)
                for cls in COVER_ELEMENTS[typ]:
                    self.assertTrue(self.visible_at_zero(rows, cls),
                                    f"{typ} hook: {cls} is not visible on frame 0 (cover would be blank)")

    def test_later_scenes_keep_the_staged_fade(self):
        for typ, scene in SCENES.items():
            with self.subTest(scene_type=typ):
                scene = {**scene, "id": "b"}
                rows = self.build(scene, first=False)
                for cls in COVER_ELEMENTS[typ]:
                    self.assertFalse(self.forced_inline(rows, cls),
                                     f"{typ}: a non-hook scene must still fade in (found forced visibility on {cls})")

    def test_the_theme_still_hides_the_cover_classes(self):
        """If the CSS stops hiding these, this suite's premise changed — re-check the rule."""
        css = (ROOT / "templates/_spotlight/scene.css").read_text()
        hidden = set(re.findall(r"\.([a-z0-9-]+)\s*\{[^{}]*?opacity:\s*0\s*;", css))
        for cls in ("sp-heading", "sp-sub", "sp-imgcard", "sp-steps"):
            self.assertIn(cls, hidden, f"{cls} is no longer CSS-hidden; frame-0 rule needs review")


if __name__ == "__main__":
    unittest.main()
