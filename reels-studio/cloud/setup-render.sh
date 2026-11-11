#!/usr/bin/env bash
# Render toolchain on a GitHub Actions ubuntu runner (4 vCPU / 16 GB, passwordless sudo).
# Same pinned stack as the sandbox (setup/setup-sandbox.sh): apt fonts + ffmpeg, Node 22 in /usr/local,
# hyperframes 0.8.137, Kokoro, Chrome headless shell; plus whisper-cli (QA gate) built with all cores.
# ~/.cache/hyperframes (Kokoro model, whisper build + model, browser) is restored by actions/cache.
# 2026-11-11 (F29): sections are timed + fail-closed with a marker, because an anonymous stall inside
# this script burned a full 60-minute voice job twice in one day (run 43045492141) with zero signal.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RS="$(dirname "$HERE")"
export HYPERFRAMES_NO_TELEMETRY=1 HYPERFRAMES_NO_UPDATE_CHECK=1 DO_NOT_TRACK=1 CI=1

section() { echo "TOOLCHAIN-SECTION $1 $(date -u +%T)"; }
runsec() { local name="$1"; local budget="$2"; shift 2; section "$name"; timeout "$budget" "$@" || { echo "TOOLCHAIN-STALL $name (budget ${budget}s)"; exit 24; }; }

runsec sandbox-stack 1200 bash "$RS/setup/setup-sandbox.sh"
export PATH=/usr/local/bin:$PATH   # Node 22 + hyperframes live in /usr/local (setup-sandbox.sh)
echo "== python deps + APPROVED VOICE stack (owner 2026-10-09: Chatterbox, voice-lab option 3)"
pipi() { python3 -m pip install -q "$@" 2>/dev/null || python3 -m pip install -q --break-system-packages "$@"; }
# Order matters: CPU torch first (no 2.5 GB CUDA wheels), then Chatterbox (pins numpy<2 on py3.12), then the rest.
# kokoro-onnx 0.6.1 (reference clip + previews) declares numpy>=2 but runs fine on 1.26 -> --no-deps + its real deps.
runsec pip-torch 1200 bash -c 'python3 -m pip install -q --progress-bar off torch==2.6.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cpu || python3 -m pip install -q --break-system-packages --progress-bar off torch==2.6.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cpu'
runsec pip-chatterbox 600 bash -c 'python3 -m pip install -q --progress-bar off chatterbox-tts==0.1.7 || python3 -m pip install -q --break-system-packages --progress-bar off chatterbox-tts==0.1.7'
runsec pip-voice-rest 420 bash -c 'python3 -m pip install -q --progress-bar off scipy soundfile pillow praat-parselmouth "espeakng-loader>=0.2.4" "phonemizer>=3.4.0" "onnxruntime>=1.20.1" && python3 -m pip install -q --progress-bar off --no-deps kokoro-onnx==0.6.1' || runsec pip-voice-rest-retry 420 bash -c 'python3 -m pip install -q --break-system-packages --progress-bar off scipy soundfile pillow praat-parselmouth "espeakng-loader>=0.2.4" "phonemizer>=3.4.0" "onnxruntime>=1.20.1" && python3 -m pip install -q --progress-bar off --no-deps kokoro-onnx==0.6.1'
python3 -c "import chatterbox, kokoro_onnx, numpy, torch; print('voice stack ok: torch', torch.__version__, 'numpy', numpy.__version__)"
echo "== Chatterbox weights pinned to the approved model revision (Hugging Face cache)"
runsec chatterbox-weights 900 env PYTHONPATH="$RS" python3 - <<'PY'
from pathlib import Path
from huggingface_hub import snapshot_download
from lib.pipeline import CHATTERBOX_MODEL_FILES, CHATTERBOX_MODEL_REPO, CHATTERBOX_MODEL_REVISION, verify_chatterbox_snapshot

model_dir = Path(snapshot_download(
    repo_id=CHATTERBOX_MODEL_REPO,
    revision=CHATTERBOX_MODEL_REVISION,
    allow_patterns=list(CHATTERBOX_MODEL_FILES),
))
verified = verify_chatterbox_snapshot(model_dir)
print(f"verified {len(verified)} Chatterbox model files: {CHATTERBOX_MODEL_REPO}@{CHATTERBOX_MODEL_REVISION}")
PY
echo "== whisper-cli for the intelligibility gate (all cores)"
runsec whisper-build 1200 env JOBS="$(nproc)" bash "$RS/setup/setup-whisper.sh"
echo "== Kokoro model (first run only; cached afterwards)"
if [ ! -f "$HOME/.cache/hyperframes/tts/models/kokoro-v1.0.onnx" ]; then
  runsec kokoro-warmup 420 bash -c 'hyperframes tts "warm up" -o /tmp/warmup.wav >/dev/null 2>&1 || true'
fi
ls -la "$HOME/.cache/hyperframes/tts/models/" 2>/dev/null | tail -2 || true
echo "== graphics engine: Playwright Chromium + system libraries (renderer=graphics)"
runsec playwright 900 bash -c 'python3 -m pip install -q "playwright==1.64.1" imageio-ffmpeg && python3 -m playwright install --with-deps chromium'
echo "CLOUD_SETUP_DONE nproc=$(nproc) mem=$(free -g | awk '/Mem/{print $2}')G"
