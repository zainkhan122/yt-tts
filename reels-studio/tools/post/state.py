"""Durable write-ahead journal. Commit reservation BEFORE any Buffer mutation.

GitHub Contents API is used with a file SHA (compare-and-swap). A race, lost GitHub
response or write failure stops processing. Concurrency in post.yml serializes runs.
There is deliberately no force push and no retry of a conflicted journal write.
"""
import base64
import copy
import json

import requests

from lib.secrets import gh_token
from tools.post.common import ROOT, load_json, save_json

PATH = "reels-studio/tracker/publications.json"


class Journal:
    def __init__(self, cfg, remote=False, path=None, session=None):
        self.path = path or ROOT / "tracker/publications.json"
        self.remote = remote
        self.cfg = cfg
        self.session = session or requests.Session()
        self.sha = None
        if remote:
            token = gh_token()
            if not token:
                raise RuntimeError("GitHub token missing; cannot persist a write-ahead journal")
            self.headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
            self.url = f"https://api.github.com/repos/{cfg['repository']}/contents/{PATH}"
            r = self.session.get(self.url, headers=self.headers, params={"ref": cfg.get("branch", "main")}, timeout=(10, 30))
            if r.status_code != 200:
                raise RuntimeError(f"Cannot read durable journal (HTTP {r.status_code})")
            body = r.json()
            self.sha = body["sha"]
            self.data = json.loads(base64.b64decode(body["content"]))
        else:
            self.data = load_json(self.path)
        self.saved = copy.deepcopy(self.data)

    @property
    def records(self):
        return self.data["records"]

    def save(self, reason):
        if self.data == self.saved:
            return
        if self.remote:
            payload = {"message": "publishing: " + reason[:120], "branch": self.cfg.get("branch", "main"), "sha": self.sha,
                       "content": base64.b64encode((json.dumps(self.data, indent=2, sort_keys=True) + "\n").encode()).decode()}
            try:
                r = self.session.put(self.url, headers=self.headers, json=payload, timeout=(10, 30))
            except requests.RequestException as exc:
                raise RuntimeError("Journal write uncertain; stop before any further Buffer request") from exc
            if r.status_code != 200:
                raise RuntimeError(f"Journal write failed/conflicted (HTTP {r.status_code}); publishing stopped")
            self.sha = r.json()["content"]["sha"]
        save_json(self.path, self.data)
        self.saved = copy.deepcopy(self.data)
