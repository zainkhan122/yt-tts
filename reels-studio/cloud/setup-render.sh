#!/usr/bin/env bash
# Render toolchain on a GitHub Actions ubuntu runner (4 vCPU / 16 GB, passwordless sudo).
# Same pinned stack as the sandbox (setup/setup-sandbox.sh): apt fonts + ffmpeg, Node 22 in /usr/local,
# hyperframes 0.8.137, Kokoro, Chrome headless shell; plus whisper-cli (QA gate) built with all cores.
# ~/.cache/hyperframes (Kokoro model, whisper build + model, browser) is restored by actions/cache.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RS="$(dirname "$HERE")"
export HYPERFRAMES_NO_TELEMETRY=1 HYPERFRAMES_NO_UPDATE_CHECK=1 DO_NOT_TRACK=1 CI=1
bash "$RS/setup/setup-sandbox.sh"
export PATH=/usr/local/bin:$PATH   # Node 22 + hyperframes live in /usr/local (setup-sandbox.sh)
echo "== python deps"
PKGS="numpy scipy soundfile pillow kokoro-onnx praat-parselmouth"
python3 -m pip install -q $PKGS 2>/dev/null || python3 -m pip install -q --break-system-packages $PKGS
echo "== whisper-cli for the intelligibility gate (all cores)"
JOBS="$(nproc)" bash "$RS/setup/setup-whisper.sh"
echo "== Kokoro model (first run only; cached afterwards)"
if [ ! -f "$HOME/.cache/hyperframes/tts/models/kokoro-v1.0.onnx" ]; then
  hyperframes tts "warm up" -o /tmp/warmup.wav >/dev/null 2>&1 || true
fi
ls -la "$HOME/.cache/hyperframes/tts/models/" 2>/dev/null | tail -2 || true
echo "CLOUD_SETUP_DONE nproc=$(nproc) mem=$(free -g | awk '/Mem/{print $2}')G"
