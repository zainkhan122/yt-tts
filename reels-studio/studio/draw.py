"""Daily random count (1–5 videos per day) and reconciliation against what is scheduled.

Rules:
  * the count for a day is drawn before the first video of that day is scheduled;
  * a draw is recorded once per day and never overwritten;
  * the number of distinct videos scheduled for the day must equal the drawn count,
    unless a reason is recorded (for example, a held video). Going over is always an error.
"""
import datetime as dt
import secrets
from dataclasses import dataclass

from studio.rules import Finding

MIN_PER_DAY, MAX_PER_DAY = 1, 5


def draw_count(rng=None):
    rng = rng or secrets.SystemRandom()
    return rng.randint(MIN_PER_DAY, MAX_PER_DAY)


def record_draw(record, day, count, drawn_at, method="secrets.SystemRandom().randint(1,5)"):
    """Return a new record with the day's draw added. Refuses to overwrite an existing draw."""
    if not (MIN_PER_DAY <= count <= MAX_PER_DAY):
        raise ValueError(f"count {count} outside {MIN_PER_DAY}–{MAX_PER_DAY}")
    days = dict(record.get("days", {}))
    if day in days:
        raise ValueError(f"{day} already has a draw ({days[day]['count']}); draws are never overwritten")
    days[day] = {"count": count, "drawn_at": drawn_at, "method": method}
    return {**record, "days": days}


@dataclass(frozen=True)
class Slot:
    video_id: str
    scheduled_at: str  # ISO 8601 with offset, the planned publish time


def reconcile(record, day, slots, reason=""):
    """Compare the day's draw with the videos scheduled for that day. Returns Findings."""
    where = f"draw {day}"
    out = []
    entry = record.get("days", {}).get(day)
    videos = sorted({s.video_id for s in slots})
    if entry is None:
        if videos:
            out.append(Finding("D001", "error", where, f"{len(videos)} video(s) scheduled with no draw recorded"))
        return out

    drawn = entry["count"]
    if slots:
        earliest = min(dt.datetime.fromisoformat(s.scheduled_at) for s in slots)
        drawn_at = dt.datetime.fromisoformat(entry["drawn_at"])
        if drawn_at > earliest:
            out.append(Finding("D002", "error", where, "draw was recorded after the first schedule of the day"))

    if len(videos) > drawn:
        out.append(Finding("D003", "error", where, f"{len(videos)} videos scheduled, drawn count is {drawn}"))
    elif len(videos) < drawn and not reason.strip():
        out.append(Finding("D004", "warning", where, f"{len(videos)} scheduled, drawn {drawn}; record a reason"))
    return out
