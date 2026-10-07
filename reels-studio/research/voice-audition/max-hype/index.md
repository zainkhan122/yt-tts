# Maximum enthusiasm af_heart: D vs F

Listen to the `00-...-in-order.mp3` file (samples in table order).

Script lines:
- Okay, this AI just put Minecraft inside GTA Five!
- And no, it's not a mod pack.
- An AI coding agent built the whole thing!
- The best part?
- It's free, it's open source, and it hit almost five thousand GitHub stars in one week!

| Sample | Speed / blend | Preset | Pace | Note |
|---|---|---|---|---|
| D-hype | ×1.33 | hype | 231 wpm | current channel voice |
| F-maxhype | ×1.33 | maxhype | 231 wpm | MAX enthusiasm: wider melody (hook +1 st), brighter, punchier; same pace as D |

## Measured (2026-10-08, whisper small.en, same 5 lines)

| | D-hype (previous default) | F-maxhype (NEW default) |
|---|---|---|
| pace | 231 wpm (x1.33) | 231 wpm (x1.33) |
| avg pitch | 213 Hz | 222 Hz (+0.7 st) |
| melody range (p10-p90) | 8.3 st | 11.4 st (+37%) |
| whisper intelligibility | 100% | 98.5% (only "An AI" heard as "The AI") |

F = af_heart + Praat PSOLA intonation expansion x1.45 per line (`expand_melody`), stronger line accents
(hook +1.0 st, "!" +0.7, "?" +0.44), +1.1 st lift, presence +4.5 dB, air +3.5 dB, 4.5:1 compression.
Fallback to D: set `"voice_fx": "hype"` in `config/channel.json`. Per-brief override: `"melody": 1.3`.
