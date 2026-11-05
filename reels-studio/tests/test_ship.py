"""Tests for tools/ship.py: every link in the brief -> receipt -> queue -> artifact -> panel chain.

Each test builds a throwaway repo tree, so the real repo is never touched.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import ship  # noqa: E402
from post.common import fingerprint  # noqa: E402

VID = "repo-test-01"
MP4 = b"fake-mp4-bytes-v1"
COVER = b"fake-cover-bytes"


@pytest.fixture
def tree(tmp_path):
    """A complete, consistent tree for one video. Tests break one link at a time."""
    brief = {"id": VID, "seo": {"youtube": {"title": "t"}}, "post": {"hashtags": ["#Shorts"]}}
    (tmp_path / "briefs").mkdir()
    (tmp_path / "briefs" / f"{VID}.json").write_text(json.dumps(brief), encoding="utf-8")
    rec = tmp_path / "research" / "production" / "receipts"
    rec.mkdir(parents=True)
    (rec / "2026-11-05-shorts-01.json").write_text(json.dumps(
        {"briefs": {VID: {"brief_sha256": ship.sha256_file(tmp_path / "briefs" / f"{VID}.json")}}}), encoding="utf-8")
    (tmp_path / "queue").mkdir()
    mp4 = tmp_path / "video.mp4"
    mp4.write_bytes(MP4)
    cover = tmp_path / "cover.jpg"
    cover.write_bytes(COVER)
    ship.review(VID, mp4, "42048880432", cover, root=tmp_path)
    (tmp_path / "queue" / "publish.json").write_text(json.dumps({"items": [{
        "video_id": VID, "brief_sha256": fingerprint(brief),
        "asset_digest": "sha256:" + ship.sha256_file(mp4),
        "cover_sha256": ship.sha256_file(cover), "platforms": ["youtube", "instagram"],
    }]}), encoding="utf-8")
    (tmp_path / "research" / "production" / f"viewer-panel-{VID}.md").write_text(
        "# Viewer panel\n\nPanel result: PASS (owner override)\n", encoding="utf-8")
    return tmp_path


def test_consistent_tree_passes(tree):
    assert ship.check(VID, root=tree) == []


def test_brief_edited_after_receipt_is_drift(tree):
    p = tree / "briefs" / f"{VID}.json"
    b = json.loads(p.read_text(encoding="utf-8"))
    b["post"]["hashtags"] = ["#changed"]
    p.write_text(json.dumps(b), encoding="utf-8")
    errs = ship.check(VID, root=tree)
    assert any("receipt" in e and "edited after receipt" in e for e in errs)
    assert any(e.startswith("queue: brief_sha256") for e in errs)


def test_scheduled_file_differs_from_reviewed_file_is_drift(tree):
    # This is the 5 Nov failure: reviewed one render, scheduled a re-render.
    q = tree / "queue" / "publish.json"
    d = json.loads(q.read_text(encoding="utf-8"))
    d["items"][0]["asset_digest"] = "sha256:" + "0" * 64
    q.write_text(json.dumps(d), encoding="utf-8")
    errs = ship.check(VID, root=tree)
    assert any(e.startswith("artifact: release asset") for e in errs)


def test_unreviewed_video_is_drift(tree):
    (tree / "research" / "production" / "reviewed" / f"{VID}.json").unlink()
    errs = ship.check(VID, root=tree)
    assert any(e.startswith("review: no review record") for e in errs)


def test_cover_mismatch_is_drift(tree):
    q = tree / "queue" / "publish.json"
    d = json.loads(q.read_text(encoding="utf-8"))
    d["items"][0]["cover_sha256"] = "f" * 64
    q.write_text(json.dumps(d), encoding="utf-8")
    assert any(e.startswith("cover: queued cover differs") for e in ship.check(VID, root=tree))


def test_missing_cover_blocks_youtube(tree):
    q = tree / "queue" / "publish.json"
    d = json.loads(q.read_text(encoding="utf-8"))
    d["items"][0]["cover_sha256"] = None
    q.write_text(json.dumps(d), encoding="utf-8")
    assert any(e.startswith("cover: youtube is scheduled") for e in ship.check(VID, root=tree))


def test_panel_fail_blocks(tree):
    (tree / "research" / "production" / f"viewer-panel-{VID}.md").write_text(
        "Panel result: FAIL\n", encoding="utf-8")
    assert any(e.startswith("panel: verdict is FAIL") for e in ship.check(VID, root=tree))


def test_panel_words_without_verdict_line_do_not_pass(tree):
    # Free text saying PASS is not a verdict. Only the "Panel result:" line counts.
    (tree / "research" / "production" / f"viewer-panel-{VID}.md").write_text(
        "All checks PASS and it is great.\n", encoding="utf-8")
    assert any(e.startswith("panel: verdict is missing") for e in ship.check(VID, root=tree))


def test_only_latest_receipt_governs(tree):
    # An older receipt pinning a previous brief version is history, not drift.
    old = tree / "research" / "production" / "receipts" / "2026-11-04-shorts-01.json"
    old.write_text(json.dumps({"briefs": {VID: {"brief_sha256": "0" * 64}}}), encoding="utf-8")
    assert ship.check(VID, root=tree) == []


def test_not_queued_is_reported(tree):
    (tree / "queue" / "publish.json").write_text(json.dumps({"items": []}), encoding="utf-8")
    assert ship.check(VID, root=tree) == ["queue: item not queued (nothing to ship yet)"]


def test_review_rejects_non_numeric_run(tree):
    with pytest.raises(SystemExit):
        ship.review(VID, tree / "video.mp4", "run-42", None)


def test_bad_video_id_rejected():
    with pytest.raises(SystemExit):
        ship._valid("../etc")
