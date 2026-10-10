#!/usr/bin/env python3
"""Durable Google OAuth without a live sandbox callback server.

Agent: start -> give the private direct-Google link to the owner.
Owner: Google consent -> stable Pages callback -> download response JSON -> attach
privately to the agent immediately. Agent: finish <attachment-path>.

The real HTTPS callback stays registered with Google; this is NOT Google's legacy
urn:ietf:wg:oauth:2.0:oob flow. Client secret, PKCE verifier and signing key never
enter the public page, the download file or source control.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from lib.secrets import YOUTUBE_PATH
from tools.post.common import load_json
from tools.youtube.oauth_connect import (PRIVATE, PENDING, complete, make_flow,
    parse_client, secure_write, store_github_secret, verify_state)

LINK_FILE = PRIVATE / "youtube_authorization_url"


def start(client_file=None):
    client_file = Path(client_file or PRIVATE/"google_client.json")
    client = parse_client(load_json(client_file))
    pending, url = make_flow(client)  # no origin / no dependency on a sandbox host
    secure_write(PENDING, pending)
    PRIVATE.mkdir(parents=True, exist_ok=True)
    import os
    fd = os.open(LINK_FILE, os.O_WRONLY|os.O_CREAT|os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(url + "\n")
    LINK_FILE.chmod(0o600)
    return {"request_link_file": str(LINK_FILE), "expires_at": pending["expires"],
            "handoff": "file", "publishing_performed": False}


def validate_response(value, pending, now=None):
    if not isinstance(value, dict) or value.get("kind") != "hypeless-youtube-oauth-response" or value.get("version") != 1:
        raise ValueError("Attach the response file downloaded AFTER Google consent, not the original client-secret JSON")
    code, state = value.get("code"), value.get("state")
    if not isinstance(code, str) or not code or len(code) > 8192 or not isinstance(state, str) or len(state) > 4096:
        raise ValueError("Invalid OAuth response file")
    verify_state(pending, state, now=now)
    return code, state


def finish(response_file):
    response_file = Path(response_file)
    if response_file.is_symlink() or not response_file.is_file() or response_file.stat().st_size > 30_000:
        raise ValueError("Expected a small, regular OAuth response JSON file")
    response_file.chmod(0o600)
    pending = load_json(PENDING)
    code, state = validate_response(load_json(response_file), pending)
    # complete() exchanges over Google's fixed HTTPS token endpoint, validates
    # the exact expected channel, then encrypts the refresh credential for Actions.
    result = complete(pending, code, state)
    response_file.unlink(missing_ok=True)  # used, short-lived code is no longer useful
    LINK_FILE.unlink(missing_ok=True)
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("start")
    p.add_argument("--client-file")
    p = sub.add_parser("finish")
    p.add_argument("response_file")
    sub.add_parser("retry-secret-upload", help="If the token was saved locally but GitHub secret storage failed")
    args = ap.parse_args()
    try:
        if args.command == "start":
            result = start(args.client_file)
        elif args.command == "finish":
            result = finish(args.response_file)
        else:
            bundle = load_json(YOUTUBE_PATH)
            store_github_secret(bundle)
            PENDING.unlink(missing_ok=True)
            LINK_FILE.unlink(missing_ok=True)
            result = {"secret_stored": True, "publishing_performed": False}
        print(json.dumps(result, indent=2))  # no code, client secret or token printed
    except Exception as exc:
        from lib.secrets import redact
        raise SystemExit("OAuth connection not completed: " + redact(str(exc)))


if __name__ == "__main__":
    main()
