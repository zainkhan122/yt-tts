"""Buffer GraphQL client with quota-aware pacing and safe retry semantics.

Only explicit rate-limit rejections are retried for createPost. A lost mutation
response/5xx may mean the post WAS created: surface AmbiguousResult and reconcile
by persisted channel + media + text instead of blindly sending again.
"""
import datetime as dt
import email.utils
import random
import re
import time

import requests

from lib.secrets import buffer_token, redact
from tools.post.common import now_utc

ENDPOINT = "https://api.buffer.com"
POST_FIELDS = """id channelId status dueAt sentAt createdAt externalLink text schedulingType
 assets { source mimeType }
 error { message supportUrl }
 metadata { __typename ... on YoutubePostMetadata { title notifySubscribers type } }"""
CREATE = """mutation HypelessCreate($input: CreatePostInput!) {
 createPost(input: $input) {
  __typename
  ... on PostActionSuccess { post { """ + POST_FIELDS + """ } }
  ... on MutationError { message }
 }
}"""
CHANNEL_FIELDS = """id name service serviceId externalLink type timezone isDisconnected isLocked isQueuePaused
 metadata { __typename ... on InstagramMetadata { defaultToReminders }
 ... on YoutubeMetadata { defaultToReminders } }"""
STATE_QUERY = """query HypelessState($org: OrganizationId!, $input: PostsInput!, $recent: PostsInput!) {
 channels(input: { organizationId: $org }) { """ + CHANNEL_FIELDS + """ }
 facebookInput: __type(name: "FacebookPostMetadataInput") { inputFields { name type { kind name } } }
 posts(first: 100, input: $input) {
  edges { node { """ + POST_FIELDS + """ } }
  pageInfo { hasNextPage endCursor }
 }
 recent: posts(first: 100, input: $recent) {
  edges { node { """ + POST_FIELDS + """ } }
  pageInfo { hasNextPage endCursor }
 }
}"""
MORE_POSTS = """query HypelessPosts($input: PostsInput!, $after: String) {
 posts(first: 100, after: $after, input: $input) {
  edges { node { """ + POST_FIELDS + """ } }
  pageInfo { hasNextPage endCursor }
 }
}"""


class BufferError(RuntimeError):
    def __init__(self, message, code="ERROR", wait_seconds=0):
        super().__init__(redact(str(message)))
        self.code = code
        self.wait_seconds = max(0, wait_seconds)


class Deferred(BufferError):
    pass


class AmbiguousResult(BufferError):
    pass


def rate_policies(header):
    """Names are opaque; parse r/t from each policy, allowing optional whitespace."""
    rows = []
    for part in re.split(r',\s*(?=")', header or ""):
        r = re.search(r";\s*r\s*=\s*(\d+)", part)
        t = re.search(r";\s*t\s*=\s*(\d+)", part)
        if r and t:
            rows.append({"remaining": int(r[1]), "reset_seconds": int(t[1])})
    return rows


def retry_after(headers):
    value = headers.get("Retry-After", headers.get("retry-after", ""))
    try:
        return max(0, float(value))
    except (TypeError, ValueError):
        try:
            return max(0, (email.utils.parsedate_to_datetime(value) - now_utc()).total_seconds())
        except (TypeError, ValueError, OverflowError):
            rows = rate_policies(headers.get("RateLimit", headers.get("ratelimit", "")))
            return max((p["reset_seconds"] for p in rows if p["remaining"] == 0), default=60)


class BufferClient:
    def __init__(self, settings, token=None, session=None, sleep=time.sleep, clock=time.monotonic, jitter=None):
        self.settings = settings
        self.token = token or buffer_token()
        if not self.token:
            raise BufferError("BUFFER_API_KEY is missing", "AUTH")
        self.session = session or requests.Session()
        self.sleep, self.clock = sleep, clock
        self.jitter = jitter or (lambda: random.uniform(0.1, 0.9))
        self.last_request = None
        self.policies = []
        self.policy_time = 0
        self.request_count = 0
        self.capabilities = {"facebook_ai_generated": False}

    def _pace(self):
        now = self.clock()
        elapsed = now - self.policy_time
        low = [p for p in self.policies if p["remaining"] <= self.settings.get("quota_reserve", 5)
               and p["reset_seconds"] > elapsed]
        if low:
            wait = max(p["reset_seconds"] - elapsed for p in low)
            raise Deferred("Quota reserve reached; leave requests for recovery", "QUOTA_RESERVE", wait)
        if self.last_request is not None:
            wait = self.settings.get("request_spacing_seconds", 3) - (now - self.last_request)
            if wait > 0:
                self.sleep(wait)

    def request(self, query, variables=None, mutation=False):
        attempts = self.settings.get("max_attempts", 4)
        for attempt in range(attempts):
            self._pace()
            self.last_request = self.clock()
            self.request_count += 1
            try:
                response = self.session.post(ENDPOINT,
                    headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json", "User-Agent": "Hypeless-Reels-Studio/1"},
                    json={"query": query, "variables": variables or {}}, timeout=(10, 90), allow_redirects=False)
            except (requests.Timeout, requests.ConnectionError) as exc:
                if mutation:
                    raise AmbiguousResult("Mutation response lost; reconcile before any retry", "TRANSPORT") from exc
                if attempt + 1 == attempts:
                    raise Deferred("Buffer temporarily unreachable", "TRANSPORT", 300) from exc
                self.sleep(min(2 ** (attempt + 1), 30) + self.jitter())
                continue
            self.policies = rate_policies(response.headers.get("RateLimit", ""))
            self.policy_time = self.clock()
            if response.status_code == 429:
                wait = retry_after(response.headers)
                if wait > self.settings.get("max_inline_wait_seconds", 60) or attempt + 1 == attempts:
                    raise Deferred("Buffer rate limit: deferred until Retry-After", "RATE_LIMIT_EXCEEDED", wait)
                self.sleep(wait + self.jitter())
                continue
            if response.status_code in (401, 403):
                raise BufferError("Buffer authentication/permission failed; reconnect or rotate key", "AUTH")
            if response.status_code >= 500:
                if mutation:
                    raise AmbiguousResult("Buffer 5xx after create request; reconcile first", "SERVER")
                if attempt + 1 == attempts:
                    raise Deferred("Buffer server unavailable", "SERVER", 300)
                self.sleep(min(2 ** (attempt + 1), 30) + self.jitter())
                continue
            if response.status_code != 200:
                raise BufferError(f"Unexpected Buffer HTTP {response.status_code}; request rejected", "HTTP")
            try:
                body = response.json()
            except ValueError as exc:
                if mutation:
                    raise AmbiguousResult("Unreadable mutation response; reconcile first", "BAD_RESPONSE") from exc
                raise Deferred("Unreadable Buffer response", "BAD_RESPONSE", 300) from exc
            errors = body.get("errors") or []
            if errors:
                # A mutation may have succeeded even with top-level errors. Keep its ID.
                result = (body.get("data") or {}).get("createPost") or {}
                if mutation and (result.get("post") or {}).get("id"):
                    return body["data"]
                codes = {e.get("extensions", {}).get("code", "UNKNOWN") for e in errors}
                if codes <= {"RATE_LIMIT_EXCEEDED"}:
                    wait = retry_after(response.headers)
                    if attempt + 1 < attempts and wait <= self.settings.get("max_inline_wait_seconds", 60):
                        self.sleep(wait + self.jitter())
                        continue
                    raise Deferred("Buffer rate-limited the request", "RATE_LIMIT_EXCEEDED", wait)
                if codes & {"UNAUTHORIZED", "FORBIDDEN"}:
                    raise BufferError("Buffer permission/authentication error", "AUTH")
                if codes <= {"GRAPHQL_VALIDATION_FAILED", "BAD_USER_INPUT"}:
                    raise BufferError("GraphQL validation rejected the request", "INVALID_INPUT")
                if mutation:
                    raise AmbiguousResult("Uncertain GraphQL mutation outcome: " + ",".join(sorted(codes)), "GRAPHQL")
                if codes <= {"UNEXPECTED", "INTERNAL_SERVER_ERROR"} and attempt + 1 < attempts:
                    self.sleep(min(2 ** (attempt + 1), 30) + self.jitter())
                    continue
                raise Deferred("Buffer query failed: " + ",".join(sorted(codes)), "GRAPHQL", 300)
            if not isinstance(body.get("data"), dict):
                if mutation:
                    raise AmbiguousResult("Missing mutation result", "BAD_RESPONSE")
                raise Deferred("Missing query result", "BAD_RESPONSE", 300)
            return body["data"]
        raise Deferred("Retry budget exhausted", "RETRY_EXHAUSTED", 300)

    def state(self):
        org = self.settings["organization_id"]
        channel_ids = [c["buffer_id"] for c in self.settings["channels"].values()]
        inp = {"organizationId": org, "filter": {"channelIds": channel_ids,
               "status": ["scheduled", "sending", "draft", "needs_approval", "error"]},
               "sort": [{"field": "createdAt", "direction": "desc"}]}
        recent = {"organizationId": org, "filter": {"channelIds": channel_ids, "status": ["sent"],
                  "dueAt": {"start": (now_utc() - dt.timedelta(days=14)).isoformat()}},
                  "sort": [{"field": "createdAt", "direction": "desc"}]}
        result = self.request(STATE_QUERY, {"org": org, "input": inp, "recent": recent})
        fields = (result.get("facebookInput") or {}).get("inputFields") or []
        self.capabilities["facebook_ai_generated"] = any(f["name"] == "isAiGenerated" and f.get("type", {}).get("name") == "Boolean" for f in fields)
        posts, seen, count = [], set(), 1
        for name, filters in (("posts", inp), ("recent", recent)):
            page = result[name]
            while True:
                for edge in page["edges"]:
                    if edge["node"]["id"] not in seen:
                        posts.append(edge["node"])
                        seen.add(edge["node"]["id"])
                if not page["pageInfo"]["hasNextPage"]:
                    break
                if count >= self.settings.get("max_pages", 10):
                    raise BufferError("Post scan incomplete; refusing incomplete duplicate/capacity checks", "PAGINATION")
                page = self.request(MORE_POSTS, {"input": filters, "after": page["pageInfo"]["endCursor"]})["posts"]
                count += 1
        return result["channels"], posts

    def create(self, payload):
        result = self.request(CREATE, {"input": payload}, mutation=True).get("createPost") or {}
        if (result.get("post") or {}).get("id"):
            return result["post"]
        kind = result.get("__typename", "Unknown")
        if kind == "LimitReachedError":
            raise Deferred("Buffer posting limit reached; wait for capacity", "POSTING_LIMIT", 6 * 3600)
        if kind in {"InvalidInputError", "UnauthorizedError", "NotFoundError"}:
            raise BufferError(result.get("message", kind), kind)
        # RestProxyError / UnexpectedError might happen after a remote write.
        raise AmbiguousResult(result.get("message", "Unknown mutation result"), kind)
