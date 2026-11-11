"""Tests for audio_analyze and reference_analyzer tools."""
import json
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent


class AudioAnalyzeTests(unittest.TestCase):
    def test_ffmpeg_exe_resolves(self):
        import sys
        sys.path.insert(0, str(ROOT / "tools"))
        import audio_analyze as aa
        exe = aa._ffmpeg_exe()
        self.assertTrue(len(exe) > 0)
        self.assertTrue(Path(exe).exists())

    def test_compute_metrics_no_words_with_waveform(self):
        import sys
        sys.path.insert(0, str(ROOT / "tools"))
        import audio_analyze as aa
        # With no words but a valid audio path, waveform stats should still work
        result = aa.compute_metrics([], 0, "", None)
        # Should not crash; may have note about no whisper
        self.assertIsInstance(result, dict)

    def test_performance_bonus_buckets(self):
        import sys
        sys.path.insert(0, str(ROOT / "tools"))
        import audio_analyze as aa
        # Test the metrics computation logic with mock data
        words = [
            {"word": "hello", "start": 0.0, "end": 0.3},
            {"word": "world", "start": 0.4, "end": 0.7},
            {"word": "this", "start": 0.8, "end": 1.1},
            {"word": "is", "start": 1.2, "end": 1.3},
            {"word": "a", "start": 1.4, "end": 1.5},
            {"word": "test", "start": 1.6, "end": 2.0},
        ]
        result = aa.compute_metrics(words, 3.0, "hello world this is a test", None)
        self.assertIn("wpm", result)
        self.assertGreater(result["wpm"], 0)


class ReferenceAnalyzerTests(unittest.TestCase):
    def test_yt_dlp_metadata_format(self):
        """Test that yt_dlp_metadata returns expected keys (mocked)."""
        import sys
        sys.path.insert(0, str(ROOT / "tools"))
        import reference_analyzer as ra
        fake_json = json.dumps({
            "title": "Test Video",
            "description": "A test description",
            "uploader": "Test Channel",
            "duration": 30,
            "view_count": 100,
            "like_count": 10,
            "comment_count": 5,
            "tags": ["test", "shorts"],
            "webpage_url": "https://youtube.com/watch?v=test",
            "id": "test123",
        })
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout=fake_json, stderr="")
            result = ra.yt_dlp_metadata("https://youtube.com/watch?v=test")
        self.assertEqual(result["title"], "Test Video")
        self.assertEqual(result["view_count"], 100)
        self.assertEqual(result["id"], "test123")

    def test_lessons_report_generates(self):
        import sys
        sys.path.insert(0, str(ROOT / "tools"))
        import reference_analyzer as ra
        data = {
            "metadata": {
                "title": "Test Video",
                "url": "https://youtube.com/watch?v=test",
                "uploader": "Test Channel",
                "duration_s": 30,
                "view_count": 100,
                "like_count": 10,
                "comment_count": 5,
                "description": "Line 1\nLine 2\n#Shorts #Test",
                "tags": ["test", "shorts"],
            },
            "audio": {"wpm": 150, "silence_pct": 10.0},
            "scene_changes": [5.0, 15.0, 25.0],
            "scene_count": 3,
        }
        report = ra.lessons_report(data)
        self.assertIn("Test Video", report)
        self.assertIn("WPM: 150", report)
        self.assertIn("Scene changes: 3", report)


if __name__ == "__main__":
    unittest.main()
