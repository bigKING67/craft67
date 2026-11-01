"""Actual POSIX cancellation/timeout, including cleanup after the leader exits."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

RUNTIME = Path(__file__).resolve().parents[1] / 'skills/workflow-craft/scripts'

DRIVER = """
import json,signal,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from twc_lib import evidence
evidence._TERMINATE_GRACE_SECONDS=float(sys.argv[4])
previous=signal.getsignal(signal.SIGINT)
result=evidence.execute(Path.cwd(),'probe',
    dict(argv=[sys.executable,sys.argv[2]],timeout_seconds=float(sys.argv[3])),None)
assert signal.getsignal(signal.SIGINT)==previous
print(json.dumps(result),flush=True)
"""

LEADER = """
import os,subprocess,sys,time
subprocess.Popen([sys.executable,'worker.py'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(60)
"""

WORKER = """
import json,os,signal,subprocess,sys,time
from pathlib import Path
def stop(signum,frame):
    raise SystemExit(143)
signal.signal(signal.SIGTERM,stop)
external=None
try:
    Path('resource').write_text('owned fixture')
    external=subprocess.Popen([sys.executable,'external.py'],start_new_session=True,
        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    while not Path('locked').exists():
        time.sleep(.01)
    Path('ready.json').write_text(json.dumps(dict(leader=os.getppid(),worker=os.getpid(),external=external.pid)))
    time.sleep(60)
finally:
    # The leader has the default SIGTERM action and exits before this cleanup.
    Path('cleaning').write_text('yes')
    time.sleep(.25)
    if external is not None:
        external.terminate()
        external.wait(timeout=3)
    Path('resource').unlink()
    Path('cleaned').write_text('yes')
"""

EXTERNAL = """
import fcntl,time
from pathlib import Path
lock=Path('resource.lock').open('w')
fcntl.flock(lock,fcntl.LOCK_EX)
Path('locked').write_text('yes')
time.sleep(60)
"""

STUBBORN = """
import json,os,signal,time
from pathlib import Path
signal.signal(signal.SIGTERM,signal.SIG_IGN)
Path('ready.json').write_text(json.dumps(dict(leader=os.getpid())))
time.sleep(60)
"""


@unittest.skipUnless(os.name == 'posix', 'actual POSIX signals and advisory lock')
class PosixCleanupTests(unittest.TestCase):
    def exercise(self, *, timeout=False, stubborn=False, repeated=False):
        with tempfile.TemporaryDirectory(prefix='workflow cancel 空格 ') as folder:
            root = Path(folder)
            for name, source in [('leader.py', STUBBORN if stubborn else LEADER),
                                 ('worker.py', WORKER), ('external.py', EXTERNAL)]:
                (root / name).write_text(source, encoding='utf-8')
            process = subprocess.Popen([sys.executable, '-B', '-c', DRIVER, str(RUNTIME),
                'leader.py', '1' if timeout else '30', '.25' if stubborn else '3'],
                cwd=root, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True, start_new_session=True)
            owned = {}
            try:
                deadline = time.monotonic() + 8
                while time.monotonic() < deadline:
                    try:
                        owned = json.loads((root / 'ready.json').read_text())
                        break
                    except (FileNotFoundError, json.JSONDecodeError):
                        if process.poll() is not None:
                            self.fail('driver exited before the check was ready: ' + repr(process.communicate()))
                        time.sleep(.02)
                self.assertTrue(owned, 'real check must reach the resource-owning phase')
                start = time.monotonic()
                if not timeout:
                    process.send_signal(signal.SIGINT)
                if repeated:
                    deadline = time.monotonic() + 3
                    while not (root / 'cleaning').exists() and time.monotonic() < deadline:
                        time.sleep(.01)
                    self.assertTrue((root / 'cleaning').exists())
                    process.send_signal(signal.SIGINT)
                stdout, stderr = process.communicate(timeout=8)
                elapsed = time.monotonic() - start
                self.assertEqual(process.returncode, 0, stderr)
                result = json.loads(stdout)
                self.assertEqual((result['status'], result['reason']),
                                 ('incomplete', 'timeout' if timeout else 'cancelled'), stderr)
                if stubborn:
                    self.assertEqual(result['exit_code'], -signal.SIGKILL)
                    self.assertGreaterEqual(elapsed, .2)
                    self.assertLess(elapsed, 5)
                else:
                    self.assertTrue((root / 'cleaned').is_file(),
                                    'descendant finally must finish after the leader exits')
                    self.assertFalse((root / 'resource').exists())
                    import fcntl
                    with (root / 'resource.lock').open() as lock:
                        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    with self.assertRaises(ProcessLookupError):
                        os.kill(owned['external'], 0)
                return result
            finally:
                # Only sessions created and recorded by this test are eligible.
                for group in (owned.get('leader'), owned.get('external'), process.pid):
                    if group is not None:
                        try:
                            os.killpg(group, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                process.wait(timeout=5)
                process.stdout.close()
                process.stderr.close()

    def test_actual_sigint_waits_for_descendant_resource_and_detached_lock_cleanup(self):
        self.exercise()

    def test_actual_timeout_waits_for_descendant_cleanup(self):
        self.exercise(timeout=True)

    def test_repeated_sigint_does_not_interrupt_resource_cleanup(self):
        self.exercise(repeated=True)

    def test_uncooperative_group_is_killed_after_bounded_grace(self):
        self.exercise(stubborn=True)

    def test_denied_existence_probe_is_not_reported_as_absence(self):
        sys.path.insert(0, str(RUNTIME))
        from twc_lib import evidence
        with patch.object(evidence.os, 'killpg', side_effect=PermissionError):
            self.assertTrue(evidence._group_alive(SimpleNamespace(pid=123)))
        with patch.object(evidence.os, 'killpg', side_effect=ProcessLookupError):
            self.assertFalse(evidence._group_alive(SimpleNamespace(pid=123)))

    def test_actual_termination_permission_error_is_not_swallowed(self):
        sys.path.insert(0, str(RUNTIME))
        from twc_lib import evidence
        previous = signal.getsignal(signal.SIGINT)
        with patch.object(evidence.os, 'killpg', side_effect=PermissionError):
            with self.assertRaises(PermissionError):
                evidence._stop(SimpleNamespace(pid=123))
        self.assertEqual(signal.getsignal(signal.SIGINT), previous)


if __name__ == '__main__':
    unittest.main()
