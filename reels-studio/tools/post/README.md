# Hypeless delivery — Buffer + GitHub Actions

## Current state (2026-10-10)

**Connected:** one Buffer account, with YouTube, Instagram and a Facebook Page. A second key/account is **not** needed for these three platforms. `BUFFER_API_KEY` is an encrypted repository Actions secret, not source code. The local recovery copy is outside git at `~/.config/reels-studio/buffer_token`, mode 600. Do not print either credential.

**Setup remains dry-run-only.** `config/publishing.json.enabled = false` and `live_pilot_passed = false`. Every existing render in `queue/publish.json` is held. No Buffer draft, scheduled post or live post is created during setup. GitHub Pages media hosting is separate from social publishing.

**Facebook is connected but auto-posting has an additional policy hold:** these videos use realistic AI narration, Meta requires the native disclosure/label tool, and Buffer does not expose that flag for Facebook. A caption disclaimer is not a substitute. YouTube/Instagram can enter a pilot; Facebook waits for a supported native-label path. [1](https://support.buffer.com/en-us/articles/flagging-posts-as-ai-generated-in-buffer-V7jAnzYJ5n) [3](https://about.fb.com/news/2026/02/meta-prepares-for-2026-us-midterms/)

Owner-reported YouTube uploads are permanently locked against re-upload, independently of render/voice revisions:

| Brief | Verified public upload |
|---|---|
| `repo-removemacai-01` | https://www.youtube.com/shorts/lzXGzOsidCg |
| `tool-muse-01` | https://www.youtube.com/shorts/6OAa4KofxvQ |
| `spotlight-papermorph-01` | https://www.youtube.com/shorts/Mt8Yn9ShBmM |

Verified against the channel's public feed and Buffer's sent history. These locks apply to **YouTube only**, not Instagram/Facebook. The first Apple Intelligence video is not among the six Option-3-audited queued renders; do not cross-post an old voice version without an approved-voice render/kit.

## What happens if 10 videos are rendered?

Rendering does **not** immediately send them to Buffer. Enqueue pins the exact Release asset IDs and leaves the videos **held**. After owner posting approval and a fresh fact/copy review:

1. Start with **3 videos/day**, at **12:30, 17:30, 21:30 Asia/Karachi**. These are conservative starting slots, **not claimed analytics-derived optimal times**.
2. Instagram is offset by 5 minutes and Facebook by 10. Each channel has at least 3 hours between posts. Existing Buffer/manual posts consume the same calendar capacity.
3. Fill only the next **48 hours**, with a target of **6 pending posts/channel** against the configured Free-plan cap of 10. Excess videos stay in our durable backlog, not in Buffer. A ten-video balanced fixture yields six videos in the two-day horizon and four still waiting (18 platform posts with three fully eligible channels; Facebook is currently policy-held).
4. **At most 9 create operations/run**, 3 seconds between API calls. Four small cron checks/day replenish the queue; they do not publish everything simultaneously. A full video has three platform posts, so the usual per-run batch is three videos.
5. Max **one repo video/day**, prioritizing at least one tool and one news item. If the remaining backlog cannot supply the required mix, **hold and request fresh topics**, rather than fill the calendar with repos.
6. Scheduled timestamps use explicit UTC `dueAt` with `customScheduled`, never `shareNow` or unbounded `addToQueue`.

The pipeline serves **approved, rendered content**. It does not invent/research/approve new daily stories unattended. Daily topic discovery and production still follow the existing owner-approved radar/render workflow. If there is insufficient approved content, the queue stays empty rather than publishing stale material.

## Buffer policy / API handling

Use the official API only: `POST https://api.buffer.com`, Bearer key, GraphQL. No scraping of private interfaces or quota bypass. The public schema was saved from Buffer introspection on 2026-10-10 and is used for offline query/input tests.

- Published Free-plan API quotas: 100 requests/15 min, 250/24 h, 3,000/30 days. The code **reads actual `RateLimit` headers** instead of assuming those quotas are fixed.
- Reserve 5 requests for recovery. Honor `Retry-After` (seconds or HTTP date), add jitter and bound attempts to 4.
- For a short safe rate-limit rejection, wait within the run (maximum 60 seconds). For daily/monthly exhaustion or a longer delay, persist `cooldown_until`; subsequent cron runs make **no Buffer request** until then.
- Queries: bounded exponential backoff for transport/5xx/transient errors.
- Mutation: only an **explicit rejection**, such as 429, is automatically retried. Timeout, lost response, 5xx, ambiguous proxy errors or unknown GraphQL mutation outcomes become `uncertain`, not a blind second create.
- Check both HTTP status **and** GraphQL `errors`/typed mutation-error unions. `200 OK` is not sufficient.
- Invalid input or disconnected/changed/locked/paused/reminder-only channel: block, report, do not hammer the endpoint. Never downgrade automatically to a manual reminder.
- Sent-history scans are bounded to 14 days; active/draft/error history is fully paginated. Permanent manual/sent locks remain in our journal beyond that window. Incomplete pagination fails closed.

## Durable duplicate protection

`tracker/publications.json` is the authoritative per-**video + platform** journal in `main`.

1. Read Buffer state, account identities, pending counts and existing posts.
2. Reconcile known post IDs, exact immutable media URLs, matching text, or matching YouTube titles. Multiple matches are a conflict, not permission to create another post.
3. Commit `submitting` to GitHub via a Contents API SHA compare-and-swap **before** calling Buffer.
4. Send one request. Persist its returned ID/status immediately.
5. If the runner dies after Buffer accepted a post, the next run finds the receipt. If no unique receipt can be established, leave it held for agent review. Never assume 'not found yet' means safe to recreate.
6. If the GitHub journal is unavailable/conflicted, do **not** call Buffer. The workflow concurrency group serializes all posting/deployment runs; no force pushes.

There is no claim of server-side exactly-once delivery: Buffer exposes no idempotency key. The integration prefers a held post over a possible duplicate. A partial multi-platform success reuses its reserved slot for remaining platforms when that time is still viable.

### Error states and recovery

| State | Action |
|---|---|
| `retry_wait` | Explicit rejection only; wait for `retry_at`, check quota/capacity again, choose a future valid slot. Four attempts maximum. |
| `uncertain` / `submitting` | Reconcile first. Without a unique receipt, agent investigates Buffer before any change. No automatic recreate. |
| `blocked` | Correct/review copy, authorization or account configuration. No automatic repeated create. |
| `dead_letter` | Retry budget exhausted. Agent resolves explicitly. |
| `delivery_error` | Buffer accepted the post but the social network rejected delivery. Keep its ID and surface the error/help URL. Do not duplicate it as a new post. Agent resolves/retries that existing post after investigation. |
| `approval_required` / `notification_required` | Not automatic delivery. Agent resolves Buffer's channel/publishing policy; never pretend it was posted. |
| `scheduled` / `sending` | Wait; keep media live. |
| `sent` | Only claim published after Buffer reports sent; capture the external post URL. |
| `published_manual` | Owner-reported and verified upload, never auto-create again. |

Permanent/ambiguous/delivery issues fail the delivery job and appear in the Actions summary and the report artifact. GitHub notification delivery itself depends on the owner's notification settings; no email/SMS integration is claimed.

## Stable video hosting / quality gates

- Pages: https://zainkhan122.github.io/yt-tts/
- Each asset has an immutable path: `media/<github-release-asset-id>/<video-id>.mp4`.
- Never give Buffer the redirecting/expiring GitHub Release CDN URL. Those URLs are used only for unauthenticated downloads during the hosting build; PAT headers are never forwarded to the CDN.
- Verify Release IDs, file sizes/digests, all seven render QA checks, and the exact approved voice audit: **Chatterbox cloning Michael, exag 0.7, cfg 0.4, flow**.
- Keep every pending/ambiguous/error asset, plus seven days after successful delivery. A new Pages deploy includes the old pending media, not just this batch.
- A 750 MB site guard fails rather than evicts a needed asset. Finished videos remain archived in Releases after Pages retention ends.
- Before scheduling, validate public HTTPS, **no redirect**, `video/mp4`, expected length and MP4 header.
- Existing on-screen credit captions remain removed. Credits are appended to platform descriptions/captions instead.

## Platform details / limitations

- YouTube: required title + category 28, explicit public privacy, not made for kids. Generic synthetic narration over real demos defaults to no realistic-synthetic-content flag; set per-video `youtube_ai_generated` if the content needs it. The uploaded render, not just its voice, determines this disclosure.
- Instagram: Reel + share to feed + native `isAiGenerated: true`; thumbnail selected by time offset. Buffer does not accept a custom video thumbnail URL.
- Facebook: Reel + explicit **“AI-generated narration.”** in the caption. The current Buffer Facebook input schema has **no native AI-info field**. Do not claim the native label is set. These realistic AI-narrated videos are **policy-held** for Facebook until a supported native-label path is available. Caption text does not release this hold.
- No automatic pinned/first comments or backend YouTube tags are claimed; free-plan/endpoint support varies. Existing full SEO/post kits remain available.
- TikTok and X are **not connected or scheduled** in this integration.

## Operations (the agent does these; owner does not install anything)

```bash
# No render/TTS bootstrap is needed for these commands.
python3 -m pip install -r tools/post/requirements.txt
python3 -m unittest discover -s tests -v
python3 reels.py post --dry-run
python3 tools/post/queue_ctl.py enqueue <id> --tag renders-YYYY-MM-DD --category tool
# After owner posting approval AND actual same-day fact/copy review:
python3 tools/post/queue_ctl.py approve <id> --platforms youtube instagram --reviewed-until <timezone-aware-ISO-date>
python3 tools/post/queue_ctl.py enable --confirm OWNER_APPROVED_LIVE_POSTING
python3 reels.py sync -m 'Approve one Buffer delivery pilot'
python3 tools/gh_actions.py dispatch post.yml -i mode=schedule -i video_ids=<id> -i pilot=true
# Reconcile after its scheduled time and verify actual external posts.
python3 tools/gh_actions.py dispatch post.yml -i mode=reconcile
# Pull the new journal; only after every pilot platform is SENT:
python3 tools/post/queue_ctl.py pilot-passed <id>
python3 reels.py sync -m 'Verified live pilot; activate paced daily delivery'
```

**Kill switch:** cancel any in-progress `Hypeless delivery` run, then disable the workflow to stop new triggers, set `enabled: false` and hold queue entries. Merely disabling the workflow does not stop a run already in progress. Already scheduled Buffer posts **remain scheduled**; pause/cancel them in Buffer as appropriate. Disabling our cron does not cancel Buffer's own queue.

Source files: `config/publishing.json`, `queue/publish.json`, `tracker/publications.json`, `tools/post/`, `.github/workflows/post.yml`. Reports are Actions artifacts (30 days), not credentials/source. Finished MP4s remain in GitHub Releases; heavy files are never committed.

The personal GitHub token's extra **Administration: write** permission is only needed to create Pages the first time, not for routine posting. The workflow uses its short-lived `GITHUB_TOKEN` and least-privilege job permissions.

## Official references checked 2026-10-10

- https://support.buffer.com/en-us/articles/flagging-posts-as-ai-generated-in-buffer-V7jAnzYJ5n
- https://about.fb.com/news/2026/02/meta-prepares-for-2026-us-midterms/
- https://developers.buffer.com/guides/api-limits.md
- https://developers.buffer.com/guides/error-handling.md
- https://developers.buffer.com/guides/posts-and-scheduling.md
- https://developers.buffer.com/guides/hosting-media.md
- https://developers.buffer.com/types/CreatePostInput.md
- https://developers.buffer.com/types/PostInputMetaData.md
- https://developers.buffer.com/types/FacebookPostMetadataInput.md
- https://developers.buffer.com/types/InstagramPostMetadataInput.md
- https://developers.buffer.com/types/YoutubePostMetadataInput.md
- https://docs.github.com/en/rest/pages/pages#create-a-github-pages-site

Current integration status/proof is also recorded in `research/publishing/setup-report.md`. A passing dry-run is **not** an end-to-end public publishing test; the live pilot remains an explicit next step.
