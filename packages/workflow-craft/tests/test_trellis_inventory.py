"""Read-only source assessment, including ambiguous and moving migration inputs."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/trellis_inventory.py'
SPEC = importlib.util.spec_from_file_location('trellis_inventory', SCRIPT)
inventory_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inventory_module)


class TrellisInventoryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name).resolve() / 'project'
        self.write('.trellis/.version', '0.6.15\n')
        self.write('.trellis/spec/index.md', '# Existing project rules\n')
        self.write('AGENTS.md', '# Keep these project instructions\n')
        (self.root / '.trellis/tasks').mkdir()

    def write(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value.encode() if isinstance(value, str) else value)
        return path

    def task(self, directory, **changes):
        data = dict(id=Path(directory).name, status='in_progress', workflow_profile='full',
                    parent=None, children=[])
        data.update(changes)
        return self.write('.trellis/tasks/' + directory + '/task.json', json.dumps(data))

    def scan(self):
        return inventory_module.inventory(self.root)

    def codes(self, result):
        return {finding['code'] for finding in result['findings']}

    def snapshot(self):
        return {path.relative_to(self.root).as_posix(): path.read_bytes()
                for path in self.root.rglob('*') if path.is_file()}

    def test_preserves_tree_history_and_existing_planning_sources(self):
        self.task('parent', status='planning', children=['child'])
        self.task('child', parent='parent', title='private-title', assignee='private-person')
        self.write('.trellis/tasks/child/prd.md', '# Acceptance\n')
        self.write('.trellis/tasks/archive/2026-01/old/task.json',
                   json.dumps(dict(id='old', status='completed', custom_data='private-value')))
        before = self.snapshot()
        result = self.scan()
        self.assertEqual(result['status'], 'ok')
        self.assertFalse(result['migration_ready'])
        self.assertEqual(result['summary']['tasks'], 3)
        self.assertEqual(result['summary']['archived'], 1)
        self.assertEqual(result['summary']['relations'], 2)
        old = next(row for row in result['tasks'] if row['id'] == 'old')
        self.assertIsNone(old['declared_profile'])
        self.assertEqual(old['effective_profile'], 'full')
        self.assertTrue(old['legacy_profile_default'])
        for relative, source in result['sources'].items():
            self.assertEqual(source['sha256'], hashlib.sha256(before[relative]).hexdigest())
        self.assertEqual(self.snapshot(), before)
        for private in ('private-title', 'private-person', 'private-value'):
            self.assertNotIn(private, json.dumps(result))

    def test_duplicate_source_identity_does_not_guess_relation(self):
        self.task('same')
        self.task('archive/2026-01/same', status='completed')
        self.task('child', parent='same')
        result = self.scan()
        self.assertEqual(result['status'], 'needs_review')
        self.assertTrue({'ambiguous_task_id', 'ambiguous_task_directory', 'unresolved_parent'} <= self.codes(result))
        self.assertIsNone(result['relations'][0]['target_source'])

    def test_includes_noncanonical_task_attachments_without_exposing_contents(self):
        self.task('parent', status='planning', children=['child'])
        self.task('child', parent='parent')
        self.write('.trellis/tasks/child/prd.md', '# Acceptance\n')
        attachment = '.trellis/tasks/child/evidence/native-result.json'
        self.write(attachment, '{"private-evidence": "retained"}\n')
        self.write('.trellis/tasks/child/delivery-runbook.md', 'private-runbook')
        self.write('.trellis/tasks/index.md', 'private-index')
        before = self.snapshot()
        result = self.scan()
        expected = sorted(path for path in before if path.startswith('.trellis/tasks/'))
        self.assertEqual(result['task_files'], expected)
        self.assertEqual(result['summary']['task_files'], len(expected))
        self.assertTrue(set(expected) <= set(result['sources']))
        self.assertEqual(result['sources'][attachment]['sha256'],
                         hashlib.sha256(before[attachment]).hexdigest())
        self.assertEqual(self.snapshot(), before)
        for private in ('private-evidence', 'private-runbook', 'private-index'):
            self.assertNotIn(private, json.dumps(result))

    def test_unreadable_attachment_prevents_complete_inventory(self):
        self.task('one')
        relative = '.trellis/tasks/one/large-evidence.bin'
        self.write(relative, b'X' * (inventory_module.MAX_BYTES + 1))
        result = self.scan()
        self.assertEqual(result['status'], 'needs_review')
        self.assertIn(relative, result['task_files'])
        self.assertNotIn(relative, result['sources'])
        self.assertIn('file_exceeds_inventory_limit', self.codes(result))

    def test_relations_use_directory_names_not_json_ids(self):
        self.task('10-29-parent', id='parent', children=['10-29-child'])
        self.task('10-29-child', id='child', parent='10-29-parent')
        result = self.scan()
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['summary']['relations'], 2)
        self.assertTrue(all(row['target_source'] for row in result['relations']))

    def test_archived_parent_can_retain_history_without_active_backlink(self):
        self.task('archive/2026-01/parent', status='completed', children=['child'])
        self.task('child')
        result = self.scan()
        self.assertEqual(result['status'], 'ok')
        self.assertIn('archived_parent_without_backlink', self.codes(result))
        self.assertFalse(result['migration_ready'])

    def test_inconsistent_relations_and_completion_remain_observations(self):
        completed = self.task('parent', status='completed', children=['child', 'missing'])
        self.task('child')
        before = completed.read_bytes()
        result = self.scan()
        self.assertTrue({'completed_but_not_archived', 'nonreciprocal_child', 'unresolved_child'} <= self.codes(result))
        self.assertEqual(completed.read_bytes(), before)
        task = next(row for row in result['tasks'] if row['id'] == 'parent')
        self.assertEqual(task['status'], 'completed')
        self.assertFalse(task['archived'])

    def test_reciprocal_cycle_is_not_a_valid_task_tree(self):
        self.task('one', parent='two', children=['two'])
        self.task('two', parent='one', children=['one'])
        self.assertIn('cyclic_parent_relation', self.codes(self.scan()))

    def test_malformed_inputs_are_reported_without_raw_values(self):
        self.write('.trellis/tasks/broken/task.json', '{private-secret')
        self.task('bad', id='../private-secret', status='private-secret',
                  workflow_profile='private-secret', children='private-secret')
        self.write('.trellis/tasks/large/task.json', b'X' * (inventory_module.MAX_BYTES + 1))
        result = self.scan()
        self.assertEqual(result['summary']['discovered_task_records'], 3)
        self.assertEqual(result['summary']['tasks'], 1)
        self.assertTrue({'invalid_task_json', 'invalid_task_id', 'invalid_children',
                         'unrecognized_task_status', 'unrecognized_workflow_profile',
                         'file_exceeds_inventory_limit'} <= self.codes(result))
        self.assertNotIn('private-secret', json.dumps(result))
        self.assertIsNone(result['tasks'][0]['effective_profile'])

    def test_symlink_sources_and_directories_are_not_followed(self):
        outside = self.root.parent / 'outside'
        outside.mkdir()
        (outside / 'task.json').write_text('{"id": "outside-secret"}')
        (self.root / '.trellis/tasks/linked').symlink_to(outside, target_is_directory=True)
        (self.root / '.trellis/spec/linked.md').symlink_to(outside / 'task.json')
        result = self.scan()
        self.assertIn('symlink_not_read', self.codes(result))
        self.assertNotIn('outside-secret', json.dumps(result))
        self.assertEqual(result['summary']['tasks'], 0)
        self.assertNotIn('.trellis/spec/linked.md', result['sources'])

    def test_changed_source_is_not_certified_as_stable(self):
        task = self.task('moving')
        original_open = inventory_module.os.open
        reads = 0

        def changing_open(path, flags, *args, **kwargs):
            nonlocal reads
            if path == task:
                reads += 1
                if reads == 2:
                    task.write_text(task.read_text().replace('in_progress', 'completed'))
            return original_open(path, flags, *args, **kwargs)

        with patch.object(inventory_module.os, 'open', side_effect=changing_open):
            result = self.scan()
        self.assertEqual(result['status'], 'needs_review')
        self.assertIn('source_changed_during_read', self.codes(result))

    def test_new_spec_during_scan_is_not_silently_omitted(self):
        self.task('existing')
        original_walk = inventory_module.os.walk
        walks = 0

        def changing_walk(path, *args, **kwargs):
            nonlocal walks
            if Path(path) == self.root / '.trellis/spec':
                walks += 1
                if walks == 2:
                    self.write('.trellis/spec/added.md', 'new spec')
            return original_walk(path, *args, **kwargs)

        with patch.object(inventory_module.os, 'walk', side_effect=changing_walk):
            result = self.scan()
        self.assertIn('spec_file_set_changed', self.codes(result))

    def test_cli_is_read_only_and_never_claims_migration_ready(self):
        self.task('one')
        before = self.snapshot()
        run = subprocess.run([sys.executable, '-B', str(SCRIPT), '--project', str(self.root)],
                             capture_output=True, text=True, check=False)
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(run.stdout)
        self.assertFalse(result['migration_ready'])
        self.assertEqual(self.snapshot(), before)
        self.assertFalse((self.root / '.team-workflow').exists())

    def test_missing_project_has_controlled_cli_error(self):
        run = subprocess.run([sys.executable, '-B', str(SCRIPT), '--project', str(self.root / 'missing')],
                             capture_output=True, text=True, check=False)
        self.assertEqual(run.returncode, 2)
        self.assertEqual(json.loads(run.stdout)['status'], 'error')
        self.assertEqual(run.stderr, '')


if __name__ == '__main__':
    unittest.main()
