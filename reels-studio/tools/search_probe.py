#!/usr/bin/env python3
"""Search-demand probe: does anyone actually *search* for this topic?

The idea feed ranks topics by consensus (how many watchlist channels covered them),
but consensus ≠ search demand. A tool covered by two creators may still be
something nobody types into a search box. This module adds the missing signal:

  * fetch_suggestions(query)  -> real autocomplete results (Google/YouTube + DuckDuckGo)
  * searched_score(query)     -> 0-100 demand score from suggestion volume + intent modifiers

Both endpoints are free and need no API key. Results are cached to
research/search_cache.json so repeated runs in one session don't hammer the
network, and requests are spaced to stay polite.

Usage:
  python3 tools/search_probe.py "voice cloning"
  python3 tools/search_probe.py --json "CapCut alternative"
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "research" / "search_cache.json"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
MIN_INTERVAL = 0.6  # seconds between live requests

# Intent modifiers that signal a real searcher, not a browser.
HIGH_INTENT = re.compile(
    r"\b(alternative|vs|versus|free|tutorial|how to|how do i|review|best|cheapest|"
    r"self-hosted|open source|open-source|local|selfhost|setup|install|guide|"
    r"crack|keygen|premium|free tier|worth it|is it|does it|can it)\b",
    re.I,
)


def _load_cache() -> dict:
    if CACHE.exists():
        try:
            return json.loads(CACHE.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_cache(cache: dict) -> None:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    tmp = CACHE.with_suffix(".tmp")
    tmp.write_text(json.dumps(cache, indent=2, sort_keys=True) + "\n")
    tmp.replace(CACHE)


def _get(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
    return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "replace")


def _google_suggest(query: str, n: int = 10) -> list[str]:
    """Google Suggest (YouTube client). Returns JS-wrapped JSON; we parse the array out."""
    url = ("https://suggestqueries.google.com/complete/search?client=youtube&ds=yt&hl=en&q="
           + urllib.parse.quote(query))
    raw = _get(url)
    m = re.search(r"window\.google\.ac\.h\(\s*(\[.*?\])\s*\)\s*;?\s*$", raw, re.S)
    if not m:
        return []
    try:
        arr = json.loads(m.group(1))
        out = arr[1] if isinstance(arr, list) and len(arr) > 1 else []
        return [str(x[0]) for x in out if isinstance(x, list) and x][:n]
    except (json.JSONDecodeError, IndexError, TypeError):
        return []


def _ddg_suggest(query: str, n: int = 10) -> list[str]:
    """DuckDuckGo autocomplete (type=list) returns a plain JSON list of strings."""
    url = "https://duckduckgo.com/ac/?q=" + urllib.parse.quote(query) + "&type=list"
    raw = _get(url)
    try:
        arr = json.loads(raw)
        if isinstance(arr, list) and arr and isinstance(arr[0], list):
            return [str(x) for x in arr[1]][ :n]
        return [str(x) for x in arr][:n]
    except (json.JSONDecodeError, TypeError, IndexError):
        return []


def fetch_suggestions(query: str, n: int = 10, use_cache: bool = True) -> list[str]:
    """Return autocomplete suggestions for a query. Tries Google (YouTube) then DuckDuckGo."""
    query = query.strip()
    if not query:
        return []
    cache = _load_cache()
    key = query.lower()
    if use_cache and key in cache:
        return cache[key].get("suggestions", [])
    sugg = _google_suggest(query, n)
    if not sugg:
        time.sleep(MIN_INTERVAL)
        sugg = _ddg_suggest(query, n)
    if use_cache:
        cache[key] = {"suggestions": sugg, "ts": time.time()}
        _save_cache(cache)
    return sugg


def searched_score(query: str, suggestions: list[str] | None = None) -> dict:
    """0-100 demand score. Higher = more people search for it / with purchase/intent intent.

    Score is built from:
      * suggestion volume (more suggestions = more related queries exist)
      * share of suggestions carrying a high-intent modifier
      * a small bonus if the bare query itself is a high-intent phrase
    """
    if suggestions is None:
        suggestions = fetch_suggestions(query)
    if not suggestions:
        return {"score": 0, "suggestions": [], "note": "no autocomplete data (blocked or empty)"}
    high = [s for s in suggestions if HIGH_INTENT.search(s)]
    volume = min(len(suggestions), 10) / 10.0          # 0..1
    intent = (len(high) / len(suggestions)) if suggestions else 0.0
    base_intent = 0.25 if HIGH_INTENT.search(query) else 0.0
    score = round(100 * (0.5 * volume + 0.4 * intent + 0.1 * base_intent))
    return {"score": score, "suggestions": suggestions, "high_intent": high}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("query")
    ap.add_argument("--json", action="store_true", help="print machine-readable JSON")
    ap.add_argument("--no-cache", action="store_true")
    a = ap.parse_args()
    res = searched_score(a.query, fetch_suggestions(a.query, use_cache=not a.no_cache))
    if a.json:
        print(json.dumps(res, indent=2, sort_keys=True))
    else:
        print(f"query: {a.query}")
        print(f"score: {res['score']}")
        for s in res.get("suggestions", []):
            print(f"  - {s}")
        if res.get("note"):
            print(f"note: {res['note']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
