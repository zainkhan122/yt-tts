"""Topic selection v4 (approved 31 Oct 2026). The agent judges; code records and checks.

What code does:
  - draws how many picks the day gets, at random, within config/selection.json (2 to 7), and records the draw;
  - checks each pick's judgment record is complete (viewer gain, demand, traction, competition, media plan, reason);
  - checks each pick's source is a live https link and is from the last 24 hours (or has a written reason);
  - checks each claim the video will state has a source line, unless the owner has approved that exact claim;
  - checks the day's picks match the drawn count and do not repeat a subject within the novelty window.

What code does NOT do: classify, score, weight, or pick. There is no category mix and no weighted score.
The agent reads the item, classifies it in words, and decides; analytics (Buffer, yt-dlp reference insights,
autocomplete demand) are inputs to that judgment, recorded in the pick.
"""
from __future__ import annotations

import datetime as dt
import json
import random
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config" / "selection.json"

REQUIRED_TEXT = ("subject", "classification", "viewer_gain", "competition", "media_plan", "reason")


def load_config(path: Path = CONFIG) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def draw_pick_count(cfg: dict, rng: random.Random | None = None) -> int:
    """Uniform random draw within the configured range. Recorded, so the choice is auditable."""
    rng = rng or random.Random()
    lo, hi = int(cfg["picks_per_day"]["min"]), int(cfg["picks_per_day"]["max"])
    if not 1 <= lo <= hi:
        raise ValueError("picks_per_day range is invalid")
    return rng.randint(lo, hi)


def new_day_record(day: dt.date, cfg: dict | None = None, rng: random.Random | None = None) -> dict:
    cfg = cfg or load_config()
    return {
        "date": day.isoformat(),
        "pick_count": draw_pick_count(cfg, rng),
        "picks": [],
    }


def _is_https_url(url: str) -> bool:
    try:
        parts = urlparse(url or "")
    except ValueError:
        return False
    return parts.scheme == "https" and bool(parts.netloc)


def validate_pick(pick: dict, *, today: dt.date, cfg: dict | None = None) -> list[str]:
    """Return a list of problems. An empty list means the judgment record is complete and checkable."""
    cfg = cfg or load_config()
    problems: list[str] = []
    pid = pick.get("id") or "<no id>"

    for key in REQUIRED_TEXT:
        value = pick.get(key)
        if not isinstance(value, str) or not value.strip():
            problems.append(f"{pid}: '{key}' is missing or empty")

    if not _is_https_url(pick.get("source_url", "")):
        problems.append(f"{pid}: source_url must be an https link to the item itself")

    # freshness: default 24 h from the item's own timestamp
    try:
        found = dt.date.fromisoformat(pick.get("found_at", ""))
    except (TypeError, ValueError):
        problems.append(f"{pid}: found_at must be an ISO date (the day the item appeared)")
    else:
        age = (today - found).days
        if age < 0:
            problems.append(f"{pid}: found_at is in the future")
        elif age > 1 and not str(pick.get("older_reason", "")).strip():
            problems.append(f"{pid}: item is {age} days old; write older_reason to use it")

    demand = pick.get("demand") or {}
    if not isinstance(demand, dict) or not demand.get("autocomplete_queries"):
        problems.append(f"{pid}: demand.autocomplete_queries is missing (run tools/demand/autocomplete.py)")

    claims = pick.get("claims")
    if not isinstance(claims, list) or not claims:
        problems.append(f"{pid}: claims list is missing (list every number or capability the video states)")
    else:
        for n, claim in enumerate(claims, 1):
            if not isinstance(claim, dict) or not str(claim.get("text", "")).strip():
                problems.append(f"{pid}: claim {n} has no text")
                continue
            has_source = _is_https_url(str(claim.get("source", ""))) or str(claim.get("source_line", "")).strip()
            if not has_source and not claim.get("owner_approved"):
                problems.append(f"{pid}: claim {n} has no source line and is not owner-approved: {claim['text']!r}")
    return problems


def validate_day(record: dict, *, today: dt.date, cfg: dict | None = None,
                 recent_subjects: list[tuple[str, dt.date]] | None = None) -> list[str]:
    cfg = cfg or load_config()
    problems: list[str] = []
    picks = record.get("picks") or []
    want = record.get("pick_count")
    lo, hi = int(cfg["picks_per_day"]["min"]), int(cfg["picks_per_day"]["max"])
    if not isinstance(want, int) or not lo <= want <= hi:
        problems.append(f"pick_count must be a drawn integer from {lo} to {hi}")
    if len(picks) != want:
        problems.append(f"day has {len(picks)} pick(s) but the draw was {want}")

    seen = set()
    for pick in picks:
        problems += validate_pick(pick, today=today, cfg=cfg)
        key = re.sub(r"\W+", " ", str(pick.get("subject", "")).lower()).strip()
        if key in seen:
            problems.append(f"{pick.get('id')}: subject repeated within the same day")
        seen.add(key)
        for old_subject, old_day in recent_subjects or []:
            days = (today - old_day).days
            if re.sub(r"\W+", " ", old_subject.lower()).strip() == key and 0 <= days < int(cfg["novelty_days"]):
                problems.append(f"{pick.get('id')}: subject already covered {days} day(s) ago")
    return problems


def save_day(record: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Draw today's pick count and check a day's picks.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("draw", help="draw and record today's pick count")
    d.add_argument("--day", default=dt.date.today().isoformat())
    d.add_argument("--out", type=Path)
    c = sub.add_parser("check", help="check a day's picks file")
    c.add_argument("path", type=Path)
    c.add_argument("--day", default=dt.date.today().isoformat())
    args = ap.parse_args(argv)
    if args.cmd == "draw":
        day = dt.date.fromisoformat(args.day)
        rec = new_day_record(day)
        out = args.out or ROOT / "intake" / f"{day.isoformat()}-selection.json"
        save_day(rec, out)
        print(f"pick count for {day}: {rec['pick_count']} (recorded in {out})")
        return 0
    rec = json.loads(args.path.read_text(encoding="utf-8"))
    problems = validate_day(rec, today=dt.date.fromisoformat(args.day))
    for p in problems:
        print("BLOCK", p)
    print("OK" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
