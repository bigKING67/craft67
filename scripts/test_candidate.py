"""Downloaded candidates must retain exact identity and package bytes."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import candidate


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.archive = self.directory / 'review-craft.tgz'
        self.archive.write_bytes(b'fixture archive')
        self.manifest = {'schema': 'craft67.candidate.v1', 'status': 'offline-candidate',
                         'package': 'review-craft', 'package_path': 'packages/review-craft', 'source_sha': 'a' * 40, 'version': '1.2.3',
                         'files': {self.archive.name: candidate.digest(self.archive)}}
        self.save()
        patcher = patch.object(candidate, 'version_for', return_value='1.2.3')
        patcher.start()
        self.addCleanup(patcher.stop)

    def save(self):
        (self.directory / candidate.MANIFEST).write_text(json.dumps(self.manifest))

    def verify(self):
        return candidate.verify(self.directory, 'review-craft', 'a' * 40)

    def test_original_bytes_pass_but_tampering_fails(self):
        self.verify()
        self.archive.write_bytes(b'changed')
        with self.assertRaises(ValueError):
            self.verify()

    def test_wrong_source_package_version_and_status_fail(self):
        for field in ('source_sha', 'package', 'package_path', 'version', 'status'):
            with self.subTest(field=field):
                original = self.manifest[field]
                self.manifest[field] = 'wrong'
                self.save()
                with self.assertRaises(ValueError):
                    self.verify()
                self.manifest[field] = original

    def test_all_supported_package_formats(self):
        self.archive.unlink()
        for package in candidate.SUPPORTED:
            with self.subTest(package=package):
                suffix = '.tgz' if package in ('review-craft', 'creative-craft', 'money-craft', 'reverse-craft') else '.zip'
                artifact = self.directory / (package + suffix)
                artifact.write_bytes(b'fixture')
                self.manifest.update(package=package, package_path=f'packages/{package}',
                                     files={artifact.name: candidate.digest(artifact)})
                self.save()
                candidate.verify(self.directory, package, 'a' * 40)
                artifact.unlink()

    def test_unlisted_file_fails(self):
        (self.directory / 'unexpected').write_text('extra')
        with self.assertRaises(ValueError):
            self.verify()

    def test_symlink_archive_fails(self):
        self.archive.unlink()
        target = self.directory / 'target'
        target.write_bytes(b'fixture archive')
        self.archive.symlink_to(target)
        self.manifest['files']['target'] = candidate.digest(target)
        self.save()
        with self.assertRaises(ValueError):
            self.verify()


if __name__ == '__main__':
    unittest.main()
