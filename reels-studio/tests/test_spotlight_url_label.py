"""Browser address labels must fit the fixed bar without replacing source URLs."""
import unittest

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


if __name__ == "__main__":
    unittest.main()
