import json
from pathlib import Path
import tempfile
import unittest
import test_research_run as fixtures
from test_research_run import research_run as rr

class MissingRowsRunner(fixtures.FakeProviderRunner):
    def __call__(self, command, **kwargs):
        result=super().__call__(command,**kwargs)
        payload=json.loads(result.stdout)
        if payload.get('operation')=='valuations' and payload.get('ok'):
            payload['data']={'item':[]}
            payload['warnings']=['provider returned no row for requested securities: 000333.SZ']
            folder=Path(payload['capture']['path']);raw=folder/'response.json'
            source=json.loads(raw.read_text());source['data']=payload['data'];raw.write_text(json.dumps(source))
            receipt=folder/'capture.json';capture=json.loads(receipt.read_text());capture.update(response_sha256=rr.sha256_file(raw),response_bytes=raw.stat().st_size);receipt.write_text(json.dumps(capture))
            result.stdout=json.dumps(payload)
        return result

class MissingRowsTests(unittest.TestCase):
    def test_missing_rows_remain_gap_through_resume_status_and_finalization(self):
        helper=fixtures.ResearchRunTests()
        with tempfile.TemporaryDirectory() as directory:
            root=helper.initialize(directory)
            result=rr.collect_workspace(root,runtime=Path('fixture-runtime.py'),runner=MissingRowsRunner())
            self.assertFalse(result['valid']);self.assertEqual(result['provider_gaps'],1)
            gap=next(r for r in result['results'] if r['id']=='S03')
            self.assertEqual(gap['error']['kind'],'missing_requested_securities')
            self.assertEqual(gap['error']['missing'],['000333.SZ'])
            resumed=rr.collect_workspace(root,runtime=Path('fixture-runtime.py'),resume=True,runner=lambda *a,**kw:self.fail('resume must not request'))
            self.assertEqual(resumed['provider_gaps'],1)
            status=rr.research_status(root);self.assertEqual(status['stages']['provider_evidence'],'complete_with_gaps')
            _root,_plan,case,_state=rr.load_workspace(root)
            self.assertNotIn('S03',rr.available_evidence_sources(root,case))
            item=next(r for r in case['operations'] if r['id']=='S03')
            source=rr.provider_source(root,item)
            self.assertIn('raw-response',[f['role'] for f in source['files']])
            helper.import_official_sources(root,directory);helper.write_finalization_artifacts(root)
            self.assertTrue(rr.finalize_workspace(root)['valid'])
            receipt=json.loads((root/'completion-receipt.json').read_text())
            self.assertEqual(receipt['assessment']['evidence_coverage'],'PARTIAL')
            self.assertIn('S03',receipt['provider_gaps'])
            (root/'evidence/captures/S03/response.json').write_text('{}')
            with self.assertRaises(rr.ResearchRunError):rr.research_status(root)

    def test_coverage_uses_rows_not_warning_text(self):
        for operation in ('snapshot','valuations'):
            item={'id':'S02','provider':'fuyao','operation':operation,'arguments':{'thscodes':'000333.SZ,600519.SH'}}
            payload={'schema':'money-craft.data-response.v1','provider':'fuyao','operation':operation,'ok':True,'data':{'item':[{'thscode':'000333.SZ'}]},'warnings':[]}
            status,error=rr.operation_status(item,payload,0)
            self.assertEqual(status,'provider_gap');self.assertEqual(error['missing'],['600519.SH'])
            payload['data']['item'].append({'thscode':'600519.SH'})
            payload['warnings']=['informational warning']
            self.assertEqual(rr.operation_status(item,payload,0),('passed',None))
            for rows in (None,[{}],[{'thscode':'000001.SZ'}],[{'thscode':'000333.SZ'}]*2):
                payload['data']['item']=rows
                with self.assertRaises(rr.ResearchRunError):rr.operation_status(item,payload,0)
