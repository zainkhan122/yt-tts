# Fact sheet — repo-koubo-01 (digital-human-koubo)

Checked 2026-10-28 (GitHub API + README + release v1.0.0). Refresh `stars` at render time.

| Claim | Source | Checked |
|---|---|---|
| One photo + one sentence → finished talking-head video with a digital human (script, lip-sync, voice clean-up, captions, packaging) | README intro, github.com/andyhuo520/digital-human-koubo | 2026-10-28 |
| 1,251 stars, 293 forks, MIT, created 2026-10-26 | GitHub API | 2026-10-28 13:51 UTC (manifest) |
| Pipeline: agent skill (SKILL.md) + Renoise MCP (Grok Video 1.5) for lip-synced segments ≤15 s + whisper transcription check + 4-frame inspection per segment + Remotion 4 editing | README "What it does" / "How it works" | 2026-10-28 |
| The 27-second demo livestream ad cost 482 Renoise credits | README intro blockquote | 2026-10-28 |
| Cost gate: agent quotes segments·seconds·credits·balance and waits for "yes"; segment 1 previewed before batching | README "What it does" | 2026-10-28 |
| 5 editing styles (A xiaolin explainer, B huazi koubo, C launch side, D tutorial, E multi-host) | README + skills/assets/styles/* | 2026-10-28 |
| 48 packaging components measured frame-by-frame from 25 videos by top creators (MrBeast, Mark Rober, MKBHD, Vox, Kurzgesagt, …) | README "What it does" + skills/assets/packaging/each/ (48 images) | 2026-10-28 |
| Multi-language: English, Japanese, Korean, French, Spanish, Arabic tested, whisper back-check 94–100 % | README "What it does" | 2026-10-28 |
| Voice unification: 1/3-octave spectral matching, de-essing, shared reverb; sibilance spread 13.2 dB → 5.9 dB in their tests | README "What it does" | 2026-10-28 |
| Agents: Claude Code tested; Codex expected; others if they support skills + remote MCP + local commands | README "Supported agents" | 2026-10-28 |
| 8 official demo MP4s in release v1.0.0, incl. two 9:16 (workbuddy-live-ad 720×1280 27 s; renoise-koubo-huazi 720×1280 89 s) | GitHub release API + ffprobe of downloads | 2026-10-28 |

## Catches (mandatory)
- Generation runs on **paid Renoise credits** (482 for the 27 s ad; login via browser, no API key).
- The text-behind-presenter effect needs **macOS** (Apple Vision person segmentation); rest is cross-platform.
- Swapping the voice after generation leaves ~100 ms lip offset (README note).
- All demo presenters are AI and labelled as such in the source videos.

## Risk gates
- Flags: none on the radar row. Licence MIT (code + docs); demo media is the maker's own, credited.
- No third-party IP shown in the segments used (styles demos are the maker's own presenters).

## Media plan (official media first, own captures second)
- hook/catch clip: `workbuddy-live-ad.mp4` (official, 9:16)
- montage: `koubo-montage.mp4` — assembled from four official README demo clips
- page scenes: own capture `desktop-full.jpg` with README region cameras
