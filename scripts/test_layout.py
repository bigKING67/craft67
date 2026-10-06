"""Exercise catalog evolution and Git pin boundaries using isolated repositories."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('layout', Path(__file__).with_name('verify-layout.py'))
layout = importlib.util.module_from_spec(spec)
spec.loader.exec_module(layout)


class LayoutTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git('init', '-q')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'user.name', 'Fixture')
        self.catalog = {'schema_version': 1, 'packages': []}
        self.add_package('example')
        self.git('add', 'catalog.json', 'packages')
        self.git('commit', '-qm', 'fixture')

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args], text=True, stderr=subprocess.PIPE).strip()

    def save(self):
        (self.root / 'catalog.json').write_text(json.dumps(self.catalog))

    def add_package(self, name):
        directory = self.root / 'packages' / name
        directory.mkdir(parents=True)
        (directory / 'SKILL.md').write_text('# Fixture\n')
        (directory / 'VERSION').write_text('1.0.0\n')
        self.catalog['packages'].append({'name': name, 'path': f'packages/{name}',
            'skills': [{'name': name, 'path': 'SKILL.md'}], 'checks': [['true']],
            'version_source': {'path': 'VERSION', 'format': 'text'}})
        self.save()

    def test_catalog_controls_counts_and_matrix(self):
        self.add_package('another')
        report, matrix = layout.inspect_layout(self.root)
        self.assertTrue(report['ok'], report)
        self.assertEqual((report['packages'], report['skills']), (2, 2))
        self.assertEqual(matrix['include'][1], {'package': 'another', 'path': 'packages/another'})

    def test_duplicate_skill_and_missing_entry_fail(self):
        self.add_package('another')
        self.catalog['packages'][1]['skills'] = [{'name': 'example', 'path': 'missing.md'}]
        self.save()
        report, _ = layout.inspect_layout(self.root)
        self.assertFalse(report['ok'])
        self.assertEqual(len(report['errors']), 2)

    def test_unregistered_package_fails(self):
        (self.root / 'packages/unregistered').mkdir()
        self.assertFalse(layout.inspect_layout(self.root)[0]['ok'])

    def test_escaping_skill_fails(self):
        self.catalog['packages'][0]['skills'][0]['path'] = '../../catalog.json'
        self.save()
        self.assertFalse(layout.inspect_layout(self.root)[0]['ok'])

    def register_upstream(self):
        path = 'packages/example/upstreams/reference'
        self.git('config', '-f', '.gitmodules', 'submodule.reference.path', path)
        self.git('config', '-f', '.gitmodules', 'submodule.reference.url', 'https://example.invalid/reference.git')
        self.git('update-index', '--add', '--cacheinfo', f'160000,{self.git("rev-parse", "HEAD")},{path}')
        return path

    def test_current_pins_do_not_require_old_snapshot_or_checkout(self):
        path = self.register_upstream()
        self.assertTrue(layout.inspect_layout(self.root)[0]['ok'])
        report, _ = layout.inspect_layout(self.root, check_checkouts=True)
        self.assertIn(f'uninitialized upstream checkout: {path}', report['errors'])
        self.git('commit', '--allow-empty', '-qm', 'new pin')
        self.git('update-index', '--cacheinfo', f'160000,{self.git("rev-parse", "HEAD")},{path}')
        self.assertTrue(layout.inspect_layout(self.root)[0]['ok'])

    def test_checkout_must_match_current_index_pin(self):
        path = self.register_upstream()
        checkout = self.root / path
        checkout.parent.mkdir(parents=True)
        subprocess.run(['git', 'clone', '-q', '--no-hardlinks', str(self.root), str(checkout)],
                       check=True, capture_output=True)
        self.assertTrue(layout.inspect_layout(self.root, check_checkouts=True)[0]['ok'])
        self.git('commit', '--allow-empty', '-qm', 'different pin')
        self.git('update-index', '--cacheinfo', f'160000,{self.git("rev-parse", "HEAD")},{path}')
        report, _ = layout.inspect_layout(self.root, check_checkouts=True)
        self.assertIn(f'upstream checkout differs from index pin: {path}', report['errors'])

    def test_unregistered_gitlink_fails(self):
        self.register_upstream()
        (self.root / '.gitmodules').unlink()
        self.assertFalse(layout.inspect_layout(self.root)[0]['ok'])

    def test_invalid_matrix_emits_no_usable_output(self):
        self.catalog['packages'][0]['path'] = '../outside'
        self.save()
        script = self.root / 'scripts/verify-layout.py'
        script.parent.mkdir()
        script.write_text(Path(layout.__file__).read_text())
        result = subprocess.run(['python3', str(script), '--matrix'], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')
        self.assertFalse(json.loads(result.stderr)['ok'])


if __name__ == '__main__':
    unittest.main()
