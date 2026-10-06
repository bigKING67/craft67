import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import test_research_run as fixtures
from test_research_run import research_run as rr

class StateContractTests(unittest.TestCase):
    def test_malformed_state_is_structured_error_without_writes(self):
        helper=fixtures.ResearchRunTests()
        with tempfile.TemporaryDirectory() as directory:
            root=helper.initialize(directory);path=root/'run-state.json';original=json.loads(path.read_text())
            cases=[]
            for key,value in (('revision',True),('revision',2),('created_at','not-a-date'),('created_at','2026-09-19T24:00:00Z'),('created_at','2026-09-19T00:00:00+01:99'),('created_at','2026-09-19T00:00:00'),('unknown',1)):
                state=copy.deepcopy(original);state[key]=value;cases.append(state)
            for key,value in (('sequence',True),('type',''),('at','2026-99-99T00:00:00Z'),('details',None),('details',[]),('unexpected',1)):
                state=copy.deepcopy(original);state['events'][0][key]=value;cases.append(state)
            for key in ('created_at','revision'):
                state=copy.deepcopy(original);del state[key];cases.append(state)
            state=copy.deepcopy(original);del state['events'][0]['at'];cases.append(state)
            for index,state in enumerate(cases):
                with self.subTest(index=index):
                    path.write_text(json.dumps(state));before=path.read_bytes()
                    result=subprocess.run([sys.executable,str(fixtures.SCRIPT_DIR/'money_craft.py'),'research','status','--workspace',str(root)],capture_output=True,text=True,timeout=10)
                    self.assertNotEqual(result.returncode,0)
                    self.assertEqual(json.loads(result.stdout)['error']['kind'],'invalid_state')
                    self.assertNotIn('Traceback',result.stderr)
                    self.assertEqual(path.read_bytes(),before)

    def test_valid_timezone_timestamps_and_clock_rollback_remain_valid(self):
        helper=fixtures.ResearchRunTests()
        with tempfile.TemporaryDirectory() as directory:
            root=helper.initialize(directory);state=json.loads((root/'run-state.json').read_text())
            state['created_at']='2026-09-19T10:00:00+08:00'
            state['events'][0]['at']='2026-09-19T01:59:59.123456Z'
            rr.validate_state(state)
