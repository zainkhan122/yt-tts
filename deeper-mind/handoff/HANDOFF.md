# HANDOFF — deeper-mind/ standalone pipeline

Resume here. This folder is a **self-contained system, separate from `vault/`** (see
`../README.md` — vault/ is reference only, never mixed).

## Locked decisions
- **Voice: `bm_george`** (Kokoro, male), set per video in `project.json` `"voice"`.
  Independent of `vault/`'s af_heart — the two systems do not share a voice.
- Lane: animated depth-psychology. Cadence: 1 long-form (7–10 min)/wk + 4 Shorts/wk.
- Visual: flat 2D storybook motion-comic, 9:16. See `../plan/CONTENT_PLAN.md`.

## Folder map (all under deeper-mind/)
- `pipeline/produce.py` — one-shot producer (config → verified output folder).
- `pipeline/tts.py` — Kokoro wrapper; auto-downloads model to `~/.cache/kokoro`.
- `pipeline/sample_voices.py` — renders the 28-voice Kokoro audition set.
- `pipeline/repo_push.py` — pushes this folder to GitHub (Git Data API, single commit).
- `plan/CONTENT_PLAN.md` — **single source of truth** for the 3-month slate.
- `plan/video-NN-<slug>/` — per-video source: `project.json` + keyframes `k1..kN.png`.
- `output/<Title>/` — deliverables (mp4 + metadata + cover + shorts/ + state.json + produce.log).

## How to produce a video
1. `cp -r plan/video-01-where-do-dreams-come-from plan/video-02-<slug>`
2. Edit `project.json`: `title`, each beat's `narration`/`caption`/`motion`, and replace
   keyframes `k1..kN.png` (any aspect; cropped to 9:16). Keep `"voice":"bm_george"`.
3. `python3 pipeline/produce.py plan/video-02-<slug>/project.json`
4. Output → `output/<Title>/`, auto-verified (1080p long-form + 1080x1920 Shorts).

`produce.py` self-installs deps, self-heals the Kokoro model, pre-flights the config,
is idempotent (cached TTS in `.work/`), and writes `state.json` ok/failed.

## Repo
- Repo: **`zainkhan122/yt-tts`**, branch `main` (PUBLIC). This folder lives at `deeper-mind/`.
- Push: `GITHUB_PAT=<token> python3 pipeline/repo_push.py` (single commit, adds only
  `deeper-mind/*`, preserves vault/). `--dry-run` previews.
- Committed: code + plan + handoff + keyframes + metadata + cover + state. **Not** committed:
  `*.mp4` (large, regenerable via `produce.py`).

## Security
- The GitHub PAT is used in-memory only (env `GITHUB_PAT`, or `/tmp/pat` outside the
  workspace). It is **never** hardcoded, written to the workspace, or committed. If access
  is lost, stop and ask the user to re-paste it.
