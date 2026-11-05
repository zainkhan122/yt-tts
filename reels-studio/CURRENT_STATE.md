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

## Update 2026-11-05 (later): cloud render succeeded, awaiting owner review
- Capture pack rebuilt (`captures/repo-craft-anything-01`, tar pushed to the capture-packs release).
- Designed covers (no tool media) drawn in `covers/repo-craft-anything-01/draw_designs.py`. Owner picked cover 1 ("CAN AI RECREATE ANY APP?"). `cover-selected.jpg` sha `9fbee12e6aa6` is pinned in the receipt and the cover pack.
- Receipt `research/production/receipts/2026-11-05-shorts-01.json` validated; preflight PASS.
- Cloud render run `42026430184` failed at QA: loudness. Cause: the graphics path muxed `vo.wav` instead of the final mix. Fixed in `f29aea3` (`lib/pipeline.py` uses `assets/mix.wav`).
- Cloud render run `42029040421`: SUCCESS. QA 9/9 in cloud. No public release created (dispatched without `--publish-release`). Artifact `13415623795`, saved to `/home/user/.graphics-work/cloud-42029040421/out/`.
- Local QA on the MP4: PASS (speech visual change 0.835, graphic-only 0.167, motion gap 0.5 s).
- Deliverables for owner: `/home/user/uploads/repo-craft-anything-01/` (video.mp4, cover.jpg, script.md, description.md, seo.md).
- OPEN: the description has only `#shorts`. The owner rule is five niche hashtags. Fix in the plan, then re-approve the topic and rebuild the receipt before queueing.
- NOT DONE (owner gate): queue, approve, Buffer schedule. Nothing is queued or scheduled.

## 2026-11-05 update: repo-craft-anything-01 scheduled (owner go)

- Hashtags: brief builder now takes post hashtags from the plan's SEO description (`#Shorts #CraftAnything #OpenSource #RustLang #AIAgents`).
- Viewer panel: FAIL on the first render (near-blank frame at 12.9 s; real-media rule vs no-tool-media rule). Owner override recorded in `research/production/viewer-panel-repo-craft-anything-01.md`. Findings stay on file.
- Render attempts: 42038109244 (hashtag fix, no release), 42045217486 and 42047256857 (voice_seed 1 and 2 failed TTS alignment, 0% matched), 42048880432 (`voice_seed` 0 explicit, publish-release, QA passed, release `renders-2026-11-05`).
- Queue: enqueued and approved (`reviewed-until` 2026-11-12, platforms youtube/instagram/facebook). Cover approved, sha `9fbee12e6aa6`.
- Buffer: dry-run success, verify success, schedule success. Due times (UTC): YouTube 2026-11-05 18:20, Instagram 21:18, Facebook 22:11 (PKT +5: 23:20, 02:18, 03:11 on 6 Nov).
- Open: 12.9 s near-blank frame is still in the video. Real-media rule is waived for this batch only. Decide before the next batch.
