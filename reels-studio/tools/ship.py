#!/usr/bin/env python3
"""Ship state: one record per Short, in queue/publish.json. Nothing else decides.

State of a Short (the queue item is the only state; every other file is an input pinned by hash):

  enqueued (approval=held)      enqueue pins brief canonical hash and the release asset digest
  pinned (item.review set)      enqueue pins the MP4 identity from the release asset digest (automatic);
                                 the viewer panel must state the same sha256 ("Video sha256: <hex>")
  approved (approval=approved)  queue_ctl approve runs check() and pins the panel file hash
  scheduled                     post.yml writes Buffer receipts (derived log, never read for decisions)

Items with ship_legacy=true were scheduled before this guard existed. They are listed, not checked.

Commands:
  python3 tools/ship.py review <video_id> --mp4 <file> --run <actions_run_id> [--cover <file>]
  python3 tools/ship.py check <video_id> [--live]   exit 0 only if every link agrees
  python3 tools/ship.py check-all [--live]          check every approved, non-legacy item (CI runs this)
  python3 tools/ship.py pin-held                    pin review for held items enqueued before this change
  --live compares the queued digest with the digest GitHub reports for the release asset right now.

Rules: gates are code. Vision and human notes are advisory. Free text is never a verdict:
the panel verdict is read only from its own "Panel result:" line.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from brief_identity import identity  # noqa: E402  (the one brief identity)

VALID_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{2,80}$")
PANEL_LINE = re.compile(r"^Panel result:\s*(PASS|FAIL)\b", re.MULTILINE)
PANEL_SHA = re.compile(r"^Video sha256:\s*([0-9a-f]{64})\b", re.MULTILINE)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _valid(video_id: str) -> str:
    if not VALID_ID.match(video_id):
        raise SystemExit(f"bad video id: {video_id!r}")
    return video_id


def _queue_path(root: Path) -> Path:
    return root / "queue" / "publish.json"


def _item(queue: dict, video_id: str):
    return next((i for i in queue.get("items", []) if i.get("video_id") == video_id), None)


def panel_file(video_id: str, root: Path) -> Path | None:
    files = sorted((root / "research" / "production").glob(f"viewer-panel-*{video_id}*.md"))
    return files[-1] if files else None


def panel_verdict(video_id: str, root: Path) -> str | None:
    f = panel_file(video_id, root)
    if not f:
        return None
    found = PANEL_LINE.findall(f.read_text(encoding="utf-8", errors="replace"))
    return found[-1] if found else None


def panel_video_sha(video_id: str, root: Path) -> str | None:
    f = panel_file(video_id, root)
    if not f:
        return None
    found = PANEL_SHA.findall(f.read_text(encoding="utf-8", errors="replace"))
    return found[-1] if found else None


def release_review(asset_digest: str | None, asset_bytes: int | None) -> dict:
    """Automatic review at enqueue: the release asset's own sha256 digest identifies the bytes."""
    if not asset_digest or not asset_digest.startswith("sha256:") or len(asset_digest) != 71:
        raise SystemExit(f"release asset has no usable sha256 digest ({asset_digest!r}); cannot pin the review")
    return {"mp4_sha256": asset_digest[7:], "mp4_bytes": asset_bytes, "source": "release-digest",
            "run_id": None, "cover_sha256": None}


def live_asset_digest(tag: str, name: str) -> str | None:
    """Digest GitHub reports for a release asset right now (needs GH_TOKEN or GITHUB_TOKEN)."""
    import os
    import urllib.request
    repo = os.environ.get("GITHUB_REPOSITORY", "zainkhan122/yt-tts")
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}/releases/tags/{tag}",
                                 headers={"Accept": "application/vnd.github+json",
                                          **({"Authorization": f"Bearer {token}"} if token else {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode("utf-8"))
    for a in data.get("assets", []):
        if a.get("name") == name:
            return a.get("digest")
    return None


def panel_sha(video_id: str, root: Path) -> str | None:
    f = panel_file(video_id, root)
    return sha256_file(f) if f else None


def latest_receipt_pin(video_id: str, root: Path):
    """(receipt name, brief_identity_sha256) from the latest receipt that pins this brief."""
    pinned = None
    for rp in sorted((root / "research" / "production" / "receipts").glob("*.json")):
        entry = (_load(rp).get("briefs") or {}).get(video_id)
        if entry:
            pinned = (rp.name, entry.get("brief_identity_sha256"))  # latest by name governs
    return pinned


def review(video_id: str, mp4: Path, run_id: str, cover: Path | None = None, *, root: Path = ROOT) -> dict:
    """Record the review on the queue item. The MP4 must be byte-identical to the released asset."""
    _valid(video_id)
    if not mp4.is_file():
        raise SystemExit(f"no such file: {mp4}")
    if not run_id.isdigit():
        raise SystemExit("--run must be the numeric Actions run id")
    qp = _queue_path(root)
    queue = _load(qp)
    item = _item(queue, video_id)
    if item is None:
        raise SystemExit(f"{video_id} is not enqueued; enqueue first (the release asset must exist)")
    digest = sha256_file(mp4)
    if item.get("asset_digest") != "sha256:" + digest:
        raise SystemExit(f"local MP4 sha256 {digest[:12]} is not the released asset {str(item.get('asset_digest'))[:19]}; "
                         "download the asset from the release, not from another run")
    item["review"] = {
        "mp4_sha256": digest,
        "mp4_bytes": mp4.stat().st_size,
        "run_id": run_id,
        "cover_sha256": sha256_file(cover) if cover else None,
    }
    _save(qp, queue)
    return item["review"]


def check(video_id: str, *, root: Path = ROOT, live: bool = False) -> list[str]:
    """Return drift errors. Empty list means every link agrees."""
    _valid(video_id)
    qp = _queue_path(root)
    queue = _load(qp)
    item = _item(queue, video_id)
    if item is None:
        return ["queue: item not queued"]
    if item.get("ship_legacy"):
        return []  # explicitly grandfathered; see ship_legacy_reason
    errors: list[str] = []

    brief_path = root / "briefs" / f"{video_id}.json"
    if not brief_path.exists():
        return [f"brief missing: briefs/{video_id}.json"]
    brief_id_now = identity(_load(brief_path))

    pin = latest_receipt_pin(video_id, root)
    if pin is None:
        errors.append("receipt: no receipt pins this brief")
    elif pin[1] is None:
        errors.append(f"receipt {pin[0]}: no brief_identity_sha256 (receipt predates the identity pin; rebuild it)")
    elif pin[1] != brief_id_now:
        errors.append(f"receipt {pin[0]}: brief identity {str(pin[1])[:12]} != brief {brief_id_now[:12]} (brief edited after receipt)")
    if item.get("brief_sha256") != brief_id_now:
        errors.append(f"queue: brief identity {str(item.get('brief_sha256'))[:12]} != brief {brief_id_now[:12]}")

    review_rec = item.get("review")
    if not review_rec:
        errors.append("review: not reviewed (scheduled file must be reviewed before approval)")
    else:
        if item.get("asset_digest") != "sha256:" + review_rec.get("mp4_sha256", ""):
            errors.append("artifact: reviewed MP4 is not the released asset")
        if "youtube" in (item.get("platforms") or []):
            if not item.get("cover_sha256"):
                errors.append("cover: youtube is scheduled but no cover is approved")
            elif review_rec.get("cover_sha256") and review_rec["cover_sha256"] != item["cover_sha256"]:
                errors.append("cover: queued cover differs from the reviewed cover")

    if review_rec:
        pv = panel_video_sha(video_id, root)
        if pv != review_rec.get("mp4_sha256"):
            errors.append(f"panel: panel states video sha256 {str(pv)[:12]} but the released file is {review_rec.get('mp4_sha256','')[:12]} (reviewed a different file)")
    if live and item.get("release_tag"):
        name = f"{video_id}.mp4"
        now = live_asset_digest(item["release_tag"], name)
        if now != item.get("asset_digest"):
            errors.append(f"release: live asset digest {str(now)[:19]} != queued {str(item.get('asset_digest'))[:19]} (asset replaced on GitHub)")

    try:
        import package_lint
        brief_for_pkg = _load(brief_path)
        pres = package_lint.pairing(brief_for_pkg, package_lint.cover_text_for(video_id, root))
        if pres is not None and not item.get("package_pairing_grandfathered"):
            errors += [f"package {e}" for e in package_lint.blocking_errors(pres)]
    except Exception as exc:
        errors.append(f"package: pairing lint failed to run ({exc})")

    insp = (_load(brief_path).get("inspiration") or {})
    if insp:
        ref = (root / "research" / "references"
               / f"{insp.get('platform')}-{insp.get('source')}-{insp.get('post_id')}")
        td = ref / "teardown.md"
        if not td.exists():
            errors.append(f"teardown: brief cites inspiration but {td.relative_to(root)} is missing "
                          "(run tools/reference_teardown.py on the source short)")
        elif "AGENT-TODO" in td.read_text(encoding="utf-8", errors="replace"):
            errors.append("teardown: teardown.md still has [AGENT-TODO] sections — complete the analysis "
                          "(hook/beats/media/colour/take-avoid) before approval")
        if not (ref / "manifest.json").exists():
            errors.append("teardown: manifest.json missing beside teardown.md")

    verdict = panel_verdict(video_id, root)
    if verdict != "PASS":
        errors.append(f"panel: verdict is {verdict or 'missing'} (approval needs PASS)")
    if item.get("approval") == "approved":
        if not item.get("approved_panel_sha"):
            errors.append("panel: approved without a pinned panel record")
        elif item["approved_panel_sha"] != panel_sha(video_id, root):
            errors.append("panel: panel file changed after approval")
        if "youtube" in (item.get("platforms") or []):
            if not item.get("approved_cover_sha"):
                errors.append("cover: approved without a pinned cover")
            elif item["approved_cover_sha"] != item.get("cover_sha256"):
                errors.append("cover: changed after approval")
    return errors


def check_all(*, root: Path = ROOT, live: bool = False) -> dict[str, list[str]]:
    queue = _load(_queue_path(root))
    out = {}
    for i in queue.get("items", []):
        if i.get("ship_legacy") or i.get("approval") != "approved":
            continue
        errs = check(i["video_id"], root=root, live=live)
        if errs:
            out[i["video_id"]] = errs
    return out


def pin_held(*, root: Path = ROOT) -> list[str]:
    """Pin the review for held items that were enqueued before automatic pinning existed."""
    qp = _queue_path(root)
    queue = _load(qp)
    pinned = []
    for i in queue.get("items", []):
        if i.get("approval") == "held" and not i.get("review") and not i.get("ship_legacy"):
            i["review"] = release_review(i.get("asset_digest"), i.get("asset_size"))
            pinned.append(i["video_id"])
    if pinned:
        _save(qp, queue)
    return pinned


def record_approval(video_id: str, *, root: Path = ROOT) -> None:
    """Called by queue_ctl after the guard passes: pin the panel file that justified approval."""
    queue = _load(_queue_path(root))
    item = _item(queue, video_id)
    item["approved_panel_sha"] = panel_sha(video_id, root)
    item["approved_cover_sha"] = item.get("cover_sha256")
    _save(_queue_path(root), queue)


def next_action(video_id: str, *, root: Path = ROOT) -> str:
    """The single next step for a Short, derived from the queue state and the guard. Read-only."""
    _valid(video_id)
    queue = _load(_queue_path(root))
    item = _item(queue, video_id)
    if item is None:
        return "render in the cloud (reels.py cloud --publish-release --wait), then queue_ctl enqueue"
    if item.get("ship_legacy"):
        return "none: legacy item (scheduled before the guard)"
    if item.get("approval") == "approved":
        errs = check(video_id, root=root)
        return "approved and consistent: wait for post.yml schedule" if not errs else "fix drift: " + "; ".join(errs)
    if not item.get("review"):
        return "pin review: python3 tools/ship.py pin-held"
    errs = check(video_id, root=root)
    if errs:
        panel_errs = [e for e in errs if e.startswith("panel")]
        other = [e for e in errs if not e.startswith("panel")]
        if other:
            return "fix drift: " + "; ".join(other)
        return "viewer panel: review the frames, then write Video sha256 and Panel result in " + \
               f"research/production/viewer-panel-{video_id}.md ({'; '.join(panel_errs)})"
    return ("ready: python3 tools/post/queue_ctl.py approve " + video_id +
            " --reviewed-until <ISO time within 14 days> --platforms " + " ".join(item.get("platforms") or []))


def render_status(*, root: Path = ROOT) -> str:
    """Deterministic status view of the queue. Generated, never edited by hand."""
    queue = _load(_queue_path(root))
    items = queue.get("items", [])
    lines = ["# Shorts status (generated from queue/publish.json)", "",
             "Do not edit by hand. Regenerate: `python3 tools/ship.py status --write`. CI fails if this file is stale.", ""]
    counts: dict[str, int] = {}
    for i in items:
        key = "legacy" if i.get("ship_legacy") else i.get("approval", "unknown")
        counts[key] = counts.get(key, 0) + 1
    lines.append("## Counts")
    lines += [f"- {k}: {v}" for k, v in sorted(counts.items())]
    lines += ["", "## Open items (not legacy, not yet approved)", "", "| Short | Next action |", "|---|---|"]
    open_items = [i for i in items if not i.get("ship_legacy") and i.get("approval") != "approved"]
    for i in open_items:
        lines.append(f"| {i['video_id']} | {next_action(i['video_id'], root=root)} |")
    if not open_items:
        lines.append("| (none) | |")
    bad = check_all(root=root)
    lines += ["", "## Approved items that disagree with their pins", ""]
    lines += [f"- {v}: " + "; ".join(e) for v, e in bad.items()] or ["- none"]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("review")
    r.add_argument("video_id")
    r.add_argument("--mp4", required=True, type=Path)
    r.add_argument("--run", required=True)
    r.add_argument("--cover", type=Path)
    c = sub.add_parser("check")
    c.add_argument("video_id")
    c.add_argument("--live", action="store_true")
    sub.add_parser("pin-held")
    nx = sub.add_parser("next")
    nx.add_argument("video_id")
    st = sub.add_parser("status")
    st.add_argument("--write", action="store_true")
    st.add_argument("--check", action="store_true")
    ca = sub.add_parser("check-all")
    ca.add_argument("--live", action="store_true")
    args = ap.parse_args(argv)
    if args.cmd == "next":
        print(next_action(args.video_id))
        return 0
    if args.cmd == "status":
        text = render_status()
        target = ROOT / "STATUS.md"
        if args.write:
            target.write_text(text, encoding="utf-8")
            print("wrote STATUS.md")
            return 0
        if args.check:
            current = target.read_text(encoding="utf-8") if target.exists() else ""
            if current != text:
                print("STATUS.md is stale: run python3 tools/ship.py status --write")
                return 1
            print("STATUS.md is current")
            return 0
        print(text, end="")
        return 0
    if args.cmd == "pin-held":
        print("pinned: " + (", ".join(pin_held()) or "none"))
        return 0
    if args.cmd == "review":
        print(json.dumps(review(args.video_id, args.mp4, args.run, args.cover), indent=2))
        return 0
    if args.cmd == "check":
        errors = check(args.video_id, live=args.live)
        print("OK" if not errors else "DRIFT:\n  - " + "\n  - ".join(errors))
        return 0 if not errors else 1
    bad = check_all(live=args.live)
    for vid, errs in bad.items():
        print(f"{vid}:\n  - " + "\n  - ".join(errs))
    print("OK: all approved items agree" if not bad else f"DRIFT in {len(bad)} item(s)")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
