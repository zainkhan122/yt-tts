#!/usr/bin/env bash
# One command after a session reset. Never touches Git, posts, secrets or approved media.
# Run `bash setup/restore-production.sh` for local graphic-review dependencies;
# add --full on a Python 3.12 / >=8 GB machine or an Actions runner for production voice.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [ "${1:-}" = '--full' ]; then
  if ! python3 -c 'import sys; assert sys.version_info[:2] == (3,12)' 2>/dev/null; then
    echo 'Full voice stack requires Python 3.12. Use the approved house-voice Actions workflow on small/reset sandboxes.' >&2; exit 2
  fi
  bash "$ROOT/cloud/setup-render.sh"
else
  python3 -m pip install 'playwright==1.64.1' imageio-ffmpeg pillow numpy soundfile requests
  python3 -m playwright install --with-deps chromium
  python3 - <<'PY'
import imageio_ffmpeg, PIL, playwright, numpy, soundfile
print('LOCAL REVIEW STACK READY:', imageio_ffmpeg.get_ffmpeg_exe())
PY
  echo 'Approved Chatterbox Option-3 voice: use Actions review-voice.yml; local preview is not a production render.'
fi
