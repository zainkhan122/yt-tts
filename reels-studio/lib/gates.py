"""Gate receipts: brief lint + SEO gate results, persisted with stable rule IDs.

Before this module the two gates only printed; the printed lines were lost with the run.
Now every result is a `{"id", "severity", "message"}` finding (see RULES in
tools/brief_lint.py, RULE_IDS in tools/seo_pack.py) and each render's manifest.json gets a
`gates` section - the manifest rides inside the published kit, so the receipt travels with
the video and a later rebuild can be compared rule by rule instead of by prose.

Stdlib only (no numpy/render deps): the workflow safety suites import this in CI.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.brief_lint import check as lint_check  # noqa: E402
from tools.seo_pack import check as seo_check  # noqa: E402


def run(brief_path):
    """Run both gates against one brief -> receipt-shaped report.

    {"brief", "lint": [findings], "seo": [findings],
     "rollup": {"errors", "warnings", "by_id": {rule id: count}}}
    """
    brief_path = Path(brief_path)
    _, lint_errors, lint_warns, lint_findings = lint_check(brief_path)
    try:
        _, seo_errors, seo_warns, seo_findings, *_ = seo_check(brief_path)
    except Exception as exc:  # a broken brief is recorded, not raised: the receipt must exist
        seo_errors, seo_warns, seo_findings = [f"[SP000] seo gate failed: {exc}"], [], [
            {"id": "SP000", "severity": "error", "message": f"seo gate failed: {exc}"}]
    findings = lint_findings + seo_findings
    by_id = {}
    for f in findings:
        by_id[f["id"]] = by_id.get(f["id"], 0) + 1
    return {"brief": brief_path.stem if brief_path.stem else brief_path.name, "path": str(brief_path),
            "lint": lint_findings, "seo": seo_findings,
            "rollup": {"errors": len(lint_errors) + len(seo_errors), "warnings": len(lint_warns) + len(seo_warns),
                       "by_id": dict(sorted(by_id.items()))}}


def record(manifest_path, report):
    """Merge one gate report into a render manifest (the durable per-video receipt)."""
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text())
    history = manifest.get("gates", {}).get("history", [])
    entry = {"at": report.get("at"), "lint": report["lint"], "seo": report["seo"], "rollup": report["rollup"]}
    previous = manifest.get("gates", {}).get("current")
    manifest["gates"] = {"current": entry, "history": [*history, entry][-10:]}
    if previous and previous.get("rollup", {}).get("by_id") != report["rollup"]["by_id"]:
        manifest["gates"]["changed_since_last_run"] = {
            "before": previous["rollup"]["by_id"], "after": report["rollup"]["by_id"]}
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return manifest["gates"]


def summary_lines(report):
    lines = [f"{report['brief']}: {report['rollup']['errors']} error(s), {report['rollup']['warnings']} warning(s)"]
    for f in report["lint"] + report["seo"]:
        lines.append(f"  {'x' if f['severity'] == 'error' else '!'} [{f['id']}] {f['message']}")
    if not report["lint"] and not report["seo"]:
        lines.append("  clean: no findings")
    return lines
