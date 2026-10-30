"""Local lifecycle acceptance without touching real projects, hosts or platforms."""
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

from test_tasks import TaskFixture
from test_workflow import RUNTIME
from twc_lib import context, evidence, lifecycle, policy, sessions, tasks
from twc_lib.models import WorkflowError, task_ref


class LifecycleTests(TaskFixture):
    def create(self, task='local:one', session='one', parent=None, contract='contract.json'):
        config, sha = self.configuration()
        return lifecycle.create(self.root, config, sha, task, contract, parent, session, offline=True)

    def move(self, action, task=None, session='one', **kwargs):
        config, sha = self.configuration()
        return lifecycle.transition(self.root, config, sha, action, task, session, **kwargs)

    def view(self, task=None, session='one', root=None):
        root = root or self.root
        config, sha = policy.load(root)
        return tasks.resume(root, config, sha, policy.runtime_identity(), context.binding(root, session), task, session)

    def verify_session(self, session='one', **kwargs):
        config, sha = self.configuration()
        return evidence.verify(self.root, config, sha, execute_commands=True, approved_policy=sha, session=session, **kwargs)

    def record(self, name='local:one'):
        config, _ = self.configuration()
        return tasks.load(self.root, task_ref(config, name))

    def test_end_to_end_loop_preserves_contract_and_never_authorizes_merge(self):
        contract = (self.root / 'contract.json').read_bytes()
        self.assertEqual(self.create()['execution_state'], 'planning')
        self.move('start')
        denied = self.move('complete')
        self.assertFalse(denied['applied'])
        self.assertEqual(self.verify_session()['status'], 'passed')
        self.assertEqual(self.move('complete')['execution_state'], 'completed')
        self.assertEqual(self.view()['execution']['completion'], 'current')
        self.assertFalse(self.view()['execution']['merge_authorized'])
        self.assertEqual(self.move('archive')['execution_state'], 'archived')
        self.assertEqual(self.view()['status'], 'no_task')
        self.move('reopen', 'local:one')
        self.assertEqual(self.view()['execution']['state'], 'in_progress')
        self.assertIn('previous_completion', self.record()['execution']['history'][-1])
        self.assertEqual((self.root / 'contract.json').read_bytes(), contract)
        self.assertEqual(self.lint()['status'], 'ok')

    def test_sessions_do_not_inherit_or_overwrite_each_others_binding(self):
        self.prepare('pr:3')  # Legacy workspace pointer remains supported, but is not inherited.
        self.create('local:one', 'one')
        self.create('local:two', 'two')
        self.assertEqual(self.view(session='one')['task_ref']['slug'], 'one')
        self.assertEqual(self.view(session='two')['task_ref']['slug'], 'two')
        self.assertEqual(self.view(session='new')['status'], 'no_task')
        self.assertIn('task list', self.view(session='new')['next_actions'])
        self.assertFalse(any(action.startswith('prepare') for action in self.view(session='new')['next_actions']))
        self.move('start', session='one')
        self.assertFalse(self.move('finish', session='one')['task_state_changed'])
        self.assertEqual(self.record()['execution']['state'], 'in_progress')
        self.assertEqual(self.view(session='one')['status'], 'no_task')
        self.assertEqual(self.view(session='two')['task_ref']['slug'], 'two')
        self.assertEqual(context.binding(self.root)['task_ref']['number'], 3)

    def test_pause_and_start_do_not_recreate_contract_or_evidence(self):
        self.create()
        self.move('start')
        self.verify_session()
        revision = self.record()['revision']
        self.move('pause')
        self.assertEqual(self.view()['status'], 'no_task')
        self.move('start', 'local:one', session='next-host')
        self.assertEqual(self.view(session='next-host')['checks']['unit']['status'], 'passed')
        self.assertEqual(self.record()['revision'], revision)
        self.assertEqual(self.record()['execution']['state'], 'in_progress')

    def test_parent_requires_every_child_currently_completed(self):
        self.create('local:parent', 'parent')
        self.move('start', session='parent')
        self.verify_session('parent')
        for name in ('a', 'b', 'c'):
            self.create('local:' + name, name, 'local:parent')
            self.move('start', session=name)
            self.verify_session(name)
            if name != 'c':
                self.move('complete', session=name)
        result = self.move('complete', session='parent')
        self.assertIn('child_not_currently_completed:local:c', result['blockers'])
        self.move('complete', session='c')
        self.assertEqual(self.move('complete', session='parent')['status'], 'ok')
        self.move('reopen', session='a')
        self.assertEqual(self.view(session='parent')['execution']['completion'], 'stale')
        self.assertEqual(self.move('archive', session='parent')['status'], 'attention_required')

    def test_new_code_marks_old_completion_stale_and_prevents_archive(self):
        self.create()
        self.move('start')
        self.verify_session()
        self.move('complete')
        (self.root / 'a.txt').write_text('changed after completion\n')
        view = self.view()
        self.assertEqual(view['execution']['state'], 'completed')
        self.assertEqual(view['execution']['completion'], 'stale')
        self.assertFalse(self.move('archive')['applied'])
        self.move('reopen')
        self.verify_session()
        self.assertEqual(self.move('complete')['status'], 'ok')

    def test_manual_review_is_explicit_bound_and_cannot_override_failed_checks(self):
        self.contract_file('review-contract.json', acceptance=[{'text': 'unit passes', 'checks': ['unit']}, 'Copy reviewed'])
        self.create(contract='review-contract.json')
        self.move('start')
        self.verify_session()
        self.assertIn('explicit_acceptance_review_missing_or_invalid', self.move('complete')['blockers'])
        review = self.root / '.team-workflow/tasks/local-one/review.md'
        review.write_text('Reviewer checked the copy against the accepted wording.\n')
        relative = review.relative_to(self.root).as_posix()
        result = self.move('complete', reviewed=['AC-2'], review_evidence=[relative])
        self.assertEqual(result['status'], 'ok')
        self.assertFalse(result['merge_authorized'])
        review.write_text('Review changed.\n')
        self.assertEqual(self.view()['execution']['completion'], 'stale')
        self.move('reopen')
        self.checks([('unit', 'raise SystemExit(1)', 5)])
        self.verify_session()
        result = self.move('complete', reviewed=['AC-1', 'AC-2'], review_evidence=[relative])
        self.assertFalse(result['applied'])
        self.assertIn('acceptance_not_verified', result['blockers'])

    def test_branch_switch_needs_explicit_start_and_worktree_binding_is_independent(self):
        self.create()
        self.move('start')
        self.commit_task()
        self.git('switch', '-qc', 'other-branch')
        with self.assertRaisesRegex(WorkflowError, 'branch'):
            self.view()
        self.move('start', 'local:one')
        self.assertEqual(self.view()['status'], 'ok')
        other = self.root.parent / 'other-tree'
        self.git('worktree', 'add', '-q', '-b', 'other-tree', str(other))
        self.assertEqual(self.view(root=other)['status'], 'no_task')
        config, sha = policy.load(other)
        lifecycle.transition(other, config, sha, 'start', 'local:one', 'one')
        self.assertEqual(context.binding(other, 'one')['branch'], 'other-tree')
        self.assertEqual(context.binding(self.root, 'one')['branch'], 'other-branch')

    def test_trellis_owner_and_missing_session_refuse_lifecycle_mutation(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(WorkflowError, 'session'):
                self.create(session=None)
        path = self.root / '.team-workflow/config.toml'
        path.write_text(path.read_text().replace('workflow_owner = "workflow-craft"', 'workflow_owner = "trellis"'))
        with self.assertRaisesRegex(WorkflowError, 'Trellis owns'):
            self.create()
        self.assertFalse((self.root / '.team-workflow/tasks/local-one').exists())

    def test_legacy_contract_adoption_is_explicit_and_preserves_evidence(self):
        self.prepare('local:one')
        self.verify(task='local:one')
        self.assertNotIn('execution', self.record())
        self.move('start', 'local:one')
        self.assertEqual(self.view()['checks']['unit']['status'], 'passed')
        self.assertEqual(self.record()['revision'], 1)

    def test_cross_session_verification_and_missing_session_are_rejected(self):
        self.create()
        self.move('start')
        with self.assertRaisesRegex(WorkflowError, 'session'):
            self.verify_session('other', task='local:one')
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(WorkflowError, 'session'):
                self.verify(task='local:one')

    def test_lock_prevents_a_second_process_mutating_same_worktree(self):
        self.create()
        with sessions.workspace_lock(self.root):
            run = subprocess.run([sys.executable, '-B', str(RUNTIME / 'twc.py'), '--project', str(self.root),
                                  '--session', 'two', 'task', 'start', '--task', 'local:one'],
                                 text=True, capture_output=True)
        self.assertEqual(run.returncode, 2)
        self.assertIn('Workspace is busy', json.loads(run.stdout)['message'])
        self.assertEqual(self.record()['execution']['state'], 'planning')

    def test_graph_tampering_and_session_symlinks_fail_closed(self):
        self.create()
        path = self.root / '.team-workflow/tasks/local-one/task.json'
        row = json.loads(path.read_text())
        row['execution']['parent'] = row['task_ref']
        path.write_text(json.dumps(row))
        self.assertEqual(self.lint()['status'], 'attention_required')
        with self.assertRaisesRegex(WorkflowError, 'cyclic'):
            self.move('start')
        link = sessions.path(self.root, 'unsafe')
        link.symlink_to(self.root / 'contract.json')
        with self.assertRaisesRegex(WorkflowError, 'symlink'):
            context.binding(self.root, 'unsafe')

    def test_input_drift_during_completion_does_not_record_completed(self):
        self.create()
        self.move('start')
        self.verify_session()
        original = lifecycle.blockers
        def changed(*args, **kwargs):
            result = original(*args, **kwargs)
            (self.root / 'a.txt').write_text('concurrent edit\n')
            return result
        with patch.object(lifecycle, 'blockers', side_effect=changed):
            with self.assertRaisesRegex(WorkflowError, 'inputs changed'):
                self.move('complete')
        self.assertEqual(self.record()['execution']['state'], 'in_progress')

    def test_contract_update_keeps_parent_and_history_but_invalidates_checks(self):
        self.create()
        self.move('start')
        self.verify_session()
        history = self.record()['execution']['history']
        self.contract_file('contract.json', goal='Refined acceptance scope')
        self.prepare('local:one', session='one', update_contract=True)
        self.assertEqual(self.record()['execution']['history'], history)
        self.assertEqual(self.view()['checks']['unit']['status'], 'stale')

    def test_read_only_cli_list_does_not_create_local_state(self):
        local = self.root / '.team-workflow/local'
        self.assertFalse(local.exists())
        run = subprocess.run([sys.executable, '-B', str(RUNTIME / 'twc.py'), '--project', str(self.root), 'task', 'list'],
                             text=True, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stdout)
        self.assertEqual(json.loads(run.stdout)['tasks'], [])
        self.assertFalse(local.exists())
