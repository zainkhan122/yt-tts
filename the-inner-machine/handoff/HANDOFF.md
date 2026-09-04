# The Inner Machine — handoff

**Updated:** 2026-08-31  
**Current milestone:** production system v1 hardened; three-month content plan v1 created; Video 01 brief/script/sources prepared; 16 landscape base images and 4 diagrams generated; 6 related Pexels landscape photos downloaded; 52-beat storyboard created and validation passed; measured Kokoro TTS and caption schedule generated; landscape render completed and ffprobe QA passed; local video/audio/render intermediates purged after the workspace budget warning.

## Done

- Strategy separated from the reference channel and rewritten as `STRATEGY.md` v2.
- `SYSTEM.md` added as the operating system and gate sequence.
- Long-form project corrected to 1920×1080 landscape at 30 fps.
- Kokoro `voices-v1.0.bin` downloaded to `reusable/` and checksum recorded in `reusable/voice_config.json`.
- `tools/validate_project.py` added and wired into `pipeline/produce.py` before rendering.
- `tools/validate_storyboard.py` added; it passed with 52 beats, 26 assets, no consecutive reuse, no unused manifest assets and no asset reuse; every sentence beat must have a distinct asset.
- `tools/qa_video.py` added for machine-readable ffprobe final QA.
- Video 01 asset manifest contains 16 AI landscape bases, 4 explanatory diagrams and 6 related Pexels landscape photos.

## Important state

Video 01 is ready for the next gate, not for rendering yet. Pexels video search returned HTTP 403 for the supplied key, so six related Pexels photos were used as supplemental stock. The photos can be animated with purposeful pans/parallax; do not describe them as video footage. Do not begin TTS until the voice-plan timing implementation and final storyboard review are complete.

## Next session

The rendered binary was regenerated at 1280x720, downloaded by the user, then purged. Three thumbnail options and the metadata package are ready; option A was revised with top-left negative-space text and the non-obstruction rule is now enforced system-wide. Short A and Short B have been rendered with 8 independent native portrait images, appended CTA narration and portrait QA passed.

## Required build order

brief/research → script → unique assets and manifests → storyboard validation → selective kinetic emphasis gate → measured TTS → `assemble_v2.py` render → encoded-frame inspection → final QA → thumbnails/metadata → native-vertical Shorts → publish package.

**Locked typography rule:** Kinetic typography is selective emphasis—not captions and not a text layer on every image. Only a small set of high-value beats receives 1–3 meaningful words; all other beats remain text-free. `tools/validate_kinetic.py` is a required hard gate.
