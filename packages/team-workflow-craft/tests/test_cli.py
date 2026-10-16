"""Run the real built product after removing its temporary source checkout."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

PACKAGE = Path(__file__).resolve().parents[1]


class InstalledProductTests(unittest.TestCase):
    def test_real_artifact_three_host_paths_and_offline_workflow(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            source = root / 'source'
            source.mkdir()
            shutil.copytree(PACKAGE / 'skills', source / 'skills', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            shutil.copytree(PACKAGE / 'scripts', source / 'scripts', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            for name in ('VERSION', 'LICENSE'):
                shutil.copyfile(PACKAGE / name, source / name)
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
            env.pop('PYTHONPATH', None)

            def run(argv, cwd=root, expected=0):
                result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, timeout=45)
                self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                return result.stdout

            output = root / 'artifacts'
            built = json.loads(run([sys.executable, str(source / 'scripts/build.py'), '--output-dir', str(output)]))
            artifact = Path(built['artifact'])
            projects = {}
            for host in ('codex', 'claude', 'pi'):
                project = root / host
                project.mkdir()
                relative = '.claude' if host == 'claude' else '.agents'
                command = [sys.executable, str(source / 'scripts/install.py'), '--artifact', str(artifact),
                           '--project', str(project), '--host', host]
                plan = json.loads(run(command))
                self.assertEqual(plan['status'], 'dry_run')
                self.assertFalse((project / relative).exists())
                installed = json.loads(run(command + ['--apply']))
                self.assertEqual(installed['status'], 'install')
                projects[host] = (project, project / relative / 'skills/team-workflow-craft/scripts/twc.py')
            # All subsequent invocations run from the installed bundle, with no source copy available.
            shutil.rmtree(source)
            for host, (project, cli) in projects.items():
                with self.subTest(host=host):
                    self.assertIn('prepare', run([sys.executable, str(cli), '--help'], project))
                    self.assertEqual(run([sys.executable, str(cli), '--version'], project).strip(),
                                     (PACKAGE / 'VERSION').read_text().strip())
            project, cli = projects['codex']
            git = ['git', '-C', str(project)]
            run(git + ['init', '-q', '-b', 'main'])
            run(git + ['config', 'user.name', 'Fixture'])
            run(git + ['config', 'user.email', 'fixture@example.invalid'])
            run(git + ['config', 'core.hooksPath', str(project / 'no-hooks')])
            (project / '.gitignore').write_text('.agents/\n.claude/\n')
            (project / 'check.py').write_text('assert 2 + 2 == 4\n')
            run(git + ['add', '.gitignore', 'check.py'])
            run(git + ['commit', '-qm', 'fixture'])
            command = [sys.executable, str(cli), '--project', str(project)]
            init = ['init', '--provider', 'cnb', '--base-url', 'https://cnb.cool', '--repository', 'team/project', '--base-ref', 'main']
            self.assertFalse(json.loads(run(command + init))['applied'])
            self.assertTrue(json.loads(run(command + init + ['--apply']))['applied'])
            config = project / '.team-workflow/config.toml'
            with config.open('a') as stream:
                stream.write('\n[checks.unit]\nargv = ' + json.dumps([sys.executable, 'check.py']) + '\ncwd = "."\n')
            doctor = json.loads(run(command + ['doctor']))
            self.assertEqual(doctor['toolchain']['status'], 'matched')
            self.assertEqual(doctor['host_loading'], 'unverified')
            self.assertEqual(doctor['actor']['platform']['provider'], 'cnb')
            self.assertEqual(doctor['actor']['git']['author']['name'], 'Fixture')
            contract = dict(goal='test a feature', non_goals=[], scope=['check.py'], dependencies=[],
                            acceptance=['arithmetic check'], integrator='maintainer', contracts=[], complexity='L1', risk='normal')
            (project / 'contract.json').write_text(json.dumps(contract))
            run(git + ['add', '.team-workflow/config.toml', '.team-workflow/toolchain.lock.json', '.team-workflow/.gitignore', 'contract.json'])
            run(git + ['commit', '-qm', 'workflow'])
            packet = json.loads(run(command + ['prepare', '--task', 'pr:8', '--contract', 'contract.json', '--offline']))
            preview = json.loads(run(command + ['verify']))
            record = json.loads(run(command + ['verify', '--execute', '--approved-policy', preview['policy_sha256']]))
            self.assertEqual(record['status'], 'passed')
            draft = json.loads(run(command + ['handoff', '--packet', packet['packet'], '--evidence', record['evidence'],
                                               '--done', 'feature complete', '--next', 'review']))
            self.assertEqual(draft['readiness'], 'unknown')
            self.assertTrue((project / draft['markdown']).exists())
            self.assertFalse(draft['merge_authorized'])
            self.assertEqual(draft['actor']['git']['committer']['email'], 'fixture@example.invalid')
            self.assertIn('verification_actor_unverified', draft['unknowns'])
            rejected = json.loads(run(command + ['handoff', '--publish', '--packet', packet['packet']], expected=2))
            self.assertIn('unsupported', rejected['message'])


if __name__ == '__main__':
    unittest.main()
