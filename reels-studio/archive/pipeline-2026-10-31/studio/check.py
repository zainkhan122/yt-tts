"""CLI: check briefs against the v2 hard rules.

    python3 -m studio.check                      # every brief in briefs/
    python3 -m studio.check briefs/x.json        # one brief
    python3 -m studio.check --show-final x       # also print final text per platform

Exit status 1 when any brief has an error.
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from studio.rules import PLATFORMS, assemble, check_brief, errors

ROOT = Path(__file__).resolve().parent.parent


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("paths", nargs="*")
    p.add_argument("--today", default=None, help="YYYY-MM-DD (default: local today)")
    p.add_argument("--captures", default=str(ROOT / "captures"), help="capture packs root")
    p.add_argument("--show-final", action="store_true")
    a = p.parse_args(argv)

    paths = [Path(x) for x in a.paths] or sorted((ROOT / "briefs").glob("*.json"))
    today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
    failed = 0
    for path in paths:
        path = path if path.is_absolute() else (ROOT / path if (ROOT / path).exists() else Path.cwd() / path)
        try:
            brief = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"✗ {path.name}: cannot read ({exc})")
            failed += 1
            continue
        bid = brief.get("id", path.stem)
        captures = Path(a.captures) / bid
        findings = check_brief(brief, today=today, captures_dir=captures if captures.exists() else None)
        errs = errors(findings)
        mark = "✗" if errs else "✓"
        warns = len(findings) - len(errs)
        print(f"{mark} {bid}: {len(errs)} error(s), {warns} warning(s)")
        for f in findings:
            print(f"    {f}")
        if a.show_final and not errs:
            for platform in PLATFORMS:
                if platform in brief.get("seo", {}):
                    print(f"  --- {platform}\n{assemble(brief['seo'], platform)}\n")
        failed += 1 if errs else 0
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
