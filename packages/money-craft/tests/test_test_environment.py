import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from storage_check import inventory
import test_environment
SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/test_environment.py'


@unittest.skipUnless(os.name == 'posix', 'macOS/Linux only')
class EnvironmentTests(unittest.TestCase):
    def command(self, out, code, *options):
        return [sys.executable, str(SCRIPT), '--output-dir', str(out), *options,
                '--', '{python}', '-c', code]

    def test_success_and_failure_preserve_evidence_remove_scratch(self):
        with tempfile.TemporaryDirectory() as directory:
            for exit_code in (0, 7):
                out = Path(directory).resolve()/str(exit_code)
                code = ('import os,pathlib,sys; '
                        'p=pathlib.Path(os.environ["MONEY_CRAFT_TEST_OUTPUT"]); '
                        '(p/"report.md").write_text("evidence"); '
                        '(p/"scratch.txt").write_text(os.environ["MONEY_CRAFT_DATA_HOME"]); '
                        f'sys.exit({exit_code})')
                process = subprocess.run(self.command(out, code), capture_output=True, text=True)
                self.assertEqual(process.returncode, exit_code, process.stderr)
                self.assertEqual((out/'report.md').read_text(), 'evidence')
                self.assertFalse(Path((out/'scratch.txt').read_text()).exists())
                receipt = json.loads((out/'test-environment-receipt.json').read_text())
                self.assertTrue(receipt['temporary_environment_removed'])
                self.assertEqual(receipt['semantic_verdict'], 'NOT_ASSESSED')

    def test_timeout_kills_descendant(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory).resolve()/'evidence'
            child = f'import time,pathlib;time.sleep(2);pathlib.Path({str(out/"leak")!r}).write_text("bad")'
            code = f'import subprocess,sys,time;subprocess.Popen([sys.executable,"-c",{child!r}]);time.sleep(30)'
            result = subprocess.run(self.command(out, code, '--timeout', '1'), capture_output=True)
            self.assertEqual(result.returncode, 124, result.stderr)
            time.sleep(2)
            self.assertFalse((out/'leak').exists())
            self.assertTrue(json.loads((out/'test-environment-receipt.json').read_text())['temporary_environment_removed'])

    def test_interrupt_cleans_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory).resolve()/'evidence'
            code = ('import os,pathlib,time; '
                    '(pathlib.Path(os.environ["MONEY_CRAFT_TEST_OUTPUT"])/"ready").write_text(os.environ["TMPDIR"]); '
                    'time.sleep(30)')
            process = subprocess.Popen(self.command(out, code))
            try:
                deadline = time.monotonic()+10
                while not (out/'ready').exists() and time.monotonic()<deadline:
                    time.sleep(.02)
                self.assertTrue((out/'ready').exists())
                process.send_signal(signal.SIGTERM)
                self.assertEqual(process.wait(timeout=10), 143)
                self.assertFalse(Path((out/'ready').read_text()).exists())
            finally:
                if process.poll() is None:
                    process.kill(); process.wait()

    def test_existing_output_and_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            out = root/'existing'; out.mkdir(); (out/'keep').write_text('keep')
            alias = root/'alias'; alias.symlink_to(out, target_is_directory=True)
            for target in (out, alias/'new'):
                result = subprocess.run(self.command(target, 'raise AssertionError()'), capture_output=True)
                self.assertNotEqual(result.returncode, 0)
            self.assertEqual((out/'keep').read_text(), 'keep')
            self.assertFalse((out/'new').exists())

    def test_empty_venv_is_disposable(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory).resolve()/'evidence'
            code = ('import sys,os,pathlib; assert sys.prefix != sys.base_prefix; '
                    '(pathlib.Path(os.environ["MONEY_CRAFT_TEST_OUTPUT"])/"python").write_text(sys.executable)')
            result = subprocess.run(self.command(out, code, '--runtime', 'empty'), capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(Path((out/'python').read_text()).exists())

    def test_setup_failure_preserves_receipt_and_removes_scratch(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory).resolve()/'evidence'
            with mock.patch.object(test_environment, 'execute', return_value=9) as execute:
                self.assertEqual(test_environment.run(out, ['must-not-run'], 'empty', 10), 9)
            self.assertEqual(execute.call_count, 1)
            receipt = json.loads((out/'test-environment-receipt.json').read_text())
            self.assertEqual(receipt['status'], 'SETUP_FAILED')
            self.assertTrue(receipt['temporary_environment_removed'])

    def test_missing_command_still_cleans_scratch(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory).resolve()/'evidence'
            with self.assertRaises(FileNotFoundError):
                test_environment.run(out, ['/nonexistent/money-craft-test-command'], 'none', 10)
            receipt = json.loads((out/'test-environment-receipt.json').read_text())
            self.assertEqual(receipt['status'], 'ERROR')
            self.assertTrue(receipt['temporary_environment_removed'])

    def test_inventory_preserves_research_and_skips_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            for kind in ('research', 'acceptance', 'skill-evals'):
                path=root/'local'/kind/'20000101-example'; path.mkdir(parents=True)
                (path/'evidence').write_text('keep')
            (root/'local'/'external').symlink_to(root, target_is_directory=True)
            result = inventory(root)
            self.assertEqual(len(result['older_than_30_days_review_only']), 2)
            self.assertFalse(any('research' in p for p in result['older_than_30_days_review_only']))
            self.assertEqual(len(result['categories']), 3)
            self.assertEqual((root/'local/research/20000101-example/evidence').read_text(), 'keep')


if __name__ == '__main__':
    unittest.main()
