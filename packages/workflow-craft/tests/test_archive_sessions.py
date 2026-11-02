"""Archive completed work across sessions without replacing its completion basis."""
import json
import subprocess
import sys
from unittest.mock import patch

from test_tasks import TaskFixture
from test_workflow import RUNTIME
from twc_lib import context, evidence, lifecycle, policy, sessions, tasks
from twc_lib.models import WorkflowError, task_ref


class ArchiveSessionTests(TaskFixture):
    def create(self, task='local:one', session='one', parent=None):
        config, sha = self.configuration()
        return lifecycle.create(self.root, config, sha, task, 'contract.json', parent, session, offline=True)

    def move(self, action, task=None, session='one'):
        config, sha = self.configuration()
        return lifecycle.transition(self.root, config, sha, action, task, session)

    def complete(self, task='local:one', session='one', parent=None):
        self.create(task, session, parent)
        self.move('start', session=session)
        config, sha = self.configuration()
        self.assertEqual(evidence.verify(self.root, config, sha, execute_commands=True,
                                        approved_policy=sha, session=session)['status'], 'passed')
        self.assertEqual(self.move('complete', session=session)['execution_state'], 'completed')

    def record_path(self, task='local:one', root=None):
        root = root or self.root
        config, _ = policy.load(root)
        return tasks.target(root, task_ref(config, task), 'task.json')

    def execution(self, task='local:one', root=None):
        return json.loads(self.record_path(task, root).read_text())['execution']

    def evidence_bytes(self, root=None):
        root = root or self.root
        return {path.relative_to(root).as_posix(): path.read_bytes()
                for path in (root / '.workflow/tasks').rglob('*')
                if path.is_file() and path.name != 'task.json'}

    def cli(self, *args, session='fresh', root=None, expected=0):
        run = subprocess.run([sys.executable, '-B', str(RUNTIME / 'twc.py'), '--project', str(root or self.root),
                              '--session', session, *args], text=True, capture_output=True)
        self.assertEqual(run.returncode, expected, run.stdout + run.stderr)
        self.assertEqual(run.stderr, '')
        return json.loads(run.stdout)

    def assert_archived(self, before, task='local:one', root=None):
        after = self.execution(task, root)
        self.assertEqual(after['state'], 'archived')
        self.assertEqual(after['completion'], before['completion'])
        self.assertEqual(after['parent'], before['parent'])
        self.assertEqual(after['history'][:-1], before['history'])
        self.assertEqual(after['history'][-1]['action'], 'archive')

    def test_new_session_archives_child_without_invalidating_parent_completion(self):
        self.create('local:parent', 'parent')
        self.move('start', session='parent')
        config, sha = self.configuration()
        self.assertEqual(evidence.verify(self.root, config, sha, execute_commands=True,
                                        approved_policy=sha, session='parent')['status'], 'passed')
        self.complete('local:child', 'child', 'local:parent')
        self.assertEqual(self.move('complete', session='parent')['execution_state'], 'completed')
        self.move('finish', session='parent')
        self.move('finish', session='child')
        parent_bytes = self.record_path('local:parent').read_bytes()
        before, evidence_before = self.execution('local:child'), self.evidence_bytes()
        self.assertEqual(self.cli('resume', '--task', 'local:child')['execution']['completion'], 'current')
        self.assertEqual(self.cli('task', 'archive', '--task', 'local:child')['execution_state'], 'archived')
        self.assert_archived(before, 'local:child')
        self.assertEqual(self.record_path('local:parent').read_bytes(), parent_bytes)
        self.assertEqual(self.cli('resume', '--task', 'local:parent')['execution']['completion'], 'current')
        self.assertEqual(self.evidence_bytes(), evidence_before)
        self.assertIsNone(context.binding(self.root, 'fresh'))

    def test_fresh_clone_archives_completed_task_without_reopening_or_source_writes(self):
        self.complete()
        self.move('finish')
        self.commit_task()
        source_bytes, source_evidence = self.record_path().read_bytes(), self.evidence_bytes()
        clone = self.root.parent / 'receiver'
        subprocess.run(['git', 'clone', '-q', str(self.root), str(clone)], check=True)
        for key, value in (('user.name', 'Receiver'), ('user.email', 'receiver@example.invalid'),
                           ('core.hooksPath', str(clone / 'no-hooks'))):
            subprocess.run(['git', '-C', str(clone), 'config', key, value], check=True)
        subprocess.run(['git', '-C', str(clone), 'remote', 'set-url', 'origin',
                        'https://gitea.example.invalid/team/product.git'], check=True)
        self.assertFalse((clone / '.workflow/local').exists())
        before, evidence_before = self.execution(root=clone), self.evidence_bytes(clone)
        self.assertEqual(self.cli('resume', '--task', 'local:one', root=clone)['execution']['completion'], 'current')
        self.assertEqual(self.cli('task', 'archive', '--task', 'local:one', root=clone)['execution_state'], 'archived')
        self.assert_archived(before, root=clone)
        self.assertEqual(self.evidence_bytes(clone), evidence_before)
        self.assertEqual(self.record_path().read_bytes(), source_bytes)
        self.assertEqual(self.evidence_bytes(), source_evidence)
        self.assertIsNone(context.binding(clone, 'fresh'))

    def test_archive_requires_explicit_selection_and_respects_another_task_binding(self):
        self.complete()
        self.move('finish')
        before = self.record_path().read_bytes()
        self.assertEqual(self.cli('task', 'archive', expected=2)['error'], 'workflow_error')
        self.assertIn('explicitly reopen', self.cli('task', 'start', '--task', 'local:one', expected=2)['message'])
        self.create('local:other', 'occupied')
        other_bytes = self.record_path('local:other').read_bytes()
        binding_bytes = sessions.path(self.root, 'occupied').read_bytes()
        self.assertEqual(self.cli('task', 'archive', '--task', 'local:one', session='occupied', expected=2)['error'],
                         'workflow_error')
        self.assertEqual(self.record_path().read_bytes(), before)
        self.assertEqual(self.record_path('local:other').read_bytes(), other_bytes)
        self.assertEqual(sessions.path(self.root, 'occupied').read_bytes(), binding_bytes)

    def test_unbound_archive_refuses_stale_completion_without_changing_history(self):
        self.complete()
        self.move('finish')
        before, evidence_before = self.record_path().read_bytes(), self.evidence_bytes()
        (self.root / 'a.txt').write_text('changed since completion\n')
        result = self.cli('task', 'archive', '--task', 'local:one', expected=1)
        self.assertFalse(result['applied'])
        self.assertEqual(result['execution_state'], 'completed')
        self.assertIn('completion_context_changed', result['blockers'])
        self.assertEqual(self.record_path().read_bytes(), before)
        self.assertEqual(self.evidence_bytes(), evidence_before)
        self.assertIsNone(context.binding(self.root, 'fresh'))

    def test_unbound_archive_detects_binding_change_during_validation(self):
        self.complete()
        self.move('finish')
        before, evidence_before = self.record_path().read_bytes(), self.evidence_bytes()
        original = lifecycle.completion_problems
        config, _ = self.configuration()
        replacement = dict(task_ref=task_ref(config, 'local:one'), branch='main')

        def changed(*args, **kwargs):
            problems = original(*args, **kwargs)
            sessions.write(self.root, replacement, 'fresh')
            return problems

        with patch.object(lifecycle, 'completion_problems', side_effect=changed):
            with self.assertRaisesRegex(WorkflowError, 'inputs changed'):
                self.move('archive', 'local:one', session='fresh')
        self.assertEqual(context.binding(self.root, 'fresh'), dict(replacement, session='fresh'))
        self.assertEqual(self.record_path().read_bytes(), before)
        self.assertEqual(self.evidence_bytes(), evidence_before)

    def test_explicit_archive_does_not_rebind_an_existing_session_after_branch_switch(self):
        self.complete()
        before, evidence_before = self.record_path().read_bytes(), self.evidence_bytes()
        binding_bytes = sessions.path(self.root, 'one').read_bytes()
        self.git('switch', '-qc', 'another-branch')
        result = self.cli('task', 'archive', '--task', 'local:one', session='one', expected=2)
        self.assertIn('binding conflicts with this branch', result['message'])
        self.assertEqual(self.record_path().read_bytes(), before)
        self.assertEqual(sessions.path(self.root, 'one').read_bytes(), binding_bytes)
        self.assertEqual(self.evidence_bytes(), evidence_before)
