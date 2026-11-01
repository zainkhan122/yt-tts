# Production lessons → pipeline checks

Each lesson from a failed or slow cycle is enforced by a check, not left as a note.
Update this table whenever a new failure teaches us something.

| # | Lesson (where it cost time) | Enforced by |
|---|---|---|
| 1 | Clip scenes are boxed in a card with black margins. Use image scenes with focus moves, the layout that passed the viewer panel. | `preflight` brief rule: image scenes for tool media; clip only for full-frame motion (review) |
| 2 | Tool media at 640 px is soft when enlarged. Make own vector graphics at 1920×1080 for diagrams and text. Native pixels are never upscaled past 3×. | `captures` kit rule (review); the kit is in `captures/<id>/kit/` |
| 3 | A focus box that clips a label looks broken in the render. | `tools/motion/focus_check.py` (scene `keep_visible`), run by `preflight` |
| 4 | Static scenes hold too long. A visual change must come every 4.5 s. | `focus_check.py` hold limit; panel frames |
| 5 | Cloud renders run from origin `main`. A dispatch from unpushed work renders an old brief. | `reels.py cloud` calls `preflight.check_dispatch_head` and refuses when origin ≠ local or brief/receipt are uncommitted |
| 6 | `origin` disappears after a restore (`.git/config` is not snapshotted). | Re-add without credentials; token only in the push header (never written to config) |
| 7 | A brief edit makes the receipt stale (brief sha, script sha, word count). | `production_gate.validate_receipt`; refresh after every brief edit |
| 8 | A cover change is required before a failed-input render can be re-dispatched (duplicate guard). | cover pack pushed with `cover_store.py`, and `selection.json` sha updated |
| 9 | Captures and covers are gitignored; `git add` silently skips them. Use `-f` for spec and selection files. | Commit step checklist (below) |
| 10 | Stale local render files block preflight (no QA manifest). Delete a render folder before re-rendering. | `preflight` render check |
| 11 | Panel is the last gate, so one cycle costs about 15 minutes. Check locally first: focus steps, contact sheet, receipt, origin head. | Local-first order in the checklist |
| 12 | Workspace snapshot limit (128 MB / 10,000 files). Keep only current renders locally; the GitHub release holds the rest. | Cleanup after every render: compare sha with release asset before deleting a local copy |
| 13 | Pans that stop on a node show a sliver of the neighbouring node at the card edge. Each focus step must show whole labels, or none at the edge (check `keep_visible` on every step, including the ends). | `focus_check.py` (partial overlap); extend to sub-labels at 1:1 later |
| 14 | A landscape image leaves the lower third of a 9:16 frame empty. Build kit images at the card's portrait proportion so the media fills the middle of the frame. | Kit spec: diagram and feed images at 1080×1400 or taller; check in the local contact sheet before dispatch |
| 15 | A scrim over the lower half of a card hid the media in three renders. Shading must never cover the tool's media; captions get space, not a dark overlay. | Visual frame check (contact sheet) before any dispatch; the scrim was removed from the template |
| 16 | Half-checked renders cost a full cloud cycle each. The local browser now runs (Playwright + Chromium, user-space libraries), so the layout audit and frame sheets run before dispatch. | `tools/layout_audit.py` on the brief, then a local contact sheet; both must pass before `reels.py cloud` |
| 17 | Piping a dispatch into `head -1` killed the local process after the cloud run was already created. A second dispatch was then blocked by the duplicate guard, and the first run looked failed. | Dispatch to a log file, never through a pipe; read `run id` from the log before any re-dispatch |
| 18 | A new motion rule failed published briefs in CI (outclass test) and blocked the YouTube worker. | Versioned standard: `motion_standard >= 2` opts a brief into the hold and media-aspect rules; published briefs are not re-judged |
| 19 | One stale copy pin failed the whole publishing test, which blocked every video's dry-run. | Per-item test. A stale pin is exempt only with a visible `copy_pin_pending` note on that queue row |
| 20 | Two videos got the same post time: the random offset depended only on platform/day/slot, and the gap check ran before the offset. | `cadence.py`: gap check on the final time; offset salted with the channel's post count |
| 21 | A YouTube Shorts cover is a separate step after Buffer sends the post. Approving the cover digest is required before the enrichment worker can set it. | `cover_ctl extract` → look at the preview → `cover_ctl approve`; `thumbnails.set` only with the recorded digest |
| 22 | Unit tests missing `yt-dlp` or `pynacl` in the CI image failed the YouTube worker's safety step. | `tools/youtube/requirements.txt` lists `yt-dlp`; the test job runs the same requirements |
| 23 | `post.yml` exits 1 on legacy `tool-*` rows marked uncertain even when the new posts are created. Operators read the wrong status. | Open: per-row report and a closing step for those rows (see decisions) |

## Per-video checklist (in order; stop at the first failure)

0. Local audit: `tools/layout_audit.py` passes and the local frame sheet shows no shaded or cut media (no dispatch before this).
1. Media: tool's own media checked; own graphics built at 1920×1080 where the tool's media is small.
2. Brief: `brief_lint` 0 errors; `focus_check` PASS; SEO pack 0 errors.
3. Receipt: script and assets stages refreshed; `validate_receipt(verify_assets=True)` passes.
4. Cover: built by `covers/system`; text matches `treatment.cover_concepts[0].text`; pushed with `cover_store.py push`.
5. Commit (use `-f` for ignored spec/selection files), rebase on origin, push; check `ls-remote origin main` equals local HEAD.
6. Dispatch once with `--receipt`, output to a log file (lesson 17). Check the run list before any re-dispatch. Wait for QA. Download the artifact. Remove any stale local render first.
7. Viewer panel on the downloaded MP4 and a contact sheet. Only then cover and copy review with the owner.
