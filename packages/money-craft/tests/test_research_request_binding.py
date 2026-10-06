import json
from pathlib import Path
import tempfile
import unittest
import test_research_run as fixtures
from test_research_run import research_run as rr

class RequestBindingTests(unittest.TestCase):
    def test_request_and_normalized_parameters_cannot_drift(self):
        helper=fixtures.ResearchRunTests()
        for mutation in ('normalized','request','both','path','missing'):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as directory:
                root=helper.initialize(directory);helper.collect(root)
                normalized=root/'evidence/S04-history.normalized.json'
                request=root/'evidence/captures/S04/request.json'
                payload=json.loads(normalized.read_text())
                original={'schema':'money-craft.sanitized-request.v1','provider':'fuyao','operation':'history','method':'GET','path':'/api/a-share/prices/historical','parameters':payload['parameters'],'authentication':'fixture'}
                if request.exists():original=json.loads(request.read_text())
                if mutation in ('normalized','both'):
                    payload['parameters']['thscode']='999999.SH';normalized.write_text(json.dumps(payload))
                if mutation in ('request','both'):original['parameters']['thscode']='999999.SH'
                if mutation=='path':original['path']='/wrong-operation'
                if mutation=='missing':
                    if request.exists():request.unlink()
                else:request.write_text(json.dumps(original))
                with self.assertRaises(rr.ResearchRunError):rr.research_status(root)

    def test_expected_projection_matches_real_cli_for_plan_operations(self):
        import money_craft as mc
        helper=fixtures.ResearchRunTests()
        with tempfile.TemporaryDirectory() as directory:
            root=helper.initialize(directory)
            _root,_plan,case,_state=rr.load_workspace(root)
            for item in case['operations']:
                command=rr.operation_command(Path(mc.__file__),item,root/'capture')
                args=mc.build_parser().parse_args(command[2:])
                operation,path,_params,output=mc.prepare_operation(args)
                expected_path,expected_params=rr.fuyao_request_projection(item)
                self.assertEqual(expected_path,path)
                self.assertEqual(expected_params,output)

    def test_finalized_request_file_is_hash_bound(self):
        helper=fixtures.ResearchRunTests()
        with tempfile.TemporaryDirectory() as directory:
            root=helper.initialize(directory);helper.collect(root)
            helper.import_official_sources(root,directory);helper.write_finalization_artifacts(root)
            self.assertTrue(rr.finalize_workspace(root)['valid'])
            path=root/'evidence/captures/S04/request.json'
            request=json.loads(path.read_text());request['authentication']='changed-label'
            path.write_text(json.dumps(request))
            status=rr.research_status(root)
            self.assertFalse(status['complete'])
            self.assertEqual(status['stages']['receipt'],'pending')

    def test_explicit_none_uses_same_defaults_as_cli(self):
        import money_craft as mc
        cases = [
            {"operation":"search","arguments":{"query":"000333","limit":None}},
            {"operation":"history","arguments":{"thscode":"000333.SZ","start":"2026-01-01","end":"2026-01-02","interval":None,"adjust":None}},
            {"operation":"financials","arguments":{"thscode":"000333.SZ","statement":"income","period":None,"limit":None}},
        ]
        for case in cases:
            case["id"]="S01"
            command=rr.operation_command(Path(mc.__file__),case,Path("/synthetic-capture"))
            args=mc.build_parser().parse_args(command[2:])
            _operation,path,_parameters,output=mc.prepare_operation(args)
            self.assertEqual(rr.fuyao_request_projection(case),(path,output))
