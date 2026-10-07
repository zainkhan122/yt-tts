#!/usr/bin/env python3
"""GitHub Actions helper for reels-studio (token via lib/secrets.gh_token(); never printed).

  gh_actions.py dispatch <workflow.yml> [-i key=value ...]   start a run, print its id
  gh_actions.py wait <run_id> [--timeout 1500]               poll until done (prints job table on change)
  gh_actions.py jobs <run_id>                                job/step status table
  gh_actions.py logs <job_id> [--tail 60] [--grep REGEX]     tail of one job's log
  gh_actions.py download <run_id> <artifact> <dest_dir>      fetch + unzip an artifact
"""
import argparse
import io
import json
import re
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from lib.secrets import gh_token  # noqa: E402

REPO = "zainkhan122/yt-tts"
API = f"https://api.github.com/repos/{REPO}"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def _headers():
    return {"Authorization": f"Bearer {gh_token()}", "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "reels-studio"}


def api(method, path, body=None, raw=False):
    req = urllib.request.Request(path if path.startswith("http") else API + path, method=method, headers=_headers(),
                                 data=json.dumps(body).encode() if body is not None else None)
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(req, timeout=60) as r:
            data = r.read()
            return r.status, (data if raw else json.loads(data or b"{}"))
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 307, 308):  # signed blob URL: fetch WITHOUT the GitHub token
            with urllib.request.urlopen(e.headers["Location"], timeout=300) as r:
                return r.status, r.read()
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


def logs(job_id, tail, grep):
    s, data = api("GET", f"/actions/jobs/{job_id}/logs", raw=True)
    text = data.decode("utf-8", "replace") if isinstance(data, bytes) else str(data)
    lines = [re.sub(r"^\S+Z ", "", l) for l in text.splitlines()]
    if grep:
        lines = [l for l in lines if re.search(grep, l, re.I)]
    print("\n".join(lines[-tail:]))


def download(run_id, name, dest):
    s, d = api("GET", f"/actions/runs/{run_id}/artifacts?per_page=100")
    art = next((a for a in d.get("artifacts", []) if a["name"] == name), None)
    if not art:
        raise SystemExit(f"artifact {name} not found: {[a['name'] for a in d.get('artifacts', [])]}")
    s, blob = api("GET", art["archive_download_url"], raw=True)
    Path(dest).mkdir(parents=True, exist_ok=True)
    zipfile.ZipFile(io.BytesIO(blob)).extractall(dest)
    print(f"{name}: {len(blob) / 1e6:.1f} MB -> {dest}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("dispatch"); p.add_argument("workflow"); p.add_argument("-i", "--input", action="append", default=[])
    p = sub.add_parser("wait"); p.add_argument("run_id"); p.add_argument("--timeout", type=int, default=1500)
    p = sub.add_parser("jobs"); p.add_argument("run_id")
    p = sub.add_parser("logs"); p.add_argument("job_id"); p.add_argument("--tail", type=int, default=60); p.add_argument("--grep")
    p = sub.add_parser("download"); p.add_argument("run_id"); p.add_argument("artifact"); p.add_argument("dest")
    a = ap.parse_args()
    if a.cmd == "dispatch":
        dispatch(a.workflow, dict(kv.split("=", 1) for kv in a.input))
    elif a.cmd == "wait":
        print("conclusion:", wait(a.run_id, a.timeout))
    elif a.cmd == "jobs":
        print(job_table(a.run_id))
    elif a.cmd == "logs":
        logs(a.job_id, a.tail, a.grep)
    else:
        download(a.run_id, a.artifact, a.dest)


if __name__ == "__main__":
    main()
