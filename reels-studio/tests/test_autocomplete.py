"""Autocomplete demand probe: parsing, presence/breadth, and honest failure recording. No network."""
import io
import json
import unittest

from tools.demand import autocomplete as A


class FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def opener_for(suggestions_by_source):
    def opener(req, timeout=None):
        url = req.full_url
        source = "youtube" if "ds=yt" in url else "web"
        return FakeResp(json.dumps(["q", suggestions_by_source[source]]).encode())
    return opener


class Autocomplete(unittest.TestCase):
    def test_presence_and_breadth(self):
        op = opener_for({"youtube": ["free deepseek", "free deepseek api", "free deepseek proxy"],
                         "web": ["free deepseek api"]})
        r = A.probe_term("free deepseek", opener=op)
        yt = r["sources"]["youtube"]
        self.assertTrue(yt["term_listed"])
        self.assertEqual(yt["breadth"], 3)
        self.assertFalse(r["sources"]["web"]["term_listed"])

    def test_failure_is_recorded_not_silent(self):
        def broken(req, timeout=None):
            raise OSError("no route")
        r = A.probe_term("anything", opener=broken)
        self.assertIn("error", r["sources"]["youtube"])

    def test_report_states_its_limit(self):
        op = opener_for({"youtube": [], "web": []})
        report = A.probe(["x"], opener=op)
        self.assertIn("not search volume", report["limit"])

    def test_empty_term_refused(self):
        with self.assertRaises(ValueError):
            A.probe_term("  ", opener=opener_for({"youtube": [], "web": []}))


if __name__ == "__main__":
    unittest.main()
