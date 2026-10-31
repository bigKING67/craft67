"""Status adapters read the configured mode without running the workflow."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

RUNTIME = Path(__file__).resolve().parents[1] / 'skills/workflow-craft/scripts'
sys.path.insert(0, str(RUNTIME))
from twc_lib import policy, statusline


class StatuslineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / '项目 with spaces'
        self.root.mkdir()
        self.env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull,
                        GIT_CONFIG_COUNT='0', PYTHONDONTWRITEBYTECODE='1')
        self.git('init', '-q', '-b', 'main')

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args], env=self.env,
                                       stderr=subprocess.PIPE, text=True).strip()

    def configure(self, mode='personal'):
        policy.init(self.root, '', '', 'main', apply=True, mode=mode)
        return self.root / '.team-workflow/config.toml'

    def cli(self, *args, data=None):
        result = subprocess.run([sys.executable, '-B', str(RUNTIME / 'workflow_status.py'), *args],
                                cwd=self.root, input=data, capture_output=True, text=True,
                                timeout=5, env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')
        return result.stdout.strip()

    def test_missing_mode_never_guesses_or_initializes(self):
        self.assertEqual(self.cli('--project', str(self.root)), 'Workflow: 未配置')
        self.assertFalse((self.root / '.team-workflow').exists())

    def test_mode_refresh_subdirectory_and_nested_project(self):
        config = self.configure()
        sub = self.root / 'sub'
        sub.mkdir()
        self.assertEqual(self.cli('--project', str(sub)), 'Workflow: solo')
        config.write_text(config.read_text().replace('"personal"', '"team"'))
        self.assertEqual(self.cli('--project', str(sub)), 'Workflow: team')
        nested = sub / 'nested'
        nested.mkdir()
        subprocess.check_call(['git', '-C', str(nested), 'init', '-q'], env=self.env)
        self.assertEqual(self.cli('--project', str(nested)), 'Workflow: 未配置')

    def test_linked_worktree_reads_its_own_config(self):
        self.configure()
        self.git('add', '.team-workflow/config.toml')
        self.git('-c', 'user.name=fixture', '-c', 'user.email=fixture@example.invalid',
                 '-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'fixture')
        other = self.root.parent / 'linked'
        self.git('worktree', 'add', '-qb', 'other', str(other))
        config = other / '.team-workflow/config.toml'
        config.write_text(config.read_text().replace('"personal"', '"team"'))
        self.assertEqual(self.cli('--project', str(other)), 'Workflow: team')
        self.assertEqual(self.cli('--project', str(self.root)), 'Workflow: solo')

    def test_legacy_configuration_keeps_team_meaning(self):
        policy.init(self.root, 'https://cnb.cool', 'example/project', 'main',
                    provider='cnb', apply=True, mode='team')
        config = self.root / '.team-workflow/config.toml'
        lines = config.read_text().replace('schema_version = 2', 'schema_version = 1').splitlines()
        config.write_text('\n'.join(line for line in lines
                                    if not line.startswith(('development_mode', 'project_id'))))
        self.assertEqual(self.cli('--project', str(self.root)), 'Workflow: team')

    def test_invalid_configuration_reports_fixed_error(self):
        config = self.configure()
        valid = config.read_text()
        for content in ('not a config [', valid.replace('"personal"', '"bad-secret-value"'),
                        valid.replace('development_mode = "personal"', ''),
                        valid.replace('auto_commit = false', 'auto_commit = true')):
            with self.subTest(content=content[:20]):
                config.write_text(content)
                self.assertEqual(self.cli('--project', str(self.root)), 'Workflow: 配置错误')

    def test_symlink_is_not_followed(self):
        config = self.configure()
        target = self.root / 'elsewhere.toml'
        config.rename(target)
        config.symlink_to(target)
        self.assertEqual(self.cli('--project', str(self.root)), 'Workflow: 配置错误')
        config.unlink()
        target.rename(config)
        directory = config.parent
        moved = self.root / 'elsewhere'
        directory.rename(moved)
        directory.symlink_to(moved, target_is_directory=True)
        self.assertEqual(self.cli('--project', str(self.root)), 'Workflow: 配置错误')

    def test_claude_uses_current_workspace_then_cwd(self):
        self.configure()
        sub = self.root / 'sub'
        sub.mkdir()
        other = self.root.parent / 'empty'
        other.mkdir()
        data = dict(cwd=str(other), workspace=dict(current_dir=str(sub), project_dir=str(other)))
        self.assertEqual(self.cli('--claude', data=json.dumps(data)), 'Workflow: solo')
        self.assertEqual(self.cli('--claude', data=json.dumps(dict(cwd=str(sub)))), 'Workflow: solo')

    def test_claude_malformed_input_does_not_fall_back_to_process_cwd(self):
        self.configure()
        for data in ('invalid secret', '{}', '[]', '{"cwd": 123}', '{"cwd": "\\u0000"}',
                     ' ' * (64 * 1024 + 1)):
            self.assertEqual(self.cli('--claude', data=data), 'Workflow: 不可用')

    def test_claude_deeply_nested_input_is_unavailable(self):
        self.configure()
        data = '[' * 2000 + '0' + ']' * 2000
        self.assertEqual(self.cli('--claude', data=data), 'Workflow: 不可用')

    def test_no_writes_or_check_execution_or_network(self):
        config = self.configure()
        config.write_text(config.read_text() + '\n[checks.never]\nargv = ["must-not-execute"]\n')
        def snapshot():
            return {str(p.relative_to(self.root)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in self.root.rglob('*') if p.is_file()}
        before = snapshot()
        with patch('urllib.request.OpenerDirector.open', side_effect=AssertionError('network forbidden')):
            self.assertEqual(statusline.render(str(self.root)), 'Workflow: solo')
        self.assertEqual(self.cli('--project', str(self.root)), 'Workflow: solo')
        self.assertEqual(snapshot(), before)

    def test_unavailable_git_timeout_and_invalid_paths_are_bounded(self):
        for error in (FileNotFoundError('secret path'), subprocess.TimeoutExpired('git', 1)):
            with patch.object(statusline.subprocess, 'run', side_effect=error):
                self.assertEqual(statusline.render(str(self.root)), 'Workflow: 不可用')
        for path in (None, '', 123, '\0'):
            self.assertEqual(statusline.render(path), 'Workflow: 不可用')
        config = self.configure()
        config.write_bytes(b' ' * (1024 * 1024 + 1))
        self.assertEqual(self.cli('--project', str(self.root)), 'Workflow: 不可用')

    def test_pi_adapter_events_without_host_or_model(self):
        node = shutil.which('node')
        if not node:
            self.skipTest('Pi adapter requires Node 22.18+; Python CLI remains independent')
        version = tuple(map(int, subprocess.check_output([node, '-p', 'process.versions.node'], text=True).strip().split('.')))
        if version < (22, 18, 0):
            self.skipTest('Pi adapter contract test requires Node 22.18+')
        self.configure()
        test = Path(__file__).with_name('statusline.test.mjs')
        result = subprocess.run([node, str(test), str(self.root)],
                                env=dict(self.env, WORKFLOW_CRAFT_PYTHON=sys.executable),
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('Pi status adapter: passed', result.stdout)
