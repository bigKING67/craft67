import json
from pathlib import Path
import tempfile
import unittest
import test_research_run as fixtures
from test_research_run import research_run as rr

class CaptureContentTests(unittest.TestCase):
    def test_normalized_changes_fail_status_and_resume(self):
        helper=fixtures.ResearchRunTests()
        for mutation in ('value','identity','bool'):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as directory:
                root=helper.initialize(directory);helper.collect(root)
                path=root/'evidence/S02-snapshot.normalized.json';payload=json.loads(path.read_text())
                if mutation=='identity':payload['data']['item'][0]['ticker']='999999'
                elif mutation=='bool':payload['data']['item'][0]['new_value']=True
                else:payload['data']['item'][0]['last_price']='999.99'
                path.write_text(json.dumps(payload))
                with self.assertRaises(rr.ResearchRunError):rr.research_status(root)
                with self.assertRaises(rr.ResearchRunError):rr.collect_workspace(root,runtime=Path('fixture-runtime.py'),resume=True,runner=lambda *a,**k:self.fail('unexpected request'))

    def test_decimal_projection_calendar_filter_and_type_integrity(self):
        helper=fixtures.ResearchRunTests()
        with tempfile.TemporaryDirectory() as directory:
            root=helper.initialize(directory);helper.collect(root)
            _root,_plan,case,_state=rr.load_workspace(root)
            item=next(i for i in case['operations'] if i['operation']=='calendar')
            folder=root/'evidence/captures'/item['id'];raw=folder/'response.json'
            normalized=root/'evidence'/item['output'];payload=json.loads(normalized.read_text())
            raw.write_text('{"code":0,"request_id":'+json.dumps(payload['request_id'])+',"data":{"timestamp":1,"value":1e-7,"ratio":1.2300,"flag":1,"item":[{"date":"19000101"},{"date":"20260823"}]}}')
            capture=folder/'capture.json';meta=json.loads(capture.read_text());meta.update(response_sha256=rr.sha256_file(raw),response_bytes=raw.stat().st_size);capture.write_text(json.dumps(meta))
            payload['source_timestamp_ms']=1
            payload['data']={'timestamp':1,'value':'1E-7','ratio':'1.2300','flag':1,'item':[{'date':'20260823'}]}
            rr.validate_provider_capture(root,item,payload)
            payload['data']['flag']=True
            with self.assertRaises(rr.ResearchRunError):rr.validate_provider_capture(root,item,payload)

    def test_actual_cli_calendar_capture_matches_projection(self):
        import subprocess
        import sys
        code=r'''
import io,os,sys
sys.path.insert(0,sys.argv[1])
import money_craft as mc
os.environ['FUYAO_API_KEY']='synthetic-fixture-key'
class Response(io.BytesIO):headers={}
class Opener:
    def open(self,*a,**k):return Response(b'{"code":0,"message":"fixture","request_id":"r","data":{"timestamp":1,"value":1e-7,"ratio":1.2300,"item":[{"date":"20260101"},{"date":"20260102"}]}}')
import urllib.request;urllib.request.build_opener=lambda *a:Opener()
sys.argv=['money_craft.py','data','calendar','--start','2026-01-02','--end','2026-01-02','--capture-dir',sys.argv[2],'--source-id','S10']
raise SystemExit(mc.main())
'''
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);capture=root/'evidence/captures'
            result=subprocess.run([sys.executable,'-c',code,str(fixtures.SCRIPT_DIR),str(capture)],capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr)
            payload=json.loads(result.stdout)
            item={'id':'S10','operation':'calendar','arguments':{'start':'2026-01-02','end':'2026-01-02'}}
            rr.validate_provider_capture(root,item,payload)
            self.assertEqual(payload['data']['value'],'1E-7')
            self.assertEqual(payload['data']['item'],[{'date':'20260102'}])
