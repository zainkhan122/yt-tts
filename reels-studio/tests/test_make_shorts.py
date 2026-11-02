"""Tests for the one-line driver and the checks it relies on (failures F01-F13 in config/failure_ledger.json)."""
import hashlib
import json
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import make_shorts as ms  # noqa: E402
import preflight as pf  # noqa: E402
import receipt_build as rb  # noqa: E402


# ---------- request parsing -------------------------------------------------------------

@pytest.mark.parametrize("text,expected", [
    ("make 3 shorts today", (3, True)),
    ("make five shorts today", (5, True)),
    ("Make 1 short today", (1, True)),
])
def test_parse_request(text, expected):
    assert ms.parse_request(text) == expected


@pytest.mark.parametrize("text", ["make some videos", "make 11 shorts today", "make 0 shorts"])
def test_parse_request_rejects(text):
    with pytest.raises(SystemExit):
        ms.parse_request(text)


# ---------- select: shortfall is a stop, queued and busy ids are excluded ------------------

def _tree(tmp_path, monkeypatch, plans, queued=(), busy=()):
    monkeypatch.setattr(ms, "ROOT", tmp_path)
    for vid, prio in plans.items():
        d = tmp_path / "videos" / vid
        d.mkdir(parents=True)
        (d / "plan.json").write_text(json.dumps({"priority": prio}))
    (tmp_path / "queue").mkdir()
    (tmp_path / "queue" / "publish.json").write_text(json.dumps({"items": [{"video_id": q} for q in queued]}))
    monkeypatch.setattr(ms, "_valid_plan", lambda p: None)  # the plan checker is tested by its own suite
    monkeypatch.setattr(ms, "APPROVALS", tmp_path / "config" / "topic-approvals.json")
    _approve_all(tmp_path, plans)
    return {"batches": [{"status": "open", "ids": list(busy)}]} if busy else {}


def _approve_all(tmp_path, plans):
    (tmp_path / "config").mkdir(exist_ok=True)
    rec = {vid: {"plan_sha256": ms.plan_sha(tmp_path / "videos" / vid / "plan.json"), "approved_by": "owner",
                 "note": "test"} for vid in plans}
    (tmp_path / "config" / "topic-approvals.json").write_text(json.dumps({"approved": rec}))


def test_select_stops_when_short(tmp_path, monkeypatch):
    st = _tree(tmp_path, monkeypatch, {"tool-a-01": 100, "repo-b-01": 100})
    with pytest.raises(ms.Stop) as exc:
        ms.stage_select(st, 3)
    assert "need 3 approved ready plan(s), found 2" in str(exc.value)


def test_select_skips_queued_and_busy_and_orders_by_priority(tmp_path, monkeypatch):
    st = _tree(tmp_path, monkeypatch,
               {"repo-a-01": 100, "repo-b-01": 50, "repo-c-01": 10, "repo-d-01": 100},
               queued=["repo-c-01"], busy=["repo-d-01"])
    assert ms.stage_select(st, 2) == ["repo-b-01", "repo-a-01"]


def test_select_reports_rejected_plans(tmp_path, monkeypatch):
    st = _tree(tmp_path, monkeypatch, {"repo-a-01": 100})
    monkeypatch.setattr(ms, "_valid_plan", lambda p: "one viewer question required")
    with pytest.raises(ms.Stop) as exc:
        ms.stage_select(st, 1)
    assert "rejected: repo-a-01: one viewer question required" in str(exc.value)


# ---------- driver: stop keeps the batch open; resume skips finished stages --------------

def test_drive_stops_and_resumes_from_failed_stage(tmp_path, monkeypatch):
    monkeypatch.setattr(ms, "ROOT", tmp_path)
    monkeypatch.setattr(ms, "STATE", tmp_path / "state.json")
    calls = []
    fail_once = {"render": True}

    def fake(name):
        def f(*a, **k):
            calls.append(name)
            if name == "render" and fail_once["render"]:
                fail_once["render"] = False
                raise ms.Stop("cloud failed")
        return f

    for name in ["select", "build", "gate", "source", "render", "fetch", "panel", "cover", "queue", "buffer"]:
        monkeypatch.setattr(ms, f"stage_{name}", fake(name), raising=False)
    monkeypatch.setattr(ms, "stage_select", lambda st, n: (calls.append("select"), ["repo-a-01"])[1])
    batch = {"id": "2026-11-02-shorts-01", "count": 1, "schedule": False, "ids": [], "status": "open",
             "stage": "select", "stages_done": []}
    st = {"batches": [batch]}
    # drive() raises Stop; main() turns it into a message. Check the state after the failure.
    with pytest.raises(ms.Stop):
        ms.drive(st, batch)
    assert batch["stage"] == "render" and "gate" in batch["stages_done"]
    saved = json.loads((tmp_path / "state.json").read_text())
    assert saved["batches"][0]["stage"] == "render"
    calls.clear()
    assert ms.drive(st, batch) == "done"
    assert calls[0] == "render"          # gate/source were not repeated
    assert "build" not in calls


def test_schedule_only_when_asked(monkeypatch):
    modes = []
    monkeypatch.setattr(ms, "stage_buffer", lambda batch, schedule: modes.append(schedule))
    b = {"id": "x", "count": 1, "schedule": False, "ids": ["repo-a-01"], "stages_done": [], "stage": ""}
    for name in ["select", "build", "gate", "source", "render", "fetch", "panel", "cover", "queue"]:
        monkeypatch.setattr(ms, f"stage_{name}", lambda *a, **k: None, raising=False)
    monkeypatch.setattr(ms, "stage_select", lambda st, n: ["repo-a-01"])
    monkeypatch.setattr(ms, "STATE", ROOT / "tracker" / "does-not-matter.json")
    monkeypatch.setattr(ms, "save_state", lambda st: None)
    ms.drive({"batches": [b]}, b)
    assert modes == [False]              # the buffer stage runs dry-run/verify only unless scheduling was asked


# ---------- receipts ---------------------------------------------------------------------

def test_batch_id_format():
    assert rb.BATCH_RE.match("2026-11-02-shorts-01")
    assert not rb.BATCH_RE.match("Bad Name")
    assert not rb.BATCH_RE.match("../etc")


# ---------- preflight checks (F01-F03) on a temp workspace --------------------------------

@pytest.fixture
def ws(tmp_path, monkeypatch):
    monkeypatch.setattr(pf, "ROOT", tmp_path)
    cap = tmp_path / "captures" / "repo-x-01"
    cap.mkdir(parents=True)
    (cap / "plan-1.jpg").write_bytes(b"jpg")
    (cap / "anim.mp4").write_bytes(b"mp4")
    cov = tmp_path / "covers" / "repo-x-01"
    cov.mkdir(parents=True)
    (cov / "cover-selected.jpg").write_bytes(b"cover")
    sha = hashlib.sha256(b"cover").hexdigest()
    (cov / "selection.json").write_text(json.dumps({"file": "cover-selected.jpg", "sha256": sha, "text": "HEAD TEXT"}))
    vid = tmp_path / "videos" / "repo-x-01"
    vid.mkdir(parents=True)
    (vid / "plan.json").write_text(json.dumps({"cover": {"text": "HEAD TEXT"}}))
    return tmp_path


def test_assets_present_blocks_file_not_in_any_push(ws):
    brief = {"capture": "captures/repo-x-01", "scenes": [{"image": "plan-1.jpg"}, {"src": "missing.mp4"}]}
    res = pf.check_assets_present("repo-x-01", brief)
    assert res[0]["status"] == "BLOCK" and "missing.mp4" in res[0]["detail"]


def test_assets_present_passes(ws):
    brief = {"capture": "captures/repo-x-01", "scenes": [{"image": "plan-1.jpg"}, {"src": "anim.mp4"}]}
    assert pf.check_assets_present("repo-x-01", brief)[0]["status"] == "PASS"


def test_assets_absent_locally_but_recorded_in_push_is_note(ws):
    _record_push(ws)
    (ws / "captures" / "repo-x-01" / "anim.mp4").unlink()
    (ws / "tracker" / "capture-pushes.json").write_text(json.dumps({"repo-x-01": {
        "asset": "repo-x-01.tar", "files": {"anim.mp4": "x", "plan-1.jpg": "y"}}}))
    brief = {"capture": "captures/repo-x-01", "scenes": [{"src": "anim.mp4"}]}
    assert pf.check_assets_present("repo-x-01", brief)[0]["status"] == "NOTE"


def _record_push(ws, cap="repo-x-01"):
    import capture_store
    src = ws / "captures" / cap
    (ws / "tracker").mkdir(exist_ok=True)
    (ws / "tracker" / "capture-pushes.json").write_text(
        json.dumps({cap: {"asset": f"{cap}.tar", "files": capture_store.file_digests(src)}}))


def test_capture_release_blocks_missing_asset(ws):
    res = pf.check_capture_pack_release("repo-x-01", {"capture": "captures/repo-x-01"},
                                        fetch_release=lambda: {"assets": []})
    assert res[0]["status"] == "BLOCK" and "not in the capture-packs release" in res[0]["detail"]


def test_capture_release_note_without_push_record(ws):
    rel = {"assets": [{"name": "repo-x-01.tar"}]}
    res = pf.check_capture_pack_release("repo-x-01", {"capture": "captures/repo-x-01"}, fetch_release=lambda: rel)
    assert res[0]["status"] == "NOTE"


def test_capture_release_passes_when_content_matches_push(ws):
    _record_push(ws)
    rel = {"assets": [{"name": "repo-x-01.tar"}]}
    assert pf.check_capture_pack_release("repo-x-01", {"capture": "captures/repo-x-01"},
                                         fetch_release=lambda: rel)[0]["status"] == "PASS"


def test_capture_release_blocks_changed_file_even_if_mtime_is_old(ws):
    _record_push(ws)
    f = ws / "captures" / "repo-x-01" / "anim.mp4"
    f.write_bytes(b"regenerated")  # content changed after the push
    rel = {"assets": [{"name": "repo-x-01.tar"}]}
    res = pf.check_capture_pack_release("repo-x-01", {"capture": "captures/repo-x-01"}, fetch_release=lambda: rel)
    assert res[0]["status"] == "BLOCK" and "anim.mp4" in res[0]["detail"]


def test_mtime_change_alone_does_not_block(ws):
    import os
    _record_push(ws)
    for p in (ws / "captures" / "repo-x-01").iterdir():
        os.utime(p, (time.time() + 999, time.time() + 999))  # a restore touches mtimes only
    rel = {"assets": [{"name": "repo-x-01.tar"}]}
    assert pf.check_capture_pack_release("repo-x-01", {"capture": "captures/repo-x-01"},
                                         fetch_release=lambda: rel)[0]["status"] == "PASS"


def test_capture_release_blocks_when_unreadable(ws):
    def boom():
        raise RuntimeError("no token")
    res = pf.check_capture_pack_release("repo-x-01", {"capture": "captures/repo-x-01"}, fetch_release=boom)
    assert res[0]["status"] == "BLOCK" and "unreadable" in res[0]["detail"]


def test_cover_checks_sha_and_text(ws):
    assert pf.check_cover("repo-x-01")[0]["status"] == "PASS"
    (ws / "covers" / "repo-x-01" / "cover-selected.jpg").write_bytes(b"changed")
    assert "sha mismatch" in pf.check_cover("repo-x-01")[0]["detail"]
    (ws / "covers" / "repo-x-01" / "cover-selected.jpg").write_bytes(b"cover")
    (ws / "videos" / "repo-x-01" / "plan.json").write_text(json.dumps({"cover": {"text": "OTHER"}}))
    assert "!= selected cover" in pf.check_cover("repo-x-01")[0]["detail"]


def test_cover_missing_selection_blocks(ws):
    (ws / "covers" / "repo-x-01" / "selection.json").unlink()
    assert pf.check_cover("repo-x-01")[0]["status"] == "BLOCK"


# ---------- origin unreadable is a BLOCK (F06) -------------------------------------------

def test_unreadable_origin_blocks_dispatch(monkeypatch):
    import subprocess

    class R:
        returncode = 1
        stdout = ""
        stderr = "no remote"

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: R())
    res = pf.check_dispatch_head("repo-x-01", "research/production/receipts/x.json")
    assert res[0]["status"] == "BLOCK"


def test_select_waits_for_owner_topic_approval(tmp_path, monkeypatch):
    st = _tree(tmp_path, monkeypatch, {"repo-a-01": 100})
    (tmp_path / "config" / "topic-approvals.json").write_text(json.dumps({"approved": {}}))
    with pytest.raises(ms.Stop) as exc:
        ms.stage_select(st, 1)
    assert "owner approval of topics is required" in str(exc.value) and "repo-a-01" in str(exc.value)


def test_topic_approval_is_per_topic_id(tmp_path, monkeypatch):
    st = _tree(tmp_path, monkeypatch, {"repo-a-01": 100, "repo-b-01": 100})
    (tmp_path / "config" / "topic-approvals.json").write_text(json.dumps({"approved": {"repo-b-01": {"approved_by": "owner"}}}))
    assert ms.stage_select(st, 1) == ["repo-b-01"]   # only the approved topic is selected


def test_approve_topic_needs_owner_words(tmp_path, monkeypatch):
    _tree(tmp_path, monkeypatch, {"repo-a-01": 100})
    monkeypatch.setattr(ms, "APPROVALS", tmp_path / "config" / "topic-approvals.json")
    with pytest.raises(SystemExit):
        ms.approve_topic("repo-a-01", "")
    ms.approve_topic("repo-a-01", "yes, make it")
    assert ms.topic_approved("repo-a-01")


# ---------- legacy briefs (owner decision 2) ---------------------------------------------

def test_legacy_mark_uses_sent_and_manual_only(tmp_path):
    import mark_legacy as ml
    pubs = {"records": {
        "a:youtube": {"state": "sent"}, "a:instagram": {"state": "sent"},
        "b:facebook": {"state": "scheduled"}, "c:youtube": {"state": "uncertain"},
        "d:youtube": {"state": "published_manual"}}}
    assert ml.compute(pubs) == {"a": ["instagram", "youtube"], "d": ["youtube"]}


def test_legacy_brief_turns_cloud_source_blocks_into_notes(ws, monkeypatch):
    (ws / "config").mkdir(exist_ok=True)
    (ws / "config" / "legacy-briefs.json").write_text(json.dumps({"briefs": {"repo-x-01": ["youtube"]}}))
    brief = {"capture": "captures/repo-x-01", "scenes": [{"src": "gone.mp4"}]}
    monkeypatch.setattr(pf, "check_capture_pack_release", lambda *a, **k: [pf._result("capture_release", "BLOCK", "x", "y")])
    monkeypatch.setattr(pf, "check_cover", lambda *a, **k: [pf._result("cover", "BLOCK", "no cover", "y")])
    res = pf._cloud_source_checks("repo-x-01", brief)
    assert all(r["status"] == "NOTE" for r in res), res


def test_non_legacy_brief_keeps_blocks(ws, monkeypatch):
    brief = {"capture": "captures/repo-x-01", "scenes": [{"src": "gone.mp4"}]}
    monkeypatch.setattr(pf, "check_capture_pack_release", lambda *a, **k: [pf._result("capture_release", "PASS", "ok", "")])
    monkeypatch.setattr(pf, "check_cover", lambda *a, **k: [pf._result("cover", "PASS", "ok", "")])
    res = pf._cloud_source_checks("repo-x-01", brief)
    assert any(r["status"] == "BLOCK" for r in res)


def test_build_generates_brief_before_pulling_capture():
    """Regression (2 Nov): stage_build read briefs/<id>.json before brief_from_plan had written it."""
    import inspect
    import make_shorts
    src = inspect.getsource(make_shorts.stage_build)
    assert src.index("brief_from_plan") < src.index('capture_store.py", "pull"')


def test_build_pulls_capture_pack_only_when_missing():
    """Regression (2 Nov): a kit built locally was pulled from the store before it had been pushed."""
    import inspect
    import make_shorts
    src = inspect.getsource(make_shorts.stage_build)
    assert "exists()" in src and src.index("exists()") < src.index('capture_store.py", "pull"')
