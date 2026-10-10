"""Official YouTube Data API: OAuth refresh, quota accounting and safe retries.

No browser scraping, service accounts, Buffer-token reuse or quota bypass.
Non-idempotent creates / media writes are NEVER retried after an unknown outcome.
"""
import datetime as dt
import json
import random
import time
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

import requests

from lib.secrets import redact, register_sensitive, youtube_credentials
from tools.post.buffer_api import retry_after
from tools.post.common import iso, now_utc

API = "https://www.googleapis.com/youtube/v3/"
UPLOAD = "https://www.googleapis.com/upload/youtube/v3/"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
PACIFIC = ZoneInfo("America/Los_Angeles")


class YouTubeError(RuntimeError):
    def __init__(self, message, code="ERROR", wait_seconds=0):
        super().__init__(redact(str(message)))
        self.code, self.wait_seconds = code, max(0, wait_seconds)


class Deferred(YouTubeError):
    pass


class Uncertain(YouTubeError):
    pass


def quota_reset(now):
    tomorrow = now.astimezone(PACIFIC).date() + dt.timedelta(days=1)
    return dt.datetime.combine(tomorrow, dt.time(), PACIFIC).astimezone(dt.timezone.utc) + dt.timedelta(minutes=2)


def validate_session_url(url):
    p = urlparse(url)
    if (p.scheme != "https" or p.hostname != "www.googleapis.com" or p.port not in (None, 443)
            or p.username or p.password or p.path != "/upload/youtube/v3/videos"
            or not parse_qs(p.query).get("upload_id") or p.fragment):
        raise YouTubeError("Rejected unexpected resumable upload host/path", "INVALID_SESSION_URL")
    return url


class YouTubeAPI:
    def __init__(self, cfg, journal, credentials=None, session=None, sleep=time.sleep,
                 clock=time.monotonic, wallclock=now_utc, jitter=None):
        self.cfg, self.journal = cfg, journal
        self.credentials = credentials if credentials is not None else youtube_credentials()
        if not isinstance(self.credentials, dict) or not all(isinstance(self.credentials.get(k), str) and self.credentials[k] for k in ("client_id", "client_secret", "refresh_token")):
            raise YouTubeError("Google OAuth is not connected; a Buffer key cannot authorize this API", "OAUTH_MISSING")
        for k in ("client_secret", "refresh_token"):
            register_sensitive(self.credentials[k])
        self.session = session or requests.Session()
        self.sleep, self.clock, self.wallclock = sleep, clock, wallclock
        self.jitter = jitter or (lambda: random.uniform(0.1, 1.0))
        self.token, self.expires, self.last_request = None, 0, None
        self.request_count = 0

    def refresh(self):
        for attempt in range(self.cfg["max_attempts"]):
            try:
                r = self.session.post(TOKEN_ENDPOINT, data={"client_id": self.credentials["client_id"],
                    "client_secret": self.credentials["client_secret"], "refresh_token": self.credentials["refresh_token"],
                    "grant_type": "refresh_token"}, timeout=(10, 30), allow_redirects=False)
            except (requests.Timeout, requests.ConnectionError):
                if attempt + 1 == self.cfg["max_attempts"]:
                    raise Deferred("Google token endpoint unavailable", "TOKEN_NETWORK", 300)
                self.sleep(2 ** attempt + self.jitter())
                continue
            if r.status_code == 429 or r.status_code >= 500:
                wait = retry_after(r.headers) if r.status_code == 429 else 2 ** (attempt+1)
                if wait > self.cfg["max_inline_wait_seconds"] or attempt + 1 == self.cfg["max_attempts"]:
                    raise Deferred("Google token service deferred", "TOKEN_RATE", wait)
                self.sleep(wait + self.jitter())
                continue
            try:
                body = r.json()
            except ValueError:
                raise Deferred("Unreadable Google token response", "TOKEN_RESPONSE", 300)
            if r.status_code != 200 or not body.get("access_token"):
                reason = body.get("error", "AUTH")
                raise YouTubeError("Reconnect Google OAuth: " + str(reason), "AUTH_RECONNECT")
            self.token = body["access_token"]
            self.expires = self.clock() + max(30, int(body.get("expires_in", 3600)) - 90)
            register_sensitive(self.token)
            return

    def _charge(self, cost, upload_start):
        now = self.wallclock()
        day = str(now.astimezone(PACIFIC).date())
        quota = self.journal.data.setdefault("quota", {})
        if quota.get("day_pacific") != day:
            quota.clear()
            quota.update(day_pacific=day, general_units=0, upload_starts=0)
        if quota["general_units"] + cost > self.cfg["general_quota_budget_per_day"]:
            raise Deferred("Local YouTube quota budget reached", "QUOTA_BUDGET", (quota_reset(now)-now).total_seconds())
        if upload_start and quota["upload_starts"] >= self.cfg["max_upload_starts_per_day"]:
            raise Deferred("Paced upload-start limit reached", "UPLOAD_BUDGET", (quota_reset(now)-now).total_seconds())
        if self.request_count >= self.cfg["max_api_requests_per_run"]:
            raise Deferred("Per-run request budget reached", "RUN_BUDGET", 3600)
        quota["general_units"] += cost
        quota["upload_starts"] += int(upload_start)
        # Persistence failure stops BEFORE the HTTP request.
        self.journal.save("reserve YouTube quota")
        self.request_count += 1

    def request(self, method, resource, *, params=None, body=None, data=None, headers=None,
                cost=1, idempotent=True, upload_start=False, timeout=(10, 90)):
        if resource.startswith("https://"):
            url = validate_session_url(resource)
        elif resource.startswith("upload/"):
            url = UPLOAD + resource.removeprefix("upload/")
        else:
            if ":" in resource or ".." in resource or resource.startswith("/"):
                raise YouTubeError("Invalid API resource", "INVALID_RESOURCE")
            url = API + resource
        refreshed = False
        for attempt in range(self.cfg["max_attempts"]):
            if not self.token or self.clock() >= self.expires:
                self.refresh()
            if self.last_request is not None:
                wait = self.cfg["request_spacing_seconds"] - (self.clock() - self.last_request)
                if wait > 0:
                    self.sleep(wait)
            self._charge(cost, upload_start)
            self.last_request = self.clock()
            h = {"Authorization": "Bearer " + self.token, "User-Agent": "Hypeless-YouTube/1", **(headers or {})}
            try:
                r = self.session.request(method, url, params=params, json=body, data=data, headers=h,
                                         timeout=timeout, allow_redirects=False)
            except (requests.Timeout, requests.ConnectionError) as exc:
                if not idempotent:
                    raise Uncertain("YouTube write response lost; reconcile before retry", "NETWORK") from exc
                if attempt + 1 == self.cfg["max_attempts"]:
                    raise Deferred("YouTube unreachable after bounded retries", "NETWORK", 300) from exc
                self.sleep(2 ** (attempt+1) + self.jitter())
                continue
            if r.status_code in (200, 201, 204, 308):
                return r
            if r.status_code == 401:
                if refreshed:
                    raise YouTubeError("Google authorization rejected after refresh", "AUTH_RECONNECT")
                self.refresh()
                refreshed = True
                continue  # explicit auth rejection; no operation was accepted
            try:
                error = r.json().get("error", {})
                reasons = {e.get("reason", "") for e in error.get("errors", [])}
                message = error.get("message", "YouTube request rejected")
            except (ValueError, AttributeError):
                reasons, message = set(), "YouTube request rejected"
            if reasons & {"quotaExceeded", "dailyLimitExceeded"}:
                raise Deferred("YouTube daily quota exhausted", "QUOTA_EXCEEDED", (quota_reset(self.wallclock())-self.wallclock()).total_seconds())
            if "uploadLimitExceeded" in reasons:
                raise Deferred("YouTube channel upload limit reached", "UPLOAD_LIMIT", 86400)
            if r.status_code == 429 or reasons & {"rateLimitExceeded", "userRateLimitExceeded"}:
                wait = retry_after(r.headers)
                if wait > self.cfg["max_inline_wait_seconds"] or attempt + 1 == self.cfg["max_attempts"]:
                    raise Deferred("YouTube rate limit; honor Retry-After", "RATE_LIMIT", wait)
                self.sleep(wait + self.jitter())
                continue
            if r.status_code in (500, 502, 503, 504):
                if not idempotent:
                    raise Uncertain("YouTube server error after a write; reconcile first", "SERVER")
                if attempt + 1 == self.cfg["max_attempts"]:
                    raise Deferred("YouTube server temporarily unavailable", "SERVER", 300)
                self.sleep(2 ** (attempt+1) + self.jitter())
                continue
            if r.status_code == 404 and resource.startswith("https://"):
                raise YouTubeError("Resumable session expired; reconcile before restart", "SESSION_EXPIRED")
            raise YouTubeError(f"YouTube HTTP {r.status_code}: {message}", next(iter(sorted(reasons)), "HTTP_"+str(r.status_code)))
        raise Deferred("YouTube retry budget exhausted", "RETRY_EXHAUSTED", 300)

    def json(self, method, resource, **kwargs):
        r = self.request(method, resource, **kwargs)
        try:
            result = r.json()
            if not isinstance(result, dict):
                raise ValueError()
            return result
        except ValueError:
            if kwargs.get("idempotent", True):
                raise Deferred("Unreadable YouTube response", "BAD_RESPONSE", 300)
            raise Uncertain("Unreadable YouTube write receipt", "BAD_RESPONSE")

    def verify_channel(self):
        result = self.json("GET", "channels", params={"part": "id,contentDetails", "mine": "true"})
        matches = [c for c in result.get("items", []) if c["id"] == self.cfg["channel_id"]]
        if len(matches) != 1:
            raise YouTubeError("OAuth selected a different YouTube channel; nothing will be uploaded", "CHANNEL_MISMATCH")
        return matches[0]

    def pages(self, resource, params, maximum=10):
        params = dict(params)
        for _ in range(maximum):
            body = self.json("GET", resource, params=params)
            yield from body.get("items", [])
            if not body.get("nextPageToken"):
                return
            params["pageToken"] = body["nextPageToken"]
        raise YouTubeError("Pagination incomplete; refusing an incomplete duplicate check", "PAGINATION")
