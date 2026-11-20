#!/usr/bin/env bash
# Restore only the approved CPU voice + pinned speech QA on a large runner.
# Does not apt-update, install browsers or touch publishing. Uses Actions caches.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
python3 -c 'import sys; assert sys.version_info[:2] == (3,12), "Voice stack requires Python 3.12"'
if ! command -v ffmpeg >/dev/null; then
  python3 -m pip install -q --progress-bar off imageio-ffmpeg
  mkdir -p "$HOME/.local/bin"
  FFMPEG="$(python3 -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')"
  ln -sf "$FFMPEG" "$HOME/.local/bin/ffmpeg"
  export PATH="$HOME/.local/bin:$PATH"
  if [ -n "${GITHUB_PATH:-}" ]; then echo "$HOME/.local/bin" >> "$GITHUB_PATH"; fi
fi
for exe in ffmpeg git cmake c++ curl; do command -v "$exe" >/dev/null || { echo "Missing runner dependency: $exe" >&2; exit 2; }; done
export PIP_DISABLE_PIP_VERSION_CHECK=1 HYPERFRAMES_NO_TELEMETRY=1 HYPERFRAMES_NO_UPDATE_CHECK=1 DO_NOT_TRACK=1
if ! python3 -c 'import torch,torchaudio' 2>/dev/null; then
 timeout 1200 python3 -m pip install -q --progress-bar off --timeout 60 --retries 3 --index-url https://download.pytorch.org/whl/cpu 'torch>=2.6,<3' torchaudio
fi
timeout 600 python3 -m pip install -q --progress-bar off chatterbox-tts==0.1.7 scipy soundfile pillow praat-parselmouth
python3 -c 'import torch, torchaudio, chatterbox, scipy, soundfile, parselmouth; print("approved voice dependencies ready")'
PYTHONPATH="$ROOT" python3 - <<'PY'
from pathlib import Path
from huggingface_hub import snapshot_download
from lib.pipeline import CHATTERBOX_MODEL_FILES, CHATTERBOX_MODEL_REPO, CHATTERBOX_MODEL_REVISION, verify_chatterbox_snapshot
p=Path(snapshot_download(repo_id=CHATTERBOX_MODEL_REPO,revision=CHATTERBOX_MODEL_REVISION,allow_patterns=list(CHATTERBOX_MODEL_FILES)))
verify_chatterbox_snapshot(p);print('approved voice weights verified')
PY
JOBS="$(nproc)" bash "$ROOT/setup/setup-whisper.sh"
echo 'VOICE_SETUP_DONE'
