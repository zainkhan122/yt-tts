#!/usr/bin/env python3
"""GitHub Actions helper for reels-studio (token via lib/secrets.gh_token(); never printed).

  gh_actions.py dispatch <workflow.yml> [-i key=value ...]   start a run, print its id
  gh_actions.py wait <run_id> [--timeout 1500]               poll until done (prints job table on change)
  gh_actions.py jobs <run_id>                                job/step status table
  gh_actions.py logs <job_id> [--tail 60] [--grep REGEX]     tail of one job's log
  gh_actions.py download <run_id> <artifact> <dest_dir>      fetch + unzip an artifact
  gh_actions.py delete-artifact <run_id> <artifact>          delete a temporary artifact after Release publication
  gh_actions.py cancel <run_id>                              cancel a run (uploaded artifacts are kept)
"""
import argparse
import io
import json
import re
import stat
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from lib.secrets import gh_token  # noqa: E402

REPO = "zainkhan122/yt-tts"
API_ROOT = "https://api.github.com"
API = f"{API_ROOT}/repos/{REPO}"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def _headers():
    return {"Authorization": f"Bearer {gh_token()}", "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "reels-studio"}


def _url(path):
    """Accept repo-relative paths ('/actions/runs/1'), absolute repo paths
    ('/repos/owner/name/releases') and full URLs. Before 2026-10-12 the helper
    silently prefixed /repos/... too, producing a confusing 404 that cost real
    debugging time; both forms now work (tests/test_gh_actions.py)."""
    if path.startswith("http"):
        return path
    if path.startswith("/repos/"):
        return API_ROOT + path
    return API + path


def api(method, path, body=None, raw=False):
    req = urllib.request.Request(_url(path), method=method, headers=_headers(),
                                 data=json.dumps(body).encode() if body is not None else None)
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(req, timeout=60) as r:
            data = r.read()
            return r.status, (data if raw else json.loads(data or b"{}"))
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 307, 308):  # signed blob URL: fetch WITHOUT the GitHub token
            loc = e.headers.get("Location")
            if not loc:
                return e.code, {"message": "redirect without a Location header"}
            try:
                with urllib.request.urlopen(loc, timeout=300) as r:
                    return r.status, r.read()
            except urllib.error.HTTPError as e2:  # e.g. log blob not written yet (404)
                return e2.code, {"message": f"redirect target failed: HTTP {e2.code}"}
        return e.code, json.loads(e.read() or b"{}")


def dispatch(wf, inputs):
    t0 = time.time()
    s, d = api("POST", f"/actions/workflows/{wf}/dispatches", {"ref": "main", "inputs": inputs})
    if s != 204:
        raise SystemExit(f"dispatch failed: HTTP {s} {d.get('message')}")
    for _ in range(20):
        time.sleep(3)
        s, d = api("GET", f"/actions/workflows/{wf}/runs?event=workflow_dispatch&per_page=3")
        for run in d.get("workflow_runs", []):
            created = time.mktime(time.strptime(run["created_at"], "%Y-%m-%dT%H:%M:%SZ")) - time.timezone
            if created >= t0 - 10:
                print(run["id"])
                return run["id"]
    raise SystemExit("run did not appear")


def job_table(run_id):
    s, d = api("GET", f"/actions/runs/{run_id}/jobs?per_page=50")
    rows = []
    for j in d.get("jobs", []):
        step = next((st["name"] for st in j.get("steps", []) if st["status"] == "in_progress"), "")
        failed = next((st["name"] for st in j.get("steps", []) if st.get("conclusion") == "failure"), "")
        rows.append(f"  {j['name']:18s} {j['status']:11s} {j.get('conclusion') or '':9s} "
                    f"{('FAILED at: ' + failed) if failed else step}  (job {j['id']})")
    return "\n".join(rows)


def wait(run_id, timeout):
    last, t0 = "", time.time()
    while time.time() - t0 < timeout:
        s, run = api("GET", f"/actions/runs/{run_id}")
        tbl = job_table(run_id)
        if tbl != last:
            print(f"[{int(time.time() - t0)}s] run {run.get('status')} {run.get('conclusion') or ''}\n{tbl}", flush=True)
            last = tbl
        if run.get("status") == "completed":
            return run.get("conclusion")
        time.sleep(20)
    print("timeout (run continues in the cloud)")
    return None


def release_url(tag):
    """Return the permanent GitHub Release link after the remote batch publisher finishes."""
    status, data = api("GET", f"/releases/tags/{urllib.parse.quote(tag, safe='')}")
    if status != 200 or not data.get("html_url") or data.get("draft"):
        raise SystemExit(f"published GitHub Release {tag!r} not found (HTTP {status})")
    return data["html_url"]


def logs(job_id, tail, grep):
    s, data = api("GET", f"/actions/jobs/{job_id}/logs", raw=True)
    if not isinstance(data, bytes):  # friendly path: log blob 404s while a job is still running
        print(f"logs not available yet (HTTP {s}: {data.get('message', '')}) — the job may still be running")
        return 2
    text = data.decode("utf-8", "replace")
    lines = [re.sub(r"^\S+Z ", "", l) for l in text.splitlines()]
    if grep:
        lines = [l for l in lines if re.search(grep, l, re.I)]
    print("\n".join(lines[-tail:]))


def _find_artifact(run_id, name):
    s, d = api("GET", f"/actions/runs/{run_id}/artifacts?per_page=100")
    art = next((a for a in d.get("artifacts", []) if a["name"] == name), None)
    if not art:
        raise SystemExit(f"artifact {name} not found: {[a['name'] for a in d.get('artifacts', [])]}")
    return art


MAX_ARTIFACT_BYTES = 128_000_000
MAX_ARTIFACT_FILES = 1000


def safe_extract_artifact(blob, dest):
    """Verify a bounded Actions ZIP and reject traversal, symlinks, duplicates, and CRC errors."""
    dest = Path(dest)
    if dest.is_symlink():
        raise SystemExit(f"refusing symlink artifact destination: {dest}")
    if dest.exists() and any(dest.iterdir()):
        raise SystemExit(f"refusing to merge artifact into non-empty destination: {dest}")
    if len(blob) > MAX_ARTIFACT_BYTES:
        raise SystemExit(f"artifact ZIP exceeds size limit ({len(blob)} bytes)")
    dest.mkdir(parents=True, exist_ok=True)
    root = dest.resolve()
    try:
        archive = zipfile.ZipFile(io.BytesIO(blob))
    except zipfile.BadZipFile as exc:
        raise SystemExit(f"invalid Actions artifact ZIP: {exc}") from exc
    with archive:
        infos = archive.infolist()
        if len(infos) > MAX_ARTIFACT_FILES:
            raise SystemExit(f"artifact has too many entries ({len(infos)})")
        total = sum(info.file_size for info in infos)
        if total > MAX_ARTIFACT_BYTES:
            raise SystemExit(f"artifact expands beyond size limit ({total} bytes)")
        seen = set()
        for info in infos:
            name = info.filename
            rel = PurePosixPath(name)
            if (not name or "\\" in name or rel.is_absolute() or ".." in rel.parts
                    or not rel.parts or ":" in rel.parts[0]):
                raise SystemExit(f"unsafe artifact path: {name!r}")
            mode = (info.external_attr >> 16) & 0o170000
            if mode == stat.S_IFLNK:
                raise SystemExit(f"refusing symlink in artifact: {name!r}")
            target = (root / Path(*rel.parts)).resolve()
            try:
                target.relative_to(root)
            except ValueError as exc:
                raise SystemExit(f"artifact path escapes destination: {name!r}") from exc
            norm = str(target)
            if norm in seen:
                raise SystemExit(f"duplicate artifact path: {name!r}")
            seen.add(norm)
        bad = archive.testzip()
        if bad is not None:
            raise SystemExit(f"artifact CRC check failed at {bad!r}")
        archive.extractall(root)
    return len(infos), total


def artifact_size(run_id, name):
    """Return the compressed byte size reported by Actions before downloading."""
    art = _find_artifact(run_id, name)
    try:
        size = int(art.get("size_in_bytes", 0))
    except (TypeError, ValueError) as exc:
        raise SystemExit(f"artifact {name} has an invalid size in the Actions API") from exc
    if size <= 0:
        raise SystemExit(f"artifact {name} has no recorded bytes")
    return size


def download(run_id, name, dest):
    art = _find_artifact(run_id, name)
    s, blob = api("GET", art["archive_download_url"], raw=True)
    if s != 200 or not isinstance(blob, bytes):
        raise SystemExit(f"artifact download failed: HTTP {s}")
    count, expanded = safe_extract_artifact(blob, dest)
    print(f"{name}: verified ZIP {len(blob) / 1e6:.1f} MB, expanded {expanded / 1e6:.1f} MB, {count} entries -> {dest}")


def delete_artifact(run_id, name):
    """Remove a temporary render artifact after its files have been published to a GitHub Release."""
    art = _find_artifact(run_id, name)
    s, d = api("DELETE", f"/actions/artifacts/{art['id']}")
    if s != 204:
        raise SystemExit(f"artifact delete failed: HTTP {s} {d.get('message', '')}")
    print(f"{name}: temporary Actions artifact deleted")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("dispatch"); p.add_argument("workflow"); p.add_argument("-i", "--input", action="append", default=[])
    p = sub.add_parser("wait"); p.add_argument("run_id"); p.add_argument("--timeout", type=int, default=1500)
    p = sub.add_parser("jobs"); p.add_argument("run_id")
    p = sub.add_parser("logs"); p.add_argument("job_id"); p.add_argument("--tail", type=int, default=60); p.add_argument("--grep")
    p = sub.add_parser("download"); p.add_argument("run_id"); p.add_argument("artifact"); p.add_argument("dest")
    p = sub.add_parser("delete-artifact"); p.add_argument("run_id"); p.add_argument("artifact")
    p = sub.add_parser("cancel"); p.add_argument("run_id")
    a = ap.parse_args()
    if a.cmd == "dispatch":
        dispatch(a.workflow, dict(kv.split("=", 1) for kv in a.input))
    elif a.cmd == "wait":
        print("conclusion:", wait(a.run_id, a.timeout))
    elif a.cmd == "jobs":
        print(job_table(a.run_id))
    elif a.cmd == "logs":
        logs(a.job_id, a.tail, a.grep)
    elif a.cmd == "cancel":
        s, d = api("POST", f"/actions/runs/{a.run_id}/cancel")
        print("cancel:", s, "(202 = accepted)")
    elif a.cmd == "download":
        download(a.run_id, a.artifact, a.dest)
    else:
        delete_artifact(a.run_id, a.artifact)


if __name__ == "__main__":
    main()
