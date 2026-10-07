# viral-short — HyperFrames demo (9:16, 23 s)

A vertical "tool reveal" short built with HyperFrames 0.8.137. It has a word-timed karaoke voice-over, a beat-synced music bed, SFX, 9 scenes, and 5 declared variables for batch branding.

## Reproduce

```bash
bash ../setup-sandbox.sh                          # fresh sandbox only: Node 22, FFmpeg, Chrome, CLI, Kokoro
bash ../setup-whisper.sh                          # only for step 2: safe whisper build (-j1) + small.en model
source ../env.sh                                   # telemetry off, cache dirs (small-VM friendly)
# 1. voice-over (local Kokoro TTS) + loudness normalisation
hyperframes tts assets/audio/vo-script.txt --voice af_heart --speed 1.1 -o assets/audio/vo.wav
#    (then: ffmpeg two-pass loudnorm to -16 LUFS -> assets/audio/vo-master.wav)
# 2. word timings -> captions
hyperframes transcribe assets/audio/vo.wav --engine whisper --model small.en --no-runtime-install
python3 tools/align_captions.py                    # -> assets/captions.json (inlined in index.html)
# 3. royalty-free music + SFX (seeded, deterministic; drop lands on bar 9 = 17.763 s)
python3 tools/synth_audio.py --out assets/audio --duration 23.5 --bpm 121.6 --drop 17.76
# 4. voice-over carve on the music bed (already applied: its lanes are inlined in index.html)
#    needs a repo checkout (kept OUTSIDE the workspace, it is ~139 MB) + npm i -D @hyperframes/core@0.8.137
#    git clone --depth 1 https://github.com/heygen-com/hyperframes /var/tmp/hf/hyperframes
node /var/tmp/hf/hyperframes/skills/hyperframes-audio/scripts/carve.mjs --comp index.html --bed music --voice vo --strength 0.5
# 5. gates, proof frames, render
hyperframes lint && hyperframes check && hyperframes snapshot --at 0,3,6.9,10.4,14.6,18.2,21.3
hyperframes render -o renders/viral-short.mp4
# 6. one template -> many videos
hyperframes render --batch batch-rows.json --strict-variables --output "renders/variants/variant-{index}.mp4"
```

Variables: `handle`, `name`, `tagline`, `accent`, `accent2` (see `data-composition-variables` on `<html>`).
Fonts: Anton, Inter and JetBrains Mono (SIL OFL, from google/fonts). Music and SFX are synthesised from scratch by `tools/synth_audio.py`.
