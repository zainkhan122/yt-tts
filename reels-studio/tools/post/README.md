# Hypeless Buffer delivery — current operating guide

## Current decisions (owner, 10 Oct 2026)

- **Default finishing step (owner, 15 Oct 2026):** for an approved video, *render passes QA → send to Buffer on scheduled slots* (YouTube/Instagram/Facebook) is the default end of the pipeline. Artifact-only delivery now requires an explicit owner hold for that video.

- One Buffer account/key covers **YouTube Shorts, Instagram Reels and Facebook Reels**. No second key is needed for this scope; TikTok/X are not connected.
- **Facebook is included.** The earlier native-AI-label hold was explicitly removed by the owner. Its caption always discloses AI narration; capability discovery uses a native flag if Buffer later exposes it. Caption disclosure is not claimed equivalent to a native label, and no rollout date is promised.
- Audience: **global English, US-led**. All scheduling calendars use **America/New_York**, with DST-aware UTC conversion. Buffer's existing UI timezone/weekly slots remain unmodified.
- Prefer explicit `mode: customScheduled` + `dueAt`, not `shareNow` or blindly filling the existing queue.
- **Three shorts/day baseline**, scaling with the researched batch up to the owner ceiling of **10/day** (2026-10-12; extended slot grid keeps 150-minute spacing). Separate calendar per platform; the daily mix is editorial (owner 2026-10-11 — no hardcoded 2/2/1 split; strongest researched topics win).
- **Buffer publishing is ACTIVE**, explicitly authorised 2026-10-10. The Claude pilot was confirmed sent on YT/IG/FB. On 2026-10-12 two live runs scheduled 15 posts (five videos x YT/IG/FB) and a second five-video wave followed the same day (10-video ceiling). Remaining held backlog items (tool-muse-01, repo-scm-01, spotlight-papermorph-01) stay held until the owner approves posting. Scheduled is not sent: reconcile before claiming anything is public.

Full researched schedule: `research/publishing/strategy-2026-10-10.md`.

## What happens to a ten-video batch?

Rendering does not publish. The queue pins exact Release asset IDs, sizes/digests and the approved brief hash. After posting approval and fresh fact/copy review:

1. Select eligible platform-specific slots in the next **48 hours**.
2. Respect existing Buffer/manual posts, spacing, expiry, daily caps and the content mix.
3. Keep **at most 8 pending/channel** operationally, below the configured Free-plan cap of 10. Extra videos remain in our backlog, never a bulk dump.
4. **At most 9 creates/run**, at least 3 seconds between API calls; four small cron checks/day replenish the queue.
5. A missing story/category, expired review, disconnected account or full queue is a hold, not permission to publish filler or re-upload an older video.

The three initial slots are a test schedule, not claimed optimal times. Your Buffer API snapshot currently reports Asia/Karachi and many daily slots; we bypass those slots using explicit timestamps. Changing the UI display timezone is useful for manual operation, but is not required for correct UTC delivery.

## Credentials and identities

`BUFFER_API_KEY` is an encrypted GitHub Actions secret. Local recovery file: `~/.config/reels-studio/buffer_token` (600, outside git). Never print/commit it. Fixed Buffer channel IDs and social service IDs are checked before posting; reconnecting a different account must not silently redirect content.

Google OAuth is a **separate** connection for YouTube long uploads AND Shorts backend tags/playlists. Buffer's current YouTube input exposes title/description/hashtags, not backend tags or playlist insertion. The direct worker enriches confirmed sent Shorts without altering their public copy/privacy. See `tools/youtube/README.md`.

## Duplicate protection / receipts

`tracker/publications.json` is authoritative by **video ID + platform**, independent of render/voice revisions.

Verified manual uploads locked against YouTube re-upload:

| Brief | Existing video |
|---|---|
| `repo-removemacai-01` | https://www.youtube.com/shorts/lzXGzOsidCg |
| `tool-muse-01` | https://www.youtube.com/shorts/6OAa4KofxvQ |
| `spotlight-papermorph-01` | https://www.youtube.com/shorts/Mt8Yn9ShBmM |

These locks do not suppress IG/FB. RemoveMacAI still needs an approved Option 3 render/kit before being newly distributed elsewhere; do not use an old voice version merely because it already exists on YouTube.

Flow:

1. Read Buffer account status, pending counts, active posts and recent sent history.
2. Reconcile known IDs, exact immutable asset URLs, matching copy/YouTube titles. Multiple matches are a conflict, not an invitation to create again.
3. Persist `submitting` through GitHub Contents API compare-and-swap **before** calling Buffer.
4. Send one paced request; persist the returned post ID immediately.
5. If a response is lost, find the unique receipt. If uncertain, hold for agent review. Never assume “not found yet” means safe to send again.

Buffer exposes no server idempotency key; we do not promise magical exactly-once delivery. A held post is preferable to a duplicate. A GitHub journal write failure or conflict stops before further provider writes.

## Rate limits / errors

Official published Free-plan quotas: 100 requests/15 min, 250/24 h and 3,000/30 days. The client reads actual `RateLimit` headers, keeps a five-request reserve and honors `Retry-After` rather than assuming the plan never changes.

- Queries: up to four attempts, exponential backoff + jitter for transient failures.
- Create: an explicit 429/rate rejection may be safely retried. A timeout/5xx/unknown mutation result may have succeeded: reconcile first, never blindly recreate.
- Short safe waits: within the job, up to 60 seconds. Longer/daily/monthly limits persist a cooldown; later runs make no Buffer request before it expires.
- Check HTTP status **and** GraphQL errors/typed mutation unions. HTTP 200 alone is not success.
- Fully paginate active/draft/error history; scan recent sent posts for 14 days. Permanent duplicate locks remain beyond that window. Incomplete scans fail closed.
- Permanent input/permission/identity errors stop and report. No silent downgrade to reminder publishing.

| State | Meaning / next action |
|---|---|
| `retry_wait` | Explicit rejection, persist retry time and recheck capacity; bounded attempts. |
| `uncertain` / `submitting` | Reconcile receipt; without a unique match, agent investigates before any repeat. |
| `blocked` / `dead_letter` | Fix input/authorization or review exhausted retries. |
| `delivery_error` | Provider accepted the post but delivery failed. Keep its ID; resolve the existing post, never duplicate it. |
| `approval_required` / `notification_required` | Not automatic publishing; surface it rather than claiming success. |
| `scheduled` / `sending` | Retain media and wait. Not published yet. |
| `sent` / `published_manual` | Confirmed post or verified manual upload; no automatic re-upload. |

Permanent/ambiguous delivery issues fail the Actions job and appear in its summary/artifact. Email delivery depends on GitHub notification settings; no separate email/SMS alert service is claimed.

## Read-only Buffer Insights (pre-production)

`buffer_insights.py` queries paginated `sent` posts for every configured channel, collects per-post `metrics` and
`metricsUpdatedAt`, and stores every Buffer-detected video plus tracked publication records in
`tracker/buffer-insights.json`. It also records platform-by-platform coverage, missing tracked post IDs, metric
freshness, and up to seven changed metric snapshots per post. A complete scan is required; pagination/permission
errors produce no accepted snapshot. The manual Actions workflow is read-only against Buffer and only commits the
analytics JSON and a Markdown report to GitHub. It does not create, edit, schedule, or publish posts.

The Buffer metrics taxonomy keeps `reactions` distinct from Facebook `likes` and keeps `shares` distinct from
`reposts`; percentage values are already in Buffer's 0–100 scale. Metrics are ranked **within** each channel, not
compared as equivalent counts across networks. Views, retention/watch time, engagement, comments, shares, saves,
clicks, follows, and other supported network-specific measures are kept where Buffer exposes them. Metrics refresh
daily and may lag the network by about a day; `metricsUpdatedAt` is recorded per post. Metric correlation does not
identify which creative change caused a result.

## Performance loop — analytics → changes → trending topics

Fetching metrics is only step one. The closed loop that turns them into decisions:

1. **Fetch (daily).** `Buffer Insights (read-only)` runs on a daily cron (05:17 UTC) plus manual dispatch, and commits a fresh `tracker/buffer-insights.json`. The production gate already refuses stale/incomplete snapshots, so every batch starts from current numbers.
2. **Analyse (automatic).** The `Performance (analytics + topic advice)` workflow runs after every successful Insights run (weekly fallback cron). It executes `tools/post/performance.py`, which joins Buffer metrics to briefs (hook, template, niche), queue category and the backlog, then writes `tracker/performance.json` and `research/performance/performance-<date>.md`. Rules: metrics are ranked only **within** a platform (Facebook's primary metric is impressions; YouTube/Instagram use views); posts under 2 days old are listed as *too early* and never judged; winners/losers use mature (≥7-day) videos only; no dimension finding becomes a recommendation below n = 4 judged videos (slots n = 3), and every recommendation cites its n and medians. Correlation is never dressed up as causation — before changing voice or format, inspect the actual winners' hooks, first frames and audio QA.
3. **Act (next batch).** SELECT reads `tracker/performance.json` before scoring topics: follow its `recommendations` (which category/hook-style/slot to prioritise or rework) and start from `topic_advice.top_candidates`. The same workflow refreshes `tools/trend_radar.py` (GitHub/Hugging Face, risk-flagged items excluded), and the advisor re-ranks backlog candidates: base score × category performance (0.8–1.2×), × 0.5 when a candidate overlaps a video already published, risk-flagged candidates blocked outright. Record what was followed or deliberately overridden in the six-stage receipt's `metrics_review.decisions`.
4. **Verify.** The following days' reports show whether the change moved the percentile of the next batch — that before/after comparison is the only honest evidence a change worked.

Post-level metrics require Buffer's **personal API key** / `insightsRead` access. If this read-only workflow gets a
permission error, stop and fix that authorization; do not fall back to mutations or claim that analytics were read.
Before a new video, run or verify **Actions → Buffer Insights (read-only)**, then include the fresh snapshot hash,
all shared-video coverage, findings, and explicit topic/script/voice/visual decisions in the six-stage receipt. The
pre-render gate rejects a missing, incomplete, stale, or channel-uncovered snapshot.

Official metric references: [paginated posts with metrics](https://developers.buffer.com/examples/get-posts-with-metrics.html)
and [metric names/freshness/units](https://developers.buffer.com/guides/post-metrics.html).

## Media / voice / disclosure

- Short media uses stable public HTTPS Pages URLs: `media/<release-asset-id>/<video-id>.mp4`. Never pass expiring redirected Release URLs to Buffer.
- Release downloads follow CDN redirects **without** forwarding GitHub credentials. Check digest, size, seven QA gates and the exact **Option 3 Chatterbox Michael flow** voice audit.
- Preserve every pending/ambiguous/error asset and seven days after completed publication. The 750 MB Pages guard fails rather than evicts a needed file. Releases remain the permanent archive.
- Validate direct public response, MIME, length and MP4 header before scheduling.
- Render release assets are immutable; use a new revision tag for a changed render. Do not delete an asset pinned by a queue.
- No on-screen credit captions were restored. Credits are in post descriptions/captions.
- Instagram uses its native `isAiGenerated` field. Facebook is included with caption disclosure until native support is detected. YouTube disclosure is set according to the content, not guessed from a generic narrator alone.
- Backend tags/playlist enrichment needs Google OAuth. No automatic first/pinned comments or unsupported IG/FB backend fields are claimed. Shorts covers are supported through the YouTube enrichment worker as of 2026-10-11 — agent-reviewed digest required first; see `tools/youtube/README.md`.

## Agent operations

```bash
python3 -m pip install -r tools/post/requirements.txt
python3 -m unittest discover -s tests -v
python3 reels.py post --dry-run
python3 tools/post/queue_ctl.py enqueue <id> --tag renders-YYYY-MM-DD --category tool
# After owner approval and actual fresh source/copy review:
python3 tools/post/queue_ctl.py approve <id> --reviewed-until <ISO-date> --platforms youtube instagram facebook
python3 tools/post/queue_ctl.py enable --confirm OWNER_APPROVED_LIVE_POSTING
python3 reels.py sync -m 'Approve one three-platform pilot'
python3 tools/gh_actions.py dispatch post.yml -i mode=schedule -i video_ids=<id> -i pilot=true
# After due time, reconcile and verify all three actual external posts:
python3 tools/gh_actions.py dispatch post.yml -i mode=reconcile
# Pull latest journal before recording the pilot result.
python3 tools/post/queue_ctl.py pilot-passed <id>
```

A pilot is not complete merely because Buffer accepted a schedule. `pilot-passed` requires every selected platform to be sent with an external URL. Routine scheduling needs both `enabled` and `live_pilot_passed`.

**Kill switch:** cancel in-progress runs, disable both delivery workflows, then set enabled flags false and hold queue entries. Existing Buffer schedules and already armed YouTube schedules continue independently; pause/cancel them at the provider if required. Merely disabling a workflow does not cancel its in-progress run or the provider queue.

Files: `config/publishing.json`, `queue/publish.json`, `tracker/publications.json`, `tools/post/`, `.github/workflows/post.yml`. Budget/pruning tool: `tools/maintenance/storage.py`. Heavy media stays outside source/snapshots; other projects and remote git history are untouched.

Official references: [API limits](https://developers.buffer.com/guides/api-limits.md), [error handling](https://developers.buffer.com/guides/error-handling.md), [scheduling](https://developers.buffer.com/guides/posts-and-scheduling.md), [media hosting](https://developers.buffer.com/guides/hosting-media.md), [YouTube metadata schema](https://developers.buffer.com/types/YoutubePostMetadataInput.md).

The earlier `setup-report.md` / first cloud run are historical evidence of the initial setup (including its now-superseded Facebook hold). Current decisions and latest cloud evidence are in the 10 Oct strategy/expansion records.
