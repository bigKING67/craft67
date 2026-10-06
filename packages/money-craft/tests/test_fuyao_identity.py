from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/money-craft/scripts'))
import money_craft as mc

class FuyaoIdentityTests(unittest.TestCase):
    def run_cli(self, operation, data, capture):
        code=r'''
import io,json,os,sys
sys.path.insert(0,sys.argv[1])
import money_craft as mc
os.environ['FUYAO_API_KEY']='synthetic-fixture-key'
data=json.loads(sys.argv[3]);calls=[]
class Response(io.BytesIO):headers={}
class Opener:
    def open(self,*args,**kwargs):
        calls.append(1)
        return Response(json.dumps({'code':0,'message':'fixture','request_id':'r','data':data}).encode())
import urllib.request;urllib.request.build_opener=lambda *args:Opener()
sys.argv=['money_craft.py','data',sys.argv[2],'--thscodes','999999.SH,999998.SZ','--capture-dir',sys.argv[4],'--source-id','S01']
result=mc.main()
assert len(calls)==1
raise SystemExit(result)
'''
        return subprocess.run([sys.executable,'-c',code,str(Path(mc.__file__).parent),operation,json.dumps(data),str(capture)],capture_output=True,text=True,timeout=10)

    def test_invalid_identity_is_rejected_before_capture(self):
        cases=[{}, {'item':None},{'item':[None]}, {'item':[{}]},
               {'item':[{'thscode':'999997.SH','ticker':'999997'}]},
               {'item':[{'thscode':'999999.SH','ticker':'999998'}]},
               {'item':[{'thscode':'999999.SH','ticker':'999999'}]*2}]
        for operation in ('snapshot','valuations'):
            for data in cases:
                with self.subTest(operation=operation,data=data),tempfile.TemporaryDirectory() as directory:
                    capture=Path(directory)/'capture';result=self.run_cli(operation,data,capture)
                    self.assertEqual(result.returncode,mc.EXIT_SCHEMA,result.stdout+result.stderr)
                    self.assertEqual(json.loads(result.stdout)['error']['kind'],'malformed_response')
                    self.assertFalse(capture.exists())

    def test_complete_partial_and_empty_results_preserve_data_and_warn(self):
        rows=[{'thscode':'999999.SH','ticker':'999999'},{'thscode':'999998.SZ','ticker':'999998'}]
        for operation in ('snapshot','valuations'):
            for size in (2,1,0):
                data={'item':rows[:size]}
                with self.subTest(operation=operation,size=size),tempfile.TemporaryDirectory() as directory:
                    capture=Path(directory)/'capture';result=self.run_cli(operation,data,capture)
                    self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                    payload=json.loads(result.stdout)
                    self.assertEqual(payload['data'],data)
                    self.assertEqual(bool(payload['warnings']),size<2)
                    if size<2:self.assertIn('999998.SZ',payload['warnings'][0])
                    self.assertTrue((capture/'S01/capture.json').is_file())
