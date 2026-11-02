"""Offline launcher contracts; fake Codex records invocation without a model or network."""
import importlib.util
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/codex_readonly.py'
SPEC = importlib.util.spec_from_file_location('codex_readonly', SCRIPT)
launcher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(launcher)


@unittest.skipUnless(os.name == 'posix', 'Manual POSIX launcher; not a Windows host claim')
class CodexReadonlyTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name).resolve()
        self.project = self.base / 'project.with spaces'
        skill = self.project / '.agents/skills/workflow-craft/SKILL.md'
        skill.parent.mkdir(parents=True)
        skill.write_text('fixture Skill\n')
        self.prompt = self.base / 'prompt.txt'
        self.prompt.write_text('Read only, do not run checks or write files.\n')
        self.output = self.base / 'attempt'
        self.called = self.base / 'model-called.json'
        self.git = self.program('git-fixture', '''
if '--version' in sys.argv:
    print('git version fixture')
else:
    print(os.getcwd())
''')
        self.codex = self.program('codex-fixture', '''
if '--version' in sys.argv:
    print('codex-cli fixture')
    raise SystemExit(0)
if sys.argv[-3:] == ['mcp', 'list', '--json']:
    import tomllib
    enabled = True
    for index, value in enumerate(sys.argv):
        if value == '-c':
            settings = tomllib.loads(sys.argv[index + 1])
            enabled = settings.get('mcp_servers', {}).get('fixture.server.with.dots', {}).get('enabled', enabled)
    if os.environ.get('LAUNCHER_IGNORE_MCP_DISABLE'):
        enabled = True
    print(json.dumps([{'name': 'fixture.server.with.dots', 'enabled': enabled,
                       'transport': {'env': {'TOKEN': 'private-fixture-value'}}}]))
    raise SystemExit(0)
receipt = {'argv': sys.argv[1:], 'prompt': sys.stdin.read(), 'pid': os.getpid(),
           'path': os.environ['PATH'], 'zdotdir': os.environ.get('ZDOTDIR'),
           'python': subprocess.check_output(['python3', '-c', 'import sys; print(sys.executable)'], text=True).strip(),
           'git': subprocess.check_output(['git', '--version'], text=True).strip()}
Path(os.environ['LAUNCHER_CALLED']).write_text(json.dumps(receipt))
if os.environ.get('LAUNCHER_TIMEOUT'):
    child = os.fork()
    if child == 0:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        if os.environ.get('LAUNCHER_CHILD_READY'):
            Path(os.environ['LAUNCHER_CHILD_READY']).write_text(str(os.getpid()))
        time.sleep(1)
        Path(os.environ['LAUNCHER_SURVIVED']).write_text('survived')
        os._exit(0)
    time.sleep(30)
Path(sys.argv[sys.argv.index('--output-last-message') + 1]).write_text('fixture answer')
print(json.dumps({'type': 'fixture.completed'}))
raise SystemExit(int(os.environ.get('LAUNCHER_EXIT', '0')))
''')
        self.env = dict(os.environ, LAUNCHER_CALLED=str(self.called),
                        PYTHONDONTWRITEBYTECODE='1')

    def program(self, name, body):
        path = self.base / name
        path.write_text('#!' + sys.executable + '\nimport os, sys, json, subprocess, signal, time\nfrom pathlib import Path\n' + body)
        path.chmod(0o755)
        return path

    def run_launcher(self, *extra, env=None):
        return subprocess.run([sys.executable, '-B', str(SCRIPT), '--project', str(self.project),
                               '--prompt-file', str(self.prompt), '--output', str(self.output),
                               '--git', str(self.git), '--codex', str(self.codex), *extra],
                              capture_output=True, text=True, env=env or self.env, timeout=15)

    def test_preview_does_not_call_model_or_create_output(self):
        result = self.run_launcher()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'preview')
        self.assertFalse(self.output.exists())
        self.assertFalse(self.called.exists())

    def test_execution_pins_tools_without_replacing_shell_profile_or_model(self):
        profile = self.base / 'existing-profile'
        profile.mkdir()
        (profile / '.zprofile').write_text('export PATH=/nonexistent\n')
        before = (profile / '.zprofile').read_bytes()
        result = self.run_launcher('--execute', env=dict(self.env, ZDOTDIR=str(profile)))
        self.assertEqual(result.returncode, 0, result.stderr)
        called = json.loads(self.called.read_text())
        self.assertEqual(Path(called['python']).resolve(), Path(sys.executable).resolve())
        self.assertEqual(called['git'], 'git version fixture')
        self.assertEqual(called['zdotdir'], str(profile))
        self.assertEqual((profile / '.zprofile').read_bytes(), before)
        self.assertEqual(called['prompt'], self.prompt.read_text())
        argv = called['argv']
        settings = dict(value.split('=', 1) for i, value in enumerate(argv) if i and argv[i - 1] == '-c')
        self.assertEqual(settings['allow_login_shell'], 'false')
        self.assertEqual(settings['approval_policy'], '"never"')
        self.assertEqual(settings['shell_environment_policy.experimental_use_profile'], 'false')
        self.assertEqual(settings['features.shell_snapshot'], 'false')
        self.assertEqual(settings['features.plugins'], 'false')
        self.assertEqual(settings['features.hooks'], 'false')
        self.assertEqual(tomllib.loads('mcp_servers=' + settings['mcp_servers'])['mcp_servers'],
                         {'fixture.server.with.dots': {'enabled': False}})
        self.assertEqual(tomllib.loads('projects=' + settings['projects'])['projects'],
                         {str(self.project): {'trust_level': 'trusted'}})
        self.assertEqual(argv[argv.index('--sandbox') + 1], 'read-only')
        self.assertIn('--ephemeral', argv)
        self.assertNotIn('--model', argv)
        self.assertNotIn('--ignore-user-config', argv)
        self.assertNotIn('--dangerously-bypass-approvals-and-sandbox', argv)
        self.assertEqual(json.loads((self.output / 'result.json').read_text())['exit_code'], 0)
        self.assertNotIn('private-fixture-value', (self.output / 'plan.json').read_text())

    def test_enabled_mcp_after_overrides_prevents_model_launch(self):
        result = self.run_launcher('--execute', env=dict(self.env, LAUNCHER_IGNORE_MCP_DISABLE='1'))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('effective MCP configuration is still enabled', result.stderr)
        self.assertFalse(self.output.exists())
        self.assertFalse(self.called.exists())

    @unittest.skipUnless(shutil.which('codex'), 'Optional native CLI configuration check; no model')
    def test_native_cli_merges_server_overrides_and_disables_literal_names(self):
        native_home = self.base / 'native-config'
        native_home.mkdir()
        (native_home / 'config.toml').write_text(
            '[mcp_servers."offline.probe"]\ncommand = "/usr/bin/false"\n'
            '[mcp_servers."offline.probe".env]\nTOKEN = "private-fixture-value"\n')
        self.codex = Path(shutil.which('codex')).resolve()
        env = dict(self.env, CODEX_HOME=str(native_home))
        result = self.run_launcher(env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        preview = json.loads(result.stdout)
        self.assertEqual(preview['disabled_mcp_servers'], 1)
        argv = preview['argv'][:preview['argv'].index('exec')]
        resolved = subprocess.run([*argv, 'mcp', 'list', '--json'], cwd=self.project,
                                  env=env, capture_output=True, text=True, timeout=10)
        self.assertEqual(resolved.returncode, 0, resolved.stderr)
        servers = json.loads(resolved.stdout)
        self.assertEqual([(entry['name'], entry['enabled']) for entry in servers], [('offline.probe', False)])
        self.assertNotIn('private-fixture-value', result.stdout)
        self.assertFalse(self.output.exists())

    def test_native_failure_is_preserved_and_returned(self):
        result = self.run_launcher('--execute', env=dict(self.env, LAUNCHER_EXIT='7'))
        self.assertEqual(result.returncode, 7, result.stderr)
        self.assertEqual(json.loads((self.output / 'result.json').read_text())['child_exit_code'], 7)
        self.assertTrue((self.output / 'events.jsonl').exists())

    def test_previous_attempt_is_not_overwritten(self):
        self.output.mkdir()
        prior = self.output / 'result.json'
        prior.write_text('original failure')
        result = self.run_launcher('--execute')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(prior.read_text(), 'original failure')
        self.assertFalse(self.called.exists())

    def test_output_inside_project_is_rejected(self):
        self.output = self.project / 'evidence'
        result = self.run_launcher('--execute')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.output.exists())
        self.assertFalse(self.called.exists())

    def test_missing_git_does_not_fall_back_or_call_model(self):
        self.git = self.base / 'missing-git'
        result = self.run_launcher('--execute')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.output.exists())
        self.assertFalse(self.called.exists())

    def test_macos_launcher_uses_selected_developer_git(self):
        developer = self.base / 'developer'
        actual = developer / 'usr/bin/git'
        actual.parent.mkdir(parents=True)
        actual.symlink_to(self.git)
        with patch.object(launcher.sys, 'platform', 'darwin'), \
             patch.object(launcher, 'executable', side_effect=[Path('/usr/bin/git'), self.git]), \
             patch.object(launcher, 'capture', return_value=str(developer)) as capture:
            self.assertEqual(launcher.resolve_git('git', self.project, self.env), self.git)
        self.assertEqual(capture.call_args.args[0], ['/usr/bin/xcode-select', '-p'])

    def test_timeout_stops_owned_child_after_native_parent_exits(self):
        survived = self.base / 'survived'
        result = self.run_launcher('--execute', '--timeout', '0.3',
                                   env=dict(self.env, LAUNCHER_TIMEOUT='1', LAUNCHER_SURVIVED=str(survived)))
        self.assertEqual(result.returncode, 124, result.stderr)
        self.assertTrue(self.called.exists(), 'fixture must enter the native execution path')
        self.assertEqual(json.loads((self.output / 'result.json').read_text())['status'], 'timed_out')
        time.sleep(1.1)
        self.assertFalse(survived.exists(), 'child ignoring SIGTERM must not outlive the deadline')
        self.output = self.base / 'recovery'
        recovered = self.run_launcher('--execute')
        self.assertEqual(recovered.returncode, 0, recovered.stderr)
        self.assertEqual(json.loads((self.base / 'attempt/result.json').read_text())['exit_code'], 124)

    def test_interrupt_stops_owned_group_and_preserves_result(self):
        ready, survived = self.base / 'child-ready', self.base / 'survived'
        env = dict(self.env, LAUNCHER_TIMEOUT='1', LAUNCHER_CHILD_READY=str(ready),
                   LAUNCHER_SURVIVED=str(survived))
        argv = [sys.executable, '-B', str(SCRIPT), '--project', str(self.project),
                '--prompt-file', str(self.prompt), '--output', str(self.output),
                '--git', str(self.git), '--codex', str(self.codex), '--execute']
        process = subprocess.Popen(argv, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, start_new_session=True)
        try:
            deadline = time.monotonic() + 5
            while not ready.exists() and process.poll() is None and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue(ready.exists(), 'owned child must enter its SIGTERM-ignoring state')
            process.send_signal(signal.SIGINT)
            stdout, stderr = process.communicate(timeout=5)
            self.assertEqual(process.returncode, 130, stderr)
            self.assertEqual(json.loads((self.output / 'result.json').read_text())['status'], 'interrupted')
            time.sleep(1.1)
            self.assertFalse(survived.exists())
        finally:
            if process.poll() is None:
                process.kill()
            process.communicate(timeout=5)
            if self.called.exists():
                try:
                    os.killpg(json.loads(self.called.read_text())['pid'], signal.SIGKILL)
                except ProcessLookupError:
                    pass

    def test_nonfinite_or_unbounded_timeout_is_rejected(self):
        for value in ('nan', 'inf', '0', '-1', '301'):
            with self.subTest(value=value):
                result = self.run_launcher('--execute', '--timeout', value)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(self.called.exists())
                self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
