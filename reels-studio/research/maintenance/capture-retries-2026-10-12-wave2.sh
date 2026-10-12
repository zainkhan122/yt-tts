#!/usr/bin/env bash
# Wave-2 capture repairs, run one at a time (2 GB sandbox: never two heavy captures in parallel).
#   1 higgsfield  -> fresh extra pass with consent dismissal (site capture reused)
#   2 sol         -> fresh extra pass with the generalized region harvest (site capture reused)
#   3 clef        -> fresh extra pass with the generalized region harvest (site capture reused)
#   4 ltx-2.5     -> full re-capture on the dedicated model page (ltx.studio is a WebGL app that
#                    stalls hyperframes' scroll loop; ltx.io/model/ltx-2-5 is the announcement surface)
set -u
cd /home/user/yt-tts/reels-studio
export REELS_DISMISS_CONSENT=1
run() { echo; echo "########## CAPTURE $1"; python3 tools/capture.py "$1" "${@:2}" && echo "OK: $1" || echo "FAILED: $1"; }
# keep the previous extra outputs aside so a half-failed rerun can never mix stale screenshots in
[ -d /var/tmp/reels/captures/news-gpt61-sol-01/extra ] && mv /var/tmp/reels/captures/news-gpt61-sol-01/extra /var/tmp/reels/captures/news-gpt61-sol-01/extra.prev
[ -d /var/tmp/reels/captures/news-clef-01/extra ] && mv /var/tmp/reels/captures/news-clef-01/extra /var/tmp/reels/captures/news-clef-01/extra.prev
run tool-higgsfield-01  --url https://higgsfield.ai/creator-hub/changelog --reuse-site /var/tmp/reels/captures/tool-higgsfield-01/site
run news-gpt61-sol-01   --url https://developers.openai.com/api/docs/models/gpt-6.1-sol --reuse-site /var/tmp/reels/captures/news-gpt61-sol-01/site
run news-clef-01        --url https://huggingface.co/Cloudflare/clef --reuse-site /var/tmp/reels/captures/news-clef-01/site
run tool-ltx25-01       --url https://ltx.io/model/ltx-2-5
echo; echo "WAVE2_RETRIES_DONE"
