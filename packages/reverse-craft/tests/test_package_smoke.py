import importlib.util
import io
from pathlib import Path
import tarfile
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('package_smoke', Path(__file__).resolve().parents[1] / 'scripts/package_smoke.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PackageSmokeTests(unittest.TestCase):
    def test_archive_boundary_and_source_parity(self):
        cases = [('package/SKILL.md', b'valid', None, True),
                 ('package/../SKILL.md', b'valid', None, False),
                 ('package/SKILL.md', b'wrong', None, False),
                 ('package/SKILL.md', b'', tarfile.SYMTYPE, False),
                 ('package/other.md', b'valid', None, False)]
        for name, content, kind, valid in cases:
            with self.subTest(name=name, content=content, kind=kind), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                archive = root / 'candidate.tgz'
                with tarfile.open(archive, 'w:gz') as output:
                    member = tarfile.TarInfo(name)
                    member.size = len(content)
                    if kind:
                        member.type, member.linkname = kind, '/outside'
                    output.addfile(member, io.BytesIO(content))
                if valid:
                    module.extract_verified(archive, root / 'out', {'SKILL.md': b'valid'})
                    self.assertEqual((root / 'out/SKILL.md').read_bytes(), b'valid')
                else:
                    with self.assertRaises(ValueError):
                        module.extract_verified(archive, root / 'out', {'SKILL.md': b'valid'})

    def test_missing_and_duplicate_entries_fail(self):
        for names in (['SKILL.md'], ['SKILL.md', 'SKILL.md']):
            with self.subTest(names=names), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                archive = root / 'candidate.tgz'
                with tarfile.open(archive, 'w:gz') as output:
                    for name in names:
                        member = tarfile.TarInfo('package/' + name)
                        member.size = 1
                        output.addfile(member, io.BytesIO(b'x'))
                with self.assertRaises(ValueError):
                    module.extract_verified(archive, root / 'out', {'SKILL.md': b'x', 'VERSION': b'x'})


if __name__ == '__main__':
    unittest.main()
