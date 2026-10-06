from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT/'skills/money-craft/scripts'
sys.path.insert(0,str(SCRIPTS))
import money_craft as mc


class CliPreflightTests(unittest.TestCase):
    def test_explicit_empty_optional_dates_are_rejected(self):
        parser = mc.build_parser()
        cases = (
            ['series','--series-id','PCEPI','--as-known-on',''],
            ['observations','--series-id','PCEPI','--as-known-on',''],
            ['observations','--series-id','PCEPI','--start',''],
            ['observations','--series-id','PCEPI','--end',''],
            ['vintages','--series-id','PCEPI','--start',''],
            ['vintages','--series-id','PCEPI','--end',''],
            ['calendar','--start',''],['calendar','--end',''],
            ['corporate-actions','--provider','yfinance','--symbol','NVDA','--start',''],
            ['corporate-actions','--provider','fuyao','--thscode','600519.SH','--end',''],
        )
        for flags in cases:
            with self.subTest(flags=flags), self.assertRaises(mc.MoneyCraftError) as caught:
                mc.prepare_operation(parser.parse_args(['data',*flags]))
            self.assertEqual(caught.exception.exit_code,mc.EXIT_USAGE)
        for flags in (['series','--series-id','PCEPI'],['vintages','--series-id','PCEPI'],['calendar'],['corporate-actions','--provider','yfinance','--symbol','NVDA']):
            mc.prepare_operation(parser.parse_args(['data',*flags]))

    def test_yfinance_rejects_fuyao_identifiers_before_provider_access(self):
        cases = (("snapshot","--thscodes",[]),("valuations","--thscodes",[]),
                 ("history","--thscode",["--start","2026-01-01","--end","2026-01-31"]),
                 ("financials","--thscode",["--statement","income"]),("corporate-actions","--thscode",[]))
        parser = mc.build_parser()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)/"capture"
            for operation,flag,extra in cases:
                base = ['data',operation,'--provider','yfinance','--symbol','NVDA',*extra]
                valid = parser.parse_args(base)
                _,_,parameters,_ = mc.prepare_operation(valid)
                self.assertEqual(parameters['symbol'],'NVDA')
                for value in ('600519.SH',''):
                    args = parser.parse_args([*base,flag,value,'--capture-dir',str(target),'--source-id','S01'])
                    with self.subTest(operation=operation,value=value), mock.patch.object(mc.yfinance_adapter,'YFinanceClient',side_effect=AssertionError('Provider reached')):
                        with self.assertRaises(mc.MoneyCraftError) as caught:
                            mc.run_data(args)
                        self.assertEqual(caught.exception.exit_code,mc.EXIT_USAGE)
                        self.assertEqual(caught.exception.kind,'usage_error')
                        self.assertFalse(target.exists())

    def test_dates_require_canonical_calendar_format(self):
        for value in ('20260101','2026-W01-4','2026-1-1','2026-02-30'):
            with self.subTest(value=value), self.assertRaises(mc.MoneyCraftError) as caught:
                mc.parse_iso_date(value)
            self.assertEqual(caught.exception.exit_code,mc.EXIT_USAGE)
        self.assertEqual(mc.parse_iso_date('2024-02-29'),dt.date(2024,2,29))

    def test_invalid_capture_arguments_stop_before_provider_construction(self):
        script = r'''
import sys,json
sys.path.insert(0,sys.argv[1])
import money_craft as mc
import fred_adapter as fred
import yfinance_adapter as yf
def forbidden(*args,**kwargs):
    raise AssertionError('provider or credential access reached')
mc.load_fuyao_credential = forbidden
mc.FuyaoClient = forbidden
fred.load_credential = forbidden
fred.FredClient = forbidden
yf.YFinanceClient = forbidden
sys.argv = ['money_craft.py','data','search','--provider',sys.argv[2],'--query','fixture']+json.loads(sys.argv[3])
raise SystemExit(mc.main())
'''
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)/'capture'
            for provider in ('fuyao','fred','yfinance'):
                for flags in (['--capture-dir',str(target)],['--source-id','S01'],['--capture-dir',str(target),'--source-id','invalid']):
                    with self.subTest(provider=provider,flags=flags):
                        result = subprocess.run([sys.executable,'-c',script,str(SCRIPTS),provider,json.dumps(flags)],capture_output=True,text=True,timeout=10)
                        self.assertEqual(result.returncode,mc.EXIT_USAGE,result.stdout+result.stderr)
                        self.assertEqual(json.loads(result.stdout)['error']['kind'],'usage_error')
                        self.assertFalse(target.exists())
