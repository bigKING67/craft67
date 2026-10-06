"""Exercise the actual workflow input guards in disposable Git repositories."""
import importlib.util
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def run_block(workflow, step):
    text = (ROOT / '.github/workflows' / workflow).read_text()
    start = text.index(f'      - name: {step}\n')
    block = text[start:].split('\n      - ', 1)[0]
    match = re.search(r'        run: \|\n((?:          .*\n|\n)+)', block + '\n')
    if match is None:
        raise AssertionError(f'missing executable block: {step}')
    return '\n'.join(line[10:] for line in match[1].splitlines())


class DesignWorkflowInputsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo'
        self.package = self.repo / 'packages/design-craft'
        self.package.mkdir(parents=True)
        (self.package / 'VERSION').write_text('1.2.3\n')
        self.baseline = 'benchmarks/baselines/fixture.json'
        path = self.package / self.baseline
        path.parent.mkdir(parents=True)
        path.write_text('{}\n')
        self.git('init', '-q', '-b', 'main')
        self.git('config', 'user.name', 'Workflow Test')
        self.git('config', 'user.email', 'workflow@example.invalid')
        self.git('add', '--', 'packages/design-craft')
        self.git('commit', '-qm', 'fixture')
        self.tag = 'design-craft/v1.2.3'
        self.git('tag', '-a', self.tag, '-m', 'fixture tag')
        self.env = {**os.environ, 'GITHUB_REF': f'refs/tags/{self.tag}',
                    'GITHUB_SHA': self.git('rev-parse', 'HEAD').strip(),
                    'BENCHMARK_BASELINE': self.baseline, 'NATIVE_RUN_ID': '123'}

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.repo,
                                       stderr=subprocess.PIPE, text=True)

    def candidate(self, **overrides):
        return subprocess.run(['bash', '-c', run_block('benchmark.yml', 'Validate candidate inputs')],
                              cwd=self.package, env={**self.env, **overrides},
                              capture_output=True, text=True)

    def test_root_workflows_preserve_original_artifact_contract(self):
        validator = ROOT / 'packages/design-craft/scripts/design_craft_workflow_validate.py'
        spec = importlib.util.spec_from_file_location('design_workflow_contract', validator)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        producer = (ROOT / '.github/workflows/benchmark.yml').read_text()
        consumer = (ROOT / '.github/workflows/release-certify.yml').read_text()
        self.assertEqual(module.benchmark_artifact_contract_errors(producer, consumer), [])
        broken = consumer.replace('benchmark-result-full.json', 'wrong-name.json')
        self.assertTrue(module.benchmark_artifact_contract_errors(producer, broken))

    def test_exact_annotated_tag_and_committed_baseline_pass(self):
        result = self.candidate()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_wrong_ref_sha_run_and_baseline_fail_closed(self):
        for change in ({'GITHUB_REF': 'refs/heads/main'},
                       {'GITHUB_REF': 'refs/tags/v1.2.3'},
                       {'GITHUB_REF': 'refs/tags/browser67/v1.2.3'},
                       {'GITHUB_SHA': '0' * 40},
                       {'NATIVE_RUN_ID': '0'},
                       {'NATIVE_RUN_ID': '123; echo invalid'},
                       {'BENCHMARK_BASELINE': '../fixture.json'}):
            with self.subTest(change=change):
                self.assertNotEqual(self.candidate(**change).returncode, 0)

    def test_lightweight_tag_and_untracked_baseline_are_rejected(self):
        self.git('tag', '-d', self.tag)
        self.git('tag', self.tag)
        self.assertNotEqual(self.candidate().returncode, 0)
        self.git('tag', '-d', self.tag)
        self.git('tag', '-a', self.tag, '-m', 'fixture tag')
        untracked = 'benchmarks/baselines/untracked.json'
        (self.package / untracked).write_text('{}')
        self.assertNotEqual(self.candidate(BENCHMARK_BASELINE=untracked).returncode, 0)

    def test_certification_requires_main_and_namespaced_tag(self):
        # Only the external existence query is stubbed; Git checks run for real.
        bin_dir = self.root / 'bin'
        bin_dir.mkdir()
        gh = bin_dir / 'gh'
        gh.write_text('#!/bin/sh\nexit 1\n')
        gh.chmod(0o755)
        env = {**self.env, 'PATH': f'{bin_dir}:{os.environ["PATH"]}',
               'GITHUB_REF': 'refs/heads/main', 'RELEASE_TAG': self.tag,
               'CONFIRM_CERTIFICATION': f'certify-{self.tag}',
               'RELEASE_LEVEL': 'operational_95', 'BENCHMARK_RUN_ID': '456',
               'PHYSICAL_DEVICE_RUN_ID': '', 'GITHUB_RUN_ID': '789',
               'GITHUB_ENV': str(self.root / 'github-env')}
        script = run_block('release-certify.yml', 'Verify immutable certification inputs')
        result = subprocess.run(['bash', '-c', script], cwd=self.package, env=env,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('CERTIFICATION_ARTIFACT_NAME=release-certification-design-craft-v1.2.3-789',
                      (self.root / 'github-env').read_text())
        for change in ({'GITHUB_REF': f'refs/tags/{self.tag}'},
                       {'RELEASE_TAG': 'browser67/v1.2.3'},
                       {'GITHUB_SHA': '0' * 40},
                       {'CONFIRM_CERTIFICATION': 'wrong'}):
            with self.subTest(change=change):
                rejected = subprocess.run(['bash', '-c', script], cwd=self.package,
                                          env={**env, **change}, capture_output=True)
                self.assertNotEqual(rejected.returncode, 0)


if __name__ == '__main__':
    unittest.main()
