"""Local member setup check stays read-only and independent of the collaboration platform."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

PACKAGE = Path(__file__).resolve().parents[1]
SCRIPTS = PACKAGE / 'skills/workflow-craft/scripts'
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location('twc_local_doctor_test', SCRIPTS / 'twc.py')
twc = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(twc)


class LocalDoctorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='twc-local-doctor-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.project = self.root / 'project'
        self.project.mkdir()
        self.env = {key: value for key, value in os.environ.items()
                    if key in ('PATH', 'HOME', 'USER', 'LOGNAME', 'TMPDIR', 'TMP', 'TEMP', 'LANG', 'LC_ALL', 'SYSTEMROOT')}
        self.env.update(PYTHONDONTWRITEBYTECODE='1', GIT_CONFIG_GLOBAL=os.devnull,
                        GIT_CONFIG_SYSTEM=os.devnull, GIT_CONFIG_COUNT='0', GIT_TERMINAL_PROMPT='0')
        self.git('init', '-q', '-b', 'main')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        (self.project / 'check.py').write_text('assert True\n')
        self.git('add', 'check.py')
        self.git('-c', 'core.hooksPath=' + str(self.root / 'no-hooks'), '-c', 'commit.gpgSign=false',
                 'commit', '-qm', 'fixture')

    def git(self, *args):
        subprocess.run(['git', '-C', str(self.project), *args], env=self.env, check=True,
                       capture_output=True, timeout=15)

    def cli(self, *args, expected=0):
        result = subprocess.run([sys.executable, str(SCRIPTS / 'twc.py'), '--project', str(self.project), *args],
                                env=self.env, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def configure(self):
        twc.policy.init(self.project, 'https://cnb.cool', 'fixture/project', 'main', apply=True, provider='cnb', mode='team')

    def snapshot(self):
        return {str(path.relative_to(self.project)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in self.project.rglob('*') if path.is_file() and not path.is_symlink()}

    def test_before_init_reports_missing_setup_without_writing(self):
        before = self.snapshot()
        report = self.cli('doctor', '--local', expected=1)
        self.assertEqual(report['scope'], 'member_local_preflight')
        self.assertEqual(report['project_config'], 'missing')
        self.assertEqual(report['toolchain']['status'], 'missing')
        self.assertEqual(report['platform']['status'], 'not_requested')
        self.assertIn('initialize_project', report['next_steps'])
        self.assertFalse((self.project / '.team-workflow').exists())
        self.assertEqual(self.snapshot(), before)

    def test_configured_workflow_does_not_claim_runtime_or_host_acceptance(self):
        self.configure()
        before = self.snapshot()
        real_run = subprocess.run

        def git_only(argv, *args, **kwargs):
            # Read-only Git inspection is allowed; no project checks, network or other tools.
            self.assertEqual(argv[0], 'git')
            self.assertNotIn('fetch', argv)
            return real_run(argv, *args, **kwargs)

        with patch('subprocess.run', side_effect=git_only):
            report = twc.local_doctor(self.project)
        self.assertEqual(report['status'], 'ok' if os.name == 'posix' else 'attention_required')
        self.assertEqual(report['project_config'], 'valid')
        self.assertEqual(report['toolchain']['status'], 'matched')
        self.assertEqual(report['base_ref']['status'], 'resolved')
        self.assertEqual(report['host_loading'], 'unverified')
        self.assertEqual(self.snapshot(), before)

    def test_missing_name_prompts_before_and_after_init_without_writing(self):
        self.git('config', '--unset', 'user.name')
        self.git('config', '--unset', 'user.email')
        for configured in (False, True):
            with self.subTest(configured=configured):
                if configured:
                    self.configure()
                before = self.snapshot()
                report = self.cli('doctor', '--local', expected=1)
                self.assertEqual(report['status'], 'attention_required')
                self.assertEqual(report['member']['status'], 'missing')
                self.assertIsNone(report['member']['name'])
                self.assertTrue(report['member']['message'])
                self.assertIn('configure_member_name', report['next_steps'])
                self.assertEqual(report['platform']['status'], 'not_requested')
                self.assertEqual(self.snapshot(), before)

    def test_name_alone_is_sufficient_and_current_member_is_read_each_time(self):
        self.configure()
        self.git('config', '--unset', 'user.email')
        for name in ('67', '小王'):
            with self.subTest(name=name):
                self.git('config', 'user.name', name)
                before = self.snapshot()
                report = self.cli('doctor', '--local', expected=0 if os.name == 'posix' else 1)
                self.assertEqual(report['member']['status'], 'available')
                self.assertEqual(report['member']['name'], name)
                self.assertNotIn('configure_member_name', report['next_steps'])
                self.assertEqual(self.snapshot(), before)
        # Name-only onboarding does not assert that a complete commit identity exists.
        full = self.cli('doctor', expected=1)
        self.assertEqual(full['actor']['git']['status'], 'incomplete')

    def test_existing_global_name_is_reused_and_local_name_takes_precedence(self):
        self.configure()
        self.git('config', '--unset', 'user.name')
        global_config = self.root / 'global.gitconfig'
        self.env['GIT_CONFIG_GLOBAL'] = str(global_config)
        self.git('config', '--global', 'user.name', 'Global Member')
        global_before = global_config.read_bytes()
        for name in ('Global Member', 'Local Member'):
            with self.subTest(name=name):
                if name == 'Local Member':
                    self.git('config', '--local', 'user.name', name)
                before = self.snapshot()
                report = self.cli('doctor', '--local', expected=0 if os.name == 'posix' else 1)
                self.assertEqual(report['member']['name'], name)
                self.assertNotIn('configure_member_name', report['next_steps'])
                self.assertEqual(self.snapshot(), before)
                self.assertEqual(global_config.read_bytes(), global_before)

    def test_resume_reminds_without_blocking_or_writing_in_all_task_states(self):
        self.configure()
        self.git('config', '--unset', 'user.name')
        self.git('config', '--unset', 'user.email')
        cases = [('no_task', ()), ('no_task_record', ('--task', 'pr:9')), ('ok', ())]
        for status, arguments in cases:
            with self.subTest(status=status):
                if status == 'ok':
                    self.cli('prepare', '--task', 'pr:9', '--offline')
                before = self.snapshot()
                report = self.cli('resume', *arguments)
                self.assertEqual(report['status'], status)
                self.assertEqual(report['member']['status'], 'missing')
                self.assertTrue(report['member']['message'])
                self.assertIn('configure_member_name', report['next_actions'])
                self.assertGreater(len(report['next_actions']), 1)
                self.assertEqual(self.snapshot(), before)
        self.git('config', 'user.name', '67')
        before = self.snapshot()
        report = self.cli('resume')
        self.assertEqual(report['member']['name'], '67')
        self.assertNotIn('configure_member_name', report['next_actions'])
        self.assertEqual(self.snapshot(), before)

    def test_email_or_invalid_name_cannot_replace_member_name(self):
        self.configure()
        for name in ('', '   ', 'invalid\nname'):
            with self.subTest(name=name):
                self.git('config', 'user.name', name)
                before = self.snapshot()
                report = self.cli('doctor', '--local', expected=1)
                self.assertEqual(report['member']['status'], 'missing')
                self.assertIsNone(report['member']['name'])
                self.assertIn('configure_member_name', report['next_steps'])
                self.assertEqual(self.snapshot(), before)

    def test_invalid_config_and_lock_are_actionable_without_echoing_content(self):
        self.configure()
        config = self.project / '.team-workflow/config.toml'
        original = config.read_text()
        config.write_text('private_marker_do_not_echo = [invalid')
        report = self.cli('doctor', '--local', expected=1)
        self.assertEqual(report['project_config'], 'invalid')
        self.assertNotIn('private_marker_do_not_echo', json.dumps(report))
        config.write_text(original)
        (self.project / '.team-workflow/toolchain.lock.json').write_text('{broken')
        report = self.cli('doctor', '--local', expected=1)
        self.assertEqual(report['toolchain']['status'], 'invalid')
        self.assertIn('review_toolchain_lock', report['next_steps'])

    def test_project_entry_parent_link_does_not_scan_external_profile(self):
        self.configure()
        external = self.root / 'external'
        outside_skill = external / 'skills/workflow-craft'
        outside_skill.mkdir(parents=True)
        (outside_skill / 'VERSION').write_text('9.9.9\n')
        (outside_skill / 'SKILL.md').write_text('External profile must not be scanned\n')
        (self.project / '.agents').symlink_to(external, target_is_directory=True)
        original = twc.policy.runtime_identity

        def local_identity(path=None):
            self.assertIsNone(path, 'must not hash a linked project entry')
            return original()

        with patch.object(twc.policy, 'runtime_identity', side_effect=local_identity):
            report = twc.local_doctor(self.project)
        self.assertEqual(report['status'], 'attention_required')
        self.assertTrue(report['project_entries'][0]['symlink'])
        report = self.cli('doctor', expected=1)
        self.assertTrue(report['project_entries'][0]['symlink'])

    def test_unsafe_state_path_is_reported_without_following_it(self):
        external = self.root / 'external'
        external.mkdir()
        (self.project / '.team-workflow').symlink_to(external, target_is_directory=True)
        report = self.cli('doctor', '--local', expected=1)
        self.assertEqual(report['project_config'], 'unsafe_path')
        self.assertEqual(list(external.iterdir()), [])

    def test_windows_process_family_remains_unqualified(self):
        self.configure()
        with patch.object(twc, 'os', SimpleNamespace(name='nt')):
            report = twc.local_doctor(self.project)
        self.assertEqual(report['status'], 'attention_required')
        self.assertEqual(report['verification']['implementation'], 'unsupported')
        self.assertIn('qualify_native_process_tree_verification', report['next_steps'])

    def test_local_and_online_diagnosis_are_mutually_exclusive(self):
        result = subprocess.run([sys.executable, str(SCRIPTS / 'twc.py'), '--project', str(self.project),
                                 'doctor', '--local', '--online'], env=self.env,
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.project / '.team-workflow').exists())


if __name__ == '__main__':
    unittest.main()
