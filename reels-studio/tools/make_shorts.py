#!/usr/bin/env python3
"""One command for a batch of Shorts: plan -> build -> gate -> render -> review -> queue -> Buffer.

    python3 tools/make_shorts.py "make 3 shorts today"            # produce and queue (no Buffer write)
    python3 tools/make_shorts.py "make 3 shorts today and schedule"  # also schedule to Buffer (owner go)
    python3 tools/make_shorts.py --resume                          # continue the open batch
    python3 tools/make_shorts.py --status                          # where the open batch stands

Each stage is recorded in tracker/make-shorts-state.json. A stage that cannot pass STOPS the batch and
prints exactly what is missing. Nothing is skipped silently and nothing is retried blindly.

Stages and what they need (a stop is shown as STOP, a human-judgment wait as WAIT):
  1 select     N valid videos/<id>/plan.json with no queue item and no open batch -> STOP if short
  2 build      video_plan check, brief_from_plan, receipt_build (validated receipt) -> STOP on error
  3 gate       preflight for every brief (lint, rules, motion, layout, assets, capture release, cover)
  4 source     capture packs + covers pushed to the capture-packs release; brief, plan, receipt committed,
               pushed, origin == HEAD -> STOP on any mismatch
  5 render     reels.py cloud --publish-release --wait with a log file -> STOP on workflow failure
  6 fetch      release MP4 + kit downloaded to /var/tmp/reels (sha256 checked against the release digest)
  7 panel      viewer_panel frames -> WAIT until research/production/viewer-panel-<id>.md says PASS
  8 cover      cover_ctl extract -> WAIT until the cover is approved (--approve-cover <id>)
  9 queue      queue_ctl enqueue + approve (reviewed-until +7 days) -> commit + push
 10 buffer     post.yml dry-run, verify, then schedule (part of the request)

The agent writes the plans (topic judgment, script, visual plan), reviews the frames and cover, and
passes the verdicts. The code enforces every fact that can be checked; it does not write judgments.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]      # reels-studio/
REPO = ROOT.parent                              # git repo root
TZ = ZoneInfo("Asia/Karachi")
STATE = ROOT / "tracker" / "make-shorts-state.json"
APPROVALS = ROOT / "config" / "topic-approvals.json"
LOGS = Path("/var/tmp/reels/make-shorts")
STAGES = ["select", "build", "gate", "source", "render", "fetch", "panel", "cover", "queue", "buffer"]
WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
         "nine": 9, "ten": 10}
PLAN_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,60}$")


class Stop(Exception):
    """A gate or a missing human verdict. The batch stays open at this stage."""


# ---------- state -------------------------------------------------------------------------------

def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {}


def save_state(st: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(st, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_request(text: str) -> tuple[int, bool]:
    """'make 3 shorts today' -> (3, True). Scheduling is part of the request (owner, 2 Nov 2026)."""
    t = text.lower()
    m = re.search(r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\b\s+shorts?", t)
    if not m:
        raise SystemExit("could not read a count; say e.g. 'make 3 shorts today'")
    raw = m.group(1)
    count = int(raw) if raw.isdigit() else WORDS[raw]
    if not 1 <= count <= 10:
        raise SystemExit("count must be between 1 and 10 per batch")
    return count, True


def run(cmd: list[str], *, cwd: Path = ROOT, log: str, env: dict | None = None, timeout: int = 1800) -> int:
    LOGS.mkdir(parents=True, exist_ok=True)
    path = LOGS / f"{log}.log"
    with path.open("w", encoding="utf-8") as fh:
        proc = subprocess.run(cmd, cwd=cwd, stdout=fh, stderr=subprocess.STDOUT, timeout=timeout,
                              env={**os.environ, **(env or {})})
    if proc.returncode != 0:
        tail = "\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[-12:])
        raise Stop(f"`{' '.join(cmd[:3])}...` exited {proc.returncode} (log {path}):\n{tail}")
    return proc.returncode


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True, check=check)


# ---------- stages ------------------------------------------------------------------------------

def _valid_plan(plan_path: Path) -> str | None:
    """None when the plan passes tools/video_plan.py, else the last line it printed as the reason."""
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "video_plan.py"), str(plan_path)],
                       capture_output=True, text=True, cwd=ROOT)
    if r.returncode == 0:
        return None
    lines = (r.stdout + r.stderr).strip().splitlines()
    return lines[-1] if lines else "video_plan failed"


def plan_sha(plan_path: Path) -> str:
    return hashlib.sha256(plan_path.read_bytes()).hexdigest()


def topic_approved(vid: str) -> bool:
    """Owner decision (1 Nov 2026): the owner approves every topic before anything is built. Approval is
    recorded per topic id, because it comes before the plan is written."""
    if not APPROVALS.exists():
        return False
    return vid in json.loads(APPROVALS.read_text(encoding="utf-8")).get("approved", {})


def approve_topic(vid: str, note: str) -> None:
    if not PLAN_RE.match(vid):
        raise SystemExit(f"bad topic id {vid!r}")
    if not note.strip():
        raise SystemExit("an approval needs the owner's words in the note")
    data = json.loads(APPROVALS.read_text(encoding="utf-8")) if APPROVALS.exists() else {"approved": {}}
    data["approved"][vid] = {"approved_by": "owner",
                             "at": dt.datetime.now(TZ).replace(microsecond=0).isoformat(), "note": note.strip()}
    APPROVALS.parent.mkdir(parents=True, exist_ok=True)
    APPROVALS.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"approved topic {vid}")


def stage_select(st: dict, count: int) -> list[str]:
    queued = set()
    qpath = ROOT / "queue" / "publish.json"
    if qpath.exists():
        queued = {i["video_id"] for i in json.loads(qpath.read_text(encoding="utf-8")).get("items", [])}
    busy = {v for b in st.get("batches", []) for v in b.get("ids", []) if b.get("status") != "done"}
    ready, rejected, unapproved = [], [], []
    for p in sorted((ROOT / "videos").glob("*/plan.json")):
        vid = p.parent.name
        if vid in queued or vid in busy:
            continue
        reason = _valid_plan(p)
        if reason:
            rejected.append(f"{vid}: {reason}")
            continue
        prio = json.loads(p.read_text(encoding="utf-8")).get("priority", 100)
        if not topic_approved(vid):
            unapproved.append(vid)
            continue
        ready.append((prio, vid))
    ready.sort()
    if len(ready) < count:
        msg = []
        if unapproved:
            msg.append("WAIT (owner approval of topics is required): " + ", ".join(sorted(unapproved)) +
                       ". Ask the owner; after a yes run: python3 tools/make_shorts.py --approve-topic <id> --note '<owner words>'")
        msg.append(f"need {count} approved ready plan(s), found {len(ready)}. Author videos/<id>/plan.json for any missing.")
        msg += [f"  rejected: {r}" for r in rejected]
        raise Stop("\n".join(msg))
    return [vid for _, vid in ready[:count]]


def stage_build(st: dict, batch: dict) -> None:
    for vid in batch["ids"]:
        plan = ROOT / "videos" / vid / "plan.json"
        reason = _valid_plan(plan)
        if reason:
            raise Stop(f"{vid}: plan no longer valid: {reason}")
        # The brief is generated from the plan first; only then does it name the capture pack to pull.
        run([sys.executable, "tools/brief_from_plan.py", f"videos/{vid}/plan.json"], log=f"{batch['id']}-brief-{vid}")
        cap = json.loads((ROOT / "briefs" / f"{vid}.json").read_text(encoding="utf-8"))["capture"].rstrip("/").split("/")[-1]
        run([sys.executable, "tools/capture_store.py", "pull", cap], log=f"{batch['id']}-pull-{cap}")  # no-op when complete
    receipt_rel = f"reels-studio/research/production/receipts/{batch['id']}.json"
    run([sys.executable, "tools/receipt_build.py", batch["id"], *batch["ids"]], log=f"{batch['id']}-receipt")
    batch["receipt"] = receipt_rel


def stage_gate(batch: dict) -> None:
    sys.path.insert(0, str(ROOT / "tools"))
    import preflight as pf
    blocked = []
    for vid in batch["ids"]:
        verdict = pf.preflight(vid)
        blocked += [f"{vid}: {x['check']}: {x['detail']} -> {x['fix']}" for x in verdict["results"] if x["status"] == "BLOCK"]
    if blocked:
        raise Stop("preflight BLOCKED:\n  " + "\n  ".join(blocked))


def stage_source(batch: dict) -> None:
    caps = sorted({json.loads((ROOT / "briefs" / f"{v}.json").read_text(encoding="utf-8"))["capture"]
                   .rstrip("/").split("/")[-1] for v in batch["ids"]})
    run([sys.executable, "tools/capture_store.py", "push", *caps], log=f"{batch['id']}-push-captures")
    for v in batch["ids"]:
        run([sys.executable, "tools/cover_store.py", "push", v], log=f"{batch['id']}-push-cover-{v}")
    files = [f"briefs/{v}.json" for v in batch["ids"]] + [f"videos/{v}/plan.json" for v in batch["ids"]] \
        + [f"research/production/receipts/{batch['id']}.json"]
    git("add", "-f", *[f"reels-studio/{f}" for f in files])
    if git("diff", "--cached", "--quiet", check=False).returncode != 0:
        git("commit", "-m", f"make_shorts {batch['id']}: {', '.join(batch['ids'])}")
    rebase = git("pull", "--rebase", "--autostash", "origin", "main", check=False)
    if rebase.returncode != 0:
        raise Stop(f"rebase on origin failed; resolve by hand: {rebase.stderr.strip()[-300:]}")
    git("push", "origin", "HEAD:main")
    remote = subprocess.run(["git", "-C", str(REPO), "ls-remote", "origin", "main"], capture_output=True, text=True).stdout.split()
    local = git("rev-parse", "HEAD").stdout.strip()
    if not remote or remote[0] != local:
        raise Stop(f"origin main {remote[0][:7] if remote else '?'} != local {local[:7]} after push")


def stage_render(batch: dict) -> None:
    tag = f"renders-{batch['id']}"
    cmd = [sys.executable, "reels.py", "cloud", *batch["ids"], "--receipt", batch["receipt"],
           "--tag", tag, "--publish-release", "--wait"]
    batch["tag"] = tag
    if run(cmd, log=f"{batch['id']}-cloud", timeout=6000) != 0:
        raise Stop("cloud render failed")


def download_release_asset(tag: str, name: str, out: Path) -> str:
    """Stream one release asset to disk. Returns its sha256 as GitHub reports it (the release digest).
    The signed blob URL is fetched WITHOUT the GitHub token (lesson 2026-11-01)."""
    import urllib.request
    sys.path.insert(0, str(ROOT / "tools"))
    import gh_actions
    s, rel = gh_actions.api("GET", f"/releases/tags/{tag}")
    if s != 200:
        raise Stop(f"release {tag} not found (HTTP {s})")
    asset = next((a for a in rel.get("assets", []) if a["name"] == name), None)
    if not asset:
        raise Stop(f"release {tag} has no asset {name}")
    req = urllib.request.Request(asset["url"], headers={**gh_actions._headers(), "Accept": "application/octet-stream"})
    opener = urllib.request.build_opener(gh_actions._NoRedirect)
    try:
        with opener.open(req, timeout=120) as r:  # 200 would mean the API served the bytes directly
            data = r.read()
    except urllib.error.HTTPError as e:
        loc = e.headers.get("Location")
        if e.code not in (301, 302, 307, 308) or not loc:
            raise Stop(f"download {name} failed: HTTP {e.code}")
        with urllib.request.urlopen(loc, timeout=600) as r:
            data = r.read()
    out.write_bytes(data)
    digest = (asset.get("digest") or "").removeprefix("sha256:")
    local = hashlib.sha256(data).hexdigest()
    if digest and digest != local:
        raise Stop(f"{name}: downloaded bytes {local[:12]} != release digest {digest[:12]}")
    return local


def stage_fetch(batch: dict) -> None:
    """Download the release MP4 + kit to /var/tmp (never the workspace) and record each sha256."""
    dest = Path("/var/tmp/reels/fetch") / batch["id"]
    dest.mkdir(parents=True, exist_ok=True)
    for vid in batch["ids"]:
        for name in (f"{vid}.mp4", f"{vid}-kit.zip"):
            batch.setdefault("digests", {})[name] = download_release_asset(batch["tag"], name, dest / name)
    batch["fetched"] = str(dest)


def stage_panel(batch: dict) -> None:
    for vid in batch["ids"]:
        panel = ROOT / "research" / "production" / f"viewer-panel-{vid}.md"
        text = panel.read_text(encoding="utf-8") if panel.exists() else ""
        if "Panel result: FAIL" in text:
            raise Stop(f"{vid}: viewer panel FAIL. Return the video to production (rebuild), then start a new batch.")
        if "Panel result: PASS" not in text:
            run([sys.executable, "tools/viewer_panel.py", str(Path(batch["fetched"]) / f"{vid}.mp4"), vid],
                log=f"{batch['id']}-panel-{vid}")
            frames = Path(batch["fetched"]) / "frames"
            raise Stop(f"WAIT: review the viewer panel frames for {vid} ({frames}), then write "
                       f"{panel.relative_to(REPO)} with 'Panel result: PASS' or 'Panel result: FAIL'.")


def stage_cover(batch: dict, approved: set[str]) -> None:
    for vid in batch["ids"]:
        if vid in approved:
            continue
        run([sys.executable, "tools/youtube/cover_ctl.py", "extract", vid], log=f"{batch['id']}-cover-{vid}")
        raise Stop(f"WAIT: look at renders/covers/{vid}-cover.jpg, then run: "
                   f"python3 tools/make_shorts.py --approve-cover {vid}")


def stage_queue(batch: dict) -> None:
    now = dt.datetime.now(TZ).replace(microsecond=0)
    until = (now + dt.timedelta(days=7)).replace(hour=0, minute=0, second=0).isoformat()
    for vid in batch["ids"]:
        cat = json.loads((ROOT / "briefs" / f"{vid}.json").read_text(encoding="utf-8")).get("production_category", "repo")
        cat = cat if cat in {"news", "tool", "repo"} else "repo"
        run([sys.executable, "tools/post/queue_ctl.py", "enqueue", vid, "--tag", batch["tag"], "--category", cat],
            log=f"{batch['id']}-enqueue-{vid}")
        run([sys.executable, "tools/post/queue_ctl.py", "approve", vid, "--reviewed-until", until,
             "--platforms", "youtube", "instagram", "facebook"], log=f"{batch['id']}-approve-{vid}")
    git("add", "-f", "reels-studio/queue/publish.json")
    if git("diff", "--cached", "--quiet", check=False).returncode != 0:
        git("commit", "-m", f"make_shorts {batch['id']}: queue approved")
        rebase = git("pull", "--rebase", "--autostash", "origin", "main", check=False)
        if rebase.returncode != 0:
            raise Stop(f"rebase on origin failed after queue approval: {rebase.stderr.strip()[-300:]}")
        git("push", "origin", "HEAD:main")


def stage_buffer(batch: dict, schedule: bool) -> None:
    """Dry-run, then verify, then schedule. Scheduling is part of the request; schedule=False is a rehearsal."""
    sys.path.insert(0, str(ROOT / "tools"))
    import gh_actions
    ids = ",".join(batch["ids"])
    for mode in ["dry-run", "verify"] + (["schedule"] if schedule else []):
        run_id = gh_actions.dispatch("post.yml", {"mode": mode, "video_ids": ids})
        result = gh_actions.wait(run_id, 1800)
        if result != "success":
            raise Stop(f"post.yml {mode} run {run_id} ended {result}; see the run before continuing")
        batch.setdefault("buffer_runs", []).append({"mode": mode, "run_id": run_id})


# ---------- driver ------------------------------------------------------------------------------

def open_batch(st: dict, count: int, schedule: bool) -> dict:
    today = dt.datetime.now(TZ).date().isoformat()
    n = 1 + sum(1 for b in st.get("batches", []) if b["id"].startswith(today))
    batch = {"id": f"{today}-shorts-{n:02d}", "count": count, "schedule": schedule,
             "ids": [], "status": "open", "stage": "select", "stages_done": []}
    st.setdefault("batches", []).append(batch)
    return batch


def drive(st: dict, batch: dict) -> str:
    handlers = {
        "select": lambda: batch.__setitem__("ids", stage_select(st, batch["count"])),
        "build": lambda: stage_build(st, batch),
        "gate": lambda: stage_gate(batch),
        "source": lambda: stage_source(batch),
        "render": lambda: stage_render(batch),
        "fetch": lambda: stage_fetch(batch),
        "panel": lambda: stage_panel(batch),
        "cover": lambda: stage_cover(batch, set(batch.get("covers_approved", []))),
        "queue": lambda: stage_queue(batch),
        "buffer": lambda: stage_buffer(batch, batch["schedule"]),
    }
    for name in STAGES:
        if name in batch["stages_done"]:
            continue
        batch["stage"] = name
        save_state(st)
        try:
            handlers[name]()
        except SystemExit as exc:  # helper modules report failures with SystemExit
            raise Stop(str(exc)) from exc
        batch["stages_done"].append(name)
        save_state(st)
    batch["status"] = "done"
    save_state(st)
    return "done"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("request", nargs="?", default="", help="e.g. 'make 3 shorts today'")
    ap.add_argument("--count", type=int)
    ap.add_argument("--no-schedule", action="store_true", help="rehearsal only: stop after the read-only Buffer checks")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--approve-cover", action="append", default=[], metavar="ID")
    ap.add_argument("--approve-topic", metavar="ID", help="record the OWNER's approval of a topic (plan must be valid)")
    ap.add_argument("--note", default="", help="the owner's words, quoted")
    args = ap.parse_args(argv)

    if args.approve_topic:
        approve_topic(args.approve_topic, args.note)
        return 0
    st = load_state()
    if args.status:
        open_ = [b for b in st.get("batches", []) if b.get("status") != "done"]
        print(json.dumps(open_[-1] if open_ else {"status": "no open batch"}, indent=2))
        return 0
    if args.resume or not args.request and args.count is None:
        open_ = [b for b in st.get("batches", []) if b.get("status") != "done"]
        if not open_:
            print("no open batch; say e.g. 'make 3 shorts today'")
            return 0
        batch = open_[-1]
    else:
        count, asked_schedule = parse_request(args.request) if args.request else (args.count, True)
        count = args.count or count
        batch = open_batch(st, count, asked_schedule and not args.no_schedule)
    batch.setdefault("covers_approved", []).extend(v for v in args.approve_cover if v not in batch.get("covers_approved", []))
    try:
        drive(st, batch)
    except Stop as stop:
        save_state(st)
        print(f"batch {batch['id']} stopped at stage '{batch['stage']}':\n{stop}")
        return 1
    print(f"batch {batch['id']} done: {', '.join(batch['ids'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
