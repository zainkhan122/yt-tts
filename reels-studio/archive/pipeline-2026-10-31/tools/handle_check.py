#!/usr/bin/env python3
"""Check social handle availability without logging in.

  handle_check.py name1 name2 ...      -> table: YouTube / TikTok / Instagram  (free | TAKEN | ?)
  handle_check.py --no-ig name1 ...    -> skip Instagram (fast pass; then IG-check only the shortlist)

YouTube: /@handle returns 404 when free. TikTok: the profile page embeds a user-detail statusCode
(0 = exists, 10221/10202 = no such user), which is more reliable than "has videos". Instagram: public mobile
web_profile_info endpoint (404 = free, 200 = taken); if rate-limited it prints "?" (check by hand).
"""
import json
import re
import sys
import time
import urllib.error
import urllib.request

IG_UA = ("Instagram 219.0.0.12.117 Android (31/12; 480dpi; 1080x2400; samsung; SM-G991B; o1s; exynos2100; en_US; 346138365)")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"


def _get(url, headers=None, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception:
        return 0, ""


def youtube(h):
    s, _ = _get(f"https://www.youtube.com/@{h}")
    return "free" if s == 404 else "TAKEN" if s == 200 else "?"


def tiktok(h):
    s, html = _get(f"https://www.tiktok.com/@{h}")
    m = re.search(r'"webapp\.user-detail":\{.*?"statusCode":(\d+)', html, re.S)
    if m:
        code = int(m.group(1))
        return "TAKEN" if code in (0, 10222) else "free" if code in (10221, 10202) else f"?{code}"  # 10222 = private account (exists)
    if f'"uniqueId":"{h}"' in html.lower() or f'"uniqueid":"{h}"' in html.lower():
        return "TAKEN"
    return "?"


def instagram(h):
    s, body = _get(f"https://i.instagram.com/api/v1/users/web_profile_info/?username={h}",
                   {"User-Agent": IG_UA, "x-ig-app-id": "567067343352427", "Accept": "*/*"})
    for wait in (30, 60):  # Instagram rate-limits datacenter IPs quickly: back off and retry
        if s != 429:
            break
        time.sleep(wait)
        s, body = _get(f"https://i.instagram.com/api/v1/users/web_profile_info/?username={h}",
                       {"User-Agent": IG_UA, "x-ig-app-id": "567067343352427", "Accept": "*/*"})
    if s == 404:
        return "free"
    if s == 200:
        try:
            return "TAKEN" if json.loads(body).get("data", {}).get("user") else "free"
        except Exception:
            return "?"
    return "?"


def main(names):
    ig = "--no-ig" not in names
    names = [n for n in names if not n.startswith("--")]
    print(f"{'handle':16s} {'YouTube':8s} {'TikTok':8s} {'Instagram':9s} len")
    for h in names:
        h = h.lower().lstrip("@")
        r = (youtube(h), tiktok(h), instagram(h) if ig else "-")
        print(f"@{h:15s} {r[0]:8s} {r[1]:8s} {r[2]:9s} {len(h)}", flush=True)
        time.sleep(1.2)


if __name__ == "__main__":
    main(sys.argv[1:])
