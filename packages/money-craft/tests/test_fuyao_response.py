from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from test_provider import FakeOpener, FakeResponse
import money_craft as mc
import fuyao_client

class FuyaoResponseTests(unittest.TestCase):
    def test_duplicate_keys_and_null_success_are_rejected(self):
        responses=[
            b'{"code":2001,"code":0,"message":"ok","request_id":"r","data":{}}',
            b'{"code":0,"message":"ok","request_id":"r","data":{"value":1,"value":2}}',
            b'{"code":0,"message":"ok","request_id":"r","data":null}',
        ]
        for raw in responses:
            with self.subTest(raw=raw):
                opener=FakeOpener([FakeResponse(raw)])
                with self.assertRaises(mc.MoneyCraftError) as caught:
                    mc.FuyaoClient('fixture',opener=opener).request('snapshot','/snapshot',{})
                self.assertEqual(caught.exception.kind,'malformed_response')
                self.assertEqual(caught.exception.exit_code,mc.EXIT_SCHEMA)
                self.assertEqual(len(opener.requests),1)

    def test_valid_empty_list_and_error_null_are_preserved(self):
        for code,data in ((0,{'timestamp':1,'item':[]}),(2001,None)):
            raw=json.dumps({'code':code,'message':'fixture','request_id':'r','data':data}).encode()
            self.assertEqual(fuyao_client.parse_json(raw)['data'],data)

    def test_cli_invalid_response_creates_no_capture(self):
        script=r'''
import io,os,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import money_craft as mc
os.environ['FUYAO_API_KEY']='synthetic-fixture-key'
raw=sys.argv[3].encode()
class Response(io.BytesIO):
    headers={}
class Opener:
    calls=0
    def open(self,*args,**kwargs):
        self.calls+=1
        return Response(raw)
opener=Opener()
import urllib.request;urllib.request.build_opener=lambda *args:opener
sys.argv=['money_craft.py','data','snapshot','--thscodes','600519.SH','--capture-dir',sys.argv[2],'--source-id','S01']
code=mc.main()
assert opener.calls==1
raise SystemExit(code)
'''
        scripts=Path(mc.__file__).parent
        for raw in ('{"code":0,"message":"fixture","request_id":"r","data":null}', '{"code":2001,"code":0,"message":"fixture","request_id":"r","data":{}}'):
            with tempfile.TemporaryDirectory() as directory:
                capture=Path(directory)/'capture'
                result=subprocess.run([sys.executable,'-c',script,str(scripts),str(capture),raw],capture_output=True,text=True,timeout=10)
                self.assertEqual(result.returncode,mc.EXIT_SCHEMA,result.stdout+result.stderr)
                self.assertEqual(json.loads(result.stdout)['error']['kind'],'malformed_response')
                self.assertFalse(capture.exists())
                self.assertNotIn('synthetic-fixture-key',result.stdout+result.stderr)
