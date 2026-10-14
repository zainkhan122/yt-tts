#!/usr/bin/env bash
# Optional speech-to-text component used by `hyperframes transcribe` and the render QA gate.
#
# The CLI can otherwise build whisper.cpp itself with an unbounded `-j` count. Pin the
# source commit, bound compilation through JOBS, pin the model repository revision, and
# verify the complete model bytes before exposing the file at the CLI's cache path.
# All large files stay under ~/.cache/hyperframes/whisper, outside the checkout.
#
#   bash reels-studio/setup/setup-whisper.sh   # small.en only; JOBS defaults to 1
#
# To transcribe, keep --no-runtime-install set so the CLI cannot start an implicit build:
#   hyperframes transcribe assets/audio/vo.wav --model small.en --no-runtime-install
set -euo pipefail
JOBS=${JOBS:-1}
MODEL=${MODEL:-small.en}
WHISPER_TAG=v1.9.5
WHISPER_COMMIT=d1be6fde11ac6e0407606b4e42fe72d34add8037
MODEL_REVISION=5359861c739e955e79d9a303bcbc70fb988958b1
MODEL_SHA256=c6138d6d58ecc8322097e0f987c32f1be8bb0a18532a3f88f734d1bbf9c41e5d
MODEL_SHA1=db8a495a91d927739e50b3fc1cc4c6b8f6c2d022
MODEL_BYTES=487614201

if [[ "$MODEL" != "small.en" ]]; then
  echo "Only the independently verified small.en model is enabled; unsupported MODEL=$MODEL" >&2
  exit 2
fi
if ! [[ "$JOBS" =~ ^[1-9][0-9]*$ ]]; then
  echo "JOBS must be a positive integer, got: $JOBS" >&2
  exit 2
fi

ROOT="$HOME/.cache/hyperframes/whisper"
SRC="$ROOT/whisper.cpp"
BIN="$SRC/build/bin/whisper-cli"
BUILD_STAMP="$ROOT/whisper.cpp.build-commit"
MODEL_FILE="$ROOT/models/ggml-small.en.bin"
MODEL_URL="https://huggingface.co/ggerganov/whisper.cpp/resolve/$MODEL_REVISION/ggml-small.en.bin?download=true"
mkdir -p "$ROOT"

if ! command -v cmake >/dev/null || ! command -v c++ >/dev/null; then
  echo "== apt: cmake + C/C++ compiler"
  sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq cmake build-essential >/dev/null
fi

build_is_valid() {
  [ -x "$BIN" ] \
    && [ -f "$BUILD_STAMP" ] \
    && grep -Fxq "$WHISPER_COMMIT" "$BUILD_STAMP" \
    && [ "$(git -C "$SRC" rev-parse HEAD 2>/dev/null || true)" = "$WHISPER_COMMIT" ]
}

if build_is_valid; then
  echo "== pinned whisper-cli already built: $BIN"
else
  echo "== clone whisper.cpp $WHISPER_TAG and verify $WHISPER_COMMIT"
  rm -rf "$SRC"
  git clone -q --depth 1 --branch "$WHISPER_TAG" https://github.com/ggml-org/whisper.cpp.git "$SRC"
  ACTUAL_COMMIT=$(git -C "$SRC" rev-parse HEAD)
  if [ "$ACTUAL_COMMIT" != "$WHISPER_COMMIT" ]; then
    echo "whisper.cpp source commit mismatch: expected $WHISPER_COMMIT, got $ACTUAL_COMMIT" >&2
    exit 2
  fi
  echo "== build whisper-cli only, -j$JOBS"
  cmake -S "$SRC" -B "$SRC/build" -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_SHARED_LIBS=OFF -DWHISPER_BUILD_TESTS=OFF -DWHISPER_BUILD_SERVER=OFF >/dev/null
  cmake --build "$SRC/build" --config Release -j"$JOBS" --target whisper-cli
  printf '%s\n' "$WHISPER_COMMIT" > "$BUILD_STAMP.tmp"
  mv "$BUILD_STAMP.tmp" "$BUILD_STAMP"
fi
echo "   whisper.cpp commit: $(git -C "$SRC" rev-parse --short HEAD)"

model_is_valid() {
  [ -s "$MODEL_FILE" ] \
    && [ "$(stat -c '%s' "$MODEL_FILE")" = "$MODEL_BYTES" ] \
    && printf '%s  %s\n' "$MODEL_SHA256" "$MODEL_FILE" | sha256sum --check --status \
    && printf '%s  %s\n' "$MODEL_SHA1" "$MODEL_FILE" | sha1sum --check --status
}

if model_is_valid; then
  echo "== verified model present: $MODEL_FILE"
else
  echo "== download pinned ggml-small.en.bin ($MODEL_REVISION)"
  mkdir -p "$ROOT/models"
  rm -f "$MODEL_FILE" "$MODEL_FILE.part"
  curl --fail --location --retry 3 --silent --show-error --output "$MODEL_FILE.part" "$MODEL_URL"
  actual_bytes=$(stat -c '%s' "$MODEL_FILE.part")
  if [ "$actual_bytes" != "$MODEL_BYTES" ]; then
    echo "Whisper model size mismatch: expected $MODEL_BYTES bytes, got $actual_bytes" >&2
    rm -f "$MODEL_FILE.part"
    exit 2
  fi
  printf '%s  %s\n' "$MODEL_SHA256" "$MODEL_FILE.part" | sha256sum --check --status
  printf '%s  %s\n' "$MODEL_SHA1" "$MODEL_FILE.part" | sha1sum --check --status
  mv "$MODEL_FILE.part" "$MODEL_FILE"
fi

ls -la "$BIN" "$MODEL_FILE"
echo "WHISPER_DONE"
