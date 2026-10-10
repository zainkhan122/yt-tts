# Direct YouTube publishing + Shorts enrichment

**Client JSON received; Google channel consent is still pending.** `enabled=true` prepares the authorised Shorts metadata worker, while `live_pilot_passed=false` and the empty long queue keep routine long uploads gated. Cron uses enrichment-only mode until a long-form pilot passes, and makes no requests without OAuth. The encrypted upload-session key is installed. No direct Google upload/enrichment is claimed completed yet.

## Scope

- Long-form, landscape episodes: resumable private upload → processing check → title/description/tags → custom thumbnail → category and long-form playlists → future `status.publishAt` → confirmed public receipt.
- Buffer Shorts: Buffer handles native title/description/hashtags and publication; this worker adds backend tags plus category/Shorts playlists once Buffer reports sent and provides a real YouTube ID. Public copy/privacy are preserved.
- Native IG/FB captions/hashtags remain in the Buffer route. Do not invent YouTube-style backend fields for other networks.
- Production contract: `briefs/long/README.md`. This uploader does not itself research stories or render long episodes.

## Pacing / configuration

`config/youtube.json`: America/New_York (DST-aware), Tue 09:00 repo, Fri 12:00 news, Sun 10:00 tool. Up to three long videos/week. Prepare/upload only within 72 hours of the slot; at least three hours must remain when arming publication. One upload per run; two session starts/day; local general API quota budget 2,000 units/day. These are conservative operational caps, not claims about your project's exact quota.

Current Google documentation assigns `videos.insert` to a separate 100-upload/day bucket, with one unit per call. Other writes, such as metadata/thumbnail/playlist operations, have their own method costs; we account conservatively and handle actual quota rejections. Daily budgets reset using **America/Los_Angeles**, not audience time or UTC. Unknown account-level upload limits are respected rather than bypassed. [1](https://developers.google.com/youtube/v3/docs/videos/insert)

Buffer and YouTube Actions workflows share `hypeless-publishing` concurrency. No bulk uploads/publication. Buffer uses per-network calendars and two-day lookahead; the long worker checks existing short receipts for collisions. Notification policy reserves room for long videos rather than notifying subscribers five times/day.

## Retry / duplicate safety

- Journal: `tracker/youtube-publications.json`. CAS update must succeed before an external write; a lost/conflicted GitHub write stops processing.
- A unique, non-sensitive `hypeless-ref-...` backend tag binds the internal video ID and MP4 digest. It is a receipt-recovery marker, not an SEO claim. It is never added to the public description.
- Resumable session URI is SecretBox-encrypted under `YOUTUBE_STATE_KEY` and bound to media/channel before any media bytes are sent. Raw session URLs, refresh tokens and access tokens are never journaled publicly.
- Resume from Google's `308 Range` response, not a local guessed offset. `308` is handled as a receipt, never followed as an HTTP redirect.
- Use efficient 64 MiB chunks (a multiple of 256 KiB), not thousands of tiny chunks. Media stays under runner scratch and is removed on success/failure.
- Persist the final-chunk reservation before sending it. A lost final response is probed on the same upload session; a confirmed video ID is reused.
- Session expiry or an ambiguous create without a unique receipt is held for agent reconciliation, not blindly re-uploaded. The bounded recent-owned-upload scan is not claimed as proof that a video could never exist elsewhere in a channel's history.
- Queries/idempotent updates: bounded retries with exponential backoff + jitter. Explicit rate-limit rejections honor `Retry-After`. Long cooldowns are persisted across runs.
- Non-idempotent create/media write after transport loss/5xx: reconcile first. Four attempt budget; invalid credentials/permissions/inputs are actionable holds, not retry storms.
- Playlist creation and membership have their own reservations and receipt checks. No blind reinsertion after a timeout.
- Initial upload is **private**. Processing, custom thumbnail and metadata gates must pass before scheduling. A past `publishAt` can publish immediately, so stale/near slots are held/replanned, never sent.
- “Sent” requires the API to confirm **public**. Scheduled/private/processing is never labelled published.

Official upload protocol: https://developers.google.com/youtube/v3/guides/using_resumable_upload_protocol

## Metadata and thumbnails

`seo.py` validates source links, a natural primary keyword, title ≤100 characters, description ≤5,000 UTF-8 bytes after chapters/credits, tags ≤500 characters including separators/quotes, sensible hashtags and real chapter timings. Long videos do not use `#Shorts`.

Enrichment reads the current video first and updates `part=snippet` only, preserving title/description/category/language and existing tags. It never includes the status part, so tags cannot change privacy. A conditional ETag helps detect concurrent edits; conflicts require a fresh review rather than overwriting owner changes.

Playlist keys: `tool`, `news`, `repo`, `shorts`, `long`. The worker adopts one matching owned playlist or creates it once, then checks membership before insertion. Explicit playlist IDs can be configured. Manual uploads are excluded from enrichment by default (`include_manual_uploads=false`); they stay protected against re-upload.

Thumbnail: `thumbnail.py` creates a branded 1280×720 JPEG and a **250px-wide preview**. Main text: max six words, max three lines, large Anton, high contrast. The report includes text bounding boxes, scaled glyph heights, byte size and SHA-256. Agent visual approval is required in addition to automatic checks. API currently supports up to 50 MB, but our own budget is 1.8 MB for fast delivery, not a claimed platform limit. [3](https://developers.google.com/youtube/v3/docs/thumbnails/set)

## Queue / operations — agent does the work

```bash
python3 reels.py youtube --mode dry-run
python3 tools/youtube/thumbnail.py briefs/long/<id>.json --dest renders/<id> --proof-image <approved-image>
# Publish final MP4, manifest, thumbnail and thumbnail report into a NEW immutable Release tag.
python3 tools/youtube/queue_ctl.py enqueue <id> --tag long-renders-YYYY-MM-DD --category tool
# After source/copy review and actually looking at the 250px thumbnail:
python3 tools/youtube/queue_ctl.py approve <id> --reviewed-until <ISO-date> --thumbnail-reviewed
python3 reels.py sync -m 'Approve private long-video pilot'
python3 tools/gh_actions.py dispatch youtube.yml -i mode=private-pilot -i video_ids=<id>
# Inspect actual private upload. Then explicitly approve public release / enable config:
python3 tools/youtube/queue_ctl.py approve <id> --reviewed-until <ISO-date> --thumbnail-reviewed --public
python3 tools/youtube/queue_ctl.py enable --confirm OWNER_APPROVED_YOUTUBE_DELIVERY
python3 reels.py sync -m 'Approve one public long-video pilot'
python3 tools/gh_actions.py dispatch youtube.yml -i mode=schedule -i video_ids=<id> -i pilot=true
# Reconcile after its publication time, pull journal, then record the verified public pilot:
python3 tools/gh_actions.py dispatch youtube.yml -i mode=reconcile
python3 tools/youtube/queue_ctl.py pilot-passed <id>
```

OAuth connection steps: `research/publishing/google-connection.md`. Never paste credentials into source or issue comments.

## Failure states / kill switch

| State | Meaning / action |
|---|---|
| `queued` | Approved file can be attempted when within the upload window/budget. |
| `session_start_uncertain` | Session allocation response lost. No new session until reconciled/reviewed. |
| `uploading` | Decrypt saved session, probe offset and resume. |
| `upload_uncertain` / `expired_uncertain` | Find a unique marker receipt; otherwise agent investigates. No blind fresh upload. |
| `uploaded_private` / `processing` | Keep the existing video ID and wait for processing. |
| `private_ready` | Metadata complete; private pilot or awaiting approved future publication. |
| `scheduling` | Re-read status/publishAt after an ambiguous update. |
| `scheduled` | YouTube acknowledged future release; not yet sent. |
| `sent` | Actual public receipt + URL, never re-upload. |
| `blocked` / `publication_failed` / `duplicate_conflict` | Stop and surface an actionable error against the existing resource. |

Cancel in-progress delivery runs, disable both workflows and set enabled flags false to stop new work. **Existing Buffer schedules and already armed YouTube `publishAt` values continue independently.** Cancel/pause those at the provider if needed; disabling a cron does not revoke a schedule. No deletion/cancellation of existing public videos is automatic.

## Storage / boundaries

Never put MP4s, OAuth JSON, raw upload-session URIs or API keys into git. Long media uses Releases → runner scratch, not Pages. Existing finished render releases are immutable; use a new `-r2` tag for revisions. Audit workspace/project budgets with `tools/maintenance/storage.py`; prune only after byte-for-byte archive verification. Existing source/media credits and all three manual YouTube duplicate locks remain intact.
