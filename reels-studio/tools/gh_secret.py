#!/usr/bin/env python3
"""GitHub Actions secrets: list them, and install one from the local vault or the environment.

Why this exists: the Buffer key has to be an Actions secret (`BUFFER_API_KEY`) for the delivery
workflow to schedule posts. Setting it by hand in the GitHub UI needs a browser and an admin
login; this tool does the same thing with the PAT alone — it fetches the repository's public
encryption key, seals the value with it (libsodium sealed box) and uploads the ciphertext.

The VALUE IS NEVER PRINTED, NEVER LOGGED and never written to the repository.

  python3 tools/gh_secret.py list                          # names + timestamps only
  python3 tools/gh_secret.py set BUFFER_API_KEY             # from $BUFFER_API_KEY or the local vault
  python3 tools/gh_secret.py set BUFFER_API_KEY --from-file C:\\secure\\buffer.txt
  python3 tools/gh_secret.py set BUFFER_API_KEY --from-env OTHER_VAR

Requires a token that can read/write repository secrets (classic PAT: `repo` scope, or a
fine-grained PAT with "Secrets: write" on the repository).
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.secrets import gh_token, register_sensitive  # noqa: E402

API = "https://api.github.com/repos/zainkhan122/yt-tts"


def _headers(token: str) -> dict:
    return {"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "reels-studio"}


def _request(method: str, path: str, token: str, body=None):
    import urllib.request
    req = urllib.request.Request(API + path, method=method, headers=_headers(token),
                                 data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw or b"{}")
        except json.JSONDecodeError:
            return e.code, {"message": raw.decode("utf-8", "replace")[:200]}


def list_secrets(token: str) -> int:
    status, data = _request("GET", "/actions/secrets?per_page=100", token)
    if status != 200:
        print(f"cannot list secrets: HTTP {status} {data.get('message', '')}", file=sys.stderr)
        return 1
    secrets = data.get("secrets") or []
    if not secrets:
        print("no Actions secrets set on this repository")
        return 0
    print(f"{len(secrets)} Actions secret(s):")
    for s in secrets:
        print(f"  {s.get('name', '?'):28s} updated {s.get('updated_at', '?')}")
    return 0


def set_secret(token: str, name: str, value: str) -> int:
    if not value.strip():
        print(f"refusing to set an empty value for {name}", file=sys.stderr)
        return 2
    register_sensitive(value)
    status, key = _request("GET", "/actions/secrets/public-key", token)
    if status != 200:
        print(f"cannot read the repository encryption key: HTTP {status} {key.get('message', '')}", file=sys.stderr)
        print("the token needs secret write access to this repository", file=sys.stderr)
        return 1
    try:
        from nacl.public import PublicKey, SealedBox
    except ImportError:
        print("pynacl is required to seal the secret: python3 -m pip install pynacl", file=sys.stderr)
        return 2
    ciphertext = base64.b64encode(
        SealedBox(PublicKey(base64.b64decode(key["key"]))).encrypt(value.encode())).decode()
    status, data = _request("PUT", f"/actions/secrets/{name}", token,
                             {"key_id": key["key_id"], "encrypted_value": ciphertext})
    if status not in (201, 204):
        print(f"GitHub rejected the secret: HTTP {status} {data.get('message', '')}", file=sys.stderr)
        return 1
    print(f"secret {name} stored (value not shown)")
    return 0


def read_value(args) -> str | None:
    if args.from_file:
        p = Path(args.from_file)
        if not p.exists():
            print(f"file not found: {p}", file=sys.stderr)
            return None
        return p.read_text(encoding="utf-8").strip()
    if args.from_env:
        return os.environ.get(args.from_env, "").strip()
    from lib.secrets import buffer_token  # the local vault copy, if any
    return (buffer_token() or "").strip()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    p = sub.add_parser("set")
    p.add_argument("name")
    p.add_argument("--from-file")
    p.add_argument("--from-env")
    a = ap.parse_args(argv)

    token = gh_token()
    if not token:
        print("no GitHub token: set GH_TOKEN or save one at ~/.config/reels-studio/gh_token", file=sys.stderr)
        return 1

    if a.cmd == "list":
        return list_secrets(token)

    value = read_value(a)
    if value is None:
        return 2
    return set_secret(token, a.name, value)


if __name__ == "__main__":
    sys.exit(main())
