# Current state — 2026-11-05

Authoritative for the present. Older state lives in the history of this file and in `HANDOFF-2026-10-26.md` (superseded).

| Area | State |
|---|---|
| Repo head | `main` = `6d0e3b2` (graphics renderer sync). |
| Renderer | `graphics` (new) and `hyperframes` (existing) are both live; the brief field picks one. |
| Batch `repo-craft-anything-01` | Brief set to `renderer: graphics`. NOT dispatched. Receipt stale. Capture and cover packs missing from `main`. Cover needs owner re-approval. |
| Schedule | Nothing scheduled, queued or approved for this batch. |
| Buffer | Owner route "pipeline" approved 5 Nov, but blocked by the items above. |
| Producer/critic (optional) | PAUSED BY OWNER / UNQUALIFIED. Its `agent-*` workflows are disabled. Do not restart without explicit approval. |
| Tests | graphics 28 pass; gates 6 pass; pipeline 8 pass (local, repo copy). |

## Owner decisions in force
- Topics approved per short. Plan edits need re-approval.
- Cloud render on GitHub Actions only.
- No publish, queue or schedule without explicit instruction.
- Varied animation types; animation timed to the voice; highest visual quality.
- Faceless; five hashtags; visual-change gate 75%.

## Resume rules
- Read `HANDOFF-2026-11-05.md` first.
- Check receipts, captures and covers on `main` before any dispatch. Use the GitHub API, not the shallow clone.
- Do not re-upload or re-render anything with an existing platform receipt or reservation.
- Do not write secrets into files or git config.
