"""Evidence order follows observed records, including across clones and clock rollback."""
import json
import subprocess
import sys
from unittest.mock import patch

from test_tasks import TaskFixture
from test_workflow import RUNTIME
from twc_lib import evidence, lifecycle, policy


class EvidenceOrderingTests(TaskFixture):
    def setup_task(self, checks=('unit',)):
        self.checks([(name, 'from pathlib import Path; import sys; '
                      f'sys.exit(7 if Path(".workflow/local/{name}-fail").exists() else 0)', 5)
                     for name in checks])
        self.git('commit', '-qam', 'approved conditional checks')
        config, sha = self.configuration()
        lifecycle.create(self.root, config, sha, 'local:one', 'contract.json', session='one', offline=True)
        lifecycle.transition(self.root, config, sha, 'start', session='one')

    def run_at(self, stamp, root=None, selected=()):
        root = root or self.root
        config, sha = policy.load(root)
        with patch('twc_lib.models.now', return_value=stamp), patch('twc_lib.evidence.now', return_value=stamp):
            return evidence.verify(root, config, sha, selected, execute_commands=True,
                                   approved_policy=sha, session='one')

    def cli(self, *args, root=None, expected=0):
        result = subprocess.run([sys.executable, str(RUNTIME / 'twc.py'), '--project', str(root or self.root),
                                 '--session', 'one', *args], capture_output=True, text=True)
        self.assertEqual(result.returncode, expected, result.stderr or result.stdout)
        self.assertNotIn('Traceback', result.stderr)
        return json.loads(result.stdout)

    def test_clock_rollback_across_clone_blocks_failure_then_allows_success(self):
        self.setup_task()
        first = self.run_at('2026-11-02T10:05:00+00:00')
        self.assertEqual(first['status'], 'passed')
        original = (self.root / first['task_evidence']).read_bytes()
        self.commit_task()
        clone = self.root.parent / 'receiver'
        subprocess.run(['git', 'clone', '-q', '-c', 'core.autocrlf=true', str(self.root), str(clone)], check=True)
        for key, value in [('user.name', 'Receiver'), ('user.email', 'receiver@example.invalid'),
                           ('core.hooksPath', str(clone / 'no-hooks'))]:
            subprocess.run(['git', '-C', str(clone), 'config', key, value], check=True)
        received = (clone / first['task_evidence']).read_bytes()
        self.assertIn(b'\r\n', received)
        self.assertEqual(json.loads(received), json.loads(original))
        self.cli('task', 'start', '--task', 'local:one', root=clone)
        marker = clone / '.workflow/local/unit-fail'
        marker.write_text('fail')
        failed = self.run_at('2026-11-02T10:00:00+00:00', clone)
        self.assertEqual((failed['status'], failed['checks'][0]['exit_code']), ('failed', 7))
        self.assertEqual(self.cli('resume', root=clone)['checks']['unit']['status'], 'failed')
        denied = self.cli('task', 'complete', root=clone, expected=1)
        self.assertIn('required_checks_not_currently_passed', denied['blockers'])
        marker.unlink()
        self.assertEqual(self.run_at('2026-11-02T09:55:00+00:00', clone)['status'], 'passed')
        self.assertEqual(self.cli('resume', root=clone)['checks']['unit']['status'], 'passed')
        self.assertEqual(self.cli('task', 'complete', root=clone)['execution_state'], 'completed')
        self.assertEqual(self.cli('resume', root=clone)['execution']['completion'], 'current')
        self.assertEqual((clone / first['task_evidence']).read_bytes(), received)
        self.assertEqual((self.root / first['task_evidence']).read_bytes(), original)

    def conflicting_records(self, *, legacy=False):
        self.setup_task()
        first = self.run_at('2026-11-02T10:05:00+00:00')
        path = self.root / first['task_evidence']
        data = path.read_bytes()
        path.unlink()  # An independent branch did not observe this other branch's pass.
        marker = self.root / '.workflow/local/unit-fail'
        marker.write_text('fail')
        second = self.run_at('2026-11-02T10:10:00+00:00')
        path.write_bytes(data)
        marker.unlink()
        paths = [self.root / run['task_evidence'] for run in (first, second)]
        if legacy:
            for path in paths:
                value = json.loads(path.read_text())
                for check in value['checks']:
                    check.pop('supersedes', None)
                path.write_text(json.dumps(value))
        historical = {path: path.read_bytes() for path in paths}
        view = self.cli('resume')
        self.assertEqual(view['checks']['unit']['status'], 'incomplete')
        self.assertEqual(view['checks']['unit']['reason'], 'evidence_order_unresolved')
        self.assertEqual(self.cli('task', 'complete', expected=1)['applied'], False)
        self.assertEqual(self.run_at('2026-11-02T09:55:00+00:00')['status'], 'passed')
        self.assertEqual(self.cli('resume')['checks']['unit']['status'], 'passed')
        self.assertEqual(self.cli('task', 'complete')['execution_state'], 'completed')
        self.assertTrue(all(path.read_bytes() == data for path, data in historical.items()))

    def test_independent_branch_conflict_requires_observed_rerun(self):
        self.conflicting_records()

    def test_legacy_conflict_remains_readable_and_requires_observed_rerun(self):
        self.conflicting_records(legacy=True)

    def test_clock_rollback_keeps_unattempted_checks_and_selected_reruns_separate(self):
        self.setup_task(('unit', 'full'))
        self.assertEqual(self.run_at('2026-11-02T10:05:00+00:00')['status'], 'passed')
        marker = self.root / '.workflow/local/unit-fail'
        marker.write_text('fail')
        self.assertEqual(self.run_at('2026-11-02T10:00:00+00:00')['status'], 'failed')
        states = self.cli('resume')['checks']
        self.assertEqual({name: row['status'] for name, row in states.items()}, {'unit': 'failed', 'full': 'passed'})
        self.run_at('2026-11-02T09:55:00+00:00', selected=('full',))
        self.assertEqual(self.cli('resume')['checks']['unit']['status'], 'failed')
        marker.unlink()
        self.run_at('2026-11-02T09:50:00+00:00', selected=('unit',))
        self.assertEqual(self.cli('task', 'complete')['execution_state'], 'completed')
