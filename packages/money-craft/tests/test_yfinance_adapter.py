from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "money-craft" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import money_craft as mc  # noqa: E402
import research_run  # noqa: E402
import yfinance_adapter as adapter  # noqa: E402


class FakeLoc:
    def __init__(self, frame: "FakeFrame") -> None:
        self.frame = frame

    def __getitem__(self, key: object) -> "FakeFrame":
        if isinstance(key, tuple):
            row_labels, column_labels = key
            row_positions = [self.frame.index.index(label) for label in row_labels]
            column_positions = [self.frame.columns.index(label) for label in column_labels]
        else:
            row_positions = [position for position, keep in enumerate(key) if keep]  # type: ignore[arg-type]
            column_positions = list(range(len(self.frame.columns)))
        return FakeFrame(
            [self.frame.index[position] for position in row_positions],
            [self.frame.columns[position] for position in column_positions],
            [
                [self.frame.rows[row][column] for column in column_positions]
                for row in row_positions
            ],
        )


class FakeFrame:
    def __init__(self, index: list[object], columns: list[object], rows: list[list[object]]) -> None:
        self.index = index
        self.columns = columns
        self.rows = rows
        self.loc = FakeLoc(self)

    def itertuples(self, index: bool = False, name: object | None = None):  # noqa: A002
        if not self.columns and not index:
            return iter(())  # pandas has no arrays to zip in this case.
        return iter(tuple(row) for row in self.rows)


class FakeTicker:
    def __init__(self, symbol: str) -> None:
        self.symbol = symbol
        self.fast_info = {
            "currency": "USD",
            "exchange": "NMS",
            "timezone": "America/New_York",
            "quoteType": "EQUITY",
            "lastPrice": 123.45,
            "marketCap": 3000000000,
        }
        self.history_calls: list[dict[str, object]] = []

    def history(self, **kwargs: object) -> FakeFrame:
        self.history_calls.append(kwargs)
        return FakeFrame(
            [dt.datetime(2026, 8, 21, tzinfo=dt.timezone.utc)],
            ["Open", "Close", "Dividends"],
            [[120.0, 123.45, 0.0]],
        )

    def get_valuation_measures(self, **kwargs: object) -> FakeFrame:
        return FakeFrame(["MarketCap", "PeRatio"], ["Current"], [[3000000000], [30.5]])

    def get_income_stmt(self, **kwargs: object) -> FakeFrame:
        return FakeFrame(["TotalRevenue"], ["2025-01-26", "2024-01-28"], [[1000, 800]])

    get_balance_sheet = get_income_stmt
    get_cash_flow = get_income_stmt

    def get_actions(self, **kwargs: object) -> FakeFrame:
        return FakeFrame(
            [dt.datetime(2025, 1, 1), dt.datetime(2026, 1, 1)],
            ["Dividends", "Stock Splits"],
            [[0.1, 0.0], [0.2, 0.0]],
        )


class FakeSearch:
    def __init__(self, query: str, **kwargs: object) -> None:
        self.quotes = [
            {
                "symbol": query.upper(),
                "shortname": "NVIDIA",
                "longname": "NVIDIA Corporation",
                "exchange": "NMS",
                "quoteType": "EQUITY",
                "currency": "USD",
            }
        ]


class FakeYFinance:
    __version__ = "1.7.0-test"
    Search = FakeSearch

    def __init__(self) -> None:
        self.tickers: list[FakeTicker] = []

    def Ticker(self, symbol: str) -> FakeTicker:  # noqa: N802
        ticker = FakeTicker(symbol)
        self.tickers.append(ticker)
        return ticker


class YFinanceAdapterTests(unittest.TestCase):
    def test_cli_classifies_yfinance_errors_before_capture(self):
        script = r"""
import sys
sys.path.insert(0,sys.argv[1])
import money_craft as mc
import yfinance_adapter as yf
kind,retryable = sys.argv[3],sys.argv[4]=='true'
def unavailable():
    raise yf.YFinanceAdapterError(kind,'fixture failure',retryable=retryable)
yf.YFinanceClient = unavailable
sys.argv = ['money_craft.py','data','snapshot','--provider','yfinance','--symbol','NVDA','--capture-dir',sys.argv[2],'--source-id','S01']
raise SystemExit(mc.main())
"""
        for kind,retryable,expected in (("missing_optional_dependency",False,mc.EXIT_CONFIG),("malformed_response",False,mc.EXIT_SCHEMA),("provider_error",False,mc.EXIT_PROVIDER),("transient_provider_error",True,mc.EXIT_TRANSIENT)):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                capture = Path(directory)/"capture"
                result = subprocess.run([sys.executable,'-c',script,str(SCRIPT_DIR),str(capture),kind,str(retryable).lower()],capture_output=True,text=True,timeout=10)
                self.assertEqual(result.returncode,expected,result.stdout+result.stderr)
                output = json.loads(result.stdout)
                self.assertEqual(output['error']['kind'],kind)
                self.assertEqual(output['error']['retryable'],retryable)
                self.assertFalse(output['ok'])
                self.assertFalse(capture.exists())

    def test_export_invalid_unicode_returns_structured_error(self):
        module = FakeYFinance()
        calls = []
        class Search:
            def __init__(self,*args,**kwargs):
                calls.append(1)
                self.quotes = [{"symbol":"NVDA","shortname":"bad\ud800"}]
        module.Search = Search
        with self.assertRaises(adapter.YFinanceAdapterError) as caught:
            adapter.YFinanceClient(module).request("search",{"query":"NVDA"})
        self.assertEqual(caught.exception.kind,"malformed_response")
        self.assertFalse(caught.exception.retryable)
        self.assertEqual(calls,[1])
        self.assertNotIn("bad",str(caught.exception))

    def test_cli_out_of_range_history_never_creates_capture(self):
        script = r"""
import sys
sys.path.insert(0,sys.argv[1])
from test_yfinance_adapter import FakeYFinance, FakeTicker, FakeFrame
import money_craft as mc
module = FakeYFinance()
ticker = FakeTicker('NVDA')
ticker.history = lambda **kwargs: FakeFrame(['2026-02-01'],['Close'],[[1]])
module.Ticker = lambda symbol: ticker
sys.modules['yfinance'] = module
sys.argv = ['money_craft.py','data','history','--provider','yfinance','--symbol','NVDA','--start','2026-01-01','--end','2026-01-31','--capture-dir',sys.argv[2],'--source-id','S01']
raise SystemExit(mc.main())
"""
        with tempfile.TemporaryDirectory() as directory:
            capture = Path(directory)/"capture"
            result = subprocess.run([sys.executable,"-c",script,str(ROOT/'tests'),str(capture)],capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,mc.EXIT_SCHEMA,result.stdout+result.stderr)
            self.assertEqual(json.loads(result.stdout)["error"]["kind"],"malformed_response")
            self.assertFalse(capture.exists())

    def test_history_rejects_invalid_or_out_of_range_dates(self):
        for date in ("2026-02-30","20260101","garbage",True,"2025-12-31","2026-02-01"):
            with self.subTest(date=date):
                module = FakeYFinance();ticker = FakeTicker("NVDA")
                ticker.history = lambda **kwargs:FakeFrame([date],["Close"],[[1]])
                module.Ticker = lambda symbol:ticker
                with self.assertRaises(adapter.YFinanceAdapterError) as caught:
                    adapter.YFinanceClient(module).request("history",{"symbol":"NVDA","start":"2026-01-01","end":"2026-01-31"})
                self.assertEqual(caught.exception.kind,"malformed_response")
        module = FakeYFinance();ticker = FakeTicker("NVDA")
        ticker.history = lambda **kwargs:FakeFrame([dt.datetime(2026,1,1,tzinfo=dt.timezone(dt.timedelta(hours=8))),"2026-01-31T23:00:00-05:00"],["Close"],[[1],[2]])
        module.Ticker = lambda symbol:ticker
        result = adapter.YFinanceClient(module).request("history",{"symbol":"NVDA","start":"2026-01-01","end":"2026-01-31"})
        self.assertEqual(result.data["table"]["rows"],[[1],[2]])

    def test_actions_validate_dates_before_filtering(self):
        for start,end in ((None,None),("2026-01-01","2026-01-31")):
            with self.assertRaises(adapter.YFinanceAdapterError):
                adapter._filter_frame_dates(FakeFrame(["garbage"],["Dividends"],[[1]]),start,end)
        frame = FakeFrame(["2025-12-31","2026-01-01","2026-01-31","2026-02-01"],["Dividends"],[[0],[1],[2],[3]])
        filtered = adapter._filter_frame_dates(frame,"2026-01-01","2026-01-31")
        self.assertEqual(filtered.index,["2026-01-01","2026-01-31"])

    def test_corporate_actions_preserve_provider_currency_column_only(self):
        module = FakeYFinance();ticker = FakeTicker("NVDA")
        module.Ticker = lambda symbol:ticker
        for currency in ("USD","",None):
            ticker.get_actions = lambda **kwargs:FakeFrame([dt.date(2026,1,1)],["Dividends","Dividends FX"],[[0.2,currency]])
            result = adapter.YFinanceClient(module).request("corporate-actions",{"symbol":"NVDA"})
            self.assertEqual(result.data["table"]["rows"],[[adapter.Decimal("0.2"),currency]])
        for values in ((0.2,{}),(0.2,True),(0.2,123),("0.2","USD")):
            ticker.get_actions = lambda **kwargs:FakeFrame([dt.date(2026,1,1)],["Dividends","Dividends FX"],[list(values)])
            with self.subTest(values=values), self.assertRaises(adapter.YFinanceAdapterError):
                adapter.YFinanceClient(module).request("corporate-actions",{"symbol":"NVDA"})

    def test_frame_rejects_non_numeric_cells_before_column_limit(self):
        for value in (True,False,"12.3","",[],{},dt.date(2026,1,1)):
            with self.subTest(value=value), self.assertRaises(adapter.YFinanceAdapterError) as caught:
                adapter._frame(FakeFrame(["Revenue"],["2025"],[[value]]))
            self.assertEqual(caught.exception.kind,"malformed_response")
        with self.assertRaises(adapter.YFinanceAdapterError):
            adapter._frame(FakeFrame(["Revenue"],["2025","2024"],[[1,"invalid"]]),limit_columns=1)

    def test_frame_numeric_cells_preserve_missing_zero_and_precision(self):
        values = [0,-2,adapter.Decimal("1.234567890123456789"),1.5,None,float("nan"),adapter.Decimal("Infinity")]
        result = adapter._frame(FakeFrame(["Revenue"],list(range(len(values))),[values]))
        self.assertEqual(result["rows"],[[0,-2,adapter.Decimal("1.234567890123456789"),adapter.Decimal("1.5"),None,None,None]])

    def test_snapshot_rejects_non_numeric_quote_fields(self):
        for value in (True,False,"123.45","",[],{}):
            with self.subTest(value=value):
                module = FakeYFinance();ticker = FakeTicker("NVDA")
                ticker.fast_info["lastPrice"] = value
                module.Ticker = lambda symbol:ticker
                with self.assertRaises(adapter.YFinanceAdapterError) as caught:
                    adapter.YFinanceClient(module).request("snapshot",{"symbol":"NVDA"})
                self.assertEqual(caught.exception.kind,"malformed_response")
                self.assertFalse(caught.exception.retryable)

    def test_snapshot_checks_all_numeric_fields_not_just_last_price(self):
        for key in ("previousClose","open","dayHigh","dayLow","yearHigh","yearLow","marketCap","shares"):
            with self.subTest(key=key):
                module = FakeYFinance();ticker = FakeTicker("NVDA")
                ticker.fast_info[key] = "invalid"
                module.Ticker = lambda symbol:ticker
                with self.assertRaises(adapter.YFinanceAdapterError):
                    adapter.YFinanceClient(module).request("snapshot",{"symbol":"NVDA"})
        module = FakeYFinance();ticker = FakeTicker("NVDA")
        ticker.fast_info.update(lastPrice=adapter.Decimal("1.25"),shares=0,marketCap=123)
        module.Ticker = lambda symbol:ticker
        result = adapter.YFinanceClient(module).request("snapshot",{"symbol":"NVDA"})
        self.assertEqual(result.data["last_price"],adapter.Decimal("1.25"))
        self.assertEqual(result.data["shares"],0)

    def test_frame_preserves_positions_with_repeated_labels(self):
        frame = FakeFrame(["same","same"],["value","value"],[[1,2],[3,4]])
        result = adapter._frame(frame)
        self.assertEqual(result["index"],["same","same"])
        self.assertEqual(result["columns"],["value","value"])
        self.assertEqual(result["rows"],[[1,2],[3,4]])
        self.assertEqual(adapter._frame(frame,limit_columns=1)["rows"],[[1],[3]])

    def test_frame_rejects_row_count_and_width_mismatch(self):
        for rows in ([[1]], [[1],[2],[3]], [[1,2],[3,4]], [[],[]]):
            with self.subTest(rows=rows), self.assertRaises(adapter.YFinanceAdapterError) as caught:
                adapter._frame(FakeFrame(["a","b"],["value"],rows))
            self.assertEqual(caught.exception.kind,"malformed_response")
        with self.assertRaises(adapter.YFinanceAdapterError):
            adapter._frame(FakeFrame(["a"],["one","two"],[[1]]),limit_columns=1)

    def test_frame_retains_empty_axes_without_inventing_data(self):
        self.assertEqual(adapter._frame(FakeFrame(["a","b"],[],[[],[]]))["rows"],[[],[]])
        result = adapter._frame(FakeFrame([],["one"],[]))
        self.assertEqual(result["columns"],["one"])
        self.assertEqual(result["rows"],[])

    def test_missing_numeric_values_are_gaps_and_zero_is_preserved(self):
        for missing in (None,float("nan"),adapter.Decimal("NaN"),adapter.Decimal("Infinity")):
            module = FakeYFinance()
            ticker = FakeTicker("NVDA");ticker.fast_info = {"currency":"USD","lastPrice":missing}
            module.Ticker = lambda symbol: ticker
            with self.subTest(missing=str(missing)), self.assertRaises(adapter.YFinanceAdapterError):
                adapter.YFinanceClient(module,sleeper=lambda delay:None).request("snapshot",{"symbol":"NVDA"})
        module = FakeYFinance();ticker = FakeTicker("NVDA");ticker.fast_info = {"lastPrice":0}
        module.Ticker = lambda symbol:ticker
        self.assertEqual(adapter.YFinanceClient(module).request("snapshot",{"symbol":"NVDA"}).data["last_price"],0)
        ticker.get_income_stmt = lambda **kwargs:FakeFrame(["Revenue"],["2025"],[[None]])
        with self.assertRaises(adapter.YFinanceAdapterError):
            adapter.YFinanceClient(module,sleeper=lambda delay:None).request("financials.income",{"symbol":"NVDA","period":"annual"})

    def test_cli_empty_snapshot_does_not_create_capture(self):
        script = r"""
import sys, types
sys.path.insert(0,sys.argv[1])
import money_craft as mc
calls = []
def ticker(symbol):
    calls.append(symbol)
    return types.SimpleNamespace(fast_info={})
sys.modules['yfinance'] = types.SimpleNamespace(Ticker=ticker,__version__='fixture')
sys.argv = ['money_craft.py','data','snapshot','--provider','yfinance','--symbol','NVDA','--capture-dir',sys.argv[2],'--source-id','S01']
code = mc.main()
assert len(calls) == 3
raise SystemExit(code)
"""
        with tempfile.TemporaryDirectory() as directory:
            capture = Path(directory)/"capture"
            result = subprocess.run([sys.executable,"-c",script,str(SCRIPT_DIR),str(capture)],capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,mc.EXIT_TRANSIENT,result.stdout+result.stderr)
            self.assertEqual(json.loads(result.stdout)["error"]["kind"],"transient_provider_error")
            self.assertFalse(capture.exists())

    def test_search_rejects_malformed_rows_without_silent_filtering(self):
        for row in (None, {}, {"symbol":True}, {"symbol":" "}):
            with self.subTest(row=row):
                module = FakeYFinance()
                class Search:
                    def __init__(self, *args, **kwargs):
                        self.quotes = [{"symbol":"NVDA"},row]
                module.Search = Search
                with self.assertRaises(adapter.YFinanceAdapterError) as caught:
                    adapter.YFinanceClient(module).request("search",{"query":"NVDA"})
                self.assertEqual(caught.exception.kind,"malformed_response")
                self.assertFalse(caught.exception.retryable)

    def test_empty_required_data_is_provider_gap_but_empty_actions_are_valid(self):
        class EmptyTicker(FakeTicker):
            def __init__(self,symbol):
                super().__init__(symbol)
                self.fast_info = {}
            def history(self,**kwargs):return FakeFrame([],[],[])
            def get_valuation_measures(self,**kwargs):return FakeFrame([],[],[])
            def get_income_stmt(self,**kwargs):return FakeFrame([],[],[])
            def get_actions(self,**kwargs):return FakeFrame([],[],[])
        module = FakeYFinance();module.Ticker = EmptyTicker
        for operation in ("snapshot","history","valuations","financials.income"):
            sleeps = []
            with self.subTest(operation=operation), self.assertRaises(adapter.YFinanceAdapterError) as caught:
                adapter.YFinanceClient(module,sleeper=sleeps.append).request(operation,{"symbol":"NVDA","start":"2026-01-01","end":"2026-01-31","period":"annual"})
            self.assertEqual(caught.exception.kind,"transient_provider_error")
            self.assertEqual(sleeps,[0.5,1.0])
        result = adapter.YFinanceClient(module).request("corporate-actions",{"symbol":"NVDA"})
        self.assertEqual(result.data["table"]["rows"],[])

    def test_search_is_a_versioned_adapter_export_not_a_claimed_wire_response(self) -> None:
        module = FakeYFinance()
        result = adapter.YFinanceClient(module, version="1.7.0-test").request(
            "search", {"query": "NVDA", "limit": 5}
        )
        export = json.loads(result.adapter_export)
        self.assertEqual(export["schema"], "money-craft.yfinance-adapter-export.v1")
        self.assertEqual(export["provider"], "yfinance")
        self.assertEqual(result.data["item"][0]["symbol"], "NVDA")

    def test_empty_search_retries_with_a_bound_and_remains_a_provider_gap(self) -> None:
        calls: list[str] = []

        class EmptySearch:
            def __init__(self, query: str, **kwargs: object) -> None:
                calls.append(query)
                self.quotes: list[object] = []

        module = FakeYFinance()
        module.Search = EmptySearch
        sleeps: list[float] = []
        with self.assertRaises(adapter.YFinanceAdapterError) as caught:
            adapter.YFinanceClient(module, version="1.7.0-test", sleeper=sleeps.append).request(
                "search", {"query": "NVDA", "limit": 5}
            )
        self.assertEqual(caught.exception.kind, "transient_provider_error")
        self.assertEqual(calls, ["NVDA", "NVDA", "NVDA"])
        self.assertEqual(sleeps, [0.5, 1.0])

    def test_cache_lock_recovers_with_bounded_retry(self) -> None:
        import sqlite3
        from unittest.mock import patch

        client = adapter.YFinanceClient(FakeYFinance(), sleeper=lambda delay: None)
        payload = {"item": [{"symbol": "NVDA"}]}
        with patch.object(client, "_execute", side_effect=[sqlite3.OperationalError("database is locked"), payload]) as execute:
            result = client.request("search", {"query": "NVDA"})
        self.assertEqual(execute.call_count, 2)
        self.assertEqual(result.data, payload)

    def test_persistent_cache_lock_remains_a_transient_gap(self) -> None:
        import sqlite3
        from unittest.mock import patch

        sleeps = []
        client = adapter.YFinanceClient(FakeYFinance(), sleeper=sleeps.append)
        with patch.object(client, "_execute", side_effect=sqlite3.OperationalError("database table is locked")) as execute:
            with self.assertRaises(adapter.YFinanceAdapterError) as caught:
                client.request("search", {"query": "NVDA"})
        self.assertEqual(execute.call_count, 3)
        self.assertEqual(sleeps, [0.5, 1.0])
        self.assertEqual(caught.exception.kind, "transient_provider_error")
        self.assertTrue(caught.exception.retryable)

    def test_other_database_errors_are_not_retried(self) -> None:
        import sqlite3
        from unittest.mock import patch

        client = adapter.YFinanceClient(FakeYFinance(), sleeper=lambda delay: self.fail("unexpected retry"))
        with patch.object(client, "_execute", side_effect=sqlite3.OperationalError("database disk image is malformed")) as execute:
            with self.assertRaises(adapter.YFinanceAdapterError) as caught:
                client.request("search", {"query": "NVDA"})
        self.assertEqual(execute.call_count, 1)
        self.assertEqual(caught.exception.kind, "provider_error")
        self.assertFalse(caught.exception.retryable)

    def test_history_converts_inclusive_money_craft_end_to_yfinance_exclusive_end(self) -> None:
        module = FakeYFinance()
        result = adapter.YFinanceClient(module, version="1.7.0-test").request(
            "history",
            {
                "symbol": "NVDA",
                "start": "2026-08-01",
                "end": "2026-08-23",
                "interval": "1d",
                "adjust": "auto",
            },
        )
        self.assertEqual(module.tickers[0].history_calls[0]["end"], "2026-08-24")
        self.assertEqual(result.data["adjustment"], "auto-adjusted")
        self.assertEqual(result.data["table"]["columns"], ["Open", "Close", "Dividends"])

    def test_snapshot_maps_current_fast_info_camel_case_contract(self) -> None:
        module = FakeYFinance()
        result = adapter.YFinanceClient(module, version="1.7.0-test").request(
            "snapshot", {"symbol": "NVDA"}
        )
        self.assertEqual(result.data["last_price"], adapter.Decimal("123.45"))
        self.assertEqual(result.data["market_cap"], 3000000000)
        self.assertEqual(result.data["quote_type"], "EQUITY")

    def test_financials_are_bounded_to_requested_columns(self) -> None:
        module = FakeYFinance()
        result = adapter.YFinanceClient(module, version="1.7.0-test").request(
            "financials.income",
            {"symbol": "NVDA", "period": "annual", "limit": 1},
        )
        self.assertEqual(result.data["table"]["columns"], ["2025-01-26"])
        self.assertEqual(result.data["table"]["rows"], [[1000]])

    def test_data_cli_preparation_keeps_fuyao_compatible_and_adds_explicit_yfinance_symbol(self) -> None:
        parser = mc.build_parser()
        args = parser.parse_args(
            [
                "data",
                "history",
                "--provider",
                "yfinance",
                "--symbol",
                "0700.HK",
                "--start",
                "2026-01-01",
                "--end",
                "2026-08-23",
                "--adjust",
                "auto",
            ]
        )
        operation, path, parameters, output = mc.prepare_operation(args)
        self.assertEqual((operation, path), ("history", "yfinance://history"))
        self.assertEqual(parameters["symbol"], "0700.HK")
        self.assertEqual(output["end"], "2026-08-23")

    def test_research_run_command_and_identity_are_provider_bound(self) -> None:
        item = {
            "id": "S01",
            "provider": "yfinance",
            "operation": "search",
            "arguments": {"query": "NVDA", "limit": 5},
        }
        command = research_run.operation_command(Path("runtime.py"), item, Path("captures"))
        self.assertIn("yfinance", command)
        payload = {
            "schema": "money-craft.data-response.v1",
            "ok": True,
            "provider": "yfinance",
            "operation": "search",
            "data": {
                "item": [
                    {"symbol": "NVDA", "currency": "USD", "quoteType": "EQUITY"}
                ]
            },
        }
        case = {
            "identity": {
                "base_currency": "USD",
                "provider_identifiers": {"yfinance": "NVDA"},
            }
        }
        research_run.validate_identity(payload, case)

    def test_yfinance_capture_is_labeled_as_an_unauthenticated_adapter_export(self) -> None:
        module = FakeYFinance()
        adapter_result = adapter.YFinanceClient(module, version="1.7.0-test").request(
            "snapshot", {"symbol": "NVDA"}
        )
        result = mc.ProviderResult(
            operation="snapshot",
            path="yfinance://snapshot",
            parameters={"symbol": "NVDA"},
            payload={"request_id": None, "data": adapter_result.data},
            raw_response=adapter_result.adapter_export,
            fetched_at=adapter_result.fetched_at,
            provider="yfinance",
        )
        with tempfile.TemporaryDirectory() as directory:
            destination = mc.capture_result(
                Path(directory),
                "S02",
                result,
                output_parameters=result.parameters,
                authentication="none",
            )
            request = json.loads((destination / "request.json").read_text(encoding="utf-8"))
            capture = json.loads((destination / "capture.json").read_text(encoding="utf-8"))
        self.assertEqual(request["provider"], "yfinance")
        self.assertEqual(request["authentication"], "none")
        self.assertEqual(capture["provider"], "yfinance")


if __name__ == "__main__":
    unittest.main()
