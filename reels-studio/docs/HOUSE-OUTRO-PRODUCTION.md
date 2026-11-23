# House outro in Short production

Reference: the delivered GTA6 Clipper and MoneyPrinterTurbo Shorts end with the `YOUR CALL` house card, Hypeless logo and handle, pink Follow button, a topic-specific COMMENT keyword, cursor press, voice CTA and narration-aligned house captions. The visual component alone is not the complete outro. Do not shorten it to fit an arbitrary duration gate or append it silently.

For the graphics stage renderer, use its endcard scene and the shared `graphics/outro.js` + `graphics/templates/shared.js` contract with the CTA in the script. Confirm the voiced CTA, synchronized word captions, cursor and full outro in the finished MP4.

For custom/off-pipeline renders, generate the CTA in the established Chatterbox Option-3 house voice and obtain aligned word timings via `tools/one_go_review.py`; then use `tools/append_house_outro.py` with the exact body duration, WAV, timings, keyword and input/output files. The body remains the approved content; the CTA is additional. Example syntax is in that tool's help. The tool uses the shared card, caption and brand assets. Always inspect the finished MP4 and audio, run production QA against an updated full-length manifest, and repin final MP4, cover and review before any scheduling.

This is a production instruction and shared assembly tool, not yet a universal automated ship gate. Existing custom renderers can bypass it. A future hard gate must cover all render paths and validate the actual finished video and audio, without retroactively breaking previously approved schedules.
