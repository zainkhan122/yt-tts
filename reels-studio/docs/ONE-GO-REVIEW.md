# Restore and render a voiced review in one command

For an existing scene renderer implementing the local handoff contract:

```
cd ~/yt-tts/reels-studio
python3 tools/one_go_review.py --id repo-gta6-clipper-01 \
  --script briefs/graphics/repo-gta6-clipper-01/script.json \
  --renderer briefs/graphics/repo-gta6-clipper-01/house-preview.py \
  --video renders/repo-gta6-clipper-01/review.mp4 \
  --cover covers/repo-gta6-clipper-01/cover.jpg \
  --art covers/repo-gta6-clipper-01/purpose-made-art.png
```

The command restores missing local review dependencies, requests the approved Option-3 voice on a larger GitHub Actions runner, resumes the saved run rather than duplicating it, validates voice output and script fingerprint, downloads it, and runs the local scene renderer. It requires purpose-made art and a composed 1080×1920 cover before voice dispatch, then embeds and verifies that cover in the renderer’s declared output. The renderer must call `tools/append_house_outro.py` with the approved Chatterbox CTA and aligned timings; the review command checks its exact-output assembly marker before embedding the cover. This marker does not replace final audiovisual inspection. It never publishes or schedules anything.

A fresh workspace needs Python, pip, sudo, network access, the repo checkout and GitHub token available through the existing secret helper. Actions in a public repository are not confidential: don't use this workflow for secret/private script text. The tool won't upload local footage to Actions. A saved dispatch with an uncertain outcome fails closed rather than dispatching a duplicate. See `review-run.json` inside the relevant render directory.

Production voice and full rendering require Python 3.12 and substantial RAM; this 2 GB sandbox uses the larger Actions runner for that job. On a suitably provisioned Python 3.12 host, `bash setup/restore-production.sh --full` installs the full pinned production stack. `bash setup/restore-production.sh` restores local review dependencies only. A voiced review is not a publication approval: verify third-party rights, audio intelligibility, genuine word alignment, motion/layout, frame-zero cover and all production gates before sharing.
