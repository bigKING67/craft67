"""Real repository relocation, immutable history, collisions and concurrent writers."""
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

from test_tasks import TaskFixture
from test_workflow import RUNTIME
from twc_lib import context, layout, migration, policy, sessions, statusline, tasks, workspace
from twc_lib.models import WorkflowError, relative_path


class LayoutTests(TaskFixture):
    def legacy(self):
        (self.root / '.workflow').rename(self.root / '.team-workflow')
        self.git('add', '--', '.workflow', '.team-workflow')
        self.git('commit', '-qm', 'legacy directory')
        return self.root / '.team-workflow'

    def files(self, directory):
        return {p.relative_to(directory).as_posix(): (p.read_bytes(), p.stat().st_mode & 0o777)
                for p in directory.rglob('*') if p.is_file()}

    def apply(self):
        preview = migration.migrate(self.root)
        return migration.migrate(self.root, True, preview['inventory_sha256'])

    def test_new_default_and_legacy_read_write_use_one_directory(self):
        self.assertEqual(layout.directory(self.root).name, '.workflow')
        old = self.legacy()
        self.prepare()
        self.assertEqual(self.verify()['status'], 'passed')
        self.assertEqual(statusline.read_mode(str(self.root)), 'team')
        self.assertEqual(self.resume()['checks']['unit']['status'], 'passed')
        self.assertTrue((old / 'tasks/pr-3/task.json').is_file())
        self.assertFalse((self.root / '.workflow').exists())

    def test_preview_is_readonly_and_relocation_preserves_all_bytes_and_actors(self):
        old = self.legacy()
        contracts = old / 'contracts'
        contracts.mkdir()
        raw = json.dumps(self.contract, indent=2).replace('\n', '\r\n').encode()
        (contracts / 'legacy.json').write_bytes(raw)
        config, sha = self.configuration()
        context.prepare(self.root, config, sha, 'pr:3', '.team-workflow/contracts/legacy.json', offline=True)
        self.verify()
        self.draft()
        before = self.files(old)
        status = self.git('status', '--porcelain')
        preview = migration.migrate(self.root)
        self.assertFalse(preview['applied'])
        self.assertEqual(self.files(old), before)
        self.assertEqual(self.git('status', '--porcelain'), status)
        result = migration.migrate(self.root, True, preview['inventory_sha256'])
        self.assertTrue(result['applied'])
        self.assertFalse(old.exists())
        self.assertEqual(self.files(self.root / '.workflow'), before)
        self.assertEqual(relative_path(self.root, '.team-workflow/contracts/legacy.json').read_bytes(), raw)
        view = self.resume()
        self.assertEqual(view['revision'], 1)
        self.assertEqual(view['stale_sources'], [])
        self.assertEqual(view['checks']['unit']['status'], 'stale')  # Code paths changed, no invented pass.
        self.assertEqual(self.lint()['status'], 'ok')
        self.assertEqual(self.verify()['status'], 'passed')
        self.assertEqual(self.resume()['checks']['unit']['status'], 'passed')

    def test_inventory_approval_and_drift_are_required(self):
        old = self.legacy()
        preview = migration.migrate(self.root)
        with self.assertRaisesRegex(WorkflowError, 'approved-inventory'):
            migration.migrate(self.root, True)
        (old / 'new-note.txt').write_text('another writer changed the inventory')
        with self.assertRaisesRegex(WorkflowError, 'approved-inventory'):
            migration.migrate(self.root, True, preview['inventory_sha256'])
        self.assertTrue(old.exists())
        self.assertFalse((self.root / '.workflow').exists())

    def test_no_local_state_before_migration_is_supported(self):
        old = self.legacy()
        self.assertFalse((old / 'local').exists())
        self.assertTrue(self.apply()['applied'])
        self.assertFalse((self.root / '.workflow/local').exists())

    def test_dual_directories_reject_reads_writes_and_statusline(self):
        self.legacy()
        other = self.root / '.workflow'
        other.mkdir()
        (other / 'foreign.txt').write_text('keep')
        for operation in (lambda: policy.load(self.root), lambda: self.prepare(),
                          lambda: migration.migrate(self.root), lambda: self.resume()):
            with self.assertRaisesRegex(WorkflowError, 'Both'):
                operation()
        self.assertEqual(statusline.read_mode(str(self.root)), 'invalid')
        self.assertEqual((other / 'foreign.txt').read_text(), 'keep')

    def test_foreign_directory_is_not_initialized_or_migrated(self):
        config = self.root / '.workflow/config.toml'
        config.write_text('owner = "another-tool"\n')
        before = self.files(config.parent)
        with self.assertRaises(WorkflowError):
            policy.init(self.root, None, None, self.base, apply=True, mode='personal')
        with self.assertRaises(WorkflowError):
            migration.migrate(self.root)
        self.assertEqual(self.files(config.parent), before)

    def test_symlink_and_nested_symlink_cannot_be_migrated(self):
        old = self.legacy()
        (old / 'linked').symlink_to(self.root / 'a.txt')
        with self.assertRaisesRegex(WorkflowError, 'symlink'):
            migration.migrate(self.root)
        self.assertTrue((old / 'linked').is_symlink())

    def test_tracked_local_state_and_ignored_target_are_refused(self):
        old = self.legacy()
        local = old / 'local'
        local.mkdir()
        (local / 'private.txt').write_text('fixture only')
        self.git('add', '-f', '--', '.team-workflow/local/private.txt')
        with self.assertRaisesRegex(WorkflowError, 'tracked'):
            migration.migrate(self.root)

    def test_root_ignore_cannot_hide_the_migrated_configuration(self):
        self.legacy()
        (self.root / '.gitignore').write_text('.workflow/\n')
        with self.assertRaisesRegex(WorkflowError, 'Git-ignored'):
            migration.migrate(self.root)

    def test_rename_failure_leaves_the_original_intact_and_can_retry(self):
        old = self.legacy()
        before = self.files(old)
        with patch.object(migration, 'rename_directory', side_effect=OSError('simulated rename failure')):
            with self.assertRaises(OSError):
                self.apply()
        self.assertEqual(self.files(old), before)
        self.assertTrue(self.apply()['applied'])
        self.assertFalse(migration.migrate(self.root, True)['changed'])

    def test_destination_created_after_preflight_is_never_replaced(self):
        old = self.legacy()
        original = migration.rename_directory

        def concurrent_directory(source, target):
            target.mkdir()
            return original(source, target)

        with patch.object(migration, 'rename_directory', concurrent_directory):
            with self.assertRaises(OSError):
                self.apply()
        self.assertTrue(old.exists())
        self.assertTrue((self.root / '.workflow').is_dir())
        self.assertEqual(list((self.root / '.workflow').iterdir()), [])

    def test_an_old_runtime_writer_blocks_relocation(self):
        old = self.legacy()
        self.prepare()
        preview = migration.migrate(self.root)
        with sessions.file_lock(old / 'local/mutation.lock'):
            with self.assertRaisesRegex(WorkflowError, 'Workspace is busy'):
                migration.migrate(self.root, True, preview['inventory_sha256'])
        self.assertTrue(old.exists())

    def test_stable_mutex_blocks_other_processes_on_both_sides_of_rename(self):
        self.legacy()
        self.prepare()
        original = migration.rename_directory
        observations = []

        def contender():
            run = subprocess.run([sys.executable, '-B', str(RUNTIME / 'twc.py'), '--project', str(self.root),
                                  'prepare', '--task', 'pr:3', '--contract', 'contract.json', '--offline'],
                                 capture_output=True, text=True)
            observations.append((run.returncode, json.loads(run.stdout)))

        def rename(path, target):
            contender()
            result = original(path, target)
            contender()
            return result

        with patch.object(migration, 'rename_directory', rename):
            self.apply()
        self.assertEqual([code for code, _ in observations], [2, 2])
        self.assertTrue(all('Workspace is busy' in row['message'] for _, row in observations))
        self.assertEqual(self.verify()['status'], 'passed')

    def test_mode_change_uses_the_same_cross_process_mutex(self):
        self.legacy()
        config, sha = self.configuration()
        with sessions.workspace_lock(self.root, relocating=True):
            run = subprocess.run([sys.executable, '-B', str(RUNTIME / 'twc.py'), '--project', str(self.root),
                                  'mode', '--set', 'personal', '--apply', '--approved-policy', sha],
                                 capture_output=True, text=True)
        self.assertEqual(run.returncode, 2)
        self.assertIn('Workspace is busy', json.loads(run.stdout)['message'])
        self.assertEqual(self.configuration(), (config, sha))
        self.assertFalse(list((self.root / '.team-workflow').glob('.*.tmp')))

    def test_local_link_after_preview_cannot_touch_external_mutex(self):
        old = self.legacy()
        self.prepare()
        preview = migration.migrate(self.root)
        outside = self.root.parent / 'external'
        outside.mkdir()
        external_lock = outside / 'mutation.lock'
        external_lock.write_bytes(b'preserve')
        external_lock.chmod(0o644)
        before = (external_lock.read_bytes(), external_lock.stat().st_mode)
        (old / 'local').rename(old / 'local.saved')
        (old / 'local').symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(WorkflowError, 'symlink'):
            migration.migrate(self.root, True, preview['inventory_sha256'])
        self.assertEqual((external_lock.read_bytes(), external_lock.stat().st_mode), before)

    def test_worktree_mutexes_are_not_shared_between_worktrees(self):
        sibling = self.root.parent / 'sibling'
        self.git('worktree', 'add', '-q', '-b', 'sibling', str(sibling))
        with sessions.workspace_lock(self.root), sessions.workspace_lock(sibling):
            self.assertNotEqual(workspace.git(self.root, 'rev-parse', '--git-path', 'workflow-craft-mutation.lock'),
                                workspace.git(sibling, 'rev-parse', '--git-path', 'workflow-craft-mutation.lock'))
