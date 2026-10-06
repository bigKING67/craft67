#!/usr/bin/env python3
"""Fuyao A-share HTTPS client: credentials, bounded transport, retries and response admission."""

from __future__ import annotations

import http.client
import json
import math
import os
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
from cli_common import (
    EXIT_CONFIG,
    EXIT_PROVIDER,
    EXIT_SCHEMA,
    EXIT_TRANSIENT,
    VERSION,
    MoneyCraftError,
    ProviderResult,
    sanitize_message,
    utc_now,
)

BASE_URL = "https://fuyao.aicubes.cn"
API_KEY_ENV = "FUYAO_API_KEY"
MAX_API_KEY_BYTES = 4096
MAX_RESPONSE_BYTES = 10 * 1024 * 1024
REQUEST_TIMEOUT_SECONDS = 30
MAX_ATTEMPTS = 3
RETRY_DELAYS = (0.5, 1.0)
TRANSIENT_BUSINESS_CODES = {4001, 5002, 5003}
AUTH_CODES = {2001, 2003}


@dataclass(frozen=True)
class FuyaoCredential:
    api_key: str
    source: str
    capture_label: str


class _BoundedRedirectBody:
    """Constrain urllib's redirect drain while retaining its redirect policy."""

    def __init__(self, stream: Any) -> None:
        self.stream = stream

    def __getattr__(self, name: str) -> Any:
        return getattr(self.stream, name)

    def close(self) -> None:
        try:
            self.stream.close()
        except OSError as exc:
            raise MoneyCraftError("local_io_error", "redirect response cleanup failed", exit_code=EXIT_PROVIDER) from exc

    def read(self, size: int = -1) -> bytes:
        if getattr(self.stream, "closed", False):
            return b""
        data = self.stream.read(MAX_RESPONSE_BYTES + 1 if size < 0 else min(size, MAX_RESPONSE_BYTES + 1))
        if len(data) > MAX_RESPONSE_BYTES:
            raise MoneyCraftError("response_too_large", "provider redirect response exceeds byte limit", exit_code=EXIT_SCHEMA)
        if size < 0:
            length = getattr(self.stream, "headers", {}).get("Content-Length")
            if length is not None:
                try:
                    expected = int(length)
                except ValueError as exc:
                    raise MoneyCraftError("malformed_response", "provider redirect Content-Length is invalid", exit_code=EXIT_SCHEMA) from exc
                if expected < 0 or len(data) > expected:
                    raise MoneyCraftError("malformed_response", "provider redirect length contradicts Content-Length", exit_code=EXIT_SCHEMA)
                if len(data) < expected:
                    raise http.client.IncompleteRead(data, expected - len(data))
        return data


class SameHostRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Do not forward the API key to a different redirect host."""

    def http_error_302(self, req: Any, fp: Any, code: int, msg: str, headers: Any) -> Any:
        try:
            return super().http_error_302(req, _BoundedRedirectBody(fp), code, msg, headers)
        finally:
            active_error = sys.exc_info()[1]
            try:
                fp.close()
            except OSError as exc:
                if isinstance(active_error, urllib.error.HTTPError):
                    active_error.msg = f"{active_error.reason} (response cleanup failed)"
                elif isinstance(active_error, MoneyCraftError):
                    active_error.args = (f"{active_error} (response cleanup failed)",)
                elif active_error is None:
                    raise MoneyCraftError("local_io_error", "redirect response cleanup failed", exit_code=EXIT_PROVIDER) from exc
                # An existing transport exception retains its classification;
                # cleanup details must never replace it.

    http_error_301 = http_error_303 = http_error_307 = http_error_308 = http_error_302

    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> Any:
        original = urllib.parse.urlsplit(req.full_url)
        target = urllib.parse.urlsplit(newurl)
        if (original.scheme not in ("https", "http") or target.scheme != original.scheme
                or original.netloc.lower() != target.netloc.lower()
                or target.username is not None or target.password is not None):
            raise urllib.error.HTTPError(newurl, code, "cross-host redirect rejected", headers, fp)
        if code == 308 and sys.version_info < (3, 11):
            code = 307  # Python 3.10 urllib predates 308; 3.11+ treats 307/308 identically.
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fuyao_api_key_path(
    home: Path | None = None,
    environment: Mapping[str, str] | None = None,
) -> Path:
    try:
        return runtime_paths.config_file("fuyao-api-key", environment, home=home)
    except runtime_paths.RuntimePathError as exc:
        raise MoneyCraftError(
            "invalid_configuration",
            sanitize_message(exc),
            exit_code=EXIT_CONFIG,
        ) from exc


def validate_fuyao_key(value: str) -> str:
    if any(ord(character) < 32 or 127 <= ord(character) <= 159 or ord(character) > 255 for character in value):
        raise MoneyCraftError("invalid_configuration", "Fuyao API key is not a valid HTTP header value", exit_code=EXIT_CONFIG)
    return value


def load_fuyao_credential(
    environment: Mapping[str, str] | None = None,
    *,
    home: Path | None = None,
) -> FuyaoCredential:
    environ = os.environ if environment is None else environment
    environment_value = environ.get(API_KEY_ENV, "").strip()
    if environment_value:
        return FuyaoCredential(
            api_key=validate_fuyao_key(environment_value),
            source="environment",
            capture_label=f"environment:{API_KEY_ENV}",
        )

    path = fuyao_api_key_path(home, environ)
    path_display = runtime_paths.display_path(path, home=home)
    try:
        value = runtime_paths.read_private_text(path, subject=path_display, max_bytes=MAX_API_KEY_BYTES).strip()
    except runtime_paths.PrivateFileError as exc:
        message = f"configure {API_KEY_ENV} or {path_display}" if exc.kind == "missing_configuration" else str(exc)
        raise MoneyCraftError(exc.kind, message, exit_code=EXIT_CONFIG) from exc
    if not value or "\n" in value or "\r" in value:
        raise MoneyCraftError(
            "invalid_configuration",
            f"{path_display} must contain exactly one non-empty line",
            exit_code=EXIT_CONFIG,
        )
    return FuyaoCredential(
        api_key=validate_fuyao_key(value),
        source="secure-file",
        capture_label=f"secure-file:{path_display}",
    )


def parse_json(raw: bytes) -> dict[str, Any]:
    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON object key")
            result[key] = value
        return result

    try:
        text = raw.decode("utf-8")
        payload = json.loads(
            text,
            parse_float=Decimal,
            object_pairs_hook=unique_object,
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"invalid constant: {value}")),
        )
        # Escaped lone surrogates are accepted by json.loads but cannot be
        # written to our UTF-8 capture or stdout contracts.
        def validate_strings(value: Any) -> None:
            if isinstance(value, str):
                value.encode("utf-8")
            elif isinstance(value, dict):
                for key, item in value.items():
                    validate_strings(key)
                    validate_strings(item)
            elif isinstance(value, list):
                for item in value:
                    validate_strings(item)
        validate_strings(payload)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, InvalidOperation, RecursionError) as exc:
        raise MoneyCraftError(
            "malformed_response",
            "provider response is not valid UTF-8 JSON",
            exit_code=EXIT_SCHEMA,
        ) from exc
    if not isinstance(payload, dict):
        raise MoneyCraftError(
            "malformed_response",
            "provider response must be a JSON object",
            exit_code=EXIT_SCHEMA,
        )
    if type(payload.get("code")) is not int:
        raise MoneyCraftError(
            "malformed_response",
            "provider response is missing integer code",
            exit_code=EXIT_SCHEMA,
        )
    if "message" not in payload or "request_id" not in payload or "data" not in payload:
        raise MoneyCraftError(
            "malformed_response",
            "provider response does not match the ApiResponse envelope",
            exit_code=EXIT_SCHEMA,
        )
    if not isinstance(payload["message"], str) or not isinstance(payload["request_id"], str):
        raise MoneyCraftError(
            "malformed_response",
            "provider message and request_id must be strings",
            exit_code=EXIT_SCHEMA,
        )
    if payload["code"] == 0 and payload["data"] is None:
        raise MoneyCraftError(
            "malformed_response",
            "successful provider response must contain a data object",
            exit_code=EXIT_SCHEMA,
        )
    if payload["data"] is not None and not isinstance(payload["data"], dict):
        raise MoneyCraftError(
            "malformed_response",
            "provider data must be an object or null",
            exit_code=EXIT_SCHEMA,
        )
    return payload


def bounded_retry_after(headers: Mapping[str, str] | None) -> float | None:
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


class FuyaoClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = BASE_URL,
        opener: Any | None = None,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        if not api_key.strip():
            raise MoneyCraftError(
                "missing_configuration",
                f"{API_KEY_ENV} is not configured",
                exit_code=EXIT_CONFIG,
            )
        self._api_key = validate_fuyao_key(api_key.strip())
        self._base_url = base_url.rstrip("/")
        self._opener = opener or urllib.request.build_opener(SameHostRedirectHandler())
        self._sleeper = sleeper

    def request(self, operation: str, path: str, parameters: Mapping[str, Any]) -> ProviderResult:
        last_error: MoneyCraftError | None = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                return self._request_once(operation, path, parameters)
            except MoneyCraftError as exc:
                last_error = exc
                if not exc.retryable:
                    raise
                if attempt >= MAX_ATTEMPTS:
                    raise MoneyCraftError(
                        exc.kind,
                        str(exc),
                        code=exc.code,
                        retryable=True,
                        exit_code=EXIT_TRANSIENT,
                        request_id=exc.request_id,
                    ) from exc
                delay = (
                    exc.retry_after
                    if exc.retry_after is not None
                    else RETRY_DELAYS[min(attempt - 1, len(RETRY_DELAYS) - 1)]
                )
                self._sleeper(delay)
        assert last_error is not None
        raise last_error

    def _request_once(self, operation: str, path: str, parameters: Mapping[str, Any]) -> ProviderResult:
        query = urllib.parse.urlencode(
            [(key, str(value)) for key, value in parameters.items() if value is not None],
            safe=",",
        )
        url = f"{self._base_url}{path}"
        if query:
            url += f"?{query}"
        request = urllib.request.Request(
            url,
            method="GET",
            headers={
                "Accept": "application/json",
                "User-Agent": f"money-craft/{VERSION}",
                "X-api-key": self._api_key,
            },
        )
        try:
            with self._opener.open(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                content_length = response.headers.get("Content-Length")
                declared_length = None
                if content_length is not None:
                    try:
                        declared_length = int(content_length)
                    except ValueError as exc:
                        raise MoneyCraftError(
                            "malformed_response",
                            "provider Content-Length is invalid",
                            exit_code=EXIT_SCHEMA,
                        ) from exc
                    if declared_length < 0 or declared_length > MAX_RESPONSE_BYTES:
                        raise MoneyCraftError(
                            "response_too_large",
                            f"provider response exceeds {MAX_RESPONSE_BYTES} bytes",
                            exit_code=EXIT_SCHEMA,
                        )
                raw = response.read(MAX_RESPONSE_BYTES + 1)
                if len(raw) > MAX_RESPONSE_BYTES:
                    raise MoneyCraftError(
                        "response_too_large",
                        f"provider response exceeds {MAX_RESPONSE_BYTES} bytes",
                        exit_code=EXIT_SCHEMA,
                    )
                if declared_length is not None and len(raw) != declared_length:
                    if len(raw) < declared_length:
                        raise http.client.IncompleteRead(raw, declared_length - len(raw))
                    raise MoneyCraftError("malformed_response", "provider length contradicts Content-Length", exit_code=EXIT_SCHEMA)
        except urllib.error.HTTPError as exc:
            close_failed = False
            try:
                exc.close()
            except OSError:
                close_failed = True
            retryable = exc.code == 429 or 500 <= exc.code <= 599
            message = sanitize_message(exc.reason, (self._api_key,))
            if close_failed:
                message += " (response cleanup failed)"
            raise MoneyCraftError(
                "http_error",
                f"provider HTTP {exc.code}: {message}",
                code=exc.code,
                retryable=retryable,
                exit_code=EXIT_TRANSIENT if retryable else EXIT_PROVIDER,
                retry_after=bounded_retry_after(exc.headers),
            ) from exc
        except (urllib.error.URLError, TimeoutError, socket.timeout, OSError, http.client.IncompleteRead) as exc:
            raise MoneyCraftError(
                "network_error",
                sanitize_message(exc, (self._api_key,)),
                retryable=True,
                exit_code=EXIT_TRANSIENT,
            ) from exc
        payload = parse_json(raw)
        code = payload["code"]
        request_id = payload.get("request_id") if isinstance(payload.get("request_id"), str) else None
        if code != 0:
            retryable = code in TRANSIENT_BUSINESS_CODES
            if code in AUTH_CODES:
                kind = "authentication_error"
            elif 1000 <= code < 2000:
                kind = "validation_error"
            elif 3000 <= code < 4000:
                kind = "data_error"
            elif retryable:
                kind = "transient_provider_error"
            else:
                kind = "provider_error"
            raise MoneyCraftError(
                kind,
                sanitize_message(payload.get("message", "provider business error"), (self._api_key,)),
                code=code,
                retryable=retryable,
                exit_code=EXIT_TRANSIENT if retryable else EXIT_PROVIDER,
                request_id=request_id,
            )
        return ProviderResult(
            operation=operation,
            path=path,
            parameters={key: value for key, value in parameters.items() if value is not None},
            payload=payload,
            raw_response=raw,
            fetched_at=utc_now(),
        )
