#!/usr/bin/env bash
# Push this repo to GitHub from the Arena sandbox, self-healing after sandbox resets.
#
# Why this exists: the sandbox snapshot never persists .git/config (so `origin` and any
# credential embedded there vanish on reset) — but ~/.config/reels-studio/ DOES persist.
# That directory holds gh_token (the GitHub PAT) and git-askpass.sh (the credential shim).
# This wrapper restores the remote, rewires the shim, fetches, and pushes. Usage:
#
#   tools/git_push.sh            # push main
#   tools/git_push.sh main --force-with-lease
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
git config user.name >/dev/null 2>&1 || git config user.name zain
git config user.email >/dev/null 2>&1 || git config user.email zain@example.com
git remote get-url origin >/dev/null 2>&1 || git remote add origin https://github.com/zainkhan122/yt-tts.git
AP="$HOME/.config/reels-studio/git-askpass.sh"
test -f "$AP" || { echo "missing $AP — recreate the askpass shim (see ~/.config/reels-studio/)"; exit 1; }
GIT_ASKPASS="$AP" GIT_TERMINAL_PROMPT=0 git fetch -q origin
GIT_ASKPASS="$AP" GIT_TERMINAL_PROMPT=0 git push origin "${@:-main}"
