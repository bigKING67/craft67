"""Completed task evidence survives Git's platform-specific checkout settings."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from test_workflow import RUNTIME
from twc_lib import evidence, lifecycle, policy, tasks
from twc_lib.models import WorkflowError


class PolicyPortabilityTests(unittest.TestCase):
    def roundtrip(self, newline):
        with tempfile.TemporaryDirectory() as temporary, patch.dict(os.environ, {
            'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_SYSTEM': os.devnull,
            'GIT_CONFIG_COUNT': '0', 'GIT_TERMINAL_PROMPT': '0',
        }):
            root = Path(temporary).resolve()
            source = root / 'source'
            source.mkdir()

            def git(project, *args):
                return subprocess.check_output(['git', '-C', str(project), *args],
                                               stderr=subprocess.PIPE, text=True).strip()

            git(source, 'init', '-q', '-b', 'main')
            git(source, 'config', 'user.name', 'Fixture')
            git(source, 'config', 'user.email', 'fixture@example.invalid')
            git(source, 'config', 'core.autocrlf', 'false')
            # The business contract has its own byte contract; the workflow
            # initializer must protect its policy without editing root rules.
            attributes = b'/contract.json -text\n'
            (source / '.gitattributes').write_bytes(attributes)
            git(source, 'add', '.gitattributes')
            git(source, 'commit', '-qm', 'baseline')
            base = git(source, 'rev-parse', 'HEAD')
            policy.init(source, None, None, base, apply=True, mode='personal')
            path = source / '.team-workflow/config.toml'
            self.assertNotIn(b'\r\n', path.read_bytes())
            content = path.read_text(encoding='utf-8')
            content += '\n[checks.unit]\nargv = ' + json.dumps([sys.executable, '-c', 'print("ok")'])
            content += '\ncwd = "."\ntimeout_seconds = 5\n'
            path.write_bytes(content.replace('\n', newline).encode('utf-8'))
            contract = dict(goal='Portable evidence', non_goals=[], scope=['contract.json'], dependencies=[],
                            acceptance=[dict(text='unit passes', checks=['unit'])], contracts=[],
                            complexity='L1', risk='normal')
            (source / 'contract.json').write_bytes(json.dumps(contract).encode('utf-8'))
            git(source, 'add', '--', '.team-workflow', 'contract.json')
            git(source, 'commit', '-qm', 'workflow configuration')
            config, sha = policy.load(source)
            lifecycle.create(source, config, sha, 'local:portable', 'contract.json', session='source')
            lifecycle.transition(source, config, sha, 'start', 'local:portable', 'source')
            result = evidence.verify(source, config, sha, execute_commands=True,
                                     approved_policy=sha, session='source')
            self.assertEqual(result['status'], 'passed')
            self.assertEqual(lifecycle.transition(source, config, sha, 'complete',
                                                  'local:portable', 'source')['execution_state'], 'completed')
            git(source, 'add', '--', '.team-workflow/tasks')
            git(source, 'commit', '-qm', 'completed task')
            self.assertEqual((source / '.gitattributes').read_bytes(), attributes)

            for autocrlf in ('true', 'false'):
                with self.subTest(autocrlf=autocrlf, newline=repr(newline)):
                    clone = root / ('receiver-' + autocrlf)
                    git(root, 'clone', '-q', '-c', 'core.autocrlf=' + autocrlf, str(source), str(clone))
                    self.assertEqual((clone / '.team-workflow/config.toml').read_bytes(), path.read_bytes())
                    received, received_sha = policy.load(clone)
                    self.assertEqual(received_sha, sha)
                    view = tasks.resume(clone, received, received_sha, policy.runtime_identity(),
                                        None, 'local:portable')
                    self.assertEqual(view['execution']['completion'], 'current')
                    self.assertEqual(view['checks']['unit']['status'], 'passed')
                    # An actual policy edit must still invalidate evidence and
                    # reject the approval bound to the previous policy bytes.
                    changed = clone / '.team-workflow/config.toml'
                    changed.write_bytes(changed.read_bytes().replace(b'timeout_seconds = 5', b'timeout_seconds = 6'))
                    updated, new_sha = policy.load(clone)
                    self.assertNotEqual(new_sha, sha)
                    view = tasks.resume(clone, updated, new_sha, policy.runtime_identity(), None, 'local:portable')
                    self.assertEqual(view['execution']['completion'], 'stale')
                    with self.assertRaisesRegex(WorkflowError, 'current policy_sha256'):
                        evidence.verify(clone, updated, new_sha, execute_commands=True, approved_policy=sha)

    def test_lf_policy_survives_windows_style_checkout(self):
        self.roundtrip('\n')

    def test_crlf_policy_is_preserved_by_both_checkout_styles(self):
        self.roundtrip('\r\n')
