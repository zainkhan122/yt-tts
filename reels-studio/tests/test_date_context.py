"""Live date-context: relative dates must come from the clock, not handoffs."""
import datetime as dt
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.date_context import date_context, format_date_context  # noqa: E402


class DateContextTests(unittest.TestCase):
    def test_zones_can_disagree_on_the_calendar_day(self):
        # 00:30 UTC on 27 Nov is already 27 Nov in Karachi but still 26 Nov in New York.
        ctx = date_context(dt.datetime(2026, 11, 27, 0, 30, tzinfo=dt.timezone.utc))
        self.assertEqual(ctx['source'], 'host_clock')
        self.assertEqual(ctx['zones']['UTC']['today'], '2026-11-27')
        self.assertEqual(ctx['zones']['Asia/Karachi']['today'], '2026-11-27')
        self.assertEqual(ctx['zones']['Asia/Karachi']['yesterday'], '2026-11-26')
        self.assertEqual(ctx['zones']['America/New_York']['today'], '2026-11-26')
        self.assertEqual(ctx['zones']['America/New_York']['yesterday'], '2026-11-25')

    def test_year_boundary(self):
        ctx = date_context(dt.datetime(2027, 1, 1, 0, 30, tzinfo=dt.timezone.utc))
        self.assertEqual(ctx['zones']['Asia/Karachi']['today'], '2027-01-01')
        self.assertEqual(ctx['zones']['Asia/Karachi']['yesterday'], '2026-12-31')
        self.assertEqual(ctx['zones']['America/New_York']['today'], '2026-12-31')

    def test_naive_now_rejected(self):
        with self.assertRaises(ValueError):
            date_context(dt.datetime(2026, 11, 27, 0, 30))

    def test_format_names_today_and_yesterday(self):
        ctx = date_context(dt.datetime(2026, 11, 27, 12, 0, tzinfo=dt.timezone.utc))
        text = format_date_context(ctx)
        self.assertIn('today 2026-11-27', text)
        self.assertIn('yesterday 2026-11-26', text)


if __name__ == '__main__':
    unittest.main()
