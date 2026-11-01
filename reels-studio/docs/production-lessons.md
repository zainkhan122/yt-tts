# Production lessons → pipeline checks

Each lesson is enforced by code that runs in `tools/preflight.py` (or in the step named), not by a note.
A row marked **Open** has no code check yet; it stays open until one exists. Update this table
whenever a new failure teaches us something, and point the row at a real function.

| # | Lesson (where it cost time) | Enforced by (code) |
|---|---|---|
| 1 | Clip scenes are boxed in a card with black margins. Tool media belongs in image scenes with focus moves. | **Open.** No code check yet. Planned: `preflight` rule that blocks a clip scene carrying tool media unless it is marked full-frame. |
| 2 | Tool media at 640 px is soft when enlarged. Own graphics are built at 1920×1080; native pixels are never upscaled past 3×. | **Open.** No code check yet. |
| 3 | A focus box that clips a label looks broken in the render. | `tools/motion/focus_check.py` (`keep_visible`) via `preflight.check_motion` |
| 4 | Static scenes hold too long. A visual change must come every 4.5 s. | `focus_check.py` hold limit via `preflight.check_motion` |
| 5 | Cloud renders run from origin `main`. A dispatch from unpushed work renders an old brief. | `preflight.check_dispatch_head`, called by `reels.py cloud` |
| 6 | `origin` disappears after a restore (`.git/config` is not snapshotted). | `preflight.check_dispatch_head` BLOCKs when origin `main` differs from local HEAD; it reports NOTE if origin cannot be read, so a missing remote is visible before dispatch |
| 7 | A brief edit makes the receipt stale (brief sha, script sha, word count). | `production_gate.validate_receipt` |
| 8 | A cover change is required before a failed-input render can be re-dispatched (duplicate guard). | `cover_store.py push`; `reels.py cloud` duplicate guard uses the cover hash in the fingerprint |
| 9 | Captures, covers and spec files are gitignored in places; `git add` silently skips them. | `preflight.check_tracked` (blocks when a spec, queue or receipt file is not tracked) |
| 10 | Stale local render files block preflight (no QA manifest). | `preflight.check_render` |
| 11 | Panel is the last gate, so a failed cycle costs about 15 minutes. | `reels.py cloud` runs the full `preflight()` first and blocks on any BLOCK |
| 12 | Workspace snapshot limit (128 MB / 10,000 files). | `preflight.check_workspace` (uses `tools/maintenance/storage.py audit`) |
| 13 | Pans that stop on a node show a sliver of the neighbouring node at the card edge. | `focus_check.py` (`keep_visible` on every step, including the ends) |
| 14 | A landscape image leaves the lower third of a 9:16 frame empty. | `preflight.check_media_aspect` |
| 15 | A scrim over the lower half of a card hid the media in three renders. | `tools/layout_audit.py` scrim check via `preflight.check_layout` |
| 16 | Half-checked renders cost a full cloud cycle each. | `preflight.check_layout` (local Chromium; `tools/browser_setup.py` sets it up) |
| 17 | Piping a dispatch into `head -1` killed the local process after the cloud run was created; the duplicate guard then looked like a failure. | `reels.py cloud` writes `tracker/dispatch-log.json` and refuses a repeat within 6 h unless `--redispatch REASON` is given |
| 18 | A new motion rule failed published briefs in CI. | Versioned standard: `motion_standard >= 2` opts a brief into the hold and media-aspect rules (`preflight.check_motion`, `check_media_aspect`) |
| 19 | One stale copy pin failed the whole publishing test. | `tests/test_pipeline_gates.py` and `tests/test_publishing.py` per-item pins; exempt only with `copy_pin_pending` |
| 20 | Two videos got the same post time. | `tools/post/cadence.py`: a bracket held by any scheduled post on the channel is skipped; the gap check runs on the final time |
| 21 | A YouTube Shorts cover is approved separately after the post is sent. | `tools/post/queue_ctl.py approve` requires `cover_sha256` for YouTube items |
| 22 | Unit tests missing `yt-dlp` or `pynacl` failed the YouTube worker's safety step. | `tools/youtube/requirements.txt`; `tests/test_pipeline_gates.py` checks `yt-dlp` is listed |
| 23 | `post.yml` exits 1 on legacy `tool-*` rows marked uncertain even when the new posts are created. | `tools/post/publisher.py` `blocking()`: uncertain rows are listed for review and do not fail the run; failed and channel-level issues still do (`tests/test_pipeline_gates.py` PublisherExitTests) |

## Failures, 26 Oct to 1 Nov, and the code that now prevents them

The full list with status is `config/failure_ledger.json`; `tests/test_failure_ledger.py` fails if an
"enforced" row points at code that does not exist. Open rows are listed there, not hidden.
One command runs the whole chain: `docs/make-shorts.md`.

## Per-video checklist (in order; stop at the first BLOCK)

1. `python3 tools/preflight.py <brief-id>` → every check PASS. This covers lint, studio rules, queue pin, render, motion, media aspect, policy, local layout audit, tracked files and workspace.
2. Media: the tool's own media checked; own graphics built where the tool's media is small.
3. Receipt: `validate_receipt(verify_assets=True)` passes after any brief edit.
4. Cover: built and checked; text matches the brief's `cover_concepts[0].text`; pushed with `cover_store.py push`.
5. Commit, rebase on origin, push; `git ls-remote origin main` equals local HEAD.
6. Dispatch once with `reels.py cloud`, output to a log file (lesson 17). Wait for QA. Download the artifact.
7. Viewer panel on the downloaded MP4. Only then cover and copy review with the owner.
