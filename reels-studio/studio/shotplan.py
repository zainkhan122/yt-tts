"""Shot plan (v3): how a short is shown, beat by beat. Validated before anything renders.

A shot plan is written for one idea by the writer. It is not chosen from a template. The
plan says what the viewer sees at each moment: the project's real media (a README image, a demo
clip, a product screenshot), a data-backed chart, a stat with its source, an animated callout on
a real frame, a licensed sticker, or a short text line.

The rules below are the floor. They make sure a short shows something real most of the time,
does not scroll over one static page, and does not invent numbers. They do not dictate the
order or the look.
"""
import argparse
import datetime as dt
import json
import re
from dataclasses import dataclass
from pathlib import Path

from studio.rules import Finding

KINDS = ("capture", "video", "chart", "stat", "callout", "sticker", "text")
REAL_KINDS = ("capture", "video")
MOTIONS = ("static", "push-in", "pan", "scroll", "cut")
MIN_BEAT_S, MAX_BEAT_S = 0.8, 7.0
MIN_REAL_SHARE = 0.55
MAX_TEXT_SHARE = 0.20
MAX_SAME_KIND_RUN = 2
MAX_SCROLL_RUN_S = 2.5
MAX_TEXT_WORDS_PER_LINE = 8
MAX_CALLOUT_WORDS = 4
MIN_BEATS_PER_10S = 3          # warning only: pacing below this feels slow
HTTPS_RE = re.compile(r"^https://\S+$")
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _f(out, code, where, msg):
    out.append(Finding(code, "error", where, msg))


def _w(out, code, where, msg):
    out.append(Finding(code, "warning", where, msg))


def _words(text):
    return len(str(text).split())


def check_plan(plan, *, captures_dir=None, claims=None):
    """Return Findings for one shot plan. Empty (or warnings only) means it may be rendered."""
    out = []
    pid = plan.get("id", "<no id>")
    duration = plan.get("duration_s")
    beats = plan.get("beats")
    if not isinstance(duration, (int, float)) or duration <= 0:
        _f(out, "SP000", pid, "duration_s must be a positive number")
        return out
    if not isinstance(beats, list) or not beats:
        _f(out, "SP000", pid, "beats must be a non-empty list")
        return out

    # SP001: contiguous coverage from 0 to duration.
    cursor = 0.0
    for i, b in enumerate(beats):
        where = f"{pid} beat {i + 1}"
        t0, t1 = b.get("t0"), b.get("t1")
        if not isinstance(t0, (int, float)) or not isinstance(t1, (int, float)) or t1 <= t0:
            _f(out, "SP001", where, "t0 and t1 must be numbers with t1 > t0")
            continue
        if abs(t0 - cursor) > 0.01:
            _f(out, "SP001", where, f"gap or overlap: starts at {t0}, previous ended at {cursor:.2f}")
        cursor = t1
        length = t1 - t0
        if not MIN_BEAT_S <= length <= MAX_BEAT_S:
            _f(out, "SP002", where, f"beat is {length:.2f}s; allowed {MIN_BEAT_S}–{MAX_BEAT_S}s")
    if abs(cursor - duration) > 0.01:
        _f(out, "SP001", pid, f"beats end at {cursor:.2f}s but duration_s is {duration}")

    valid = [b for b in beats if b.get("kind") in KINDS]
    for i, b in enumerate(beats):
        if b.get("kind") not in KINDS:
            _f(out, "SP015", f"{pid} beat {i + 1}", f"unknown kind {b.get('kind')!r}; allowed {KINDS}")

    # SP006: first second shows something real.
    if beats and beats[0].get("kind") not in ("capture", "video", "chart", "stat"):
        _f(out, "SP006", f"{pid} beat 1", "the first beat must show real media, a chart or a sourced stat")

    # SP003: real media share.
    def _is_real(b):
        if b["kind"] in REAL_KINDS:
            return True
        # An annotation drawn on a real frame is still real media on screen.
        return b["kind"] == "callout" and str(b.get("on", "")).startswith(("capture:", "owner_test:"))
    real_time = sum(b["t1"] - b["t0"] for b in valid if _is_real(b))
    text_time = sum(b["t1"] - b["t0"] for b in valid if b["kind"] == "text")
    if duration and real_time / duration < MIN_REAL_SHARE:
        _f(out, "SP003", pid, f"real media is {real_time / duration:.0%} of the run; need {MIN_REAL_SHARE:.0%}+")
    if duration and text_time / duration > MAX_TEXT_SHARE:
        _f(out, "SP005", pid, f"text cards are {text_time / duration:.0%} of the run; max {MAX_TEXT_SHARE:.0%}")

    # SP004 and SP005b: runs.
    run, prev = 0, None
    for i, b in enumerate(valid):
        run = run + 1 if b["kind"] == prev else 1
        prev = b["kind"]
        if run > MAX_SAME_KIND_RUN:
            _f(out, "SP004", f"{pid} beat {i + 1}", f"more than {MAX_SAME_KIND_RUN} '{b['kind']}' beats in a row")
    for i in range(1, len(valid)):
        if valid[i]["kind"] == "text" and valid[i - 1]["kind"] == "text":
            _f(out, "SP005", f"{pid} beat {i + 1}", "two text cards in a row")

    # SP011: scrolling over one page must not run long.
    scroll_run = 0.0
    for i, b in enumerate(valid):
        if b["kind"] == "capture" and b.get("motion") == "scroll":
            scroll_run += b["t1"] - b["t0"]
            if scroll_run > MAX_SCROLL_RUN_S:
                _f(out, "SP011", f"{pid} beat {i + 1}", f"scrolling for {scroll_run:.1f}s; max {MAX_SCROLL_RUN_S}s without a change of view")
                break
        else:
            scroll_run = 0.0

    # Per-kind checks.
    used_assets = set()
    for i, b in enumerate(valid):
        where = f"{pid} beat {i + 1} ({b['kind']})"
        k = b["kind"]
        if k in ("capture", "video"):
            asset = str(b.get("asset", ""))
            if not (asset.startswith("capture:") or asset.startswith("owner_test:") or HTTPS_RE.match(asset)):
                _f(out, "SP012", where, "asset must be capture:<file>, owner_test:<file> or an https URL")
            if asset.startswith("capture:") and captures_dir is not None:
                rel = asset.split(":", 1)[1]
                if not (Path(captures_dir) / rel).exists():
                    _f(out, "SP012", where, f"capture {rel!r} is not in the capture pack")
            used_assets.add(asset)
            if k == "capture" and b.get("motion", "static") not in MOTIONS:
                _f(out, "SP012", where, f"motion must be one of {MOTIONS}")
        elif k == "chart":
            d = b.get("data") or {}
            if not HTTPS_RE.match(str(d.get("source", ""))):
                _f(out, "SP007", where, "chart needs an https data source")
            if not ISO_DATE_RE.match(str(d.get("retrieved_at", ""))):
                _f(out, "SP007", where, "chart needs retrieved_at (YYYY-MM-DD)")
            vals = d.get("values") or []
            if not (isinstance(vals, list) and len(vals) >= 3 and all(isinstance(v, (int, float)) for v in vals)):
                _f(out, "SP007", where, "chart needs at least 3 numeric values from the source")
        elif k == "stat":
            if not HTTPS_RE.match(str(b.get("source", ""))):
                _f(out, "SP008", where, "stat needs an https source")
            if not ISO_DATE_RE.match(str(b.get("retrieved_at", ""))):
                _f(out, "SP008", where, "stat needs retrieved_at (YYYY-MM-DD)")
            if not str(b.get("value", "")).strip() or not str(b.get("label", "")).strip():
                _f(out, "SP008", where, "stat needs value and label")
        elif k == "sticker":
            if not str(b.get("asset", "")).startswith("sticker:"):
                _f(out, "SP009", where, "sticker asset must be sticker:<name>")
            if not str(b.get("license", "")).strip():
                _f(out, "SP009", where, "sticker needs a licence (or 'owner-made')")
        elif k == "callout":
            if _words(b.get("text", "")) > MAX_CALLOUT_WORDS:
                _f(out, "SP014", where, f"callout is longer than {MAX_CALLOUT_WORDS} words")
            on = b.get("on", "")
            if not on or on not in used_assets:
                _f(out, "SP010", where, "callout must point at a capture or video used in this plan")
        elif k == "text":
            text = str(b.get("text", ""))
            for line in text.split("\n"):
                if _words(line) > MAX_TEXT_WORDS_PER_LINE:
                    _f(out, "SP014", where, f"text line has {_words(line)} words; max {MAX_TEXT_WORDS_PER_LINE}")
                    break
            if not text.strip():
                _f(out, "SP014", where, "text beat is empty")

    # SP013: claims in the brief must be shown; beats may only cite real claims.
    if claims is not None:
        cited = {b["claim"] for b in valid if b.get("claim")}
        for c in cited - set(claims):
            _f(out, "SP013", pid, f"beat cites unknown claim {c!r}")
        for c in sorted(set(claims) - cited):
            _f(out, "SP013", pid, f"claim {c!r} is not shown in any beat")

    # Pacing (warning only).
    if duration and len(valid) / duration * 10 < MIN_BEATS_PER_10S:
        _w(out, "SP020", pid, f"only {len(valid) / duration * 10:.1f} beats per 10s; consider more visual changes")
    return out


def errors(findings):
    return [f for f in findings if f.level == "error"]


def main(argv=None):
    p = argparse.ArgumentParser(description="Validate a shot plan before rendering.")
    p.add_argument("paths", nargs="+")
    p.add_argument("--captures", default=None, help="capture pack directory for capture:<file> checks")
    a = p.parse_args(argv)
    failed = 0
    for path in a.paths:
        plan = json.loads(Path(path).read_text(encoding="utf-8"))
        findings = check_plan(plan, captures_dir=a.captures)
        errs = errors(findings)
        print(f"{'✗' if errs else '✓'} {plan.get('id', path)}: {len(errs)} error(s), {len(findings) - len(errs)} warning(s)")
        for f in findings:
            print(f"    {f}")
        failed += 1 if errs else 0
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
