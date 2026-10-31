#!/usr/bin/env python3
"""Need mining: find unmet viewer questions in reference-channel comments.

The idea feed ranks topics by consensus (how many channels covered them) and the
search probe ranks by demand (how many people search for them). This module adds
the third signal: *need*. Viewers leave questions in comments ("how do I...",
"is there a tool that...", "can it...") when a workflow they care about is
unmet. Mining those questions tells us what problems people are actually
trying to solve, so we can pick topics that answer a real need.

  python3 tools/need_miner.py --channels github.awesome,github.signals --per-channel 3
  python3 tools/need_miner.py --json   # machine-readable

Uses yt-dlp (free, no key) to list recent videos and pull top comments. Results
are cached to research/need_cache.json. Falls back gracefully when comments are
unavailable (disabled, bot-blocked, or zero comments).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "research" / "need_cache.json"

# Question patterns that signal an unmet workflow, not a generic comment.
QUESTION = re.compile(
    r"\b(how (do|can|to) i|how would i|is there (a|an|any)|is it possible|"
    r"can it|can you|why (doesn't|does not|isn't)|does it (support|work with|do)|"
    r"will it|alternative to|instead of|replace(s)?|free (alternative|version)|"
    r"self-host|self host|without (api|login|signup|sign-up)|"
    r"run (it )?local(ly)?|on (my|a) (mac|linux|windows|pc))\b",
    re.I,
)
# Topic-ish nouns that help group questions by subject.
TOPIC_HINT = re.compile(
    r"\b(tool|repo|api|model|agent|plugin|extension|script|app|software|"
    r"claude|chatgpt|cursor|codex|gemini|llm|rag|mcp|whisper|tts|stt|"
    r"video|image|audio|voice|pdf|data|database|docker|kubernetes)\b",
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


def _ytdlp_json(args: list[str], timeout: int = 120) -> dict | None:
    p = subprocess.run(["yt-dlp", *args, "--no-warnings", "-J"], capture_output=True, text=True, timeout=timeout)
    if p.returncode or not p.stdout.strip():
        return None
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        return None


def list_recent(channel_url: str, n: int = 3) -> list[dict]:
    """Latest shorts/videos of a channel as {url, title, views, comment_count}."""
    info = _ytdlp_json(["--flat-playlist", "--playlist-end", str(n), channel_url])
    if not info:
        return []
    entries = info.get("entries") or []
    out = []
    for e in entries:
        if not e:
            continue
        url = e.get("url") or (f"https://www.youtube.com/shorts/{e['id']}" if e.get("id") else "")
        out.append({"url": url, "title": e.get("title") or "",
                    "views": e.get("view_count") or 0, "id": e.get("id") or ""})
    return out


def top_comments(video_url: str, n: int = 40) -> list[str]:
    """Top comments on one video as plain text. Returns [] if unavailable."""
    info = _ytdlp_json(["--skip-download", "--write-comments", "--playlist-end", "1", video_url])
    if not info:
        return []
    entries = info.get("entries") or []
    if not entries:
        # single video dump: comments live at top level
        comment_blocks = info.get("comments") or []
    else:
        e0 = entries[0] or {}
        comment_blocks = e0.get("comments") or []
    out = []
    for c in comment_blocks[:n]:
        txt = (c.get("text") or "").strip()
        if txt:
            out.append(txt)
    return out


def mine(channels: list[str], per_channel: int = 3, use_cache: bool = True) -> dict:
    """Mine need questions across channels. Returns {topic_hint: {questions: [...], channels: set, count}}."""
    cache = _load_cache() if use_cache else {}
    by_topic: dict[str, dict] = {}
    total_comments = 0
    total_questions = 0
    for ch in channels:
        ch_key = ch.lower()
        ch_cache = cache.get(ch_key, {})
        if use_cache and ch_cache.get("videos"):
            videos = ch_cache["videos"]
        else:
            videos = list_recent(f"https://www.youtube.com/@{ch}/shorts", per_channel)
            if use_cache:
                cache[ch_key] = {"videos": videos, "ts": time.time()}
        for v in videos:
            vk = v["url"]
            vcache = (cache.get(ch_key, {}).get("comments") or {}).get(vk)
            if use_cache and vcache is not None:
                comments = vcache
            else:
                comments = top_comments(vk)
                if use_cache:
                    c = cache.setdefault(ch_key, {})
                    c.setdefault("comments", {})[vk] = comments
                    c["videos"] = videos
                    c["ts"] = time.time()
            if not comments:
                continue
            total_comments += len(comments)
            for c in comments:
                if not QUESTION.search(c):
                    continue
                total_questions += 1
                hints = set(m.group(0).lower() for m in TOPIC_HINT.finditer(c)) or {"general"}
                for h in hints:
                    bucket = by_topic.setdefault(h, {"questions": [], "channels": set(), "count": 0})
                    bucket["questions"].append(c[:160])
                    bucket["channels"].add(ch)
                    bucket["count"] += 1
    if use_cache:
        _save_cache(cache)
    return {"by_topic": by_topic, "total_comments": total_comments, "total_questions": total_questions}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--channels", default="GithubAwesome,intheworldofai,mreflow,matthew_berman",
                    help="comma-separated YouTube handles (from sources.csv)")
    ap.add_argument("--per-channel", type=int, default=3)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-cache", action="store_true")
    a = ap.parse_args()
    chs = [c.strip() for c in a.channels.split(",") if c.strip()]
    res = mine(chs, a.per_channel, use_cache=not a.no_cache)
    ranked = sorted(res["by_topic"].items(), key=lambda kv: -kv[1]["count"])
    if a.json:
        out = {"channels": chs, "total_comments": res["total_comments"],
               "total_questions": res["total_questions"],
               "topics": [{"hint": h, "count": d["count"], "channels": sorted(d["channels"]),
                            "questions": d["questions"][:5]} for h, d in ranked]}
        print(json.dumps(out, indent=2, sort_keys=True))
    else:
        print(f"channels: {chs}")
        print(f"comments scanned: {res['total_comments']} | questions found: {res['total_questions']}")
        print()
        for h, d in ranked[:20]:
            print(f"[{d['count']}] {h} ({', '.join(sorted(d['channels']))})")
            for q in d["questions"][:3]:
                print(f"    - {q}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
