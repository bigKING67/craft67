from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT/'skills/money-craft/scripts'
sys.path.insert(0,str(SCRIPTS))
import money_craft as mc


class CliRuntimeTests(unittest.TestCase):
    def test_explicit_invalid_python_is_structured_configuration_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            not_executable = root/'not-executable';not_executable.write_text('fixture');not_executable.chmod(0o600)
            bad_executable = root/'bad-executable';bad_executable.write_text('not an executable format');bad_executable.chmod(0o700)
            for candidate in (str(root/'missing'),str(root),str(not_executable),str(bad_executable),'relative/python'):
                env = {key:value for key,value in os.environ.items() if not key.startswith('MONEY_CRAFT_')}
                env['MONEY_CRAFT_DATA_PYTHON'] = candidate
                with self.subTest(candidate=candidate):
                    result = subprocess.run([sys.executable,str(SCRIPTS/'money_craft.py'),'--help'],env=env,capture_output=True,text=True,timeout=10)
                    self.assertEqual(result.returncode,mc.EXIT_CONFIG,result.stdout+result.stderr)
                    self.assertEqual(json.loads(result.stdout)['error']['kind'],'invalid_configuration')
                    self.assertNotIn('Traceback',result.stderr)

    def test_valid_explicit_launcher_reexecutes_once_with_guard(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory);launcher = root/'launcher';marker = root/'marker'
            launcher.write_text('#!'+sys.executable+'\nimport os,sys\nfrom pathlib import Path\np=Path('+repr(str(marker))+')\np.write_text(p.read_text()+"x" if p.exists() else os.environ.get("MONEY_CRAFT_DATA_RUNTIME_ACTIVE","missing"))\nos.execve(sys.executable,[sys.executable,*sys.argv[1:]],dict(os.environ))\n')
            launcher.chmod(0o700)
            env = {key:value for key,value in os.environ.items() if not key.startswith('MONEY_CRAFT_')}
            env['MONEY_CRAFT_DATA_PYTHON'] = str(launcher)
            result = subprocess.run([sys.executable,str(SCRIPTS/'money_craft.py'),'--help'],env=env,capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertEqual(marker.read_text(),'1')
            self.assertIn('usage:',result.stdout)

    def test_missing_default_python_keeps_current_interpreter(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(os.environ,{},clear=True):
            with mock.patch.object(mc,'preferred_data_python',return_value=(Path(directory)/'missing','default')):
                with mock.patch.object(mc.os,'execve',side_effect=AssertionError('unexpected exec')):
                    mc.maybe_reexec_data_runtime()

    def test_relocated_data_home_without_venv_keeps_current_interpreter(self):
        with tempfile.TemporaryDirectory() as directory:
            env = {key: value for key, value in os.environ.items()
                   if key not in {'MONEY_CRAFT_DATA_PYTHON', 'MONEY_CRAFT_DATA_RUNTIME_ACTIVE'}}
            env['MONEY_CRAFT_DATA_HOME'] = str(Path(directory)/'data')
            result = subprocess.run([sys.executable, str(SCRIPTS/'money_craft.py'), 'self-test', '--json'],
                                    capture_output=True, text=True, env=env, check=False)
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertTrue(json.loads(result.stdout)['runtime_valid'])

    def test_dependency_probe_invalid_encoding_is_diagnostic(self):
        with tempfile.TemporaryDirectory() as directory:
            launcher = Path(directory)/'launcher'
            launcher.write_text('#!'+sys.executable+'\nimport os\nos.write(1, bytes([255]))\n')
            launcher.chmod(0o700)
            availability, error = mc.probe_python_modules(launcher, (('markdown','markdown'),))
            self.assertEqual(availability, {'markdown':False})
            self.assertIn('UnicodeDecodeError', error)

    def test_current_dependency_probe_broken_spec_is_diagnostic(self):
        for failure in (ValueError('private detail'), ImportError('private detail')):
            with self.subTest(failure=type(failure).__name__), mock.patch.object(mc.importlib.util,'find_spec',side_effect=failure):
                availability, error = mc.probe_python_modules(Path(sys.executable), (('markdown','markdown'),))
                self.assertEqual(availability, {'markdown':False})
                self.assertIn(type(failure).__name__, error)
                self.assertNotIn('private detail', error)

    def test_doctor_broken_yfinance_spec_remains_structured(self):
        with tempfile.TemporaryDirectory() as directory:
            env = {key:value for key,value in os.environ.items() if not key.startswith('MONEY_CRAFT_')}
            env.update(MONEY_CRAFT_CONFIG_HOME=directory, MONEY_CRAFT_DATA_RUNTIME_ACTIVE='1')
            code = ('import runpy,sys,types;sys.modules["yfinance"]=types.ModuleType("yfinance");'
                    'sys.argv=['+repr(str(SCRIPTS/'money_craft.py'))+',"doctor","--json"];'
                    'sys.path.insert(0,'+repr(str(SCRIPTS))+');runpy.run_path(sys.argv[0],run_name="__main__")')
            result = subprocess.run([sys.executable,'-c',code],env=env,capture_output=True,text=True,timeout=15)
            self.assertEqual(result.returncode,0,result.stderr)
            payload = json.loads(result.stdout)['yfinance']
            self.assertFalse(payload['configured'])
            self.assertIn('ValueError',payload['dependency_probe_error'])
            self.assertFalse(payload['network_checked'])

    def test_yfinance_research_probe_failure_is_configuration_error(self):
        for mode in ('auto','required'):
            with self.subTest(mode=mode), mock.patch.object(mc.importlib.util,'find_spec',side_effect=ValueError('private detail')):
                with self.assertRaises(mc.WorkflowError) as caught:
                    mc.research_provider(mode,adapter='yfinance',security_supported=True)
                self.assertEqual(caught.exception.exit_code,mc.EXIT_CONFIG)
                self.assertEqual(caught.exception.kind,'invalid_configuration')
                self.assertNotIn('private detail',str(caught.exception))

    def test_research_yfinance_availability_preserves_modes(self):
        with mock.patch.object(mc.importlib.util,'find_spec',return_value=None):
            self.assertFalse(mc.research_provider('auto',adapter='yfinance',security_supported=True)['configured'])
            with self.assertRaises(mc.WorkflowError) as caught:
                mc.research_provider('required',adapter='yfinance',security_supported=True)
            self.assertEqual(caught.exception.kind,'missing_optional_dependency')
        with mock.patch.object(mc.importlib.util,'find_spec',return_value=object()):
            self.assertTrue(mc.research_provider('required',adapter='yfinance',security_supported=True)['configured'])
        with mock.patch.object(mc.importlib.util,'find_spec',side_effect=AssertionError('must not probe')):
            self.assertFalse(mc.research_provider('disabled',adapter='yfinance',security_supported=True)['configured'])
            self.assertFalse(mc.research_provider('required',adapter='yfinance',security_supported=False)['configured'])
