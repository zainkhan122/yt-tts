# Multi-mode visual production: review-only experiment

## Status: acceptance not complete

An integrated review video was rendered, but **no human has reviewed its full audiovisual playback**, mode selection was hand-directed, and several PhoneBox actions could not be verified. Do not publish or schedule it. The available screen recording is a public **demo with sample data**, not a real physical phone or computer connection.

## Architecture audit and changes

Existing semantic/planner contracts and the existing provider registry/AssetStore remain unchanged; the existing layer renderer and FFmpeg helper are reused. Prior browser capture tools supported screenshots but did not produce independently verified action receipts. The OpenRouter pilot remains owner-paused. No authorized repository image/video generation adapter was established; the image generation below occurred through Arena's interactive host tool, not a repository API.

- `graphics/production/screen_demo.py`: opt-in Playwright recording for explicitly allowed HTTPS hosts, with click/fill/drag/navigation interfaces, selector-based before/after screenshot and DOM-attribute verification, action timing relative to page ready and cursor coordinates. Only the click route below was executed and verified against the live demo; fill, drag and navigation have not been validated against a real application. A recorded browser interaction is not proof that a real external device or media player changed. It does not record the OS cursor itself or a continuous pointer trace. URL host check is not a complete network isolation/security control.
- `graphics/production/production_modes.py`: explicit capability/status and fallback selection, beat-level mode intent and verification checklist. This is an explicit callable interface; it is **not wired to automatic semantic-planner inference**, and its capability flags are caller declarations, not independent proof.
- `graphics/production/layer_renderer.py`: optional native 1080x1920 compositing (`native=True`) rather than compositing at 540x960 and enlarging; default legacy mode remains unchanged. Source screenshots and video are still lower resolution than the output, so native compositing does not create detail absent from those sources.
- `graphics/production/test_production_modes.py` and `graphics/production/test_layer_renderer.py`: selection, fallback, verification and native compositor tests. Unit tests use synthetic assets and do not establish provider capability.
- `graphics/production/multimode_demo/build_integrated.py`: manually directed review edit using existing verified timing; `mode-plan.json` and `timeline.json` record choices and events. `integrated-review.mp4`, `contact.jpg`, `motion-graphics-mode.mp4`, and title/diagram PNGs are generated review assets.
- `graphics/production/phonebox_live/recording.webm`, `00-before.png`, `00-after.png`, `receipt.json`: actual recording and screenshots of a Playwright click in the public PhoneBox demo. Receipt documents the target cursor coordinate, time relative to page-ready, and observed DOM class change from playing to not playing. That is a real demo UI state change using made-up data, not proof of real music playback or attached hardware. `playback-demo.mp4` is a crop of this recording.
- `graphics/production/multimode_art/phone-desk.png`: actual image produced via Arena's interactive image tool, inspected and imported manually. It is an AI-generated still, not video, a real photograph or a PhoneBox capture. Image-to-video was not available/verified; no external API was invented or used.

## Beat/mode and evidence

| Beat | Source/mode | What is actually observed | Limitations |
|---|---|---|---|
| Intro | AI visual / generated still | Generic phone/laptop scene, AI-labelled; image scales | No generated object motion or image-to-video |
| Music | Screen demo / public live demo recording | Play/Pause DOM class and icon changed after real Playwright click | Sample-data simulation; not real external music playback |
| System | Existing demo screen capture | CPU/GPU/memory/network screenshot moves into view | Static screenshot; no live statistics verified |
| Editor | Programmatic / image layers | Cursor and widget move over a screenshot | Explicitly labelled illustrative drag, not a genuine app drag |
| USB / Wi-Fi | Programmatic diagram | Packets move along drawn lines synchronized near spoken words | Both connections are illustrative; no actual USB cable, Wi-Fi pairing or status was tested |
| Agent / permissions | Programmatic diagram | Drawn phone and computer, and text that features depend on setup and permissions | No actual two running processes or distinct OS permission states were captured |

`phonebox_live/receipt.json` verifies only the observed demo class change. The motion-graphics mode has actual layer-object movement; it does not cover the user's complete requested charts/timelines/kinetic-typography library. Screen capture supports real clicks in the demo. AI image mode is only manual interactive image generation/import, not an authorized repository provider adapter or independently verified image-to-video.

## Media and review

`integrated-review.mp4`: 1080x1920 native-composited H.264, 24 fps, 23.04 s, AAC mono. It uses the existing 0.97x-paced Chatterbox house voice (23.0349 s), prior real word alignment and original narration. Full FFmpeg video/audio decode succeeded. Sixteen sampled frames, including all beat changes and playback state change, were inspected by the producing agent (`contact.jpg`); no complete independent or human audio/video review occurred. Text and UI visibility remain questionable on a phone, transitions are cuts, and some lower-resolution source screenshots remain small. Safe-area and collision analysis was not executed. No dedicated frame-zero cover or voiced house outro is present; this is not a production Short.

Independent media: `phonebox_live/recording.webm` (screen demo), `multimode_art/phone-desk.png` (AI-generated still), `motion-graphics-mode.mp4` (programmatic connection diagram clip). The integrated review contains all three types, but this does not establish independent acceptance for an AI video provider or full semantic mode selection.

## Reproduction / tests

From `reels-studio` with Playwright/Chromium system libraries, Pillow and imageio-ffmpeg installed:

```
python3 -m graphics.production.multimode_demo.build_integrated
python3 -m pytest -q -rs graphics/production/test_production_modes.py graphics/production/test_layer_renderer.py graphics/production/test_automated_planner.py tests/test_visual_execution.py tests/test_production_alignment_semantic.py tests/test_beat_production.py graphics/tests tests/test_voice_handoff.py
```

105 tests passed. A separate Playwright capture ran against the public demo; the live site may change. The playback clip was cropped from the recorded browser video at 2.2 s for 2.3 s with FFmpeg. No mock recording was called real. Battery fixture SHA-256 remains `088f77d8e8778d60382ad908e796cf1c26f46cc4a089e6c1b0dd950f3ffa9385`. No publishing or provider-policy changes were made.
