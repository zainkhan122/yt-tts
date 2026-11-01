"""Every enforced failure in config/failure_ledger.json must point at code that exists."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "config" / "failure_ledger.json"


def _entries():
    return json.loads(LEDGER.read_text(encoding="utf-8"))["entries"]


def test_ledger_ids_unique_and_statuses_valid():
    ids = [e["id"] for e in _entries()]
    assert len(ids) == len(set(ids))
    assert all(e["status"] in {"enforced", "open"} for e in _entries())


def test_enforced_entries_resolve_to_real_code():
    problems = []
    for e in _entries():
        if e["status"] != "enforced":
            continue
        ref = e.get("enforced_by", "")
        if "::" not in ref:  # a plain config file counts as enforcement only if it exists
            if not (ROOT / ref).exists():
                problems.append(f"{e['id']}: config {ref!r} does not exist")
            continue
        path, name = ref.split("::", 1)
        src = ROOT / path if not path.startswith("reels.py") else ROOT / "reels.py"
        if not src.exists():
            problems.append(f"{e['id']}: {path} does not exist")
            continue
        if not re.search(rf"\b{re.escape(name.split('::')[-1])}\b", src.read_text(encoding="utf-8")):
            problems.append(f"{e['id']}: {name} not found in {path}")
    assert not problems, "\n".join(problems)


def test_open_entries_are_listed_not_hidden():
    opened = [e["id"] for e in _entries() if e["status"] == "open"]
    assert opened, "open items must stay visible until they have code"
