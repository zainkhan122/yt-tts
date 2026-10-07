# Voice audition: pick the channel voice

Line: "An AI coding agent built this: real Minecraft, running inside GTA Five. It's free, open source, and it got almost five thousand GitHub stars in its first week."

Listen to `00-all-voices-in-order.mp3`, which plays the samples in the table's order with short gaps.

| # | Voice | Speed | Length | Words/min | Note | File |
|---|---|---|---|---|---|---|
| 1 | `af_heart` | ×1.15 | 10.4 s | 161 | US female, Kokoro grade A (current default) | [01-af_heart-x1.15.mp3](01-af_heart-x1.15.mp3) |
| 2 | `af_bella` | ×1.15 | 11.0 s | 152 | US female, grade A-, brighter | [02-af_bella-x1.15.mp3](02-af_bella-x1.15.mp3) |
| 3 | `bf_emma` | ×1.15 | 9.6 s | 176 | UK female, grade B- | [03-bf_emma-x1.15.mp3](03-bf_emma-x1.15.mp3) |
| 4 | `am_michael` | ×1.15 | 11.3 s | 149 | US male, grade C+, calm | [04-am_michael-x1.15.mp3](04-am_michael-x1.15.mp3) |
| 5 | `am_puck` | ×1.15 | 10.0 s | 168 | US male, grade C+, energetic | [05-am_puck-x1.15.mp3](05-am_puck-x1.15.mp3) |
| 6 | `af_heart` | ×1.05 | 11.1 s | 151 | speed test: our old pace | [06-af_heart-x1.05.mp3](06-af_heart-x1.05.mp3) |
| 7 | `af_heart` | ×1.30 | 9.3 s | 181 | speed test: TikTok-creator pace | [07-af_heart-x1.30.mp3](07-af_heart-x1.30.mp3) |

Benchmark from the social scan: top TikTok AI-tool creators speak at **~170–230 wpm** (`research/social/index.csv`).

## Speed calibration for the ~170 wpm target (from the social scan)

| Voice | wpm at ×1.15 | Speed for ~170 wpm |
|---|---|---|
| af_heart | 161 | ×1.22 |
| af_bella | 152 | ×1.29 |
| bf_emma | 176 | ×1.11 |
| am_michael | 149 | ×1.31 |
| am_puck | 168 | ×1.16 |

After the pick, set `voice` + `speed` in `config/channel.json`. Every brief inherits them.
