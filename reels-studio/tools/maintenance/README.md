# Storage safeguards

- Saved workspace warning: 100 MB; snapshot budget approximately 128 MB / 10,000 files.
- Tracked Reels Studio/workflow source budget: 20 MB. No tracked MP4/MOV/WebM/MKV, no new individual source file over 5 MB.
- Finished short/long media: GitHub Releases; not git. Heavy downloads/transcodes: runner scratch or `/var/tmp`, never permanent workspace copies.
- Short-form public hosting: retained Pages bundle, 750 MB cap. Keep pending/uncertain/error media and seven days after successful posting; fail rather than evict a needed video.
- Long-form uploads: one job at a time, bounded file size, disk-space check, cleanup even when the job fails.
- Finished render releases are immutable: revisions get fresh tags. Do not delete/replace a pinned MP4 or kit to save space.
- Capture packs: remote archive must exist with a digest, and every local file must match byte-for-byte before local pruning. No archive extraction is needed for verification.
- Do not delete credentials, briefs, source research, dedupe receipts, remote Release archives, or another project. Do not rewrite shared repository history.

```bash
python3 tools/maintenance/storage.py audit
python3 tools/maintenance/storage.py prune-capture muse          # verify only
python3 tools/maintenance/storage.py prune-capture muse --apply  # verified local duplicate only
```

GitHub Actions audit measures its sparse checkout, not the hosted runner's whole home/toolchain. Arena workspace audit measures snapshot-relevant files under the workspace root. The repository's other projects are outside this cleanup scope.

On 2026-10-10, 36 Muse capture files (28.55 MB) were verified against `capture-packs/muse.tar` and their local copies removed. The archive, source references and files needed to reconstruct future captures remain available. Detailed evidence is in `research/publishing/capture-cleanup-2026-10-10.json`.
