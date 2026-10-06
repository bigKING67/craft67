"""Extra evidence is declared before initialization, without weakening old plans."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import test_research_run as fixtures
from research_workflow import company_research_plan, WorkflowError
import money_craft


DECLARATION = {'id': 'S23', 'kind': 'official-document', 'role': 'comparison quarter formal filing', 'period': '2026-1'}


def plan(extra):
    return company_research_plan(security='美的集团', thscode='000333.SZ', as_of='2026-08-23', latest_report='2026-2',
                                 provider={'mode': 'disabled', 'configured': False}, additional_evidence=extra)


class AdditionalEvidenceTests(unittest.TestCase):
    def test_declared_quarter_imports_and_is_bound_to_plan(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); ws = root/'run'; source = root/'q1.pdf'; source.write_bytes(b'%PDF-1.7\nquarter')
            p = plan([DECLARATION]); fixtures.research_run.initialize_workspace(ws,p,template_root=fixtures.ROOT/'skills/money-craft/templates')
            frozen = (ws/'plan.json').read_bytes()
            result = fixtures.research_run.import_official_source(ws,source_id='S23',source_file=source,url='https://example.invalid/q1.pdf')
            self.assertTrue(result['valid']); self.assertEqual(result['kind'],'official-document')
            _, _, case, _ = fixtures.research_run.load_workspace(ws)
            extra = next(x for x in case['official_sources'] if x['id']=='S23')
            self.assertEqual(extra['period'],'2026-1'); self.assertFalse(extra['required'])
            self.assertEqual((ws/'plan.json').read_bytes(),frozen)
            self.assertEqual(fixtures.research_run.research_status(ws)['missing_sources'],['S11','S12','S13'])
            extra['period']='2025-1'; (ws/'case.json').write_text(json.dumps(case))
            with self.assertRaisesRegex(fixtures.research_run.ResearchRunError,'identity'):
                fixtures.research_run.research_status(ws)

    def test_old_plan_rejects_extra_without_being_mutated(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);ws=root/'run';p=plan(None)
            fixtures.research_run.initialize_workspace(ws,p,template_root=fixtures.ROOT/'skills/money-craft/templates')
            before=(ws/'plan.json').read_bytes(); source=root/'q1.pdf';source.write_bytes(b'%PDF-1.7\nquarter')
            with self.assertRaises(fixtures.research_run.ResearchRunError):
                fixtures.research_run.import_official_source(ws,source_id='S23',source_file=source,url='https://example.invalid/q1.pdf')
            self.assertEqual(before,(ws/'plan.json').read_bytes())

    def test_public_declaration_stays_in_public_collection(self):
        p=plan([{'id':'S40','kind':'public-material','role':'public quote check'}]);case=fixtures.research_run.derived_case(p,'a'*64)
        self.assertNotIn('S40',[x['id'] for x in case['official_sources']])
        self.assertEqual(next(x for x in case['public_sources'] if x['id']=='S40')['trust'],'unverified-public')

    def test_invalid_declarations_are_rejected(self):
        invalid=[{},'invalid',[DECLARATION]*17,[DECLARATION,DECLARATION],
                 [dict(DECLARATION,id='S11')],[dict(DECLARATION,id='S31')],
                 [dict(DECLARATION,id='../escape')],[dict(DECLARATION,kind='verified-provider')],
                 [dict(DECLARATION,role=' ')],[dict(DECLARATION,role='x'*257)],
                 [dict(DECLARATION,period='2026-5')],[dict(DECLARATION,required=True)]]
        for declarations in invalid:
            with self.subTest(declarations=declarations), self.assertRaises(WorkflowError):plan(declarations)

    def test_all_declarations_validated_before_mutation(self):
        from research_workflow import add_evidence_requirements
        p=plan(None);before=copy.deepcopy(p)
        with self.assertRaises(WorkflowError):add_evidence_requirements(p,[DECLARATION,dict(DECLARATION,id='S11')])
        self.assertEqual(p,before)

    def test_json_input_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'sources.json'
            for content in [b'{}',b'bad json',b'\xff',b' '*65537]:
                p.write_bytes(content)
                with self.assertRaises(WorkflowError):money_craft.load_additional_evidence(p)
            # Decoder depth limits differ by Python version; either decoding or
            # declaration validation must reject this non-declaration input.
            p.write_bytes(b'['*2000+b']'*2000)
            with self.assertRaises(WorkflowError):
                plan(money_craft.load_additional_evidence(p))
            p.write_text('[]')
            with patch.object(money_craft.json, 'loads', side_effect=RecursionError('decoder depth')):
                with self.assertRaises(WorkflowError):money_craft.load_additional_evidence(p)
            p.write_text(json.dumps([DECLARATION]));self.assertEqual(money_craft.load_additional_evidence(p),[DECLARATION])

    def test_cli_plan_supports_explicit_declaration(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'sources.json';p.write_text(json.dumps([DECLARATION]))
            import os
            result=subprocess.run([sys.executable,str(fixtures.SCRIPT_DIR/'money_craft.py'),'research','plan',
                '--security','美的集团','--thscode','000333.SZ','--as-of','2026-08-23','--latest-report','2026-2',
                '--provider-mode','disabled','--additional-evidence',str(p),'--json'],capture_output=True,text=True,
                env={**os.environ,'MONEY_CRAFT_DATA_PYTHON':sys.executable},timeout=10)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertEqual(json.loads(result.stdout)['official_evidence_requirements'][-1]['id'],'S23')


if __name__=='__main__':unittest.main()
