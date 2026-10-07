#!/usr/bin/env bash
# =====================================================================================
#  Reels Studio: ONE-CLICK RESTORE (idempotent, safe to re-run any time)
#
#     bash ~/yt-tts/reels-studio/bootstrap.sh            # after a sandbox reset
#
#  If even the workspace copy is gone, this one-liner rebuilds everything from GitHub:
#     curl -fsSL https://raw.githubusercontent.com/zainkhan122/yt-tts/main/reels-studio/bootstrap.sh | bash
#
#  1. git working copy: sparse + blobless clone of ONLY reels-studio/ (the repo is ~7 GB);
#     repairs .git/config, which workspace snapshots deliberately drop, then pulls the latest SSOT
#  2. toolchain: Node 22, FFmpeg, Chrome libs, HyperFrames CLI (pinned), Kokoro TTS, whisper.cpp (-j1)
#  3. doctor: every check green = ready to render
#
#  Pushing / publishing needs a GitHub token for THIS session only:
#     export GH_TOKEN=...   (or write it to /var/tmp/gh/token)  - never commit it, never put it in ~/
# =====================================================================================
# Whole script is one function: bash parses it completely before running anything, so no child
# process (apt, npm, git) can swallow the rest of the script when it is piped in via curl | bash.
main() {
  set -euo pipefail
  URL="https://github.com/zainkhan122/yt-tts.git"
  REPO="${REELS_REPO:-$HOME/yt-tts}"
  T0=$(date +%s)
  say() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

  say "1/3 git working copy ($REPO, sparse: /reels-studio/)"
  if [ ! -d "$REPO/.git" ]; then
    git clone -q --filter=blob:none --no-checkout --depth 1 "$URL" "$REPO"
    git -C "$REPO" sparse-checkout set --no-cone '/reels-studio/'
    git -C "$REPO" checkout -q main
    echo "   cloned (only reels-studio/ is downloaded)"
  else
    if ! git -C "$REPO" config --get remote.origin.url >/dev/null 2>&1; then
      echo "   .git/config missing (snapshots exclude it): restoring from template"
      grep -v '^#' "$REPO/reels-studio/setup/git-config.template" > "$REPO/.git/config"
    fi
    git -C "$REPO" sparse-checkout set --no-cone '/reels-studio/' >/dev/null 2>&1 || true
    if git -C "$REPO" fetch -q --depth 1 origin main 2>/dev/null; then
      if git -C "$REPO" merge -q --ff-only origin/main 2>/dev/null; then echo "   up to date with GitHub"
      else echo "   NOTE: local commits/changes not on GitHub yet - run: python3 reels.py sync"; fi
    else
      echo "   offline? using the local copy"
    fi
  fi
  HERE="$REPO/reels-studio"

  say "2/3 toolchain (skips what is already installed)"
  WITH_WHISPER=1 bash "$HERE/setup/setup-sandbox.sh" </dev/null
  python3 -c "import numpy, scipy, soundfile, kokoro_onnx" 2>/dev/null || pip install -q numpy scipy soundfile kokoro-onnx 2>/dev/null \
    || pip install -q --break-system-packages numpy scipy soundfile kokoro-onnx

  say "3/3 doctor"
  rc=0; python3 "$HERE/reels.py" doctor </dev/null || rc=$?
  echo "restore finished in $(( $(date +%s) - T0 ))s  ->  cd $HERE && python3 reels.py --help"
  return $rc
}
main "$@" </dev/null
