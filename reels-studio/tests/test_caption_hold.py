"""Cover rule (owner 2026-10-12): an image hook holds its karaoke caption until the first sentence ends.

Python half (policy + timings) runs everywhere; the JS half (templates/_base/base.js captions())
is exercised with node by extracting the real function and running it against mocks, so the
renderer rule cannot silently rot. Skips the JS half when node is unavailable.
"""
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lib import scenes  # noqa: E402


def load_spotcore():
    spec = importlib.util.spec_from_file_location("spotcore", ROOT / "templates/_spotlight/spotcore.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def brief(root, scenes_list, captions=None):
    pack = Path(root) / "pack"
    pack.mkdir(parents=True, exist_ok=True)
    (pack / "manifest.json").write_text(json.dumps({"files": {}, "regions_css": {}, "facts": {}}))
    b = {"id": "hook-demo-01", "template": "tool-spotlight", "capture": str(pack), "scenes": scenes_list, "seo": {}}
    if captions is not None:
        b["captions"] = captions
    return b


IMAGE_HOOK = [{"id": "hook", "type": "image", "image": "og.png", "heading": "A MODEL THAT *CANNOT* RAMBLE",
               "say": "Cloudflare Clef does not write answers at all. It picks from the options you give it."},
              {"id": "card", "type": "page", "say": "Clef is a twenty seven billion parameter model."}]
CLIP_HOOK = [{"id": "hook", "type": "clip", "src": "demo.mp4", "in": 0, "out": 3, "say": "Watch this."},
             {"id": "end", "type": "endcard", "say": "Which one wins?"}]


class SentenceEndTests(unittest.TestCase):
    def test_first_sentence_end_uses_real_timings(self):
        words = [("Cloudflare", 0.1, 0.5), ("Clef", 0.5, 0.9), ("does", 0.9, 1.2), ("not", 1.2, 1.4),
                 ("write", 1.4, 1.7), ("answers.", 1.7, 2.3), ("It", 2.4, 2.6)]
        self.assertEqual(scenes.sentence_end(words), 2.3)

    def test_question_and_quote_marks_count(self):
        self.assertEqual(scenes.sentence_end([("Really?", 0.0, 1.0), ("Yes.", 1.0, 2.0)]), 1.0)
        self.assertEqual(scenes.sentence_end([("Really?", 0.0, 1.0)]), 1.0)

    def test_no_punctuation_falls_back_to_last_word_then_segment(self):
        self.assertEqual(scenes.sentence_end([("a", 0.0, 1.0), ("b", 1.0, 2.0)]), 2.0)
        self.assertEqual(scenes.sentence_end([], 9.5), 9.5)
        self.assertIsNone(scenes.sentence_end(None))


class HookPolicyTests(unittest.TestCase):
    def setUp(self):
        self.spotcore = load_spotcore()

    def segments(self, b):
        return self.spotcore.segments(b, {"gap": 0.15, "post": 0.25, "lead": 0.35})

    def test_image_hook_opens_the_hold(self):
        with tempfile.TemporaryDirectory() as tmp:
            b = brief(tmp, IMAGE_HOOK)
            self.segments(b)
        self.assertEqual(b["captions"]["hold_seg"], "hook")

    def test_clip_hook_keeps_normal_captions(self):
        with tempfile.TemporaryDirectory() as tmp:
            b = brief(tmp, CLIP_HOOK)
            self.segments(b)
        self.assertNotIn("hold_seg", b["captions"])

    def test_brief_can_opt_out_or_choose_another_scene(self):
        with tempfile.TemporaryDirectory() as tmp:
            b = brief(tmp, IMAGE_HOOK, captions={"hold_seg": ""})
            self.segments(b)
            self.assertEqual(b["captions"]["hold_seg"], "")
            b2 = brief(tmp, IMAGE_HOOK, captions={"hold_seg": "card"})
            self.segments(b2)
            self.assertEqual(b2["captions"]["hold_seg"], "card")

    def test_silent_image_hook_does_not_open_a_hold(self):
        silent = [{"id": "hook", "type": "image", "image": "og.png", "heading": "ONLY A HEADING", "hold": 2.0},
                  {"id": "end", "type": "endcard", "say": "Which one wins?"}]
        with tempfile.TemporaryDirectory() as tmp:
            b = brief(tmp, silent)
            self.segments(b)
        self.assertNotIn("hold_seg", b["captions"])


HARNESS = textwrap.dedent('''
    const fs = require("fs");
    const src = fs.readFileSync(process.argv[2], "utf8");
    const start = src.indexOf("function captions(tl) {");
    if (start < 0) { console.error("captions() not found"); process.exit(2); }
    let depth = 0, end = start;
    for (let i = src.indexOf("{", start); i < src.length; i++) {
      if (src[i] === "{") depth++;
      else if (src[i] === "}") { depth--; if (depth === 0) { end = i + 1; break; } }
    }
    const fn = src.slice(start, end);
    const payload = JSON.parse(process.argv[3]);

    const nodes = [];
    const mkNode = (tag, cls, text) => {
      const el = { tag, class: cls || "", text: text || "", children: [], style: {}, attrs: {},
        clientWidth: 920,
        // the caption fitter measures intrinsic word widths; a real element does this in layout
        getBoundingClientRect() { return { x: 0, y: 0, width: 60 + 10 * (this.text || "").length, height: 80 }; },
        appendChild(c) { this.children.push(c); return c; },
        querySelector() { return { style: {} }; },
        setAttribute(k, v) { this.attrs[k] = v; } };
      nodes.push(el);
      return el;
    };
    const root = mkNode("div");
    const zone = mkNode("div");
    const $ = (sel) => (sel === "#root" ? root : sel === "#cap-zone" ? zone : mkNode("div"));
    const mk = (tag, cls, parent, text) => { const el = mkNode(tag, cls, text); if (parent) parent.appendChild(el); return el; };
    const DATA_ = { captions: payload.captions, order: payload.order, segs: payload.segs };
    const D = payload.D;
    const calls = [];
    const tl = { fromTo: (t, a, b, at) => calls.push(["fromTo", at]), set: (t, a, at) => calls.push(["set", at]) };
    new Function("$", "mk", "DATA_", "D", "tl", fn + "; return captions;")(null, null, null, null, null);
    const fnc = new Function("$", "mk", "DATA_", "D", "return " + fn + ";")($, mk, DATA_, D);
    fnc(tl);
    const groups = nodes.filter((n) => n.class === "cg");
    console.log(JSON.stringify({ groups: groups.length }));
''')
HARNESS_PATH = ROOT / "tests/_caption_harness.js"


def payload(hold):
    words = [["Cloudflare", 0.1, 0.5], ["Clef", 0.5, 0.9], ["does", 0.9, 1.2], ["not", 1.2, 1.4],
             ["write", 1.4, 1.7], ["answers.", 1.7, 2.3], ["It", 2.4, 2.7], ["picks", 2.7, 3.0], ["fast.", 3.0, 3.4]]
    caps = {"maxWords": 3, "keywords": []}
    if hold:
        caps["hold_seg"], caps["hold_until"] = "hook", 2.3
    return {"captions": caps, "order": ["hook"], "segs": {"hook": {"caption": True, "words": words}}, "D": 4.0}


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class RendererHoldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        HARNESS_PATH.write_text(HARNESS)

    @classmethod
    def tearDownClass(cls):
        HARNESS_PATH.unlink(missing_ok=True)

    def run_harness(self, hold):
        out = subprocess.run(["node", str(HARNESS_PATH), str(ROOT / "templates/_base/base.js"), json.dumps(payload(hold))],
                             capture_output=True, text=True, timeout=60)
        self.assertEqual(out.returncode, 0, out.stderr[-400:])
        return json.loads(out.stdout)

    def test_hold_drops_the_covered_words(self):
        with_hold = self.run_harness(True)["groups"]
        without = self.run_harness(False)["groups"]
        self.assertEqual(without, 3)              # 9 words at 3 per group, unchanged behaviour
        self.assertEqual(with_hold, 1)            # both groups starting before 2.3 s are held; "It picks fast." shows
        self.assertLess(with_hold, without)


if __name__ == "__main__":
    unittest.main()
