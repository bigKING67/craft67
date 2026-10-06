"""Offline integration with actual pandas objects; optional dependency lane."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import types
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/money-craft/scripts'))
import yfinance_adapter as adapter

try:
    import pandas as pd
except ImportError:
    pd = None


@unittest.skipIf(pd is None,'pandas integration requires optional data dependencies')
class YFinancePandasTests(unittest.TestCase):
    def test_real_transport_exceptions_have_bounded_retry_policy(self):
        from curl_cffi.requests.exceptions import ConnectTimeout, ReadTimeout, SSLError
        from yfinance.exceptions import YFRateLimitError
        for error, attempts in ((ConnectTimeout('fixture'),3),(ReadTimeout('fixture'),3),(TimeoutError('fixture'),3),(YFRateLimitError(),3),(SSLError('fixture'),1),(ValueError('fixture'),1)):
            calls, sleeps = [], []
            def ticker(symbol):
                calls.append(symbol)
                raise error
            module = types.SimpleNamespace(Ticker=ticker)
            with self.subTest(error=type(error).__name__), self.assertRaises(adapter.YFinanceAdapterError) as caught:
                adapter.YFinanceClient(module,version='fixture',sleeper=sleeps.append).request('snapshot',{'symbol':'NVDA'})
            self.assertEqual(len(calls),attempts)
            self.assertEqual(sleeps,[0.5,1.0] if attempts==3 else [])
            self.assertEqual(caught.exception.retryable,attempts==3)

    def test_nullable_cells_and_exports_use_null(self):
        frame = pd.DataFrame({'value':pd.Series([1,pd.NA,0],dtype='Int64')})
        result = adapter._frame(frame)
        self.assertEqual(result['rows'],[[1],[None],[0]])
        module = types.SimpleNamespace(Ticker=lambda symbol:types.SimpleNamespace(get_income_stmt=lambda **kwargs:frame,get_balance_sheet=None,get_cash_flow=None))
        result = adapter.YFinanceClient(module,version='fixture').request('financials.income',{'symbol':'NVDA','period':'annual'})
        self.assertEqual(json.loads(result.adapter_export)['data']['table']['rows'],[[1],[None],[0]])
        self.assertNotIn('<NA>',result.adapter_export.decode())

    def test_pandas_missing_scalars_and_invalid_date_index(self):
        self.assertIsNone(adapter._scalar(pd.NA))
        self.assertIsNone(adapter._scalar(pd.NaT))
        with self.assertRaises(adapter.YFinanceAdapterError):
            adapter._index_dates(pd.DataFrame({'Close':[1]},index=[pd.NaT]))

    def test_duplicate_labels_and_zero_columns_preserve_positions(self):
        frame = pd.DataFrame([[1,2],[3,4]],index=['a','a'],columns=['x','x'])
        self.assertEqual(adapter._frame(frame)['rows'],[[1,2],[3,4]])
        self.assertEqual(adapter._frame(frame,limit_columns=1)['rows'],[[1],[3]])
        self.assertEqual(adapter._frame(pd.DataFrame(index=['a','b']))['rows'],[[],[]])

    def test_timezone_filter_and_nullable_action_currency(self):
        index = pd.DatetimeIndex(['2026-01-01','2026-01-31','2026-02-01'],tz='America/New_York')
        frame = pd.DataFrame({'Dividends':[0.1,0,0.2],'Dividends FX':pd.array(['USD',pd.NA,'USD'],dtype='string')},index=index)
        filtered = adapter._filter_frame_dates(frame,'2026-01-01','2026-01-31')
        result = adapter._frame(filtered,text_columns=('Dividends FX',))
        self.assertEqual(result['rows'],[[adapter.Decimal('0.1'),'USD'],[0,None]])
        self.assertEqual(adapter._index_dates(filtered),['2026-01-01','2026-01-31'])
