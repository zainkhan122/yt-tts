# Resume Hypeless safely — read this before doing work

## Authority / boundaries

SSOT: **https://github.com/zainkhan122/yt-tts**, folders **`reels-studio/` and `.github/workflows/` only**. Do not touch another project or rewrite shared history. `CURRENT_STATE.md` is a sanitized, dated snapshot; live config, queues, journals and Actions receipts are authoritative if newer.

**Optional agent status:** a non-publishing comparison lab, not an activated daily content engine. The owner permits only free OpenRouter variants and limited provider training on public sources/owned pilot drafts. No secrets/private account data in prompts. No paid or automatic model/provider fallback. No automatic promotion based on model scores.

## First actions in a restored workspace

```bash
# The workspace snapshot may intentionally omit .git/config. Restore its public
# partial-clone/promisor and author settings; never fetch the multi-GB other projects.
cd ~/yt-tts/reels-studio
# Only if .git/config is absent:
cp setup/git-config.template ../.git/config
# Inspect before changing anything:
git status --short
python3 tools/maintenance/resume_status.py
```

If clean, fetch sparse history with `git fetch --filter=blob:none --deepen=24 origin main` and fast-forward. If commits diverged or a rebase is active, inspect it; **do not force-push/reset blindly**. Read newer upstream work before reimplementing it. A cloud publisher can legitimately have committed new receipt states while the local agent was idle.

A completely blank workspace can restore the public project via `bootstrap.sh`; use lightweight posting/pilot requirements for control work rather than installing the full TTS stack locally. Heavy rendering belongs in GitHub Actions.

## What each directory owns

| Path | Responsibility |
|---|---|
| `config/` | Channel/voice/scheduling policy; optional-agent model lock and OFF switches |
| `agent/` | Versioned producer/critic instructions, schemas, frozen cases, acceptance contract |
| `briefs/` | Reviewed human-guided production inputs; shadow candidates are not promoted here automatically |
| `topics/`, `research/` | Source registry, evidence, studies, dated experiments and outcomes |
| `tools/agent/` | Sandboxed public research, bounded model calls, hard gates, shadow rendering/comparison |
| `tools/post/` | Existing deterministic Buffer delivery and duplicate journal handling |
| `tools/youtube/` | Direct long uploads, OAuth, Shorts tags/playlists, encrypted resumable state |
| `tracker/` | Durable provider receipts and sanitized operational state |
| `queue/` | Explicit publication approvals; never infer approval from a completed render |
| `templates/`, `brand/`, `lib/` | Controlled rendering and the approved Option 3 voice pipeline |
| `tools/maintenance/` | Budget audit, archive-verified pruning and read-only resume status |
| `.github/workflows/` | Cloud workers, permissions, concurrency and manual/cron entry points |

## Credentials — NEVER echo or commit

- Private local vault: `~/.config/reels-studio/`, directory mode **700**, files **600**.
- GitHub PAT, Buffer key, Google client/refresh credentials and upload-state key may be in that vault. OpenRouter may exist **only** as encrypted Actions secret `OPENROUTER_API_KEY`; local absence is not a reason to request it again.
- Actions secrets: `BUFFER_API_KEY`, `YOUTUBE_OAUTH_JSON`, `YOUTUBE_STATE_KEY`, `OPENROUTER_API_KEY`.
- Model prompts must not contain vault files, environment dumps, bearer headers, signed upload URLs, private customer data or publishing credentials.
- Google OAuth uses the stable Pages **file-handoff** callback. Do not revive an expired `e2b.app` OAuth URL. Client JSON alone is not authorization; changing app publishing status does not prove the old token grant was extended.
- GitHub encrypted secret values cannot be exported by the ordinary API. A brand-new environment needs authorized GitHub access for writes; do not promise authentication magically transfers to a new conversation. Existing cloud jobs retain their own encrypted secrets independently of the chat.

## Before re-running a pilot

1. Inspect current `config/agent-pilot.json` and model-selection revision.
2. Read `agent/ACCEPTANCE.md`, the latest run artifacts/report, and checkpoint/cost receipts.
3. Check the Actions API for in-progress jobs; **do not duplicate them**.
4. Use a fresh pilot ID after an inspected interruption or a material prompt/model revision. Do not silently replay lost inference requests.
5. Source/auth/protocol failures are not quality passes. Unit tests and tiny model probes are not video-quality evidence.
6. Candidate MP4s stay in quarantined Actions artifacts; no production queue insertion, Pages deployment or social post from this lab.
7. Save sanitized results, failure reasons, model/provider/usage receipts, source/asset hashes and exact next actions in git. Heavy media stays outside the saved workspace or in approved archives.

## Publishing / voice invariants

- Preserve all existing per-video/per-platform receipts, including the three manual YouTube duplicate locks.
- Facebook remains included per the owner's explicit instruction; do not restore the old native-label hold. Caption disclosure is not claimed to set a native flag.
- Narration: **Option 3, Chatterbox cloning pinned Michael reference, exag 0.7 / cfg 0.4 / continuous flow**. Never fall back to raw Kokoro for final media.
- No on-screen credit captions. Attribution and access/pricing caveats belong in post copy.
- Max one repo Short/day, with tools and news represented. Do not fill gaps with stale or invented stories.
- Scheduled is not sent. OAuth configured is not verified. Model self-approval is not qualification.

## Storage

Snapshot budget is approximately 128 MB / 10,000 files; warning at 100 MB. Do not save new heavy baselines/candidates under `/home/user` when the existing delivery ZIP already consumes space. Use runner scratch or `/var/tmp`, retain small evidence/state, and verify archives before pruning. Do not delete unique user data or pending media.

## Current blocked critic / immutable archive

Latest inspected continuation: `38087458049` (three explicit free-provider 429 responses; no render). Full checkpoint reference: `research/pilots/free-p5/full-checkpoint-archive.json`. Restore was tested byte-for-byte across 156 files; source/call state and hashes remain intact.

After confirming the provider is available and policy/config is unchanged, an explicit continuation can use:

```bash
python3 tools/gh_actions.py dispatch agent-resume-critic.yml -i checkpoint_source=archived-free-p5 -i source_run=38087458049 -i source_artifact=resumed-pilot-evidence -i case_id=news-gemini-agent-01
```

This is not permission to retry now or repeatedly hammer a limited endpoint. Inspect `research/pilots/PILOT_REPORT.md` and the latest Actions runs first. No automatic cron, fallback or promotion exists. The audio specialist is also unproven under $0 balance: plain-JSON audio was rejected with a minimum-balance requirement; do not fund the account or relax limits without the owner.
