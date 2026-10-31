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


class RuntimeVersionTests(unittest.TestCase):
    def test_unsupported_python_reports_json_before_loading_runtime(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cli = root / 'twc.py'
            # No runtime libraries are present: the version error must precede imports.
            shutil.copyfile(PACKAGE / 'skills/workflow-craft/scripts/twc.py', cli)
            project = root / 'project'
            for version in ((3, 9, 6), (3, 10, 99)):
                with self.subTest(version=version):
                    program = (
                        'import runpy, sys; '
                        f'sys.version_info = {version!r}; '
                        f'sys.argv = [{str(cli)!r}, "--project", {str(project)!r}, "resume"]; '
                        f'runpy.run_path({str(cli)!r}, run_name="__main__")'
                    )
                    result = subprocess.run(
                        [sys.executable, '-c', program], cwd=root,
                        env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'),
                        capture_output=True, text=True, timeout=10)
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertEqual(result.stderr, '')
                    report = json.loads(result.stdout)
                    self.assertEqual(report['status'], 'error')
                    self.assertEqual(report['required_python'], '>=3.11')
                    self.assertEqual(report['python'], '.'.join(map(str, version)))
                    self.assertFalse(project.exists())
                    self.assertFalse((root / '__pycache__').exists())


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
            env = {key: value for key, value in os.environ.items()
                   if key in ('PATH', 'HOME', 'USER', 'LOGNAME', 'TMPDIR', 'TMP', 'TEMP', 'LANG', 'LC_ALL', 'SYSTEMROOT', 'USERPROFILE', 'HOMEDRIVE', 'HOMEPATH')}
            env.update(PYTHONDONTWRITEBYTECODE='1', GIT_CONFIG_GLOBAL=os.devnull,
                       GIT_CONFIG_SYSTEM=os.devnull, GIT_CONFIG_COUNT='0', GIT_TERMINAL_PROMPT='0')

            def run(argv, cwd=root, expected=0):
                result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, encoding='utf-8', timeout=45)
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
                projects[host] = (project, project / relative / 'skills/workflow-craft/scripts/twc.py')
            # All subsequent invocations run from the installed bundle, with no source copy available.
            shutil.rmtree(source)
            for host, (project, cli) in projects.items():
                with self.subTest(host=host):
                    git = ['git', '-C', str(project)]
                    run(git + ['init', '-q', '-b', 'main'])
                    status = cli.with_name('workflow_status.py')
                    self.assertEqual(run([sys.executable, '-B', str(status), '--project', str(project)]).strip(),
                                     'Workflow: 未配置')
                    self.assertTrue((cli.parent.parent / 'assets/adapters/pi-status.ts').is_file())
                    run(git + ['config', 'core.hooksPath', str(project / 'no-hooks')])
                    self.assertIn('prepare', run([sys.executable, str(cli), '--help'], project))
                    self.assertEqual(run([sys.executable, str(cli), '--version'], project).strip(),
                                     (PACKAGE / 'VERSION').read_text().strip())
                    preflight = json.loads(run([sys.executable, str(cli), 'doctor', '--local'], project, expected=1))
                    self.assertEqual(preflight['installation_integrity'], 'matched')
                    self.assertTrue(any(row['is_current'] and row['matches_runtime']
                                        for row in preflight['project_entries']))
                    self.assertEqual(preflight['member']['status'], 'missing')
                    self.assertIn('configure_member_name', preflight['next_steps'])
                    run(git + ['config', 'user.name', 'Fixture'])
                    named = json.loads(run([sys.executable, str(cli), 'doctor', '--local'], project, expected=1))
                    self.assertEqual(named['member']['name'], 'Fixture')
                    self.assertEqual(named['member']['status'], 'available')
                    self.assertNotIn('configure_member_name', named['next_steps'])
                    self.assertFalse((project / '.team-workflow').exists())
            project, cli = projects['codex']
            git = ['git', '-C', str(project)]
            run(git + ['config', 'user.email', 'fixture@example.invalid'])
            (project / '.gitignore').write_text('.agents/\n.claude/\n')
            (project / 'check.py').write_text('assert 2 + 2 == 4\n')
            run(git + ['add', '.gitignore', 'check.py'])
            run(git + ['commit', '-qm', 'fixture'])
            command = [sys.executable, str(cli), '--project', str(project)]
            init = ['init', '--mode', 'team', '--provider', 'cnb', '--base-url', 'https://cnb.cool', '--repository', 'team/project', '--base-ref', 'main']
            self.assertFalse(json.loads(run(command + init))['applied'])
            self.assertTrue(json.loads(run(command + init + ['--apply']))['applied'])
            self.assertEqual(run([sys.executable, '-B', str(cli.with_name('workflow_status.py')),
                                  '--project', str(project)]).strip(), 'Workflow: team')
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
            run(git + ['add', '.team-workflow/config.toml', '.team-workflow/toolchain.lock.json', '.team-workflow/.gitignore', '.team-workflow/.gitattributes', 'contract.json'])
            run(git + ['commit', '-qm', 'workflow'])
            run(git + ['config', '--unset', 'user.name'])
            run(git + ['config', '--unset', 'user.email'])
            initial = json.loads(run(command + ['resume']))
            self.assertIn('configure_member_name', initial['next_actions'])
            run(git + ['config', 'user.name', '67'])
            self.assertEqual(json.loads(run(command + ['doctor', '--local']))['member']['name'], '67')
            prepared = json.loads(run(command + ['prepare', '--task', 'pr:8', '--contract', 'contract.json', '--offline']))
            self.assertEqual(prepared['task_record'], '.team-workflow/tasks/pr-8/task.json')
            task_path = project / prepared['task_record']
            task_before = task_path.read_bytes()
            self.assertEqual(json.loads(task_before)['recorded_by']['member']['name'], '67')
            run(git + ['config', 'user.name', '小王'])
            reparsed = json.loads(run(command + ['prepare', '--task', 'pr:8', '--contract', 'contract.json', '--offline']))
            self.assertEqual(reparsed['actor']['member']['name'], '小王')
            self.assertEqual(task_path.read_bytes(), task_before)
            preview = json.loads(run(command + ['verify']))
            record = json.loads(run(command + ['verify', '--execute', '--approved-policy', preview['policy_sha256']]))
            self.assertEqual(record['status'], 'passed')
            self.assertTrue((project / record['task_evidence']).is_file())
            evidence_path = project / record['task_evidence']
            evidence_before = evidence_path.read_bytes()
            self.assertEqual(json.loads(evidence_before)['actor']['member']['name'], '小王')
            run(git + ['config', 'user.name', '小李'])
            view = json.loads(run(command + ['resume']))
            self.assertEqual(view['acceptance'][0]['status'], 'needs_review')
            self.assertEqual(view['checks']['unit']['status'], 'passed')
            self.assertEqual(view['member']['name'], '小李')
            self.assertNotIn('configure_member_name', view['next_actions'])
            draft = json.loads(run(command + ['handoff', '--done', 'feature complete', '--next', 'review']))
            self.assertEqual(draft['readiness'], 'unknown')
            self.assertTrue((project / draft['markdown']).exists())
            self.assertFalse(draft['merge_authorized'])
            self.assertEqual(draft['actor']['git']['status'], 'incomplete')
            self.assertEqual(draft['prepared_by']['member']['name'], '67')
            self.assertEqual(draft['checks']['unit']['actor']['member']['name'], '小王')
            self.assertEqual(draft['actor']['member']['name'], '小李')
            markdown = (project / draft['markdown']).read_text(encoding='utf-8')
            for label in ('Prepared by: 67', 'executed by 小王', 'Handed off by: 小李'):
                self.assertIn(label + ' (self-reported name; platform identity unverified)', markdown)
            self.assertEqual(task_path.read_bytes(), task_before)
            self.assertEqual(evidence_path.read_bytes(), evidence_before)
            self.assertIn('verification_actor_unverified', draft['unknowns'])
            resumed = json.loads(run(command + ['resume']))
            self.assertEqual(resumed['handed_off_by']['member']['name'], '小李')
            self.assertEqual(json.loads(run(command + ['check']))['status'], 'ok')
            rejected = json.loads(run(command + ['handoff', '--publish'], expected=2))
            self.assertIn('unsupported', rejected['message'])

            # The same source-independent artifact supports a personal project with no remote or email.
            project, cli = projects['pi']
            git = ['git', '-C', str(project)]
            (project / '.gitignore').write_text('.agents/\n')
            (project / 'value.txt').write_text('ready\n')
            run(git + ['add', '.gitignore', 'value.txt'])
            run(git + ['-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture'])
            command = [sys.executable, str(cli), '--project', str(project)]
            self.assertEqual(json.loads(run(command + ['resume'], expected=1))['development_mode']['status'],
                             'selection_required')
            run(command + ['init', '--mode', 'personal', '--apply'])
            config = project / '.team-workflow/config.toml'
            with config.open('a') as stream:
                stream.write('\n[checks.unit]\nargv = ' + json.dumps([
                    sys.executable, '-c', 'from pathlib import Path; assert Path("value.txt").read_text() == "ready\\n"']) + '\n')
            contract = dict(goal='Keep local content readable', scope=['value.txt'], non_goals=[], dependencies=[],
                            contracts=[], complexity='L1', risk='normal',
                            acceptance=[dict(text='Local content is ready', checks=['unit'])])
            (project / 'contract.json').write_text(json.dumps(contract))
            run(git + ['add', '.team-workflow/config.toml', '.team-workflow/toolchain.lock.json',
                       '.team-workflow/.gitignore', '.team-workflow/.gitattributes', 'contract.json'])
            run(git + ['-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'workflow'])
            prepared = json.loads(run(command + ['prepare', '--task', 'local:content', '--contract', 'contract.json']))
            self.assertEqual(prepared['platform_status'], 'not_applicable')
            preview = json.loads(run(command + ['verify']))
            self.assertEqual(json.loads(run(command + ['verify', '--execute', '--approved-policy', preview['policy_sha256']]))['status'], 'passed')
            draft = json.loads(run(command + ['handoff', '--done', 'Content checked', '--next', 'Resume next session']))
            self.assertEqual(draft['readiness'], 'advisory_ready')
            self.assertEqual(draft['readiness_scope'], 'local_task')
            self.assertEqual(draft['actor']['git']['status'], 'incomplete')
            self.assertEqual(draft['actor']['platform']['status'], 'not_configured')
            self.assertFalse(draft['merge_authorized'])
            preview = json.loads(run(command + ['mode', '--set', 'team']))
            self.assertFalse(preview['applied'])
            run(command + ['mode', '--set', 'team', '--apply', '--approved-policy', preview['policy_sha256']])
            resumed = json.loads(run(command + ['resume']))
            self.assertEqual(resumed['development_mode']['current'], 'team')
            self.assertEqual(resumed['checks']['unit']['status'], 'stale')


if __name__ == '__main__':
    unittest.main()
