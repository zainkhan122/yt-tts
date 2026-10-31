"""URL normalisation for tools/gh_actions.py.

Regression for the 2026-10-12 session bug: api() prefixed /repos/... with the repo
base again, so legit absolute repo paths returned 404 and looked like a bad token.
"""
import pathlib
import sys
import unittest
from unittest.mock import patch

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

    def test_delete_artifact_uses_discovered_artifact_id(self):
        from unittest.mock import patch
        with patch.object(gh_actions, "api", side_effect=[
            (200, {"artifacts": [{"id": 731, "name": "render-demo"}]}),
            (204, {})
        ]) as api, patch("builtins.print"):
            gh_actions.delete_artifact("42", "render-demo")
        api.assert_any_call("DELETE", "/actions/artifacts/731")


class ReleaseLinkTests(unittest.TestCase):
    def test_returns_only_a_published_release_url(self):
        with patch.object(gh_actions, "api", return_value=(200, {
            "draft": False, "html_url": "https://github.com/example/release"
        })) as api:
            self.assertEqual(gh_actions.release_url("renders-2026-10-14"),
                             "https://github.com/example/release")
        self.assertIn("/releases/tags/renders-2026-10-14", api.call_args.args[1])

    def test_draft_or_missing_release_is_not_reported_as_published(self):
        for status, data in ((200, {"draft": True, "html_url": "https://example.invalid/draft"}),
                             (404, {"message": "Not Found"})):
            with self.subTest(status=status), patch.object(gh_actions, "api", return_value=(status, data)):
                with self.assertRaisesRegex(SystemExit, "not found"):
                    gh_actions.release_url("renders-2026-10-14")


if __name__ == "__main__":
    unittest.main()
