"""Browser address labels must fit the fixed bar without replacing source URLs."""
import unittest
from pathlib import Path
from unittest.mock import patch

from templates._spotlight import spotcore


class SpotlightUrlLabelTests(unittest.TestCase):
    def test_short_repo_address_stays_readable(self):
        url = "https://github.com/QwenLM/Qwen-Image-2.1"
        self.assertEqual(spotcore.url_display_label(url), "github.com/QwenLM/Qwen-Image-2.1")

    def test_long_article_url_keeps_host_and_target_slug(self):
        url = "https://blog.google/innovation-and-ai/technology/developers-tools/embeddinggemma-2/"
        self.assertEqual(spotcore.url_display_label(url), "blog.google/…/embeddinggemma-2")
        self.assertLessEqual(len(spotcore.url_display_label(url)), 54)

    def test_scene_keeps_source_url_separate_from_display_label(self):
        url = "blog.google/innovation-and-ai/technology/developers-tools/embeddinggemma-2/"
        scene = {"id": "name", "type": "page", "url": url}
        out = spotcore.scenes({"scenes": [scene]})[0]
        self.assertEqual(out["url"], url)
        self.assertEqual(out["display_url"], "blog.google/…/embeddinggemma-2")

    def test_capture_fallback_url_is_compacted_too(self):
        url = "https://blog.google/innovation-and-ai/technology/developers-tools/embeddinggemma-2/"
        with patch.object(spotcore, "capture", return_value=(None, {"url": url, "facts": {}, "regions_css": {}})):
            data = spotcore.data({"scenes": [{"id": "page", "type": "page"}]}, {}, 1.0, {},
                                 {"cut": "glide", "flavor": "tool"})
        self.assertEqual(data["url"], url)
        self.assertEqual(data["display_url"], "blog.google/…/embeddinggemma-2")

    def test_all_browser_scene_types_use_the_compact_url(self):
        js = (Path(__file__).resolve().parents[1] / "templates" / "_spotlight" / "scene.js").read_text()
        self.assertEqual(js.count("url: s.display_url || s.url || X.display_url || X.url"), 4)


if __name__ == "__main__":
    unittest.main()
