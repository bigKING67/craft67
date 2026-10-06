"""Synthetic crosscheck fixtures; no live provider payloads are embedded."""
import datetime as dt
import hashlib
import json
import unittest
from decimal import localcontext
import test_earnings_baseline as fixtures
import earnings_crosscheck as crosscheck
import earnings_update as eu


def millis(value):
    return int(dt.datetime.fromisoformat(value + 'T00:00:00+08:00').timestamp() * 1000)


class CrosscheckTests(unittest.TestCase):
    def setUp(self):
        helper = fixtures.BaselineTests()
        helper.setUp()
        self.addCleanup(helper.doCleanups)
        helper.seal()
        self.root, self.sealed = helper.root, helper.sealed
        self.folder = self.root / 'capture'
        self.folder.mkdir()
        self.raw = {'code': 0, 'request_id': 'synthetic', 'data': {'item': [
            dict(thscode='600519.SH', fiscal_year=2025, fiscal_period='Q1', period='quarterly', currency='CNY',
                 period_end_ms=millis('2025-03-31'), report_date_ms=millis('2025-04-20'), operating_income='100'),
            dict(thscode='600519.SH', fiscal_year=2025, fiscal_period='Q2', period='quarterly', currency='CNY',
                 period_end_ms=millis('2025-06-30'), report_date_ms=millis('2025-08-20'), operating_income='160')]}}
        self.spec = dict(schema='money-craft.earnings-crosscheck-input.v1', security_id='CN-SH:600519', as_of='2026-04-01',
            provider_capture='capture', provider_basis='ytd_confirmed_against_filing', checks=[dict(metric='revenue', year=2025,
            quarter=2, kind='quarter', unit='CNY', value='60', source_refs=[dict(source_id='S03', locator='synthetic table')])])

    def run_check(self):
        path = self.root / 'check.json'
        path.write_text(json.dumps(self.spec))
        body = json.dumps(self.raw).encode()
        (self.folder / 'response.json').write_bytes(body)
        (self.folder / 'capture.json').write_text(json.dumps(dict(schema='money-craft.source-capture.v1', provider='fuyao',
            operation='financials.income', response_sha256=hashlib.sha256(body).hexdigest(), request_id='synthetic', fetched_at='2026-03-20T08:00:00Z')))
        return crosscheck.check_file(path, self.sealed)

    def test_quarter_from_cumulative_and_no_auto_promotion(self):
        result = self.run_check()
        self.assertEqual(result['checks'][0]['provider_value'], '60')
        self.assertEqual(result['numeric_status'], 'MATCHED')
        self.assertEqual(result['research_readiness'], 'PARTIAL')
        self.assertTrue(result['captured_after_baseline'] is False)

    def test_threshold_boundaries(self):
        self.spec['checks'][0].update(kind='ytd', value='100')
        for value, expected in [('101','MATCHED'), ('101.01','REVIEW_REQUIRED'), ('105','REVIEW_REQUIRED'), ('105.01','CONFLICT')]:
            with self.subTest(value=value):
                self.raw['data']['item'][1]['operating_income'] = value
                self.assertEqual(self.run_check()['numeric_status'], expected)

    def test_missing_capture(self):
        self.spec.pop('provider_capture')
        self.assertEqual(self.run_check()['numeric_status'], 'MISSING')

    def test_missing_or_null_period_is_not_zero(self):
        self.raw['data']['item'][0]['operating_income'] = None
        result = self.run_check()
        self.assertEqual(result['numeric_status'], 'MISSING')
        self.assertIsNone(result['checks'][0]['provider_value'])

    def test_basis_must_be_explicit(self):
        self.spec.pop('provider_basis')
        self.assertEqual(self.run_check()['numeric_status'], 'UNVERIFIED_BASIS')

    def test_bad_metadata_rejected(self):
        for key, value in [('currency','USD'), ('period_end_ms',millis('2025-06-29')), ('report_date_ms',millis('2026-05-01'))]:
            with self.subTest(key=key):
                row = self.raw['data']['item'][1]
                original = row[key]; row[key] = value
                with self.assertRaises(eu.EarningsError): self.run_check()
                row[key] = original

    def test_duplicate_period_rejected(self):
        self.raw['data']['item'].append(self.raw['data']['item'][1].copy())
        with self.assertRaises(eu.EarningsError): self.run_check()

    def test_business_failure_rejected(self):
        self.raw['code'] = 4001
        with self.assertRaises(eu.EarningsError): self.run_check()

    def test_nonfinite_rejected(self):
        self.raw['data']['item'][1]['operating_income'] = 'NaN'
        with self.assertRaises((eu.EarningsError, ValueError)): self.run_check()

    def test_capture_tampering_rejected(self):
        self.run_check()
        (self.folder / 'response.json').write_text('{}')
        with self.assertRaises(eu.EarningsError): crosscheck.check_file(self.root / 'check.json', self.sealed)

    def test_future_capture_rejected(self):
        self.run_check()
        path = self.folder / 'capture.json'
        data = json.loads(path.read_text()); data['fetched_at'] = '2027-01-01T00:00:00Z'; path.write_text(json.dumps(data))
        with self.assertRaises(eu.EarningsError): crosscheck.check_file(self.root / 'check.json', self.sealed)

    def test_threshold_does_not_round_with_ambient_precision(self):
        self.spec['checks'][0].update(kind='ytd', value='100')
        for precision, value in [(28, '101.0000000000000000000000000001'), (2, '101.04')]:
            with self.subTest(precision=precision), localcontext() as context:
                context.prec = precision
                self.raw['data']['item'][1]['operating_income'] = value
                self.assertEqual(self.run_check()['numeric_status'], 'REVIEW_REQUIRED')
