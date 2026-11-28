#!/usr/bin/env python3
"""Print the live date context for a work session.

This is the project's guard against stale handoff dates. It reads the host
clock at runtime; it never derives "today" from a dated document. A dated
handoff (for example HANDOFF-2026-11-06.md) is a historical record, not the
current date.

Examples:
  python3 tools/date_context.py
  python3 tools/date_context.py --json
  python3 tools/date_context.py --timezone Asia/Karachi --timezone UTC

This utility cannot change an assistant platform's injected system date. If
that injected date, a user-supplied date and the host clock disagree, report
the disagreement explicitly and use the date the user has confirmed for the
task; record relative dates ("yesterday") against that confirmed reference.
"""
import argparse
import datetime as dt
import json
from zoneinfo import ZoneInfo

DEFAULT_ZONES = ('UTC', 'Asia/Karachi', 'America/New_York')


def date_context(now=None, zones=DEFAULT_ZONES):
    """Return today's/yesterday's calendar dates for each zone at `now`."""
    if now is None:
        now = dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        raise ValueError('now must be timezone-aware')
    now_utc = now.astimezone(dt.timezone.utc)
    zone_rows = {}
    for name in zones:
        local = now_utc.astimezone(ZoneInfo(name))
        today = local.date()
        zone_rows[name] = {
            'now': local.isoformat(timespec='seconds'),
            'today': today.isoformat(),
            'yesterday': (today - dt.timedelta(days=1)).isoformat(),
            'tomorrow': (today + dt.timedelta(days=1)).isoformat(),
        }
    return {
        'source': 'host_clock',
        'generated_at_utc': now_utc.isoformat(timespec='seconds'),
        'zones': zone_rows,
    }


def format_date_context(context):
    lines = [
        'Current date context (live host clock; dated handoffs are history, not today):',
        f"  generated_at_utc: {context['generated_at_utc']}",
    ]
    for name, row in context['zones'].items():
        lines.append(
            f"  {name}: now {row['now']} · today {row['today']} · yesterday {row['yesterday']}"
        )
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--timezone', action='append', dest='zones',
                        help='IANA timezone to include; repeatable (default: UTC, Asia/Karachi, America/New_York)')
    parser.add_argument('--json', action='store_true', help='print JSON instead of text')
    args = parser.parse_args(argv)
    context = date_context(zones=tuple(args.zones) if args.zones else DEFAULT_ZONES)
    print(json.dumps(context, indent=2) if args.json else format_date_context(context))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
