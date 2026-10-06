"""Regressions for version drift across the existing package metadata formats."""
import json
from pathlib import Path
import tempfile
import unittest

from versions import inspect_package


class VersionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.directory = self.root / 'packages/example'
        self.directory.mkdir(parents=True)
        self.package = {'path': 'packages/example', 'version_source': {'path': 'VERSION', 'format': 'text'}}
        (self.directory / 'VERSION').write_text('1.2.3\n')

    def test_detects_lock_root_and_python_drift(self):
        (self.directory / 'package.json').write_text(json.dumps({'version': '1.2.3'}))
        (self.directory / 'package-lock.json').write_text(json.dumps({
            'version': '1.2.3', 'packages': {'': {'version': '1.2.2'}}}))
        (self.directory / 'pyproject.toml').write_text('[project]\nversion = "1.2.1"\n')
        version, errors = inspect_package(self.root, self.package)
        self.assertEqual(version, '1.2.3')
        self.assertEqual(len(errors), 2)
        self.assertTrue(any('packages[""]' in error for error in errors))
        self.assertTrue(any('pyproject.toml' in error for error in errors))

    def test_pack_authority_does_not_confuse_installer_version(self):
        self.package['version_source'] = {'path': 'skill-pack.json', 'format': 'json', 'field': 'pack_version'}
        (self.directory / 'skill-pack.json').write_text(json.dumps({
            'pack_version': '2.2.0', 'minimum_installer_version': '2.1.0'}))
        self.assertEqual(inspect_package(self.root, self.package), ('2.2.0', []))

    def test_accepts_prerelease_and_build_metadata(self):
        (self.directory / 'VERSION').write_text('1.2.3-rc.1+build.7')
        self.assertEqual(inspect_package(self.root, self.package), ('1.2.3-rc.1+build.7', []))

    def test_rejects_missing_and_malformed_versions(self):
        for invalid in ('v1.2.3', '01.2.3', '1.2.3-01', '1.2.3-alpha..1'):
            with self.subTest(version=invalid):
                (self.directory / 'VERSION').write_text(invalid)
                self.assertTrue(inspect_package(self.root, self.package)[1])
        (self.directory / 'VERSION').unlink()
        with self.assertRaises(FileNotFoundError):
            inspect_package(self.root, self.package)


if __name__ == '__main__':
    unittest.main()
