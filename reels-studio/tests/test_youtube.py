"""No live Google/Buffer calls. Failure injection for the direct uploader."""
import base64
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import requests
from PIL import Image
from tools.post.common import iso, load_json
from tools.post.cadence import at_local, can_notify, clocks_for
from tools.youtube import api, contracts, metadata, oauth_connect, resumable, runner, schedule, secure_state, seo, thumbnail

NOW = dt.datetime(2026,10,10,10,tzinfo=dt.timezone.utc)
SESSION = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&upload_id=unit-test"
KEY = base64.urlsafe_b64encode(b"k"*32).decode()
VIDEO_ID = "YTTEST00001"


def cfg():
    return load_json(ROOT/"config/youtube.json")


class Journal:
    def __init__(self):
        self.data = {"records": {}, "quota": {}, "playlists": {}, "memberships": {}, "enrichment": {}}
        self.saves = []
        self.fail_on = None

    @property
    def records(self):
        return self.data["records"]

    def save(self, message):
        if self.fail_on and self.fail_on in message:
            raise RuntimeError("journal unavailable")
        self.saves.append((message, copy.deepcopy(self.data)))


class Clock:
    def __init__(self):
        self.t = 0.0
        self.waits = []

    def now(self):
        return self.t

    def sleep(self, value):
        self.t += value
        self.waits.append(value)


def response(status=200, body=None, headers=None):
    r = Mock()
    r.status_code = status
    r.headers = headers or {}
    r.json.return_value = body if body is not None else {}
    return r


def brief():
    return {"id":"long-demo", "format":"long", "duration_seconds":480,
            "seo":{"keyword":"Example AI", "youtube":{"title":"Example AI: Tested, Not Hyped", "description":"Example AI tested with a real workflow. Here is what worked and what did not.",
                    "tags":["Example AI", "AI tools", "Example AI tutorial"], "hashtags":["#AItools", "#Hypeless"]}},
            "chapters":[{"start_seconds":0,"title":"The result"},{"start_seconds":60,"title":"The test"},{"start_seconds":300,"title":"The catch"}],
            "sources":["https://example.com/official-demo"], "credits":"Our own demo capture"}


def item(data=b"test-video-data"):
    digest = "sha256:"+hashlib.sha256(data).hexdigest()
    return {"video_id":"long-demo", "category":"tool", "asset_digest":digest, "asset_id":123,
            "assets":{"video":{"id":123,"size":len(data),"digest":digest,"name":"long-demo.mp4"},
                      "thumbnail":{"id":124,"size":100,"digest":"sha256:"+"b"*64,"name":"long-demo-thumbnail.jpg"}},
            "approval":"approved", "public_approved":True, "reviewed_at":iso(NOW), "expires_at":iso(NOW+dt.timedelta(days=14)), "thumbnail_reviewed_at":iso(NOW)}


class APITests(unittest.TestCase):
    def client(self, replies, configuration=None):
        settings = configuration or cfg()
        journal, session, clock = Journal(), Mock(), Clock()
        session.request.side_effect = replies
        client = api.YouTubeAPI(settings, journal, credentials={"client_id":"unit-client", "client_secret":"unit-secret", "refresh_token":"unit-refresh"},
            session=session, sleep=clock.sleep, clock=clock.now, wallclock=lambda:NOW, jitter=lambda:.1)
        client.token, client.expires = "test-access", 10_000
        return client, session, journal, clock

    def test_upload_initialisation_500_is_never_blindly_retried(self):
        c, s, j, _ = self.client([response(500)])
        with self.assertRaises(api.Uncertain):
            c.request("POST", "upload/videos", body={}, cost=0, upload_start=True, idempotent=False)
        self.assertEqual(s.request.call_count,1)
        self.assertEqual(j.data["quota"]["upload_starts"],1)

    def test_mutating_transport_loss_is_uncertain(self):
        c,s,_,_ = self.client([requests.Timeout()])
        with self.assertRaises(api.Uncertain):
            c.request("POST","playlistItems",body={},idempotent=False)
        self.assertEqual(s.request.call_count,1)

    def test_read_retries_are_bounded(self):
        c,s,_,clock = self.client([response(503)]*4)
        with self.assertRaises(api.Deferred):
            c.request("GET","videos")
        self.assertEqual(s.request.call_count,4)
        self.assertGreater(sum(clock.waits),10)

    def test_short_rate_limit_waits_server_retry_after(self):
        c,s,_,clock = self.client([response(429,headers={"Retry-After":"7"}),response()])
        c.request("GET","videos")
        self.assertEqual(s.request.call_count,2)
        self.assertGreaterEqual(clock.t,7)

    def test_long_rate_limit_defers(self):
        c,s,_,clock = self.client([response(429,headers={"Retry-After":"3600"})])
        with self.assertRaises(api.Deferred) as exc:
            c.request("GET","videos")
        self.assertEqual(exc.exception.wait_seconds,3600)
        self.assertEqual(s.request.call_count,1)
        self.assertEqual(clock.waits,[])

    def test_403_rate_limit_is_not_treated_as_permanent_auth(self):
        r = response(403,{"error":{"errors":[{"reason":"userRateLimitExceeded"}]}},{"Retry-After":"120"})
        c,_,_,_ = self.client([r])
        with self.assertRaises(api.Deferred) as exc:
            c.request("GET","videos")
        self.assertEqual(exc.exception.code,"RATE_LIMIT")

    def test_google_quota_uses_pacific_reset(self):
        c,_,_,_ = self.client([response(403,{"error":{"errors":[{"reason":"quotaExceeded"}]}})])
        with self.assertRaises(api.Deferred) as exc:
            c.request("GET","videos")
        self.assertEqual(exc.exception.code,"QUOTA_EXCEEDED")
        reset=api.quota_reset(NOW).astimezone(ZoneInfo("America/Los_Angeles"))
        self.assertEqual((reset.hour,reset.minute),(0,2))

    def test_quota_reset_handles_dst(self):
        n=dt.datetime(2026,11,1,7,30,tzinfo=dt.timezone.utc)
        self.assertEqual(iso(api.quota_reset(n)),"2026-11-02T08:02:00Z")

    def test_local_quota_budget_blocks_before_network(self):
        conf=cfg();conf["general_quota_budget_per_day"]=1
        c,s,_,_=self.client([],conf)
        with self.assertRaises(api.Deferred):
            c.request("PUT","videos",cost=50)
        s.request.assert_not_called()

    def test_journal_failure_blocks_before_network(self):
        c,s,j,_=self.client([]);j.fail_on="reserve YouTube quota"
        with self.assertRaises(RuntimeError):
            c.request("GET","videos")
        s.request.assert_not_called()

    def test_permanent_bad_input_never_retries(self):
        c,s,_,_=self.client([response(400,{"error":{"message":"bad title","errors":[{"reason":"invalidTitle"}]}})])
        with self.assertRaises(api.YouTubeError) as e:
            c.request("POST","upload/videos",body={},idempotent=False)
        self.assertEqual(e.exception.code,"invalidTitle")
        self.assertEqual(s.request.call_count,1)

    def test_wrong_channel_stops(self):
        c,_,_,_=self.client([response(body={"items":[{"id":"wrong-channel"}]})])
        with self.assertRaises(api.YouTubeError) as e:
            c.verify_channel()
        self.assertEqual(e.exception.code,"CHANNEL_MISMATCH")

    def test_wrong_upload_host_blocks_bearer_exfiltration(self):
        c,s,_,_=self.client([])
        with self.assertRaises(api.YouTubeError):
            c.request("PUT","https://evil.invalid/upload/youtube/v3/videos?upload_id=x",data=b"video")
        s.request.assert_not_called()

    def test_session_308_is_returned_not_followed(self):
        c,s,_,_=self.client([response(308,headers={"Range":"bytes=0-9"})])
        r=c.request("PUT",SESSION,data=b"",cost=0)
        self.assertEqual(r.status_code,308)
        self.assertFalse(s.request.call_args.kwargs["allow_redirects"])

    def test_revoked_refresh_token_requires_reconnect(self):
        c,s,_,_=self.client([])
        s.post.return_value=response(400,{"error":"invalid_grant"})
        with self.assertRaises(api.YouTubeError) as e:
            c.refresh()
        self.assertEqual(e.exception.code,"AUTH_RECONNECT")
        self.assertEqual(s.post.call_count,1)

    def test_refreshes_expired_access_token(self):
        c,s,_,_=self.client([response(body={"items":[]})]);c.expires=-1
        s.post.return_value=response(body={"access_token":"renewed-test-access","expires_in":3600})
        c.request("GET","videos")
        self.assertEqual(s.request.call_args.kwargs["headers"]["Authorization"],"Bearer renewed-test-access")


class EncryptionAndOAuthTests(unittest.TestCase):
    def test_session_is_encrypted_and_bound_to_media(self):
        i=item();encrypted=secure_state.encrypt_session(SESSION,i,cfg()["channel_id"],KEY)
        self.assertNotIn(SESSION,encrypted)
        self.assertNotIn("upload_id",encrypted)
        self.assertEqual(secure_state.decrypt_session(encrypted,i,cfg()["channel_id"],KEY),SESSION)
        other={**i,"video_id":"different-video"}
        with self.assertRaises(api.YouTubeError):
            secure_state.decrypt_session(encrypted,other,cfg()["channel_id"],KEY)

    def test_wrong_state_key_does_not_restart_upload(self):
        i=item();encrypted=secure_state.encrypt_session(SESSION,i,cfg()["channel_id"],KEY)
        other=base64.urlsafe_b64encode(b"z"*32).decode()
        with self.assertRaises(api.YouTubeError):
            secure_state.decrypt_session(encrypted,i,cfg()["channel_id"],other)

    def test_oauth_uses_pkce_state_and_stable_https_callback(self):
        p,url=oauth_connect.make_flow({"client_id":"test","client_secret":"test"},"https://8765-test.e2b.app",now=100)
        from urllib.parse import parse_qs,urlparse
        q=parse_qs(urlparse(url).query)
        self.assertEqual(q["redirect_uri"],[oauth_connect.CALLBACK])
        self.assertEqual(q["code_challenge_method"],["S256"])
        self.assertEqual(q["access_type"],["offline"])
        oauth_connect.verify_state(p,p["state"],now=200)
        with self.assertRaises(ValueError):oauth_connect.verify_state(p,"wrong",now=200)
        with self.assertRaises(ValueError):oauth_connect.verify_state(p,p["state"],now=2000)

    def test_oauth_origin_rejects_localhost_and_suffix_spoofing(self):
        for origin in ["http://localhost:8765","https://example.e2b.app.evil.invalid","https://evil.invalid","https://user@8765-test.e2b.app"]:
            with self.assertRaises(ValueError):oauth_connect.valid_origin(origin)

    def test_oauth_rejects_service_account_or_desktop_credentials(self):
        with self.assertRaises(ValueError):oauth_connect.parse_client({"installed":{"client_id":"x"}})
        with self.assertRaises(ValueError):oauth_connect.parse_client({"type":"service_account"})

    def test_uploaded_client_cannot_replace_google_token_endpoint(self):
        c=oauth_connect.parse_client({"web":{"client_id":"x.apps.googleusercontent.com","client_secret":"unit-secret","redirect_uris":[oauth_connect.CALLBACK],"token_uri":"https://evil.invalid"}})
        self.assertNotIn("token_uri",c)


class TransferAPI:
    def __init__(self,replies):
        self.cfg=cfg();self.cfg["upload_chunk_bytes"]=262144
        self.replies=list(replies);self.calls=[];self.waits=[]
        self.sleep=self.waits.append;self.jitter=lambda:0

    def request(self,method,url,**kwargs):
        self.calls.append((method,url,kwargs))
        result=self.replies.pop(0)
        if isinstance(result,Exception):raise result
        return result


class ResumableTests(unittest.TestCase):
    def run_upload(self,replies,data=b"v"*(262144+100),existing=None,journal=None):
        i=item(data);j=journal or Journal();r=existing or {"video_id":i["video_id"],"state":"queued"};j.records[i["video_id"]]=r
        client=TransferAPI(replies)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"video.mp4";path.write_bytes(data)
            result=resumable.upload(i,r,path,{"title":"Test","tags":[seo.tracking_tag(i)]},client,j,state_key=KEY,clock=lambda:NOW)
        return result,client,j,r

    def test_private_first_two_chunk_upload(self):
        result,a,j,r=self.run_upload([response(headers={"Location":SESSION}),response(308),response(308,headers={"Range":"bytes=0-262143"}),response(201,{"id":VIDEO_ID})])
        self.assertEqual(result,VIDEO_ID)
        self.assertEqual(a.calls[0][2]["body"]["status"]["privacyStatus"],"private")
        self.assertNotIn("publishAt",a.calls[0][2]["body"]["status"])
        self.assertEqual(a.calls[-1][2]["headers"]["Content-Range"],"bytes 262144-262243/262244")
        self.assertNotIn("session_ciphertext",r)
        self.assertTrue(any("reserve final" in m for m,_ in j.saves))
        self.assertNotIn(SESSION,json.dumps(j.data))

    def test_lost_final_response_probes_same_session_without_new_insert(self):
        result,a,_,r=self.run_upload([response(headers={"Location":SESSION}),response(308),api.Uncertain("timeout"),response(201,{"id":VIDEO_ID})],data=b"small-video")
        self.assertEqual(result,VIDEO_ID)
        self.assertEqual(sum(method=="POST" for method,_,_ in a.calls),1)
        self.assertEqual(a.calls[-1][2]["headers"]["Content-Range"],"bytes */11")

    def test_resume_uses_server_offset_not_local_guess(self):
        data=b"v"*(262144+50);i=item(data)
        record={"video_id":i["video_id"],"state":"uploading","confirmed_bytes":0,"session_ciphertext":secure_state.encrypt_session(SESSION,i,cfg()["channel_id"],KEY)}
        result,a,_,_=self.run_upload([response(308,headers={"Range":"bytes=0-262143"}),response(201,{"id":VIDEO_ID})],data,record)
        self.assertEqual(result,VIDEO_ID)
        self.assertEqual(sum(method=="POST" for method,_,_ in a.calls),0)
        self.assertEqual(a.calls[1][2]["headers"]["Content-Range"],"bytes 262144-262193/262194")

    def test_308_retry_after_defers_before_sending_more_data(self):
        with self.assertRaises(api.Deferred) as e:
            self.run_upload([response(headers={"Location":SESSION}),response(308,headers={"Retry-After":"180"})])
        self.assertEqual(e.exception.wait_seconds,180)

    def test_session_persistence_failure_prevents_any_media_put(self):
        j=Journal();j.fail_on="persist encrypted"
        with self.assertRaises(RuntimeError):
            self.run_upload([response(headers={"Location":SESSION})],journal=j)
        self.assertTrue(j.saves[0][0].startswith("reserve YouTube upload session"))

    def test_final_chunk_reservation_failure_blocks_final_write(self):
        j=Journal();j.fail_on="reserve final"
        with self.assertRaises(RuntimeError):
            self.run_upload([response(headers={"Location":SESSION}),response(308)],data=b"small-video",journal=j)

    def test_bad_upload_range_fails_closed(self):
        for value in ["bytes=10-20","bytes=0-1000","nonsense"]:
            with self.assertRaises(api.YouTubeError):resumable.offset_from(response(308,headers={"Range":value}),100)

    def test_expired_session_never_allocates_another_automatically(self):
        data=b"video";i=item(data)
        record={"video_id":i["video_id"],"state":"uploading","session_ciphertext":secure_state.encrypt_session(SESSION,i,cfg()["channel_id"],KEY)}
        with self.assertRaises(api.YouTubeError) as e:
            self.run_upload([api.YouTubeError("expired","SESSION_EXPIRED")],data,record)
        self.assertEqual(e.exception.code,"SESSION_EXPIRED")


class MetadataTests(unittest.TestCase):
    def test_short_tags_update_preserves_public_copy_and_excludes_status(self):
        video={"id":VIDEO_ID,"snippet":{"title":"Owner title","description":"Owner description","categoryId":"28","defaultLanguage":"en","tags":["owner tag"]},"status":{"privacyStatus":"public"}}
        merged=seo.merge_tags_preserving_copy(video,["AI tools"])
        self.assertEqual(merged["snippet"]["title"],"Owner title")
        self.assertEqual(merged["snippet"]["description"],"Owner description")
        self.assertEqual(merged["snippet"]["tags"],["owner tag","AI tools"])
        self.assertNotIn("status",merged)

    def test_uncertain_membership_is_reconciled_not_duplicated(self):
        client=Mock();client.pages.return_value=[{"id":"existing-item"}]
        j=Journal();j.data["memberships"]["p:"+VIDEO_ID]={"state":"uncertain"}
        metadata.ensure_membership(client,j,"p",VIDEO_ID)
        client.json.assert_not_called()
        self.assertEqual(j.data["memberships"]["p:"+VIDEO_ID]["state"],"done")

    def test_missing_uncertain_membership_is_held(self):
        client=Mock();client.pages.return_value=[]
        j=Journal();j.data["memberships"]["p:"+VIDEO_ID]={"state":"uncertain"}
        with self.assertRaises(api.Uncertain):metadata.ensure_membership(client,j,"p",VIDEO_ID)
        client.json.assert_not_called()

    def test_playlist_create_timeout_does_not_create_again(self):
        client=Mock();client.cfg=cfg();client.playlist_cache={};client.pages.return_value=[]
        client.json.side_effect=api.Uncertain("timeout")
        j=Journal()
        with self.assertRaises(api.Uncertain):metadata.ensure_playlist(client,j,"tool")
        with self.assertRaises(api.Uncertain):metadata.ensure_playlist(client,j,"tool")
        self.assertEqual(client.json.call_count,1)

    def test_description_has_chapters_and_sources_without_keyword_dump(self):
        b=brief();out=seo.validate(b,"long","hypeless-ref-test")
        self.assertIn("0:00 The result",out["description"])
        self.assertIn(b["sources"][0],out["description"])
        self.assertIn("hypeless-ref-test",out["tags"])
        self.assertNotIn("hypeless-ref-test",out["description"])
        self.assertNotIn("#Shorts",out["description"])

    def test_long_must_not_claim_to_be_shorts(self):
        b=brief();b["seo"]["youtube"]["hashtags"].append("#Shorts")
        with self.assertRaises(ValueError):seo.validate(b,"long")

    def test_unicode_description_budget_is_utf8_not_character_count(self):
        b=brief();b["seo"]["youtube"]["description"]="Example AI "+"🟡"*1300
        with self.assertRaises(ValueError):seo.validate(b,"long")

    def test_tags_count_quotes_and_commas(self):
        self.assertEqual(seo.tag_cost(["AI tools","repo"]),8+2+4+1)
        with self.assertRaises(ValueError):
            v={"id":VIDEO_ID,"snippet":{"title":"T","categoryId":"28","tags":["x"*495]}}
            seo.merge_tags_preserving_copy(v,["extra tag"])

    def test_malformed_chapters_are_blocked(self):
        for starts in ([3,60,300],[0,3,300],[0,60,479]):
            b=brief()
            for c,t in zip(b["chapters"],starts):c["start_seconds"]=t
            with self.assertRaises(ValueError):seo.validate(b,"long")

    def test_used_video_fields_exist_in_current_google_schema(self):
        schema=load_json(ROOT/"research/publishing/youtube-discovery-2026-10-10.json")["schemas"]
        self.assertTrue(set(seo.validate(brief())).issubset(schema["VideoSnippet"]["properties"]))
        for name in ["privacyStatus","publishAt","selfDeclaredMadeForKids","containsSyntheticMedia"]:
            self.assertIn(name,schema["VideoStatus"]["properties"])


class PublicationTests(unittest.TestCase):
    def make(self,due=NOW+dt.timedelta(hours=5),custom=True):
        i=item();snippet=seo.validate(brief(),"long",seo.tracking_tag(i))
        record={"video_id":i["video_id"],"youtube_id":VIDEO_ID,"state":"uploaded_private","publish_at":iso(due)}
        video={"id":VIDEO_ID,"etag":"version", "snippet":{**snippet,"channelId":cfg()["channel_id"]},"status":{"privacyStatus":"private","uploadStatus":"processed"},"contentDetails":{"hasCustomThumbnail":custom}}
        client=Mock();client.cfg=cfg();j=Journal();j.records[i["video_id"]]=record
        media={"snippet":snippet,"thumbnail_path":"not-read-in-this-mocked-test"}
        return i,record,video,client,j,media

    def test_missing_custom_thumbnail_prevents_public_schedule(self):
        i,r,v,a,j,m=self.make(custom=False)
        with patch.object(runner,"get_video",return_value=v),patch.object(runner,"set_thumbnail"),patch.object(runner,"playlists_for"):
            with self.assertRaises(api.Deferred) as e:runner.finish_private(i,r,m,a,j,clock=lambda:NOW)
        self.assertEqual(e.exception.code,"THUMBNAIL_PENDING")
        a.json.assert_not_called()

    def test_stale_schedule_never_turns_into_publish_now(self):
        i,r,v,a,j,m=self.make(due=NOW-dt.timedelta(minutes=1))
        with patch.object(runner,"get_video",return_value=v),patch.object(runner,"set_thumbnail"),patch.object(runner,"playlists_for"):
            with self.assertRaises(api.Deferred) as e:runner.finish_private(i,r,m,a,j,clock=lambda:NOW)
        self.assertEqual(e.exception.code,"STALE_SLOT")
        a.json.assert_not_called()

    def test_success_arms_future_private_publish_at_not_public_now(self):
        i,r,v,a,j,m=self.make()
        a.json.return_value={"status":{"privacyStatus":"private","publishAt":r["publish_at"]}}
        with patch.object(runner,"get_video",return_value=v),patch.object(runner,"set_thumbnail"),patch.object(runner,"playlists_for"):
            runner.finish_private(i,r,m,a,j,clock=lambda:NOW)
        status=a.json.call_args.kwargs["body"]["status"]
        self.assertEqual(status["privacyStatus"],"private")
        self.assertEqual(r["state"],"scheduled")
        self.assertNotEqual(r["state"],"sent")

    def test_private_pilot_does_not_arm_a_public_schedule(self):
        i,r,v,a,j,m=self.make()
        with patch.object(runner,"get_video",return_value=v),patch.object(runner,"set_thumbnail"),patch.object(runner,"playlists_for"):
            runner.finish_private(i,r,m,a,j,private_only=True,clock=lambda:NOW)
        self.assertEqual(r["state"],"private_ready")
        a.json.assert_not_called()

    def test_only_public_receipt_is_sent(self):
        i,r,v,a,j,m=self.make()
        v["status"]["privacyStatus"]="public";v["snippet"]["publishedAt"]=iso(NOW)
        self.assertTrue(runner.verify_publication(r,v,j,clock=lambda:NOW))
        self.assertEqual(r["state"],"sent")
        self.assertIn(VIDEO_ID,r["external_url"])

    def test_late_private_video_is_an_error_not_a_second_upload(self):
        _,r,v,_,j,_=self.make()
        v["status"]["publishAt"]=iso(NOW-dt.timedelta(hours=1))
        runner.verify_publication(r,v,j,clock=lambda:NOW)
        self.assertEqual(r["state"],"publication_failed")

    def test_external_copy_edit_is_not_overwritten(self):
        i,r,v,a,j,m=self.make();v["snippet"]=copy.deepcopy(v["snippet"]);v["snippet"]["title"]="Owner changed title"
        with patch.object(runner,"get_video",return_value=v):
            with self.assertRaises(api.YouTubeError):runner.finish_private(i,r,m,a,j,clock=lambda:NOW)
        a.json.assert_not_called()


class CalendarAndThumbnailTests(unittest.TestCase):
    def test_new_york_daylight_saving_not_fixed_est(self):
        summer=at_local(dt.date(2026,10,10),"13:00","America/New_York")
        winter=at_local(dt.date(2026,11,10),"13:00","America/New_York")
        self.assertEqual(summer.hour,17)
        self.assertEqual(winter.hour,18)
        self.assertIsNone(at_local(dt.date(2026,3,8),"02:30","America/New_York"))

    def test_repeated_clock_hour_is_emitted_once(self):
        self.assertEqual(iso(at_local(dt.date(2026,11,1),"01:30","America/New_York")),"2026-11-01T05:30:00Z")

    def test_fourth_fifth_slots_are_opt_in(self):
        p=load_json(ROOT/"config/publishing.json")["schedule"]["profiles"]["youtube"]
        for target in (3,4,5):self.assertEqual(len(clocks_for(p,dt.date(2026,10,12),target)),target)

    def test_rolling_notifications_include_already_scheduled_future_posts(self):
        t=NOW
        self.assertTrue(can_notify(t,[t-dt.timedelta(hours=10)],2))
        self.assertFalse(can_notify(t,[t-dt.timedelta(hours=10),t+dt.timedelta(hours=1)],2))

    def test_long_queue_has_separate_lanes_and_weekly_cap(self):
        items=[]
        for n in range(12):
            i=item();i.update(video_id=f"long-{n}",category=["repo","news","tool"][n%3],priority=n)
            items.append(i)
        rows,_=schedule.plan(items,{}, {},cfg(),NOW)
        counts={}
        for r in rows:
            local=dt.datetime.fromisoformat(r["publish_local"])
            expected={"repo":1,"news":4,"tool":6}[r["category"]]
            self.assertEqual(local.weekday(),expected)
            k=local.strftime("%G-W%V");counts[k]=counts.get(k,0)+1
        self.assertTrue(rows)
        self.assertTrue(all(n<=3 for n in counts.values()))

    def test_long_never_collides_with_known_short(self):
        i=item();rows,_=schedule.plan([i],{}, {},cfg(),NOW)
        first=rows[0]
        shorts={"x":{"platform":"youtube","state":"scheduled","due_at":first["publish_at"]}}
        rows,_=schedule.plan([i],{},shorts,cfg(),NOW)
        self.assertFalse(any(r["publish_at"]==first["publish_at"] for r in rows))

    def test_actual_250px_thumbnail_preview_is_generated(self):
        with tempfile.TemporaryDirectory() as tmp:
            report=thumbnail.build({"headline":["TESTED","NOT HYPED"]},tmp)
            self.assertTrue(all(report["checks"].values()))
            with Image.open(Path(tmp)/"thumbnail-250.jpg") as preview:
                self.assertEqual(preview.width,250)
            self.assertGreaterEqual(min(r["height_at_250"] for r in report["text"]),16)
            self.assertFalse(report["visual_reviewed"])

    def test_thumbnail_rejects_unreadable_headline(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):thumbnail.build({"headline":["THIS IS FAR TOO MANY EXTRA WORDS"]},tmp)
            with self.assertRaises(ValueError):thumbnail.build({"headline":["SUPEREXTRALONGUNREADABLEHEADLINE"]},tmp)

    def test_manifest_refuses_wrong_voice_or_vertical_video(self):
        i=item()
        m={"id":i["video_id"],"format":"long","qa":{"checks":{"approved_voice":True}},
           "stages":{"voice":{"engine":"chatterbox exag0.7 cfg0.4 ref michael-ref.wav, flow"}},
           "video":{"sha256":i["asset_digest"],"width":1920,"height":1080,"duration_seconds":480,"video_codec":"h264","audio_codec":"aac"}}
        contracts.validate_manifest(m,i)
        m["video"].update(width=1080,height=1920)
        with self.assertRaises(ValueError):contracts.validate_manifest(m,i)
        m["video"].update(width=1920,height=1080);m["stages"]["voice"]["engine"]="kokoro"
        with self.assertRaises(ValueError):contracts.validate_manifest(m,i)


if __name__ == "__main__":
    unittest.main()
