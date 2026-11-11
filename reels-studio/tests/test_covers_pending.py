"""The post.yml -> youtube.yml cover cascade must only fire when there is real work."""
import unittest

from tools.youtube.covers_pending import external_id, pending_covers


def item(video_id="news-demo-01", digest="sha256:aa"):
    return {"video_id": video_id, "cover_sha256": digest, "cover_reviewed_at": "2026-10-12T07:50:51Z"}


def sent(video_id="news-demo-01", url="https://www.youtube.com/watch?v=AbCdEfGhIjK"):
    return {video_id + ":youtube": {"video_id": video_id, "platform": "youtube", "state": "sent", "external_url": url}}


class PendingCoversTests(unittest.TestCase):
    def test_sent_approved_unconfirmed_needs_the_cascade(self):
        rows = pending_covers(sent(), [item()], {})
        self.assertEqual([r["video_id"] for r in rows], ["news-demo-01"])
        self.assertEqual(rows[0]["youtube_id"], "AbCdEfGhIjK")

    def test_confirmed_row_closes_the_cascade(self):
        enrichment = {"AbCdEfGhIjK": {"thumbnail_confirmed": True, "thumbnail_digest": "sha256:aa"}}
        self.assertEqual(pending_covers(sent(), [item()], enrichment), [])

    def test_newer_approval_reopens_the_cascade(self):
        enrichment = {"AbCdEfGhIjK": {"thumbnail_confirmed": True, "thumbnail_digest": "sha256:old"}}
        self.assertEqual(len(pending_covers(sent(), [item()], enrichment)), 1)

    def test_blocked_row_never_triggers_more_runs(self):
        enrichment = {"AbCdEfGhIjK": {"thumbnail_blocked": True}}
        self.assertEqual(pending_covers(sent(), [item()], enrichment), [])

    def test_scheduled_unapproved_and_unresolvable_rows_are_ignored(self):
        scheduled = sent()
        scheduled["news-demo-01:youtube"]["state"] = "scheduled"
        self.assertEqual(pending_covers(scheduled, [item()], {}), [])
        self.assertEqual(pending_covers(sent(), [{"video_id": "news-demo-01"}], {}), [])
        self.assertEqual(pending_covers(sent(url=None), [item()], {}), [])
        self.assertEqual(pending_covers(sent(), [item("other-video-01")], {}), [])

    def test_external_id_reads_every_url_shape_reconcile_writes(self):
        self.assertEqual(external_id("https://www.youtube.com/watch?v=AbCdEfGhIjK"), "AbCdEfGhIjK")
        self.assertEqual(external_id("https://youtu.be/AbCdEfGhIjK?t=1"), "AbCdEfGhIjK")
        self.assertEqual(external_id("https://www.youtube.com/shorts/AbCdEfGhIjK"), "AbCdEfGhIjK")
        self.assertIsNone(external_id(""))


if __name__ == "__main__":
    unittest.main()
