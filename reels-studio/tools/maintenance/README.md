# Storage safeguards

- Saved workspace warning: 100 MB; snapshot budget approximately 128 MB / 10,000 files.
- Tracked Reels Studio/workflow source budget: 20 MB. No tracked MP4/MOV/WebM/MKV, no new individual source file over 5 MB.
- Finished short/long media: GitHub Releases; not git. Heavy downloads/transcodes: runner scratch or `/var/tmp`, never permanent workspace copies.
- Short-form public hosting: retained Pages bundle, 750 MB cap. Keep pending/uncertain/error media and seven days after successful posting; fail rather than evict a needed video.
- Long-form uploads: one job at a time, bounded file size, disk-space check, cleanup even when the job fails.
- Finished render releases are immutable: revisions get fresh tags. Do not delete/replace a pinned MP4 or kit to save space.
- Capture packs: remote archive must exist with a digest, and every local file must match byte-for-byte before local pruning. No archive extraction is needed for verification.
- Cover QA: frame 0 must visibly contain hook content. `lib/framecheck.py` measures decoded grayscale pixels at t=0; the render manifest records the peak and QA refuses to publish a frame below the evidence-based threshold. The scene suite also checks real templates for visible cover-critical layers at 0.0 s.
- Downloaded kit ZIPs are intermediates only; cover extraction verifies the Release digest and removes the local ZIP in a `finally` block. Keep only the compact reviewed JPEG previews when needed.
- Do not delete credentials, briefs, source research, dedupe receipts, remote Release archives, or another project. Do not rewrite shared repository history.

```bash
python3 tools/maintenance/storage.py audit
python3 tools/maintenance/storage.py prune-capture muse          # verify only
python3 tools/maintenance/storage.py prune-capture muse --apply  # one verified local duplicate
python3 tools/maintenance/storage.py prune-all                   # verify every archived local capture pack
python3 tools/maintenance/storage.py prune-all --apply           # prune only byte-for-byte verified packs
```

GitHub Actions audit measures its sparse checkout, not the hosted runner's whole home/toolchain. Arena workspace audit measures snapshot-relevant files under the workspace root. The repository's other projects are outside this cleanup scope.

On 2026-10-10, 36 Muse capture files (28.55 MB) were verified against `capture-packs/muse.tar` and their local copies removed. The archive, source references and files needed to reconstruct future captures remain available. Detailed evidence is in `research/publishing/capture-cleanup-2026-10-10.json`.


## 2026-10-12 cleanup and measured status

The user's snapshot warning reported 134,249,222 bytes and 1,207 files. `prune-all --apply` checked all 10 local capture packs against their digest-bearing GitHub Release tarballs; all 10 passed (every member SHA-256 compared; 45.1 MB verified) before the local copies were removed. The remote capture archives were untouched. Removed the local `_verify` kit-download cache and duplicate `*-kit.zip` files; approved JPEG cover previews remain. `contracts.fetch_kit_cover` now deletes its verified download intermediate automatically after extraction.

Immediately post-prune, `storage.py audit` reported **49,393,378 bytes / 1,036 files; `ok: true`**. After the follow-on guard/docs commit, the latest audited tree (2026-10-12T15:06Z) was **49,461,864 bytes / 1,057 files; `ok: true`**. Tracked studio source is 7,428,827 bytes; no tracked videos, oversized files, or unrelated project directories were removed. The reusable default remains read-only; destructive pruning requires the explicit `--apply` flag and per-file byte verification.
