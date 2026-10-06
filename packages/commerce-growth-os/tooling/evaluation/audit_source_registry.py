#!/usr/bin/env python3
"""Audit official-source reachability without inferring current capabilities."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import socket
import ssl
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener

sys.dont_write_bytecode = True

from check_source_registry import (
    DEFAULT_REGISTRY,
    URL_RE,
    domain_allowed,
    redact_url_userinfo,
    validate_registry,
)
from evidence_metadata import build_evidence_metadata
from live_runtime import write_private_text


USER_AGENT = "commerce-growth-os-source-reachability/2.2"
HARD_HTTP_STATUSES = {404, 410}


def validate_audit_url(url: str) -> None:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    if parsed.username is not None or parsed.password is not None:
        raise ValueError(f"audit URL must not contain userinfo: {redact_url_userinfo(url)}")
    if parsed.scheme != "https" or not hostname or not domain_allowed(hostname):
        raise ValueError(
            f"audit URL is outside the official-source allowlist: {redact_url_userinfo(url)}"
        )


class AllowlistedRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        validate_audit_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def classify_status(status: int | None, error_kind: str | None, final_url: str | None) -> str:
    if error_kind in {"disallowed_url", "disallowed_redirect"}:
        return "hard_failure"
    if final_url:
        hostname = (urlparse(final_url).hostname or "").lower()
        if not hostname or not domain_allowed(hostname):
            return "hard_failure"
    if status is not None:
        if 200 <= status < 400:
            return "reachable"
        if status in {401, 403}:
            return "protected"
        if status == 429:
            return "rate_limited"
        if status in HARD_HTTP_STATUSES:
            return "hard_failure"
        if status >= 500:
            return "transient_failure"
        return "unexpected_status"
    if error_kind in {"timeout", "dns", "tls", "network"}:
        return "transient_failure"
    return "hard_failure"


def request_url(url: str, timeout: float) -> dict[str, Any]:
    started = time.monotonic()
    status = None
    final_url = None
    error = None
    error_kind = None
    methods = ("HEAD", "GET")

    try:
        validate_audit_url(url)
    except ValueError as exc:
        return {
            "url": redact_url_userinfo(url),
            "status": None,
            "classification": "hard_failure",
            "final_url": None,
            "duration_seconds": round(time.monotonic() - started, 3),
            "error_kind": "disallowed_url",
            "error": str(exc)[:300],
        }

    opener = build_opener(
        HTTPSHandler(context=ssl.create_default_context()),
        AllowlistedRedirectHandler(),
    )

    for method in methods:
        # A HEAD rejection may be retried as GET.  Do not let its status or
        # final URL affect the classification of that distinct request.
        status = None
        final_url = None
        error = None
        error_kind = None
        request = Request(url, method=method, headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*"})
        try:
            with opener.open(request, timeout=timeout) as response:
                status = response.status
                final_url = response.geturl()
                break
        except HTTPError as exc:
            status = exc.code
            final_url = exc.geturl()
            if method == "HEAD" and status in {403, 405}:
                continue
            break
        except socket.timeout as exc:
            error_kind = "timeout"
            error = str(exc)
            break
        except ssl.SSLError as exc:
            error_kind = "tls"
            error = str(exc)
            break
        except URLError as exc:
            reason = exc.reason
            error = str(reason)
            if isinstance(reason, socket.gaierror):
                error_kind = "dns"
            elif isinstance(reason, socket.timeout):
                error_kind = "timeout"
            else:
                error_kind = "network"
            break
        except OSError as exc:
            error_kind = "network"
            error = str(exc)
            break
        except ValueError as exc:
            error_kind = "disallowed_redirect"
            error = str(exc)
            break

    classification = classify_status(status, error_kind, final_url)
    return {
        "url": url,
        "status": status,
        "classification": classification,
        "final_url": final_url,
        "duration_seconds": round(time.monotonic() - started, 3),
        "error_kind": error_kind,
        "error": error[:300] if error else None,
    }


def audit(registry: Path, timeout: float, workers: int) -> dict[str, Any]:
    registry_contract = validate_registry(registry)
    if not registry_contract["passed"]:
        raise ValueError(f"source registry failed validation: {registry_contract['findings']}")
    text = registry.read_text(encoding="utf-8")
    urls = sorted(set(URL_RE.findall(text)))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(lambda url: request_url(url, timeout), urls))
    counts: dict[str, int] = {}
    for result in results:
        classification = result["classification"]
        counts[classification] = counts.get(classification, 0) + 1
    return {
        "metadata": build_evidence_metadata(
            "official-source-reachability",
            {"manifest": Path(__file__).resolve().parents[2] / "skill-pack.json", "registry": registry},
            include_codex=False,
        ),
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "content_freshness_verified": False,
        "capability_currentness_verified": False,
        "registry": str(registry),
        "urls": len(results),
        "counts": counts,
        "results": results,
    }


def self_test() -> None:
    cases = [
        (200, None, "https://www.oceanengine.com/", "reachable"),
        (302, None, "https://www.xingtu.cn/help-center", "reachable"),
        (403, None, "https://mms.pinduoduo.com/", "protected"),
        (429, None, "https://ad.xiaohongshu.com/", "rate_limited"),
        (404, None, "https://jzt.jd.com/missing", "hard_failure"),
        (503, None, "https://www.alimama.com/", "transient_failure"),
        (None, "timeout", None, "transient_failure"),
        (200, None, "https://example.com/redirect", "hard_failure"),
        (403, "disallowed_redirect", "https://www.oceanengine.com/", "hard_failure"),
    ]
    for status, error_kind, final_url, expected in cases:
        actual = classify_status(status, error_kind, final_url)
        if actual != expected:
            raise AssertionError(f"expected {expected}, got {actual}")
    validate_audit_url("https://school.oceanengine.com/product_help")
    try:
        validate_audit_url("https://user:secret@www.oceanengine.com/private")
    except ValueError as exc:
        if "secret" in str(exc):
            raise AssertionError("credential-bearing URL errors must be redacted") from exc
    else:
        raise AssertionError("credential-bearing URL must fail before a request")
    try:
        validate_audit_url("https://example.com/private")
    except ValueError:
        pass
    else:
        raise AssertionError("disallowed initial URL must fail before a request")
    handler = AllowlistedRedirectHandler()
    request = Request("https://www.oceanengine.com/")
    try:
        handler.redirect_request(
            request,
            None,
            302,
            "Found",
            {},
            "https://example.com/redirect",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("redirect to a disallowed domain must fail before following")
    opener = build_opener(AllowlistedRedirectHandler())
    redirect_handlers = [item for item in opener.handlers if isinstance(item, HTTPRedirectHandler)]
    if len(redirect_handlers) != 1 or not isinstance(redirect_handlers[0], AllowlistedRedirectHandler):
        raise AssertionError("the allowlisted redirect handler must replace urllib's default redirect handler")
    disallowed = request_url("https://example.com/private", 0.01)
    if disallowed["classification"] != "hard_failure" or disallowed["error_kind"] != "disallowed_url":
        raise AssertionError("disallowed initial URL must hard-fail without network access")
    credentialed = request_url("https://user:secret@www.oceanengine.com/private", 0.01)
    if credentialed["error_kind"] != "disallowed_url" or "secret" in json.dumps(credentialed):
        raise AssertionError("credential-bearing URL must hard-fail without leaking userinfo")

    class FakeResponse:
        status = 200

        def __init__(self, final_url: str) -> None:
            self._final_url = final_url

        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, exc_type, exc, traceback) -> None:  # type: ignore[no-untyped-def]
            return None

        def geturl(self) -> str:
            return self._final_url

    class FakeOpener:
        def __init__(self, outcomes: list[object]) -> None:
            self._outcomes = iter(outcomes)
            self.methods: list[str] = []

        def open(self, request: Request, timeout: float) -> FakeResponse:
            self.methods.append(request.get_method())
            outcome = next(self._outcomes)
            if isinstance(outcome, BaseException):
                raise outcome
            return outcome  # type: ignore[return-value]

    def assert_retry(
        outcomes: list[object],
        expected_classification: str,
        expected_kind: str | None,
        expected_status: int | None,
    ) -> None:
        opener = FakeOpener(outcomes)
        original_build_opener = globals()["build_opener"]
        globals()["build_opener"] = lambda *args: opener
        try:
            result = request_url("https://www.oceanengine.com/retry", 0.01)
        finally:
            globals()["build_opener"] = original_build_opener
        if opener.methods != ["HEAD", "GET"]:
            raise AssertionError(f"HEAD fallback should issue HEAD then GET, got {opener.methods}")
        if (
            result["classification"] != expected_classification
            or result["error_kind"] != expected_kind
            or result["status"] != expected_status
        ):
            raise AssertionError(f"HEAD fallback misclassified result: {result}")

    assert_retry(
        [
            HTTPError("https://www.oceanengine.com/retry", 403, "Forbidden", {}, None),
            FakeResponse("https://www.oceanengine.com/retry"),
        ],
        "reachable",
        None,
        200,
    )
    assert_retry(
        [
            HTTPError("https://www.oceanengine.com/retry", 405, "Method Not Allowed", {}, None),
            socket.timeout("timed out"),
        ],
        "transient_failure",
        "timeout",
        None,
    )
    assert_retry(
        [
            HTTPError("https://www.oceanengine.com/retry", 403, "Forbidden", {}, None),
            ValueError("audit URL is outside the official-source allowlist: https://example.com/redirect"),
        ],
        "hard_failure",
        "disallowed_redirect",
        None,
    )
    with tempfile.TemporaryDirectory(prefix="source-audit-self-test-") as temp:
        invalid_registry = Path(temp) / "registry.md"
        invalid_registry.write_text("https://example.com/private\n", encoding="utf-8")
        try:
            audit(invalid_registry, 0.01, 1)
        except ValueError:
            pass
        else:
            raise AssertionError("standalone audit must validate the registry before scheduling requests")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry", nargs="?", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--output")
    parser.add_argument("--fail-on", choices=["hard", "any", "never"], default="hard")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    try:
        if args.self_test:
            self_test()
            print("official source reachability audit self-test passed.")
            return 0
        if args.workers < 1 or args.workers > 8:
            raise ValueError("--workers must be between 1 and 8")
        report = audit(Path(args.registry).resolve(), args.timeout, args.workers)
        if args.output:
            output = Path(args.output).expanduser()
            write_private_text(
                output,
                json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            )
            print(f"official source reachability artifact: {output}")
        summary = {"urls": report["urls"], "counts": report["counts"]}
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))

        counts = report["counts"]
        if args.fail_on == "hard" and counts.get("hard_failure", 0):
            return 1
        if args.fail_on == "any" and any(
            counts.get(name, 0)
            for name in ("hard_failure", "transient_failure", "unexpected_status")
        ):
            return 1
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"audit_source_registry error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
