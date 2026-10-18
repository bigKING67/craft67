"""Installed CLI acceptance across independent clones; no host models or live platform."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PACKAGE = Path(__file__).resolve().parents[1]


@unittest.skipIf(os.name == 'nt', 'Complete verification requires POSIX process-tree support')
class CrossCloneAcceptanceTests(unittest.TestCase):
    def test_handoff_identity_and_revalidation_after_main_advances(self):
        with tempfile.TemporaryDirectory(prefix='twc-handoff-') as temporary:
            root = Path(temporary).resolve()
            env = {key: value for key, value in os.environ.items()
                   if key in ('PATH', 'HOME', 'USER', 'LOGNAME', 'TMPDIR', 'LANG', 'LC_ALL')}
            env.update(PYTHONDONTWRITEBYTECODE='1', GIT_CONFIG_GLOBAL=os.devnull,
                       GIT_CONFIG_SYSTEM=os.devnull, GIT_TERMINAL_PROMPT='0')

            def run(argv, cwd=root, expected=0):
                result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, timeout=45)
                self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                return result.stdout.strip()

            def git(project, *args):
                return run(['git', '-c', 'core.hooksPath=' + str(root / 'no-hooks'),
                            '-c', 'commit.gpgSign=false', '-C', str(project), *args])

            def identity(project, name):
                git(project, 'config', 'user.name', name)
                git(project, 'config', 'user.email', name.lower() + '@example.invalid')

            def commit(project, message, *paths):
                git(project, 'add', '--', *paths)
                git(project, 'commit', '-qm', message)

            artifact = json.loads(run([sys.executable, str(PACKAGE / 'scripts/build.py'),
                                       '--output-dir', str(root / 'artifacts')]))['artifact']

            def install(project, host):
                run([sys.executable, str(PACKAGE / 'scripts/install.py'), '--artifact', artifact,
                     '--project', str(project), '--host', host, '--apply'])
                directory = '.claude' if host == 'claude' else '.agents'
                return project / directory / 'skills/team-workflow-craft/scripts/twc.py'

            def twc(project, cli, *args, expected=0):
                return json.loads(run([sys.executable, str(cli), '--project', str(project), *args],
                                      cwd=project, expected=expected))

            def prepare(project, cli, *extra):
                return twc(project, cli, 'prepare', '--task', 'pr:8', '--contract', 'contract.json', '--offline', *extra)

            def verify(project, cli, expected=0):
                plan = twc(project, cli, 'verify')
                self.assertEqual(plan['status'], 'not_run')
                return twc(project, cli, 'verify', '--execute', '--approved-policy', plan['policy_sha256'],
                           expected=expected)

            def draft(project, cli):
                result = twc(project, cli, 'handoff', '--draft',
                             '--done', 'Implemented the agreed renderer', '--next', 'sixseven reviews integration')
                self.assertFalse(result['merge_authorized'])
                self.assertFalse(result['published'])
                return result

            def share(project, message):
                # Commit only the task directory, never another session's staged work.
                git(project, 'add', '--', '.team-workflow/tasks')
                git(project, 'commit', '-qm', message, '--', '.team-workflow/tasks')

            alice = root / 'alice'
            alice.mkdir()
            git(alice, 'init', '-q', '-b', 'main')
            identity(alice, 'Alice')
            cli_a = install(alice, 'claude')
            (alice / '.gitignore').write_text('.agents/\n.claude/\n__pycache__/\n')
            (alice / 'protocol.py').write_text('SUFFIX = ""\n')
            (alice / 'renderer.py').write_text('from protocol import SUFFIX\ndef render(text):\n    return text.strip() + SUFFIX\n')
            (alice / 'tests').mkdir()
            (alice / 'tests/test_core.py').write_text(
                'import unittest\nfrom protocol import SUFFIX\nfrom renderer import render\n'
                'class CoreTests(unittest.TestCase):\n'
                '    def test_suffix(self):\n        self.assertEqual(render(""), SUFFIX)\n')
            commit(alice, 'Synthetic baseline', '.gitignore', 'protocol.py', 'renderer.py', 'tests/test_core.py')
            # No external remote is contacted: origin is an isolated local bare repository.
            remote = root / 'shared.git'
            run(['git', 'init', '--bare', '-q', '-b', 'main', str(remote)])
            git(alice, 'remote', 'add', 'origin', str(remote))
            git(alice, 'push', '-q', '-u', 'origin', 'main')
            twc(alice, cli_a, 'init', '--provider', 'cnb', '--base-url', 'https://cnb.cool',
                '--repository', 'fixture/product', '--base-ref', 'origin/main', '--apply')
            config = alice / '.team-workflow/config.toml'
            with config.open('a') as stream:
                stream.write('\n[checks.unit]\nargv = ' + json.dumps(
                    [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests']) + '\ncwd = "."\n')
            contract = dict(goal='Trim and uppercase a name, then append the shared protocol suffix',
                            non_goals=['deployment'], scope=['renderer.py', 'tests'], dependencies=[],
                            acceptance=[dict(text='Core and feature checks pass together on the latest main', checks=['unit'])],
                            integrator='sixseven', contracts=['protocol.py'], complexity='L2', risk='normal')
            (alice / 'contract.json').write_text(json.dumps(contract))
            commit(alice, 'Shared workflow contract', '.team-workflow/config.toml',
                   '.team-workflow/toolchain.lock.json', '.team-workflow/.gitignore', 'contract.json')
            git(alice, 'push', '-q', 'origin', 'main')
            bob, integrator = root / 'bob', root / 'integrator'
            for project, name in ((bob, 'Bob'), (integrator, 'sixseven')):
                run(['git', '-c', 'core.hooksPath=' + str(root / 'no-hooks'), 'clone', '-q', str(remote), str(project)])
                identity(project, name)
            cli_b, cli_c = install(bob, 'codex'), install(integrator, 'pi')
            for project, cli in ((alice, cli_a), (bob, cli_b), (integrator, cli_c)):
                diagnosis = twc(project, cli, 'doctor')
                self.assertEqual(diagnosis['toolchain']['status'], 'matched')
                self.assertEqual(diagnosis['installation_integrity'], 'matched')
                self.assertEqual(diagnosis['host_loading'], 'unverified')
                self.assertFalse(twc(project, cli, 'workspace', 'inspect')['dirty'])

            git(alice, 'switch', '-qc', 'alice/renderer')
            prepare(alice, cli_a)
            (alice / 'renderer.py').write_text('from protocol import SUFFIX\ndef render(text):\n    return text.strip().upper()\n')
            (alice / 'tests/test_feature.py').write_text(
                'import unittest\nfrom protocol import SUFFIX\nfrom renderer import render\n'
                'class FeatureTests(unittest.TestCase):\n'
                '    def test_uppercase(self):\n        self.assertEqual(render(" Ada "), "ADA" + SUFFIX)\n')
            commit(alice, 'Implement uppercase on the original baseline', 'renderer.py', 'tests/test_feature.py')
            record_a = verify(alice, cli_a)
            self.assertEqual(record_a['status'], 'passed')
            self.assertEqual(draft(alice, cli_a)['readiness'], 'unknown')
            share(alice, 'twc: Alice hands off pr-8')
            git(alice, 'push', '-q', '-u', 'origin', 'alice/renderer')
            alice_head = git(alice, 'rev-parse', 'HEAD')
            (alice / 'unrelated-wip.txt').write_text('Keep the original developer work intact.\n')
            inspected = twc(alice, cli_a, 'workspace', 'inspect', '--scope', 'renderer.py')
            self.assertIn('unrelated-wip.txt', inspected['outside_scope'])

            # Bob continues from the pushed branch alone: no copied files, packet or binding.
            git(bob, 'fetch', '-q', 'origin')
            git(bob, 'switch', '-qc', 'bob/renderer', 'origin/alice/renderer')
            self.assertFalse((bob / '.team-workflow/local').exists())
            view = twc(bob, cli_b, 'resume')
            self.assertEqual(view['resolved_by'], 'branch_changes')
            self.assertEqual(view['last_handoff']['next_steps'], ['sixseven reviews integration'])
            self.assertEqual(view['acceptance'][0]['status'], 'verified')
            self.assertEqual(view['checks']['unit']['actor']['git']['author']['name'], 'Alice')
            self.assertEqual(view['handed_off_by']['git']['author']['name'], 'Alice')
            packet_b = prepare(bob, cli_b)
            self.assertEqual(packet_b['task_record_status'], 'unchanged')
            self.assertEqual(packet_b['actor']['git']['author']['name'], 'Bob')
            (bob / 'tests/test_empty.py').write_text(
                'import unittest\nfrom protocol import SUFFIX\nfrom renderer import render\n'
                'class EmptyTests(unittest.TestCase):\n'
                '    def test_empty(self):\n        self.assertEqual(render("  "), SUFFIX)\n')
            commit(bob, 'Add empty input acceptance', 'tests/test_empty.py')
            stale = draft(bob, cli_b)
            self.assertIn('stale_or_unrelated_evidence', stale['blockers'])
            self.assertIn('verify: unit', twc(bob, cli_b, 'resume')['next_actions'])
            record_b = verify(bob, cli_b)
            self.assertEqual(record_b['status'], 'passed')
            self.assertEqual(record_b['actor']['git']['author']['name'], 'Bob')

            # Main is independently green, but the combined product must be checked again.
            (integrator / 'protocol.py').write_text('SUFFIX = "!"\n')
            commit(integrator, 'Advance the public suffix protocol', 'protocol.py')
            run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests'], cwd=integrator)
            git(integrator, 'push', '-q', 'origin', 'main')
            git(bob, 'fetch', '-q', 'origin')
            stale_base = draft(bob, cli_b)
            self.assertEqual(stale_base['readiness'], 'not_ready')
            self.assertIn('local_base_not_integrated', stale_base['blockers'])
            self.assertIn('stale_or_unrelated_evidence', stale_base['blockers'])
            git(bob, 'merge', '--no-edit', 'origin/main')
            changed_contract = draft(bob, cli_b)
            self.assertIn('task_or_interface_contract_changed', changed_contract['blockers'])
            twc(bob, cli_b, 'prepare', '--task', 'pr:8', '--contract', 'contract.json', '--offline', expected=2)
            self.assertEqual(prepare(bob, cli_b, '--update-contract')['revision'], 2)
            combined = verify(bob, cli_b, expected=1)
            self.assertEqual(combined['status'], 'failed')
            self.assertIn('verification_not_passed', draft(bob, cli_b)['blockers'])
            (bob / 'renderer.py').write_text('from protocol import SUFFIX\ndef render(text):\n    return text.strip().upper() + SUFFIX\n')
            commit(bob, 'Honor the current shared protocol', 'renderer.py')
            fixed = verify(bob, cli_b)
            self.assertEqual(fixed['status'], 'passed')
            self.assertEqual(draft(bob, cli_b)['readiness'], 'unknown')
            share(bob, 'twc: Bob hands off pr-8')
            git(bob, 'push', '-q', '-u', 'origin', 'bob/renderer')

            git(integrator, 'fetch', '-q', 'origin')
            git(integrator, 'switch', '-qc', 'integration/renderer', 'origin/bob/renderer')
            view = twc(integrator, cli_c, 'resume')
            self.assertEqual(view['revision'], 2)
            self.assertEqual(view['handed_off_by']['git']['author']['name'], 'Bob')
            self.assertEqual(view['acceptance'][0]['status'], 'verified')
            self.assertEqual(twc(integrator, cli_c, 'check')['status'], 'ok')
            prepare(integrator, cli_c)
            record_c = verify(integrator, cli_c)
            final = draft(integrator, cli_c)
            self.assertEqual(record_c['status'], 'passed')
            self.assertEqual(final['actor']['git']['author']['name'], 'sixseven')
            self.assertEqual(final['integrator'], 'sixseven')
            self.assertEqual(final['readiness'], 'unknown')
            self.assertIn('platform_not_current', final['unknowns'])
            share(integrator, 'twc: integration evidence for pr-8')
            git(integrator, 'switch', '-q', 'main')
            git(integrator, 'merge', '--ff-only', 'integration/renderer')
            git(integrator, 'push', '-q', 'origin', 'main')
            # Committing task records does not change the verified code content.
            merged = twc(integrator, cli_c, 'workspace', 'inspect')
            self.assertEqual(merged['tree_sha256'], record_c['after']['tree_sha256'])
            self.assertEqual(git(remote, 'rev-parse', 'refs/heads/main'), merged['head'])
            self.assertEqual(git(alice, 'rev-parse', 'HEAD'), alice_head)
            self.assertEqual((alice / 'unrelated-wip.txt').read_text(), 'Keep the original developer work intact.\n')

if __name__ == '__main__':
    unittest.main()
