# deeper-mind/ — standalone animated-video pipeline

> ## ⚠️ SEPARATE SYSTEM — DO NOT MIX WITH `vault/`
> This folder is an **independent, self-contained pipeline**. It is **not** part of,
> and must **not** be merged with, the `vault/` system (or `finance/`) elsewhere in this
> repo. `vault/` was consulted as **reference only**. The two differ deliberately:
>
> | | `deeper-mind/` (this) | `vault/` (reference only) |
> |---|---|---|
> | Tools | `pipeline/produce.py` (single config-driven producer) | `vault/tools/*` (pipeline.py, make_short.py, …) |
> | Voice | **bm_george** (Kokoro, male) | af_heart (Kokoro, female) |
> | Source of truth | `plan/CONTENT_PLAN.md` | `vault/VIDEO_QUEUE.md` |
> | Output | `output/<Title>/` | `vault/video_NNN/` |
>
> Never import across the two, never copy conventions between them, never dedup topics
> against each other. They are parallel and independent.

## What it is
A robust, config-driven producer. One `project.json` in, one titled output folder out:

```
output/<Title>/
  <Title>.mp4                 long-form (1080x1920, verified)
  <Title>.metadata.md         description, chapters, tags, hashtags
  <Title> cover.jpg           thumbnail
  shorts/<Title> hook.mp4     vertical Short (hook beats)   + .metadata.md
  shorts/<Title> payoff.mp4   vertical Short (payoff beats) + .metadata.md
  state.json                  ok | failed (+ error, timestamp)
  produce.log                 timestamped run log
```

## Robustness (what "robust" means here)
- **Self-bootstrapping deps** — installs kokoro-onnx / soundfile / imageio-ffmpeg / pillow, and *verifies* the import; clear fatal if a dep can't install.
- **Self-healing TTS** — `tts.py` auto-downloads the Kokoro int8 model + voices bin to `~/.cache/kokoro` on first use (atomic `.part`→rename), so a full sandbox wipe recovers on its own.
- **Pre-flight** — validates config keys, that every keyframe exists, ffmpeg/font present, and disk space *before* rendering; fails fast with a readable list instead of a cryptic ffmpeg error.
- **Crash-safe** — any failure writes `state.json {status:"failed", error, ts}` and exits non-zero; success writes `{status:"ok", ts}`.
- **Idempotent / resumable** — TTS wavs are cached in `.work/`; re-running skips completed narration.
- **Verified, never ships blind** — checks dimensions, fps, audio codec, and duration on the long-form, and 1080x1920 + audio on each Short; a failed verify aborts.
- **Aspect-safe render** — keyframes are cover-and-cropped to 9:16 (any source aspect works, no stretching).

## Layout
- `pipeline/` — `produce.py` (producer), `tts.py` (Kokoro wrapper), `sample_voices.py` (voice audition), `repo_push.py` (pushes this folder to GitHub).
- `plan/` — `CONTENT_PLAN.md` (single source of truth for the slate) + `video-NN-<slug>/` source (`project.json` + keyframes).
- `handoff/` — `HANDOFF.md` (how to resume / operate).
- `output/` — produced deliverables.

## Run it
```bash
# 1. author a config (copy an existing one and edit title/beats/visuals/meta)
cp -r plan/video-01-where-do-dreams-come-from plan/video-02-<slug>
#    edit plan/video-02-<slug>/project.json  (keep "voice":"bm_george")
#    add keyframes k1.png..kN.png (any aspect; cropped to 9:16)

# 2. produce (auto-installs deps, auto-downloads Kokoro, verifies output)
python3 pipeline/produce.py plan/video-02-<slug>/project.json
#    -> output/<Title>/
```

## What is committed vs regenerable
Everything **except** the `*.mp4` binaries is committed. The videos are large and fully
regenerable from source with one command (`produce.py`), so they are intentionally not
stored in git — keeping the repo lean and the push fast.

## Push this folder to GitHub
```bash
GITHUB_PAT=<token> python3 pipeline/repo_push.py --dry-run   # preview the file list
GITHUB_PAT=<token> python3 pipeline/repo_push.py             # single commit, preserves vault/
```
`repo_push.py` uses the Git Data API (no clone), adds only `deeper-mind/*`, and leaves all
other repo content untouched. The token is read from the environment only — **never** hardcoded
or committed.
