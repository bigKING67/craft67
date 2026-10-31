"""Shared task records use LF even on a CRLF-default text runtime."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_tasks import TaskFixture
from twc_lib import tasks


class RecordNewlineTests(unittest.TestCase):
    def test_generated_json_and_markdown_have_identical_utf8_lf_bytes(self):
        native_open = io.open
        value = {'name': '六七', 'done': ['checked', 'reviewed']}
        markdown = '# 交接\n\n- checked\n- reviewed\n'
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for default_newline in ('\n', '\r\n'):
                # Exercise actual TextIOWrapper translation on any CI host.
                def platform_open(file, mode='r', buffering=-1, encoding=None,
                                  errors=None, newline=None, closefd=True, opener=None):
                    if 'b' not in mode and any(flag in mode for flag in 'wax'):
                        if newline is None:
                            newline = default_newline
                    return native_open(file, mode, buffering, encoding, errors,
                                       newline, closefd, opener)

                with self.subTest(default_newline=repr(default_newline)), patch('io.open', platform_open):
                    tasks.write(root / 'task.json', value)
                    tasks.write(root / 'handoff.md', markdown, text=True)
                    expected = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
                    self.assertEqual((root / 'task.json').read_bytes(), expected)
                    self.assertEqual((root / 'handoff.md').read_bytes(), markdown.encode('utf-8'))


class LegacyRecordNewlineTests(TaskFixture):
    def test_legacy_crlf_evidence_survives_reading_and_new_verification(self):
        self.prepare()
        self.verify()
        self.draft()
        folder = self.root / '.team-workflow/tasks'
        for path in folder.rglob('*'):
            if path.is_file():
                path.write_bytes(path.read_bytes().replace(b'\r\n', b'\n').replace(b'\n', b'\r\n'))
        before = {path: path.read_bytes() for path in folder.rglob('*') if path.is_file()}
        self.assertEqual(self.resume()['checks']['unit']['status'], 'passed')
        self.lint()
        self.assertEqual({path: path.read_bytes() for path in before}, before)
        record = self.verify()
        self.assertEqual(record['status'], 'passed')
        self.assertNotIn(b'\r\n', (self.root / record['task_evidence']).read_bytes())
        self.assertEqual({path: path.read_bytes() for path in before}, before)
