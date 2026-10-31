"""Project onboarding, personal tasks and mode changes without real platforms or hosts."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from test_workflow import Fixture
from twc_lib import actors, context, evidence, handoff, modes, policy, tasks, workspace
from twc_lib.models import WorkflowError, task_ref
import twc


class PersonalProject(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / 'project'
        self.root.mkdir()
        self.git('init', '-q', '-b', 'main')
        self.git('config', 'user.name', '67')
        self.git('config', 'user.email', '')
        self.git('config', 'core.hooksPath', str(self.root / 'no-hooks'))
        (self.root / 'a.txt').write_text('initial\n')
        self.git('add', 'a.txt')
        self.commit('initial')

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args], text=True, stderr=subprocess.PIPE).strip()

    def commit(self, message):
        self.git('-c', 'user.email=fixture@example.invalid', 'commit', '-qm', message)

    def cli(self, *args, root=None):
        return twc.run(twc.parser().parse_args(['--project', str(root or self.root), *args]))

    def setup_project(self, mode='personal'):
        self.cli('init', '--mode', mode, '--apply')
        config = self.root / '.team-workflow/config.toml'
        check = 'from pathlib import Path; assert Path("a.txt").read_text() == "initial\\n"'
        config.write_text(config.read_text() + '\n[checks.unit]\nargv = ' + json.dumps([sys.executable, '-c', check]) + '\n')
        contract = dict(goal='Keep the initial content readable', scope=['a.txt'], non_goals=[], dependencies=[],
                        contracts=[], complexity='L1', risk='normal',
                        acceptance=[dict(text='The content matches', checks=['unit'])])
        if mode == 'team':
            contract['integrator'] = 'reviewer'
        (self.root / 'contract.json').write_text(json.dumps(contract))
        self.git('add', '.team-workflow/config.toml', '.team-workflow/toolchain.lock.json',
                 '.team-workflow/.gitignore', 'contract.json')
        self.commit('workflow setup')

    def hashes(self):
        return {p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.root.rglob('*') if p.is_file() and '.git' not in p.relative_to(self.root).parts}

    def prepare(self, name='local:read-content'):
        return self.cli('prepare', '--task', name, '--contract', 'contract.json')

    def verify(self):
        sha = policy.load(self.root)[1]
        return self.cli('verify', '--execute', '--approved-policy', sha)

    def draft(self):
        return self.cli('handoff', '--draft', '--done', 'Content is verified', '--next', 'Continue the next feature')

    def test_first_use_requires_choice_and_subdirectory_reuses_it(self):
        before = self.hashes()
        for command in [('doctor', '--local'), ('resume',), ('mode',), ('init', '--apply')]:
            result = self.cli(*command)
            self.assertEqual(result['development_mode']['status'], 'selection_required')
            self.assertIsNone(result['development_mode']['current'])
        self.assertEqual(self.hashes(), before)
        self.assertFalse((self.root / '.team-workflow').exists())
        self.setup_project()
        sub = self.root / 'subdirectory'
        sub.mkdir()
        report = self.cli('doctor', '--local', root=sub)
        self.assertEqual(report['status'], 'ok')
        self.assertEqual(report['development_mode']['current'], 'personal')
        self.assertNotIn('choose_development_mode', report['next_steps'])
        self.assertNotIn('coordination', policy.load(self.root)[0])
        self.assertEqual(self.git('remote'), '')
        self.assertEqual(self.git('config', '--get', 'user.email'), '')

    def test_personal_end_to_end_needs_no_platform_or_email(self):
        self.setup_project()
        with patch.object(context, 'provider', side_effect=AssertionError('network forbidden')), \
                patch.object(actors, 'from_config', side_effect=AssertionError('network forbidden')):
            prepared = self.prepare()
            self.assertEqual(prepared['task_ref']['type'], 'local')
            self.assertEqual(prepared['platform_status'], 'not_applicable')
            self.assertEqual(self.verify()['status'], 'passed')
            draft = self.draft()
            self.assertEqual(draft['readiness'], 'advisory_ready')
            self.assertEqual(draft['readiness_scope'], 'local_task')
            self.assertFalse(draft['merge_authorized'])
            self.assertEqual(draft['actor']['member']['name'], '67')
            self.assertEqual(draft['actor']['git']['status'], 'incomplete')
            self.assertFalse(actors.attributed(draft['actor']))
            self.assertEqual(self.cli('resume')['checks']['unit']['status'], 'passed')
            self.assertEqual(self.cli('check')['status'], 'ok')
        (self.root / 'a.txt').write_text('changed\n')
        self.assertEqual(self.cli('resume')['checks']['unit']['status'], 'stale')
        self.assertEqual(self.verify()['status'], 'failed')

    def test_mode_change_preserves_history_checks_binding_and_invalidates_evidence(self):
        self.setup_project()
        self.prepare()
        self.verify()
        before = self.hashes()
        config, sha = policy.load(self.root)
        preview = self.cli('mode', '--set', 'team')
        self.assertEqual(preview['current_task']['task'], 'local:read-content')
        self.assertEqual(self.hashes(), before)
        with self.assertRaisesRegex(WorkflowError, 'approval'):
            self.cli('mode', '--set', 'team', '--apply')
        self.assertEqual(self.hashes(), before)
        self.cli('mode', '--set', 'team', '--apply', '--approved-policy', sha)
        after = self.hashes()
        self.assertEqual([p for p in before if before[p] != after[p]], ['.team-workflow/config.toml'])
        updated = policy.load(self.root)[0]
        self.assertEqual(updated['checks'], config['checks'])
        self.assertEqual(updated['project_id'], config['project_id'])
        self.assertEqual(self.cli('resume')['checks']['unit']['status'], 'stale')
        with self.assertRaisesRegex(WorkflowError, 'integrator'):
            self.cli('prepare', '--task', 'local:next-team-task', '--contract', 'contract.json', '--rebind')

    def test_team_contract_review_survives_switch_to_personal(self):
        self.setup_project('team')
        self.prepare()
        sha = policy.load(self.root)[1]
        self.cli('mode', '--set', 'personal', '--apply', '--approved-policy', sha)
        self.git('add', '.team-workflow/config.toml')
        self.commit('change default workflow')
        self.verify()
        draft = self.draft()
        self.assertEqual(draft['integrator'], 'reviewer')
        self.assertIn('task_integrator_review_required', draft['unknowns'])
        self.assertEqual(draft['readiness'], 'unknown')
        self.assertFalse(draft['merge_authorized'])

    def test_mode_change_does_not_overwrite_concurrent_config_edits(self):
        self.setup_project()
        sha = self.cli('mode', '--set', 'team')['policy_sha256']
        config = self.root / '.team-workflow/config.toml'
        config.write_text(config.read_text() + '\n# Reviewed local note\n')
        before = config.read_bytes()
        with self.assertRaisesRegex(WorkflowError, 'approval'):
            self.cli('mode', '--set', 'team', '--apply', '--approved-policy', sha)
        self.assertEqual(config.read_bytes(), before)

    def test_new_project_requires_its_own_choice(self):
        self.setup_project()
        other = self.root.parent / 'other'
        other.mkdir()
        subprocess.check_call(['git', '-C', str(other), 'init', '-q'])
        report = self.cli('resume', root=other)
        self.assertEqual(report['development_mode']['status'], 'selection_required')
        self.assertFalse((other / '.team-workflow').exists())

    def test_same_mode_is_idempotent_and_platform_can_be_added_explicitly(self):
        self.setup_project()
        self.prepare()
        config, sha = policy.load(self.root)
        before = self.hashes()
        result = self.cli('mode', '--set', 'personal', '--apply', '--approved-policy', sha)
        self.assertFalse(result['changed'])
        self.assertEqual(self.hashes(), before)
        self.cli('mode', '--set', 'team', '--provider', 'cnb', '--base-url', 'https://cnb.cool',
                 '--repository', 'team/project', '--apply', '--approved-policy', sha)
        updated = policy.load(self.root)[0]
        self.assertEqual(updated['project_id'], config['project_id'])
        self.assertEqual(updated['checks'], config['checks'])
        self.assertEqual(updated['coordination']['provider'], 'cnb')
        self.assertEqual(self.cli('resume')['task_ref']['type'], 'local')
        after = self.hashes()
        self.assertEqual([p for p in before if before[p] != after[p]], ['.team-workflow/config.toml'])

    def test_invalid_mode_and_symlink_config_are_not_silently_initialized(self):
        with self.assertRaisesRegex(WorkflowError, 'explicitly'):
            policy.init(self.root, None, None, 'main', apply=True)
        self.assertFalse((self.root / '.team-workflow').exists())
        self.setup_project()
        path = self.root / '.team-workflow/config.toml'
        original = path.read_text()
        path.write_text(original.replace('development_mode = "personal"', 'development_mode = "unknown"'))
        report = self.cli('doctor', '--local')
        self.assertEqual(report['development_mode']['status'], 'unavailable')
        self.assertNotIn('choose_development_mode', report['next_steps'])
        path.write_text(original)
        sha = policy.load(self.root)[1]
        target = self.root / 'config-copy.toml'
        path.rename(target)
        path.symlink_to(Path('..') / 'config-copy.toml')
        self.assertTrue(path.is_symlink())
        self.assertTrue(path.exists())
        with self.assertRaises(WorkflowError):
            self.cli('mode', '--set', 'team', '--apply', '--approved-policy', sha)
        self.assertEqual(target.read_text(), original)

    def test_personal_task_survives_clone_without_local_binding(self):
        self.setup_project()
        self.prepare()
        self.verify()
        self.draft()
        self.git('add', '.team-workflow/tasks/local-read-content')
        self.commit('record task')
        clone = self.root.parent / 'clone'
        self.git('clone', '-q', str(self.root), str(clone))
        self.assertFalse((clone / '.team-workflow/local').exists())
        report = self.cli('resume', root=clone)
        self.assertEqual(report['resolved_by'], 'branch_changes')
        self.assertEqual(report['development_mode']['current'], 'personal')
        self.assertEqual(report['handed_off_by']['member']['name'], '67')

    def test_local_task_identity_and_slug_cannot_escape_or_cross_projects(self):
        self.setup_project()
        config, sha = policy.load(self.root)
        for name in ('local:../outside', 'local:/absolute', 'local:', 'local:bad/name'):
            with self.assertRaises(WorkflowError):
                task_ref(config, name)
        self.prepare()
        path = self.root / '.team-workflow/local/binding.json'
        bound = json.loads(path.read_text())
        bound['task_ref']['project_id'] = '0' * 32
        path.write_text(json.dumps(bound))
        with self.assertRaisesRegex(WorkflowError, 'another configured'):
            self.cli('resume')


class ExistingTeamModes(Fixture):
    def test_legacy_configuration_remains_team_and_upgrade_preserves_settings(self):
        path = self.root / '.team-workflow/config.toml'
        config, _ = self.configuration()
        config['schema_version'] = 1
        config['workflow_owner'] = 'team-workflow-craft'
        config.pop('development_mode')
        config.pop('project_id')
        path.write_text(modes.config_text(config))
        before = path.read_bytes()
        self.assertEqual(twc.local_doctor(self.root)['development_mode']['source'], 'legacy_team_config')
        self.assertEqual(path.read_bytes(), before)
        _, sha = self.configuration()
        modes.change(self.root, 'personal', apply=True, approved_policy=sha)
        updated, _ = self.configuration()
        for key in ('coordination', 'integration', 'permissions', 'checks', 'workflow_owner'):
            self.assertEqual(updated[key], config[key])

    def test_platform_task_does_not_become_local_after_mode_change(self):
        self.prepare()
        before = (self.root / '.team-workflow/tasks/pr-3/task.json').read_bytes()
        _, sha = self.configuration()
        modes.change(self.root, 'personal', apply=True, approved_policy=sha)
        self.assertEqual((self.root / '.team-workflow/tasks/pr-3/task.json').read_bytes(), before)
        self.verify()
        draft = self.draft()
        self.assertEqual(draft['readiness_scope'], 'platform_handoff')
        self.assertIn('platform_not_current', draft['unknowns'])
        self.assertIn('handoff_actor_unverified', draft['unknowns'])
        self.assertFalse(draft['merge_authorized'])

    def test_existing_platform_cannot_be_replaced_by_mode_switch(self):
        before = (self.root / '.team-workflow/config.toml').read_bytes()
        _, sha = self.configuration()
        with self.assertRaisesRegex(WorkflowError, 'cannot replace'):
            modes.change(self.root, 'team', apply=True, approved_policy=sha,
                         provider='cnb', base_url='https://cnb.cool', repository='other/project')
        self.assertEqual((self.root / '.team-workflow/config.toml').read_bytes(), before)
