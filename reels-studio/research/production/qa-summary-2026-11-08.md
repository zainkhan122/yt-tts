# Batch 2026-11-08 · seven approved repo Shorts

Measured with `tools/short_qa.py video` on the exact MP4 bytes that are released and queued.

| Short | Release tag | MP4 sha256 (first 12) | Duration | WPM | Hook start | First phrase | Visual change | Verdict |
|---|---|---|---|---|---|---|---|---|
| repo-unslop-01 | renders-2026-11-08d | 8f3dc2203969 | 43.0 s | 174.4 | 0.28 s | 2.83 s | 0.872 | PASS |
| repo-superagent-01 | renders-2026-11-08 | d76379519cba | 41.3 s | 176.0 | 0.29 s | 3.13 s | 0.863 | PASS |
| repo-reavideo-01 | renders-2026-11-08d | 42d8028b4aef | 40.8 s | 172.3 | 0.28 s | 1.75 s | 0.858 | PASS |
| repo-dshgo-01 | renders-2026-11-08b | 6bc668fbbe1c | 40.3 s | 168.4 | 0.27 s | 2.19 s | 0.900 | PASS |
| repo-autoloop-01 | renders-2026-11-08c | 95ceaa4585e3 | 41.3 s | 176.0 | 0.28 s | 2.21 s | 0.872 | PASS |
| repo-vork-01 | renders-2026-11-08c | 31f7d9325514 | 40.3 s | 169.9 | 0.28 s | 2.32 s | 0.866 | PASS |
| repo-sand3d-01 | renders-2026-11-08d | ca4dd0452bca | 39.3 s | 174.3 | 0.09 s | 2.21 s | 0.880 | PASS |

Thresholds (`config/qa-thresholds.json`): duration 29-55 s, speech 167-211 wpm, hook start <= 0.3 s, first phrase <= 3.5 s, visual change on speech >= 0.75.

Sync: every brief rebuilt with `cue fallbacks: none` — each list/step item fires on the first word of its spoken phrase, and no missing cue can mute a later item.

Voice: the approved Chatterbox voice (channel config) for all seven. Three scripts read below the 167 wpm floor on the first pass
(unslop 162.2, reavideo 164.2, sand3d 155.1) because the engine ignores a `speed` knob; the pipeline now supports `voice_tempo`
(pitch-preserving atempo applied per clip before the timeline is laid out, so scene starts, captions and word timings are all
measured on the final audio). unslop x1.08, reavideo x1.05, sand3d x1.10 put them at 172-174 wpm with nothing drifting.

Covers: three designed concepts per Short, one accent colour, 19.34:1 headline contrast; concept 1 selected for all seven.
autoloop and vork were redrawn (a closed laptop instead of an empty box; a wireframe-to-render split instead of clipped trees)
and re-rendered so the shipped kit cover is the approved image.

Scheduling: see `queue/publish.json` + `tracker/publications.json`.
