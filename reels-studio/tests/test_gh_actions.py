"""URL normalisation for tools/gh_actions.py.

Regression for the 2026-10-12 session bug: api() prefixed /repos/... with the repo
base again, so legit absolute repo paths returned 404 and looked like a bad token.
"""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from tools import gh_actions  # noqa: E402


class UrlTests(unittest.TestCase):
    def test_repo_relative_path_gets_repo_prefix(self):
        self.assertEqual(gh_actions._url("/actions/runs/1"),
                         "https://api.github.com/repos/zainkhan122/yt-tts/actions/runs/1")

    def test_absolute_repo_path_is_not_double_prefixed(self):
        self.assertEqual(gh_actions._url("/repos/zainkhan122/yt-tts/releases"),
                         "https://api.github.com/repos/zainkhan122/yt-tts/releases")

    def test_full_url_passes_through(self):
        self.assertEqual(gh_actions._url("https://example.com/x"), "https://example.com/x")


if __name__ == "__main__":
    unittest.main()
