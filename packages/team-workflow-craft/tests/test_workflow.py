"""Behavior regressions using isolated Git repositories, never live services."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

PACKAGE = Path(__file__).resolve().parents[1]
RUNTIME = PACKAGE / 'skills/team-workflow-craft/scripts'
sys.path.insert(0, str(RUNTIME))
from twc_lib import actors, context, evidence, handoff, policy, workspace
from twc_lib.models import WorkflowError
from twc_lib.providers.gitea import Gitea, ProviderError
from twc_lib.providers import CNB
import twc


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / 'project'
        self.root.mkdir()
        self.git('init', '-q', '-b', 'main')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'core.hooksPath', str(self.root / 'no-hooks'))
        self.git('remote', 'add', 'origin', 'https://gitea.example.invalid/team/product.git')
        (self.root / 'a.txt').write_text('initial\n')
        self.git('add', 'a.txt')
        self.git('commit', '-qm', 'initial')
        self.base = self.git('rev-parse', 'HEAD')
        policy.init(self.root, 'https://gitea.example.invalid', 'team/product', self.base, apply=True)
        self.checks([('unit', 'print("ok")', 5)])
        self.contract = dict(goal='Deliver a feature', non_goals=['deployment'], scope=['a.txt'],
                             dependencies=[], acceptance=[dict(text='unit passes', checks=['unit'])], integrator='maintainer',
                             contracts=[], complexity='L1', risk='normal')
        (self.root / 'contract.json').write_text(json.dumps(self.contract))
        self.git('add', '.team-workflow/config.toml', '.team-workflow/toolchain.lock.json',
                 '.team-workflow/.gitignore', 'contract.json')
        self.git('commit', '-qm', 'workflow config')

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args], text=True, stderr=subprocess.PIPE).strip()

    def checks(self, rows):
        path = self.root / '.team-workflow/config.toml'
        base = path.read_text().split('[checks.')[0]
        for name, script, timeout in rows:
            base += f'\n[checks.{name}]\nargv = {json.dumps([sys.executable, "-c", script])}\ncwd = "."\ntimeout_seconds = {timeout}\n'
        path.write_text(base)

    def configuration(self):
        return policy.load(self.root)

    def use_cnb(self):
        path = self.root / '.team-workflow/config.toml'
        path.write_text(path.read_text().replace('provider = "gitea"', 'provider = "cnb"')
                        .replace('https://gitea.example.invalid', 'https://cnb.cool')
                        .replace('TWC_GITEA_TOKEN', 'TWC_CNB_TOKEN'))
        self.git('remote', 'set-url', 'origin', 'https://cnb.cool/team/product.git')
        self.git('add', '.team-workflow/config.toml')
        self.git('commit', '-qm', 'CNB configuration')

    def prepare(self, task='pr:3', **kwargs):
        config, sha = self.configuration()
        return context.prepare(self.root, config, sha, task, 'contract.json', offline=True, **kwargs)

    def verify(self, **kwargs):
        config, sha = self.configuration()
        return evidence.verify(self.root, config, sha, execute_commands=True, approved_policy=sha, **kwargs)

    def draft(self, online=False, task=None):
        config, sha = self.configuration()
        return handoff.draft(self.root, config, sha, task, ['feature complete'], [], ['review and integrate'], online)


class WorkflowTests(Fixture):
    def test_cnb_doctor_reports_supported_reads_without_inventing_server_version(self):
        self.use_cnb()
        config, sha = self.configuration()
        identity = dict(id='18446744073709551616', login='sixseven', full_name='成员')
        with patch.object(CNB, 'get_identity', return_value=identity) as who:
            with patch.object(CNB, 'get_repository', return_value=dict(path='team/product', visibility_level='private')):
                report = twc.doctor(self.root, config, sha, online=True)
        self.assertEqual(who.call_count, 1)
        self.assertEqual(report['status'], 'ok')
        self.assertEqual(report['platform']['version']['status'], 'unsupported')
        self.assertEqual(report['workspace']['repository_identity'], 'matched')
        self.assertEqual(report['actor']['platform']['provider'], 'cnb')
        self.assertEqual(report['actor']['platform']['data']['id'], identity['id'])

    def test_cnb_task_verify_handoff_keep_separate_operator_identities(self):
        self.use_cnb()
        config, sha = self.configuration()
        identities = [dict(id=str(i), login=login) for i, login in enumerate(('alice', 'bob', 'sixseven'), 1)]
        with patch.object(CNB, 'get_identity', side_effect=identities):
            with patch.object(CNB, 'get_task', return_value=dict(number='8', assignees=[{'username': 'alice'}])):
                packet = context.prepare(self.root, config, sha, 'issue:8', 'contract.json')
            record = self.verify(online=True)
            with patch.object(CNB, 'get_task', return_value=dict(number='8')):
                result = self.draft(online=True)
        self.assertEqual(result['task_ref']['provider'], 'cnb')
        self.assertEqual(result['prepared_by']['platform']['data']['login'], 'alice')
        self.assertEqual(result['checks']['unit']['actor']['platform']['data']['login'], 'bob')
        self.assertEqual(result['actor']['platform']['data']['login'], 'sixseven')
        self.assertEqual(result['readiness'], 'unknown')
        self.assertFalse(result['merge_authorized'])
        self.assertIn('issue_has_no_verified_delivery_pr', result['unknowns'])
        self.assertFalse(actors.attributed(result['actor'], 'https://cnb.cool', 'gitea'))
        bound = self.root / '.team-workflow/local/binding.json'
        saved = json.loads(bound.read_text())
        saved['task_ref']['provider'] = 'gitea'
        bound.write_text(json.dumps(saved))
        with self.assertRaisesRegex(WorkflowError, 'another configured'):
            self.draft()

    def test_provider_switch_rejects_stale_binding_before_execution(self):
        self.prepare()
        self.use_cnb()
        self.checks([('marker', 'open("must-not-run", "w").write("x")', 5)])
        with self.assertRaisesRegex(WorkflowError, 'another platform/repository'):
            self.verify()
        self.assertFalse((self.root / 'must-not-run').exists())

    def test_cnb_default_token_and_other_platform_token_are_removed_from_checks(self):
        self.use_cnb()
        path = self.root / '.team-workflow/config.toml'
        path.write_text(path.read_text().replace('token_env = "TWC_CNB_TOKEN"\n', ''))
        self.checks([('no_secrets', 'import os; assert "TWC_CNB_TOKEN" not in os.environ; '
                     'assert "TWC_GITEA_TOKEN" not in os.environ', 5)])
        with patch.dict(os.environ, TWC_CNB_TOKEN='fixture-cnb', TWC_GITEA_TOKEN='fixture-gitea'):
            result = self.verify()
        self.assertEqual(result['status'], 'passed')
        self.assertNotIn('fixture-cnb', json.dumps(result))

    def test_cnb_custom_identity_token_is_not_inherited_by_project_tests(self):
        self.use_cnb()
        path = self.root / '.team-workflow/config.toml'
        path.write_text(path.read_text().replace('token_env = "TWC_CNB_TOKEN"',
                        'token_env = "TWC_CNB_TOKEN"\nidentity_token_env = "TWC_IDENTITY_FIXTURE"'))
        self.checks([('no_identity_token', 'import os; assert "TWC_IDENTITY_FIXTURE" not in os.environ; '
                     'assert "TWC_CNB_IDENTITY_TOKEN" not in os.environ', 5)])
        with patch.dict(os.environ, TWC_IDENTITY_FIXTURE='identity-only', TWC_CNB_IDENTITY_TOKEN='standard-identity'):
            result = self.verify()
        self.assertEqual(result['status'], 'passed')
        self.assertIn('separate_identity_token', result['actor']['platform']['credential_binding'])

    def test_init_preview_has_no_side_effects_and_existing_config_is_protected(self):
        other = self.root.parent / 'other'
        other.mkdir()
        plan = policy.init(other, 'https://gitea.example.invalid', 'team/product', 'main')
        self.assertFalse(plan['applied'])
        self.assertEqual(list(other.iterdir()), [])
        with self.assertRaises(WorkflowError):
            policy.init(self.root, 'https://gitea.example.invalid', 'team/product', 'main', apply=True)

    def test_snapshot_reads_entire_git_root_and_binds_dirty_content(self):
        (self.root / 'other-package').mkdir()
        file = self.root / 'other-package/wip.txt'
        file.write_text('first')
        first = workspace.inspect(self.root, self.base, ['a.txt'])
        file.write_text('second')
        second = workspace.inspect(self.root, self.base, ['a.txt'])
        self.assertIn('other-package/wip.txt', first['outside_scope'])
        self.assertNotEqual(first['tree_sha256'], second['tree_sha256'])
        self.assertEqual(first['head'], second['head'])
        self.assertEqual(workspace.root_for(self.root / 'other-package'), self.root)

    def test_staged_rename_and_untracked_spaces_are_preserved(self):
        self.git('mv', 'a.txt', 'renamed file.txt')
        (self.root / 'untracked file.txt').write_text('x')
        snap = workspace.inspect(self.root, self.base)
        rename = next(row for row in snap['changes'] if row['path'] == 'renamed file.txt')
        self.assertEqual(rename['from'], 'a.txt')
        self.assertIn('untracked file.txt', [row['path'] for row in snap['changes']])

    def test_remotes_do_not_leak_userinfo_or_query(self):
        self.git('remote', 'set-url', 'origin', 'https://user:secret@git.example/team/project.git?token=hidden')
        snap = workspace.inspect(self.root, self.base)
        self.assertEqual(snap['remotes']['origin'], 'https://git.example/team/project.git')

    def test_task_binding_is_local_and_requires_explicit_switch(self):
        packet = self.prepare()
        self.assertEqual(packet['platform_status'], 'offline')
        self.assertFalse(workspace.inspect(self.root, self.base)['dirty'])
        with self.assertRaises(WorkflowError):
            self.prepare('issue:4')
        changed = self.prepare('issue:4', rebind=True)
        self.assertEqual(changed['task_ref']['number'], 4)

    def test_contract_owner_is_rejected(self):
        value = dict(self.contract, owner='another-owner')
        (self.root / 'contract.json').write_text(json.dumps(value))
        with self.assertRaises(WorkflowError):
            self.prepare()

    def test_wrong_repository_is_not_bound_to_task(self):
        self.git('remote', 'set-url', 'origin', 'https://gitea.example.invalid/other/product.git')
        with self.assertRaises(WorkflowError):
            self.prepare()

    def test_ssh_alias_does_not_claim_verified_repository(self):
        self.git('remote', 'set-url', 'origin', 'git@company-alias:team/product.git')
        packet = self.prepare()
        record = self.verify()
        result = self.draft()
        self.assertIn('git_remote_identity_unverified', result['unknowns'])

    def test_installed_marker_detects_content_drift(self):
        target = self.root.parent / 'installed'
        target.mkdir()
        (target / 'file').write_text('changed')
        (target / '.twc-install.json').write_text(json.dumps(dict(schema='team-workflow-craft.install.v1',
            files=[dict(path='file', sha256='0'*64, size=7)])))
        self.assertEqual(policy.installation_integrity(target), 'mismatch')

    def test_prepare_without_contract_is_explicitly_incomplete(self):
        config, sha = self.configuration()
        packet = context.prepare(self.root, config, sha, 'issue:3', offline=True)
        self.assertEqual(packet['contract_status'], 'missing')
        result = self.draft()
        self.assertIn('task_contract_missing', result['blockers'])
        self.assertEqual(result['readiness'], 'not_ready')

    def test_symlinked_local_or_tracked_local_is_rejected_before_execution(self):
        local = self.root / '.team-workflow/local'
        outside = self.root.parent / 'outside'
        outside.mkdir()
        local.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(WorkflowError):
            self.verify()
        local.unlink()
        local.mkdir()
        (local / 'tracked').write_text('bad')
        self.git('add', '-f', '.team-workflow/local/tracked')
        with self.assertRaises(WorkflowError):
            self.verify()

    def test_preview_and_wrong_approval_cannot_execute_project_code(self):
        self.checks([('unit', 'open("unexpected", "w").write("x")', 5)])
        config, sha = self.configuration()
        preview = evidence.verify(self.root, config, sha)
        self.assertEqual(preview['status'], 'not_run')
        self.assertFalse((self.root / '.team-workflow/local').exists())
        with self.assertRaises(WorkflowError):
            evidence.verify(self.root, config, sha, execute_commands=True, approved_policy='incorrect')
        self.assertFalse((self.root / 'unexpected').exists())

    def test_empty_check_set_cannot_pass(self):
        self.checks([])
        with self.assertRaises(WorkflowError):
            self.verify()

    def test_passed_record_is_bound_to_code_policy_time_and_exit(self):
        self.prepare()
        record = self.verify()
        self.assertEqual(record['status'], 'passed')
        self.assertEqual(record['before']['head'], record['after']['head'])
        self.assertEqual(record['checks'][0]['exit_code'], 0)
        self.assertIsNotNone(record['checks'][0]['started_at'])
        self.assertIsNone(record['checks'][0]['log_ref'])
        self.assertNotIn('ok\n', json.dumps(record))
        self.assertTrue((self.root / record['evidence']).is_file())

    def test_failure_stops_later_checks_and_returns_failed(self):
        self.checks([('bad', 'raise SystemExit(7)', 5), ('later', 'open("unexpected", "w")', 5)])
        record = self.verify()
        self.assertEqual(record['status'], 'failed')
        self.assertEqual(record['checks'][0]['exit_code'], 7)
        self.assertEqual(record['checks'][1]['status'], 'not_run')
        self.assertFalse((self.root / 'unexpected').exists())

    def test_missing_executable_is_not_run(self):
        config, sha = self.configuration()
        config['checks']['unit']['argv'] = ['twc-missing-executable-000']
        record = evidence.verify(self.root, config, sha, execute_commands=True, approved_policy=sha)
        self.assertEqual(record['status'], 'not_run')
        self.assertIsNone(record['checks'][0]['exit_code'])

    def test_timeout_is_incomplete(self):
        self.checks([('slow', 'import time; time.sleep(15)', 1)])
        record = self.verify()
        self.assertEqual(record['status'], 'incomplete')
        self.assertEqual(record['checks'][0]['reason'], 'timeout')

    @unittest.skipUnless(os.name == 'posix', 'POSIX process group observation')
    def test_redirected_background_child_is_incomplete_and_terminated(self):
        self.checks([('unit', 'import subprocess, sys; subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)', 5)])
        record = self.verify()
        self.assertEqual(record['status'], 'incomplete')
        self.assertEqual(record['checks'][0]['reason'], 'child_process_still_running')

    def test_ignored_probe_does_not_authorize_visible_packet_or_binding(self):
        (self.root / '.team-workflow/.gitignore').write_text('local/probe\n')
        with self.assertRaises(WorkflowError):
            self.prepare()
        self.assertFalse((self.root / '.team-workflow/local/binding.json').exists())
        self.assertFalse((self.root / '.team-workflow/local/packets').exists())

    def test_evidence_symlink_is_rejected_before_project_code_runs(self):
        self.checks([('unit', 'open("unexpected", "w").write("x")', 5)])
        local = self.root / '.team-workflow/local'
        local.mkdir()
        outside = self.root.parent / 'outside-evidence'
        outside.mkdir()
        (local / 'evidence').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(WorkflowError):
            self.verify()
        self.assertFalse((self.root / 'unexpected').exists())
        self.assertEqual(list(outside.iterdir()), [])

    def test_task_binding_drift_is_incomplete(self):
        self.checks([('unit', 'import json; p=".team-workflow/local/binding.json"; x=json.load(open(p)); x["task_ref"]["number"]=9; json.dump(x,open(p,"w"))', 5)])
        self.prepare()
        record = self.verify()
        self.assertEqual(record['status'], 'incomplete')
        self.assertIn('workspace_task_binding_changed', record['drift'])

    def test_code_mutation_during_test_invalidates_success(self):
        self.checks([('unit', 'open("a.txt", "w").write("changed")', 5)])
        record = self.verify()
        self.assertEqual(record['checks'][0]['status'], 'passed')
        self.assertEqual(record['status'], 'incomplete')
        self.assertIn('code_changed_during_execution', record['drift'])

    def test_policy_mutation_stops_later_checks(self):
        self.checks([('first', 'open(".team-workflow/config.toml", "a").write("\\n# changed")', 5),
                     ('later', 'open("unexpected", "w")', 5)])
        record = self.verify()
        self.assertEqual(record['status'], 'incomplete')
        self.assertIn('policy_changed_during_execution', record['drift'])
        self.assertFalse((self.root / 'unexpected').exists())

    def test_lock_drift_rejects_execution(self):
        path = self.root / '.team-workflow/toolchain.lock.json'
        value = json.loads(path.read_text())
        value['version'] = '99.0.0'
        path.write_text(json.dumps(value))
        with self.assertRaises(WorkflowError):
            self.verify()

    def test_platform_token_is_not_in_test_environment_or_saved_output(self):
        self.checks([('unit', 'import os; assert "TWC_GITEA_TOKEN" not in os.environ; print("synthetic-private-output")', 5)])
        with patch.dict(os.environ, {'TWC_GITEA_TOKEN': 'synthetic-test-token'}):
            record = self.verify()
        text = (self.root / record['evidence']).read_text()
        self.assertEqual(record['status'], 'passed')
        self.assertNotIn('synthetic-test-token', text)
        self.assertNotIn('synthetic-private-output\n', text)

    def test_handoff_unknown_without_current_platform_never_authorizes_merge(self):
        packet = self.prepare()
        record = self.verify()
        result = self.draft()
        self.assertEqual(result['readiness'], 'unknown')
        self.assertFalse(result['merge_authorized'])
        self.assertFalse(result['published'])

    def test_handoff_advisory_only_when_current_pr_matches(self):
        packet = self.prepare()
        with patch.object(Gitea, 'get_identity', return_value=dict(id=7, login='developer')):
            record = self.verify(online=True)
            observation = dict(status='observed', change=dict(status='observed', data=dict(
                head=dict(sha=record['after']['head']), base=dict(sha=record['after']['base']))))
            with patch.object(handoff, 'platform_snapshot', return_value=observation):
                result = self.draft(online=True)
        self.assertEqual(result['readiness'], 'advisory_ready')
        self.assertFalse(result['merge_authorized'])

    def test_each_operation_observes_its_operator_without_overwriting_task_assignee(self):
        config, sha = self.configuration()
        accounts = [dict(id=i, login=name, full_name='成员', email='private@example.invalid', token='never-save')
                    for i, name in enumerate(('alice', 'bob', 'sixseven'), 1)]
        task = dict(status='observed', data=dict(assignees=[dict(id=1, login='alice')], pull_request={}))
        with patch.object(Gitea, 'get_identity', side_effect=accounts) as get_identity:
            with patch.object(context, 'platform_snapshot', return_value=task):
                packet = context.prepare(self.root, config, sha, 'pr:3', 'contract.json')
            preview = evidence.verify(self.root, config, sha, online=True)
            self.assertEqual(preview['status'], 'not_run')
            self.assertEqual(get_identity.call_count, 1)  # Preview does not contact the platform.
            record = self.verify(online=True)
            observation = dict(task, change=dict(status='observed', data=dict(
                head=dict(sha=record['after']['head']), base=dict(sha=record['after']['base']))))
            with patch.object(handoff, 'platform_snapshot', return_value=observation):
                result = self.draft(online=True)
        saved_packet = json.loads((self.root / packet['packet']).read_text())
        self.assertEqual(saved_packet['platform']['data']['assignees'][0]['login'], 'alice')
        self.assertEqual(result['prepared_by']['platform']['data']['login'], 'alice')
        self.assertEqual(result['checks']['unit']['actor']['platform']['data']['login'], 'bob')
        self.assertEqual(result['actor']['platform']['data']['login'], 'sixseven')
        self.assertEqual(result['integrator'], 'maintainer')  # Operator does not become integrator.
        self.assertFalse(result['merge_authorized'])
        for artifact in (saved_packet, record, result):
            self.assertNotIn('never-save', json.dumps(artifact))
            self.assertNotIn('private@example.invalid', json.dumps(artifact))
        markdown = (self.root / result['markdown']).read_text()
        for label in ('Prepared by: alice', 'Handed off by: sixseven', 'executed by bob'):
            self.assertIn(label, markdown)

    def test_git_actor_uses_effective_author_committer_and_preserves_configuration(self):
        with patch.dict(os.environ, {'GIT_AUTHOR_NAME': 'Alice', 'GIT_AUTHOR_EMAIL': 'alice@example.invalid',
                                     'GIT_COMMITTER_NAME': 'Bob', 'GIT_COMMITTER_EMAIL': 'bob@example.invalid'}):
            actor = actors.git_identity(self.root)
        self.assertEqual(actor['author']['name'], 'Alice')
        self.assertEqual(actor['committer']['email'], 'bob@example.invalid')
        self.assertEqual(actor['trust'], 'self_asserted')
        self.assertEqual(self.git('config', 'user.name'), 'Fixture')

    def test_git_actor_does_not_guess_missing_identity_from_operating_system(self):
        self.git('config', '--unset', 'user.name')
        self.git('config', '--unset', 'user.email')
        env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_') and key != 'EMAIL'}
        env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
        with patch.dict(os.environ, env, clear=True):
            actor = actors.git_identity(self.root)
        self.assertEqual(actor['status'], 'incomplete')
        self.assertIsNone(actor['author'])
        self.assertIsNone(actor['committer'])

    def test_offline_never_reuses_an_old_platform_actor(self):
        config, _ = self.configuration()
        with patch.object(Gitea, 'get_identity', return_value=dict(id=7, login='alice')) as get_identity:
            self.assertTrue(actors.attributed(actors.snapshot(self.root, config, online=True)))
            offline = actors.snapshot(self.root, config)
        self.assertEqual(get_identity.call_count, 1)
        self.assertFalse(actors.attributed(offline))
        self.assertIsNone(offline['platform']['data'])

    def test_platform_identity_errors_and_malformed_accounts_remain_unknown(self):
        config, _ = self.configuration()
        for response in ({'login': 'alice'}, {'id': True, 'login': 'alice'}, {'id': 7, 'login': 'bad\nname'}):
            with self.subTest(response=response), patch.object(Gitea, 'get_identity', return_value=response):
                actor = actors.snapshot(self.root, config, online=True)
                self.assertEqual(actor['platform']['status'], 'invalid_response')
                self.assertFalse(actors.attributed(actor))
        with patch.object(Gitea, 'get_identity', side_effect=ProviderError('forbidden', 'safe message')):
            actor = actors.snapshot(self.root, config, online=True)
        self.assertEqual(actor['platform']['status'], 'forbidden')
        self.assertFalse(actors.attributed(actor))

    def test_git_identity_change_during_check_invalidates_evidence(self):
        self.checks([('unit', 'import subprocess; subprocess.run(["git", "config", "user.name", "Changed"], check=True)', 5)])
        result = self.verify()
        self.assertEqual(result['checks'][0]['status'], 'passed')
        self.assertEqual(result['status'], 'incomplete')
        self.assertIn('git_identity_changed_during_execution', result['drift'])

    def test_doctor_reads_platform_account_once_without_changing_local_git_identity(self):
        config, sha = self.configuration()
        with patch.object(Gitea, 'get_identity', return_value=dict(id=1, login='sixseven')) as who:
            with patch.object(Gitea, 'get_repository', return_value=dict(full_name='team/product')):
                with patch.object(Gitea, 'get_version', return_value=dict(version='fixture')):
                    report = twc.doctor(self.root, config, sha, online=True)
        self.assertEqual(report['status'], 'ok')
        self.assertEqual(who.call_count, 1)
        self.assertEqual(report['platform']['identity'], report['actor']['platform'])
        self.assertEqual(report['actor']['git']['author']['name'], 'Fixture')
        self.assertEqual(self.git('config', 'user.name'), 'Fixture')

    def test_same_login_on_another_instance_is_not_the_same_attribution(self):
        config, _ = self.configuration()
        with patch.object(Gitea, 'get_identity', return_value=dict(id=1, login='sixseven')):
            actor = actors.snapshot(self.root, config, online=True)
        self.assertTrue(actors.attributed(actor, config['coordination']['base_url']))
        self.assertFalse(actors.attributed(actor, 'https://other.example.invalid'))

    def test_missing_or_legacy_verification_actor_cannot_claim_attributed_handoff(self):
        packet = self.prepare()
        record = self.verify()
        evidence_path = self.root / record['task_evidence']
        legacy = json.loads(evidence_path.read_text())
        legacy.pop('actor')
        evidence_path.write_text(json.dumps(legacy))
        with patch.object(Gitea, 'get_identity', return_value=dict(id=7, login='sixseven')):
            observation = dict(status='observed', change=dict(status='observed', data=dict(
                head=dict(sha=record['after']['head']), base=dict(sha=record['after']['base']))))
            with patch.object(handoff, 'platform_snapshot', return_value=observation):
                result = self.draft(online=True)
        self.assertEqual(result['readiness'], 'unknown')
        self.assertIn('verification_actor_unverified', result['unknowns'])
        self.assertIsNone(result['checks']['unit']['actor'])

    def test_old_evidence_same_head_different_dirty_bytes_is_stale(self):
        packet = self.prepare()
        (self.root / 'a.txt').write_text('first')
        record = self.verify()
        (self.root / 'a.txt').write_text('second')
        result = self.draft()
        self.assertEqual(result['readiness'], 'not_ready')
        self.assertIn('stale_or_unrelated_evidence', result['blockers'])

    def test_contract_drift_is_visible_even_when_head_matches(self):
        packet = self.prepare()
        record = self.verify()
        (self.root / 'contract.json').write_text(json.dumps(dict(self.contract, goal='new goal')))
        result = self.draft()
        self.assertIn('task_or_interface_contract_changed', result['blockers'])

    def test_worktree_create_preserves_existing_dirty_work_and_previews(self):
        file = self.root / 'a.txt'
        file.write_text('existing WIP')
        destination = self.root.parent / 'task-tree'
        preview = workspace.create(self.root, destination, 'task/3', self.base)
        self.assertFalse(preview['applied'])
        self.assertFalse(destination.exists())
        result = workspace.create(self.root, destination, 'task/3', self.base, apply=True)
        self.assertTrue(result['applied'])
        self.assertEqual(file.read_text(), 'existing WIP')
        with self.assertRaises(WorkflowError):
            workspace.create(self.root, destination, 'task/4', self.base, apply=True)

    def test_configuration_rejects_unknown_permissions_and_escape_cwd(self):
        path = self.root / '.team-workflow/config.toml'
        good = path.read_text()
        for bad in (good.replace('auto_merge = false', 'auto_merge = true'),
                    good.replace('cwd = "."', 'cwd = "../"'),
                    good.replace('provider = "gitea"', 'provider = "gitea"\ntoken = "must-not-persist"')):
            path.write_text(bad)
            with self.assertRaises(WorkflowError):
                self.configuration()
        path.write_text(good)


if __name__ == '__main__':
    unittest.main()
