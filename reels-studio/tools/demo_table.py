#!/usr/bin/env python3
"""Build the demo-results markdown table from renders/*/manifest.json (numbers are measured, not typed)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ORDER = ["quiz-geography-01", "data-gdp-south-asia-01", "ranked-free-tools-01", "say-this-english-01", "say-this-urdu-voice-01"]


def row(mid):
    m = json.loads((ROOT / "renders" / mid / "manifest.json").read_text())
    b = json.loads((ROOT / m["brief"]).read_text()) if not m["brief"].startswith("/") else json.loads(Path(m["brief"]).read_text())
    q, st = m["qa"], m["stages"]
    checks = q["checks"]
    passed = sum(1 for v in checks.values() if v)
    words = st.get("words", {})
    return (f"| `renders/{mid}/{mid}.mp4` | {b.get('niche', '')} | `{m['template']}` | {q['duration']:.1f} s | {q['size_mb']:.1f} MB "
            f"| {st['render']['secs']:.0f} s / {m['total_secs']:.0f} s | {q['loudness_lufs']} LUFS / {q['peak_dbfs']} dBFS "
            f"| {words.get('whisper_char_match', 'n/a')} | {passed}/{len(checks)} |")


def main():
    lines = ["| Video | Niche | Template | Length | Size | Render / whole pipeline | Loudness / peak | Whisper heard the script | QA |",
             "|---|---|---|---|---|---|---|---|---|"]
    lines += [row(m) for m in ORDER if (ROOT / "renders" / m / "manifest.json").exists()]
    table = "\n".join(lines)
    if len(sys.argv) > 1:  # substitute into a report
        p = Path(sys.argv[1])
        s = p.read_text(encoding="utf-8")
        s = s.replace("{{DEMO_TABLE}}", table)
        p.write_text(s, encoding="utf-8")
    print(table)


if __name__ == "__main__":
    main()
