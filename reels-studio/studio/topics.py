"""Topic selection (v3): choose what to make next from judged candidates, never from a template.

Responsibilities, in order:
  1. Discovery adds candidates with a category derived from where they came from
     (github.com -> repo; a provider/launch/news page -> tool or news). Unknown -> "unclassified",
     which is never ranked until someone classifies it.
  2. The writer judges each candidate: `value` (0-5) and the reasons in `notes`. The engine
     does not invent value.
  3. This engine ranks only judged, classified, sourced, unblocked candidates. It balances the
     categories against the channel mix, favours fresh and provable topics, and gives an urgency
     bonus to real deadlines (free credits and offers expire).
  4. Ranking is refused unless a reference-channel study is recent (GUIDELINES §6).

Nothing here looks at a `type`/template field. Selection is by value, proof and balance.
"""
import argparse
import csv
import dataclasses
import datetime as dt
import json
import math
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
CATEGORIES = ("tool", "news", "repo")


class StudyMissing(RuntimeError):
    """No reference-channel study recent enough to justify choosing topics."""


@dataclasses.dataclass
class Candidate:
    id: str
    subject: str
    category: str
    source_url: str
    found_at: dt.date
    value: float | None = None          # 0-5, writer's judgment; None = not judged yet
    proof_assets: int = 0               # usable real media the writer has verified
    official_source: bool = False
    deadline: dt.date | None = None
    risk_flags: tuple = ()
    notes: str = ""


@dataclasses.dataclass
class Pick:
    id: str
    subject: str
    category: str
    score: float
    reasons: list


def category_from_url(url):
    """Where a candidate was found decides its category. Unknown hosts stay unclassified."""
    host = urlparse(url).netloc.lower().removeprefix("www.")
    if host == "github.com":
        return "repo"
    if host in {"huggingface.co"}:
        return "tool"
    return "unclassified"


def load_config(path=ROOT / "config" / "topic-mix.json"):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def check_study(study_date, today, max_age_days):
    if study_date is None:
        raise StudyMissing("no reference-channel study on file; run the study before choosing topics")
    age = (today - study_date).days
    if age < 0 or age > max_age_days:
        raise StudyMissing(f"reference-channel study is {age} days old (limit {max_age_days}); refresh it first")


def category_shares(recent, categories_cfg, window_days, today):
    """Share of recent publications per category. recent: iterable of (category, date, subject)."""
    counts = Counter()
    for cat, day, *_ in recent:
        if cat in CATEGORIES and 0 <= (today - day).days < window_days:
            counts[cat] += 1
    total = sum(counts.values())
    return {c: (counts[c] / total if total else 0.0) for c in CATEGORIES}


def _novelty_blocked(cand, recent, today, days):
    return any(subject == cand.subject and 0 <= (today - day).days < days for _, day, subject in recent)


def score_candidate(cand, shares, cfg, today):
    """Return (score, reasons) for one judged candidate."""
    w = cfg["weights"]
    reasons = []
    value_part = (cand.value or 0) / 5.0
    reasons.append(f"value {cand.value}/5")

    age = max(0, (today - cand.found_at).days)
    fresh = math.exp(-age / cfg["freshness_half_life_days"]) if cfg["freshness_half_life_days"] else 0.0
    reasons.append(f"fresh {fresh:.2f} ({age}d)")

    proof = min(1.0, cand.proof_assets / 3.0) + (0.2 if cand.official_source else 0.0)
    proof = min(1.0, proof)
    reasons.append(f"proof {cand.proof_assets} real asset(s){', official source' if cand.official_source else ''}")

    urgency = 0.0
    if cand.deadline:
        left = (cand.deadline - today).days
        urgency = 1.0 if left <= 3 else 0.6 if left <= 7 else 0.2 if left <= 21 else 0.0
        reasons.append(f"deadline in {left}d")

    target = cfg["categories"][cand.category]["target"]
    gap = target - shares.get(cand.category, 0.0)          # positive = under-represented
    balance01 = (max(-0.3, min(0.3, gap)) / 0.3 + 1) / 2   # 0..1, 0.5 when exactly on target
    reasons.append(f"mix {cand.category}: {shares.get(cand.category, 0):.0%} vs target {target:.0%}")

    score = (w["value"] * value_part + w["freshness"] * fresh + w["proof"] * proof
             + w["urgency"] * urgency + w["balance"] * balance01)
    return round(score, 4), reasons


def rank(candidates, recent, study_date, today, cfg=None, n=8):
    """Return (picks, skipped). Raises StudyMissing if the study is not current."""
    cfg = cfg or load_config()
    check_study(study_date, today, cfg["study_max_age_days"])
    recent = list(recent)  # (category, date, subject)
    shares = category_shares(recent, cfg["categories"], cfg["window_days"], today)
    skipped = []
    pool = []
    for c in candidates:
        if c.category not in CATEGORIES:
            skipped.append((c.id, "unclassified: classify the source before it can be ranked"))
            continue
        if c.value is None:
            skipped.append((c.id, "not judged: writer must set value 0-5 after the study"))
            continue
        if not c.source_url.startswith("https://"):
            skipped.append((c.id, "no https source"))
            continue
        blocked = sorted(set(c.risk_flags) & set(cfg["blocking_risk_flags"]))
        if blocked:
            skipped.append((c.id, "blocked: " + ", ".join(blocked)))
            continue
        if c.deadline and c.deadline < today:
            skipped.append((c.id, f"expired on {c.deadline}"))
            continue
        if _novelty_blocked(c, recent, today, cfg["novelty_block_days"]):
            skipped.append((c.id, f"covered within {cfg['novelty_block_days']} days"))
            continue
        pool.append(c)

    picks = []
    remaining = sorted(pool, key=lambda c: c.id)
    while remaining and len(picks) < n:
        scored = []
        for c in remaining:
            s, why = score_candidate(c, shares, cfg, today)
            scored.append((s, c, why))
        scored.sort(key=lambda x: (-x[0], x[1].id))
        chosen = None
        for s, c, why in scored:
            run = [p.category for p in picks[-cfg["max_consecutive_same_category"]:]]
            if len(run) == cfg["max_consecutive_same_category"] and all(r == c.category for r in run):
                continue  # category run limit reached; try the next candidate
            chosen = (s, c, why)
            break
        if chosen is None:
            break
        s, c, why = chosen
        picks.append(Pick(c.id, c.subject, c.category, s, why))
        remaining = [x for x in remaining if x.id != c.id]
        # the mix shifts after each pick, so recompute shares with the new pick counted as recent
        shares = category_shares(recent + [(p.category, today, p.subject) for p in picks], cfg["categories"],
                                 cfg["window_days"], today)
    return picks, skipped


def load_candidates(path):
    out = []
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            value = row.get("value", "").strip()
            deadline = row.get("deadline", "").strip()
            out.append(Candidate(
                id=row["id"], subject=row.get("subject") or row["id"], category=row.get("category") or "unclassified",
                source_url=row.get("source_url", ""), found_at=dt.date.fromisoformat(row["found_at"]),
                value=float(value) if value else None,
                proof_assets=int(row.get("proof_assets") or 0),
                official_source=(row.get("official_source") or "").lower() == "yes",
                deadline=dt.date.fromisoformat(deadline) if deadline else None,
                risk_flags=tuple(x.strip() for x in (row.get("risk_flags") or "").split(";") if x.strip()),
                notes=row.get("notes", ""),
            ))
    return out


def recent_from_publications(path, today, window_days=60):
    """(category, date, subject) for each published or scheduled video, from the publication journal."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))["records"]
    seen = {}
    for key, rec in data.items():
        video_id = key.split(":")[0]
        if rec.get("state") not in ("sent", "scheduled", "sent_pending_verification"):
            continue
        when = (rec.get("due_at") or rec.get("sent_at") or "")[:10]
        if not when:
            continue
        day = dt.date.fromisoformat(when)
        if 0 <= (today - day).days < window_days:
            seen.setdefault(video_id, day)
    out = []
    for video_id, day in seen.items():
        prefix = video_id.split("-")[0]
        cat = {"repo": "repo", "news": "news", "tool": "tool", "model": "tool"}.get(prefix, "unclassified")
        out.append((cat, day, video_id))
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description="Rank judged candidates (never by template).")
    p.add_argument("--candidates", default=str(ROOT / "topics" / "candidates.csv"))
    p.add_argument("--publications", default=str(ROOT / "tracker" / "publications.json"))
    p.add_argument("--study-date", required=True, help="YYYY-MM-DD of the latest reference-channel study")
    p.add_argument("--today", default=None)
    p.add_argument("-n", type=int, default=8)
    a = p.parse_args(argv)
    today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
    cands = load_candidates(a.candidates)
    recent = recent_from_publications(a.publications, today)
    try:
        picks, skipped = rank(cands, recent, dt.date.fromisoformat(a.study_date), today, n=a.n)
    except StudyMissing as exc:
        print(f"✗ {exc}")
        return 1
    print(f"Recent mix (last 60 days): {Counter(c for c, _, _ in recent)}")
    for i, pk in enumerate(picks, 1):
        print(f"{i}. [{pk.category}] {pk.subject}  score {pk.score}\n     " + " · ".join(pk.reasons))
    print(f"\nSkipped ({len(skipped)}):")
    for cid, why in skipped:
        print(f"  - {cid}: {why}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
