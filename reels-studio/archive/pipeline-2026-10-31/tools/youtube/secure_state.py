"""Encrypt resumable session capabilities before storing them in a public repo."""
import base64
import json

from nacl.exceptions import CryptoError
from nacl.secret import SecretBox

from lib.secrets import youtube_state_key
from tools.youtube.api import YouTubeError, validate_session_url


def _box(key=None):
    value = key or youtube_state_key()
    if not value:
        raise YouTubeError("YOUTUBE_STATE_KEY missing; cannot safely persist upload sessions", "STATE_KEY_MISSING")
    try:
        return SecretBox(base64.urlsafe_b64decode(value))
    except (ValueError, TypeError):
        raise YouTubeError("Invalid upload-state encryption key", "STATE_KEY_INVALID")


def encrypt_session(url, item, channel_id, key=None):
    validate_session_url(url)
    body = {"uri": url, "video_id": item["video_id"], "sha256": item["asset_digest"], "channel_id": channel_id}
    return base64.b64encode(_box(key).encrypt(json.dumps(body, sort_keys=True).encode())).decode()


def decrypt_session(ciphertext, item, channel_id, key=None):
    try:
        body = json.loads(_box(key).decrypt(base64.b64decode(ciphertext)))
    except (CryptoError, ValueError, TypeError):
        raise YouTubeError("Cannot decrypt resumable checkpoint; do not start another upload", "STATE_DECRYPTION")
    if (body.get("video_id"), body.get("sha256"), body.get("channel_id")) != (item["video_id"], item["asset_digest"], channel_id):
        raise YouTubeError("Upload checkpoint belongs to different media/channel", "STATE_BINDING")
    return validate_session_url(body["uri"])


def validate_key(key=None):
    _box(key)
