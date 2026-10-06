from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1]/'skills/money-craft/scripts'
sys.path.insert(0, str(SCRIPTS))
import money_craft as mc
import fuyao_client


class FuyaoCredentialTests(unittest.TestCase):
    def test_redaction_precedes_truncation(self):
        secret = 'synthetic-credential-abcdef'
        result = mc.sanitize_message('x'*490+secret, (secret,))
        self.assertNotIn('synthetic', result)
        self.assertLessEqual(len(result), 500)

    def test_changed_file_is_rejected_before_read(self):
        for replacement in ('regular', 'symlink', 'fifo'):
            with self.subTest(replacement=replacement), tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve(); path = root/'fuyao-api-key'; other = root/'other'
                path.write_text('original-fixture'); path.chmod(0o600)
                if replacement == 'regular':
                    other.write_text('replacement-fixture'); other.chmod(0o600)
                elif replacement == 'symlink':
                    target = root/'target'; target.write_text('replacement-fixture');target.chmod(0o600);other.symlink_to(target)
                else:
                    os.mkfifo(other,0o600)
                original = Path.lstat
                def inspect(target, *args, **kwargs):
                    info = original(target,*args,**kwargs)
                    if target == path: os.replace(other,path)
                    return info
                # The old implementation would block on a FIFO; guard that old path.
                original_read = Path.read_text
                def read(target,*args,**kwargs):
                    if target == path and replacement == 'fifo': raise AssertionError('unsafe FIFO read')
                    return original_read(target,*args,**kwargs)
                with mock.patch.object(Path,'lstat',inspect), mock.patch.object(Path,'read_text',read):
                    with self.assertRaises(mc.MoneyCraftError) as caught:
                        mc.load_fuyao_credential({'MONEY_CRAFT_CONFIG_HOME':str(root)})
                self.assertEqual(caught.exception.kind,'invalid_configuration')
                self.assertEqual(caught.exception.exit_code,mc.EXIT_CONFIG)

    def test_growth_after_inspection_is_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();path=root/'fuyao-api-key';path.write_text('fixture');path.chmod(0o600)
            original=Path.lstat
            def inspect(target,*args,**kwargs):
                info=original(target,*args,**kwargs)
                if target==path:path.write_bytes(b'x'*(fuyao_client.MAX_API_KEY_BYTES+1))
                return info
            with mock.patch.object(Path,'lstat',inspect):
                with self.assertRaises(mc.MoneyCraftError) as caught:
                    mc.load_fuyao_credential({'MONEY_CRAFT_CONFIG_HOME':str(root)})
            self.assertEqual(caught.exception.kind,'invalid_configuration')

    def test_inspection_failure_is_configuration_error_without_details(self):
        with mock.patch.object(Path,'lstat',side_effect=PermissionError('private-fixture-detail')):
            with self.assertRaises(mc.MoneyCraftError) as caught:
                mc.load_fuyao_credential({},home=Path('/synthetic-home'))
        self.assertEqual(caught.exception.kind,'invalid_configuration')
        self.assertNotIn('private-fixture-detail',str(caught.exception))

    def test_real_cli_replacement_stops_before_request_or_capture(self):
        import json
        import subprocess
        script = r'''
import os,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import money_craft as mc
root=Path(sys.argv[2]).resolve()
os.environ.pop('FUYAO_API_KEY',None)
os.environ['MONEY_CRAFT_CONFIG_HOME']=str(root)
path=root/'fuyao-api-key';other=root/'replacement'
original=Path.lstat
def inspect(target,*args,**kwargs):
    metadata=original(target,*args,**kwargs)
    if target==path:os.replace(other,path)
    return metadata
Path.lstat=inspect
def forbidden(*args,**kwargs):raise AssertionError('request must not start')
mc.FuyaoClient.request=forbidden
sys.argv=['money_craft.py','data','snapshot','--thscodes','600519.SH','--capture-dir',str(root/'capture'),'--source-id','S01']
raise SystemExit(mc.main())
'''
        for kind in ('regular','fifo'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                root=Path(directory);p=root/'fuyao-api-key';p.write_text('original-fixture');p.chmod(0o600)
                p=root/'replacement'
                if kind=='regular':p.write_text('replacement-fixture');p.chmod(0o600)
                else:os.mkfifo(p,0o600)
                result=subprocess.run([sys.executable,'-c',script,str(SCRIPTS),directory],capture_output=True,text=True,timeout=10)
                self.assertEqual(result.returncode,mc.EXIT_CONFIG,result.stdout+result.stderr)
                self.assertEqual(json.loads(result.stdout)['error']['kind'],'invalid_configuration')
                self.assertFalse((root/'capture').exists())
                self.assertNotIn('original-fixture',result.stdout+result.stderr)
                self.assertNotIn('replacement-fixture',result.stdout+result.stderr)
