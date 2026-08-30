# HANDOFF — The Inner Machine (resume here)

Read `../brand/setup.md` first (authoritative strategy/SOP). This folder is **independent of the
reference channel** (`vault/` "The Deeper Mind") — technique-only reference, never copied.

## Locked / decisions
- **Channel:** The Inner Machine · handle @TheInnerMachine (verify at launch).
- **Voice:** Kokoro, own choice — demo `bm_george`, confirm before launch (audition in `voices/`).
- **Brand:** graphite/steel/copper/cyan; logo+banner in `../brand/`.
- **Strategy:** mechanism explainers (Machinery / Behavior / Self / Glitches) — NOT Jungian.

## Folder map
- `../brand/` — logo, banner, setup.md (strategy/SOP), make_brand.py.
- `../pipeline/` — produce.py (producer), tts.py, sample_voices.py, repo_push.py.
- `../plan/video-NN-<slug>/` — per-video source.
- `../output/<Title>/` — deliverables.

## Produce a video
1. `cp -r ../plan/video-01-… ../plan/video-02-<slug>`; edit project.json + keyframes.
2. `python3 ../pipeline/produce.py ../plan/video-02-<slug>/project.json`
3. `state.json` must read `ok` before upload.

## Repo
- Repo `zainkhan122/yt-tts` branch `main`. This channel lives under `the-inner-machine/`.
- Push: `GITHUB_PAT=<token> python3 ../pipeline/repo_push.py` (single commit; preserves vault/).
  ⚠️ The repo still has a misnamed `deeper-mind/` from a bad push — remove it and push this
  folder instead (needs the PAT re-pasted).
- Committed: code + brand + plan + metadata + state. Not `*.mp4` (regenerable).

## Security
- PAT from env only; never hardcoded/committed. If lost, stop and re-ask.
