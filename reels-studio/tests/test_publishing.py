"""Safety regression suite. No real credentials/network calls or social writes."""
import copy
import datetime as dt
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import requests
from graphql import build_client_schema, coerce_input_value, parse, validate
from tools.post import buffer_api as api
from tools.post import planner, publisher, media
from tools.post.common import (check_manifest, config, iso, key, load_json, media_url,
                               parse_time, queue, save_json)
from tools.post.state import Journal
from lib import secrets

NOW = dt.datetime(2026, 10, 10, 1, tzinfo=dt.timezone.utc)


def channels(cfg):
    return [{"id": c["buffer_id"], "serviceId": c["service_id"], "service": p,
             "isDisconnected": False, "isLocked": False, "isQueuePaused": False,
             "metadata": {"defaultToReminders": False}} for p, c in cfg["buffer"]["channels"].items()]


def fake_payload(item, platform, due, cfg):
    return {"channelId": cfg["buffer"]["channels"][platform]["buffer_id"], "dueAt": iso(due),
            "text": item["title"], "assets": [{"video": {"url": media_url(item, cfg)}}]}


def fixture_items(n=10):
    originals = queue()
    items = []
    for i in range(n):
        item = copy.deepcopy(originals[i % 3])
        item.update(video_id=f"test-video-{i}", title=f"AI video {i}", priority=i,
                    category=["news", "tool", "repo"][i % 3], approval="approved",
                    reviewed_at=iso(NOW), expires_at=iso(NOW + dt.timedelta(days=3)),
                    asset_id=100 + i, media_path=f"media/{100+i}/test-video-{i}.mp4")
        items.append(item)
    return items


class MemoryJournal:
    def __init__(self, records=None, fail_reserve=False):
        self.data = {"records": copy.deepcopy(records or {}), "cooldown_until": None}
        self.fail_reserve = fail_reserve
        self.saves = []

    @property
    def records(self):
        return self.data["records"]

    def save(self, message):
        if self.fail_reserve and message.startswith("reserve"):
            raise RuntimeError("durable store unavailable")
        self.saves.append((message, copy.deepcopy(self.data)))


class FakeClock:
    def __init__(self):
        self.value, self.sleeps = 0.0, []

    def time(self):
        return self.value

    def sleep(self, value):
        self.sleeps.append(value)
        self.value += value


def response(status=200, data=None, headers=None):
    result = Mock()
    result.status_code = status
    result.headers = headers or {}
    result.json.return_value = data if data is not None else {"data": {"ok": True}}
    return result


class ClientTests(unittest.TestCase):
    def make(self, responses, settings=None):
        cfg = config()["buffer"]
        if settings:
            cfg.update(settings)
        clock, session = FakeClock(), Mock()
        session.post.side_effect = responses
        client = api.BufferClient(cfg, token="test-only-noncredential", session=session,
                                  clock=clock.time, sleep=clock.sleep, jitter=lambda: 0.25)
        return client, session, clock

    def test_parse_all_quota_windows_with_spaces(self):
        h = '"100-in-15min"; r=98; t=897, "250-in-1day";r=245;t=86397, "3000-in-30days"; r=2969; t=696980'
        self.assertEqual([p["remaining"] for p in api.rate_policies(h)], [98, 245, 2969])

    def test_pacing_applies_to_every_request(self):
        c, session, clock = self.make([response(), response()])
        c.request("query { x }")
        c.request("query { y }")
        self.assertGreaterEqual(clock.value, 3)
        self.assertFalse(session.post.call_args.kwargs["allow_redirects"])

    def test_short_429_honors_retry_after_and_jitter(self):
        c, session, clock = self.make([response(429, headers={"Retry-After": "4", "RateLimit": '"policy"; r=0; t=4'}), response()])
        c.request("query { x }")
        self.assertEqual(session.post.call_count, 2)
        self.assertGreaterEqual(clock.value, 4.25)

    def test_long_429_defers_without_sleeping(self):
        c, session, clock = self.make([response(429, headers={"Retry-After": "86400"})])
        with self.assertRaises(api.Deferred) as caught:
            c.request("query { x }")
        self.assertEqual(caught.exception.wait_seconds, 86400)
        self.assertEqual(session.post.call_count, 1)
        self.assertEqual(clock.sleeps, [])

    def test_graphql_rate_limit_is_not_mistaken_for_success(self):
        body = {"errors": [{"message": "slow down", "extensions": {"code": "RATE_LIMIT_EXCEEDED"}}]}
        c, session, clock = self.make([response(data=body, headers={"Retry-After": "7200"})])
        with self.assertRaises(api.Deferred):
            c.request("mutation { x }", mutation=True)
        self.assertEqual(session.post.call_count, 1)

    def test_quota_reserve_prevents_next_request(self):
        c, session, clock = self.make([response(headers={"RateLimit": '"remaining-month"; r=4; t=9999'})])
        c.request("query { x }")
        with self.assertRaises(api.Deferred):
            c.request("query { y }")
        self.assertEqual(session.post.call_count, 1)

    def test_query_503_retries_bounded_with_backoff(self):
        c, session, clock = self.make([response(503)] * 4)
        with self.assertRaises(api.Deferred):
            c.request("query { x }")
        self.assertEqual(session.post.call_count, 4)
        self.assertGreaterEqual(sum(clock.sleeps), 14)

    def test_query_connection_error_retries(self):
        c, session, _ = self.make([requests.ConnectionError(), response()])
        c.request("query { x }")
        self.assertEqual(session.post.call_count, 2)

    def test_mutation_timeout_never_blindly_retried(self):
        c, session, _ = self.make([requests.Timeout()])
        with self.assertRaises(api.AmbiguousResult):
            c.create({})
        self.assertEqual(session.post.call_count, 1)

    def test_mutation_500_is_ambiguous_not_safe_retry(self):
        c, session, _ = self.make([response(500)])
        with self.assertRaises(api.AmbiguousResult):
            c.create({})
        self.assertEqual(session.post.call_count, 1)

    def test_auth_error_never_retries(self):
        c, session, _ = self.make([response(401)])
        with self.assertRaises(api.BufferError) as caught:
            c.request("query { x }")
        self.assertEqual(caught.exception.code, "AUTH")
        self.assertEqual(session.post.call_count, 1)

    def test_typed_validation_error_stops(self):
        body = {"data": {"createPost": {"__typename": "InvalidInputError", "message": "invalid title"}}}
        c, session, _ = self.make([response(data=body)])
        with self.assertRaises(api.BufferError) as caught:
            c.create({})
        self.assertNotIsInstance(caught.exception, api.AmbiguousResult)
        self.assertEqual(session.post.call_count, 1)

    def test_posting_limit_defers(self):
        body = {"data": {"createPost": {"__typename": "LimitReachedError", "message": "queue full"}}}
        c, _, _ = self.make([response(data=body)])
        with self.assertRaises(api.Deferred) as caught:
            c.create({})
        self.assertEqual(caught.exception.code, "POSTING_LIMIT")

    def test_success_with_warning_keeps_receipt(self):
        body = {"data": {"createPost": {"post": {"id": "known-id"}}}, "errors": [{"message": "warning"}]}
        c, _, _ = self.make([response(data=body)])
        self.assertEqual(c.create({})["id"], "known-id")

    def test_active_and_recent_history_pagination(self):
        p = {"id": "one"}
        first = {"data": {"channels": [], "posts": {"edges": [{"node": p}], "pageInfo": {"hasNextPage": True, "endCursor": "cursor"}},
                          "recent": {"edges": [], "pageInfo": {"hasNextPage": False, "endCursor": None}}}}
        second = {"data": {"posts": {"edges": [{"node": {"id": "two"}}], "pageInfo": {"hasNextPage": False, "endCursor": None}}}}
        c, session, _ = self.make([response(data=first), response(data=second)])
        _, posts = c.state()
        self.assertEqual([p["id"] for p in posts], ["one", "two"])
        self.assertEqual(session.post.call_args.kwargs["json"]["variables"]["after"], "cursor")

    def test_incomplete_duplicate_scan_fails_closed(self):
        data = {"data": {"channels": [], "posts": {"edges": [], "pageInfo": {"hasNextPage": True, "endCursor": "cursor"}},
                         "recent": {"edges": [], "pageInfo": {"hasNextPage": False}}}}
        c, _, _ = self.make([response(data=data)], {"max_pages": 1})
        with self.assertRaises(api.BufferError):
            c.state()


class PlannerTests(unittest.TestCase):
    def setUp(self):
        self.cfg = config()
        self.cfg["buffer"]["channels"]["facebook"].pop("posting_hold", None)  # generic three-channel scheduler fixture
        self.channels = channels(self.cfg)

    def planned(self, items=None, records=None, posts=None, **kwargs):
        with patch.object(planner, "payload_for", side_effect=fake_payload):
            return planner.plan(items or fixture_items(), records or {}, self.channels, posts or [], self.cfg, NOW, **kwargs)

    def test_ten_videos_stay_in_backlog_not_bulk_dump(self):
        self.cfg["schedule"]["max_posts_per_run"] = 100
        rows, _ = self.planned()
        self.assertEqual(len(rows), 18)  # six videos × three channels, four videos held back
        for platform in ("youtube", "instagram", "facebook"):
            selected = [r for r in rows if r["platform"] == platform]
            self.assertEqual(len(selected), 6)
            days = {}
            for row in selected:
                days.setdefault(row["due_local"][:10], []).append(row)
            for day in days.values():
                self.assertEqual(len(day), 3)
                self.assertEqual(sum(r["category"] == "repo" for r in day), 1)
                self.assertTrue({"news", "tool"}.issubset({r["category"] for r in day}))
            times = sorted(parse_time(r["due_at"]) for r in selected)
            self.assertTrue(all((b - a).total_seconds() >= 180*60 for a, b in zip(times, times[1:])))

    def test_default_run_has_at_most_nine_mutations(self):
        rows, _ = self.planned()
        self.assertLessEqual(len(rows), 9)

    def test_existing_queue_consumes_capacity(self):
        posts = [{"id": f"{p}-{i}", "channelId": c["buffer_id"], "status": "scheduled", "dueAt": iso(NOW + dt.timedelta(days=5+i))}
                 for p, c in self.cfg["buffer"]["channels"].items() for i in range(self.cfg["buffer"]["queue_target_per_channel"])]
        rows, _ = self.planned(posts=posts)
        self.assertEqual(rows, [])

    def test_manual_upload_locks_are_per_platform(self):
        items = fixture_items(3)
        rec = {key(items[0]["video_id"], "youtube"): {"video_id": items[0]["video_id"], "platform": "youtube", "state": "published_manual"}}
        rows, _ = self.planned(items, records=rec)
        self.assertNotIn((items[0]["video_id"], "youtube"), {(r["video_id"], r["platform"]) for r in rows})
        self.assertIn((items[0]["video_id"], "instagram"), {(r["video_id"], r["platform"]) for r in rows})

    def test_partial_success_reuses_existing_slot_on_remaining_platforms(self):
        items = fixture_items(3)
        original = self.planned(items)[0]
        yt = next(r for r in original if r["video_id"] == items[0]["video_id"] and r["platform"] == "youtube")
        rec = {key(items[0]["video_id"], "youtube"): {"video_id": items[0]["video_id"], "platform": "youtube", "state": "scheduled",
               "due_at": yt["due_at"], "buffer_post_id": "already-scheduled"}}
        remote = [{"id": "already-scheduled", "channelId": yt["payload"]["channelId"], "status": "scheduled", "dueAt": yt["due_at"]}]
        rows, _ = self.planned(items, records=rec, posts=remote)
        remaining = [r for r in rows if r["video_id"] == items[0]["video_id"]]
        self.assertEqual({r["platform"] for r in remaining}, {"instagram", "facebook"})
        for row in remaining:
            old = next(r for r in original if r["video_id"] == row["video_id"] and r["platform"] == row["platform"])
            self.assertEqual(row["due_at"], old["due_at"])

    def test_uncertain_outcome_blocks_new_create(self):
        item = fixture_items(1)[0]
        rec = {key(item["video_id"], p): {"video_id": item["video_id"], "platform": p, "state": "uncertain"} for p in item["platforms"]}
        rows, _ = self.planned([item], records=rec, pilot=True)
        self.assertEqual(rows, [])

    def test_held_queue_is_not_live_eligible(self):
        items = fixture_items(3)
        for i in items:
            i["approval"] = "held"
        self.assertEqual(self.planned(items)[0], [])
        self.assertGreater(len(self.planned(items, preview=True)[0]), 0)

    def test_expired_fact_review_blocks_scheduling(self):
        items = fixture_items(3)
        for i in items:
            i["expires_at"] = iso(NOW - dt.timedelta(minutes=1))
        self.assertEqual(self.planned(items)[0], [])

    def test_no_repo_only_day(self):
        items = fixture_items(6)
        for i in items:
            i["category"] = "repo"
        self.assertEqual(self.planned(items)[0], [])

    def test_disconnected_channel_does_not_block_healthy_channels(self):
        self.channels[0]["isDisconnected"] = True
        rows, notes = self.planned()
        self.assertTrue(rows)
        self.assertFalse(any(r["platform"] == "youtube" for r in rows))
        self.assertTrue(any("isDisconnected" in n for n in notes))

    def test_social_account_identity_mismatch_blocks(self):
        self.channels[0]["serviceId"] = "wrong-account"
        rows, _ = self.planned()
        self.assertFalse(any(r["platform"] == "youtube" for r in rows))

    def test_facebook_native_label_policy_hold_blocks_even_when_connected(self):
        self.cfg["buffer"]["channels"]["facebook"]["posting_hold"] = "Native AI label unsupported"
        rows, notes = self.planned()
        self.assertFalse(any(r["platform"] == "facebook" for r in rows))
        self.assertTrue(any("policy hold" in n for n in notes))

    def test_notification_only_channel_blocks(self):
        self.channels[0]["metadata"]["defaultToReminders"] = True
        rows, _ = self.planned()
        self.assertFalse(any(r["platform"] == "youtube" for r in rows))

    def test_retry_after_persists_across_runs(self):
        items = fixture_items(3)
        rec = {key(i["video_id"], p): {"video_id": i["video_id"], "platform": p, "state": "retry_wait", "retry_at": iso(NOW + dt.timedelta(days=1))}
               for i in items for p in i["platforms"]}
        self.assertEqual(self.planned(items, records=rec)[0], [])


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.cfg = config()
        self.cfg["buffer"]["channels"]["facebook"].pop("posting_hold", None)  # fake API, not an actual Facebook publish
        self.items = fixture_items(3)
        with patch.object(planner, "payload_for", side_effect=fake_payload):
            self.rows = planner.plan(self.items, {}, channels(self.cfg), [], self.cfg, NOW)[0]

    def test_reservation_failure_means_zero_buffer_calls(self):
        journal, client = MemoryJournal(fail_reserve=True), Mock()
        with self.assertRaises(RuntimeError):
            publisher.deliver(self.rows, self.items, journal, client, self.cfg, clock=lambda: NOW)
        client.create.assert_not_called()

    def test_lost_response_recovered_without_duplicate(self):
        journal, client = MemoryJournal(), Mock()
        client.create.side_effect = api.AmbiguousResult("timeout")
        publisher.deliver(self.rows, self.items, journal, client, self.cfg, clock=lambda: NOW)
        self.assertEqual(client.create.call_count, 1)
        row = self.rows[0]
        k = key(row["video_id"], row["platform"])
        self.assertEqual(journal.records[k]["state"], "uncertain")
        post = {"id": "already-created", "channelId": row["payload"]["channelId"], "status": "scheduled", "dueAt": row["due_at"],
                "text": row["payload"]["text"], "assets": [{"source": row["media_url"]}], "metadata": None}
        publisher.reconcile(journal.records, [], [post], self.cfg, NOW)
        self.assertEqual(journal.records[k]["buffer_post_id"], "already-created")
        publisher.deliver([row], self.items, journal, client, self.cfg, clock=lambda: NOW)
        self.assertEqual(client.create.call_count, 1)

    def test_rate_rejection_persists_cooldown_then_stops_batch(self):
        journal, client = MemoryJournal(), Mock()
        client.create.side_effect = api.Deferred("rate limited", "RATE_LIMIT_EXCEEDED", 86400)
        publisher.deliver(self.rows, self.items, journal, client, self.cfg, clock=lambda: NOW)
        self.assertEqual(client.create.call_count, 1)
        self.assertEqual(journal.data["cooldown_until"], iso(NOW + dt.timedelta(days=1)))
        self.assertEqual(next(iter(journal.records.values()))["state"], "retry_wait")

    def test_success_persisted_per_post_and_rerun_is_idempotent(self):
        journal, client = MemoryJournal(), Mock()
        def success(payload):
            return {"id": payload["channelId"] + payload["dueAt"], "status": "scheduled", "channelId": payload["channelId"], "dueAt": payload["dueAt"]}
        client.create.side_effect = success
        publisher.deliver(self.rows[:3], self.items, journal, client, self.cfg, clock=lambda: NOW)
        self.assertEqual(len(journal.saves), 6)  # reserve + receipt, each durable
        publisher.deliver(self.rows[:3], self.items, journal, client, self.cfg, clock=lambda: NOW)
        self.assertEqual(client.create.call_count, 3)

    def test_delivery_error_is_not_recreated(self):
        rec = {"video_id": "x", "platform": "youtube", "channel_id": "y", "state": "scheduled", "buffer_post_id": "p"}
        post = {"id": "p", "channelId": "y", "status": "error", "error": {"message": "permission expired"}}
        publisher.reconcile({"x:youtube": rec}, [], [post], self.cfg, NOW)
        self.assertEqual(rec["state"], "delivery_error")
        self.assertIn("permission expired", rec["last_error"])

    def test_retry_budget_moves_to_dead_letter(self):
        row = self.rows[0]
        k = key(row["video_id"], row["platform"])
        journal = MemoryJournal({k: {"video_id": row["video_id"], "platform": row["platform"], "state": "retry_wait", "attempts": 4}})
        client = Mock()
        publisher.deliver([row], self.items, journal, client, self.cfg, clock=lambda: NOW)
        client.create.assert_not_called()
        self.assertEqual(journal.records[k]["state"], "dead_letter")

    def test_journal_compare_and_swap_conflict_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            session = Mock()
            import base64
            doc = {"records": {}}
            session.get.return_value = response(data={"sha": "old-sha", "content": base64.b64encode(json.dumps(doc).encode()).decode()})
            session.put.return_value = response(409)
            with patch("tools.post.state.gh_token", return_value="unit-test-not-secret"):
                journal = Journal(self.cfg, remote=True, path=Path(tmp)/"journal.json", session=session)
                journal.records["reserved"] = {"state": "submitting"}
                with self.assertRaises(RuntimeError):
                    journal.save("test")
            self.assertFalse((Path(tmp)/"journal.json").exists())


class SchemaAndMediaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = build_client_schema(load_json(ROOT / "research/publishing/buffer-schema-2026-10-10.json"))

    def test_graphql_queries_and_mutation_validate_against_official_schema(self):
        for query_text in (api.STATE_QUERY, api.MORE_POSTS, api.CREATE):
            self.assertEqual(validate(self.schema, parse(query_text)), [])

    def test_platform_payloads_validate_against_official_schema(self):
        cfg = config()
        for item in queue():
            for platform in item["platforms"]:
                payload = planner.payload_for(item, platform, NOW + dt.timedelta(days=1), cfg)
                coerce_input_value(payload, self.schema.get_type("CreatePostInput"))
                self.assertEqual(payload["mode"], "customScheduled")
                self.assertEqual(payload["schedulingType"], "automatic")
                self.assertNotIn("thumbnailUrl", payload["assets"][0]["video"])

    def test_native_ai_label_only_where_schema_supports_it(self):
        cfg, item = config(), queue()[0]
        fb = planner.payload_for(item, "facebook", NOW, cfg)
        ig = planner.payload_for(item, "instagram", NOW, cfg)
        self.assertNotIn("isAiGenerated", fb["metadata"]["facebook"])
        self.assertIn("AI-generated narration.", fb["text"])
        self.assertTrue(ig["metadata"]["instagram"]["isAiGenerated"])

    def test_all_six_kits_have_option_three_voice_and_qa(self):
        manifests = load_json(ROOT / "research/publishing/initial-kit-manifests.json")
        self.assertEqual(len(manifests), 6)
        for vid, manifest in manifests.items():
            check_manifest(manifest, vid)

    def test_old_voice_cannot_pass_publishing_gate(self):
        vid, manifest = next(iter(load_json(ROOT / "research/publishing/initial-kit-manifests.json").items()))
        manifest["stages"]["voice"]["engine"] = "kokoro am_michael"
        with self.assertRaises(ValueError):
            check_manifest(manifest, vid)

    def test_redirecting_media_rejected(self):
        session = Mock()
        session.get.return_value = response(302, headers={"Location": "https://other.invalid/asset.mp4"})
        with self.assertRaises(ValueError):
            media.verify_url("https://example.invalid/video.mp4", 100, session=session)
        self.assertFalse(session.get.call_args.kwargs["allow_redirects"])

    def test_valid_public_mp4_range(self):
        session = Mock()
        r = response(206, headers={"Content-Type": "video/mp4", "Content-Range": "bytes 0-1023/2000"})
        r.iter_content.return_value = iter([b"\x00\x00\x00\x20ftypisom"])
        session.get.return_value = r
        media.verify_url("https://example.invalid/video.mp4", 2000, session=session)
        r.close.assert_called_once()

    def test_pending_media_never_evicted(self):
        item = fixture_items(1)[0]
        rec = {"k": {"state": "uncertain", "media_ref": item, "sent_at": None}}
        self.assertEqual(media.references([], rec, config(), NOW), [item])

    def test_three_reported_youtube_uploads_are_locked(self):
        records = load_json(ROOT / "tracker/publications.json")["records"]
        for vid in ("repo-removemacai-01", "tool-muse-01", "spotlight-papermorph-01"):
            rec = records[key(vid, "youtube")]
            self.assertIn(rec["state"], {"sent", "published_manual"})
            self.assertIn("youtube.com/shorts/", rec["external_url"])

    def test_secret_scanner_and_log_redaction_include_buffer(self):
        with patch.dict("os.environ", {"BUFFER_API_KEY": "unit-test-buffer-credential-only"}):
            self.assertTrue(secrets.contains_secret("leak unit-test-buffer-credential-only"))
            self.assertEqual(secrets.redact("unit-test-buffer-credential-only"), "[REDACTED]")


if __name__ == "__main__":
    unittest.main()
