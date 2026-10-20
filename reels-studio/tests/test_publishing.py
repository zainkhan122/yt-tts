"""Safety regression suite. No real credentials/network calls or social writes."""
import copy
import datetime as dt
import io
import json
import os
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
        self.cfg["schedule"].pop("daily_target_overrides", None)  # dated production overrides never alter fixtures
        self.channels = channels(self.cfg)

    def planned(self, items=None, records=None, posts=None, **kwargs):
        with patch.object(planner, "payload_for", side_effect=fake_payload):
            return planner.plan(items or fixture_items(), records or {}, self.channels, posts or [], self.cfg, NOW, **kwargs)

    def test_planner_recreates_released_rows_against_corrected_media(self):
        # Regression (2026-10-18): release_row promised recreation, but the planner
        # blocked every non-RETRYABLE record, so cleared rows could never come back.
        from tools.post.common import key as row_key
        items = fixture_items(1)
        records = {row_key(items[0]["video_id"], p): {"video_id": items[0]["video_id"],
                   "platform": p, "state": "released", "buffer_post_id": None,
                   "previous_buffer_post_id": "gone", "due_at": "2026-10-13T19:00:00Z"}
                   for p in items[0]["platforms"]}
        rows, _ = self.planned(items=items, records=records)
        self.assertEqual({r["platform"] for r in rows}, set(items[0]["platforms"]))

    def test_ten_videos_stay_in_backlog_not_bulk_dump(self):
        # Content mix is editorial (see test_mix_is_not_hardcoded); pacing still governs.
        self.cfg["schedule"]["max_posts_per_run"] = 100
        rows, _ = self.planned()
        self.assertEqual(len(rows), 19)
        for platform in ("youtube", "instagram", "facebook"):
            selected = [r for r in rows if r["platform"] == platform]
            self.assertGreaterEqual(len(selected), 6)  # most of the batch is scheduled, not dumped
            days = {}
            for row in selected:
                days.setdefault(row["due_local"][:10], []).append(row)
            for day in days.values():
                self.assertLessEqual(len(day), self.cfg["schedule"]["daily_target"])
            times = sorted(parse_time(r["due_at"]) for r in selected)
            self.assertTrue(all((b - a).total_seconds() >= self.cfg["schedule"]["minimum_gap_minutes"]*60 for a, b in zip(times, times[1:])))

    def test_dated_override_expands_one_day_only(self):
        # Owner-instruction batches may raise a single calendar day, never the 3/day baseline.
        self.cfg["schedule"]["max_posts_per_run"] = 100
        self.cfg["schedule"]["daily_target_overrides"] = {"2026-10-10": 5}
        rows, _ = self.planned()
        for platform in ("youtube", "instagram", "facebook"):
            selected = [r for r in rows if r["platform"] == platform]
            override_day = [r for r in selected if r["due_local"][:10] == "2026-10-10"]
            self.assertEqual(len(override_day), 5)
            times = sorted(parse_time(r["due_at"]) for r in override_day)
            self.assertTrue(all((b - a).total_seconds() >= self.cfg["schedule"]["minimum_gap_minutes"]*60 for a, b in zip(times, times[1:])))
            self.assertLessEqual(sum(r["category"] == "repo" for r in override_day),
                                 self.cfg["schedule"]["max_repo_videos_per_day"])
        # Removing the override restores the baseline target per day.
        self.cfg["schedule"]["daily_target_overrides"] = {}
        base_rows, _ = self.planned()
        self.assertEqual(len(base_rows), 19)
        for platform in ("youtube", "instagram", "facebook"):
            days = {}
            for r in (x for x in base_rows if x["platform"] == platform):
                days.setdefault(r["due_local"][:10], []).append(r)
            self.assertTrue(all(len(v) <= 3 for v in days.values()))

    def test_override_cannot_exceed_hard_caps(self):
        self.cfg["schedule"]["max_posts_per_run"] = 100
        self.cfg["schedule"]["daily_target_overrides"] = {"2026-10-10": 99}
        rows, _ = self.planned()
        days = {}
        for r in rows:
            days.setdefault((r["platform"], r["due_local"][:10]), []).append(r)
        self.assertTrue(days)
        self.assertTrue(all(len(v) <= self.cfg["schedule"]["max_videos_per_day"] for v in days.values()))

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

    def test_repo_weighted_batch_is_allowed_when_merit_picks_it(self):
        # Owner 2026-10-11: the mix is not hardcoded. A repo-strong batch schedules under
        # the same pacing caps instead of being vetoed by a fixed news/tool requirement.
        items = fixture_items(6)
        for i in items:
            i["category"] = "repo"
        self.cfg["schedule"]["max_posts_per_run"] = 100
        rows, notes = self.planned(items)
        self.assertTrue(rows)
        self.assertFalse(any("repo-only" in n or "mix" in n for n in notes))
        for platform in ("youtube", "instagram", "facebook"):
            selected = [r for r in rows if r["platform"] == platform]
            times = sorted(parse_time(r["due_at"]) for r in selected)
            self.assertTrue(all((b - a).total_seconds() >= self.cfg["schedule"]["minimum_gap_minutes"]*60 for a, b in zip(times, times[1:])))

    def test_mix_is_not_hardcoded_in_config(self):
        self.assertEqual(self.cfg["schedule"]["required_daily_categories"], [])
        self.assertGreaterEqual(self.cfg["schedule"]["max_repo_videos_per_day"], self.cfg["schedule"]["max_videos_per_day"])

    def test_daily_ceiling_is_ten_and_has_no_hidden_five_clamp(self):
        # Owner 2026-10-12: the 5/day cap is removed; the ceiling is 10 and the scheduler
        # must be able to place more than 5 on a day when a dated override asks for it.
        self.assertEqual(self.cfg["schedule"]["max_videos_per_day"], 10)
        self.cfg["schedule"]["max_posts_per_run"] = 100
        self.cfg["buffer"]["queue_target_per_channel"] = 10  # capacity guardrail raised for the test day
        self.cfg["schedule"]["daily_target_overrides"] = {"2026-10-10": 10}
        now = dt.datetime(2026, 10, 10, 6, 0, tzinfo=dt.timezone.utc)  # first lookahead day is the override day
        with patch.object(planner, "payload_for", side_effect=fake_payload):
            rows, _ = planner.plan(fixture_items(12), {}, self.channels, [], self.cfg, now)
        day_rows = [r for r in rows if r["platform"] == "youtube" and r["due_local"][:10] == "2026-10-10"]
        self.assertGreater(len(day_rows), 5)   # impossible while cadence hard-clamped at 5
        self.assertLessEqual(len(day_rows), 10)
        times = sorted(parse_time(r["due_at"]) for r in day_rows)
        self.assertTrue(all((b - a).total_seconds() >= self.cfg["schedule"]["minimum_gap_minutes"]*60
                            for a, b in zip(times, times[1:])))
        self.cfg["schedule"]["daily_target_overrides"] = {}

    def test_disconnected_channel_does_not_block_healthy_channels(self):
        next(c for c in self.channels if c["id"] == self.cfg["buffer"]["channels"]["youtube"]["buffer_id"])["isDisconnected"] = True
        rows, notes = self.planned()
        self.assertTrue(rows)
        self.assertFalse(any(r["platform"] == "youtube" for r in rows))
        self.assertTrue(any("isDisconnected" in n for n in notes))

    def test_social_account_identity_mismatch_blocks(self):
        next(c for c in self.channels if c["id"] == self.cfg["buffer"]["channels"]["youtube"]["buffer_id"])["serviceId"] = "wrong-account"
        rows, _ = self.planned()
        self.assertFalse(any(r["platform"] == "youtube" for r in rows))

    def test_facebook_native_label_policy_hold_blocks_even_when_connected(self):
        self.cfg["buffer"]["channels"]["facebook"]["posting_hold"] = "Native AI label unsupported"
        rows, notes = self.planned()
        self.assertFalse(any(r["platform"] == "facebook" for r in rows))
        self.assertTrue(any("policy hold" in n for n in notes))

    def test_notification_only_channel_blocks(self):
        next(c for c in self.channels if c["id"] == self.cfg["buffer"]["channels"]["youtube"]["buffer_id"])["metadata"]["defaultToReminders"] = True
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


def normalised_schema(path):
    """Build the client schema after aligning interface deprecation flags.

    The captured Buffer introspection marks RestProxyError.message deprecated while the
    MutationError interface it implements is not, which makes graphql-core reject the whole
    schema before any query can be validated. Align the implementation flags with their
    interface so the fixture stays faithful for types/arguments but valid for validation.
    """
    doc = load_json(path)
    schema = doc.get("data", doc)["__schema"]
    interfaces = {t["name"]: {f["name"]: bool(f.get("isDeprecated")) for f in (t.get("fields") or [])}
                  for t in schema["types"] if t.get("kind") == "INTERFACE"}
    for t in schema["types"]:
        if t.get("kind") != "OBJECT":
            continue
        inherited = {}
        for iface in t.get("interfaces") or []:
            inherited.update(interfaces.get(iface.get("name"), {}))
        for field in t.get("fields") or []:
            if field["name"] in inherited:
                field["isDeprecated"] = inherited[field["name"]]
                if not inherited[field["name"]]:
                    field.pop("deprecationReason", None)
    return build_client_schema(doc)


class VerifyModeExitTests(unittest.TestCase):
    """The wiring, not just the helper: --verify must exit non-zero when Buffer disagrees."""

    def run_verify(self, posts, video_id="repo-huashu-motion-01"):
        import argparse
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "report.json"
            stub = Mock()
            stub.capabilities = {"facebook_ai_generated": True}
            stub.request_count, stub.policies = 0, []
            stub.state.return_value = ([], posts)
            stub.channels.return_value = []
            argv = ["unittest", video_id, "--verify", "--report", str(report)]
            with patch.object(sys, "argv", argv), \
                 patch.object(publisher, "BufferClient", return_value=stub), \
                 patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=False):
                code = publisher.main()
            return code, json.loads(report.read_text()), report.with_suffix(".md").read_text()

    def test_missing_scheduled_post_fails_the_run(self):
        code, report, text = self.run_verify([])
        self.assertEqual(code, 1)
        self.assertIn("DRIFT", text)
        self.assertIn("Buffer has no such post", text)
        self.assertEqual(report["mode"], "verify")

    def test_matching_posts_pass(self):
        journal = load_json(ROOT / "tracker/publications.json")["records"]
        due = journal["repo-huashu-motion-01:youtube"]["due_at"]
        posts = []
        for platform in ("youtube", "instagram", "facebook"):
            rec = journal[f"repo-huashu-motion-01:{platform}"]
            posts.append({"id": rec["buffer_post_id"], "status": "scheduled", "dueAt": rec["due_at"],
                          "assets": [{"source": "https://x/media/1/repo-huashu-motion-01.mp4"}]})
        code, report, text = self.run_verify(posts)
        self.assertEqual(code, 0, text)
        self.assertIn("verified", text)
        self.assertNotIn("DRIFT", text)


class SchemaAndMediaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = normalised_schema(ROOT / "research/publishing/buffer-schema-2026-10-10.json")

    def test_graphql_queries_and_mutation_validate_against_official_schema(self):
        for query_text in (api.STATE_QUERY, api.MORE_POSTS, api.CHANNELS_QUERY, api.CREATE):
            self.assertEqual(validate(self.schema, parse(query_text)), [])

    def test_verify_plan_passes_only_when_buffer_matches_the_journal(self):
        cfg = config()
        ch = cfg["buffer"]["channels"]
        item = {"video_id": "a", "approval": "approved", "platforms": ["youtube", "facebook", "instagram"],
                "media_path": "media/1/a.mp4"}
        due = "2026-10-20T20:00:00+00:00"
        records = {f"a:{p}": {"video_id": "a", "platform": p, "state": "scheduled",
                              "buffer_post_id": f"id-{p}", "due_at": due} for p in item["platforms"]}
        good = [{"id": f"id-{p}", "channelId": ch[p]["buffer_id"], "status": "scheduled",
                 "dueAt": due, "assets": [{"source": "https://x/media/1/a.mp4"}]} for p in item["platforms"]]
        rows, issues = publisher.verify_plan(records, [item], good, cfg, NOW)
        self.assertEqual(issues, [])
        self.assertTrue(all(row["problem"] is None for row in rows))

        draft = [dict(p, status="draft") for p in good]
        _, issues = publisher.verify_plan(records, [item], draft, cfg, NOW)
        self.assertEqual({i["state"] for i in issues}, {"drift"})
        self.assertIn("not scheduled", issues[0]["error"])

        moved = [dict(p, dueAt="2026-10-21T20:00:00+00:00") for p in good]
        _, issues = publisher.verify_plan(records, [item], moved, cfg, NOW)
        self.assertIn("due time drifted", issues[0]["error"])

        stale = [dict(p, assets=[{"source": "https://x/media/9/old.mp4"}]) for p in good]
        _, issues = publisher.verify_plan(records, [item], stale, cfg, NOW)
        self.assertIn("but queue pins a.mp4", issues[0]["error"])

        _, issues = publisher.verify_plan(records, [item], [], cfg, NOW)
        self.assertEqual(len(issues), 3)
        self.assertIn("Buffer has no such post", issues[0]["error"])

    def test_verify_plan_treats_unscheduled_as_note_and_terminal_without_proof_as_drift(self):
        cfg = config()
        item = {"video_id": "b", "approval": "approved", "platforms": ["youtube"], "media_path": "media/2/b.mp4"}
        rows, issues = publisher.verify_plan({}, [item], [], cfg, NOW)
        self.assertEqual(issues, [])
        self.assertIn("not scheduled yet", rows[0]["note"])
        terminal = {"b:youtube": {"video_id": "b", "platform": "youtube", "state": "sent",
                                  "buffer_post_id": "gone", "due_at": "2026-10-19T20:00:00+00:00"}}
        _, issues = publisher.verify_plan(terminal, [item], [], cfg, NOW)
        self.assertIn("without a Buffer post or public URL", issues[0]["error"])

    def test_readback_only_calls_it_scheduled_when_buffer_agrees(self):
        records = {"a:youtube": {"video_id": "a", "platform": "youtube", "state": "submitting",
                                 "buffer_post_id": "live", "due_at": "2026-10-20T20:00:00+00:00"}}
        rows = publisher.readback(records, ["a:youtube"],
                                  [{"id": "live", "status": "scheduled", "dueAt": "2026-10-20T20:00:00+00:00",
                                    "assets": [{"source": "https://x/a.mp4"}]}], NOW)
        self.assertIsNone(rows[0]["problem"])
        self.assertEqual(records["a:youtube"]["state"], "scheduled")
        self.assertEqual(records["a:youtube"]["verified_at"], publisher.iso(NOW))

        lost = {"a:youtube": {"video_id": "a", "platform": "youtube", "state": "submitting",
                              "buffer_post_id": "ghost", "due_at": "2026-10-20T20:00:00+00:00"}}
        rows = publisher.readback(lost, ["a:youtube"], [], NOW)
        self.assertEqual(lost["a:youtube"]["state"], "unverified_missing")
        self.assertIn("absent from read-back", rows[0]["problem"])
        self.assertNotEqual(lost["a:youtube"]["state"], "scheduled")

    def test_inventory_reports_drift_without_writing(self):
        cfg = config()
        channels = [{"id": c["buffer_id"], "name": n, "service": n, "isDisconnected": False,
                     "isLocked": False, "isQueuePaused": False} for n, c in cfg["buffer"]["channels"].items()]
        journal = {
            "a:youtube": {"video_id": "a", "platform": "youtube", "state": "scheduled",
                          "buffer_post_id": "live-1", "due_at": "2026-10-20T20:00:00+00:00"},
            "a:facebook": {"video_id": "a", "platform": "facebook", "state": "scheduled",
                           "buffer_post_id": "gone-1", "due_at": "2026-10-20T16:00:00+00:00"},
        }
        posts = [{"id": "live-1", "channelId": cfg["buffer"]["channels"]["youtube"]["buffer_id"],
                  "status": "draft", "dueAt": "2026-10-20T20:00:00+00:00", "assets": [{"source": "https://x/a.mp4"}]}]
        report = {"mode": "inventory", "inventory": publisher.inventory(channels, posts, journal, cfg, [], NOW)}
        text = publisher.summary(report)
        self.assertIn("MISSING from Buffer", text)
        self.assertIn("state differs", text)
        self.assertIn("draft", text)
        self.assertIn("a.mp4", text)
        self.assertEqual(journal["a:facebook"]["state"], "scheduled")  # diagnostic never mutates

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


class LegacyMediaPathTests(unittest.TestCase):
    """A re-rendered video must keep serving its already-queued URL (fix shipped after scheduling)."""

    def test_alias_paths_are_served_and_indexed(self):
        item = {"video_id": "news-clef-01", "asset_id": 999, "asset_size": 10,
                "media_path": "media/999/news-clef-01.mp4",
                "legacy_media_paths": ["media/633351677/news-clef-01.mp4"]}
        self.assertEqual(media.legacy_paths(item), ["media/633351677/news-clef-01.mp4"])

    def test_alias_must_be_the_same_video(self):
        item = {"video_id": "news-clef-01", "asset_id": 999, "media_path": "media/999/news-clef-01.mp4",
                "legacy_media_paths": ["media/123/other-video.mp4"]}
        with self.assertRaises(ValueError):
            media.legacy_paths(item)

    def test_alias_equal_to_the_current_path_is_dropped(self):
        item = {"video_id": "news-clef-01", "asset_id": 999, "media_path": "media/999/news-clef-01.mp4",
                "legacy_media_paths": ["media/999/news-clef-01.mp4"]}
        self.assertEqual(media.legacy_paths(item), [])

    def test_no_legacy_paths_is_an_empty_list(self):
        self.assertEqual(media.legacy_paths({"video_id": "x-01", "asset_id": 1, "media_path": "media/1/x-01.mp4"}), [])


if __name__ == "__main__":
    unittest.main()


class ImmediatePilotTests(unittest.TestCase):
    def setUp(self):
        self.cfg = config()
        self.items = fixture_items(1)
        self.items[0].update(approval="approved", reviewed_at=iso(NOW), expires_at=iso(NOW + dt.timedelta(days=1)))
        self.channels = channels(self.cfg)

    def call_plan(self, records=None, posts=None, items=None):
        from tools.post.pilot import immediate_plan
        with patch("tools.post.pilot.payload_for", side_effect=lambda i,p,d,c: fake_payload(i,p,d,c)):
            return immediate_plan(items or self.items, records or {}, self.channels, posts or [], self.cfg, NOW)

    def test_immediate_pilot_has_no_scheduled_due_at(self):
        rows, _ = self.call_plan()
        self.assertEqual(len(rows), 3)
        for r in rows:
            self.assertEqual(r["payload"]["mode"], "shareNow")
            self.assertNotIn("dueAt", r["payload"])

    def test_immediate_batch_is_refused(self):
        with self.assertRaises(ValueError): self.call_plan(items=fixture_items(2))

    def test_recent_post_blocks_immediate_pilot(self):
        post={"id":"recent", "channelId":self.cfg["buffer"]["channels"]["youtube"]["buffer_id"], "status":"sent", "sentAt":iso(NOW-dt.timedelta(minutes=20))}
        with self.assertRaises(ValueError): self.call_plan(posts=[post])

    def test_manual_duplicate_is_not_recreated_by_pilot(self):
        i=self.items[0]
        records={i["video_id"]+":youtube":{"video_id":i["video_id"],"platform":"youtube","state":"published_manual","sent_at":iso(NOW-dt.timedelta(days=2))}}
        rows,_=self.call_plan(records=records)
        self.assertEqual({r["platform"] for r in rows},{"facebook","instagram"})


class RepinTests(unittest.TestCase):
    """Re-pinning a queued video to a corrected render (blank-first-frame fix, 2026-10-12)."""

    def setUp(self):
        from tools.post import repin
        self.repin = repin

    def item(self, **over):
        base = {"video_id": "news-clef-01", "asset_id": 111, "asset_size": 10, "asset_digest": "sha256:old",
                "kit_asset_id": 112, "kit_digest": "sha256:oldkit", "release_tag": "renders-2026-10-12",
                "media_path": "media/111/news-clef-01.mp4", "cover_sha256": "sha256:cover", "cover_reviewed_at": "2026-10-12T09:00:00Z"}
        base.update(over)
        return base

    def assets(self):
        return {"news-clef-01.mp4": {"id": 222, "name": "news-clef-01.mp4", "size": 20, "digest": "sha256:new"},
                "news-clef-01-kit.zip": {"id": 223, "name": "news-clef-01-kit.zip", "size": 5, "digest": "sha256:newkit"}}

    def test_repin_moves_the_pin_and_keeps_the_old_url(self):
        updated, changes = self.repin.repin(self.item(), self.assets(), "renders-2026-10-12-r3")
        self.assertEqual(updated["asset_id"], 222)
        self.assertEqual(updated["media_path"], "media/222/news-clef-01.mp4")
        self.assertEqual(updated["legacy_media_paths"], ["media/111/news-clef-01.mp4"])
        self.assertEqual(updated["kit_asset_id"], 223)
        self.assertEqual(updated["release_tag"], "renders-2026-10-12-r3")

    def test_cover_approval_is_cleared_and_must_be_redone(self):
        updated, changes = self.repin.repin(self.item(), self.assets(), "r3")
        self.assertIsNone(updated["cover_sha256"])
        self.assertIsNone(updated["cover_reviewed_at"])
        self.assertTrue(any("cover approval cleared" in c for c in changes))

    def test_missing_assets_are_refused(self):
        with self.assertRaises(ValueError):
            self.repin.repin(self.item(), {"news-clef-01.mp4": {"id": 1, "name": "news-clef-01.mp4", "size": 1}}, "r3")

    def test_already_pinned_is_a_no_op(self):
        item = self.item()
        assets = self.assets()
        item.update(asset_id=222, media_path="media/222/news-clef-01.mp4", asset_size=20, asset_digest="sha256:new",
                    kit_asset_id=223, kit_digest="sha256:newkit", release_tag="r3")
        updated, changes = self.repin.repin(item, assets, "r3")
        self.assertEqual(changes, [])
        self.assertEqual(updated["cover_sha256"], "sha256:cover")  # untouched when nothing changed

    def test_alias_list_is_capped_and_deduplicated(self):
        item = self.item(legacy_media_paths=["media/100/news-clef-01.mp4", "media/111/news-clef-01.mp4"])
        updated, _ = self.repin.repin(item, self.assets(), "r3")
        self.assertEqual(updated["legacy_media_paths"], ["media/111/news-clef-01.mp4", "media/100/news-clef-01.mp4"])


class PlanRefsTests(unittest.TestCase):
    """A superseded asset (old media_ref) must be served as an alias, never downloaded again."""

    def ref(self, vid, asset_id, legacy=None):
        item = {"video_id": vid, "asset_id": asset_id, "asset_size": 1, "media_path": f"media/{asset_id}/{vid}.mp4"}
        if legacy:
            item["legacy_media_paths"] = legacy
        return item

    def test_superseded_ref_is_not_downloaded_and_becomes_an_alias(self):
        new = self.ref("a-01", 200, legacy=["media/100/a-01.mp4"])
        old_ref = self.ref("a-01", 100)
        to_build, aliases = media.plan_refs([new, old_ref])
        self.assertEqual([i["asset_id"] for i in to_build], [200])
        self.assertEqual(aliases, {"media/100/a-01.mp4": new})

    def test_unrelated_refs_are_untouched(self):
        a = self.ref("a-01", 100)
        b = self.ref("b-01", 200)
        to_build, aliases = media.plan_refs([a, b])
        self.assertEqual({i["asset_id"] for i in to_build}, {100, 200})
        self.assertEqual(aliases, {})


class ReferenceMergeTests(unittest.TestCase):
    """Journal pins must not clobber the queue item (it carries legacy_media_paths)."""

    def item(self, asset_id, legacy=None):
        i = {"video_id": "news-clef-01", "asset_id": asset_id, "asset_size": 1, "approval": "approved",
             "platforms": ["youtube"], "media_path": f"media/{asset_id}/news-clef-01.mp4"}
        if legacy:
            i["legacy_media_paths"] = legacy
        return i

    def cfg(self):
        return {"media": {"retention_days": 7},
                "buffer": {"channels": {"youtube": {"enabled": True}}}}

    def test_journal_pin_for_the_same_asset_keeps_the_queue_metadata(self):
        queue_item = self.item(200, legacy=["media/100/news-clef-01.mp4"])
        records = {"news-clef-01:youtube": {"state": "scheduled", "sent_at": None, "media_ref": self.item(200)}}
        refs = media.references([queue_item], records, self.cfg(), NOW)
        same = [r for r in refs if r["asset_id"] == 200]
        self.assertEqual(len(same), 1)
        self.assertEqual(same[0].get("legacy_media_paths"), ["media/100/news-clef-01.mp4"])
        to_build, aliases = media.plan_refs(refs)
        self.assertEqual([i["asset_id"] for i in to_build], [200])
        self.assertEqual(aliases, {"media/100/news-clef-01.mp4": queue_item})

    def test_old_pin_is_still_kept_alive(self):
        queue_item = self.item(200, legacy=["media/100/news-clef-01.mp4"])
        records = {"news-clef-01:youtube": {"state": "scheduled", "sent_at": None, "media_ref": self.item(100)}}
        refs = media.references([queue_item], records, self.cfg(), NOW)
        self.assertEqual({r["asset_id"] for r in refs}, {100, 200})
        to_build, aliases = media.plan_refs(refs)
        self.assertEqual([i["asset_id"] for i in to_build], [200])  # the old pin is aliased, not downloaded


class QueueReleaseTests(unittest.TestCase):
    """Owner-authorised Buffer queue clear (recreate against corrected media, 2026-10-12)."""

    def setUp(self):
        from tools.post import release
        self.release = release

    def row(self, state="scheduled", pid="bp1"):
        return {"video_id": "news-clef-01", "platform": "facebook", "state": state,
                "buffer_post_id": pid, "due_at": "2026-10-13T19:00:00Z", "external_url": None}

    def test_release_marks_row_recreatable_and_keeps_audit(self):
        r = self.release.release_row(self.row(), "owner clear", self.release.now_utc())
        self.assertEqual(r["state"], "released")
        self.assertIsNone(r["buffer_post_id"])
        self.assertEqual(r["previous_buffer_post_id"], "bp1")
        self.assertIn("released_at", r)

    def test_published_rows_are_never_released(self):
        with self.assertRaises(ValueError):
            self.release.release_row(self.row(state="sent"), "x", self.release.now_utc())
        with self.assertRaises(ValueError):
            self.release.release_row(self.row(state="published_manual"), "x", self.release.now_utc())

    def test_released_is_not_terminal_so_the_planner_can_recreate(self):
        from tools.post.common import TERMINAL
        self.assertNotIn(self.release.RELEASED, TERMINAL)
        r = self.release.release_row(self.row(), "x", self.release.now_utc())
        self.assertNotIn(r["state"], TERMINAL)


    def test_writes_require_the_exact_confirmation(self):
        import subprocess, sys
        out = subprocess.run([sys.executable, str(ROOT / "tools/post/release.py"), "--keys", "a-01:facebook"],
                             capture_output=True, text=True)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("refusing to write", out.stdout + out.stderr)

    def test_pending_rows_filter(self):
        journal = {"records": {"a:facebook": self.row(), "b:youtube": self.row(state="sent"),
                               "c:instagram": self.row(state="released")}}
        rows = self.release.pending_rows(journal)
        self.assertEqual(sorted(rows), ["a:facebook", "c:instagram"])

    def test_delete_row_is_terminal_and_keeps_audit(self):
        from tools.post.common import TERMINAL
        r = self.row(state="delivery_error")
        r["last_error"] = "unknown error"
        out = self.release.delete_row(r, "owner delete", self.release.now_utc())
        self.assertEqual(out["state"], "deleted")
        self.assertIn(out["state"], TERMINAL)
        self.assertIsNone(out["buffer_post_id"])
        self.assertEqual(out["previous_buffer_post_id"], "bp1")
        self.assertIn("deleted_at", out)
        self.assertNotIn("last_error", out)

    def test_delete_row_refuses_published(self):
        with self.assertRaises(ValueError):
            self.release.delete_row(self.row(state="sent"), "x", self.release.now_utc())

    def test_is_published_distinguishes_failed_delivery(self):
        self.assertTrue(self.release.is_published({"status": "sent"}))
        self.assertFalse(self.release.is_published({"status": "sent", "error": {"message": "x"}}))
        self.assertFalse(self.release.is_published({"status": "error", "error": {"message": "x"}}))
        self.assertFalse(self.release.is_published(None))

    def test_deletable_rows_include_delivery_error_only(self):
        journal = {"records": {"a:facebook": self.row(), "b:youtube": self.row(state="sent"),
                               "c:instagram": self.row(state="delivery_error"),
                               "d:youtube": self.row(state="uncertain")}}
        rows = self.release.deletable_rows(journal)
        self.assertEqual(sorted(rows), ["a:facebook", "c:instagram"])

    def test_sent_buffer_posts_are_never_editpost_refresh_candidates(self):
        found = [
            {"key": "sent:facebook", "status": "sent", "verdict": "STALE"},
            {"key": "scheduled:instagram", "status": "scheduled", "verdict": "STALE"},
            {"key": "fresh:youtube", "status": "scheduled", "verdict": "OK"},
            {"key": "published:facebook", "status": "published", "verdict": "STALE"},
        ]
        self.assertTrue(self.release.sent_in_buffer("sent"))
        self.assertTrue(self.release.sent_in_buffer("published"))
        self.assertFalse(self.release.sent_in_buffer("scheduled"))
        self.assertEqual([r["key"] for r in self.release.refresh_candidates(found)], ["scheduled:instagram"])

    def test_scheduled_delivery_fails_closed_if_media_refresh_fails(self):
        workflow = (ROOT.parent / ".github/workflows/post.yml").read_text()
        start = workflow.index("- name: Fail-closed media freshness guard")
        end = workflow.index("- name: Paced delivery / read-only validation", start)
        guard = workflow[start:end]
        self.assertIn("needs.prepare.outputs.mode == 'schedule'", guard)
        self.assertIn("inputs.skip_global_media_refresh != true", guard)
        skip_input = workflow[workflow.index("skip_global_media_refresh:"):workflow.index("skip_global_media_refresh:") + 260]
        self.assertIn("default: false", skip_input)
        self.assertIn("release.py --refresh --confirm OWNER_APPROVED_MEDIA_REFRESH", guard)
        self.assertNotIn("continue-on-error", guard)
        # GitHub's default success() condition prevents the following createPost step after a failure.
        self.assertLess(start, end)

    def test_audit_flags_posts_still_holding_old_media(self):
        from tools.post.release import audit
        queue = {"items": [{"video_id": "news-clef-01", "media_path": "media/633733386/news-clef-01.mp4"}]}
        cfg = {"media": {"base_url": "https://cdn.example/media"}}
        rows = {"news-clef-01:facebook": {"video_id": "news-clef-01", "buffer_post_id": "bp1"}}
        posts = [{"id": "bp1", "status": "scheduled", "dueAt": "2026-10-13T19:00:00Z",
                  "assets": [{"source": "https://cdn.example/media/media/633071756/news-clef-01.mp4"}]}]
        out = audit(rows, posts, queue, cfg)
        self.assertEqual(out[0]["verdict"], "STALE")
        posts[0]["assets"] = [{"source": "https://cdn.example/media/media/633733386/news-clef-01.mp4"}]
        self.assertEqual(audit(rows, posts, queue, cfg)[0]["verdict"], "OK")

    def test_refresh_payload_swaps_the_video_and_keeps_slot(self):
        from tools.post.release import refresh_input
        from tools.post.common import iso, now_utc
        cfg = self.cfg()
        item = {"video_id": "news-clef-01", "media_path": "media/633733386/news-clef-01.mp4"}
        fb = refresh_input({"buffer_post_id": "bp1", "_key": "news-clef-01:facebook"}, item, cfg, iso(now_utc()))
        self.assertEqual(fb["id"], "bp1")
        self.assertEqual(fb["assets"][0]["video"]["url"],
                         "https://cdn.example/media/media/633733386/news-clef-01.mp4")
        self.assertEqual(fb["metadata"], {"facebook": {"type": "reel"}})   # required members resent, whole post validates
        for kept in ("dueAt", "mode", "schedulingType", "text"):          # never rewritten: slot + caption stay as stored
            self.assertNotIn(kept, fb)
        ig = refresh_input({"buffer_post_id": "bp2", "_key": "news-clef-01:instagram"}, item, cfg, iso(now_utc()))
        self.assertEqual(ig["assets"][0]["video"]["metadata"], {"thumbnailOffset": 1000})
        self.assertEqual(ig["metadata"]["instagram"]["type"], "reel")
        self.assertTrue(ig["metadata"]["instagram"]["shouldShareToFeed"])

    def cfg(self):
        import json
        from tools.post.common import config
        c = json.loads(json.dumps(config()))
        c["media"] = {"base_url": "https://cdn.example/media"}
        return c

    def test_refresh_requires_its_own_confirmation(self):
        import subprocess, sys
        out = subprocess.run([sys.executable, str(ROOT / "tools/post/release.py"), "--refresh",
                              "--confirm", "OWNER_APPROVED_QUEUE_CLEAR"], capture_output=True, text=True)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("refusing to refresh", out.stdout + out.stderr)
