#!/usr/bin/env python3
"""Optional yfinance adapter for bounded Hong Kong and U.S. market research data."""

from __future__ import annotations

import datetime as dt
import importlib
import importlib.metadata
import json
import math
import sys
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping


SNAPSHOT_NUMERIC_FIELDS = (
    "last_price", "previous_close", "open", "day_high", "day_low",
    "year_high", "year_low", "market_cap", "shares",
)


class YFinanceAdapterError(RuntimeError):
    def __init__(self, kind: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.kind = kind
        self.retryable = retryable


@dataclass(frozen=True)
class YFinanceResult:
    operation: str
    symbol: str | None
    parameters: dict[str, Any]
    data: dict[str, Any]
    adapter_export: bytes
    fetched_at: str
    version: str


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def installed_version() -> str | None:
    try:
        return importlib.metadata.version("yfinance")
    except importlib.metadata.PackageNotFoundError:
        return None


def _scalar(value: Any) -> Any:
    # yfinance loads pandas; keep the core importable without optional deps.
    pandas = sys.modules.get("pandas")
    if pandas is not None and (value is pandas.NA or value is pandas.NaT):
        return None
    if isinstance(value, Decimal):
        return value if value.is_finite() else None
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, (dt.datetime, dt.date)):
        return value.isoformat()
    if isinstance(value, float):
        return None if not math.isfinite(value) else Decimal(str(value))
    item = getattr(value, "item", None)
    if callable(item):
        try:
            converted = item()
        except (TypeError, ValueError):
            pass
        else:
            if converted is not value:
                return _scalar(converted)
    isoformat = getattr(value, "isoformat", None)
    if callable(isoformat):
        try:
            return isoformat()
        except (TypeError, ValueError):
            pass
    if isinstance(value, Mapping):
        return {str(key): _scalar(item_value) for key, item_value in value.items()}
    if isinstance(value, (list, tuple)):
        return [_scalar(item_value) for item_value in value]
    return str(value)


def _frame(frame: Any, *, limit_columns: int | None = None, text_columns: tuple[str, ...] = ()) -> dict[str, Any]:
    if frame is None:
        return {"orientation": "index-columns", "index": [], "columns": [], "rows": []}
    columns = list(getattr(frame, "columns", []))
    index = list(getattr(frame, "index", []))
    width = len(columns)
    rows: list[list[Any]] = []
    # Iterate original positions: label-based .loc can duplicate or substitute
    # rows/columns when labels repeat. Limit only after validating full width.
    for row in frame.itertuples(index=False, name=None):
        if len(row) != width:
            raise YFinanceAdapterError("malformed_response", "yfinance table row width does not match its columns")
        normalized = [_scalar(value) for value in row]
        for column, value in zip(columns, normalized):
            if value is None:
                continue
            if column in text_columns:
                valid = isinstance(value, str)
            else:
                valid = not isinstance(value, bool) and isinstance(value, (int, Decimal))
            if not valid:
                raise YFinanceAdapterError("malformed_response", "yfinance table cell has an invalid type for its column")
        rows.append(normalized if limit_columns is None else normalized[:limit_columns])
    # pandas emits no tuples for zero columns with index=False, even when
    # the index has entries. Represent those positions as empty rows.
    if width == 0 and not rows:
        rows = [[] for _ in index]
    if len(rows) != len(index):
        raise YFinanceAdapterError("malformed_response", "yfinance table row count does not match its index")
    if limit_columns is not None:
        columns = columns[:limit_columns]
    return {
        "orientation": "index-columns",
        "index": [_scalar(value) for value in index],
        "columns": [_scalar(value) for value in columns],
        "rows": rows,
    }


def _index_dates(frame: Any) -> list[str]:
    if frame is None:
        return []
    if not hasattr(frame, "index"):
        raise YFinanceAdapterError("malformed_response", "yfinance dated table has no index")
    dates = []
    for value in frame.index:
        label = _scalar(value)
        try:
            if not isinstance(label, str) or dt.date.fromisoformat(label[:10]).isoformat() != label[:10]:
                raise ValueError("invalid date")
            if len(label) != 10:
                if len(label) <= 10 or label[10] not in {"T", " "}:
                    raise ValueError("invalid timestamp")
                dt.datetime.fromisoformat(label)
        except (ValueError, TypeError) as exc:
            raise YFinanceAdapterError("malformed_response", "yfinance table index contains an invalid date") from exc
        # Daily market dates use the timestamp's own calendar date, not UTC.
        dates.append(label[:10])
    return dates


def _filter_frame_dates(frame: Any, start: str | None, end: str | None) -> Any:
    dates = _index_dates(frame)
    if frame is None or (start is None and end is None):
        return frame
    if not hasattr(frame, "loc"):
        raise YFinanceAdapterError("malformed_response", "yfinance dated table cannot be filtered")
    mask = [(start is None or date >= start) and (end is None or date <= end) for date in dates]
    return frame.loc[mask]


def _mapping_values(mapping: Any, keys: Mapping[str, str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for output_key, provider_key in keys.items():
        try:
            value = mapping.get(provider_key)
        except (AttributeError, KeyError, TypeError):
            try:
                value = mapping[provider_key]
            except (AttributeError, KeyError, TypeError):
                value = None
        result[output_key] = _scalar(value)
    return result


class YFinanceClient:
    def __init__(
        self,
        module: Any | None = None,
        *,
        version: str | None = None,
        sleeper: Any = time.sleep,
    ) -> None:
        if module is None:
            try:
                module = importlib.import_module("yfinance")
            except ImportError as exc:
                raise YFinanceAdapterError(
                    "missing_optional_dependency",
                    "install skills/money-craft/requirements-yfinance.txt in the active Python environment",
                ) from exc
        self._yf = module
        self._version = version or installed_version() or str(getattr(module, "__version__", "unknown"))
        self._sleeper = sleeper

    def request(self, operation: str, parameters: Mapping[str, Any]) -> YFinanceResult:
        normalized = {str(key): value for key, value in parameters.items() if value is not None}
        symbol = str(normalized["symbol"]).upper() if "symbol" in normalized else None
        data: dict[str, Any] | None = None
        for attempt in range(1, 4):
            try:
                data = self._execute(operation, symbol, normalized)
                if operation == "snapshot":
                    available = any(data.get(key) is not None for key in SNAPSHOT_NUMERIC_FIELDS)
                elif operation in {"history", "valuations"} or operation.startswith("financials."):
                    available = any(value is not None for row in data["table"]["rows"] for value in row)
                else:
                    available = True
                if not available:
                    raise YFinanceAdapterError(
                        "transient_provider_error", f"yfinance {operation} returned no usable data", retryable=True,
                    )
                break
            except Exception as exc:
                if isinstance(exc, YFinanceAdapterError):
                    error = exc
                else:
                    name = type(exc).__name__
                    retryable = name in {
                        "ConnectionError",
                        "ReadTimeout",
                        "ConnectTimeout",
                        "Timeout",
                        "TimeoutError",
                        "YFRateLimitError",
                    } or (
                        name == "OperationalError"
                        and str(exc).strip().lower() in {"database is locked", "database table is locked"}
                    )
                    error = YFinanceAdapterError(
                        "transient_provider_error" if retryable else "provider_error",
                        f"yfinance {operation} failed: {name}: {str(exc)[:300]}",
                        retryable=retryable,
                    )
                if not error.retryable or attempt == 3:
                    if error is exc:
                        raise error
                    raise error from exc
                self._sleeper(0.5 if attempt == 1 else 1.0)
        assert data is not None
        fetched_at = utc_now()
        export = {
            "schema": "money-craft.yfinance-adapter-export.v1",
            "provider": "yfinance",
            "yfinance_version": self._version,
            "operation": operation,
            "symbol": symbol,
            "parameters": _scalar(normalized),
            "fetched_at": fetched_at,
            "data": data,
        }
        try:
            raw = (json.dumps(export, ensure_ascii=False, indent=2, default=str, allow_nan=False) + "\n").encode("utf-8")
        except (UnicodeError, ValueError, TypeError, RecursionError) as exc:
            raise YFinanceAdapterError("malformed_response", "yfinance data cannot be exported as valid UTF-8 JSON") from exc
        return YFinanceResult(
            operation=operation,
            symbol=symbol,
            parameters=normalized,
            data=data,
            adapter_export=raw,
            fetched_at=fetched_at,
            version=self._version,
        )

    def _execute(self, operation: str, symbol: str | None, parameters: Mapping[str, Any]) -> dict[str, Any]:
        if operation == "search":
            search = self._yf.Search(
                str(parameters["query"]),
                max_results=int(parameters.get("limit", 10)),
                news_count=0,
                lists_count=0,
                include_research=False,
                raise_errors=True,
            )
            quotes = getattr(search, "quotes", None)
            if not isinstance(quotes, list):
                raise YFinanceAdapterError("malformed_response", "yfinance search quotes must be a list")
            if not quotes:
                raise YFinanceAdapterError(
                    "transient_provider_error",
                    "yfinance search returned no quotes",
                    retryable=True,
                )
            if any(not isinstance(item, dict) or not isinstance(item.get("symbol"), str)
                   or not item["symbol"].strip() for item in quotes):
                raise YFinanceAdapterError("malformed_response", "yfinance search row has an invalid symbol")
            keys = (
                "symbol",
                "shortname",
                "longname",
                "exchange",
                "exchDisp",
                "quoteType",
                "typeDisp",
                "currency",
            )
            return {"item": [{key: _scalar(item.get(key)) for key in keys} for item in quotes]}

        if symbol is None:
            raise YFinanceAdapterError("usage_error", "symbol is required")
        ticker = self._yf.Ticker(symbol)
        if operation == "snapshot":
            values = _mapping_values(
                ticker.fast_info,
                {
                    "currency": "currency",
                    "exchange": "exchange",
                    "timezone": "timezone",
                    "quote_type": "quoteType",
                    "last_price": "lastPrice",
                    "previous_close": "previousClose",
                    "open": "open",
                    "day_high": "dayHigh",
                    "day_low": "dayLow",
                    "year_high": "yearHigh",
                    "year_low": "yearLow",
                    "market_cap": "marketCap",
                    "shares": "shares",
                },
            )
            for key in SNAPSHOT_NUMERIC_FIELDS:
                value = values[key]
                if value is not None and (isinstance(value, bool) or not isinstance(value, (int, Decimal))):
                    raise YFinanceAdapterError("malformed_response", f"yfinance snapshot {key} must be numeric or missing")
            return {"symbol": symbol, **values}
        if operation == "history":
            end_inclusive = dt.date.fromisoformat(str(parameters["end"]))
            frame = ticker.history(
                start=str(parameters["start"]),
                end=(end_inclusive + dt.timedelta(days=1)).isoformat(),
                interval=str(parameters.get("interval", "1d")),
                auto_adjust=parameters.get("adjust") != "none",
                actions=True,
                repair=False,
            )
            dates = _index_dates(frame)
            if any(date < str(parameters["start"]) or date > str(parameters["end"]) for date in dates):
                raise YFinanceAdapterError("malformed_response", "yfinance history date is outside the requested range")
            return {
                "symbol": symbol,
                "adjustment": "auto-adjusted" if parameters.get("adjust") != "none" else "unadjusted",
                "end_semantics": "Money Craft inclusive end converted to yfinance exclusive end plus one day",
                "table": _frame(frame),
            }
        if operation == "valuations":
            frame = ticker.get_valuation_measures(freq="quarterly", periods=5)
            return {"symbol": symbol, "table": _frame(frame)}
        if operation.startswith("financials."):
            statement = operation.split(".", 1)[1]
            method = {
                "income": ticker.get_income_stmt,
                "balance": ticker.get_balance_sheet,
                "cash-flow": ticker.get_cash_flow,
            }.get(statement)
            if method is None:
                raise YFinanceAdapterError("usage_error", f"unsupported financial statement: {statement}")
            frame = method(freq="yearly" if parameters.get("period") == "annual" else "quarterly")
            limit = int(parameters["limit"]) if "limit" in parameters else None
            return {
                "symbol": symbol,
                "period": parameters.get("period"),
                "statement": statement,
                "table": _frame(frame, limit_columns=limit),
            }
        if operation == "corporate-actions":
            frame = _filter_frame_dates(
                ticker.get_actions(period="max"),
                str(parameters["start"]) if "start" in parameters else None,
                str(parameters["end"]) if "end" in parameters else None,
            )
            return {"symbol": symbol, "table": _frame(frame, text_columns=("Dividends FX",))}
        raise YFinanceAdapterError("usage_error", f"unsupported yfinance operation: {operation}")
