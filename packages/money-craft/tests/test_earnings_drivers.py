import copy
import json
import unittest
from decimal import Decimal
import test_earnings_baseline as fixtures
import earnings_drivers as model
import earnings_update as eu


class DriverTests(unittest.TestCase):
    def setUp(self):
        helper=fixtures.BaselineTests(); helper.setUp(); self.addCleanup(helper.doCleanups)
        self.root=helper.root
        refs=[dict(source_id='S03',locator='synthetic model inputs')]
        self.payload=dict(schema='money-craft.earnings-drivers-input.v1',security_id='CN-SH:600519',currency='CNY',as_of='2026-04-01',
            sources=helper.preview['sources'],dimension='product',historical_period=dict(start='2025-01-01',end='2025-06-30',kind='ytd',accounting_basis='synthetic consolidated'),
            forecast_period=dict(start='2026-01-01',end='2026-06-30',kind='ytd',accounting_basis='synthetic consolidated'),
            segments={'A':dict(dimension='product',revenue='100',source_refs=refs)},
            historical=dict(revenue='100',net_income='30',gross_margin='0.6',expense_rate='0.2',tax_rate='0.25',other_pretax='0',minority_profit='0',source_refs=refs),
            scenarios={},sensitivity=[dict(driver='gross_margin',delta='0.01')])
        for name,growth in [('bear','-0.1'),('base','0'),('bull','0.1')]:
            self.payload['scenarios'][name]={k:dict(value=v,rationale='synthetic hypothesis',confirmation_condition='test evidence confirms',invalidation_condition='test evidence contradicts',next_evidence='test disclosure',source_refs=refs) for k,v in {'growth:A':growth,'gross_margin':'0.6','expense_rate':'0.2','tax_rate':'0.25','other_pretax':'0','minority_profit':'0'}.items()}

    def run_model(self):
        p=self.root/'model.json';p.write_text(json.dumps(self.payload));return model.review_file(p)

    def test_scenarios_and_sensitivity(self):
        result=self.run_model()
        self.assertEqual(Decimal(result['scenarios']['base']['net_income']),30)
        self.assertEqual(Decimal(result['sensitivity'][0]['net_income_change']),Decimal('0.75'))
        self.assertEqual(result['claim_support'],'UNVERIFIED')

    def test_mixed_dimensions_rejected(self):
        self.payload['segments']['A']['dimension']='channel'
        with self.assertRaises(eu.EarningsError):self.run_model()

    def test_history_must_tie(self):
        self.payload['historical']['net_income']='31'
        with self.assertRaises(eu.EarningsError):self.run_model()

    def test_missing_falsification_rejected(self):
        self.payload['scenarios']['base']['gross_margin']['invalidation_condition']=''
        with self.assertRaises(eu.EarningsError):self.run_model()

    def test_invalid_shock_rejected(self):
        self.payload['sensitivity'][0]['delta']='0.5'
        with self.assertRaises(eu.EarningsError):self.run_model()

    def test_nonfinite_rejected(self):
        self.payload['scenarios']['base']['gross_margin']['value']='NaN'
        with self.assertRaises(eu.EarningsError):self.run_model()

    def test_future_source_rejected(self):
        self.payload['sources']['S03']['published_on']='2027-01-01'
        with self.assertRaises(eu.EarningsError):self.run_model()

    def test_actual_bridge_and_residual(self):
        self.payload['as_of']='2026-09-01'
        self.payload['sources']['S03']['published_on']='2026-08-01'
        values={k:v['value'] for k,v in self.payload['scenarios']['base'].items()};values['growth:A']='0.1';values['gross_margin']='0.65'
        self.payload['actual']=dict(period=self.payload['forecast_period'],drivers=values,revenue='110',net_income='40',source_refs=[dict(source_id='S03',locator='synthetic actual')])
        result=self.run_model()['actual_review']
        self.assertEqual(result['residual_status'],'REQUIRES_RESEARCH')
        total=sum(Decimal(x['contribution']) for x in result['bridge'])+Decimal(result['unexplained_residual'])
        self.assertEqual(total,Decimal(result['actual_vs_base_net_income']))

    def test_actual_window_mismatch_rejected(self):
        self.payload['actual']=dict(period={})
        with self.assertRaises(eu.EarningsError):self.run_model()

    def test_linked_model_tampering_detected(self):
        import earnings_baseline as baseline
        helper=fixtures.BaselineTests();helper.setUp();self.addCleanup(helper.doCleanups)
        artifact=helper.root/'model-input.json';artifact.write_text('{}')
        helper.preview['linked_model_hashes']={'model-input.json':eu.digest(artifact)}
        helper.seal();baseline.inspect_baseline(helper.sealed)
        artifact.write_text('{"changed":true}')
        with self.assertRaises(eu.EarningsError):baseline.inspect_baseline(helper.sealed)

    def test_invalid_fiscal_windows_rejected(self):
        for mode in ('reversed', 'annual', 'empty_basis'):
            with self.subTest(mode=mode):
                saved = copy.deepcopy(self.payload)
                for key in ('historical_period', 'forecast_period'):
                    period = self.payload[key]
                    if mode == 'reversed': period['start'], period['end'] = period['end'], period['start']
                    elif mode == 'annual': period['kind'] = 'annual'
                    else: period['accounting_basis'] = ''
                with self.assertRaises(eu.EarningsError): self.run_model()
                self.payload = saved

    def test_profitable_endpoints_survive_unavailable_bridge(self):
        self.payload['as_of'] = '2026-09-01'
        self.payload['sources']['S03']['published_on'] = '2026-08-01'
        values = {k:v['value'] for k,v in self.payload['scenarios']['base'].items()}
        values.update(gross_margin='0.1', expense_rate='0.05')
        self.payload['actual'] = dict(period=self.payload['forecast_period'], drivers=values, revenue='100', net_income='3.75',
            source_refs=[dict(source_id='S03', locator='synthetic actual')])
        result = self.run_model()
        self.assertTrue(result['valid'])
        self.assertEqual(result['actual_review']['bridge_status'], 'UNAVAILABLE')
        self.assertEqual(result['actual_review']['bridge'], [])
        self.assertEqual(Decimal(result['actual_review']['actual_model']['net_income']), Decimal('3.75'))
        self.assertEqual(result['actual_review']['residual_status'], 'RECONCILED')
