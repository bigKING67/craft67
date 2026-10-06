import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import test_research_run as fixtures
from test_research_run import research_run as rr

class YFinanceBindingTests(unittest.TestCase):
    def capture(self, root):
        code=r'''
import sys
from decimal import Decimal
sys.path.insert(0,sys.argv[1])
import money_craft as mc
import yfinance_adapter as yf
client=yf.YFinanceClient(module=object(),version='fixture')
client._execute=lambda *args:{'last_price':Decimal('1.2300'),'symbol':'NVDA'}
yf.YFinanceClient=lambda *args,**kwargs:client
sys.argv=['money_craft.py','data','snapshot','--provider','yfinance','--symbol','nvda','--capture-dir',sys.argv[2],'--source-id','S02']
raise SystemExit(mc.main())
'''
        result=subprocess.run([sys.executable,'-c',code,str(fixtures.SCRIPT_DIR),str(root/'evidence/captures')],capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        return json.loads(result.stdout)

    def test_actual_adapter_export_matches_and_drift_is_rejected(self):
        for mutation in (None,'data','normalized_symbol','request_symbol','export_symbol','export_operation','export_parameters','export_time','export_schema'):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);payload=self.capture(root)
                item={'id':'S02','provider':'yfinance','operation':'snapshot','arguments':{'symbol':'nvda'},'title':'fixture','output':'S02.json'}
                folder=root/'evidence/captures/S02'
                if mutation=='data':payload['data']['last_price']='999'
                if mutation=='normalized_symbol':payload['parameters']['symbol']='MSFT'
                if mutation=='request_symbol':
                    p=folder/'request.json';v=json.loads(p.read_text());v['parameters']['symbol']='MSFT';p.write_text(json.dumps(v))
                if mutation and mutation.startswith('export_'):
                    p=folder/'response.json';v=json.loads(p.read_text());key=mutation[7:]
                    if key=='time':key='fetched_at'
                    v[key]={'symbol':'MSFT'} if key=='parameters' else 'changed'
                    p.write_text(json.dumps(v));meta=folder/'capture.json';m=json.loads(meta.read_text());m.update(response_sha256=rr.sha256_file(p),response_bytes=p.stat().st_size);meta.write_text(json.dumps(m))
                if mutation:
                    with self.assertRaises(rr.ResearchRunError):rr.validate_provider_capture(root,item,payload)
                else:
                    rr.validate_provider_capture(root,item,payload)
                    self.assertEqual(payload['data']['last_price'],'1.2300')

    def test_projection_matches_cli_defaults_and_optional_dates(self):
        import money_craft as mc
        cases=[('search',{'query':'NVDA','limit':None}),('snapshot',{'symbol':'nvda'}),('valuations',{'symbol':'0700.hk'}),('history',{'symbol':'nvda','start':'2026-01-01','end':'2026-01-02','adjust':None,'interval':None}),('financials',{'symbol':'nvda','statement':'income','period':None,'limit':None}),('corporate-actions',{'symbol':'nvda','start':None,'end':None})]
        for operation,args in cases:
            item={'id':'S01','provider':'yfinance','operation':operation,'arguments':args}
            command=rr.operation_command(Path(mc.__file__),item,Path('/synthetic-capture'))
            parsed=mc.build_parser().parse_args(command[2:]);_op,path,_params,output=mc.prepare_operation(parsed)
            self.assertEqual(rr.yfinance_request_projection(item),(path,output))

    def test_full_yfinance_collection_preserves_bindings(self):
        import datetime as dt
        plan=fixtures.company_research_plan(security='NVIDIA Corporation',security_id='US-NASDAQ:NVDA',base_currency='USD',as_of='2026-08-23',latest_report='2026-2',latest_report_end='2025-07-27',latest_annual_report='2025-4',provider={'mode':'auto','configured':True,'network_checked':False},today=dt.date(2026,8,23))
        script=r'''
import sys
from decimal import Decimal
sys.path.insert(0,sys.argv[1])
import money_craft as mc
import yfinance_adapter as yf
client=yf.YFinanceClient(module=object(),version='fixture')
def execute(operation,*args):
    if operation=='search':return {'item':[{'symbol':'NVDA','currency':'USD','quoteType':'EQUITY'}]}
    if operation=='snapshot':return {'last_price':Decimal('1.2300')}
    return {'table':{'rows':[[Decimal('1.2300')]]}}
client._execute=execute
yf.YFinanceClient=lambda *a,**kw:client
sys.argv=['money_craft.py',*sys.argv[2:]]
raise SystemExit(mc.main())
'''
        def runner(command,**kwargs):
            return subprocess.run([sys.executable,'-c',script,str(fixtures.SCRIPT_DIR),*command[2:]],timeout=10,**kwargs)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'run'
            rr.initialize_workspace(root,plan,template_root=fixtures.ROOT/'skills/money-craft/templates')
            result=rr.collect_workspace(root,runtime=fixtures.SCRIPT_DIR/'money_craft.py',runner=runner)
            self.assertTrue(result['valid'])
            self.assertEqual(rr.research_status(root)['stages']['provider_evidence'],'complete')
            rr.collect_workspace(root,runtime=Path('fixture'),resume=True,runner=lambda *a,**k:self.fail('resume requested'))
            _root,_plan,case,_state=rr.load_workspace(root)
            source=rr.provider_source(root,case['operations'][0])
            self.assertIn('sanitized-request',[f['role'] for f in source['files']])
            path=root/'evidence/S02-snapshot.normalized.json';payload=json.loads(path.read_text());payload['data']['last_price']='9';path.write_text(json.dumps(payload))
            with self.assertRaises(rr.ResearchRunError):rr.research_status(root)
