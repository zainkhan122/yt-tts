"""Shot plan rules (v3): real media on screen, sourced data, no endless scrolling, no invented numbers."""
import copy
import tempfile
import unittest
from pathlib import Path

from studio import shotplan as S

SRC = "https://github.com/example/tool"
DATE = "2026-10-21"


def beat(t0, t1, kind="capture", **kw):
    b = {"t0": t0, "t1": t1, "kind": kind}
    if kind == "capture":
        b.setdefault("asset", "capture:hero.jpg")
        b.setdefault("motion", "push-in")
    if kind == "video":
        b.setdefault("asset", "capture:demo.mp4")
    if kind == "chart":
        b.setdefault("data", {"source": SRC, "retrieved_at": DATE, "series": "stars", "values": [10, 20, 35]})
    if kind == "stat":
        b.setdefault("value", "596"); b.setdefault("label", "GitHub stars"); b.setdefault("source", SRC); b.setdefault("retrieved_at", DATE)
    if kind == "sticker":
        b.setdefault("asset", "sticker:key.svg"); b.setdefault("license", "owner-made")
    if kind == "callout":
        b.setdefault("on", "capture:hero.jpg"); b.setdefault("text", "Option Shift S")
    if kind == "text":
        b.setdefault("text", "Show the bug")
    b.update(kw)
    return b


def plan(beats, duration=None):
    total = beats[-1]["t1"] if beats else 0
    return {"id": "t-plan", "duration_s": duration if duration is not None else total, "beats": beats}


def codes(findings, level="error"):
    return sorted({f.code for f in findings if f.level == level})


def good():
    # 0-3 hero capture, 3-6 video, 6-8.5 stat, 8.5-11 callout on capture, 11-14 chart, 14-16 text, 16-19 capture push, 19-21 capture pan (sticker would not count as real)
    return plan([
        beat(0, 3, "capture", motion="push-in"),
        beat(3, 6, "video"),
        beat(6, 8.5, "stat"),
        beat(8.5, 11, "callout"),
        beat(11, 14, "chart"),
        beat(14, 16, "text"),
        beat(16, 19, "capture", motion="pan"),
        beat(19, 21, "capture", motion="push-in"),
    ])


class Structure(unittest.TestCase):
    def test_good_plan_passes(self):
        self.assertEqual(S.errors(S.check_plan(good())), [])

    def test_gap_is_error(self):
        p = good()
        p["beats"][2]["t0"] = 6.5
        self.assertIn("SP001", codes(S.check_plan(p)))

    def test_duration_mismatch_is_error(self):
        p = good()
        p["duration_s"] = 30
        self.assertIn("SP001", codes(S.check_plan(p)))

    def test_beat_length_limits(self):
        p = plan([beat(0, 0.5, "capture"), beat(0.5, 20, "video")])
        self.assertIn("SP002", codes(S.check_plan(p)))

    def test_unknown_kind(self):
        p = good()
        p["beats"][1]["kind"] = "fancy"
        self.assertIn("SP015", codes(S.check_plan(p)))

    def test_bad_input_shapes(self):
        self.assertIn("SP000", codes(S.check_plan({"id": "x", "duration_s": 0, "beats": []})))
        self.assertIn("SP000", codes(S.check_plan({"id": "x", "duration_s": 5, "beats": []})))


class Variety(unittest.TestCase):
    def test_real_media_share(self):
        p = plan([beat(0, 2, "capture"), beat(2, 4, "text"), beat(4, 6, "text"), beat(6, 8, "stat")])
        self.assertIn("SP003", codes(S.check_plan(p)))

    def test_text_share_cap(self):
        p = plan([beat(0, 2, "capture"), beat(2, 4, "video"), beat(4, 6, "stat"), beat(6, 8.5, "text"),
                  beat(8.5, 10.5, "capture"), beat(10.5, 12.5, "video"), beat(12.5, 13.5, "text")])
        self.assertIn("SP005", codes(S.check_plan(p)))  # 3.5 s of 13.5 s = 26%, above the 20% cap
        ok = plan([beat(0, 2, "capture"), beat(2, 4, "video"), beat(4, 6, "stat"), beat(6, 7, "text"),
                   beat(7, 9, "capture"), beat(9, 11, "video"), beat(11, 12, "text"), beat(12, 14, "capture")])
        self.assertNotIn("SP005", codes(S.check_plan(ok)))  # 2 s of 14 s = 14%

    def test_no_two_text_cards_in_a_row(self):
        p = plan([beat(0, 2, "capture"), beat(2, 3, "text"), beat(3, 4, "text"), beat(4, 6, "video")])
        self.assertIn("SP005", codes(S.check_plan(p)))

    def test_same_kind_run_limit(self):
        p = plan([beat(0, 1.5, "capture", motion="push-in"), beat(1.5, 3, "capture", motion="pan"),
                  beat(3, 4.5, "capture", motion="push-in"), beat(4.5, 6, "video")])
        self.assertIn("SP004", codes(S.check_plan(p)))

    def test_first_beat_must_be_real_or_sourced(self):
        p = plan([beat(0, 2, "text"), beat(2, 4, "capture"), beat(4, 6, "video")])
        self.assertIn("SP006", codes(S.check_plan(p)))


class Scrolling(unittest.TestCase):
    def test_long_scroll_is_rejected(self):
        p = plan([beat(0, 3, "capture", motion="scroll"), beat(3, 6, "capture", motion="scroll"), beat(6, 8, "video")])
        self.assertIn("SP011", codes(S.check_plan(p)))

    def test_scroll_then_change_of_view_is_fine(self):
        p = plan([beat(0, 2, "capture", motion="scroll"), beat(2, 4, "video"), beat(4, 6, "capture", motion="scroll")])
        self.assertNotIn("SP011", codes(S.check_plan(p)))


class Sourcing(unittest.TestCase):
    def test_chart_needs_source_date_and_values(self):
        for bad in ({"source": "http://x.io", "retrieved_at": DATE, "values": [1, 2, 3]},
                    {"source": SRC, "retrieved_at": "yesterday", "values": [1, 2, 3]},
                    {"source": SRC, "retrieved_at": DATE, "values": [1, 2]}):
            p = plan([beat(0, 2, "capture"), beat(2, 4, "chart", data=bad), beat(4, 6, "video")])
            self.assertIn("SP007", codes(S.check_plan(p)), bad)

    def test_stat_needs_source_and_date(self):
        p = plan([beat(0, 2, "capture"), beat(2, 4, "stat", source=""), beat(4, 6, "video")])
        self.assertIn("SP008", codes(S.check_plan(p)))

    def test_sticker_needs_licence(self):
        p = plan([beat(0, 2, "capture"), beat(2, 4, "sticker", license=""), beat(4, 6, "video")])
        self.assertIn("SP009", codes(S.check_plan(p)))

    def test_asset_must_be_capture_owner_test_or_https(self):
        p = plan([beat(0, 2, "capture", asset="/tmp/x.jpg"), beat(2, 4, "video"), beat(4, 6, "stat")])
        self.assertIn("SP012", codes(S.check_plan(p)))

    def test_capture_must_exist_in_pack(self):
        with tempfile.TemporaryDirectory() as d:
            p = good()
            self.assertIn("SP012", codes(S.check_plan(p, captures_dir=Path(d))))
            (Path(d) / "hero.jpg").write_bytes(b"x")
            (Path(d) / "demo.mp4").write_bytes(b"x")
            self.assertEqual(S.errors(S.check_plan(p, captures_dir=Path(d))), [])

    def test_callout_must_point_at_used_media(self):
        p = good()
        p["beats"][3]["on"] = "capture:other.jpg"
        self.assertIn("SP010", codes(S.check_plan(p)))

    def test_callout_word_limit(self):
        p = good()
        p["beats"][3]["text"] = "one two three four five"
        self.assertIn("SP014", codes(S.check_plan(p)))


class Claims(unittest.TestCase):
    def test_every_claim_must_be_shown(self):
        p = good()
        p["beats"][0]["claim"] = "c1"
        findings = S.check_plan(p, claims={"c1", "c2"})
        self.assertIn("SP013", codes(findings))
        self.assertTrue(any("c2" in f.message for f in findings))

    def test_unknown_claim_is_rejected(self):
        p = good()
        p["beats"][0]["claim"] = "nope"
        self.assertIn("SP013", codes(S.check_plan(p, claims={"c1"})))


class Warnings(unittest.TestCase):
    def test_slow_pacing_is_only_a_warning(self):
        p = plan([beat(0, 5, "capture", motion="static"), beat(5, 10, "video")])
        findings = S.check_plan(p)
        self.assertEqual(S.errors(findings), [])
        self.assertIn("SP020", codes(findings, level="warning"))


if __name__ == "__main__":
    unittest.main()
