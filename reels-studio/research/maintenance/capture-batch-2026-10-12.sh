#!/usr/bin/env bash
# Capture batch for the 2026-10-12 shorts (topics picked by research — see research/ideas/2026-10-12-shortlist.md).
#
# HAZARD (learned the hard way this session): bash re-reads a running script from disk, so
# editing this file while a run is in flight kills the runner mid-loop. To (re)run safely:
#     cp research/maintenance/capture-batch-2026-10-12.sh /var/tmp/run.sh && bash /var/tmp/run.sh
# A failed id keeps its heavy dir in /var/tmp/reels/captures/ for a --reuse-site retry.
#
# Known capture blocks (retarget, do not fight them):
#   openai.com        -> headless capture "navigation: degraded, blocked" (403 to simple fetches too);
#                        the GPT-6.1 Astra story captures from https://arcprize.org/blog/astra instead
#   ai.google.dev     -> docs page crashed at core-extraction; use https://deepmind.google/models/gemini-image/
set -u
cd /home/user/yt-tts/reels-studio
run() { echo; echo "########## CAPTURE $1"; python3 tools/capture.py "$1" "${@:2}" && echo "OK: $1" || echo "FAILED: $1"; }
run news-gpt61-astra-01      --url https://arcprize.org/blog/astra
run news-nano-banana-21-01   --url https://deepmind.google/models/gemini-image/
run tool-qwen38-01           --url https://huggingface.co/Qwen/Qwen3.8-27B
run tool-openmontage-01      --url https://github.com/calesthio/OpenMontage --repo calesthio/OpenMontage
run repo-ds4-01              --url https://github.com/antirez/ds4 --repo antirez/ds4
echo; echo "CAPTURE_BATCH_DONE"
