# Generated-graphics engine

Builds illustrated, word-synced scenes from a tool's README, then renders them to MP4 with the TTS audio.
Design and review: `PLAN-REVIEW.md`.

```
python3 -m pytest graphics/tests
python3 -m graphics.cli lint  --sheet fixtures/craft-anything/features.json --source fixtures/craft-anything/README-source.md \
        --words fixtures/craft-anything/words.json --beats fixtures/craft-anything/beats.json --duration 36.07
python3 -m graphics.cli build  ... --audio voice.mp3 --out out.mp4 --work build/
```

Needs: Python 3.13, `playwright` with Chromium (`python3 -m playwright install chromium`), its system
libraries (Debian/Ubuntu: libnspr4, libnss3, libatk1.0-0, libatk-bridge2.0-0, libcups2, libxkbcommon0,
libxcomposite1, libxdamage1, libxrandr2, libgbm1, libpango-1.0-0, libcairo2, libasound2t64), and ffmpeg
(system, or the `imageio-ffmpeg` pip package).

Exit codes: 0 ok, 2 feature sheet fails lint, 3 beat plan fails lint, 4 render error.
Nothing renders from a plan that fails lint.
