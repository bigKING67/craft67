"""Real subprocess/lock contracts, run on Windows and POSIX (no simulated OS)."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

RUNTIME = Path(__file__).resolve().parents[1] / 'skills/workflow-craft/scripts'
sys.path.insert(0, str(RUNTIME))
from twc_lib import evidence, sessions


class ProcessTreeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='workflow 空格 ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def execute(self, code, timeout=10):
        return evidence.execute(self.root, 'probe', dict(argv=[sys.executable, '-c', code],
                                                       timeout_seconds=timeout), 'FIXTURE_TOKEN')

    def test_exit_output_arguments_and_environment_are_preserved(self):
        code = 'import os,sys; assert "FIXTURE_TOKEN" not in os.environ; print("hello"); sys.exit(7)'
        with patch.dict(os.environ, FIXTURE_TOKEN='fixture-only'):
            result = self.execute(code)
        self.assertEqual((result['status'], result['exit_code']), ('failed', 7))
        output = b'hello\r\n' if os.name == 'nt' else b'hello\n'
        self.assertEqual(result['output_sha256'], hashlib.sha256(output).hexdigest())
        self.assertEqual(result['output_bytes'], len(output))
        self.assertEqual(self.execute('print("你好 空格")')['status'], 'passed')

    def test_missing_program_cannot_pass(self):
        result = evidence.execute(self.root, 'probe', dict(argv=['workflow-missing-program-999']), None)
        self.assertEqual(result['status'], 'not_run')
        self.assertIsNone(result['exit_code'])

    def child_script(self, parent_sleep=False, redirected=False):
        # A surviving child would write the sentinel after execute returns.
        child = 'import time,pathlib; time.sleep(3); pathlib.Path("leaked").write_text("bad")'
        redirect = ', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL' if redirected else ''
        return ('import subprocess,sys,time; subprocess.Popen([sys.executable,"-c",' + repr(child) + ']' + redirect + '); '
                + ('time.sleep(30)' if parent_sleep else ''))

    def test_timeout_terminates_children(self):
        result = self.execute(self.child_script(parent_sleep=True), timeout=1)
        self.assertEqual((result['status'], result['reason']), ('incomplete', 'timeout'))
        time.sleep(3)
        self.assertFalse((self.root / 'leaked').exists())

    def test_background_children_block_completion_with_or_without_stdout(self):
        for redirected in (False, True):
            with self.subTest(redirected=redirected):
                result = self.execute(self.child_script(redirected=redirected))
                self.assertEqual((result['status'], result['reason']), ('incomplete', 'child_process_still_running'))
        time.sleep(3)
        self.assertFalse((self.root / 'leaked').exists())

    def test_cancellation_is_incomplete_and_releases_processes(self):
        original = subprocess.Popen.wait
        interrupted = False

        def wait(process, *args, **kwargs):
            nonlocal interrupted
            if not interrupted:
                interrupted = True
                raise KeyboardInterrupt
            return original(process, *args, **kwargs)

        with patch.object(subprocess.Popen, 'wait', wait):
            result = self.execute('import time; time.sleep(30)')
        self.assertEqual((result['status'], result['reason']), ('incomplete', 'cancelled'))

    @unittest.skipUnless(os.name == 'nt', 'Windows Job Object assignment failure')
    def test_assignment_failure_never_executes_project_code(self):
        from twc_lib import windows_job
        original = windows_job._api

        def denied_api():
            api = original()
            api.AssignProcessToJobObject = lambda *args: 0
            return api

        with patch.object(windows_job, '_api', denied_api):
            result = self.execute('from pathlib import Path; Path("leaked").write_text("bad")')
        self.assertEqual(result['status'], 'incomplete')
        self.assertFalse((self.root / 'leaked').exists())

    def test_lock_released_after_owner_is_killed_and_nested_use_is_safe(self):
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        (self.root / '.gitignore').write_text('.team-workflow/local/\n')
        script = ('import sys,time; from pathlib import Path; sys.path.insert(0,sys.argv[1]); '
                  'from twc_lib.sessions import workspace_lock\n'
                  'with workspace_lock(Path(sys.argv[2])):\n print("locked",flush=True); time.sleep(30)\n')
        process = subprocess.Popen([sys.executable, '-c', script, str(RUNTIME), str(self.root)],
                                   stdout=subprocess.PIPE, text=True)
        try:
            self.assertEqual(process.stdout.readline().strip(), 'locked')
            with self.assertRaisesRegex(Exception, 'Workspace is busy'):
                with sessions.workspace_lock(self.root):
                    self.fail('second writer acquired lock')
        finally:
            process.kill()
            process.wait(timeout=5)
            process.stdout.close()
        with sessions.workspace_lock(self.root):
            with sessions.workspace_lock(self.root):
                pass


if __name__ == '__main__':
    unittest.main()
