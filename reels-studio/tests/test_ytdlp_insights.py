"""yt-dlp reference insights: channel list from the registry, metadata parsing, summary. No network."""
import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.reference import ytdlp_insights as Y


def fake_runner(lines):
    def run(url, n):
        return "\n".join(json.dumps(x) for x in lines)
    return run


VIDEOS = [
    {"id": "a", "title": "Short one", "view_count": 1000, "like_count": 50, "comment_count": 5, "duration": 40, "upload_date": "20261030", "webpage_url": "https://www.youtube.com/shorts/a"},
    {"id": "b", "title": "Long one", "view_count": 9000, "like_count": 300, "comment_count": 20, "duration": 600, "upload_date": "20261029", "webpage_url": "https://www.youtube.com/watch?v=b"},
    {"id": "c", "title": "No counts", "duration": 30},
]


class Registry(unittest.TestCase):
    def test_only_https_youtube_rows_are_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "sources.csv"
            with src.open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["type", "handle", "url"])
                w.writerow(["youtube", "Chan", "https://www.youtube.com/@Chan"])
                w.writerow(["youtube", "Bad", "http://example.com"])
                w.writerow(["web", "site", "https://example.com"])
            self.assertEqual(Y.reference_channels(src), [{"handle": "Chan", "url": "https://www.youtube.com/@Chan"}])


class Summary(unittest.TestCase):
    def test_parses_and_summarises(self):
        vids = Y.fetch_channel("https://www.youtube.com/@x", 10, runner=fake_runner(VIDEOS))
        self.assertEqual(len(vids), 3)
        s = Y.summarise(vids)
        self.assertEqual(s["videos"], 3)
        self.assertEqual(s["shorts"], 2)  # 40 s and 30 s
        self.assertEqual(s["long"], 1)
        self.assertEqual(s["median_views"], 5000)  # median of 1000 and 9000
        self.assertEqual(s["top"][0]["title"], "Long one")

    def test_build_records_a_failing_channel_and_keeps_going(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "sources.csv"
            with src.open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["type", "handle", "url"])
                w.writerow(["youtube", "Good", "https://www.youtube.com/@Good"])
                w.writerow(["youtube", "Broken", "https://www.youtube.com/@Broken"])

            def runner(url, n):
                if "Broken" in url:
                    raise RuntimeError("channel unavailable")
                return fake_runner(VIDEOS)(url, n)
            report = Y.build(10, runner=runner, sources=src)
        by = {c["handle"]: c for c in report["channels"]}
        self.assertIn("videos", by["Good"])
        self.assertIn("error", by["Broken"])


if __name__ == "__main__":
    unittest.main()
