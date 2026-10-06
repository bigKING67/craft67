#!/usr/bin/env python3
"""Bounded FRED/ALFRED API adapter with protected local credentials."""

from __future__ import annotations

import datetime as dt
import json
import http.client
import math
import os
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable, Mapping

import runtime_paths

BASE_URL = "https://api.stlouisfed.org/fred"
API_KEY_ENV = "FRED_API_KEY"
MAX_API_KEY_BYTES = 4096
MAX_RESPONSE_BYTES = 10 * 1024 * 1024
REQUEST_TIMEOUT_SECONDS = 30
MAX_ATTEMPTS = 3
RETRY_DELAYS = (0.5, 1.0)


class FredAdapterError(RuntimeError):
    def __init__(
        self,
        kind: str,
        message: str,
        *,
        code: int | str | None = None,
        retryable: bool = False,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message)
        self.kind = kind
        self.code = code
        self.retryable = retryable
        self.retry_after = retry_after


@dataclass(frozen=True)
class FredCredential:
    api_key: str
    source: str
    capture_label: str


@dataclass(frozen=True)
class FredResult:
    operation: str
    path: str
    parameters: dict[str, Any]
    data: dict[str, Any]
    raw_response: bytes
    fetched_at: str


class _BoundedRedirectBody:
    """Constrain urllib's redirect drain while retaining its redirect policy."""

    def __init__(self, stream: Any) -> None:
        self.stream = stream

    def __getattr__(self, name: str) -> Any:
        return getattr(self.stream, name)

    def read(self, size: int = -1) -> bytes:
        if getattr(self.stream, "closed", False):
            return b""
        data = self.stream.read(MAX_RESPONSE_BYTES + 1 if size < 0 else min(size, MAX_RESPONSE_BYTES + 1))
        if len(data) > MAX_RESPONSE_BYTES:
            raise FredAdapterError("response_too_large", "FRED redirect response exceeds byte limit")
        if size < 0:
            length = getattr(self.stream, "headers", {}).get("Content-Length")
            if length is not None:
                try:
                    expected = int(length)
                except ValueError as exc:
                    raise FredAdapterError("malformed_response", "FRED redirect Content-Length is invalid") from exc
                if expected < 0 or len(data) > expected:
                    raise FredAdapterError("malformed_response", "FRED redirect length contradicts Content-Length")
                if len(data) < expected:
                    raise http.client.IncompleteRead(data, expected - len(data))
        return data


class SameHostRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Reject redirects that could disclose the query-string API key."""

    def http_error_302(self, req: Any, fp: Any, code: int, msg: str, headers: Any) -> Any:
        try:
            return super().http_error_302(req, _BoundedRedirectBody(fp), code, msg, headers)
        finally:
            fp.close()

    http_error_301 = http_error_303 = http_error_307 = http_error_308 = http_error_302

    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> Any:
        original = urllib.parse.urlsplit(req.full_url)
        target = urllib.parse.urlsplit(newurl)
        if (original.scheme != "https" or target.scheme != "https"
                or original.netloc.lower() != target.netloc.lower()
                or target.username is not None or target.password is not None):
            raise urllib.error.HTTPError(newurl, code, "unsafe FRED redirect rejected", headers, fp)
        if code == 308 and sys.version_info < (3, 11):
            code = 307  # Python 3.10 urllib predates 308; 3.11+ treats 307/308 identically.
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def api_key_path(
    home: Path | None = None,
    environment: Mapping[str, str] | None = None,
) -> Path:
    try:
        return runtime_paths.config_file("fred-api-key", environment, home=home)
    except runtime_paths.RuntimePathError as exc:
        raise FredAdapterError("invalid_configuration", str(exc)) from exc


def _sanitize(message: Any, secrets: tuple[str, ...] = ()) -> str:
    cleaned = str(message).replace("\r", " ").replace("\n", " ")
    for secret in secrets:
        if secret:
            cleaned = cleaned.replace(secret, "[REDACTED]")
    return cleaned[:500]


def _validate_key(value: str) -> str:
    normalized = value.strip()
    if len(normalized) != 32 or not normalized.isascii() or not normalized.isalnum() or normalized != normalized.lower():
        raise FredAdapterError(
            "invalid_configuration",
            "FRED API key must be a 32-character lowercase alphanumeric string",
        )
    return normalized


def load_credential(
    environment: Mapping[str, str] | None = None,
    *,
    home: Path | None = None,
) -> FredCredential:
    environ = os.environ if environment is None else environment
    environment_value = environ.get(API_KEY_ENV, "").strip()
    if environment_value:
        return FredCredential(
            api_key=_validate_key(environment_value),
            source="environment",
            capture_label=f"environment:{API_KEY_ENV}",
        )

    path = api_key_path(home, environ)
    path_display = runtime_paths.display_path(path, home=home)
    try:
        value = runtime_paths.read_private_text(path, subject=path_display, max_bytes=MAX_API_KEY_BYTES)
    except runtime_paths.PrivateFileError as exc:
        message = f"configure {API_KEY_ENV} or {path_display}" if exc.kind == "missing_configuration" else str(exc)
        raise FredAdapterError(exc.kind, message) from exc
    if "\n" in value.rstrip("\n") or "\r" in value:
        raise FredAdapterError(
            "invalid_configuration",
            f"{path_display} must contain exactly one non-empty line",
        )
    return FredCredential(
        api_key=_validate_key(value),
        source="secure-file",
        capture_label=f"secure-file:{path_display}",
    )


def _bounded_retry_after(headers: Mapping[str, str] | None) -> float | None:
    if headers is None:
        return None
    value = headers.get("Retry-After")
    if value is None:
        return None
    try:
        seconds = float(value)
    except ValueError:
        return None
    if not math.isfinite(seconds):
        return None
    return max(0.0, min(seconds, 10.0))


def _parse_json(raw: bytes, *, secret: str) -> dict[str, Any]:
    try:
        payload = json.loads(
            raw.decode("utf-8"),
            parse_float=Decimal,
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"invalid constant: {value}")),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, InvalidOperation, RecursionError) as exc:
        raise FredAdapterError(
            "malformed_response",
            f"FRED response is not valid UTF-8 JSON: {_sanitize(exc, (secret,))}",
        ) from exc
    if not isinstance(payload, dict):
        raise FredAdapterError("malformed_response", "FRED response must be a JSON object")
    return payload


def _canonical_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return dt.date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def pagination_warning(operation: str, payload: dict[str, Any]) -> str | None:
    """Describe completeness of an already validated provider page."""
    if operation not in {"search", "observations", "vintages"}:
        return None
    if "count" not in payload:
        return "FRED pagination completeness is unverified: response metadata is missing."
    field = {"search":"seriess", "observations":"observations", "vintages":"vintage_dates"}[operation]
    if payload["offset"] != 0 or len(payload[field]) < payload["count"]:
        return "FRED response is a partial page; do not treat it as the complete requested dataset."
    return None


def _validate_payload(operation: str, payload: dict[str, Any], parameters: dict[str, Any]) -> None:
    expected = {
        "search": "seriess",
        "series": "seriess",
        "observations": "observations",
        "vintages": "vintage_dates",
    }[operation]
    if not isinstance(payload.get(expected), list):
        raise FredAdapterError(
            "malformed_response",
            f"FRED {operation} response is missing the {expected} array",
        )

    rows = payload[expected]
    if operation in {"search", "observations", "vintages"} and "limit" in parameters and len(rows) > parameters["limit"]:
        raise FredAdapterError("malformed_response", "FRED page exceeds the requested limit")
    if operation in {"search", "observations", "vintages"} and any(key in payload for key in ("count", "offset", "limit")):
        for key in ("count", "offset", "limit"):
            value = payload.get(key)
            if type(value) is not int or value < (1 if key == "limit" else 0):
                raise FredAdapterError("malformed_response", "FRED pagination metadata is invalid")
        if payload["offset"] != parameters.get("offset", 0) or ("limit" in parameters and payload["limit"] != parameters["limit"]):
            raise FredAdapterError("malformed_response", "FRED pagination does not match the request")
        if len(rows) != min(payload["limit"], max(0, payload["count"] - payload["offset"])):
            raise FredAdapterError("malformed_response", "FRED page length contradicts pagination metadata")
    if operation in {"series", "search"}:
        if any(not isinstance(row, dict) or not isinstance(row.get("id"), str)
               or not row["id"].strip() for row in rows):
            raise FredAdapterError("malformed_response", "FRED series row has an invalid identity")
        if operation == "series" and (len(rows) != 1 or rows[0]["id"] != parameters.get("series_id")):
            raise FredAdapterError("malformed_response", "FRED series response does not match the requested identity")
    if operation == "vintages":
        if any(not _canonical_date(date) for date in rows):
            raise FredAdapterError("malformed_response", "FRED vintage dates contain an invalid date")
        start, end = parameters.get("realtime_start"), parameters.get("realtime_end")
        for key in ("realtime_start", "realtime_end"):
            if key in parameters and payload.get(key) != parameters[key]:
                raise FredAdapterError("malformed_response", "FRED vintage response does not match the requested range")
        if any((start is not None and date < start) or (end is not None and date > end) for date in rows):
            raise FredAdapterError("malformed_response", "FRED vintage date is outside the requested range")

    # The CLI's as-known-on contract requests a single closed real-time day.
    # A row's validity interval may span that day; do not require equal endpoints.
    as_of = parameters.get("realtime_start")
    if operation in {"series", "observations"} and as_of is not None and as_of == parameters.get("realtime_end"):
        if not _canonical_date(as_of) or any(payload.get(key) != as_of for key in ("realtime_start", "realtime_end")):
            raise FredAdapterError("malformed_response", "FRED response does not match the requested as-of date")
        for row in rows:
            start = row.get("realtime_start") if isinstance(row, dict) else None
            end = row.get("realtime_end") if isinstance(row, dict) else None
            if not (_canonical_date(start) and _canonical_date(end) and start <= as_of <= end):
                raise FredAdapterError("malformed_response", "FRED row is not valid on the requested as-of date")

    if operation == "observations":
        if "units" in parameters and payload.get("units") != parameters["units"]:
            raise FredAdapterError("malformed_response", "FRED units do not match the requested transformation")
        # CLI uses the default real-time-period format. Other formats carry
        # different value fields and must not be silently treated as this one.
        output_type = payload.get("output_type", 1)
        if type(output_type) is not int or output_type != 1:
            raise FredAdapterError("malformed_response", "unsupported FRED observation output type")
        for index, row in enumerate(payload[expected]):
            valid = isinstance(row, dict)
            date = row.get("date") if valid else None
            value = row.get("value") if valid else None
            valid = valid and _canonical_date(date)
            if valid:
                start, end = parameters.get("observation_start"), parameters.get("observation_end")
                if (start is not None and date < start) or (end is not None and date > end):
                    raise FredAdapterError("malformed_response", "FRED observation is outside the requested date range")
            if value != ".":
                numeric = isinstance(value, str) and re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?", value)
                try:
                    valid = bool(valid and numeric and Decimal(value).is_finite())
                except InvalidOperation:
                    valid = False
            if not valid:
                raise FredAdapterError("malformed_response", f"FRED observation row {index} has an invalid date or value")


class FredClient:
    ENDPOINTS = {
        "search": "/series/search",
        "series": "/series",
        "observations": "/series/observations",
        "vintages": "/series/vintagedates",
    }

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = BASE_URL,
        user_agent: str = "money-craft",
        opener: Any | None = None,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self._api_key = _validate_key(api_key)
        try:
            endpoint = urllib.parse.urlsplit(base_url)
            valid_url = (endpoint.scheme == "https" and bool(endpoint.hostname)
                         and endpoint.username is None and endpoint.password is None
                         and not endpoint.query and not endpoint.fragment)
            endpoint.port  # Validate malformed or out-of-range port syntax.
        except ValueError:
            valid_url = False
        if not valid_url:
            raise FredAdapterError("invalid_configuration", "FRED base URL must be HTTPS with a host and no user info, query or fragment")
        self._base_url = base_url.rstrip("/")
        self._user_agent = user_agent
        self._opener = opener or urllib.request.build_opener(SameHostRedirectHandler())
        self._sleeper = sleeper

    def request(self, operation: str, parameters: Mapping[str, Any]) -> FredResult:
        if operation not in self.ENDPOINTS:
            raise FredAdapterError("usage_error", f"unsupported FRED operation: {operation}")
        normalized = {str(key): value for key, value in parameters.items() if value is not None}
        last_error: FredAdapterError | None = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                return self._request_once(operation, normalized)
            except FredAdapterError as exc:
                last_error = exc
                if not exc.retryable or attempt >= MAX_ATTEMPTS:
                    raise
                delay = (
                    exc.retry_after
                    if exc.retry_after is not None
                    else RETRY_DELAYS[min(attempt - 1, len(RETRY_DELAYS) - 1)]
                )
                self._sleeper(delay)
        assert last_error is not None
        raise last_error

    def _request_once(self, operation: str, parameters: dict[str, Any]) -> FredResult:
        path = self.ENDPOINTS[operation]
        wire_parameters = {**parameters, "file_type": "json", "api_key": self._api_key}
        query = urllib.parse.urlencode(
            [(key, str(value)) for key, value in wire_parameters.items()],
            safe=",",
        )
        request = urllib.request.Request(
            f"{self._base_url}{path}?{query}",
            method="GET",
            headers={"Accept": "application/json", "User-Agent": self._user_agent},
        )
        try:
            with self._opener.open(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                declared_length = None
                content_length = response.headers.get("Content-Length")
                if content_length:
                    try:
                        declared_length = int(content_length)
                    except ValueError as exc:
                        raise FredAdapterError(
                            "malformed_response",
                            "FRED Content-Length is invalid",
                        ) from exc
                    if declared_length < 0 or declared_length > MAX_RESPONSE_BYTES:
                        raise FredAdapterError(
                            "response_too_large",
                            f"FRED response exceeds {MAX_RESPONSE_BYTES} bytes",
                        )
                raw = response.read(MAX_RESPONSE_BYTES + 1)
                if len(raw) > MAX_RESPONSE_BYTES:
                    raise FredAdapterError(
                        "response_too_large",
                        f"FRED response exceeds {MAX_RESPONSE_BYTES} bytes",
                    )
                if declared_length is not None:
                    if len(raw) < declared_length:
                        raise http.client.IncompleteRead(raw, declared_length - len(raw))
                    if len(raw) > declared_length:
                        raise FredAdapterError("malformed_response", "FRED response length contradicts Content-Length")
        except urllib.error.HTTPError as exc:
            retryable = exc.code == 429 or 500 <= exc.code <= 599
            # HTTP status remains authoritative when its optional error body
            # cannot be read. Always release the response before retrying.
            diagnostic = ""
            try:
                body = exc.read(4096)
            except (OSError, http.client.HTTPException):
                body = b""
                diagnostic += "error body unavailable; "
            finally:
                try:
                    exc.close()
                except (OSError, http.client.HTTPException):
                    diagnostic += "error response cleanup failed; "
            message = _sanitize(exc.reason, (self._api_key,))
            if body:
                try:
                    error_payload = json.loads(body.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
                    error_payload = None
                if isinstance(error_payload, dict) and isinstance(error_payload.get("error_message"), str):
                    message = _sanitize(error_payload["error_message"], (self._api_key,))
            raise FredAdapterError(
                "http_error",
                f"FRED HTTP {exc.code}: {diagnostic}{message}",
                code=exc.code,
                retryable=retryable,
                retry_after=_bounded_retry_after(exc.headers),
            ) from exc
        except (urllib.error.URLError, TimeoutError, socket.timeout, OSError, http.client.HTTPException) as exc:
            raise FredAdapterError(
                "network_error",
                _sanitize(exc, (self._api_key,)),
                retryable=True,
            ) from exc
        payload = _parse_json(raw, secret=self._api_key)
        if "error_code" in payload or "error_message" in payload:
            if type(payload.get("error_code")) is not int or not 400 <= payload["error_code"] <= 599:
                raise FredAdapterError("malformed_response", "FRED response has an invalid error envelope")
            code = int(payload["error_code"])
            raise FredAdapterError(
                "provider_error",
                _sanitize(payload.get("error_message", "FRED provider error"), (self._api_key,)),
                code=code,
                retryable=code == 429 or 500 <= code <= 599,
            )
        _validate_payload(operation, payload, parameters)
        return FredResult(
            operation=operation,
            path=f"/fred{path}",
            parameters=parameters,
            data=payload,
            raw_response=raw,
            fetched_at=utc_now(),
        )
