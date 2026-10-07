#!/usr/bin/env bash
# Per-engine dependencies for cloud/tts_audition.py on a GitHub Actions ubuntu runner (CPU only).
# CPU-only torch via the PyTorch CPU index (avoids ~3 GB of CUDA wheels). "+cpu" builds win version ties.
set -euo pipefail
E="${1:?engine}"
PIP="python -m pip install --progress-bar off --prefer-binary"
CPU="--extra-index-url https://download.pytorch.org/whl/cpu"
python -m pip install --progress-bar off -U pip wheel setuptools >/dev/null
free_disk() {  # runners ship ~14 GB free; drop unused toolchains (+~25 GB) before multi-GB checkpoints
  sudo rm -rf /usr/share/dotnet /usr/local/lib/android /opt/ghc /opt/hostedtoolcache/CodeQL /usr/local/.ghcup || true
  df -h / | tail -1
}
case "$E" in
  chatterbox|turbo) $PIP $CPU chatterbox-tts soundfile ;;
  qwen3)   free_disk; $PIP $CPU qwen-tts soundfile ;;
  orpheus) $PIP orpheus-cpp soundfile scipy
           $PIP llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu ;;
  edge)    $PIP edge-tts soundfile ;;
  score)   sudo apt-get update -qq && sudo apt-get install -y -qq ffmpeg >/dev/null
           $PIP $CPU torch torchaudio faster-whisper soundfile librosa jiwer ;;
  *) echo "unknown engine $E"; exit 2 ;;
esac
python -m pip list 2>/dev/null | grep -i -E "^(torch|torchaudio|chatterbox|qwen|orpheus|llama|edge|faster)" || true
