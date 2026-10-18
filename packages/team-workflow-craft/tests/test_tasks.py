"""Task records on the branch: content identity, acceptance status, resume and lint."""
import json
from pathlib import Path
import subprocess
from unittest.mock import patch

from test_workflow import Fixture
from twc_lib import context, handoff, policy, tasks, workspace
from twc_lib.models import WorkflowError


class TaskRecordTests(Fixture):
    def resume(self, root=None, task=None):
        root = root or self.root
        config, sha = policy.load(root)
        return tasks.resume(root, config, sha, policy.runtime_identity(), context.binding(root), task)

    def lint(self):
        config, _ = self.configuration()
        return tasks.check(self.root, config)

    def commit_task(self, message='twc: task metadata'):
        self.git('add', '--', '.team-workflow/tasks')
        self.git('commit', '-qm', message, '--', '.team-workflow/tasks')

    def contract_file(self, name, **changes):
        (self.root / name).write_text(json.dumps(dict(self.contract, **changes)))
        self.git('add', name)
        self.git('commit', '-qm', 'contract ' + name)

    def test_content_identity_ignores_commit_state_and_task_metadata(self):
        (self.root / 'a.txt').write_text('changed\n')
        dirty = workspace.inspect(self.root, self.base)
        self.git('commit', '-qam', 'change')
        committed = workspace.inspect(self.root, self.base)
        self.assertEqual(dirty['tree_sha256'], committed['tree_sha256'])
        self.assertNotEqual(dirty['head'], committed['head'])
        record = self.root / '.team-workflow/tasks/pr-3/note.json'
        record.parent.mkdir(parents=True)
        record.write_text('{}')
        metadata = workspace.inspect(self.root, self.base)
        self.assertEqual(metadata['tree_sha256'], committed['tree_sha256'])
        self.assertFalse(metadata['dirty'])
        self.assertEqual(metadata['task_metadata_changes'], ['.team-workflow/tasks/pr-3/note.json'])

    def test_committed_evidence_stays_fresh_until_code_changes(self):
        prepared = self.prepare()
        self.assertEqual(prepared['acceptance'], [dict(id='AC-1', text='unit passes', checks=['unit'])])
        record = self.verify()
        self.assertTrue((self.root / record['task_evidence']).is_file())
        self.assertNotIn(str(self.root), (self.root / record['task_evidence']).read_text())
        self.commit_task()
        view = self.resume()
        self.assertEqual(view['acceptance'][0]['status'], 'verified')
        self.assertEqual(view['checks']['unit']['status'], 'passed')
        self.assertFalse(any(action.startswith('verify') for action in view['next_actions']))
        (self.root / 'a.txt').write_text('new behaviour\n')
        self.git('commit', '-qam', 'more work')
        view = self.resume()
        self.assertEqual(view['acceptance'][0]['status'], 'pending')
        self.assertIn('verify: unit', view['next_actions'])

    def test_plain_acceptance_needs_human_review_and_never_reaches_advisory(self):
        self.contract_file('review.json', acceptance=[dict(text='unit passes', checks=['unit']), 'Copy reviewed'])
        config, sha = self.configuration()
        context.prepare(self.root, config, sha, 'pr:3', 'review.json', offline=True)
        record = self.verify()
        observation = dict(status='observed', change=dict(status='observed', data=dict(
            head=dict(sha=record['after']['head']), base=dict(sha=record['after']['base']))))
        with patch.object(handoff, 'platform_snapshot', return_value=observation):
            result = self.draft(online=True)
        self.assertEqual(result['readiness'], 'unknown')
        self.assertIn('acceptance_needs_human_review', result['unknowns'])
        self.assertIn('AC-2 (needs_review): Copy reviewed', result['remaining'])
        self.assertEqual([row['status'] for row in result['acceptance']], ['verified', 'needs_review'])

    def test_newer_failure_supersedes_an_older_pass(self):
        self.checks([('unit', 'import pathlib, sys; sys.exit(7 if pathlib.Path(".team-workflow/local/fail").exists() else 0)', 5)])
        self.git('commit', '-qam', 'flaky check')
        self.prepare()
        # Both runs land in the same second; ordering must not depend on the random run id.
        with patch('twc_lib.models.now', return_value='2026-10-18T10:00:00.000001+00:00'):
            self.assertEqual(self.verify()['status'], 'passed')
        (self.root / '.team-workflow/local/fail').write_text('x')
        with patch('twc_lib.models.now', return_value='2026-10-18T10:00:00.000002+00:00'):
            self.assertEqual(self.verify()['status'], 'failed')
        view = self.resume()
        self.assertEqual(view['checks']['unit']['status'], 'failed')
        self.assertEqual(view['acceptance'][0]['status'], 'failed')
        self.assertIn('verification_not_passed', self.draft()['blockers'])

    def test_contract_change_requires_explicit_update_and_invalidates_evidence(self):
        self.prepare()
        self.verify()
        self.contract_file('contract.json', goal='A narrower feature')
        with self.assertRaisesRegex(WorkflowError, 'update-contract'):
            self.prepare()
        updated = self.prepare(update_contract=True)
        self.assertEqual((updated['task_record_status'], updated['revision']), ('updated', 2))
        view = self.resume()
        self.assertEqual(view['checks']['unit']['status'], 'missing')
        self.assertEqual(len(tasks.load(self.root, view['task_ref'])['history']), 1)

    def test_fresh_clone_resumes_from_branch_changes_without_local_state(self):
        self.git('switch', '-qc', 'alice/feature')
        self.prepare()
        self.verify()
        self.draft()
        self.commit_task('twc: hand off pr-3')
        clone = self.root.parent / 'bob'
        subprocess.run(['git', 'clone', '-q', str(self.root), str(clone)], check=True)
        bob = ['git', '-C', str(clone)]
        subprocess.run([*bob, 'switch', '-qc', 'bob/feature', 'origin/alice/feature'], check=True)
        subprocess.run([*bob, 'config', 'user.name', 'Bob'], check=True)
        subprocess.run([*bob, 'config', 'user.email', 'bob@example.invalid'], check=True)
        self.assertFalse((clone / '.team-workflow/local').exists())
        view = self.resume(clone)
        self.assertEqual(view['resolved_by'], 'branch_changes')
        self.assertEqual(view['last_handoff']['done'], ['feature complete'])
        self.assertEqual(view['acceptance'][0]['status'], 'verified')
        self.assertEqual(view['handed_off_by']['git']['author']['name'], 'Fixture')
        (clone / 'a.txt').write_text('bob continues\n')
        subprocess.run([*bob, 'commit', '-qam', 'Continue the feature'], check=True)
        view = self.resume(clone)
        self.assertTrue(any('Bob: Continue the feature' in row for row in view['commits_since_handoff']))
        self.assertEqual(view['acceptance'][0]['status'], 'pending')

    def test_placeholder_handoff_is_rejected(self):
        self.prepare()
        config, sha = self.configuration()
        for text in ('TODO', '待补充', '...'):
            with self.subTest(text=text), self.assertRaisesRegex(WorkflowError, 'placeholder'):
                handoff.draft(self.root, config, sha, None, [text], [], ['review'])
        self.assertFalse((self.root / '.team-workflow/tasks/pr-3/handoff.json').exists())

    def test_staged_files_outside_scope_are_reported_before_commit(self):
        self.prepare()
        (self.root / 'other-session.txt').write_text('another agent session\n')
        self.git('add', 'other-session.txt')
        view = self.resume()
        self.assertEqual(view['code']['staged_outside_scope'], ['other-session.txt'])
        self.assertIn('review_staged_files_outside_scope_before_commit', view['next_actions'])

    def test_check_detects_edits_local_fields_and_placeholders(self):
        self.prepare()
        record = self.verify()
        self.draft()
        self.assertEqual(self.lint()['status'], 'ok')
        task_file = self.root / '.team-workflow/tasks/pr-3/task.json'
        original = task_file.read_text()
        edited = json.loads(original)
        edited['contract']['goal'] = 'quietly changed'
        task_file.write_text(json.dumps(edited))
        self.assertIn('edited outside prepare', json.dumps(self.lint()))
        task_file.write_text(original)
        summary = self.root / record['task_evidence']
        summary.write_text(json.dumps(dict(json.loads(summary.read_text()), root='/Users/someone/project')))
        self.assertIn('local-only', json.dumps(self.lint()))
        summary.unlink()
        handoff_file = self.root / '.team-workflow/tasks/pr-3/handoff.json'
        handoff_file.write_text(json.dumps(dict(json.loads(handoff_file.read_text()), done=['TBD'])))
        self.assertIn('placeholder', json.dumps(self.lint()))

    def test_ignored_task_directory_is_refused(self):
        with (self.root / '.gitignore').open('a') as stream:
            stream.write('.team-workflow/tasks/\n')
        with self.assertRaisesRegex(WorkflowError, 'Git-ignored'):
            self.prepare()

    def test_resume_without_task_points_to_prepare(self):
        view = self.resume()
        self.assertEqual(view['status'], 'no_task')
        self.assertTrue(view['next_actions'][0].startswith('prepare'))
        self.assertFalse((self.root / '.team-workflow/local').exists())


class ReviewRegressionTests(Fixture):
    def test_update_contract_requires_a_contract_and_first_contract_needs_no_update(self):
        config, sha = self.configuration()
        context.prepare(self.root, config, sha, 'issue:5', offline=True)
        added = context.prepare(self.root, config, sha, 'issue:5', 'contract.json', offline=True)
        self.assertEqual((added['task_record_status'], added['revision']), ('updated', 2))
        with self.assertRaisesRegex(WorkflowError, 'requires --contract'):
            context.prepare(self.root, config, sha, 'issue:5', offline=True, update_contract=True)
        self.assertIsNotNone(tasks.load(self.root, added['task_ref'])['contract'])

    def test_hand_edited_acceptance_mapping_is_detected(self):
        self.prepare()
        path = self.root / '.team-workflow/tasks/pr-3/task.json'
        value = json.loads(path.read_text())
        value['acceptance'][0]['checks'] = ['lint']
        path.write_text(json.dumps(value))
        config, _ = self.configuration()
        self.assertIn('edited outside prepare', json.dumps(tasks.check(self.root, config)))

    def test_verify_refuses_a_task_other_than_the_binding(self):
        self.prepare()
        self.checks([('unit', 'open("must-not-run", "w").write("x")', 5)])
        with self.assertRaisesRegex(WorkflowError, 'binding'):
            self.verify(task='issue:9')
        self.assertFalse((self.root / 'must-not-run').exists())

    def test_clean_filters_keep_identity_across_commit(self):
        (self.root / '.gitattributes').write_text('*.txt text eol=lf\n')
        self.git('add', '.gitattributes')
        self.git('commit', '-qm', 'normalize line endings')
        (self.root / 'a.txt').write_bytes(b'windows\r\nline\r\n')
        dirty = workspace.inspect(self.root, self.base)
        self.git('commit', '-qam', 'crlf content')
        self.assertEqual(dirty['tree_sha256'], workspace.inspect(self.root, self.base)['tree_sha256'])

    def test_option_like_handoff_head_is_not_passed_to_git(self):
        self.prepare()
        self.draft()
        path = self.root / '.team-workflow/tasks/pr-3/handoff.json'
        path.write_text(json.dumps(dict(json.loads(path.read_text()), code=dict(head='--output=/tmp/twc-x'))))
        config, sha = self.configuration()
        view = tasks.resume(self.root, config, sha, policy.runtime_identity(), context.binding(self.root))
        self.assertEqual(view['commits_since_handoff'], [])

    def test_automatic_ids_skip_explicit_ones(self):
        from twc_lib.models import acceptance_items
        items = acceptance_items(dict(acceptance=[dict(id='AC-1', text='explicit'), 'plain']))
        self.assertEqual([item['id'] for item in items], ['AC-1', 'AC-2'])
        items = acceptance_items(dict(acceptance=['plain', dict(id='AC-1', text='explicit')]))
        self.assertEqual([item['id'] for item in items], ['AC-2', 'AC-1'])
