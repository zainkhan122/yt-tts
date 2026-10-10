# Delivery expansion — verified 10 October 2026

## Completed
- Owner's Facebook hold removed; all three Buffer channels are eligible. Caption disclosure retained; no native-label compliance claim.
- US-led global audience calendars: America/New_York, separate weekday/weekend windows, explicit UTC timestamps. Existing Buffer UI settings preserved.
- Three shorts/day baseline, optional 4–5; two-day lookahead, eight pending/channel operational ceiling, duplicate/capacity/rate-limit guards.
- Direct YouTube long-form uploader and Shorts tags/playlist enrichment implemented, with encrypted resumable checkpoints, private-first stages and explicit publication receipts.
- Long-form weekly plan: Tuesday repo, Friday news, Sunday tools. One upload/run; quota/spacing/expiry controls.
- Thumbnail generator verified at 250px: the smoke-test headline had 28.32px glyph heights, above the 16px minimum. Actual episode thumbnails still require visual review.
- 110 safety tests passed locally and in the final YouTube cloud run; the preceding Buffer cloud run passed its 109-test suite and authenticated dry-run.
- Source-budget checks, archive-verified capture pruning, immutable render assets and parallel Release-creation handling installed.

## Cloud evidence
- Buffer: https://github.com/zainkhan122/yt-tts/actions/runs/38044990215 — success; 9 proposed rows across YT/IG/FB, ZERO created posts, one Buffer read query.
- Final YouTube workflow: https://github.com/zainkhan122/yt-tts/actions/runs/38045438696 — success; OAuth absent, ZERO Google requests, no uploads.
- Initial YouTube workflow: https://github.com/zainkhan122/yt-tts/actions/runs/38045053335 — success.
- Stable callback https://zainkhan122.github.io/yt-tts/oauth/callback/ returns direct HTTP 200.
- All six hosted short MP4s rechecked: direct HTTPS, correct MIME/size/header, approved Option 3 QA.

## Storage
- Verified and removed 36 local Muse capture copies: 28,548,011 bytes reclaimed; Release archive preserved.
- Snapshot-relevant workspace: 15.93 MB / approximately 128 MB; 1062 files.
- Tracked studio/workflow source: 5.01 MB; zero tracked video files; source budget 20 MB.
- The existing repository as a whole reports roughly 7.45 GiB including unrelated projects. Those projects and remote git history were NOT rewritten or deleted.

## Explicitly pending
- Google OAuth connection (owner selected 'not yet'). `YOUTUBE_STATE_KEY` is securely provisioned; `YOUTUBE_OAUTH_JSON` does not exist yet.
- Real private/public YouTube pilots and actual Shorts metadata enrichment. Unit/mock tests are not proof of a live upload.
- Both live switches remain OFF; no Buffer drafts/schedules/posts or YouTube videos were created during this setup.
- No new long episodes have been researched/rendered/uploaded. The uploader and production contract are built; a dedicated long-form render template/autonomous daily research engine is not claimed complete.

Next account step: `google-connection.md`. Recommended timing/cadence and rationale: `strategy-2026-10-10.md`.
