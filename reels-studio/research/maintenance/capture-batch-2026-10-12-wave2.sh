#!/usr/bin/env bash
# Wave-2 captures for 2026-10-12 (five more videos; day total 10 = the owner ceiling).
# Topics picked from the same radar/feed factors as wave 1 — see research/maintenance/2026-10-12-batch-2.json.
#
# HAZARD (learned the hard way): bash re-reads a running script from disk, so editing this file
# while a run is in flight kills the runner mid-loop. To (re)run safely:
#     cp research/maintenance/capture-batch-2026-10-12-wave2.sh /var/tmp/run.sh && bash /var/tmp/run.sh
#
# Known capture blocks (retarget, do not fight them):
#   openai.com + help.openai.com  -> 403 blocks headless/plain fetches; use the official developer
#                                    surface https://developers.openai.com/... (accessible 2026-10-12)
#   HF gated model cards (LTX-2.5) -> the card needs auth; capture the product site (ltx.studio) instead
#
# Operational lessons (2026-10-12, wave 2):
#   * Run ONE heavy capture at a time on the 2 GB sandbox. Two concurrent captures starve chrome:
#     a single phase can stretch from ~60 s to 5+ min, and puppeteer navigation (networkidle2) can
#     hit its 90 s timeout under memory pressure. capture.py retries a failed extra pass up to 3x.
#   * Never side-load a capture for an id that is still ahead in this wrapper's queue (same output
#     dirs => collided runs). If you must parallelise, pick ids NOT listed below.
#   * Cookie/consent overlays: tools/capture_extra.cjs dismisses known consent buttons and logs
#     "+consent-dismissed: <label>" into extra.json (opt-out REELS_DISMISS_CONSENT=0).
#   * hyperframes default --capture-budget (120 s) degrades inner site phases on very long SPAs;
#     our packs are unaffected (pack screenshots come from capture_extra), kept as-is on purpose.
set -u
cd /home/user/yt-tts/reels-studio
run() { echo; echo "########## CAPTURE $1"; python3 tools/capture.py "$1" "${@:2}" && echo "OK: $1" || echo "FAILED: $1"; }
run repo-opencr-01      --url https://github.com/alibaba/open-code-review --repo alibaba/open-code-review
run tool-higgsfield-01  --url https://higgsfield.ai/creator-hub/changelog
run tool-ltx25-01       --url https://www.ltx.studio/
run news-gpt61-sol-01   --url https://developers.openai.com/api/docs/models/gpt-6.1-sol
run news-clef-01        --url https://huggingface.co/Cloudflare/clef
echo; echo "WAVE2_FULL_DONE"
