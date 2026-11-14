# The house visual system

Everything a short shows is generated here. There is no official demo clip, no browser screenshot
and no README scroll: every scene is drawn from the tool's own features by the engine in this
folder.

This file is the contract between the agent (which decides *what* each scene shows) and the engine
(which decides *how* it looks).

---

## 1. The three decisions

A beat plan makes three decisions, and nothing else decides them:

| Decision | Where | Who |
|---|---|---|
| **What** each scene shows | `beats.json` → `scenes[].archetype` + `payload` | the agent |
| **How** the whole video looks | `features.json` → `tool.category` | the engine (this folder) |
| **When** each element fires | `cues.py` (bound to the real voice words) | the engine |

The second one is the part that used to be missing. Before the visual language, every video came
out in the same yellow-on-black cards no matter what the tool was. Now the tool's **category**
decides the plate, the accent pair and which archetypes are even allowed.

---

## 2. The plates

A plate is the mood of the frame. Switching plate mid-video is what makes a sequence feel edited
instead of stapled together.

| Plate | Surface | Used for |
|---|---|---|
| `paper` | warm off-white `#F7F5EF`, halftone print texture | light, editorial, explanatory |
| `ink` | near-black `#0B0B0C` | the catch, the honest limit, a dark beat |
| `slate` | grey-green `#B4B7B2` | a "here is the system" beat |
| `dots` | light blue-grey `#E9EAEE` with a dot grid | step-by-step, tutorial |
| `deep` | `#0C0E13` with a slow 72px grid | data, benchmarks, charts |

Set it per scene: `"payload": {"plate": "ink"}`. A scene with no plate inherits the previous one.

---

## 3. The typography

The house voice, copied from the reference reels:

- **The statement** — sentence case, Inter 800, tight tracking. *Not all caps.* All caps is the
  generic-AI-short look.
- **The emphasis word** — an *italic serif* in the accent colour. Mark it with `*asterisks*`:
  `"big": "Your AI reviewer *never read* the issue"`.
- **The HUD** — JetBrains Mono. A scene label on the left, a live metric on the right:
  `"hud": {"label": "// 03 — the rules", "metric": "RULES", "value": "412"}`.
- **The captions** — word-by-word karaoke, sentence case, the spoken word in the accent colour.

---

## 4. The archetypes

### The house library (every template can draw these)

| Archetype | What the viewer sees | Use for |
|---|---|---|
| `stage_board` | a composed illustration: drawn props laid out on the stage | the general "how it works" scene |
| `chart_bars` | a real bar chart with an axis, labels and values | counts, comparisons, rule sets |
| `chart_line` | a real line/area chart with an axis and drawn points | growth, curves, over time |
| `chart_donut` | segments of one whole, each on its own word | a share of something |
| `compare_split` | two columns and a divider | before/after, paid/free, A vs B |
| `verdict_pair` | ✓ what works and ⚠ the catch, two tones | the honest limit |
| `app_mock` | a fabricated application window, being used | "show the tool doing the job" |
| `steps_path` | a numbered path with a rail that fills on the voice | a recipe, a how-to |
| `spec_strip` | a row of metric badges | specs at a glance |
| `stamp_card` | a rubber stamp that slams down | "free", "open source", "the catch" |
| `quote_block` | a pull quote with attribution | a line from the maker |

There is **no human character in the house style**. The earlier illustrated narrator was removed
(owner, 14 Nov 2026): a drawn face in frame that cannot lip-sync to the voice reads as broken, so
the reel keeps its energy through motion, charts and typography instead.

### The eight originals (still supported)

`concept_card`, `stat_pop`, `chip_grid`, `flow_link`, `terminal_type`, `toggle_steps`,
`cta_stack`, `endcard`.

### Per-tool templates

A template under `graphics/templates/<name>/` may declare its own archetypes in `template.json`.
**Only archetypes the template's engine can draw are lintable** — the linter reads the engine, so a
plan can no longer pass lint and then crash on the first frame.

---

## 5. The prop library (`stage_board`)

A `stage_board` scene is a composition of drawn props, positioned in normalised coordinates
(`x`, `y`, `w`, `h` are fractions of the stage). Each prop springs in on the word that names it.

```json
{"kind": "window", "title": "vectorly — review", "x": 0.04, "y": 0.08, "w": 0.54, "h": 0.46,
 "rows": [["issue", "#418 read"], ["diff", "26 files"]]}
```

| Prop | Draws |
|---|---|
| `card` | a printed card with a hard offset shadow |
| `window` | an app/browser window with real chrome and rows |
| `panel` | a console device with a grid of icon buttons and a count |
| `matrix` | a dot matrix of many small things |
| `stack` | a stack of isometric layers |
| `gauge` | a dial with a needle |
| `note` | a small label chip with a tick |
| `stamp` | a rubber stamp |
| `folder` | a manila folder |
| `scale` | a balance scale |
| `spark` | a sparkline in a frame |
| `bar` | a single ranked bar |
| `cells` | a grid of little illustrated people |
| `envelope` | an envelope with a wax seal |
| `machine` | a machine with slots |

### Ambient motion (the frame is never still)

`HOUSE.ambient(t)` is called from every template's `setTime()` and is a pure function of the frame
time — the render is reproducible, no wall-clock animation may live on the stage. It layers:

| Layer | What it does |
|---|---|
| sheen | a wide, soft light travelling across the frame every 9 s; plate-aware (white on dark plates, dark on paper) |
| dust | ~80 motes drifting upward with a slow sway |
| breath | a slow camera push-in + sway on the whole scene (headline + picture, captions excluded), phase held across the scene |

The breath is written as a sum of two or three harmonics per axis, not one sine: a single sine
spends part of every cycle near zero velocity, and a frame that barely moves is a frame the motion
gate reads as static. `bx = 25·sin(0.31t) + 10·sin(0.83t + 1.7)`, `by = 30·cos(0.47t) + 13·sin(0.71t + 0.5)`,
`scale = 1 + 0.028·sin(0.23t) + 0.013·sin(0.61t + 2.1)`.

The QA motion gate (`tools/short_qa.py video`) measures the result at 4 fps against
`config/qa-thresholds.json`: `graphic_only_share ≤ 0.25`, `visual_change_speech ≥ 0.75`. The ambient
layers exist to pass that gate *and* to match the reference reels, which keep something moving in
every frame. Scene-local idle motion stacks on top of it — but it is scene-local, never a global
noise pass:

| Scene | What keeps it alive |
|---|---|
| `concept_card` | the halo breathes out of the printed card on a 2.4 s cycle — the hook frame is never a still print |
| `chart_bars` | the first (hero) bar rises slowly and linearly under the voice, so the chart always has a big moving mass; the other bars grow on their own cue |
| `app_mock` | the agent's reply is **typed out**, character by character, with a blinking caret — the comment bubble is on screen while it is written |
| `spec_strip` | the items rise one by one and the caption comes up last, so the strip reads top to bottom |

The overflow audit excludes the sheen/dust/motes by class: they are full-bleed by design. The scene
wrap itself is excluded for the same reason — it is the camera subject the breath moves. Its children
are still audited, so a payload element that really overflows the frame is still caught.

---

## 6. The rules the linter enforces

| Rule | What it stops |
|---|---|
| **B0** | a beat plan written for a different script |
| **B1** | a scene count that does not match the spoken phrases |
| **B2** | the same archetype twice in a row |
| **B3** | a fact-bearing scene with no feature behind it |
| **B4** | a scene that does not depict what the phrase says |
| **B5** | URLs, markdown, pasted emoji, over-long text, over-long lists |
| **B6** | a payload key the archetype does not declare |
| **B7** | a stat number that is not the feature's own metric |
| **B8/B11** | an archetype the engine cannot draw |
| **B9** | a beat bound to the wrong brief scene |
| **B10** | a chart with no numbers or no source |
| **B12** | an archetype outside the tool's visual language |

---

## 7. Commands

```bash
# lint a beat plan against its feature sheet
python3 -m graphics.cli lint --sheet graphics/fixtures/vectorly/features.json \
        --source graphics/fixtures/vectorly/source.md \
        --words  graphics/fixtures/vectorly/words.json \
        --beats  graphics/fixtures/vectorly/beats.json --duration 33.2

# render a short (needs playwright + chromium + ffmpeg)
python3 -m graphics.cli build --sheet ... --source ... --words ... --beats ... \
        --audio voice.mp3 --out out.mp4 --work build/

# build the scene document and the stage HTML without rendering (no playwright needed)
python3 tools/graphics_preview.py graphics/fixtures/vectorly/beats.json --frames 8
```

`tools/graphics_preview.py` prints the lint result, the resolved visual language, the cue plan and
the frame times. It is the fastest way to see whether a beat plan reads well.

---

## 8. Fonts

The renderer stages the channel fonts (`templates/_base/fonts/`) next to `stage.html` and the house
CSS loads them. **Without them the whole engine renders in the platform's default sans**, which is
the single biggest reason these shorts used to look like a template rather than a designed piece.

| Font | Role |
|---|---|
| Inter | the statement, the cards, the captions |
| Anton | the impact face for hooks |
| JetBrains Mono | the HUD chrome, the terminal, code |
| Noto Nastaliq Urdu | the Urdu line |
