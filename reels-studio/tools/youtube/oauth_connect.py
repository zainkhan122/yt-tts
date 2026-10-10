#!/usr/bin/env python3
"""One-time, owner-only Google OAuth connector. Never asks for a Google password.

The preferred flow is tools/youtube/oauth_handoff.py: a direct Google URL and
stable Pages callback, with a one-time private response-file handoff. It survives
sandbox replacement. The optional HTTP connector below is legacy/session-local.
"""
import argparse
import base64
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets as random_secrets
import sys
import time
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from nacl.public import PublicKey, SealedBox

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from lib.secrets import YOUTUBE_PATH, gh_token, register_sensitive
from tools.post.common import config, load_json
from tools.youtube.api import SCOPES, TOKEN_ENDPOINT

PRIVATE = Path.home()/".config/reels-studio"
PENDING = PRIVATE/"youtube_oauth_pending.json"
CALLBACK = "https://zainkhan122.github.io/yt-tts/oauth/callback/"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"


def b64(value):
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def unb64(value):
    return base64.urlsafe_b64decode(value + "="*(-len(value) % 4))


def valid_origin(value):
    p = urlparse(value)
    if p.scheme != "https" or not p.hostname or not p.hostname.endswith(".e2b.app") or p.port not in (None,443) or p.username or p.password or p.path not in ("", "/"):
        raise ValueError("Use the HTTPS live-preview host, not localhost or an iframe file preview")
    return "https://" + p.hostname


def secure_write(path, value):
    PRIVATE.mkdir(parents=True, exist_ok=True)
    PRIVATE.chmod(0o700)
    fd = os.open(path, os.O_WRONLY|os.O_CREAT|os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(value, f)
    Path(path).chmod(0o600)


def parse_client(value):
    client = value.get("web")
    if not isinstance(client, dict) or not str(client.get("client_id", "")).endswith(".apps.googleusercontent.com") or not client.get("client_secret"):
        raise ValueError("Upload a Google OAuth WEB APPLICATION client JSON, not an API key/service-account/Desktop file")
    if CALLBACK not in client.get("redirect_uris", []):
        raise ValueError("Add the exact callback URL shown here to this Web client's authorized redirect URIs, then download the JSON again")
    # Do not trust auth_uri/token_uri supplied in an uploaded JSON; endpoints are fixed.
    register_sensitive(client["client_secret"])
    return {"client_id": client["client_id"], "client_secret": client["client_secret"]}


def make_flow(client, origin=None, now=None):
    now = int(now if now is not None else time.time())
    # Request link can survive a sandbox replacement. The authorization code that
    # Google later issues is STILL short-lived and must be exchanged promptly.
    manual = origin is None
    if not manual:
        origin = valid_origin(origin)
    expires = now + (86400 if manual else 1800)
    signing = random_secrets.token_bytes(32)
    verifier = random_secrets.token_urlsafe(48)
    fields = {"nonce": random_secrets.token_urlsafe(24), "expires": expires}
    fields.update({"handoff": "file"} if manual else {"origin": origin})
    payload = b64(json.dumps(fields, separators=(",", ":")).encode())
    state = payload + "." + b64(hmac.new(signing, payload.encode(), hashlib.sha256).digest())
    pending = {"client": client, "verifier": verifier, "state": state, "signing": b64(signing), "expires": expires}
    pending.update({"handoff": "file"} if manual else {"origin": origin})
    query = {"client_id": client["client_id"], "redirect_uri": CALLBACK, "response_type": "code", "scope": " ".join(SCOPES),
             "access_type": "offline", "prompt": "consent", "include_granted_scopes": "true", "state": state,
             "code_challenge": b64(hashlib.sha256(verifier.encode()).digest()), "code_challenge_method": "S256"}
    return pending, AUTH_URL + "?" + urlencode(query)


def verify_state(pending, state, now=None):
    now = int(now if now is not None else time.time())
    if not state or not hmac.compare_digest(pending["state"], state) or now > pending["expires"]:
        raise ValueError("OAuth session expired or state did not match; start a fresh connection")
    try:
        payload, signature = state.split(".")
        expected = b64(hmac.new(unb64(pending["signing"]), payload.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError()
        decoded = json.loads(unb64(payload))
        if decoded.get("expires") != pending["expires"]:
            raise ValueError()
        if pending.get("handoff") == "file":
            if decoded.get("handoff") != "file" or "origin" in decoded:
                raise ValueError()
        elif valid_origin(decoded["origin"]) != pending["origin"]:
            raise ValueError()
    except (ValueError, KeyError):
        raise ValueError("Invalid OAuth state")


def store_github_secret(bundle):
    token = gh_token()
    if not token:
        raise ValueError("GitHub token missing; credentials were saved privately but cloud connection is not complete")
    base = "https://api.github.com/repos/" + config()["repository"]
    headers = {"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    r = requests.get(base+"/actions/secrets/public-key", headers=headers, timeout=30)
    if r.status_code != 200:
        raise ValueError("Cannot access GitHub's secret encryption key")
    key = r.json()
    ciphertext = base64.b64encode(SealedBox(PublicKey(base64.b64decode(key["key"]))).encrypt(json.dumps(bundle).encode())).decode()
    r = requests.put(base+"/actions/secrets/YOUTUBE_OAUTH_JSON", headers=headers,
                     json={"key_id": key["key_id"], "encrypted_value": ciphertext}, timeout=30)
    if r.status_code not in (201,204):
        raise ValueError("GitHub rejected encrypted secret storage; check Secrets write permission")


def complete(pending, code, state, session=requests):
    verify_state(pending, state)
    if not isinstance(code, str) or not code or len(code) > 8192:
        raise ValueError("Google authorization was cancelled or did not return a valid code")
    register_sensitive(code)
    r = session.post(TOKEN_ENDPOINT, data={**pending["client"], "code": code, "grant_type": "authorization_code",
                     "redirect_uri": CALLBACK, "code_verifier": pending["verifier"]}, timeout=(10,30), allow_redirects=False)
    if r.status_code != 200:
        raise ValueError("Google did not complete authorization. Reconnect; no publishing occurred.")
    token = r.json()
    if not token.get("refresh_token") or not token.get("access_token"):
        raise ValueError("Google did not grant offline access; reconnect with consent")
    for key in ("refresh_token", "access_token"):
        register_sensitive(token[key])
    if token.get("scope") and not set(SCOPES).issubset(set(token["scope"].split())):
        raise ValueError("Required YouTube permission was not granted")
    r = session.get("https://www.googleapis.com/youtube/v3/channels", params={"part": "id,snippet", "mine": "true"},
                    headers={"Authorization": "Bearer " + token["access_token"]}, timeout=30, allow_redirects=False)
    expected = load_json(ROOT/"config/youtube.json")["channel_id"]
    if r.status_code != 200 or not any(c["id"] == expected for c in r.json().get("items", [])):
        raise ValueError("This authorization is not for the expected Hypeless channel. Choose the correct Google/Brand channel.")
    bundle = {**pending["client"], "refresh_token": token["refresh_token"], "channel_id": expected,
              "scopes": SCOPES, "connected_at": int(time.time())}
    if token.get("refresh_token_expires_in"):
        bundle["refresh_token_expires_at"] = int(time.time()) + int(token["refresh_token_expires_in"])
    secure_write(YOUTUBE_PATH, bundle)
    store_github_secret(bundle)
    PENDING.unlink(missing_ok=True)
    return {"connected": True, "channel_id": expected, "secret_stored": True, "publishing_enabled": bool(load_json(ROOT/"config/youtube.json").get("enabled"))}


STYLE = "body{background:#050b1f;color:#eaf0ff;font:17px/1.6 system-ui;margin:0;padding:36px}main{max-width:760px;margin:auto}h1{color:#ffd60a;font-size:42px;line-height:1.1}a{color:#38bdf8}section{background:#10203a;padding:24px;border-radius:16px;margin:20px 0}button,.button{background:#ffd60a;color:#050b1f;border:0;padding:14px 20px;font-weight:800;border-radius:8px;cursor:pointer;text-decoration:none;display:inline-block}code{overflow-wrap:anywhere;color:#c7e7ff}input{max-width:100%;margin:12px 0}small{color:#a8bad5}.error{color:#ffb4a2}"


class Handler(BaseHTTPRequestHandler):
    setup_key = ""
    preloaded_client = None

    def log_message(self, fmt, *args):
        # Never log query strings, authorization codes, state, or uploaded credentials.
        print("OAuth connector request:", self.command, self.path.split("?",1)[0].split("/setup/",1)[0], flush=True)

    def respond(self, body, status=200, content_type="application/json"):
        raw = (json.dumps(body) if content_type == "application/json" else body).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type+"; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/oauth/complete":
            try:
                pending = load_json(PENDING)
                query = parse_qs(parsed.query)
                result = complete(pending, query.get("code", [""])[0], query.get("state", [""])[0])
                message = "Existing publishing settings were not changed; enabled workflows may resume." if result["publishing_enabled"] else "Publishing remains off. Return to the agent for the pilot."
                self.respond('<!doctype html><meta name="referrer" content="no-referrer"><style>'+STYLE+'</style><main><h1>YouTube connected.</h1><p>Hypeless channel verified. Credentials stored in encrypted GitHub Secrets.</p><p>No videos were uploaded by this connector. '+message+'</p><script>history.replaceState(null,"","/connected")</script></main>', content_type="text/html")
            except Exception:
                self.respond('<!doctype html><style>'+STYLE+'</style><main><h1>Connection not completed.</h1><p>Return to the setup tab and reconnect. Check that you chose the Hypeless channel and allowed the requested permission. No video was published.</p><script>history.replaceState(null,"","/connection-error")</script></main>', status=400, content_type="text/html")
            return
        if parsed.path.startswith("/setup/") and hmac.compare_digest(parsed.path.removeprefix("/setup/"), self.setup_key):
            page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="referrer" content="no-referrer"><title>Connect Hypeless YouTube</title><style>'''+STYLE+'''</style><main><small>HYPELESS / SECURE ONE-TIME CONNECTION</small><h1>Connect YouTube.<br>No passwords. No publishing.</h1><p>Use an OAuth <b>Web application</b> client owned by your Google Cloud project. The agent handles refresh tokens and encrypted cloud storage.</p><section><b>Authorized redirect URI</b><p><code>'''+CALLBACK+'''</code></p><small>Enable YouTube Data API v3. For persistent automation, use an In-production OAuth app; Testing tokens generally expire after seven days. Google may show an unverified-app warning for a personal app. Only proceed for the app you created.</small></section><section><label>Google OAuth client JSON (already supplied files are preloaded; no re-upload needed)<br><input id="file" type="file" accept="application/json,.json"></label><br><button id="start">Prepare Google sign-in</button><p id="status"></p><a id="connect" class="button" style="display:none" target="_blank" rel="noopener noreferrer">Open Google consent in a new tab ↗</a></section><p><small>Permission: YouTube account management required for uploads, metadata and playlists. This integration never uses deletion/comment endpoints. Only channel <code>'''+load_json(ROOT/"config/youtube.json")["channel_id"]+'''</code> is accepted.</small></p></main><script>const KEY='''+json.dumps(self.setup_key)+''';history.replaceState(null,'','/setup');document.querySelector('#start').onclick=async()=>{const status=document.querySelector('#status');try{const f=document.querySelector('#file').files[0];const client=f?JSON.parse(await f.text()):null;const r=await fetch('/api/start',{method:'POST',headers:{'Content-Type':'application/json','X-Setup-Key':KEY},body:JSON.stringify({client})});const d=await r.json();if(!r.ok)throw Error(d.error);const a=document.querySelector('#connect');a.href=d.authorization_url;a.style.display='inline-block';status.textContent='Ready. Open Google consent, choose Hypeless, then return to the agent.';}catch(e){status.textContent=e.message;status.className='error';}};</script></html>'''
            self.respond(page, content_type="text/html")
        else:
            self.respond('<!doctype html><style>'+STYLE+'</style><main><h1>Hypeless YouTube connection</h1><p>Open the private setup link supplied by the agent. No credentials are displayed here.</p></main>', content_type="text/html")

    def do_POST(self):
        if self.path != "/api/start" or not hmac.compare_digest(self.headers.get("X-Setup-Key", ""), self.setup_key):
            self.respond({"error": "Unauthorized setup session"}, status=403)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 100_000:
                raise ValueError("Invalid client file size")
            body = json.loads(self.rfile.read(length))
            host = self.headers.get("X-Forwarded-Host") or self.headers.get("Host", "")
            origin = valid_origin("https://"+host)
            if self.headers.get("Origin") and self.headers["Origin"] != origin:
                raise ValueError("Unexpected setup origin")
            client = parse_client(body["client"]) if body.get("client") else self.preloaded_client
            if not client:
                raise ValueError("Select your downloaded Web OAuth client JSON")
            pending, authorization = make_flow(client, origin)
            secure_write(PENDING, pending)
            self.respond({"authorization_url": authorization})
        except (ValueError, KeyError, TypeError) as exc:
            self.respond({"error": str(exc)}, status=400)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--client-file", help="Private, already supplied Web OAuth JSON; never printed")
    args = ap.parse_args()
    Handler.setup_key = random_secrets.token_urlsafe(24)
    if args.client_file:
        Handler.preloaded_client = parse_client(load_json(args.client_file))
    print("Open this path on the HTTPS live-preview host: /setup/"+Handler.setup_key, flush=True)
    print("Registered Google callback:", CALLBACK, flush=True)
    ThreadingHTTPServer(("0.0.0.0", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
