# THE INNER MACHINE — PRODUCTION STANDARD v3

This is the channel’s enforceable production bar. It is deliberately original to The Inner Machine; the reference repository contributed only general operational lessons.

## Output specifications

- Long-form: 16:9, 1920×1080 or 1280×720, 30 fps, 6–9 minutes initially.
- Shorts: 9:16, 1080×1920, 30 fps, 30–45 seconds.
- Voice: selected Kokoro voice recorded in `reusable/voice_config.json`; model/version/checksum recorded per video.
- Audio: voice clearly dominant; loudness and true peak measured with ffmpeg/ffprobe. No synthetic pad or music is shipped without a logged source/creation record.

## Editorial bar

- One viewer experience and one primary mechanism per episode.
- Hook in the first two sentences; mechanism promise within the first 30 seconds.
- Add a measured opening pause after the first vivid line or unresolved question; a pause is a timing tool, not dead air.
- Three or four chapters, one midpoint re-hook, concise synthesis and a real comment question.
- When a technical section risks feeling abstract, carry a recurring metaphor or visual anchor through it, but never let metaphor replace a clear mechanism diagram.
- Every sentence must do at least one job: create curiosity, evoke a concrete experience, explain mechanism, introduce contrast, answer a question or deliver payoff. Delete filler and repeated claims.

## Voice and delivery bar

- Target approximately 135–150 words per minute for explanatory narration; slower for a key idea, faster only for controlled escalation.
- Each sentence may define `speed`, `pause_before`, `pause_after` and `emphasis` in the voice plan. Pause timings are inserted in audio, not guessed from punctuation alone.
- Emphasis is produced through measured speed/pitch/volume treatment or deliberate wording—not ALL CAPS everywhere.
- Listen to the first 30 seconds and one chapter transition before rendering the full video. Reject fast, flat, clipped or breathless TTS.
- Record actual per-sentence durations and use them for the visual/caption timeline.

## Script bar

- Use a concrete cold open, a clear promise, escalating explanation, a midpoint re-hook, a counterpoint/limit and a satisfying synthesis.
- Prefer specific human moments over abstract introductions. Avoid “in today’s video,” generic motivational language and unsupported certainty.
- Every factual claim has a claim ID in `sources.md` and a confidence label: established, supported, debated or illustrative metaphor.
- No diagnosis, treatment, cure, universal brain claim or sensational mental-health framing.

## Visual bar

- Visual change approximately every 3–5 seconds, but not as empty wallpaper: use a diagram for causal claims, visual metaphor for abstraction and real-world footage for lived context.
- At least one original explanatory diagram per long-form.
- Target 12–18 original landscape base illustrations plus 2–4 diagrams and 3–6 licensed b-roll clips. Fewer assets are acceptable when each shot carries meaning; artificial asset counts are not a quality metric.
- Each Short has its own portrait pool: 4–6 AI illustrations and 2–4 portrait stock clips where appropriate. Never hard-crop landscape media or share the two Shorts’ hero assets.
- No asset from another episode is reused except explicitly marked reusable brand elements.
- Every sentence-level beat must have its own distinct visual asset. Asset reuse within an episode is a validation failure.
- Beat count is selected from the script’s natural sentence structure, not forced to 52; the approved long-form range is 50–65 beats.
- Motion must vary intentionally across the episode: use a planned mix of zoom, pan, rise, settle, reveal, diagram movement, parallax and transitions. Do not cycle one short motion list mechanically.

## Caption and timing bar

- Narration is split into measured sentence/keyword units.
- `caption_schedule.json` contains absolute `start`, `end`, `sentence_id`, `keyword` and `beat_id` values.
- Captions are generated only after measured TTS timing exists; no character-count timing estimates.
- **Kinetic typography is selective emphasis—not captions and not a text layer on every image.** Only high-value beats receive 1–3 meaningful overlay words, timed to the exact spoken phrase. Most beats remain text-free. Use `tools/validate_kinetic.py` and the proven `pipeline/assemble_v2.py` overlay path. A caption schedule alone is not evidence that text is visible; inspect encoded frames.
- **Diffusion Studio is an optional composition pilot.** `tools/diffusion_pilot.py` may emit JSX from a validated beat manifest. It must preserve the same selective-emphasis gate and must pass headless/export and encoded-frame checks before replacing FFmpeg production.

## Packaging bar

- Three title candidates and three materially different thumbnail candidates.
- Thumbnail is a complementary visual diagnosis, 2–4 words, never the full title. Place the text in top-left negative space by default, using a subtle dark scrim/gradient; it must never mask the main face, subject, focal object or explanatory mechanism. Move only when the top-left is not clear.
- Metadata includes a truthful first sentence, chapters, sources, relevant disclaimer, pinned comment, related video/playlist, credits and AI disclosure decision.
- Use tags sparingly; effort goes to title, thumbnail, opening and viewer satisfaction.

## Workspace safety and fail-closed gates

Run `tools/cleanup_workbench.py` before TTS, rendering or assembly. Keep the workspace under 100 MB; delete generated audio/video and render intermediates after the relevant report is captured. If a final video must be preserved, push it to an explicitly configured remote/object store first and verify the remote checksum; never rely on the workspace snapshot for large binaries.

A build does not progress if any validator fails. Final QA must include: project schema, asset manifest/provenance, caption schedule, ffprobe streams/dimensions/fps/SAR, decode spot checks, audio loudness/peak, thumbnail text fit, metadata completeness and Short CTA timing. Outputs are written atomically and only renamed after QA passes.
