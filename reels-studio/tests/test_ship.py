"""Tests for tools/ship.py. The queue item is the only state; each test breaks one link."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import ship  # noqa: E402
from brief_identity import identity  # noqa: E402

VID = "repo-test-01"
def panel_text(video_sha, verdict="PASS"):
    return f"# Viewer panel\n\nVideo sha256: {video_sha}\nPanel result: {verdict}\n"


@pytest.fixture
def tree(tmp_path):
    """A consistent tree: brief, receipt, approved and reviewed queue item, PASS panel."""
    brief = {"id": VID, "seo": {"youtube": {"title": "t"}}, "post": {"hashtags": ["#Shorts"]}}
    (tmp_path / "briefs").mkdir()
    bp = tmp_path / "briefs" / f"{VID}.json"
    bp.write_text(json.dumps(brief), encoding="utf-8")
    rec = tmp_path / "research" / "production" / "receipts"
    rec.mkdir(parents=True)
    (rec / "2026-11-05-shorts-01.json").write_text(json.dumps(
        {"briefs": {VID: {"brief_sha256": ship.sha256_file(bp), "brief_identity_sha256": identity(brief)}}}), encoding="utf-8")
    mp4 = tmp_path / "video.mp4"
    mp4.write_bytes(b"mp4-v1")
    (tmp_path / "research" / "production" / f"viewer-panel-{VID}.md").write_text(
        panel_text(ship.sha256_file(mp4)), encoding="utf-8")
    cover = tmp_path / "cover.jpg"
    cover.write_bytes(b"cover-v1")
    (tmp_path / "queue").mkdir()
    item = {
        "video_id": VID, "approval": "held", "platforms": ["youtube", "instagram"],
        "brief_sha256": identity(brief),
        "asset_digest": "sha256:" + ship.sha256_file(mp4),
        "cover_sha256": ship.sha256_file(cover),
    }
    (tmp_path / "queue" / "publish.json").write_text(json.dumps({"items": [item]}), encoding="utf-8")
    item["review"] = ship.release_review(item["asset_digest"], mp4.stat().st_size)
    (tmp_path / "queue" / "publish.json").write_text(json.dumps({"items": [item]}), encoding="utf-8")
    # approval as queue_ctl would record it
    q = json.loads((tmp_path / "queue" / "publish.json").read_text(encoding="utf-8"))
    q["items"][0]["approval"] = "approved"
    (tmp_path / "queue" / "publish.json").write_text(json.dumps(q), encoding="utf-8")
    ship.record_approval(VID, root=tmp_path)
    return tmp_path


def _queue(root):
    return json.loads((root / "queue" / "publish.json").read_text(encoding="utf-8"))


def _set(root, **fields):
    q = _queue(root)
    q["items"][0].update(fields)
    (root / "queue" / "publish.json").write_text(json.dumps(q), encoding="utf-8")


def test_consistent_tree_passes(tree):
    assert ship.check(VID, root=tree) == []
    assert ship.check_all(root=tree) == {}


def test_brief_edited_after_receipt_is_drift(tree):
    p = tree / "briefs" / f"{VID}.json"
    b = json.loads(p.read_text(encoding="utf-8"))
    b["post"]["hashtags"] = ["#changed"]
    p.write_text(json.dumps(b), encoding="utf-8")
    errs = ship.check(VID, root=tree)
    assert any("edited after receipt" in e for e in errs)
    assert any(e.startswith("queue: brief identity") for e in errs)


def test_only_latest_receipt_governs(tree):
    old = tree / "research" / "production" / "receipts" / "2026-11-04-shorts-01.json"
    old.write_text(json.dumps({"briefs": {VID: {"brief_identity_sha256": "0" * 64}}}), encoding="utf-8")
    assert ship.check(VID, root=tree) == []


def test_receipt_without_identity_is_drift(tree):
    rp = tree / "research" / "production" / "receipts" / "2026-11-05-shorts-01.json"
    rp.write_text(json.dumps({"briefs": {VID: {"brief_sha256": "x"}}}), encoding="utf-8")
    assert any("predates the identity pin" in e for e in ship.check(VID, root=tree))


def test_identity_is_format_independent(tree):
    p = tree / "briefs" / f"{VID}.json"
    b = json.loads(p.read_text(encoding="utf-8"))
    p.write_text(json.dumps(b, indent=8, sort_keys=True), encoding="utf-8")  # same content, new bytes
    assert ship.check(VID, root=tree) == []


def test_panel_for_a_different_file_is_drift(tree):
    (tree / "research" / "production" / f"viewer-panel-{VID}.md").write_text(panel_text("a" * 64), encoding="utf-8")
    assert any("reviewed a different file" in e for e in ship.check(VID, root=tree))


def test_panel_without_video_sha_is_drift(tree):
    (tree / "research" / "production" / f"viewer-panel-{VID}.md").write_text("Panel result: PASS\n", encoding="utf-8")
    assert any("reviewed a different file" in e for e in ship.check(VID, root=tree))


def test_release_review_pins_digest():
    r = ship.release_review("sha256:" + "ab" * 32, 123)
    assert r["mp4_sha256"] == "ab" * 32 and r["source"] == "release-digest" and r["mp4_bytes"] == 123


@pytest.mark.parametrize("bad", [None, "", "md5:abc", "sha256:xyz"])
def test_release_review_refuses_missing_or_bad_digest(bad):
    with pytest.raises(SystemExit):
        ship.release_review(bad, 1)


def test_live_digest_mismatch_is_drift(tree, monkeypatch):
    _set(tree, release_tag="renders-2026-11-05")
    monkeypatch.setattr(ship, "live_asset_digest", lambda tag, name: "sha256:" + "f" * 64)
    assert any(e.startswith("release: live asset digest") for e in ship.check(VID, root=tree, live=True))


def test_live_digest_match_passes(tree, monkeypatch):
    _set(tree, release_tag="renders-2026-11-05")
    monkeypatch.setattr(ship, "live_asset_digest", lambda tag, name: _queue(tree)["items"][0]["asset_digest"])
    assert ship.check(VID, root=tree, live=True) == []


def test_pin_held_backfills_only_held_unpinned_items(tree):
    q = _queue(tree)
    q["items"].append({"video_id": "held-x-01", "approval": "held", "asset_digest": "sha256:" + "1" * 64, "asset_size": 5})
    q["items"].append({"video_id": "held-y-01", "approval": "held", "asset_digest": None})
    (tree / "queue" / "publish.json").write_text(json.dumps(q), encoding="utf-8")
    with pytest.raises(SystemExit):
        ship.pin_held(root=tree)  # held-y has no usable digest: refuse the whole pin, pin nothing
    q = _queue(tree)
    q["items"][2]["asset_digest"] = "sha256:" + "2" * 64  # held-y (items[0] is the approved fixture item)
    (tree / "queue" / "publish.json").write_text(json.dumps(q), encoding="utf-8")
    assert ship.pin_held(root=tree) == ["held-x-01", "held-y-01"]
    assert ship.pin_held(root=tree) == []


def test_review_refuses_a_file_that_is_not_the_released_asset(tree):
    other = tree / "other.mp4"
    other.write_bytes(b"re-render")
    with pytest.raises(SystemExit):
        ship.review(VID, other, "42999999999", None, root=tree)


def test_review_rejects_non_numeric_run(tree):
    with pytest.raises(SystemExit):
        ship.review(VID, tree / "video.mp4", "run-42", None, root=tree)


def test_not_reviewed_is_drift(tree):
    _set(tree, review=None)
    assert any(e.startswith("review: not reviewed") for e in ship.check(VID, root=tree))


def test_asset_replaced_after_review_is_drift(tree):
    _set(tree, asset_digest="sha256:" + "0" * 64)
    assert any(e.startswith("artifact:") for e in ship.check(VID, root=tree))


def test_cover_changed_after_approval_is_drift(tree):
    _set(tree, cover_sha256="f" * 64)
    assert any(e.startswith("cover: changed after approval") for e in ship.check(VID, root=tree))


def test_approved_without_pinned_cover_is_drift(tree):
    _set(tree, approved_cover_sha=None)
    assert any(e.startswith("cover: approved without") for e in ship.check(VID, root=tree))


def test_youtube_without_cover_is_drift(tree):
    _set(tree, cover_sha256=None)
    assert any(e.startswith("cover: youtube is scheduled") for e in ship.check(VID, root=tree))


def test_panel_fail_blocks(tree):
    (tree / "research" / "production" / f"viewer-panel-{VID}.md").write_text("Panel result: FAIL\n", encoding="utf-8")
    assert any(e.startswith("panel: verdict is FAIL") for e in ship.check(VID, root=tree))


def test_panel_free_text_is_not_a_verdict(tree):
    (tree / "research" / "production" / f"viewer-panel-{VID}.md").write_text(
        "All checks PASS and it is great.\n", encoding="utf-8")
    assert any(e.startswith("panel: verdict is missing") for e in ship.check(VID, root=tree))


def test_panel_edited_after_approval_is_drift(tree):
    f = tree / "research" / "production" / f"viewer-panel-{VID}.md"
    f.write_text(f.read_text(encoding="utf-8") + "\nnew note\n", encoding="utf-8")
    assert any(e.startswith("panel: panel file changed after approval") for e in ship.check(VID, root=tree))


def test_approved_without_pinned_panel_is_drift(tree):
    _set(tree, approved_panel_sha=None)
    assert any(e.startswith("panel: approved without") for e in ship.check(VID, root=tree))


def test_legacy_items_are_listed_not_checked(tree):
    _set(tree, ship_legacy=True, review=None, approved_panel_sha=None)
    assert ship.check(VID, root=tree) == []
    assert ship.check_all(root=tree) == {}


def test_check_all_reports_unreviewed_approved_item(tree):
    _set(tree, review=None)
    assert VID in ship.check_all(root=tree)


def test_held_item_is_not_checked_by_check_all(tree):
    _set(tree, approval="held", review=None)
    assert ship.check_all(root=tree) == {}


def test_not_queued_is_reported(tree):
    (tree / "queue" / "publish.json").write_text(json.dumps({"items": []}), encoding="utf-8")
    assert ship.check(VID, root=tree) == ["queue: item not queued"]


def test_bad_video_id_rejected():
    with pytest.raises(SystemExit):
        ship._valid("../etc")


def test_next_for_unqueued_video_is_render(tree):
    assert ship.next_action("never-queued-01", root=tree).startswith("render in the cloud")


def test_next_for_held_unpinned_is_pin(tree):
    q = _queue(tree)
    q["items"].append({"video_id": "held-z-01", "approval": "held", "asset_digest": "sha256:" + "3" * 64})
    (tree / "queue" / "publish.json").write_text(json.dumps(q), encoding="utf-8")
    assert ship.next_action("held-z-01", root=tree).startswith("pin review")


def test_next_for_approved_consistent_is_wait(tree):
    assert ship.next_action(VID, root=tree).startswith("approved and consistent")


def test_next_for_missing_panel_asks_for_panel(tree):
    _set(tree, approval="held", approved_panel_sha=None)
    (tree / "research" / "production" / f"viewer-panel-{VID}.md").write_text("", encoding="utf-8")
    assert ship.next_action(VID, root=tree).startswith("viewer panel")


def test_status_render_is_deterministic(tree):
    assert ship.render_status(root=tree) == ship.render_status(root=tree)
    text = ship.render_status(root=tree)
    assert "## Counts" in text and "Do not edit by hand" in text


def test_panel_must_be_canonical_not_another_id_or_dated_file(tree):
    canonical = tree / "research" / "production" / f"viewer-panel-{VID}.md"
    canonical.unlink()
    (canonical.parent / f"viewer-panel-{VID}-extra.md").write_text(panel_text("a" * 64))
    assert ship.panel_file(VID, tree) is None
    assert any("verdict is missing" in e for e in ship.check(VID, root=tree))


def test_non_hex_release_digest_is_rejected():
    with pytest.raises(SystemExit):
        ship.release_review("sha256:" + "z" * 64, 1)


def test_requested_platforms_are_checked_before_approval(tree):
    _set(tree, approval="held", platforms=["instagram"], cover_sha256=None)
    assert any(e.startswith("cover:") for e in ship.check(VID, root=tree, platforms=["youtube"]))


def test_live_check_requires_release_tag(tree):
    assert any("missing release tag" in e for e in ship.check(VID, root=tree, live=True))


def test_delivery_rechecks_pins_before_any_mutation(tree, monkeypatch):
    from tools.post.publisher import guard_selected_for_delivery
    from tools import ship as delivery_ship
    _set(tree, release_tag="renders-test", review=None)
    monkeypatch.setattr(delivery_ship, "live_asset_digest", lambda tag, name: _queue(tree)["items"][0]["asset_digest"])
    with pytest.raises(ValueError, match="ship guard refused delivery"):
        guard_selected_for_delivery([{"video_id": VID}], root=tree)
