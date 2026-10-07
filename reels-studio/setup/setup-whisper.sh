#!/usr/bin/env bash
# Optional add-on to setup-sandbox.sh: speech-to-text for `hyperframes transcribe`.
#
# Why this exists: if whisper-cli is missing, the CLI builds whisper.cpp itself with
# `cmake --build build --config Release -j` (packages/cli/src/whisper/manager.ts) - no
# job limit. On a 2 vCPU / 2 GB box that spawns 10+ compilers, exhausts RAM and froze
# this sandbox for ~20 min. Here we build ONLY the whisper-cli target with a bounded
# job count, into the exact path the CLI checks first (so its auto-build never runs),
# and pre-download the model to the CLI's model cache.
#
# Everything lands in ~/.cache/hyperframes/whisper (excluded from workspace snapshots).
#
#   bash reels-studio/setup/setup-whisper.sh                    # -j1, small.en model (~490 MB)
#   JOBS=4 MODEL=base.en bash reels-studio/setup/setup-whisper.sh
#
# Then always transcribe with --no-runtime-install as a safety net:
#   hyperframes transcribe assets/audio/vo.wav --model small.en --no-runtime-install
set -euo pipefail
JOBS=${JOBS:-1}
MODEL=${MODEL:-small.en}
ROOT="$HOME/.cache/hyperframes/whisper"
SRC="$ROOT/whisper.cpp"
BIN="$SRC/build/bin/whisper-cli"
MODEL_FILE="$ROOT/models/ggml-$MODEL.bin"

if ! command -v cmake >/dev/null || ! command -v c++ >/dev/null; then
  echo "== apt: cmake + C/C++ compiler"
  sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq cmake build-essential >/dev/null
fi

if [ -x "$BIN" ]; then
  echo "== whisper-cli already built: $BIN"
else
  echo "== clone whisper.cpp (shallow)"
  rm -rf "$SRC"
  mkdir -p "$ROOT"
  git clone -q --depth 1 https://github.com/ggml-org/whisper.cpp.git "$SRC"
  echo "== build whisper-cli only, -j$JOBS (about 2 min at -j1 on 2 vCPU)"
  cmake -S "$SRC" -B "$SRC/build" -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_SHARED_LIBS=OFF -DWHISPER_BUILD_TESTS=OFF -DWHISPER_BUILD_SERVER=OFF >/dev/null
  cmake --build "$SRC/build" --config Release -j"$JOBS" --target whisper-cli
fi
echo "   whisper.cpp commit: $(git -C "$SRC" rev-parse --short HEAD 2>/dev/null || echo unknown)"

if [ -s "$MODEL_FILE" ]; then
  echo "== model present: $MODEL_FILE"
else
  echo "== download model ggml-$MODEL.bin"
  mkdir -p "$ROOT/models"
  curl -fL --retry 3 -s -S -o "$MODEL_FILE.part" \
    "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-$MODEL.bin"
  mv "$MODEL_FILE.part" "$MODEL_FILE"
fi

ls -la "$BIN" "$MODEL_FILE"
echo "WHISPER_DONE"
