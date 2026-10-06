"""Exercise a real local stdio subprocess; no Codex/model calls or personal data."""
import json
import os
import sys
import time
import signal
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app_server_runtime as app


FAKE = r'''
import json, os, sys, time, subprocess
mode = sys.argv[1]
def emit(x):
    print(json.dumps(x), flush=True)
for line in sys.stdin:
    req = json.loads(line)
    method = req['method']
    if method == 'initialize':
        assert os.path.isdir(os.environ['CODEX_HOME'])
        assert not os.path.exists(os.path.join(os.environ['CODEX_HOME'], 'config.toml'))
        if mode == 'descendant':
            child = "import signal,time,pathlib; signal.signal(signal.SIGTERM,signal.SIG_IGN); pathlib.Path(" + repr(sys.argv[2] + ".ready") + ").write_text('ready'); time.sleep(4); pathlib.Path(" + repr(sys.argv[2]) + ").write_text('late')"
            subprocess.Popen([sys.executable, '-c', child])
            time.sleep(30)
        if mode == 'hang':
            time.sleep(30)
        emit({'id': req['id'], 'result': {}})
    elif method == 'account/login/start':
        assert req['params']['type'] == 'apiKey'
        assert 'CODEX_API_KEY' not in os.environ
        emit({'id': req['id'], 'result': {}})
    elif method == 'thread/start':
        p = req['params']
        assert p['ephemeral'] and p['sandbox'] == 'read-only' and p['approvalPolicy'] == 'never'
        cwd = p['cwd']
        emit({'id': req['id'], 'result': {'thread': {'id': 't'}, 'model': p['model'],
              'cwd': cwd, 'reasoningEffort': p['config']['model_reasoning_effort'], 'approvalPolicy': 'never', 'sandbox': {'type': 'readOnly' if mode != 'unsafe' else 'dangerFullAccess'}}})
    elif method == 'turn/start':
        assert req['params']['effort'] == p['config']['model_reasoning_effort']
        items = req['params']['input']
        assert items[1]['type'] == 'skill' and items[1]['name'] == 'example'
        assert open(items[1]['path']).read() == '# example\n'
        if mode == 'reject':
            emit({'id': req['id'], 'error': {'message': 'private-secret'}})
            continue
        if mode == 'mutate':
            open(items[1]['path'], 'w').write('changed')
        if mode == 'approval':
            emit({'id': 99, 'method': 'item/commandExecution/requestApproval', 'params': {'secret': 'private-secret'}})
            continue
        emit({'id': req['id'], 'result': {'turn': {'id': 'u', 'status': 'inProgress'}}})
        turn = 'foreign' if mode == 'wrong-turn' else 'u'
        emit({'method': 'item/completed', 'params': {'threadId': 't', 'turnId': turn,
             'item': {'type': 'agentMessage', 'id': 'a', 'phase': 'final_answer', 'text': 'answer'}}})
        emit({'method': 'turn/completed', 'params': {'threadId': 't', 'turn': {'id': turn, 'status': 'completed', 'error': None}}})
'''


@unittest.skipUnless(os.name == "posix", "App Server adapter is POSIX-only")
class AppServerTests(unittest.TestCase):
    def run_fake(self, mode, timeout=2, marker="unused", skill_bytes=b"# example\n", effort="medium"):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            bundle = root / 'example'
            bundle.mkdir()
            (bundle / 'SKILL.md').write_bytes(skill_bytes)
            with patch.object(app, 'load_manifest', return_value={
                'default_install_root': str(root), 'skills': [{'name': 'example'}],
            }):
                return app.run_app_server('task', skill_name='example', model='test-model',
                    timeout=timeout, reasoning_effort=effort, command=[sys.executable, '-u', '-c', FAKE, mode, str(marker)])

    def test_success_binds_input_but_does_not_claim_injected_bytes(self):
        result = self.run_fake('success')
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['answer'], 'answer')
        receipt = result['skill_input_receipt']
        self.assertTrue(receipt['input_accepted'])
        self.assertTrue(receipt['turn_completed'])
        self.assertTrue(receipt['bundle_unchanged'])
        self.assertFalse(receipt['runtime_skill_loading_verified'])

    def test_high_effort_and_api_key_login_do_not_persist_key(self):
        with patch.dict(os.environ, {"CODEX_API_KEY": "credential-sentinel"}):
            result = self.run_fake('success', effort='high')
        self.assertTrue(result['ok'])
        self.assertEqual(result['skill_input_receipt']['observed_reasoning_effort'], 'high')
        self.assertEqual(result['skill_input_receipt']['authentication'], 'api-key-login-accepted')
        self.assertNotIn('credential-sentinel', json.dumps(result))

    def test_skill_digest_binds_raw_bytes(self):
        import hashlib
        raw = b"# example\r\n"
        result = self.run_fake('success', skill_bytes=raw)
        self.assertTrue(result['ok'])
        self.assertEqual(result['skill_input_receipt']['skill_sha256'], hashlib.sha256(raw).hexdigest())

    def test_rejection_approval_and_isolation_fail_closed_without_payloads(self):
        for mode in ('reject', 'approval', 'unsafe'):
            with self.subTest(mode=mode):
                result = self.run_fake(mode)
                self.assertFalse(result['ok'])
                self.assertNotIn('private-secret', json.dumps(result))

    def test_bundle_mutation_rejected(self):
        result = self.run_fake('mutate')
        self.assertFalse(result['ok'])
        self.assertIn('changed', result['error'])

    def test_timeout_and_foreign_turn_do_not_succeed(self):
        for mode in ('hang', 'wrong-turn'):
            with self.subTest(mode=mode):
                result = self.run_fake(mode, timeout=0.3)
                self.assertFalse(result['ok'])
                self.assertIn('timeout', result['error'])
                self.assertLess(result['duration_seconds'], 3)

    def test_timeout_reaps_ignoring_term_descendant(self):
        with tempfile.TemporaryDirectory() as temp:
            marker = Path(temp) / "late"
            result = self.run_fake('descendant', timeout=2, marker=marker)
            self.assertFalse(result['ok'])
            self.assertTrue(Path(str(marker) + '.ready').exists())
            time.sleep(4.1)
            self.assertFalse(marker.exists())

    def test_sigterm_unwinds_app_server_entry(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            bundle = root / "example"
            bundle.mkdir()
            (bundle / "SKILL.md").write_text("# example\n")
            marker = root / "late"
            wrapper = (
                "import app_server_runtime as a,sys; "
                + "a.load_manifest=lambda:" + repr({'default_install_root': str(root), 'skills': [{'name': 'example'}]}) + "; "
                + "a.run_app_server('task',skill_name='example',model='test-model',timeout=10,command="
                + repr([sys.executable, '-u', '-c', FAKE, 'descendant', str(marker)]) + ")"
            )
            env = os.environ.copy()
            env['PYTHONPATH'] = str(Path(__file__).resolve().parent)
            process = subprocess.Popen([sys.executable, '-c', wrapper], env=env,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                deadline = time.monotonic() + 5
                while not Path(str(marker) + '.ready').exists() and time.monotonic() < deadline:
                    time.sleep(0.02)
                self.assertTrue(Path(str(marker) + '.ready').exists())
                process.send_signal(signal.SIGTERM)
                process.communicate(timeout=3)
                self.assertEqual(process.returncode, 143)
                time.sleep(4.1)
                self.assertFalse(marker.exists())
            finally:
                if process.poll() is None:
                    process.kill()
                    process.communicate(timeout=3)


class AppServerPlatformTests(unittest.TestCase):
    def test_unsupported_platform_rejected_before_spawn(self):
        with patch.object(app.os, 'name', 'nt'), patch.object(app.subprocess, 'Popen') as spawn:
            with self.assertRaisesRegex(ValueError, 'POSIX'):
                app.run_app_server('task', skill_name='example', model='test', timeout=1)
            spawn.assert_not_called()


if __name__ == '__main__':
    unittest.main()
