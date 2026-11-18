#!/usr/bin/env python3
"""Re-consent using existing GitHub-held credentials; never log credentials or codes.

Start writes an owner-only link and SecretBox-encrypted PKCE state to Actions artifact.
Finish takes the downloaded callback JSON through a temporary encrypted Actions secret;
state is decrypted only inside the runner. Existing channel verification and secret storage
remain in oauth_connect.complete(). No YouTube content is changed.
"""
import argparse
import base64
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from lib.secrets import youtube_credentials, redact
from tools.youtube.oauth_connect import make_flow, complete
from tools.youtube.oauth_handoff import validate_response
from tools.youtube.secure_state import _box


def main():
    p = argparse.ArgumentParser(); p.add_argument('mode', choices=['start','finish']); p.add_argument('directory'); args = p.parse_args()
    path = Path(args.directory); path.mkdir(parents=True, exist_ok=True)
    try:
        if args.mode == 'start':
            creds = youtube_credentials() or {}
            if not all(creds.get(x) for x in ('client_id','client_secret')):
                raise ValueError('Existing YouTube OAuth secret does not contain client credentials')
            pending, url = make_flow({k: creds[k] for k in ('client_id','client_secret')})
            (path/'pending.enc').write_bytes(_box().encrypt(json.dumps(pending).encode()))
            (path/'authorize.txt').write_text(url+'\n')
            print('Consent link and encrypted state prepared; no YouTube mutation.')
        else:
            pending = json.loads(_box().decrypt((path/'pending.enc').read_bytes()))
            response = json.loads(base64.b64decode(os.environ['YOUTUBE_OAUTH_RESPONSE_B64'], validate=True))
            code, state = validate_response(response, pending)
            result = complete(pending, code, state)
            print('YouTube channel verified; updated OAuth secret stored:', result['secret_stored'])
    except Exception as exc:
        raise SystemExit('OAuth handoff failed: ' + redact(str(exc)))

if __name__ == '__main__':
    main()
