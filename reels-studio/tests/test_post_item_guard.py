"""Regression: one blocked queue item must never abort the rest of the run (Track B guard).

Before the guard, a blocked item could escape as an unhandled error and the preflight handler
reported the whole run as blocked, hiding the targeted shorts (dry run 39571441269).
"""
import copy
import datetime as dt
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.post import cadence, planner  # noqa: E402
from tools.post.common import config, load_json  # noqa: E402


def _stub_channels(cfg):
    out = []
    for plat, exp in cfg["buffer"]["channels"].items():
        out.append({"id": exp["buffer_id"], "serviceId": exp["service_id"], "service": plat, "name": plat,
                    "isDisconnected": False, "isLocked": False, "isQueuePaused": False, "metadata": {}})
    return out


class ItemGuard(unittest.TestCase):
    def setUp(self):
        self.cfg = config()
        self.queue = load_json(ROOT / "queue" / "publish.json")["items"]

    def test_missing_brief_is_a_named_block_not_a_crash(self):
        item = dict(self.queue[0], video_id="no-such-brief-zz", platforms=["youtube"])
        with self.assertRaises(ValueError) as cm:
            planner.copy_for(item, "youtube", self.cfg)
        self.assertIn("no-such-brief-zz", str(cm.exception))

    def test_fingerprint_mismatch_is_a_named_block(self):
        item = next(i for i in self.queue if i["video_id"] == "tool-scrawl-01")
        bad = dict(item, brief_sha256="0" * 64)
        with self.assertRaises(ValueError) as cm:
            planner.payload_for(bad, "youtube", dt.datetime(2026, 10, 22, 17, tzinfo=dt.timezone.utc), self.cfg)
        self.assertIn("tool-scrawl-01", str(cm.exception))

    def test_planner_reports_blocked_item_and_keeps_going(self):
        queue = copy.deepcopy(self.queue)
        queue.append({"video_id": "no-such-brief-zz", "platforms": ["youtube"], "category": "tool",
                      "priority": 1, "approval": "approved", "media_path": "media/1/none.mp4",
                      "asset_id": 1, "asset_size": 1, "asset_digest": None, "brief_sha256": None})
        now = dt.datetime.now(dt.timezone.utc)
        # Must not raise. The blocked item shows up as a note, the others are still considered.
        rows, notes = cadence.plan(queue, {}, _stub_channels(self.cfg), [], self.cfg, now,
                                   preview=True, pilot=False, long_records={})
        self.assertTrue(any("no-such-brief-zz" in n and "blocked" in n for n in notes), notes)
        self.assertFalse(any(r["video_id"] == "no-such-brief-zz" for r in rows))


if __name__ == "__main__":
    unittest.main()
