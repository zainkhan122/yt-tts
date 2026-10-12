# Resume Hypeless safely — read this before doing work

## Latest owner decision — 2026-10-11

**The interactive Arena agent remains the main brain** for research, scripts, asset selection, editing and QA. The optional producer/critic is **PAUSED BY OWNER and NOT QUALIFIED FOR ACTIVATION**. All five `agent-*` Actions workflows are disabled, and the inference client fails before reading a key or making a request while the pause flag is set.

Do not retry experiments merely because quota resets or a checkpoint exists. Resuming evaluation requires a new explicit owner request; activation would still require qualification and separate approval. Existing deterministic rendering, approved Buffer delivery and YouTube metadata tools remain unchanged.

The old local five-video ZIP and Mosa preview were removed only after all ten archived MP4/kit files were verified. Original masters, post kits and source captures remain in GitHub Releases. See `research/maintenance/2026-10-11-deliverable-cleanup.json`; use the archived files, not a re-upload or fresh render.

## Current batch — 2026-10-12

Owner instruction: five videos for today, scheduled, with the daily mix **no longer hardcoded** (no fixed 2 tools /
2 news / 1 repo) and topics picked by findings. Done: the mix rule now lives only in config
(`required_daily_categories: []` and ceiling `max_videos_per_day: 10` since 2026-10-12 — the old 5/day cap is gone incl. all three hardcoded clamps; commits `ee1fd2f`/hardening), and the five topics came out of a
scored shortlist (`research/ideas/2026-10-12-shortlist.md`) — GPT-6.1 Astra's cancellation, Qwen3.8-27B on one RTX
3090, ds4/DwarfStar local DeepSeek 4, Nano Banana 2.1 pricing, and OpenMontage. All five rendered green on cloud run
**38216765324** → Release `renders-2026-10-12` (10 assets; QA 7/7 each). Scheduling: two live runs (**38220006074**
3 videos / 9 posts, **38220249522** 2 videos / 6 posts) created all **15** YT/IG/FB slots — see the slot table in
`research/maintenance/2026-10-12-batch.json`. **Scheduled is not sent**: reconcile (`post.yml mode=reconcile`) before
claiming anything is public. Covers: all five extracted, visually reviewed and approved (`cover_sha256` in
`queue/publish.json`); the enrichment worker applies them as Shorts go live. Full receipt:
`research/maintenance/2026-10-12-batch.json`.

## Previous batch — 2026-10-11

Five Oct-10 productions (news-haiku-55-01, news-gemini-agent-01, tool-mosa-01, tool-pomelli-01, repo-whistle-01) were
scheduled today across YT/IG/FB by paced Buffer runs under the `hypeless-publishing` concurrency group (see
`tracker/publications.json` receipts and the Actions runs). Reconcile before assuming anything is public — scheduled is
not sent. All five carry agent-reviewed Shorts covers (`cover_sha256` in the queue); the enrichment worker applies and
confirms them as each Short goes live. Google consent RESOLVED 2026-10-11: app moved to **In production**, one fresh consent minted an indefinite grant (no `refresh_token_expires_at`), live-verified via enrichment run 38116539585 (`oauth_connected: true`). No renewal deadline remains — the old 2026-10-17 expiry is obsolete. Guardrails: keep using the token (crons do, well under the 6-month limit), do not re-consent recreationally (50-token cap), never delete the Cloud project/client, and never recreate the client JSON. If access is ever deliberately revoked, re-consent with `tools/youtube/oauth_handoff.py` — playbook: `research/publishing/google-consent-runbook.md`.

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
# Cheap re-entry: build the ≤8 KB session context pack and read it first
# (replaces reading the whole doc set; see CONTEXT-PROTOCOL.md)
python3 tools/context/ctxpack.py --write && cat .context/PACK.md
# Authoritative operational status (the pack is generated from the same source):
python3 tools/maintenance/resume_status.py
# Local safety suite deps — install from the pinned requirements, never ad hoc:
python3 -m pip install -q -r tools/youtube/requirements.txt -r tools/post/requirements.txt pytest
```

Keep the conversation small: retrieve with `tools/context/ctxgrep.py` instead of
opening full files (never open `tracker/`/`queue/` JSONs whole), and run noisy
commands through `tools/context/quiet.py`. Rules: `CONTEXT-PROTOCOL.md`.

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
| `tools/context/` | Bounded-context session tooling: context-pack builder, capped retrieval, quiet command runner (protocol: `CONTEXT-PROTOCOL.md`) |
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
- Daily mix is **not hardcoded** (owner 2026-10-11): the batch follows the researched ranking; pacing limits (ceiling **10/day** since 2026-10-12, 150-minute spacing, queue limits) still apply. Do not fill gaps with stale or invented stories.
- Scheduled is not sent. OAuth configured is not verified. Model self-approval is not qualification.

## Storage

Snapshot budget is approximately 128 MB / 10,000 files; warning at 100 MB. Do not save new heavy baselines/candidates under `/home/user` when the existing delivery ZIP already consumes space. Use runner scratch or `/var/tmp`, retain small evidence/state, and verify archives before pruning. Do not delete unique user data or pending media.

## Current blocked critic / immutable archive

Latest inspected continuation: `38087458049` (three explicit free-provider 429 responses; no render). Full checkpoint reference: `research/pilots/free-p5/full-checkpoint-archive.json`. Restore was tested byte-for-byte across 156 files; source/call state and hashes remain intact.

This checkpoint is retained for historical recovery only. **Do not execute a continuation now.** Any future owner-approved reevaluation must inspect the recorded configuration and pause decision; the old frozen configuration cannot silently override the current owner pause.

This is not permission to retry now or repeatedly hammer a limited endpoint. Inspect `research/pilots/PILOT_REPORT.md` and the latest Actions runs first. No automatic cron, fallback or promotion exists. The audio specialist is also unproven under $0 balance: plain-JSON audio was rejected with a minimum-balance requirement; do not fund the account or relax limits without the owner.
