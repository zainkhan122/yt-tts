# Hypeless — current operational state

Generated: 2026-10-10T22:10:00.455279+00:00 · source commit: `c151f831b7d4`

| System | Recorded state |
|---|---|
| Buffer delivery | enabled=True; verified pilot=True; 3/day in America/New_York |
| Buffer queue | {'approved': 3, 'held': 8} |
| Platform receipts | {'sent': 8, 'scheduled': 1, 'published_manual': 3} |
| YouTube metadata | enabled=True; completed receipts=3 |
| Long-form uploads | pilot passed=False; queued=0 |
| OPTIONAL producer/critic | production=False; publishing=False; qualification=unqualified; lifecycle=paused_by_owner |

## Current owner decision
Interactive Arena agent leads research, scripts, asset selection, editing and QA. Existing deterministic rendering and approved posting tools are retained.
The optional producer/critic is PAUSED BY OWNER / UNQUALIFIED. Its Actions workflows are disabled, and its inference client fails closed while paused.

## Optional pilot model lock (historical / inactive)

- producer: `nvidia/nemotron-3-ultra-550b-a55b:free`
- critic: `google/gemma-4-31b-it:free`
- audio_critic: `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`

**Recorded Google grant expiry:** 2026-10-17T13:42:00+00:00

## Resume rules
- The interactive Arena agent remains the main creative brain. The optional producer/critic is paused by owner instruction; do not restart it without explicit approval.
- A missing local OpenRouter key is expected when it is stored ONLY in Actions Secrets; do not ask for it again without checking secret metadata.
- Never re-upload a video with an existing platform receipt/reservation.
- The optional producer/critic cannot publish or activate itself. Model scores are not parity certification.
- A fresh conversation can restore operational state from git, not private chat reasoning. A completely new workspace still needs authorized GitHub access for writes; existing cloud jobs keep their encrypted secrets.

## Start here
1. Read `RESUME.md` and `agent/ACCEPTANCE.md`.
2. Read the latest pilot report; inspect existing Actions runs before starting another.
3. Read `tracker/publications.json` and `tracker/youtube-publications.json` before any provider operation.
4. Never infer missing results. Preserve unknown/uncertain receipts and resolve them first.

Receipt counts are recorded journal state, not fresh live-provider verification. Old local delivery MP4/ZIP copies were cleaned after archive verification; use the immutable Release links instead of regenerating or re-uploading videos.
