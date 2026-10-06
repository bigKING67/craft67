import hashlib
import json
import sys
import subprocess
import tempfile
import unittest
import contextlib
import io
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from audit_skill_task import audit, route_command, public_citations, load_run_case
from run_skill_task import prepare_case, citation_instruction
import run_skill_task


class SkillTaskAuditTests(unittest.TestCase):
    def test_no_bytecode_environment_route_requires_bound_receipt(self):
        command = "/bin/zsh -lc 'PYTHONDONTWRITEBYTECODE=1 bash /host/investment_route_plan.sh --output compact-json'"
        self.assertTrue(self.run_audit([self.event(command=command)])['machine_checks_pass'])
        self.assertFalse(self.run_audit([self.event(code=1, command=command)])['machine_checks_pass'])
        self.assertFalse(self.run_audit([self.event(payload={}, command=command)])['machine_checks_pass'])

    def test_environment_prefix_does_not_admit_non_invocations(self):
        for command in [
            'PYTHONDONTWRITEBYTECODE=1',
            'PYTHONDONTWRITEBYTECODE=1 echo bash /host/investment_route_plan.sh --output compact-json',
            'PATH=/tmp bash /host/investment_route_plan.sh --output compact-json',
            'PYTHONDONTWRITEBYTECODE=1 bash /host/investment_route_plan.sh --help --output compact-json',
            'PYTHONDONTWRITEBYTECODE=1 bash /host/investment_route_plan.sh --output compact-json; true',
        ]:
            with self.subTest(command=command):
                self.assertFalse(route_command(command))

    def test_python_core_route_requires_successful_bound_receipt(self):
        command = 'python3 -B /host/investment_route_core.py --output compact-json'
        self.assertTrue(self.run_audit([self.event(command=command)])['machine_checks_pass'])
        self.assertFalse(self.run_audit([self.event(code=1, command=command)])['machine_checks_pass'])
        self.assertFalse(self.run_audit([self.event(payload={}, command=command)])['machine_checks_pass'])

    def test_python_core_route_rejects_non_invocations(self):
        for command in [
            'echo python3 /host/investment_route_core.py --output compact-json',
            'python3 -c /host/investment_route_core.py --output compact-json',
            'python3 -m investment_route_core.py --output compact-json',
            'python3 /host/unrelated.py --output compact-json',
            'python3 /host/investment_route_core.py --help --output compact-json',
            'python3 /host/investment_route_core.py --output compact-json; true',
        ]:
            with self.subTest(command=command):
                self.assertFalse(route_command(command))

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.case = {'id': 'sample', 'criteria': ['Compare margins'], 'machine_contract': {
            'route_required': True, 'calculations_required': True, 'allowed_route_blocks': []}}
        self.receipt = {'schema': 'codex.investment-route.v2', 'route_id': 'earnings-review',
                        'status': 'ready', 'error_code': None, 'classification': {'intent': 'earnings'},
                        'stage_chain': [{'name': 'earnings'}]}
        self.calc = '<!-- money-craft-calc: {"id":"C01","operation":"divide","inputs":["9","60"],"expected":"0.15"} -->'

    def event(self, code=0, payload=None, command=None):
        return {'type': 'item.completed', 'item': {'type': 'command_execution',
                'command': command or 'bash /host/investment_route_plan.sh --output compact-json',
                'exit_code': code, 'aggregated_output': json.dumps(self.receipt if payload is None else payload)}}

    def run_audit(self, events=None, answer=None, tamper=False):
        (self.root / 'answer.md').write_text(self.calc if answer is None else answer)
        (self.root / 'events.jsonl').write_text('\n'.join(json.dumps(e) for e in (events if events is not None else [self.event()])))
        host = {'case_id': 'sample', 'exit_code': 0, 'timed_out': False,
                'artifact_hashes': {n: hashlib.sha256((self.root / n).read_bytes()).hexdigest()
                                    for n in ['answer.md', 'events.jsonl']}}
        (self.root / 'host.json').write_text(json.dumps(host))
        if tamper:
            (self.root / 'answer.md').write_text(self.calc + ' modified')
        return audit(self.root, self.case)

    def test_machine_pass_never_completes_semantic_review(self):
        r = self.run_audit()
        self.assertTrue(r['machine_checks_pass'])
        self.assertFalse(r['research_complete'])
        self.assertEqual(r['manual_criteria'][0]['status'], 'PENDING')

    def test_new_run_defaults_are_frozen_without_mutating_old_case(self):
        self.case['evidence'] = [{'source_id': 'S01', 'url': 'https://issuer.test/release'},
                                 {'source_id': 'S02', 'path': 'synthetic.json'}]
        prepared = prepare_case(self.case)
        self.assertEqual(prepared['machine_contract']['public_source_ids'], ['S01'])
        self.assertNotIn('public_source_ids', self.case['machine_contract'])
        self.assertIn('S01', citation_instruction(prepared))
        self.assertNotIn('S02', citation_instruction(prepared))
        self.case['machine_contract']['public_source_ids'] = []
        self.assertEqual(citation_instruction(prepare_case(self.case)), '')

    def test_reaudit_uses_bound_snapshot_and_rejects_drift(self):
        self.run_audit()
        prepared = prepare_case(self.case)
        prepared['machine_contract']['public_source_ids'] = ['S01']
        snapshot = self.root / 'case-snapshot.json'
        snapshot.write_text(json.dumps(prepared))
        host_path = self.root / 'host.json'; host = json.loads(host_path.read_text())
        host['artifact_hashes']['case-snapshot.json'] = hashlib.sha256(snapshot.read_bytes()).hexdigest()
        host_path.write_text(json.dumps(host))
        self.assertEqual(load_run_case(self.root, None), prepared)
        snapshot.write_text(json.dumps(self.case))
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            load_run_case(self.root, None)
        snapshot.unlink()
        with self.assertRaises(OSError):
            load_run_case(self.root, None)

    def test_unbound_snapshot_is_not_silently_trusted(self):
        self.run_audit()
        (self.root / 'case-snapshot.json').write_text(json.dumps(self.case))
        with self.assertRaisesRegex(ValueError, 'not bound'):
            load_run_case(self.root, None)
        alternate = self.root / 'alternate.json'
        alternate.write_text(json.dumps({'cases': [self.case]}))
        self.assertEqual(load_run_case(self.root, alternate), self.case)

    def test_runner_enforces_default_and_reaudit_preserves_it(self):
        source = self.root / 'release.html'; source.write_text('synthetic official source')
        case = {**self.case, 'status': 'READY_HISTORICAL', 'facts': 'Fixture only',
                'prompt': 'Explain the filing', 'evidence': [{'source_id': 'S01',
                    'path': str(source), 'url': 'https://issuer.test/release',
                    'sha256': hashlib.sha256(source.read_bytes()).hexdigest()}]}
        case_path = self.root / 'cases.json'
        case_path.write_text(json.dumps({'cases': [case]}))
        for linked in (False, True):
            out = self.root / ('linked' if linked else 'local-only')
            answer = self.calc + ('\n[S01](https://issuer.test/release)' if linked else '\n[S01](/cache/release.html)')
            event = self.event()

            class FakeHost:
                returncode = 0

                def __init__(self, argv, **kwargs):
                    self.answer_path = Path(argv[argv.index('-o')+1])
                    self.events = kwargs['stdout']

                def communicate(self, prompt, timeout):
                    self.answer_path.write_text(answer)
                    self.events.write(json.dumps(event)+'\n')

            argv = ['run_skill_task.py', '--case', 'sample', '--case-file', str(case_path),
                    '--output-dir', str(out)]
            with patch.object(sys, 'argv', argv), patch.object(run_skill_task.subprocess, 'Popen', FakeHost), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(run_skill_task.main(), 0 if linked else 4)
            frozen = load_run_case(out, None)
            self.assertEqual(frozen['machine_contract']['public_source_ids'], ['S01'])
            self.assertIn('公开HTTPS链接', (out / 'prompt.txt').read_text())
            initial = json.loads((out / 'machine-audit.json').read_text())
            replay = audit(out, frozen)
            self.assertEqual(initial['case_contract_sha256'], replay['case_contract_sha256'])
            self.assertEqual(replay['machine_checks_pass'], linked)
        self.assertNotIn('public_source_ids', json.loads(case_path.read_text())['cases'][0]['machine_contract'])

    def test_public_source_link_contract(self):
        self.case['machine_contract']['public_source_ids'] = ['S01', 'S02']
        self.case['evidence'] = [
            {'source_id': 'S01', 'url': 'https://issuer.test/release'},
            {'source_id': 'S02', 'url': 'https://issuer.test/call'}]
        for answer in [
            '[S01 release](https://issuer.test/release)\n[S02]: https://issuer.test/call',
            '[S01] <https://issuer.test/release>\n[S02 call](https://issuer.test/call)']:
            with self.subTest(answer=answer):
                self.assertEqual(public_citations(answer, self.case)[1], [])
        for answer in [
            '[S01 release](/local/release.html)\n[S02 call](/local/call.html)',
            '[S01](https://issuer.test/call)\n[S02](https://issuer.test/release)',
            '[S01](https://issuer.test/release.evil)\n[S02](https://issuer.test/call)',
            '<!-- [S01](https://issuer.test/release) -->\n[S02](https://issuer.test/call)',
            '```markdown\n[S01](https://issuer.test/release)\n```\n[S02](https://issuer.test/call)',
            '`[S01](https://issuer.test/release)`\n[S02](https://issuer.test/call)']:
            with self.subTest(answer=answer):
                self.assertTrue(public_citations(answer, self.case)[1])

    def test_public_source_failure_blocks_otherwise_valid_host(self):
        source = self.root / 'source.html'; source.write_text('official filing fixture')
        self.case['evidence'] = [{'source_id': 'S01', 'path': str(source),
            'sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'url': 'https://issuer.test/release'}]
        self.case['machine_contract']['public_source_ids'] = ['S01']
        result = self.run_audit(answer=self.calc+'\n[S01](/local/source.html)')
        self.assertFalse(result['machine_checks_pass'])
        self.assertEqual(result['errors'], ['PUBLIC_SOURCE_LINK_NOT_VERIFIED:S01'])
        result = self.run_audit(answer=self.calc+'\n[S01](https://issuer.test/release)')
        self.assertTrue(result['machine_checks_pass'])
        self.assertFalse(result['research_complete'])

    def test_registered_local_artifact_can_accompany_public_link(self):
        source = self.root / 'source.pdf'
        self.case['evidence'] = [{'source_id': 'S01', 'path': str(source),
            'url': 'https://issuer.test/release'}]
        self.case['machine_contract']['public_source_ids'] = ['S01']
        public = '[S01 release](https://issuer.test/release)'
        local = f'[S01 PDF]({source})'
        self.assertEqual(public_citations(public+'\n'+local, self.case)[1], [])
        for answer in [local, public+'\n[S01 PDF](/unregistered.pdf)',
                       public+'\n[S01](https://other.test/release)'+local]:
            with self.subTest(answer=answer):
                self.assertTrue(public_citations(answer, self.case)[1])

    def test_missing_or_ambiguous_public_source_registration_fails(self):
        self.case['machine_contract']['public_source_ids'] = ['S01']
        answer = '[S01](https://issuer.test/release)'
        self.assertTrue(public_citations(answer, self.case)[1])
        source = {'source_id': 'S01', 'url': 'https://issuer.test/release'}
        self.case['evidence'] = [source, source.copy()]
        self.assertTrue(public_citations(answer, self.case)[1])
        self.case['machine_contract']['public_source_ids'] = 'S01'
        self.assertEqual(public_citations(answer, self.case)[1], ['INVALID_PUBLIC_SOURCE_CONTRACT'])

    def test_exit_zero_without_receipt_is_rejected(self):
        r = self.run_audit([self.event(payload={'ok': True})])
        self.assertFalse(r['machine_checks_pass'])

    def test_missing_route_is_rejected(self):
        self.assertIn('ROUTE_REQUIRED_NOT_VERIFIED', self.run_audit([])['errors'])

    def test_failed_route_is_not_completed(self):
        self.assertFalse(self.run_audit([self.event(code=2)])['machine_checks_pass'])

    def test_valid_retry_can_recover(self):
        self.assertTrue(self.run_audit([self.event(code=2), self.event()])['machine_checks_pass'])

    def test_later_failure_invalidates_earlier_success(self):
        self.assertFalse(self.run_audit([self.event(), self.event(code=2)])['machine_checks_pass'])

    def test_echo_of_route_is_not_an_invocation(self):
        self.assertFalse(self.run_audit([self.event(command='echo investment_route_plan.sh --output compact-json')])['machine_checks_pass'])

    def test_help_does_not_complete_route(self):
        self.assertFalse(self.run_audit([self.event(command='bash /host/investment_route_plan.sh --help')])['machine_checks_pass'])

    def test_expected_identity_block_is_not_ready(self):
        self.case['machine_contract']['allowed_route_blocks'] = ['AMBIGUOUS_SECURITY']
        self.receipt.update(status='needs_input', error_code='AMBIGUOUS_SECURITY')
        r = self.run_audit()
        self.assertTrue(r['machine_checks_pass'])
        self.assertFalse(r['route']['ready'])

    def test_unexpected_block_is_rejected(self):
        self.receipt.update(status='needs_input', error_code='UNKNOWN')
        self.assertFalse(self.run_audit()['machine_checks_pass'])

    def test_missing_required_calculations_is_not_zero_check_pass(self):
        self.assertIn('CALCULATION_RECEIPTS_REQUIRED', self.run_audit(answer='Calculated with Decimal')['errors'])

    def test_optional_calculations_still_audit_present_receipts(self):
        self.case['machine_contract']['calculations_required'] = False
        self.assertFalse(self.run_audit(answer=self.calc.replace('0.15', '0.9'))['machine_checks_pass'])

    def test_tampered_answer_is_rejected(self):
        self.assertIn('ARTIFACT_HASH_MISMATCH:answer.md', self.run_audit(tamper=True)['errors'])

    def test_date_prefix_shell_wrapper_is_supported(self):
        self.assertTrue(route_command('/bin/zsh -lc "date\nbash /host/investment_route_plan.sh --output compact-json"'))
        self.assertFalse(route_command('bash /host/investment_route_plan.sh --output compact-json; true'))

    def test_unrelated_task_can_have_no_route_or_calculation(self):
        self.case['machine_contract'].update(route_required=False, calculations_required=False)
        self.assertTrue(self.run_audit([], answer='Mechanism review only')['machine_checks_pass'])

    def test_malformed_command_or_output_is_not_a_receipt(self):
        self.assertFalse(route_command(None))
        e = self.event()
        e['item']['aggregated_output'] = None
        self.assertFalse(self.run_audit([e])['machine_checks_pass'])

    def test_ready_label_does_not_replace_receipt_structure(self):
        self.receipt['stage_chain'] = [None]
        self.assertFalse(self.run_audit()['machine_checks_pass'])

    def test_source_drift_blocks_otherwise_valid_answer(self):
        source = self.root / 'filing.pdf'
        source.write_bytes(b'%PDF-original')
        self.case['evidence'] = [{'source_id': 'S01', 'path': str(source),
                                 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()}]
        self.assertTrue(self.run_audit()['machine_checks_pass'])
        source.write_bytes(b'%PDF-changed')
        self.assertIn('SOURCE_EVIDENCE_NOT_VERIFIED:S01', self.run_audit()['errors'])

    def test_missing_source_is_not_ignored(self):
        self.case['evidence'] = [{'source_id': 'S01', 'path': str(self.root / 'missing.pdf'), 'sha256': '0' * 64}]
        self.assertIn('SOURCE_EVIDENCE_NOT_VERIFIED:S01', self.run_audit()['errors'])

    def test_native_portfolio_receipts_require_trace_parity_and_correct_math(self):
        value = {'schema': 'money-craft.portfolio-audit.v1', 'valid': True,
                 'calculations': [{'id': 'C001', 'operation': 'multiply',
                                   'inputs': ['800000', '0.0003'], 'expected': '240', 'tolerance': '0'}]}
        def answer(v):
            return '```json\n' + json.dumps(v) + '\n```'
        event = self.event(payload=value, command='python3 -c "portfolio audit fixture"')
        result = self.run_audit([self.event(), event], answer(value))
        self.assertTrue(result['machine_checks_pass'])
        self.assertEqual(len(result['financial']['checks']), 1)
        self.assertFalse(result['research_complete'])
        self.assertIn('PORTFOLIO_RESULT_NOT_BOUND_TO_TRACE', self.run_audit([self.event()], answer(value))['errors'])
        event['item']['exit_code'] = 2
        self.assertFalse(self.run_audit([self.event(), event], answer(value))['machine_checks_pass'])
        event['item']['exit_code'] = 0
        changed = json.loads(json.dumps(value));changed['calculations'][0]['expected'] = '250'
        self.assertIn('PORTFOLIO_RESULT_NOT_BOUND_TO_TRACE', self.run_audit([self.event(), event], answer(changed))['errors'])
        bad_event = self.event(payload=changed, command='python3 fixture.py')
        self.assertIn('FINANCIAL_AUDIT_FAILED', self.run_audit([self.event(), bad_event], answer(changed))['errors'])

    def test_rejected_input_json_does_not_invent_calculation_requirement(self):
        self.case['machine_contract']['calculations_required'] = False
        value = {'schema': 'money-craft.portfolio-audit.v1', 'valid': False, 'error': 'source digest mismatch'}
        r = self.run_audit([self.event(), self.event(code=2, payload=value, command='python3 fixture.py')], '```json\n'+json.dumps(value)+'\n```')
        self.assertTrue(r['machine_checks_pass'])
        self.assertEqual(r['financial']['checks'], [])
        self.case['machine_contract']['calculations_required'] = True
        self.assertIn('CALCULATION_RECEIPTS_REQUIRED', self.run_audit(answer='```json\n'+json.dumps(value)+'\n```')['errors'])

    def test_stdout_receipts_require_canonical_input_digest_in_answer(self):
        value = {'schema': 'money-craft.portfolio-audit.v1', 'valid': True,
                 'input': {'principal': '800000'},
                 'input_hash_encoding': 'UTF-8 JSON ensure_ascii=False sort_keys=True separators=(comma,colon)',
                 'calculations': [{'id':'C001','operation':'multiply','inputs':['800000','0.0003'],'expected':'240','tolerance':'0'}]}
        digest = hashlib.sha256(json.dumps(value['input'], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        value['input_sha256'] = digest
        answer = 'Input digest: '+digest
        def run(v, text=answer, code=0):
            return self.run_audit([self.event(),self.event(code=code,payload=v,command='python3 fixture.py')],text)
        self.assertTrue(run(value)['machine_checks_pass'])
        self.assertEqual(len(run(value)['financial']['checks']),1)
        self.assertFalse(run(value,'No bound digest')['machine_checks_pass'])
        self.assertFalse(run(value,code=2)['machine_checks_pass'])
        for field,replacement in [('input',{'principal':'1'}),('input_sha256','0'*64),('input_hash_encoding','unknown')]:
            changed=json.loads(json.dumps(value));changed[field]=replacement
            self.assertFalse(run(changed)['machine_checks_pass'],field)
        changed=json.loads(json.dumps(value));changed['calculations'][0]['expected']='241'
        self.assertIn('FINANCIAL_AUDIT_FAILED',run(changed)['errors'])
        duplicate_events = [self.event(),self.event(payload=value,command='python3 a.py'),self.event(payload=value,command='python3 b.py')]
        self.assertIn('AMBIGUOUS_PORTFOLIO_RESULT',self.run_audit(duplicate_events,answer)['errors'])
        changed=json.loads(json.dumps(value));changed['input']={'principal':float('nan')}
        self.assertIn('INVALID_PORTFOLIO_INPUT_DIGEST',run(changed)['errors'])

    def test_native_portfolio_empty_and_duplicate_json_are_rejected(self):
        for value in [[], None, {}]:
            report = {'schema': 'money-craft.portfolio-audit.v1', 'valid': True, 'calculations': value}
            r = self.run_audit([self.event(), self.event(payload=report)], '```json\n'+json.dumps(report)+'\n```')
            self.assertFalse(r['machine_checks_pass'])
        raw = '{"schema":"money-craft.portfolio-audit.v1","valid":false,"valid":true,"calculations":[]}'
        r = self.run_audit(answer='```json\n'+raw+'\n```')
        self.assertIn('INVALID_PORTFOLIO_RESULT_JSON',r['errors'])

    def test_runner_rejects_changed_source_before_host_launch(self):
        source = self.root / 'filing.pdf'
        source.write_bytes(b'%PDF-changed')
        case = {**self.case, 'status': 'READY_HISTORICAL', 'facts': 'Read filing',
                'evidence': [{'source_id': 'S01', 'path': str(source), 'sha256': '0' * 64}]}
        cases = self.root / 'cases.json'
        cases.write_text(json.dumps({'cases': [case]}))
        output = self.root / 'never-created'
        command = Path(__file__).resolve().parents[1] / 'scripts/run_skill_task.py'
        result = subprocess.run([sys.executable, str(command), '--case', 'sample',
                                 '--case-file', str(cases), '--output-dir', str(output)],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('evidence hash mismatch', result.stderr)
        self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
