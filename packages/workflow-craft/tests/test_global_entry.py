"""Installed global entry -> independent project pin -> preserved local version."""
import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE / 'scripts'))
import install
import packaging
sys.path.insert(0, str(PACKAGE / 'skills/workflow-craft/scripts'))
from twc_lib import entry, policy
from twc_lib.models import WorkflowError


class GlobalEntryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.home = self.root / 'user'
        self.home.mkdir()
        self.artifact, _, _ = packaging.create_artifact(PACKAGE, self.root / 'artifacts')
        self.env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', GIT_CONFIG_GLOBAL=os.devnull,
                        GIT_CONFIG_SYSTEM=os.devnull, GIT_CONFIG_COUNT='0', GIT_TERMINAL_PROMPT='0')

    def install_global(self, host='codex', apply=True, artifact=None, upgrade=False):
        args = ['--artifact', str(artifact or self.artifact), '--global', '--host', host]
        if apply:
            args.append('--apply')
        if upgrade:
            args.append('--allow-upgrade')
        out = io.StringIO()
        with patch.object(Path, 'home', return_value=self.home), contextlib.redirect_stdout(out):
            self.assertEqual(install.main(args), 0)
        return json.loads(out.getvalue())

    def project(self, name='project'):
        path = self.root / name
        path.mkdir()
        for args in [('init', '-q'), ('config', 'user.name', 'Member'),
                     ('config', 'user.email', 'fixture@example.invalid'),
                     ('config', 'core.hooksPath', str(self.root / 'no-hooks')),
                     ('commit', '--allow-empty', '-qm', 'base')]:
            subprocess.run(['git', '-C', str(path), *args], env=self.env, check=True, capture_output=True)
        (path / 'AGENTS.md').write_bytes(b'Keep project rules\r\n')
        return path

    def cli(self, cli, project, *args, expected=0):
        p = subprocess.run([sys.executable, '-B', str(cli), '--project', str(project), *args],
                           env=self.env, capture_output=True, text=True, encoding='utf-8', timeout=30)
        self.assertEqual(p.returncode, expected, p.stdout + p.stderr)
        return json.loads(p.stdout)

    def test_explicit_global_targets_preview_idempotency_and_no_settings_changes(self):
        settings = self.home / 'settings.json'
        settings.write_bytes(b'keep')
        for host in ('codex', 'claude', 'pi'):
            preview = self.install_global(host, apply=False)
            self.assertEqual(Path(preview['target']).exists(), host == 'pi')
            installed = self.install_global(host)
            self.assertEqual(installed['scope'], 'global')
            self.assertEqual(self.install_global(host)['status'], 'already_installed')
        self.assertEqual(settings.read_bytes(), b'keep')

    def test_global_alias_is_not_duplicated_or_overwritten(self):
        for relative in ('.codex/skills/workflow-craft', '.pi/agent/skills/team-workflow-craft'):
            alias = self.home / relative
            alias.mkdir(parents=True)
            sentinel = alias / 'SKILL.md'
            sentinel.write_bytes(b'user owned')
            args = install.parse_args(['--artifact', str(self.artifact), '--global', '--host', 'codex'])
            with patch.object(Path, 'home', return_value=self.home):
                with self.assertRaisesRegex(packaging.PackagingError, 'another global'):
                    install.resolve_target(args)
            self.assertEqual(sentinel.read_bytes(), b'user owned')
            self.assertFalse((self.home / '.agents/skills/workflow-craft').exists())
            shutil.rmtree(alias)

    def test_new_projects_choose_mode_then_pin_without_touching_rules(self):
        global_cli = Path(self.install_global()['target']) / 'scripts/twc.py'
        for host, mode in (('codex', 'personal'), ('claude', 'team'), ('pi', 'personal')):
            project = self.project(host)
            child = project / 'src'
            child.mkdir()
            view = self.cli(global_cli, child, 'entry', '--host', host, expected=1)
            self.assertEqual(view['action'], 'pin_project_runtime')
            self.assertFalse((project / '.team-workflow').exists())
            self.assertFalse(Path(view['target']).exists())
            preflight = self.cli(global_cli, child, 'doctor', '--local', expected=1)
            self.assertEqual(preflight['development_mode']['status'], 'selection_required')
            blocked = self.cli(global_cli, child, 'init', '--mode', mode, '--apply', expected=1)
            self.assertFalse((project / '.team-workflow').exists())
            pinned = self.cli(global_cli, child, 'entry', '--host', host, '--apply')
            local_cli = Path(pinned['cli'])
            self.assertTrue(pinned['applied'])
            # Pinning itself cannot silently choose a mode.
            self.assertFalse((project / '.team-workflow').exists())
            self.cli(local_cli, child, 'init', '--mode', mode, '--apply')
            before = {p.relative_to(project): p.read_bytes() for p in (project / '.team-workflow').rglob('*') if p.is_file()}
            second = self.cli(global_cli, child, 'entry', '--host', host, '--apply')
            self.assertFalse(second['applied'])
            self.assertEqual(second['cli'], str(local_cli))
            self.assertEqual(before, {p.relative_to(project): p.read_bytes() for p in (project / '.team-workflow').rglob('*') if p.is_file()})
            self.assertEqual((project / 'AGENTS.md').read_bytes(), b'Keep project rules\r\n')
            selection = self.cli(global_cli, child, 'resume', expected=1)
            self.assertEqual(selection['action'], 'use_project_runtime')
            self.assertEqual(self.cli(local_cli, child, 'mode')['development_mode']['current'], mode)
            other = 'team' if mode == 'personal' else 'personal'
            preview = self.cli(local_cli, child, 'mode', '--set', other)
            self.cli(local_cli, child, 'mode', '--set', other, '--apply', '--approved-policy', preview['policy_sha256'])
            self.assertEqual(self.cli(local_cli, child, 'mode')['development_mode']['current'], other)

    def test_global_upgrade_preserves_project_pin_and_lock(self):
        global_cli = Path(self.install_global()['target']) / 'scripts/twc.py'
        project = self.project()
        pinned = self.cli(global_cli, project, 'entry', '--host', 'codex', '--apply')
        self.cli(pinned['cli'], project, 'init', '--mode', 'team', '--apply')
        lock = (project / '.team-workflow/toolchain.lock.json').read_bytes()
        source = self.root / 'new-source'
        shutil.copytree(PACKAGE / 'skills', source / 'skills', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        shutil.copyfile(PACKAGE / 'LICENSE', source / 'LICENSE')
        (source / 'VERSION').write_text('99.0.0\n', encoding='utf-8')
        artifact, _, _ = packaging.create_artifact(source, self.root / 'new-artifact')
        self.install_global(artifact=artifact, upgrade=True)
        result = self.cli(global_cli, project, 'entry', '--host', 'claude', '--apply')
        self.assertEqual(result['runtime'], pinned['runtime'])
        self.assertEqual(result['cli'], pinned['cli'])
        self.assertEqual((project / '.team-workflow/toolchain.lock.json').read_bytes(), lock)
        self.assertFalse((project / '.claude').exists())

    def test_drift_missing_runtime_and_conflicting_entries_never_fall_back(self):
        global_cli = Path(self.install_global()['target']) / 'scripts/twc.py'
        for scenario in ('drift', 'missing', 'lock', 'legacy', 'conflict'):
            with self.subTest(scenario=scenario):
                project = self.project(scenario)
                pin = self.cli(global_cli, project, 'entry', '--host', 'codex', '--apply')
                local = Path(pin['cli']).parent.parent
                self.cli(pin['cli'], project, 'init', '--mode', 'personal', '--apply')
                state = project / '.team-workflow'
                if scenario == 'drift':
                    (local / 'SKILL.md').write_text('edited', encoding='utf-8')
                elif scenario == 'missing':
                    shutil.rmtree(local)
                elif scenario == 'lock':
                    (state / 'toolchain.lock.json').write_text('{}', encoding='utf-8')
                elif scenario == 'legacy':
                    local.with_name('team-workflow-craft').mkdir()
                else:
                    other = project / '.claude/skills/workflow-craft'
                    shutil.copytree(local, other)
                    (other / 'VERSION').write_bytes(b'99.0.0\n')
                    marker = json.loads((other / packaging.INSTALL_MARKER).read_bytes())
                    for row in marker['files']:
                        if row['path'] == 'VERSION':
                            row.update(sha256=packaging.sha256_bytes(b'99.0.0\n'), size=7)
                    (other / packaging.INSTALL_MARKER).write_bytes(packaging.canonical_json(marker))
                before = {p.relative_to(state): p.read_bytes() for p in state.rglob('*') if p.is_file()}
                self.cli(global_cli, project, 'entry', '--host', 'codex', '--apply', expected=2)
                self.assertEqual(before, {p.relative_to(state): p.read_bytes() for p in state.rglob('*') if p.is_file()})

    def test_parent_symlink_cannot_write_outside_project(self):
        global_cli = Path(self.install_global()['target']) / 'scripts/twc.py'
        project = self.project()
        outside = self.root / 'outside'
        outside.mkdir()
        try:
            (project / '.agents').symlink_to(outside, target_is_directory=True)
        except OSError as error:
            self.skipTest(str(error))
        self.cli(global_cli, project, 'entry', '--host', 'codex', '--apply', expected=2)
        self.assertEqual(list(outside.iterdir()), [])

    def test_older_protocol_is_selected_by_its_own_content_not_global_constant(self):
        global_cli = Path(self.install_global()['target']) / 'scripts/twc.py'
        project = self.project()
        pin = self.cli(global_cli, project, 'entry', '--host', 'codex', '--apply')
        local = Path(pin['cli']).parent.parent
        module = local / 'scripts/twc_lib/policy.py'
        module.write_bytes(module.read_bytes().replace(b'protocol_version=3', b'protocol_version=2'))
        marker = json.loads((local / packaging.INSTALL_MARKER).read_bytes())
        for row in marker['files']:
            if row['path'] == 'scripts/twc_lib/policy.py':
                row.update(sha256=packaging.sha256_bytes(module.read_bytes()), size=module.stat().st_size)
        (local / packaging.INSTALL_MARKER).write_bytes(packaging.canonical_json(marker))
        self.cli(pin['cli'], project, 'init', '--mode', 'personal', '--apply')
        self.assertEqual(json.loads((project / '.team-workflow/toolchain.lock.json').read_bytes())['protocol_version'], 2)
        selected = self.cli(global_cli, project, 'entry', '--host', 'codex')
        self.assertEqual(selected['cli'], pin['cli'])
        self.assertEqual(self.cli(pin['cli'], project, 'doctor', '--local')['toolchain']['status'], 'matched')

    def test_parent_replacement_after_inspection_cannot_publish_outside_project(self):
        global_root = Path(self.install_global()['target'])
        for when in ('initial', 'publication', 'same_displaced'):
            with self.subTest(when=when):
                project = self.project(when)
                parent = project / '.agents'
                (parent / 'skills').mkdir(parents=True)
                target = parent / 'skills/workflow-craft'
                outside = self.root / (when + '-outside')
                outside.mkdir()
                displaced = self.root / (when + '-displaced')
                check = entry.safe_path
                calls = 0

                def replace_after_check(root, path):
                    nonlocal calls
                    check(root, path)
                    if path == target:
                        calls += 1
                        if calls == (1 if when == 'initial' else 2):
                            # Windows may reject the rename because the parent
                            # is held without delete sharing; that is the guard.
                            parent.rename(displaced)
                            parent.symlink_to(displaced if when == 'same_displaced' else outside, target_is_directory=True)

                with patch.object(policy, 'SKILL_ROOT', global_root), patch.object(entry, 'safe_path', side_effect=replace_after_check):
                    with self.assertRaises((WorkflowError, OSError)):
                        entry.select(project, 'codex', apply=True)
                self.assertEqual(list(outside.iterdir()), [])
                self.assertFalse((displaced / 'skills/workflow-craft').exists())
                self.assertEqual(list(displaced.glob('skills/.workflow-craft-entry-*')), [])
