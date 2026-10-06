#!/usr/bin/env python3
"""Shared CLI error type, exit codes and JSON output helpers for Money Craft."""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

VERSION = (Path(__file__).resolve().parent.parent / "VERSION").read_text(encoding="utf-8").strip()

EXIT_USAGE = 2
EXIT_CONFIG = 3
EXIT_PROVIDER = 4
EXIT_TRANSIENT = 5
EXIT_SCHEMA = 6


class MoneyCraftError(RuntimeError):
    def __init__(
        self,
        kind: str,
        message: str,
        *,
        code: int | str | None = None,
        retryable: bool = False,
        exit_code: int = EXIT_PROVIDER,
        request_id: str | None = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message)
        self.kind = kind
        self.code = code
        self.retryable = retryable
        self.exit_code = exit_code
        self.request_id = request_id
        self.retry_after = retry_after


@dataclass(frozen=True)
class ProviderResult:
    operation: str
    path: str
    parameters: dict[str, Any]
    payload: dict[str, Any]
    raw_response: bytes
    fetched_at: str
    provider: str = "fuyao"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [jsonable(item) for item in value]
    return value


def print_json(payload: Any) -> None:
    print(json.dumps(jsonable(payload), ensure_ascii=False, indent=2, sort_keys=False))


def sanitize_message(message: Any, secrets: tuple[str, ...] = ()) -> str:
    cleaned = str(message)
    for secret in secrets:
        if secret:
            cleaned = cleaned.replace(secret, "[REDACTED]")
    return cleaned.replace("\r", " ").replace("\n", " ")[:500]
