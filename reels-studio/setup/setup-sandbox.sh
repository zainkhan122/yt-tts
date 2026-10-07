#!/usr/bin/env bash
# Re-create the HyperFrames toolchain on a fresh Debian/Ubuntu sandbox.
# System installs (Node, FFmpeg, Chrome, models) are NOT part of the saved workspace,
# so run this after a restore. Everything large is downloaded OUTSIDE /home/user.
#
#   bash reels-studio/setup/setup-sandbox.sh                   # render toolchain
#   bash reels-studio/bootstrap.sh    # + speech-to-text (setup-whisper.sh)
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # resolve before any cd
export DEBIAN_FRONTEND=noninteractive

echo "== apt: ffmpeg, fonts, Chrome shared libraries"
sudo DEBIAN_FRONTEND=noninteractive apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ffmpeg fonts-noto-color-emoji fonts-liberation fonts-dejavu-core \
  libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libatspi2.0-0 \
  libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2 >/dev/null

echo "== Node 22 (hyperframes requires >= 22)"
if ! node --version 2>/dev/null | grep -q '^v2[2-9]'; then
  mkdir -p /var/tmp/hf && cd /var/tmp/hf
  BASE=https://nodejs.org/dist/latest-v22.x
  LINE=$(curl -fsSL "$BASE/SHASUMS256.txt" | grep 'linux-x64.tar.xz$')
  SUM=${LINE%% *}; FILE=${LINE##* }
  curl -fsSLO "$BASE/$FILE"
  echo "$SUM  $FILE" | sha256sum -c -
  sudo tar -xJf "$FILE" -C /usr/local --strip-components=1
fi
export PATH=/usr/local/bin:$PATH
node --version

echo "== HyperFrames CLI (pinned) + local TTS runtime"
sudo rm -rf /usr/local/lib/node_modules/.hyperframes-* 2>/dev/null || true   # stale temp dir from an interrupted self-update breaks reinstall (ENOTEMPTY)
sudo env HYPERFRAMES_NO_TELEMETRY=1 HYPERFRAMES_NO_UPDATE_CHECK=1 DO_NOT_TRACK=1 npm i -g hyperframes@0.8.137 --no-fund --no-audit >/dev/null
pip install -q kokoro-onnx soundfile praat-parselmouth 2>/dev/null || pip install -q --break-system-packages kokoro-onnx soundfile praat-parselmouth

echo "== Chrome headless shell + checks"
export HYPERFRAMES_NO_TELEMETRY=1 HYPERFRAMES_NO_UPDATE_CHECK=1 DO_NOT_TRACK=1 CI=1
hyperframes telemetry disable >/dev/null 2>&1 || true
hyperframes browser ensure 2>&1 | tail -3
sudo mkdir -p /var/tmp/hf/cache /var/tmp/hf/tmp && sudo chown -R "$(id -u):$(id -g)" /var/tmp/hf
hyperframes --version
if [ "${WITH_WHISPER:-0}" = "1" ]; then
  bash "$HERE/setup-whisper.sh"
else
  echo "(optional) speech-to-text for 'hyperframes transcribe': bash $HERE/setup-whisper.sh"
fi
echo "SETUP_DONE"
