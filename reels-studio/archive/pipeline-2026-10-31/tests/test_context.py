"""Bounded-context tooling: pack budget/freshness, retrieval caps, output governor."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.context import ctxgrep, ctxpack, quiet  # noqa: E402

FAKE_STATE = {
    'buffer': {'enabled': True, 'pilot_passed': True, 'timezone': 'America/New_York', 'daily_target': 3,
               'queue_approvals': {'approved': 3, 'held': 8},
               'platform_receipt_states': {'sent': 8, 'scheduled': 1, 'published_manual': 3}},
    'youtube': {'enabled': True, 'long_pilot_passed': False, 'long_queue_count': 0, 'metadata_completed': 3,
                'recorded_refresh_grant_expiry_utc': None},
    'optional_agent': {'production_enabled': False, 'publishing_enabled': False, 'qualification': 'unqualified',
                       'lifecycle_status': 'paused_by_owner'},
    'operating_policy': {'decided_on': '2026-10-11'},
}


def make_tree(tmp, big_readme=False):
    root = Path(tmp)
    (root / 'config').mkdir(parents=True)
    (root / 'research/maintenance').mkdir(parents=True)
    (root / 'README.md').write_text('x' * (40000 if big_readme else 500))
    (root / 'RESUME.md').write_text('resume body ' * 50)
    (root / 'config/operating-policy.json').write_text(json.dumps({'decided_on': '2026-10-11'}))
    (root / 'research/maintenance/2026-10-10-x.json').write_text('{}')
    return root


class PackTests(unittest.TestCase):
    def test_pack_always_within_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_tree(tmp, big_readme=True)
            md, man = ctxpack.build_pack(root, state=FAKE_STATE, budget=4096)
            self.assertLessEqual(man['pack_bytes'], 4096)
            self.assertIn('Session context pack', md)
            self.assertIn('paused_by_owner', md)

    def test_pack_trims_and_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_tree(tmp)
            md, man = ctxpack.build_pack(root, state=FAKE_STATE, budget=700)
            self.assertTrue(man['truncated'])
            self.assertIn('trimmed to budget', md)

    def test_pack_counts_naive_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_tree(tmp, big_readme=True)
            _, man = ctxpack.build_pack(root, state=FAKE_STATE)
            self.assertGreaterEqual(man['naive_docs_bytes'], 40000)
            self.assertLess(man['pack_bytes'], man['naive_docs_bytes'])

    def test_check_reports_missing_pack(self):
        with tempfile.TemporaryDirectory() as tmp:
            ok, problems = ctxpack.check_pack(Path(tmp))
            self.assertFalse(ok)
            self.assertIn('no pack found', problems[0])

    def test_check_detects_state_change_and_stale_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_tree(tmp)
            state_file = root / 'config/publishing.json'
            state_file.write_text('{"a":1}')
            _, man = ctxpack.build_pack(root, state=FAKE_STATE)
            (root / '.context').mkdir()
            (root / '.context/pack.json').write_text(json.dumps(man))
            ok, problems = ctxpack.check_pack(root)
            self.assertTrue(ok, problems)
            state_file.write_text('{"a":2}')
            man['source_commit'] = 'deadbeef' * 5
            (root / '.context/pack.json').write_text(json.dumps(man))
            ok, problems = ctxpack.check_pack(root)
            self.assertFalse(ok)
            joined = ' | '.join(problems)
            self.assertIn('stale commit', joined)
            self.assertIn('config/publishing.json', joined)

    def test_check_flags_over_budget_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_tree(tmp)
            _, man = ctxpack.build_pack(root, state=FAKE_STATE)
            man['pack_bytes'] = 999999
            (root / '.context').mkdir()
            (root / '.context/pack.json').write_text(json.dumps(man))
            ok, problems = ctxpack.check_pack(root)
            self.assertFalse(ok)
            self.assertTrue(any('exceeds budget' in p for p in problems))


class GrepTests(unittest.TestCase):
    def test_rank_prefers_repeat_hits_and_skips_large(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'docs').mkdir()
            (root / 'docs/hot.md').write_text('alpha beta\n' * 20)
            (root / 'docs/cold.md').write_text('alpha once\n')
            (root / 'docs/huge.md').write_text('alpha ' * (ctxpack.MAX_FULL_BUDGET * 100))
            hits, skipped, scanned = ctxgrep.search(root, 'alpha')
            self.assertTrue(hits[0]['file'].endswith('hot.md'))
            self.assertGreaterEqual(skipped, 1)

    def test_render_caps_output(self):
        hits = [{'file': f'docs/f{i}.md', 'score': 1, 'terms_matched': '1/1', 'hits': 1,
                 'snippets': [{'line': 1, 'text': 'y' * 200}]} for i in range(30)]
        out = ctxgrep.render(hits, 0, 30, max_bytes=300)
        self.assertIn('capped at 300 bytes', out)

    def test_explicit_path_reaches_logs_under_skipped_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / '.context/logs').mkdir(parents=True)
            (root / '.context/logs/run.log').write_text('first line\nfound alpha here\n')
            hits, _, _ = ctxgrep.search(root, 'alpha', subdir='.context/logs')
            self.assertEqual(len(hits), 1)
            self.assertIn('run.log', hits[0]['file'])
            default_hits, _, _ = ctxgrep.search(root, 'alpha')
            self.assertEqual(default_hits, [])

    def test_path_may_point_at_a_single_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'one.json').write_text('{"k": "needle-value"}')
            (root / 'other.json').write_text('nothing')
            hits, _, scanned = ctxgrep.search(root, 'needle-value', subdir='one.json')
            self.assertEqual(scanned, 1)
            self.assertEqual(len(hits), 1)
            self.assertIn('one.json', hits[0]['file'])

    def test_no_hits_reports_and_exit_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'a.md').write_text('nothing here')
            hits, _, _ = ctxgrep.search(root, 'zzzznope')
            self.assertEqual(hits, [])
            proc = subprocess.run([sys.executable, str(ROOT / 'tools/context/ctxgrep.py'), 'zzzznonexistentterm'],
                                  capture_output=True, text=True, cwd=ROOT)
            self.assertEqual(proc.returncode, 1)


class QuietTests(unittest.TestCase):
    def test_bounds_output_but_keeps_full_log_and_exit_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = quiet.LOG_DIR
            quiet.LOG_DIR = Path(tmp)
            try:
                code, log, summary = quiet.run(
                    [sys.executable, '-c', "print('noise\\n'*50); print('last-marker')"], tail=1)
                self.assertEqual(code, 0)
                self.assertIn('last-marker', summary)
                self.assertIn('lines omitted', summary)
                self.assertIn('noise', log.read_text())
                self.assertGreater(log.read_text().count('noise'), 40)
                code, _, _ = quiet.run([sys.executable, '-c', 'import sys; sys.exit(3)'], tail=2)
                self.assertEqual(code, 3)
            finally:
                quiet.LOG_DIR = old


class ResumeCarryForwardTests(unittest.TestCase):
    def test_vaultless_regeneration_keeps_recorded_expiry(self):
        from tools.maintenance.resume_status import carry_forward_expiry
        info = {'youtube': {'recorded_refresh_grant_expiry_utc': None}}
        previous = {'youtube': {'recorded_refresh_grant_expiry_utc': '2026-10-17T13:42:00+00:00'}}
        carry_forward_expiry(info, previous, vault_present=False)
        self.assertEqual(info['youtube']['recorded_refresh_grant_expiry_utc'], '2026-10-17T13:42:00+00:00')

    def test_live_vault_value_wins_over_recorded(self):
        from tools.maintenance.resume_status import carry_forward_expiry
        info = {'youtube': {'recorded_refresh_grant_expiry_utc': '2026-11-01T00:00:00+00:00'}}
        previous = {'youtube': {'recorded_refresh_grant_expiry_utc': '2026-10-17T13:42:00+00:00'}}
        carry_forward_expiry(info, previous, vault_present=True)
        self.assertEqual(info['youtube']['recorded_refresh_grant_expiry_utc'], '2026-11-01T00:00:00+00:00')

    def test_production_grant_does_not_resurrect_recorded_expiry(self):
        # A production grant has no refresh_token_expires_at; a present vault is
        # authoritative and must not inherit the old testing-mode expiry.
        from tools.maintenance.resume_status import carry_forward_expiry
        info = {'youtube': {'recorded_refresh_grant_expiry_utc': None}}
        previous = {'youtube': {'recorded_refresh_grant_expiry_utc': '2026-10-17T13:42:00+00:00'}}
        carry_forward_expiry(info, previous, vault_present=True)
        self.assertIsNone(info['youtube']['recorded_refresh_grant_expiry_utc'])


if __name__ == '__main__':
    unittest.main()
