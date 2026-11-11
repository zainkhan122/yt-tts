"""Feature sheet: the grounding data for every generated graphic.

A feature sheet is extracted from the tool's own README/docs. Every claim a graphic shows must cite a
feature id, and every quote must appear verbatim in the fetched source text. Lint is deterministic.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

ALLOWED_TOP = {"tool", "features", "benchmarks", "risks", "source_urls"}
ALLOWED_FEATURE = {"id", "title", "what", "items", "metric", "evidence_quote", "risk"}
MIN_FEATURES = 3
MIN_WHAT_WORDS = 4
_FLUFF = {"revolutionary", "game-changing", "seamless", "powerful", "amazing", "best", "unbelievable"}


@dataclass
class Violation:
    rule: str
    detail: str

    def as_dict(self) -> dict:
        return {"rule": self.rule, "detail": self.detail}


def _norm(s: str) -> str:
    # Markdown emphasis and link syntax are stripped so quotes match the rendered text.
    s = re.sub(r"[*_`]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip().lower()


def lint_feature_sheet(sheet: dict, source_text: str) -> list[Violation]:
    v: list[Violation] = []
    if not isinstance(sheet, dict):
        return [Violation("F0", "sheet must be an object")]
    for key in sheet:
        if key not in ALLOWED_TOP:
            v.append(Violation("F0", f"unknown top-level key '{key}'"))
    tool = sheet.get("tool") or {}
    if not tool.get("name"):
        v.append(Violation("F1", "tool.name is required"))

    feats = sheet.get("features") or []
    if len(feats) < MIN_FEATURES:
        v.append(Violation("F2", f"need >= {MIN_FEATURES} features, got {len(feats)}"))

    src = _norm(source_text)
    ids = set()
    for f in feats:
        fid = f.get("id")
        if not fid or fid in ids:
            v.append(Violation("F3", f"feature id missing or duplicated: {fid!r}"))
        ids.add(fid)
        for k in f:
            if k not in ALLOWED_FEATURE:
                v.append(Violation("F0", f"{fid}: unknown key '{k}'"))
        what = f.get("what", "")
        if len(what.split()) < MIN_WHAT_WORDS:
            v.append(Violation("F4", f"{fid}: 'what' needs >= {MIN_WHAT_WORDS} words"))
        if any(w.strip(".,!").lower() in _FLUFF for w in what.split()):
            v.append(Violation("F5", f"{fid}: marketing word in 'what'"))
        q = f.get("evidence_quote", "")
        if not q or _norm(q) not in src:
            v.append(Violation("F6", f"{fid}: evidence_quote not found verbatim in source"))
        if f.get("metric") is not None:
            val = f["metric"].get("value")
            if not isinstance(val, (int, float)):
                v.append(Violation("F7", f"{fid}: metric.value must be numeric"))
    if not any(f.get("risk") for f in feats) and not sheet.get("risks"):
        v.append(Violation("F8", "need at least one risk (feeds the honest 'catch')"))
    return v


def feature_index(sheet: dict) -> dict[str, dict]:
    return {f["id"]: f for f in sheet.get("features", [])}
