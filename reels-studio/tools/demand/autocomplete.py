#!/usr/bin/env python3
"""Demand probe from search autocomplete (decision 1, 31 Oct 2026).

For each search term, asks the public autocomplete endpoint what people type next. The result is
recorded as evidence for the pick's `demand` field:
  - suggestions: what autocomplete offers for the term (YouTube and web);
  - term_listed: whether the exact term appears in the suggestions (people are typing it);
  - breadth: how many suggestions share the term as a prefix (how many ways people search it).

LIMIT, stated on purpose: autocomplete shows that people search a term and how widely. It is NOT a
search-volume number. Do not write a volume figure in copy or in a pick; quote 'people type it' or
'many variations', and let the judgment do the rest.

Usage:
  python3 tools/demand/autocomplete.py "free deepseek" "edge0 mac" > out.json
  python3 tools/demand/autocomplete.py --file terms.txt --save intake/demand/2026-10-31.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ENDPOINT = "https://suggestqueries.google.com/complete/search"
SOURCES = {"youtube": {"client": "firefox", "ds": "yt"}, "web": {"client": "firefox"}}
TIMEOUT_S = 15


def fetch_suggestions(term: str, source: str, opener=urllib.request.urlopen) -> list[str]:
    params = dict(SOURCES[source], q=term)
    url = ENDPOINT + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (reels-studio demand probe)"})
    with opener(req, timeout=TIMEOUT_S) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    suggestions = data[1] if isinstance(data, list) and len(data) > 1 else []
    return [str(s) for s in suggestions if isinstance(s, str)]


def probe_term(term: str, opener=urllib.request.urlopen) -> dict:
    term = term.strip()
    if not term:
        raise ValueError("empty search term")
    out = {"term": term, "sources": {}}
    for source in SOURCES:
        try:
            sugg = fetch_suggestions(term, source, opener=opener)
        except Exception as exc:  # network or parse failure is recorded, never silent
            out["sources"][source] = {"error": f"{type(exc).__name__}: {exc}"}
            continue
        low = term.lower()
        out["sources"][source] = {
            "suggestions": sugg,
            "term_listed": any(s.lower() == low for s in sugg),
            "breadth": sum(1 for s in sugg if s.lower().startswith(low)),
        }
    return out


def probe(terms: list[str], opener=urllib.request.urlopen) -> dict:
    return {
        "probed_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "limit": "presence and breadth only; not search volume",
        "results": [probe_term(t, opener=opener) for t in terms if t.strip()],
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("terms", nargs="*")
    ap.add_argument("--file", type=Path, help="one search term per line")
    ap.add_argument("--save", type=Path, help="write the JSON here as well as printing it")
    args = ap.parse_args(argv)
    terms = list(args.terms)
    if args.file:
        terms += [line for line in args.file.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not terms:
        ap.print_usage()
        return 2
    report = probe(terms)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.save:
        args.save.parent.mkdir(parents=True, exist_ok=True)
        args.save.write_text(text + "\n", encoding="utf-8")
    print(text)
    failed = [r["term"] for r in report["results"] if any("error" in s for s in r["sources"].values())]
    if failed:
        print(f"warning: probe failed for {failed}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
