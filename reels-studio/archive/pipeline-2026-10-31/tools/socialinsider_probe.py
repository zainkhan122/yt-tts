#!/usr/bin/env python3
"""
Socialinsider free-tools probe: 30-day public analytics for any public business
account on Instagram / Facebook / YouTube / TikTok — no login, no API key.

This fills the platform layer that yt-dlp cannot reach (Instagram/Facebook
competitor posts). Data per account: followers, engagement rate, avg likes /
comments / views, posts + posts/day, and the account's top posts (caption,
likes, engagement rate, media type, timestamp).

  python3 tools/socialinsider_probe.py ig:sebintel yt:@GithubSignals tk:github.signals fb:<page>
  -> research/social/platform-snapshots-<date>.json (+ printed summary)

Backend: the same free endpoint the public tools use
(POST https://free-tools.socialinsider.io/api, JSON-RPC style). It is async:
poll until the payload arrives. Be polite — a handful of accounts per run.
Public metrics only: no reach, saves, shares or watch time (owner-only data;
for our own accounts use Buffer Insights / tracker/performance.json instead).
"""
import datetime as dt
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://free-tools.socialinsider.io/api"
METHODS = {"ig": "ig_tools.free_tools", "fb": "fb_tools.free_tools",
           "yt": "yt_tools.free_tools", "tk": "tk_tools.free_tools"}
TODAY = dt.date.today().isoformat()


def probe(platform, handle, tool="free_social_media_analytics", tries=14):
    body = {"id": 1, "method": METHODS[platform],
            "params": {"handle": handle, "timezone": "Asia/Karachi", "tool": tool,
                       "auth": {"dashboardVersion": 1}}}
    data = json.dumps(body).encode()
    last = None
    for _ in range(tries):
        req = urllib.request.Request(API, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            last = json.loads(r.read().decode())
        if isinstance(last, dict) and len(json.dumps(last)) > 80 and "error" not in last:
            return last
        time.sleep(7)
    raise RuntimeError(f"{platform}:{handle}: no data ({str(last)[:160]})")


def val(node, key):
    x = (node or {}).get(key)
    return x.get("value") if isinstance(x, dict) else x


def summarise(platform, handle, d):
    tops = []
    for p in (d.get("top_posts") or [])[:3]:
        tops.append({"caption_first_line": (p.get("caption") or "").split("\n")[0][:140],
                     "likes": p.get("like_count"), "comments": p.get("comment_count"),
                     "engagement_rate": round(p.get("si_post_engagement_rate") or 0, 2),
                     "type": p.get("si_media_type"), "at": p.get("si_created_time")})
    return {"platform": platform, "handle": handle, "followers": val(d, "profile_followers"),
            "engagement_rate": val(d, "engagement_rate"), "avg_likes": val(d, "likes"),
            "avg_comments": val(d, "comments"), "total_views_30d": val(d, "views"),
            "posts_30d": val(d, "posts"), "posts_per_day": val(d, "average_post_per_day"),
            "top_posts": tops}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    out = []
    for spec in sys.argv[1:]:
        platform, handle = spec.split(":", 1)
        print(f"== {platform}:{handle} …", flush=True)
        try:
            d = probe(platform, handle)
        except Exception as exc:
            print(f"   FAILED {exc}")
            continue
        s = summarise(platform, handle, d)
        out.append(s)
        print(f"   followers={s['followers']} ER={round(s['engagement_rate'] or 0, 2)}% "
              f"avg_comments={s['avg_comments']} views30d={s['total_views_30d']} posts30d={s['posts_30d']}")
    path = ROOT / f"research/social/platform-snapshots-{TODAY}.json"
    if path.exists():  # merge repeat runs by (platform, handle) instead of clobbering
        old = json.loads(path.read_text())
        seen = {(s["platform"], s["handle"]) for s in out}
        out = out + [s for s in old if (s["platform"], s["handle"]) not in seen]
    path.write_text(json.dumps(out, indent=1))
    print(f"wrote {path} ({len(out)} accounts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
