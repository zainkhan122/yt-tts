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
echo "== python deps + APPROVED VOICE stack (owner 2026-10-09: Chatterbox, voice-lab option 3)"
pipi() { python3 -m pip install -q "$@" 2>/dev/null || python3 -m pip install -q --break-system-packages "$@"; }
# Order matters: CPU torch first (no 2.5 GB CUDA wheels), then Chatterbox (pins numpy<2 on py3.12), then the rest.
# kokoro-onnx 0.6.1 (reference clip + previews) declares numpy>=2 but runs fine on 1.26 -> --no-deps + its real deps.
pipi torch==2.6.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cpu
pipi chatterbox-tts==0.1.7
pipi scipy soundfile pillow praat-parselmouth "espeakng-loader>=0.2.4" "phonemizer>=3.4.0" "onnxruntime>=1.20.1"
pipi --no-deps kokoro-onnx==0.6.1
python3 -c "import chatterbox, kokoro_onnx, numpy, torch; print('voice stack ok: torch', torch.__version__, 'numpy', numpy.__version__)"
echo "== Chatterbox weights (Hugging Face cache, restored by actions/cache after the first run)"
python3 -c "from chatterbox.tts import ChatterboxTTS; ChatterboxTTS.from_pretrained(device='cpu'); print('chatterbox weights ready')"
echo "== whisper-cli for the intelligibility gate (all cores)"
JOBS="$(nproc)" bash "$RS/setup/setup-whisper.sh"
echo "== Kokoro model (first run only; cached afterwards)"
if [ ! -f "$HOME/.cache/hyperframes/tts/models/kokoro-v1.0.onnx" ]; then
  hyperframes tts "warm up" -o /tmp/warmup.wav >/dev/null 2>&1 || true
fi
ls -la "$HOME/.cache/hyperframes/tts/models/" 2>/dev/null | tail -2 || true
echo "CLOUD_SETUP_DONE nproc=$(nproc) mem=$(free -g | awk '/Mem/{print $2}')G"
