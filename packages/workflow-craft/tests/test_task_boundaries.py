"""Regressions at task switching, persisted input and portable evidence boundaries."""
import copy
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

from test_tasks import TaskFixture
from twc_lib import context, records
from twc_lib.models import WorkflowError


class TaskBoundaryTests(TaskFixture):
    def test_deferred_and_selected_reverification_keep_other_evidence_stale(self):
        self.checks([(name, 'from pathlib import Path; '
                      f'p=Path(".team-workflow/local/{name}-runs"); '
                      'p.write_text(p.read_text()+"x" if p.exists() else "x")', 5)
                     for name in ('unit', 'full')])
        self.git('commit', '-qam', 'two independently selectable checks')
        self.prepare()
        self.assertEqual(self.verify()['status'], 'passed')
        task_path = self.root / '.team-workflow/tasks/pr-3/task.json'
        task_before = task_path.read_bytes()
        (self.root / 'a.txt').write_text('updated implementation\n')
        # A new session may inspect stale evidence and continue work without running checks.
        with patch('twc_lib.evidence.execute', side_effect=AssertionError('inspection must not execute')):
            view = self.resume()
        self.assertEqual({row['status'] for row in view['checks'].values()}, {'stale'})
        self.assertEqual(task_path.read_bytes(), task_before)
        self.assertEqual(self.verify(selected=['unit'])['status'], 'passed')
        view = self.resume()
        self.assertEqual(view['checks']['unit']['status'], 'passed')
        self.assertEqual(view['checks']['full']['status'], 'stale')
        local = self.root / '.team-workflow/local'
        self.assertEqual((local / 'unit-runs').read_text(), 'xx')
        self.assertEqual((local / 'full-runs').read_text(), 'x')
        draft = self.draft()
        self.assertIn('required_verification_missing', draft['unknowns'])
        self.assertNotEqual(draft['readiness'], 'advisory_ready')
        self.assertFalse(draft['merge_authorized'])
        self.assertEqual(self.verify(selected=['full'])['status'], 'passed')
        self.assertEqual({row['status'] for row in self.resume()['checks'].values()}, {'passed'})

    def configure_argv(self, argv):
        path = self.root / '.team-workflow/config.toml'
        base = path.read_text().split('[checks.')[0]
        path.write_text(base + '\n[checks.unit]\nargv = ' + json.dumps(argv) + '\ncwd = "."\ntimeout_seconds = 5\n')
        self.git('commit', '-qam', 'configure argv')

    def test_missing_executable_supersedes_pass_and_recovery_restores_it(self):
        self.configure_argv(['twc-test-tool', '/d', '/c', 'exit', '0'] if os.name == 'nt' else ['twc-test-tool'])
        bin_dir = self.root.parent / 'bin'
        bin_dir.mkdir()
        tool = bin_dir / ('twc-test-tool.exe' if os.name == 'nt' else 'twc-test-tool')
        if os.name == 'nt':
            shutil.copyfile(Path(os.environ['SYSTEMROOT']) / 'System32/cmd.exe', tool)
        else:
            tool.write_text('#!/bin/sh\nexit 0\n')
            tool.chmod(0o755)
        self.prepare()
        with patch.dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ.get('PATH', '')):
            self.assertEqual(self.verify()['status'], 'passed')
            tool.rename(bin_dir / 'disabled-tool')
            self.assertEqual(self.verify()['status'], 'not_run')
            view = self.resume()
            self.assertEqual(view['checks']['unit']['status'], 'not_run')
            self.assertEqual(view['acceptance'][0]['status'], 'pending')
            self.assertIn('verify: unit', view['next_actions'])
            self.assertIn('verification_not_passed', self.draft()['blockers'])
            (bin_dir / 'disabled-tool').rename(tool)
            self.assertEqual(self.verify()['status'], 'passed')
            self.assertEqual(self.resume()['acceptance'][0]['status'], 'verified')

    def test_skipped_later_check_preserves_prior_observation_but_blocks_handoff(self):
        self.checks([('first', 'import pathlib,sys; sys.exit(pathlib.Path(".team-workflow/local/fail").exists())', 5),
                     ('unit', 'print("ok")', 5)])
        self.git('commit', '-qam', 'two checks')
        self.prepare()
        self.verify()
        (self.root / '.team-workflow/local/fail').write_text('fail')
        run = self.verify()
        self.assertEqual(run['checks'][1]['reason'], 'earlier_check_did_not_complete')
        self.assertEqual(self.resume()['checks']['unit']['status'], 'passed')
        self.assertIn('verification_not_passed', self.draft()['blockers'])

    def test_incomplete_new_attempt_for_same_code_supersedes_old_pass(self):
        self.checks([('unit', 'import pathlib,subprocess; '
                     'subprocess.run(["git","config","user.name","Changed"],check=True) '
                     'if pathlib.Path(".team-workflow/local/change-identity").exists() else None', 5)])
        self.git('commit', '-qam', 'identity drift check')
        self.prepare()
        first = self.verify()
        self.assertEqual(first['status'], 'passed')
        (self.root / '.team-workflow/local/change-identity').write_text('change')
        second = self.verify()
        self.assertEqual(second['status'], 'incomplete')
        self.assertIn('git_identity_changed_during_execution', second['drift'])
        self.assertEqual(first['after']['tree_sha256'], second['after']['tree_sha256'])
        self.assertEqual(self.resume()['checks']['unit']['status'], 'incomplete')
        self.assertIn('verification_not_passed', self.draft()['blockers'])

    def test_switch_branch_refuses_old_binding_before_execution_and_can_rebind(self):
        common = self.git('rev-parse', 'HEAD')
        self.git('switch', '-qc', 'task-A')
        self.prepare(task='pr:3')
        self.commit_task()
        self.git('switch', '-qc', 'task-B', common)
        self.prepare(task='pr:4', rebind=True)
        self.commit_task()
        self.git('switch', '-q', 'task-A')
        with patch('twc_lib.evidence.execute') as execute:
            for operation in (self.resume, self.verify, self.draft, self.prepare):
                with self.subTest(operation=operation.__name__), self.assertRaisesRegex(WorkflowError, 'rebind'):
                    operation()
            execute.assert_not_called()
        self.prepare(task='pr:3', rebind=True)
        self.assertEqual(self.verify()['task_ref']['number'], 3)

    def test_legacy_binding_uses_packet_branch_and_empty_branch_requires_rebind(self):
        self.prepare()
        path = self.root / '.team-workflow/local/binding.json'
        value = json.loads(path.read_text())
        value.pop('branch')
        path.write_text(json.dumps(value))
        self.assertEqual(context.binding(self.root)['branch'], 'main')
        self.git('switch', '-qc', 'different')
        with self.assertRaisesRegex(WorkflowError, 'rebind'):
            self.resume()
        self.prepare(rebind=True)
        self.assertEqual(self.resume()['task_ref']['number'], 3)

    def test_legacy_binding_without_packet_cannot_silently_cross_branches(self):
        self.git('switch', '-qc', 'task-A')
        self.prepare()
        self.commit_task()
        path = self.root / '.team-workflow/local/binding.json'
        value = json.loads(path.read_text())
        value.pop('branch')
        (self.root / value['packet']).unlink()
        path.write_text(json.dumps(value))
        self.git('switch', '-qc', 'task-B')
        with self.assertRaisesRegex(WorkflowError, 'rebind'):
            self.resume()
        with self.assertRaisesRegex(WorkflowError, 'rebind'):
            self.verify()
        self.prepare(rebind=True)
        self.assertEqual(self.resume()['task_ref']['number'], 3)

    def test_explicit_rebind_recovers_unreadable_legacy_packet(self):
        self.prepare()
        path = self.root / '.team-workflow/local/binding.json'
        value = json.loads(path.read_text())
        value.pop('branch')
        path.write_text(json.dumps(value))
        (self.root / value['packet']).write_text('{')
        with self.assertRaises(WorkflowError):
            self.resume()
        self.prepare(rebind=True)
        self.assertEqual(self.resume()['task_ref']['number'], 3)

    def test_malformed_evidence_rejected_by_lint_resume_handoff_and_cli(self):
        self.prepare()
        run = self.verify()
        path = self.root / run['task_evidence']
        original = json.loads(path.read_text())
        mutations = [dict(checks=[42]), dict(checks=None), dict(created_at=42), dict(code=[]),
                     dict(actor=[]), dict(status='passed', drift=['changed'])]
        bad_check = copy.deepcopy(original['checks'])
        bad_check[0]['exit_code'] = True
        mutations.append(dict(checks=bad_check))
        bad_check = copy.deepcopy(original['checks'])
        bad_check[0]['status'] = 'unrecognized'
        mutations.append(dict(checks=bad_check))
        for update in mutations:
            with self.subTest(update=update):
                path.write_text(json.dumps(dict(original, **update)))
                self.assertEqual(self.lint()['status'], 'attention_required')
                for operation in (self.resume, self.draft):
                    with self.assertRaises(WorkflowError):
                        operation()
        path.write_text(json.dumps(dict(original, checks=[42])))
        cli = Path(__file__).resolve().parents[1] / 'skills/workflow-craft/scripts/twc.py'
        result = subprocess.run([sys.executable, str(cli), '--project', str(self.root), 'resume'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)['error'], 'workflow_error')
        self.assertNotIn('Traceback', result.stderr)

    def test_bad_task_and_handoff_fields_are_controlled_errors(self):
        self.prepare()
        self.draft()
        for filename, update in [('task.json', {'contract': 42}), ('task.json', {'sources': [42]}),
                                 ('handoff.json', {'done': 42}), ('handoff.json', {'checks': {'unit': 42}}),
                                 ('handoff.json', {'merge_authorized': True})]:
            with self.subTest(filename=filename, update=update):
                path = self.root / '.team-workflow/tasks/pr-3' / filename
                original = path.read_text()
                path.write_text(json.dumps(dict(json.loads(original), **update)))
                self.assertEqual(self.lint()['status'], 'attention_required')
                with self.assertRaises(WorkflowError):
                    self.resume()
                path.write_text(original)

    def test_summary_hashes_absolute_argv_and_keeps_full_command_only_locally(self):
        argv = [sys.executable, '-c', 'pass', '/Users/example/private-input', r'C:\Users\example\input',
                '--output=/private/tmp/example']
        self.configure_argv(argv)
        self.prepare()
        run = self.verify()
        shared_text = (self.root / run['task_evidence']).read_text()
        shared = json.loads(shared_text)
        local = json.loads((self.root / run['evidence']).read_text())
        self.assertEqual(local['checks'][0]['argv'], argv)
        self.assertNotIn('argv', shared['checks'][0])
        self.assertEqual(shared['checks'][0]['command_sha256'], records.command_hash(argv))
        for value in argv:
            if value.startswith(('/', 'C:', '--output=')):
                self.assertNotIn(value, shared_text)
        self.assertEqual(self.lint()['status'], 'ok')
        self.assertEqual(self.resume()['checks']['unit']['status'], 'passed')
        shared['checks'][0]['command_sha256'] = '0' * 64
        (self.root / run['task_evidence']).write_text(json.dumps(shared))
        self.assertEqual(self.resume()['checks']['unit']['status'], 'incomplete')

    def test_legacy_v2_commands_readable_but_lint_flags_absolute_paths(self):
        self.configure_argv(['python3', '-c', 'pass'])
        self.prepare()
        run = self.verify()
        path = self.root / run['task_evidence']
        row = json.loads(path.read_text())
        row['checks'][0].pop('command_sha256')
        row['checks'][0]['argv'] = ['python3', '-c', 'pass']
        path.write_text(json.dumps(row))
        self.assertEqual(self.resume()['checks']['unit']['status'], 'passed')
        self.assertEqual(self.lint()['status'], 'ok')
        row['checks'][0]['argv'] = [sys.executable, '-c', 'pass']
        path.write_text(json.dumps(row))
        self.assertEqual(self.lint()['status'], 'attention_required')
        self.assertEqual(self.resume()['checks']['unit']['status'], 'incomplete')

    def test_acceptance_bad_identifier_is_controlled_error(self):
        from twc_lib.models import acceptance_items
        with self.assertRaises(WorkflowError):
            acceptance_items({'acceptance': [{'id': [], 'text': 'bad'}]})

    def test_legacy_double_slash_paths_flagged_without_rejecting_https(self):
        self.prepare()
        run = self.verify()
        path = self.root / run['task_evidence']
        row = json.loads(path.read_text())
        row['checks'][0].pop('command_sha256')
        for argument in ('//usr/bin/python3', '--input=//Users/member/private-input', r'C:\Users\member\input'):
            with self.subTest(argument=argument):
                row['checks'][0]['argv'] = ['python3', '-c', 'pass', argument]
                path.write_text(json.dumps(row))
                self.assertEqual(self.lint()['status'], 'attention_required')
        row['checks'][0]['argv'] = ['python3', '-c', 'pass', '--url=https://example.invalid/path']
        path.write_text(json.dumps(row))
        self.assertEqual(self.lint()['status'], 'ok')
