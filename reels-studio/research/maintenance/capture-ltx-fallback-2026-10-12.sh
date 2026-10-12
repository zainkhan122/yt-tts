#!/usr/bin/env bash
# LTX-2.5 pack, fallback path: both ltx.io surfaces stall hyperframes' scroll loop (WebGL + looping
# media under the software renderer), so skip the site step entirely and build the pack from
# capture_extra's full-page screenshots + region map only.
set -u
cd /home/user/yt-tts/reels-studio
export REELS_DISMISS_CONSENT=1
LTX=/var/tmp/reels/captures/tool-ltx25-01
rm -rf "$LTX/site" "$LTX/extra"
mkdir -p "$LTX/empty-site" "$LTX/extra"
echo "== capture_extra: screenshots + region map (ltx.io/model/ltx-2-5)"
node tools/capture_extra.cjs https://ltx.io/model/ltx-2-5 "$LTX/extra" && echo "EXTRA_OK" || echo "EXTRA_FAILED"
echo "== curate pack from the extra outputs"
python3 tools/capture.py tool-ltx25-01 --url https://ltx.io/model/ltx-2-5 --reuse-site "$LTX/empty-site" --reuse-extra "$LTX/extra" && echo "OK: tool-ltx25-01" || echo "FAILED: tool-ltx25-01"
echo "LTX_FALLBACK_DONE"
