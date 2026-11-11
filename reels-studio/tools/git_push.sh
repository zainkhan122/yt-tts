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
chmod +x "$AP" 2>/dev/null || true
test -f "$AP" || { echo "missing $AP — recreate the askpass shim (see ~/.config/reels-studio/)"; exit 1; }
# history is blob-filtered locally (remote carries GBs of legacy video packs);
# keep the filter on every fetch or a plain fetch starts a multi-GB backfill
GIT_ASKPASS="$AP" GIT_TERMINAL_PROMPT=0 git fetch -q --filter=blob:none origin
if ! GIT_ASKPASS="$AP" GIT_TERMINAL_PROMPT=0 git push origin "${@:-main}"; then
  echo "push non-fast-forward — cloud bots advance main; rebasing and retrying once"
  GIT_ASKPASS="$AP" GIT_TERMINAL_PROMPT=0 git fetch -q --filter=blob:none origin main
  git rebase origin/main
  GIT_ASKPASS="$AP" GIT_TERMINAL_PROMPT=0 git push origin "${@:-main}"
fi
