# Schedule record: repo-koubo-01 + repo-halo-01 (2026-10-28)

- Run: **40722616027** (post.yml `mode=schedule`, `video_ids=repo-koubo-01 repo-halo-01`)
- Owner authorization: "Schedule both now" (ask_user, 2026-10-28)
- Conclusion: **success** (prepare/hosting/delivery all success; delivery read-only validation passed)
- Queue: both enqueued via `queue_ctl.py enqueue --tag renders-2026-10-28 --category repo`, then approved
  (`--reviewed-until 2026-11-04T15:00:00Z`, platforms youtube/instagram/facebook). Viewer panels PASS filed
  under `research/production/viewer-panel-repo-{koubo,halo}-01-2026-10-28.md` (gate requires PASS on file).
- Published to GitHub Release `renders-2026-10-28` earlier; media verified by runner `--verify-media`.

## Buffer read-back (tracker/publications.json, state=scheduled)

| video_id | platform | buffer_post_id | due_at |
|---|---|---|---|
| repo-koubo-01 | youtube | 6ae21dc7f835de4f32579913 | 2026-10-28T20:00:00Z |
| repo-koubo-01 | instagram | 6ae21dce1d398031838ecf23 | 2026-10-28T20:00:00Z |
| repo-koubo-01 | facebook | 6ae21dcbe490badbade8434b | 2026-10-28T20:00:00Z |
| repo-halo-01 | youtube | 6ae21dd2f835de4f32579ea3 | 2026-10-28T20:00:00Z |
| repo-halo-01 | instagram | 6ae21dda1d398031838ed6c7 | 2026-10-28T20:00:00Z |
| repo-halo-01 | facebook | 6ae21dd6f835de4f3257a189 | 2026-10-28T20:00:00Z |

All 6 runner receipts committed (`publishing: receipt ... scheduled`); read-back verification commit `dc73c12`.
