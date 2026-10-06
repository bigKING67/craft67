from __future__ import annotations
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/money-craft/scripts'))
import portfolio_audit
from financial_rigor import audit_text


def fixture(root):
    sources, funds = [], []
    for fid, weight, positions in [('US:A','0.6',[('X:A','X','0.3'),('X:C','X','0.2')]),('US:B','0.4',[('X:A','X','0.4')])]:
        sid = 'S01' if fid == 'US:A' else 'S02'
        path = root / (sid+'.txt');path.write_text(fid)
        sources.append(dict(id=sid,fund_id=fid,path=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),url='https://example.com/'+sid,as_of='2026-06-30'))
        funds.append(dict(id=fid,quote_currency='USD',weight=weight,fee=dict(rate='0.0003',source_id=sid,locator='p1'),holdings=dict(coverage='partial',as_of='2026-06-30',source_id=sid,locator='p2',positions=[dict(security_id=s,issuer_id=i,weight=w) for s,i,w in positions])))
    return dict(schema=portfolio_audit.SCHEMA,as_of='2026-09-19',base_currency='CNY',principal='1000000',assumption_note='Synthetic fixture; no actual portfolio',max_loss='0.2',max_issuer_weight='0.4',sources=sources,funds=funds,scenarios=[dict(id='stress',assumption_note='Hypothetical shocks',asset_returns={'US:A':'-0.35','US:B':'-0.08'},fx_returns={'USD':'-0.1'})])


class PortfolioTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.input=self.root/'input.json';self.payload=fixture(self.root)

    def run_input(self, payload=None):
        self.input.write_text(json.dumps(self.payload if payload is None else payload))
        return portfolio_audit.review_file(self.input)

    def test_fee_issuer_coverage_and_currency(self):
        r=self.run_input();self.assertTrue(r['valid'],r)
        from decimal import Decimal as D
        self.assertEqual(D(r['weighted_expense_ratio']),D('.0003'))
        self.assertEqual(D(r['static_annual_fee']),D('300'))
        self.assertEqual(D(r['holdings_coverage']),D('.46'))
        self.assertEqual(r['issuers'][0]['constraint_status'],'BREACHED')
        self.assertEqual(D(r['issuers'][0]['known_weight']),D('.46'))
        self.assertEqual(D(r['overlaps'][0]['security_weight_overlap']),D('.3'))
        self.assertEqual(r['overlaps'][0]['scope'],'LOWER_BOUND')
        self.assertEqual(D(r['scenarios'][0]['base_currency_return']),D('-.3178'))
        self.assertEqual(r['scenarios'][0]['loss_constraint'],'BREACHED')
        receipts='\n'.join('<!-- money-craft-calc: '+json.dumps(c)+' -->' for c in r['calculations'])
        self.assertTrue(audit_text(receipts)['valid'])

    def test_large_valid_holdings_remain_auditable_past_four_digit_ids(self):
        self.payload['funds'][0]['holdings']['positions'] = [
            dict(security_id=f'L:{i}', issuer_id='LARGE', weight='0.00001') for i in range(10000)]
        result = self.run_input()
        self.assertTrue(result['valid'], result)
        self.assertLess(self.input.stat().st_size, portfolio_audit.MAX_INPUT)
        self.assertGreater(len(result['calculations']), 9999)
        sys.path.insert(0, str(ROOT / 'scripts'))
        from audit_skill_task import portfolio_receipts
        output = json.dumps(result)
        receipts, errors = portfolio_receipts('```json\n'+output+'\n```',
            [{'exit_code': 0, 'aggregated_output': output}])
        self.assertEqual(errors, [])
        checked = audit_text(receipts)
        self.assertTrue(checked['valid'], checked['errors'])
        self.assertEqual(len(checked['checks']), len(result['calculations']))

    def test_partial_zero_overlap_and_within_limit_remain_unknown(self):
        self.payload['max_issuer_weight']='0.9'
        self.payload['funds'][1]['holdings']['positions']=[]
        r=self.run_input();self.assertTrue(r['valid']);self.assertEqual(r['overlaps'][0]['scope'],'LOWER_BOUND')
        self.assertEqual(r['issuers'][0]['constraint_status'],'UNVERIFIED')

    def test_complete_and_identity_fx(self):
        for f in self.payload['funds']:
            f['quote_currency']='CNY';f['holdings']['coverage']='complete';f['holdings']['positions']=[dict(security_id='CASH:CNY',issuer_id='CASH',weight='1')]
        self.payload['scenarios'][0]['fx_returns']={}
        r=self.run_input();self.assertTrue(r['valid']);self.assertEqual(r['overlaps'][0]['scope'],'EXACT_WITHIN_INPUT')
        self.assertEqual(r['scenarios'][0]['base_currency_return'],'-0.242')

    def test_invalid_inputs_fail_closed(self):
        variants=[]
        def add(change):
            p=copy.deepcopy(self.payload);change(p);variants.append(p)
        add(lambda p:p['funds'][0].update(weight='0.7'))
        add(lambda p:p['funds'][0]['fee'].update(rate=0.03))
        add(lambda p:p['funds'][0]['holdings'].update(coverage='complete'))
        add(lambda p:p['funds'][0]['holdings']['positions'].append(copy.deepcopy(p['funds'][0]['holdings']['positions'][0])))
        add(lambda p:p['funds'][1]['holdings']['positions'][0].update(issuer_id='OTHER'))
        add(lambda p:p['funds'][0]['fee'].update(source_id='S02'))
        add(lambda p:p['sources'][0].update(sha256='0'*64))
        add(lambda p:p['sources'][0].update(as_of='2027-01-01'))
        add(lambda p:p['sources'][1].update(as_of='2026-07-01'))
        add(lambda p:p['scenarios'][0].update(fx_returns={}))
        add(lambda p:p['scenarios'][0]['asset_returns'].update({'US:A':'-1.01'}))
        add(lambda p:p['scenarios'][0]['fx_returns'].update(USD='NaN'))
        add(lambda p:p.update(principal=True))
        add(lambda p:p.update(principal='1e10'))
        add(lambda p:p.update(max_loss='0.200000000000000000000001'))
        add(lambda p:p.update(as_of='2026-02-30'))
        add(lambda p:p.update(unrecognized='x'))
        add(lambda p:p['funds'].append(copy.deepcopy(p['funds'][0])))
        for p in variants:
            with self.subTest(payload=p):self.assertFalse(self.run_input(p)['valid'])

    def test_limits_are_breached_only_when_strictly_exceeded(self):
        self.payload['scenarios'][0].update(asset_returns={'US:A':'-0.2','US:B':'-0.2'},fx_returns={'USD':'0'})
        self.payload['max_issuer_weight']='0.46'  # X = 0.6*0.5 + 0.4*0.4
        result=self.run_input()
        self.assertEqual(result['scenarios'][0]['loss_constraint'],'WITHIN_SCENARIO')
        self.assertEqual(result['issuers'][0]['known_weight'],'0.46')
        self.assertEqual(result['issuers'][0]['constraint_status'],'UNVERIFIED')  # partial holdings
        self.payload['max_issuer_weight']='0.45'
        self.assertEqual(self.run_input()['issuers'][0]['constraint_status'],'BREACHED')

    def test_mixed_dates_rejected_even_with_matching_sources(self):
        self.payload['sources'][1]['as_of']='2026-07-01'
        self.payload['funds'][1]['holdings']['as_of']='2026-07-01'
        self.assertIn('mixed holdings',self.run_input()['error'])

    def test_duplicate_json_and_source_tamper_cli(self):
        self.input.write_text('{"schema":"x","schema":"y"}')
        self.assertFalse(portfolio_audit.review_file(self.input)['valid'])
        self.run_input();before=self.input.read_bytes();(self.root/'S01.txt').write_text('changed')
        result=subprocess.run([sys.executable,str(ROOT/'skills/money-craft/scripts/money_craft.py'),'portfolio','audit','--input',str(self.input),'--json'],capture_output=True,text=True)
        self.assertEqual(result.returncode,2,result.stderr);self.assertFalse(json.loads(result.stdout)['valid'])
        self.assertEqual(before,self.input.read_bytes())

    def test_hypothetical_risk_failure_is_successful_audit_cli(self):
        self.run_input();result=subprocess.run([sys.executable,str(ROOT/'skills/money-craft/scripts/money_craft.py'),'portfolio','audit','--input',str(self.input),'--json'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(json.loads(result.stdout)['scenarios'][0]['loss_constraint'],'BREACHED')


if __name__=='__main__':unittest.main()
