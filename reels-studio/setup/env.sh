# HyperFrames sandbox environment (source before running the CLI)
export HYPERFRAMES_NO_TELEMETRY=1      # telemetry opt-out
export HYPERFRAMES_NO_UPDATE_CHECK=1   # never self-upgrade: templates are validated on the pinned version
export DO_NOT_TRACK=1
export CI=1                            # non-interactive
export NO_COLOR=1
export HYPERFRAMES_EXTRACT_CACHE_DIR=/var/tmp/hf/cache   # /tmp is a small RAM tmpfs here
export TMPDIR=/var/tmp/hf/tmp
export PATH=/usr/local/bin:$PATH       # Node 22 + hyperframes CLI
