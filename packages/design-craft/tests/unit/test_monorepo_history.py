"""The migrated privacy gate scans initial and removed package history."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[2] / 'scripts/design_craft_public_repo_validate.py'
spec = importlib.util.spec_from_file_location('public_repo_migration', SCRIPT)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class MonorepoHistoryTests(unittest.TestCase):
    def test_initial_import_and_removed_paths_remain_audited(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = root / 'packages/design-craft'
            (package / 'docs').mkdir(parents=True)
            (package / validator.POLICY_PATH).write_text(validator.HISTORY_BASELINE)
            (root / 'catalog.json').write_text(json.dumps({'packages': [
                {'name': 'design-craft', 'path': 'packages/design-craft'}
            ]}))

            def git(*args):
                subprocess.run(['git', '-C', str(root), *args], check=True,
                               capture_output=True)

            def commit():
                git('add', '--', 'catalog.json', 'packages', 'sibling.txt')
                git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                    '-c', 'commit.gpgsign=false', 'commit', '-m', 'fixture')

            git('init', '--quiet')
            # A sibling has its own privacy policy and must not enter this package gate.
            private_path = '/' + 'Users' + '/fixture-user/private'
            (root / 'sibling.txt').write_text(private_path)
            with patch.object(validator, 'ROOT', package):
                self.assertTrue(validator.history_errors())  # No HEAD fails closed.
                commit()
                self.assertEqual(validator.history_errors(), [])
                (package / 'example.md').write_text(private_path)
                commit()
                self.assertTrue(validator.history_errors())
                (package / 'example.md').unlink()
                commit()
                self.assertTrue(validator.history_errors())  # Removal cannot hide history.


if __name__ == '__main__':
    unittest.main()
