# Generated-graphics engine

Builds illustrated, word-synced scenes from a tool's README, then renders them to MP4 with the TTS audio.
Design and review: `PLAN-REVIEW.md`.

```
python3 -m pytest graphics/tests
python3 -m graphics.cli lint  --sheet fixtures/craft-anything/features.json --source fixtures/craft-anything/source.md \
        --words fixtures/craft-anything/words.json --beats fixtures/craft-anything/beats.json --duration 36.07
python3 -m graphics.cli build  ... --audio voice.mp3 --out out.mp4 --work build/
```

Needs: Python 3.13, `playwright` with Chromium (`python3 -m playwright install chromium`), its system
libraries (Debian/Ubuntu: libnspr4, libnss3, libatk1.0-0, libatk-bridge2.0-0, libcups2, libxkbcommon0,
libxcomposite1, libxdamage1, libxrandr2, libgbm1, libpango-1.0-0, libcairo2, libasound2t64), and ffmpeg
(system, or the `imageio-ffmpeg` pip package).

Exit codes: 0 ok, 2 feature sheet fails lint, 3 beat plan fails lint, 4 render error.
Nothing renders from a plan that fails lint.

## Creative workflow and limits

The `desktop_action` archetype is an **illustration**, not product footage. Its payload
names an app, a target, a ref, a mode (`snapshot`, `click`, or `stale`) and exactly two
spoken `cue_phrases`; stale mode also supplies `new_ref`. The app context is visible
immediately, while the ref and action change on their own cues. Use it only for a
README-grounded accessibility/ref interaction. Other tools need their own specific
visual design; changing labels on this mock app is not a creative strategy.

Scene timing in the production adapter comes from the narration's per-scene word
alignment. The standalone CLI chunks words differently; both enforce the script
fingerprint. Unmatched cues are reported as fallbacks, not proof of sync. Always review
frames at scene starts, every important cue, and the end on a phone-sized preview. The
pixel-motion metric can be inflated by ambient motion and is not a taste or sync gate.

Stage typography embeds the repository's Inter font; no network font is needed. The
browser still needs its system libraries. A lint pass is not a rendered-video review.
