#!/usr/bin/env python3
"""Package pairing lint: the YouTube title and the cover text are ONE click surface.

Backed by vendored youtube-agent-skill/skills/yt-package/title.py (MIT). Our own gates cover the
title's SEO (seo_pack) and the cover's pixels (cover_rules); this lints the PAIRING — the failure
mode where the two surfaces repeat each other, or the title truncates/vagueness leaks through.

Blocking (wired into tools/ship.py, consulted before queue approval): duplicate wording across the
two surfaces, all-caps shouting, vague power-words, title over YouTube's hard 100 characters.
Advisory (surfaced in preflight as NOTEs): mobile 40-char cut, no number/name in the title,
front-loaded filler, thumbnail over 4 words (house cover rule allows 4-5, so theirs is advisory).
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "external" / "youtube-agent-skill"))
import title as _title  # noqa: E402

BLOCK_KEYS = {"duplicate", "shouting", "vague"}
ADVISORY_KEYS = {"mobile", "no-number", "front-load", "thumb-length"}
HARD = 100
DESKTOP = 60


def pairing(brief: dict, cover_text: str | None) -> dict | None:
    t = ((brief.get("seo") or {}).get("youtube") or {}).get("title") or ""
    if not t:
        return None
    return _title.check(t, cover_text)


def blocking_errors(res: dict) -> list[str]:
    errs = [f"package {k}: {m}" for k, m in res["issues"] if k in BLOCK_KEYS]
    if res["chars"] > HARD:
        errs.append(f"package length: {res['chars']} chars is over YouTube's hard {HARD}")
    return errs


def advisory_notes(res: dict) -> list[str]:
    out = [f"package {k}: {m}" for k, m in res["issues"] if k in ADVISORY_KEYS]
    if HARD >= res["chars"] > DESKTOP:
        out.append(f"package length: {res['chars']} chars — desktop search cuts near {DESKTOP}")
    return out


def cover_text_for(video_id: str, root: Path = ROOT) -> str | None:
    sel = root / "covers" / video_id / "selection.json"
    if not sel.exists():
        return None
    try:
        return json.loads(sel.read_text(encoding="utf-8")).get("text")
    except Exception:
        return None


def main():
    if len(sys.argv) < 2:
        print(__doc__); return 2
    brief = json.loads((ROOT / "briefs" / f"{Path(sys.argv[1]).stem}.json").read_text(encoding="utf-8"))
    res = pairing(brief, cover_text_for(brief["id"]))
    if res is None:
        print("no seo.youtube.title in brief"); return 1
    _title.show(res)
    errs, notes = blocking_errors(res), advisory_notes(res)
    for e in errs: print(" BLOCK", e)
    for n in notes: print(" note ", n)
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
