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
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "templates" / "_spotlight"))
import spotcore  # noqa: E402  (geometry contract shared with the renderer)

SCENES = {
    "clip": {"id": "hook", "type": "clip", "src": "demo.mp4", "in": 0, "out": 3,
             "headline": "NEW TAB, *WRITTEN BY AI*", "sub": "An AI homepage", "say": "Watch this."},
    "image": {"id": "hook", "type": "image", "img": {"file": "og.png"}, "heading": "A MODEL THAT *CANNOT RAMBLE*",
              "sub": "Probabilities, not text", "say": "Cloudflare Clef."},
    "stat": {"id": "hook", "type": "stat", "heading": "TWO DOLLARS *PER MILLION*",
             "stat": {"value": 2, "label": "per million tokens", "prefix": "$"}, "say": "Two dollars."},
    "verdict": {"id": "hook", "type": "verdict", "heading": "THE *CATCH*",
                "cons": ["One limitation"], "pros": ["One benefit"], "say": "Here is the tradeoff."},
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
    "image": ["sp-heading", "sp-sub", "sp-imgcard"],
    "stat": ["sp-heading", "sp-stat"],
    "verdict": ["sp-heading"],
    "page": ["sp-heading", "sp-browser"],
    "scroll": ["sp-heading", "sp-browser"],
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
    tag, class: classes.join(" "), classes, text: text || "", children: [], attrs: {}, style: {}, fitOptions: null,
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
  fit: (el, opts = {}) => { el.fitOptions = opts; el.scrollHeight = 40; return opts.max; },
  endCard: () => {},
  countText: () => {},
  svg: (tag, attrs, parent) => { const el = mkNode(tag, ""); if (attrs) el.attrs = { ...attrs }; if (parent && parent.appendChild) parent.appendChild(el); return el; },
};
const tl = { fromTo: () => {}, set: () => {}, to: () => {} };

const buildFn = eval("(" + body + ")");
(async () => {
  await buildFn(tl, A);
  console.log(JSON.stringify(created.filter((e) => e.class).map((e) => ({
    cls: e.class, inline: e.style.opacity === "1", hidden: e.cssHidden,
    style: { ...e.style }, fit: e.fitOptions,
  }))));
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
        data = {"extra": {"scenes": scenes, "regions": {"a": {"x": 10, "y": 10, "w": 100, "h": 50}},
                           "facts": {"name": "Example Tool", "repo": "example/tool"}, "url": "example.com"},
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

    def test_every_heading_cover_uses_the_big_bold_clip_hook_font_range(self):
        for typ, scene in SCENES.items():
            with self.subTest(scene_type=typ):
                rows = self.build(scene, first=True)
                if typ == "clip":
                    # The original reference path already uses this same big font range.
                    heading = next((r for r in rows if "sp-headline" in r["cls"].split()), None)
                    self.assertIsNotNone(heading, "clip: expected its original headline")
                else:
                    heading = next((r for r in rows if "sp-heading" in r["cls"].split()), None)
                    self.assertIsNotNone(heading, f"{typ}: expected a cover heading")
                    self.assertIn("cover-heading", heading["cls"].split(), f"{typ}: hook did not get cover typography")
                self.assertEqual(heading["fit"], {"max": 200, "min": 80, "maxH": 380})

    def test_cover_heading_css_matches_the_original_big_headline_band(self):
        css = (ROOT / "templates/_spotlight/scene.css").read_text()
        match = re.search(r"\.sp-heading\.cover-heading\s*\{([^}]*)\}", css)
        self.assertIsNotNone(match, "missing large cover-heading rule")
        props = dict(re.findall(r"([a-z-]+)\s*:\s*([^;]+);", match.group(1)))
        self.assertEqual(props.get("top"), "236px")
        self.assertEqual(props.get("height"), "380px")
        self.assertEqual(props.get("font-size"), "170px")

    def test_later_heading_keeps_the_smaller_scene_typography(self):
        scene = {**SCENES["image"], "id": "later-image"}
        rows = self.build(scene, first=False)
        heading = next(r for r in rows if "sp-heading" in r["cls"].split())
        self.assertNotIn("cover-heading", heading["cls"].split())
        self.assertEqual(heading["fit"], {"max": 128, "min": 56, "maxH": 180})

    def test_image_hook_reflows_large_title_subtitle_and_card_without_overlap(self):
        scene = {**SCENES["image"]}
        rows = self.build(scene, first=True)
        sub = next(r for r in rows if "sp-sub" in r["cls"].split())
        card = next(r for r in rows if "sp-imgcard" in r["cls"].split())
        top, height = int(card["style"]["top"].rstrip("px")), int(card["style"]["height"].rstrip("px"))
        self.assertEqual(sub["style"].get("top"), "616px")
        self.assertGreaterEqual(top, int(sub["style"]["top"].rstrip("px")) + sub.get("height", 40))
        self.assertLessEqual(top + height, spotcore.LAYOUT["stage_bottom"], "card must clear the caption zone")
        self.assertGreaterEqual(top, spotcore.LAYOUT["cover_top"] - 1)

    def test_image_hook_without_subtitle_still_uses_big_title_and_lower_card(self):
        scene = {k: v for k, v in SCENES["image"].items() if k != "sub"}
        rows = self.build(scene, first=True)
        heading = next(r for r in rows if "sp-heading" in r["cls"].split())
        card = next(r for r in rows if "sp-imgcard" in r["cls"].split())
        self.assertIn("cover-heading", heading["cls"].split())
        top, height = int(card["style"]["top"].rstrip("px")), int(card["style"]["height"].rstrip("px"))
        self.assertLessEqual(top + height, spotcore.LAYOUT["stage_bottom"])

    def test_big_title_card_layouts_move_supporting_content_below(self):
        """Every supporting card starts below the cover title AND ends above the captions."""
        cases = [("page", "sp-browser"), ("terminal", "sp-term"), ("stat", "sp-stat"), ("steps", "sp-steps")]
        for typ, cls in cases:
            with self.subTest(scene_type=typ):
                rows = self.build(SCENES[typ], first=True)
                row = next(r for r in rows if cls in r["cls"].split())
                top = int(row["style"]["top"].rstrip("px"))
                self.assertGreaterEqual(top, spotcore.LAYOUT["cover_top"] - 1,
                                        f"{typ}: card starts inside the big title band")
                bottom = top + (int(row["style"].get("height", "0").rstrip("px")) if row["style"].get("height") else 0)
                self.assertLessEqual(bottom, spotcore.LAYOUT["stage_bottom"],
                                     f"{typ}: card runs into the caption zone")

    def test_the_theme_still_hides_the_cover_classes(self):
        """If the CSS stops hiding these, this suite's premise changed — re-check the rule."""
        css = (ROOT / "templates/_spotlight/scene.css").read_text()
        hidden = set(re.findall(r"\.([a-z0-9-]+)\s*\{[^{}]*?opacity:\s*0\s*;", css))
        for cls in ("sp-heading", "sp-sub", "sp-imgcard", "sp-steps"):
            self.assertIn(cls, hidden, f"{cls} is no longer CSS-hidden; frame-0 rule needs review")


class Frame0GuardTests(unittest.TestCase):
    """lib/framecheck.py - the measurable half of the cover contract (incident 2026-10-12).

    Threshold evidence (ffmpeg signalstats YMAX of frame 0): the four broken hook renders measured
    79-81, the nine fixed r3/r4 renders 248-255. The guard must fail closed on the low side and
    never block the observed fixed range.
    """

    def test_threshold_sits_between_measured_broken_and_fixed_frames(self):
        from lib import framecheck
        self.assertEqual(framecheck.BRIGHT_YMAX, 160)      # documented, evidence-based
        self.assertGreater(framecheck.BRIGHT_YMAX, 76)     # every measured blank frame fails
        self.assertLessEqual(framecheck.BRIGHT_YMAX, 255)  # every measured fixed frame passes

    def test_max_luma_comes_from_the_raw_frame_bytes(self):
        from unittest import mock
        from lib import framecheck
        bright = bytes([10, 20, 255, 40])   # a headline pixel
        dark = bytes([10, 20, 30, 40])      # background only
        with mock.patch.object(framecheck.subprocess, "run", return_value=mock.Mock(stdout=bright)):
            self.assertEqual(framecheck.ymax_at("whatever.mp4"), 255.0)
            self.assertTrue(framecheck.frame0("whatever.mp4")[0])
        with mock.patch.object(framecheck.subprocess, "run", return_value=mock.Mock(stdout=dark)):
            self.assertEqual(framecheck.ymax_at("whatever.mp4"), 40.0)
            self.assertFalse(framecheck.frame0("whatever.mp4")[0])

    def test_fail_closed_when_the_frame_cannot_be_measured(self):
        from lib import framecheck
        self.assertFalse(framecheck.frame0("/nonexistent/file.mp4")[0])
        ok, peak = framecheck.frame0("/nonexistent/file.mp4")
        self.assertIsNone(peak)

    def test_describe_reports_both_outcomes(self):
        from lib import framecheck
        self.assertIn("NOT VISIBLE", framecheck.describe(False, 80.0))
        self.assertIn("visible", framecheck.describe(True, 250.0))

    def test_qa_gate_records_the_check_and_refuses_to_ship_a_blank_hook(self):
        """The pipeline must fail closed: a False frame0_visible raises, and the manifest keeps the number."""
        source = (ROOT / "lib/pipeline.py").read_text()
        self.assertIn('checks["frame0_visible"] = f0_ok', source)
        self.assertIn('"frame0_ymax": f0_peak', source)
        # the blank-hook refusal must still be its own fail-closed branch (the voice branch above it
        # grew a rebuild-specific message, so look for the branch itself, not a character offset)
        self.assertIn('if not checks.get("frame0_visible"):', source)
        self.assertIn('framecheck.describe(f0_ok, f0_peak)', source)


if __name__ == "__main__":
    unittest.main()
