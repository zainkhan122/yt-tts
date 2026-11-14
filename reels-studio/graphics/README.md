# Generated-graphics engine

The house renderer. It builds illustrated, word-synced scenes from a tool's own README and renders
them to MP4 with the TTS audio.

**The contract for what a scene shows and how it looks is [`HOUSE-STYLE.md`](HOUSE-STYLE.md).** Read
that first; it is the vocabulary the agent writes against.

```
python3 -m pytest graphics/tests
python3 -m graphics.cli lint  --sheet fixtures/vectorly/features.json --source fixtures/vectorly/source.md \
        --words fixtures/vectorly/words.json --beats fixtures/vectorly/beats.json --duration 33.2
python3 -m graphics.cli build  ... --audio voice.mp3 --out out.mp4 --work build/
```

Needs: Python 3.13, `playwright` with Chromium (`python3 -m playwright install chromium`), its system
libraries (Debian/Ubuntu: libnspr4, libnss3, libatk1.0-0, libatk-bridge2.0-0, libcups2, libxkbcommon0,
libxcomposite1, libxdamage1, libxrandr2, libgbm1, libpango-1.0-0, libcairo2, libasound2t64), and ffmpeg
(system, or the `imageio-ffmpeg` pip package).

Exit codes: 0 ok, 2 feature sheet fails lint, 3 beat plan fails lint, 4 render error.
Nothing renders from a plan that fails lint.

## Layout

Two rendering tiers, kept apart on purpose — one stylesheet cannot serve both without one of them
falling back to a default font.

| Path | What it is |
|---|---|
| `templates/house.js` | **the house visual language**: plates, the illustration stage, the charts, the comparator, the verdict, the fabricated app window, the prop library. Loaded by the house engine. |
| `templates/house.css` | the house style layer: the channel fonts, the plate variables, the print texture, the post-processing. Used by the house engine. |
| `templates/engine.js`, `templates/stage.css` | the house engine: the eight original archetypes plus the house library, in the house voice. It draws its own caption band and its own end-card. |
| `templates/shared.css`, `templates/shared.js`, `templates/motion.js`, `outro.js` | the shared house layer for **per-tool templates**: the caption band, the handle, the brand end-card and the deterministic narration cues. |
| `templates/<tool>/` | a per-tool template: its own archetypes, css and engine, with the shared house layer injected after it. |
| `visual_language.py` | the registry: a tool's category decides the plate, the accent pair and the archetypes on the table. |
| `features.py` | the feature sheet: the grounding data every graphic is checked against. |
| `beats.py` | the beat plan and its lint (B0–B12). |
| `cues.py` | when each element fires, bound to the real voice words. |
| `stage.py` | the pipeline adapter: brief → scene document → render. |
| `render.py` | the renderer: Playwright frame capture → ffmpeg, with the font gate, the caption-band gate and the edge-overflow audit. |

## Fixtures

`fixtures/craft-anything/` is the original smoke fixture. `fixtures/vectorly/` is a worked example of
the full house vocabulary — a board, a chart, an app mock, a spec strip, a verdict and an end card.
Build its stage with:

```
python3 tools/graphics_preview.py graphics/fixtures/vectorly/beats.json --frames 8
```
