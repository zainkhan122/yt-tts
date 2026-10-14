# Production receipts — render preflight contract

Receipts prove the six production stages and record how the current Buffer Insights snapshot influenced a
candidate. They **do not** grant permission to schedule, post, or create a public release beyond the existing
render policy. Owner approvals and platform-delivery permissions remain separate gates.

## Before filling a receipt

1. Run **Actions → Buffer Insights (read-only)** and wait for a successful run. This performs per-post metric
   queries for every sent video on the configured Buffer channels and commits `tracker/buffer-insights.json`.
   It makes no Buffer mutations. The render gate requires a complete snapshot fetched within 36 hours and at
   least one fresh metric-bearing post per active channel.
2. Discover topics from the current feed/radar/social evidence. Score every selected candidate with the rubric in
   `PIPELINE.md` §2. Add the exact topic title, integer score, and `video_id=<brief-id>` to `topics/backlog.csv`,
   setting its status to `selected` before production.
3. Verify research and dynamic facts, write the brief/script, choose the approved voice, and review the capture
   pack. Do not start the render until the receipt passes.

## Required receipt fields

- `batch_id`: safe filename stem; store as `reels-studio/research/production/receipts/<batch_id>.json`.
- `created_at`: timezone-aware UTC timestamp.
- `buffer_insights`: exact snapshot path plus SHA-256 of its bytes.
- `metrics_review`: current snapshot SHA, `reviewed_video_count` equal to all shared videos in the snapshot,
  sample post IDs, concrete findings, and four explicit decisions: `topic`, `script`, `voice`, `visual`.
- `briefs`: exactly the brief IDs in the planned batch. Each entry pins the exact brief SHA and has exactly
  `discover`, `select`, `research`, `script`, `voice`, and `assets` stage records, all `status: complete`.
- `select`: `selection_status: selected`, exact backlog topic title, six PIPELINE §2 category values, their sum (≥60),
  Buffer post IDs used as evidence, and all hard gates set true. The backlog row score and status must also match.
- `research`: primary HTTPS URLs that also appear in `brief.sources`, claim mapping, timestamps, and a dynamic-fact
  refresh within 24 hours.
- `script`: SHA-256 of ordered spoken lines and a positive word count.
- `voice`: `engine: chatterbox`, `profile: option-3` for English; `qa_thresholds.per_chunk >= 0.92` and
  `qa_thresholds.overall >= 0.95`. These are minimums, not a claim that the actual audio has passed. The render
  pipeline transcribes the generated audio and blocks before video rendering on any QA failure.
- `assets`: matching capture ID, SHA-256 of `manifest.json`, a `{path, sha256}` entry for every file listed in the
  pack manifest, plus `rights_checked` and `approval_constraints_checked` set true.

Useful checks:

```bash
python3 reels-studio/tools/production_gate.py check \
  reels-studio/research/production/receipts/<batch-id>.json <brief-id> [...]
python3 reels-studio/tools/production_gate.py asset-digests <capture-id>
python3 reels-studio/reels.py cloud <brief-id> --receipt \
  reels-studio/research/production/receipts/<batch-id>.json --wait
```

The `render.yml` plan downloads and verifies every referenced capture pack before it reserves an idempotency
fingerprint or starts video-render runners. Do not manually rerun a failed render with the same brief, voice seed,
assets, quality, and renderer. Correct the source or renderer first; exact repeats are refused by
`tracker/render-attempts.json`.
