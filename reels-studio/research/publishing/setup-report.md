# Publishing setup — 2026-10-10

## Verified

- One Buffer key authenticates and sees YouTube, Instagram Professional and Facebook Page channels, all connected/unlocked/unpaused, with automatic publishing support on YouTube/Instagram.
- Channel mappings saved in `config/publishing.json`; no private account email or API key is in source.
- `BUFFER_API_KEY` stored as an encrypted GitHub Actions repository secret.
- Pages enabled with `build_type: workflow` at https://zainkhan122.github.io/yt-tts/.
- Three manual YouTube uploads verified through the public feed and Buffer sent history; permanent YouTube-only duplicate locks saved.
- Six current kits rechecked against all 7 QA gates and Option 3's exact narration configuration. Frozen asset IDs/digests saved, not just mutable Release filenames.
- Official Buffer schema saved for offline GraphQL validation; YouTube/Instagram/Facebook payloads pass schema coercion.
- Local safety suite: 47 tests pass, including ten-video batching, quotas, Retry-After, query backoff, permanent errors, partial platform success, lost-response reconciliation, write-ahead journal failure and voice gating.
- Local live-API **read-only** dry-run: successful, **zero Buffer mutations**. Existing sent history remains intact.

## Cloud evidence — passed

- Run: https://github.com/zainkhan122/yt-tts/actions/runs/38039786831
- `prepare`: success (47 tests, six pinned asset/kit audits, Pages bundle).
- `hosting`: success (Actions-based Pages deploy).
- `delivery`: success (encrypted Buffer secret works in Actions; authenticated read-only preflight).
- Result recorded at **2026-10-10 09:00:07 UTC / 14:00:07 Asia/Karachi**: `mode=dry-run`, `created=0`, **one Buffer read query**, no delivery issues.
- Four hypothetical platform rows: Claude + free-video-tools, each on YouTube/Instagram. Facebook was correctly excluded by its native-disclosure policy hold.
- All **six hosted MP4 URLs** separately checked: direct public HTTPS, `video/mp4`, exact pinned size, valid MP4 header. Hosting includes retained assets, not only the proposed posts.
- Sanitized evidence: `cloud-validation-2026-10-10.json`. Full dry-run plan is the workflow artifact `hypeless-delivery-report` (30-day retention).
- No files outside `reels-studio/` and `.github/workflows/` changed in the repository.

## Not activated / not claimed

- `enabled: false`, `live_pilot_passed: false`; all six render queue entries held.
- No Buffer drafts, schedules or live posts created during setup.
- No end-to-end social delivery claim until an owner-approved live pilot is actually sent and its external links are verified.
- No autonomous daily research/script/capture generation. This queue safely delivers approved renders; existing radar and cloud rendering remain the production path.
- Native Instagram AI labeling is supported. Buffer's Facebook API currently lacks the native AI-info field; caption disclosure is not a substitute. Facebook automatic publishing is explicitly policy-held; YouTube/Instagram can proceed to an approved pilot.

See `tools/post/README.md` for pacing defaults, failure recovery, kill switch and official sources.
