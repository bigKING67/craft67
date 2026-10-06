from __future__ import annotations

import io
import http.client
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "money-craft" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import fred_adapter as fred  # noqa: E402
import money_craft as mc  # noqa: E402


TEST_KEY = "a" * 32


class FakeResponse:
    def __init__(self, payload: bytes, headers: dict[str, str] | None = None) -> None:
        self.payload = payload
        self.headers = headers or {}

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self, limit: int) -> bytes:
        return self.payload[:limit]


class FakeOpener:
    def __init__(self, outcomes: list[object]) -> None:
        self.outcomes = outcomes
        self.requests: list[object] = []

    def open(self, request: object, timeout: int) -> FakeResponse:
        self.requests.append(request)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        assert isinstance(outcome, FakeResponse)
        return outcome


class FredCredentialTests(unittest.TestCase):
    def test_credential_rejects_changes_after_path_inspection(self):
        for change in ("replace", "symlink", "permissions", "growth"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                home = Path(directory)
                path = fred.api_key_path(home, {})
                path.parent.mkdir(parents=True)
                path.write_text(TEST_KEY); path.chmod(0o600)
                other = path.parent/"other-key"
                other.write_text("b"*32); other.chmod(0o600)
                original = Path.lstat
                def inspect(target, *args, **kwargs):
                    info = original(target, *args, **kwargs)
                    if target == path:
                        if change == "replace":
                            os.replace(other, path)
                        elif change == "symlink":
                            path.unlink(); path.symlink_to(other)
                        elif change == "growth":
                            path.write_text(TEST_KEY + " " * fred.MAX_API_KEY_BYTES)
                        else:
                            path.chmod(0o644)
                    return info
                with mock.patch.object(Path, "lstat", inspect):
                    with self.assertRaises(fred.FredAdapterError) as caught:
                        fred.load_credential({}, home=home)
                self.assertEqual(caught.exception.kind, "invalid_configuration")
                self.assertNotIn(TEST_KEY, str(caught.exception))
                self.assertNotIn("b"*32, str(caught.exception))

    def test_credential_inspection_error_is_structured(self):
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(Path, "lstat", side_effect=PermissionError("fixture denied")):
                with self.assertRaises(fred.FredAdapterError) as caught:
                    fred.load_credential({}, home=Path(directory))
            self.assertEqual(caught.exception.kind, "invalid_configuration")

    def test_secure_file_and_environment_precedence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            path = fred.api_key_path(home, {})
            path.parent.mkdir(parents=True)
            path.write_text(TEST_KEY + "\n", encoding="utf-8")
            path.chmod(0o600)
            credential = fred.load_credential({}, home=home)
            self.assertEqual(credential.api_key, TEST_KEY)
            self.assertEqual(credential.source, "secure-file")
            overridden = fred.load_credential({"FRED_API_KEY": "b" * 32}, home=home)
            self.assertEqual(overridden.api_key, "b" * 32)
            self.assertEqual(overridden.source, "environment")

    def test_secure_file_rejects_permissive_mode_symlink_and_bad_format(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            path = fred.api_key_path(home, {})
            path.parent.mkdir(parents=True)
            path.write_text(TEST_KEY + "\n", encoding="utf-8")
            path.chmod(0o644)
            with self.assertRaises(fred.FredAdapterError):
                fred.load_credential({}, home=home)
            path.unlink()
            target = path.parent / "target"
            target.write_text(TEST_KEY + "\n", encoding="utf-8")
            target.chmod(0o600)
            path.symlink_to(target)
            with self.assertRaises(fred.FredAdapterError):
                fred.load_credential({}, home=home)
            path.unlink()
            path.write_text("INVALID\n", encoding="utf-8")
            path.chmod(0o600)
            with self.assertRaises(fred.FredAdapterError) as caught:
                fred.load_credential({}, home=home)
            self.assertEqual(caught.exception.kind, "invalid_configuration")


    def test_redirect_drain_failure_closes_stream(self):
        class Body(io.BytesIO):
            def read(self, size=-1):
                self.last_size = size
                raise http.client.IncompleteRead(b"partial")
        handler = fred.SameHostRedirectHandler()
        request = fred.urllib.request.Request("https://fixture.invalid/start")
        request.timeout = 1
        for code in (301,302,303,307,308):
            request = fred.urllib.request.Request("https://fixture.invalid/start")
            request.timeout = 1
            body = Body()
            with self.subTest(code=code), self.assertRaises(http.client.IncompleteRead):
                getattr(handler,f"http_error_{code}")(request,body,code,"redirect",{"location":"/next"})
            self.assertTrue(body.closed)
            self.assertEqual(body.last_size,fred.MAX_RESPONSE_BYTES+1)

class FredClientTests(unittest.TestCase):
    def test_json_decimal_overflow_is_structured(self):
        raw = b'{"seriess":[],"extra":1e99999999999999999999}'
        opener = FakeOpener([FakeResponse(raw)])
        with self.assertRaises(fred.FredAdapterError) as caught:
            fred.FredClient(TEST_KEY,opener=opener).request("search",{})
        self.assertEqual(caught.exception.kind,"malformed_response")
        self.assertEqual(len(opener.requests),1)

    def test_vintages_bind_explicit_bounds_and_include_endpoints(self):
        for params, dates in (({"realtime_start":"2026-01-01"}, ["2026-01-01","2026-12-31"]),
                              ({"realtime_end":"2026-01-31"}, ["2025-01-01","2026-01-31"]),
                              ({"realtime_start":"2026-01-01","realtime_end":"2026-01-31"}, ["2026-01-31","2026-01-01"])):
            for rows in (dates, []):
                payload = {**params,"vintage_dates":rows}
                raw = json.dumps(payload).encode()
                result = fred.FredClient(TEST_KEY, opener=FakeOpener([FakeResponse(raw)])).request("vintages", {"series_id":"FIXTURE",**params})
                self.assertEqual(result.raw_response,raw)
            for key in params:
                for value in (None, "2026-02-01"):
                    payload = {**params,"vintage_dates":[],key:value}
                    with self.subTest(key=key,value=value), self.assertRaises(fred.FredAdapterError):
                        fred.FredClient(TEST_KEY, opener=FakeOpener([FakeResponse(json.dumps(payload).encode())])).request("vintages",params)
        params = {"realtime_start":"2026-01-01","realtime_end":"2026-01-31"}
        for date in ("2025-12-31","2026-02-01"):
            opener = FakeOpener([FakeResponse(json.dumps({**params,"vintage_dates":[date]}).encode())])
            with self.assertRaises(fred.FredAdapterError) as caught:
                fred.FredClient(TEST_KEY, opener=opener).request("vintages",params)
            self.assertEqual(caught.exception.kind,"malformed_response")
            self.assertEqual(len(opener.requests),1)

    def test_deep_json_is_structured_for_success_and_http_error(self):
        deep = b'['*1500+b'0'+b']'*1500
        for status in (200, 400):
            with self.subTest(status=status):
                body = io.BytesIO(deep)
                outcome = FakeResponse(deep) if status == 200 else urllib.error.HTTPError("https://fixture.invalid", status, "bad request", {}, body)
                opener = FakeOpener([outcome])
                with self.assertRaises(fred.FredAdapterError) as caught:
                    fred.FredClient(TEST_KEY, opener=opener).request("search", {})
                self.assertEqual(caught.exception.kind, "malformed_response" if status == 200 else "http_error")
                self.assertEqual(len(opener.requests), 1)
                if status == 400:
                    self.assertTrue(body.closed)

    def test_declared_response_length_must_match_received_bytes(self):
        raw = b'{"seriess":[]}'
        for difference in (-1, 1):
            with self.subTest(difference=difference):
                opener = FakeOpener([FakeResponse(raw, {"Content-Length":str(len(raw)+difference)}) for _ in range(3)])
                sleeps = []
                with self.assertRaises(fred.FredAdapterError) as caught:
                    fred.FredClient(TEST_KEY, opener=opener, sleeper=sleeps.append).request("search", {})
                self.assertEqual(caught.exception.kind, "network_error" if difference > 0 else "malformed_response")
                self.assertEqual(len(opener.requests), 3 if difference > 0 else 1)
        result = fred.FredClient(TEST_KEY, opener=FakeOpener([FakeResponse(raw,{"Content-Length":str(len(raw))})])).request("search", {})
        self.assertEqual(result.raw_response,raw)

    def test_truncated_standard_library_http_response_is_not_success(self):
        raw = b'{"seriess":[]}'
        responses = []
        class Socket:
            def makefile(self, *args):
                return io.BytesIO(b'HTTP/1.1 200 OK\r\nContent-Length: 100\r\n\r\n'+raw)
        class Opener:
            def open(self, request, timeout):
                response = http.client.HTTPResponse(Socket())
                response.begin()
                responses.append(response)
                return response
        with self.assertRaises(fred.FredAdapterError) as caught:
            fred.FredClient(TEST_KEY, opener=Opener(), sleeper=lambda delay: None).request("search", {})
        self.assertEqual(caught.exception.kind, "network_error")
        self.assertEqual(len(responses), 3)
        self.assertTrue(all(response.closed for response in responses))

    def test_observations_bind_requested_range_and_units(self):
        params = {"series_id":"FIXTURE", "observation_start":"2026-01-01", "observation_end":"2026-01-31", "units":"pch"}
        good = {"units":"pch", "observations":[{"date":"2026-01-01","value":"1"},{"date":"2026-01-31","value":"2"}]}
        for date, units in (("2025-12-31","pch"), ("2026-02-01","pch"), ("2026-01-01","lin"), ("2026-01-01",None)):
            with self.subTest(date=date, units=units):
                payload = {"units":units,"observations":[{"date":date,"value":"1"}]}
                with self.assertRaises(fred.FredAdapterError):
                    fred.FredClient(TEST_KEY, opener=FakeOpener([FakeResponse(json.dumps(payload).encode())])).request("observations",params)
        result = fred.FredClient(TEST_KEY, opener=FakeOpener([FakeResponse(json.dumps(good).encode())])).request("observations",params)
        self.assertEqual(result.data,good)

    def test_pagination_metadata_and_partial_warning(self):
        good = {"count":3,"offset":0,"limit":1,"seriess":[{"id":"FIXTURE"}]}
        for patch in ({"count":True},{"count":-1},{"offset":1},{"limit":0},{"count":0},{"limit":2}):
            with self.subTest(patch=patch):
                payload = {**good,**patch}
                with self.assertRaises(fred.FredAdapterError):
                    fred.FredClient(TEST_KEY, opener=FakeOpener([FakeResponse(json.dumps(payload).encode())])).request("search",{"limit":1})
        with self.assertRaises(fred.FredAdapterError):
            fred.FredClient(TEST_KEY, opener=FakeOpener([FakeResponse(b'{"count":0,"seriess":[]}')])).request("search",{})
        self.assertIn("partial",fred.pagination_warning("search",good))
        self.assertIn("unverified",fred.pagination_warning("search",{"seriess":[]}))
        self.assertIsNone(fred.pagination_warning("search",{**good,"count":1}))
        self.assertIsNone(fred.pagination_warning("series",{"seriess":[{"id":"FIXTURE"}]}))

    def test_http_errors_close_body_and_preserve_status_on_read_failure(self):
        class BrokenBody(io.BytesIO):
            def read(self, limit):
                raise http.client.IncompleteRead(b"partial")
        for code in (400, 429, 503):
            with self.subTest(code=code):
                body = BrokenBody()
                error = urllib.error.HTTPError("https://fixture.invalid", code, "failed "+TEST_KEY, {}, body)
                opener = FakeOpener([error, FakeResponse(b'{"seriess":[]}')])
                sleeps = []
                client = fred.FredClient(TEST_KEY, opener=opener, sleeper=sleeps.append)
                if code == 400:
                    with self.assertRaises(fred.FredAdapterError) as caught:
                        client.request("search", {})
                    self.assertEqual(caught.exception.kind, "http_error")
                    self.assertEqual(caught.exception.code, 400)
                    self.assertNotIn(TEST_KEY, str(caught.exception))
                    self.assertEqual(sleeps, [])
                else:
                    self.assertEqual(client.request("search", {}).data, {"seriess":[]})
                    self.assertEqual(sleeps, [0.5])
                self.assertTrue(body.closed)

    def test_http_error_body_closed_after_successful_read(self):
        body = io.BytesIO(b'{"error_message":"bad request"}')
        error = urllib.error.HTTPError("https://fixture.invalid", 400, "failed", {}, body)
        with self.assertRaises(fred.FredAdapterError):
            fred.FredClient(TEST_KEY, opener=FakeOpener([error])).request("search", {})
        self.assertTrue(body.closed)

    def test_incomplete_response_retries_and_closes_each_attempt(self):
        class BrokenResponse(FakeResponse):
            closed = False
            def read(self, limit):
                raise http.client.IncompleteRead(b"partial "+TEST_KEY.encode())
            def __exit__(self, *args):
                self.closed = True
        responses = [BrokenResponse(b"") for _ in range(3)]
        opener = FakeOpener(responses.copy())
        sleeps = []
        with self.assertRaises(fred.FredAdapterError) as caught:
            fred.FredClient(TEST_KEY, opener=opener, sleeper=sleeps.append).request("search", {})
        self.assertEqual(caught.exception.kind, "network_error")
        self.assertTrue(all(item.closed for item in responses))
        self.assertEqual(len(opener.requests), 3)
        self.assertEqual(sleeps, [0.5, 1.0])
        self.assertNotIn(TEST_KEY, str(caught.exception))

    def test_http_cleanup_failure_remains_observable_and_structured(self):
        error = urllib.error.HTTPError("https://fixture.invalid", 400, "failed", {}, io.BytesIO())
        original_close = error.close
        def failing_close():
            original_close()
            raise OSError("fixture close failure "+TEST_KEY)
        error.close = failing_close
        with self.assertRaises(fred.FredAdapterError) as caught:
            fred.FredClient(TEST_KEY, opener=FakeOpener([error])).request("search", {})
        self.assertEqual(caught.exception.kind, "http_error")
        self.assertIn("cleanup failed", str(caught.exception))
        self.assertNotIn(TEST_KEY, str(caught.exception))
        error.close = original_close

    def test_network_timeouts_and_http_retries_are_bounded(self):
        for kind in ("timeout", "http"):
            with self.subTest(kind=kind):
                bodies = [io.BytesIO(b"unavailable") for _ in range(3)]
                outcomes = ([TimeoutError("timeout "+TEST_KEY) for _ in range(3)] if kind == "timeout" else
                            [urllib.error.HTTPError("https://fixture.invalid", 503, "unavailable", {}, body) for body in bodies])
                opener = FakeOpener(outcomes)
                sleeps = []
                with self.assertRaises(fred.FredAdapterError) as caught:
                    fred.FredClient(TEST_KEY, opener=opener, sleeper=sleeps.append).request("search", {})
                self.assertEqual(len(opener.requests), 3)
                self.assertEqual(sleeps, [0.5, 1.0])
                self.assertEqual(caught.exception.kind, "network_error" if kind == "timeout" else "http_error")
                self.assertNotIn(TEST_KEY, str(caught.exception))
                if kind == "http":
                    self.assertTrue(all(body.closed for body in bodies))

    def test_retry_after_nonfinite_or_invalid_uses_default_backoff(self):
        for value in ("NaN", "Infinity", "-Infinity", "garbage"):
            with self.subTest(value=value):
                self.assertIsNone(fred._bounded_retry_after({"Retry-After":value}))
        self.assertEqual(fred._bounded_retry_after({"Retry-After":"-1"}), 0.0)
        self.assertEqual(fred._bounded_retry_after({"Retry-After":"2.5"}), 2.5)

    def test_series_identity_and_search_rows(self):
        for operation, rows in (("series", []), ("series", [{"id":"OTHER"}]),
                                ("series", [{"id":"FIXTURE"}]*2), ("search", [None]),
                                ("search", [{"id":True}]), ("search", [{"id":" "}])):
            with self.subTest(operation=operation, rows=rows):
                opener = FakeOpener([FakeResponse(json.dumps({"seriess":rows}).encode())])
                with self.assertRaises(fred.FredAdapterError) as caught:
                    fred.FredClient(TEST_KEY, opener=opener).request(operation, {"series_id":"FIXTURE"})
                self.assertEqual(caught.exception.kind, "malformed_response")
                self.assertEqual(len(opener.requests), 1)
        for operation, rows in (("series", [{"id":"FIXTURE"}]), ("search", []), ("search", [{"id":"MiXeD.ID-1"}])):
            raw = json.dumps({"seriess":rows}).encode()
            result = fred.FredClient(TEST_KEY, opener=FakeOpener([FakeResponse(raw)])).request(operation, {"series_id":"FIXTURE"})
            self.assertEqual(result.raw_response, raw)

    def test_vintage_dates_are_canonical_dates(self):
        for value in (None, True, {}, "2026-02-30", "20260901", "2026-9-01"):
            with self.subTest(value=value):
                raw = json.dumps({"vintage_dates":[value]}).encode()
                with self.assertRaises(fred.FredAdapterError) as caught:
                    fred.FredClient(TEST_KEY, opener=FakeOpener([FakeResponse(raw)])).request("vintages", {"series_id":"FIXTURE"})
                self.assertEqual(caught.exception.kind, "malformed_response")
        for dates in ([], ["2026-09-01", "2026-08-01"]):
            raw = json.dumps({"vintage_dates":dates}).encode()
            result = fred.FredClient(TEST_KEY, opener=FakeOpener([FakeResponse(raw)])).request("vintages", {"series_id":"FIXTURE"})
            self.assertEqual(result.raw_response, raw)

    def test_as_of_response_binding(self):
        day = "2026-08-31"
        for operation, field, row in (("observations", "observations", {"date":"2026-07-01","value":"1"}),
                                      ("series", "seriess", {"id":"FIXTURE"})):
            good = {"realtime_start":day, "realtime_end":day,
                    field:[{**row, "realtime_start":"2026-08-01", "realtime_end":"9999-12-31"}]}
            bad = []
            for key in ("realtime_start", "realtime_end"):
                missing = json.loads(json.dumps(good)); missing.pop(key); bad.append(missing)
                wrong = json.loads(json.dumps(good)); wrong[key] = "2026-09-01"; bad.append(wrong)
                missing_row = json.loads(json.dumps(good)); missing_row[field][0].pop(key); bad.append(missing_row)
            for start, end in (("2026-09-01","9999-12-31"), ("2026-01-01","2026-08-30"), ("20260801",day)):
                wrong = json.loads(json.dumps(good)); wrong[field][0].update(realtime_start=start,realtime_end=end); bad.append(wrong)
            params = {"series_id":"FIXTURE", "realtime_start":day, "realtime_end":day}
            for payload in bad:
                with self.subTest(operation=operation, payload=payload):
                    opener = FakeOpener([FakeResponse(json.dumps(payload).encode())])
                    with self.assertRaises(fred.FredAdapterError) as caught:
                        fred.FredClient(TEST_KEY, opener=opener).request(operation, params)
                    self.assertEqual(caught.exception.kind, "malformed_response")
                    self.assertEqual(len(opener.requests), 1)
            result = fred.FredClient(TEST_KEY, opener=FakeOpener([FakeResponse(json.dumps(good).encode())])).request(operation, params)
            self.assertEqual(result.data, good)

    def test_redirects_require_same_host_and_https(self):
        handler = fred.SameHostRedirectHandler()
        request = fred.urllib.request.Request("https://fixture.invalid/fred/series?api_key="+TEST_KEY)
        for target in ("http://fixture.invalid/next", "https://other.invalid/next", "https://fixture.invalid:444/next", "https://user@fixture.invalid/next"):
            with self.subTest(target=target):
                with self.assertRaises(urllib.error.HTTPError) as caught:
                    handler.redirect_request(request, None, 302, "Found", {}, target)
                caught.exception.close()
        redirected = handler.redirect_request(request, None, 302, "Found", {}, "https://fixture.invalid/next")
        self.assertEqual(redirected.full_url, "https://fixture.invalid/next")

    def test_client_rejects_unsafe_base_url_before_network(self):
        for url in ("http://fixture.invalid", "https:///fred", "https://user@fixture.invalid", "https://fixture.invalid?query=1", "https://fixture.invalid/#fragment"):
            with self.subTest(url=url):
                opener = FakeOpener([])
                with self.assertRaises(fred.FredAdapterError) as caught:
                    fred.FredClient(TEST_KEY, base_url=url, opener=opener)
                self.assertEqual(caught.exception.kind, "invalid_configuration")
                self.assertEqual(opener.requests, [])

    def test_error_redaction_precedes_truncation(self):
        for offset in (0, 480, 490, 499, 500):
            with self.subTest(offset=offset):
                message = fred._sanitize("x"*offset+TEST_KEY+" tail", (TEST_KEY,))
                self.assertNotIn(TEST_KEY[:12], message)
                self.assertLessEqual(len(message), 500)
        raw = json.dumps({"error_code":400,"error_message":"x"*490+TEST_KEY}).encode()
        with self.assertRaises(fred.FredAdapterError) as caught:
            fred.FredClient(TEST_KEY, opener=FakeOpener([FakeResponse(raw)])).request("series", {"series_id":"FIXTURE"})
        self.assertNotIn(TEST_KEY[:8], str(caught.exception))

    def test_observation_rows_reject_invalid_dates_and_values(self):
        bad_rows = [None, {}, {"date":"2026-02-30","value":"1"}, {"date":"20260101","value":"1"}, {"date":"2026-01-01","value":"NaN"}, {"date":"2026-01-01","value":"Infinity"}, {"date":"2026-01-01","value":True}, {"date":"2026-01-01","value":""}, {"date":"2026-01-01","value":"1_000"}]
        for row in bad_rows:
            with self.subTest(row=row):
                opener = FakeOpener([FakeResponse(json.dumps({"observations":[row]}).encode())])
                with self.assertRaises(fred.FredAdapterError) as caught:
                    fred.FredClient(TEST_KEY, opener=opener).request("observations", {"series_id":"FIXTURE"})
                self.assertEqual(caught.exception.kind, "malformed_response")
                self.assertEqual(len(opener.requests), 1)
        raw = b'{"observations":[{"date":"2026-01-01","value":"."},{"date":"2026-02-01","value":"-0.125"}]}'
        result = fred.FredClient(TEST_KEY, opener=FakeOpener([FakeResponse(raw)])).request("observations", {"series_id":"FIXTURE"})
        self.assertEqual(result.raw_response, raw)
        self.assertEqual(result.data["observations"][0]["value"], ".")

    def test_malformed_error_envelope_never_becomes_success(self):
        for fields in ({"error_code":"400"}, {"error_code":True}, {"error_code":None}, {"error_message":"failure"}):
            with self.subTest(fields=fields):
                raw = json.dumps({"observations":[], **fields}).encode()
                with self.assertRaises(fred.FredAdapterError):
                    fred.FredClient(TEST_KEY, opener=FakeOpener([FakeResponse(raw)])).request("observations", {"series_id":"FIXTURE"})

    def test_observations_preserve_wire_payload_without_persisting_key(self) -> None:
        raw = json.dumps(
            {
                "realtime_start": "2026-08-31",
                "realtime_end": "2026-08-31",
                "count": 1,
                "offset": 0,
                "limit": 100000,
                "observations": [
                    {
                        "realtime_start": "2026-08-31",
                        "realtime_end": "2026-08-31",
                        "date": "2026-07-01",
                        "value": "2.7",
                    }
                ],
            }
        ).encode("utf-8")
        opener = FakeOpener([FakeResponse(raw)])
        result = fred.FredClient(TEST_KEY, base_url="https://fixture.invalid", opener=opener).request(
            "observations",
            {
                "series_id": "PCEPI",
                "realtime_start": "2026-08-31",
                "realtime_end": "2026-08-31",
            },
        )
        request = opener.requests[0]
        self.assertIn("api_key=" + TEST_KEY, request.full_url)
        self.assertNotIn("api_key", result.parameters)
        self.assertNotIn(TEST_KEY.encode(), result.raw_response)
        self.assertEqual(result.data["observations"][0]["value"], "2.7")

    def test_http_rate_limit_retries_and_bounds_retry_after(self) -> None:
        error = urllib.error.HTTPError(
            "https://fixture.invalid/series/search",
            429,
            "rate limited",
            {"Retry-After": "99"},
            io.BytesIO(b'{"error_code":429,"error_message":"rate limited"}'),
        )
        success = FakeResponse(b'{"seriess":[]}')
        opener = FakeOpener([error, success])
        sleeps: list[float] = []
        result = fred.FredClient(
            TEST_KEY,
            base_url="https://fixture.invalid",
            opener=opener,
            sleeper=sleeps.append,
        ).request("search", {"search_text": "inflation", "limit": 5})
        self.assertEqual(result.data["seriess"], [])
        self.assertEqual(sleeps, [10.0])

    def test_error_message_redacts_reflected_key(self) -> None:
        error = urllib.error.HTTPError(
            "https://fixture.invalid/series",
            400,
            "bad request",
            {},
            io.BytesIO(
                json.dumps(
                    {"error_code": 400, "error_message": f"invalid api_key {TEST_KEY}"}
                ).encode("utf-8")
            ),
        )
        with self.assertRaises(fred.FredAdapterError) as caught:
            fred.FredClient(
                TEST_KEY,
                base_url="https://fixture.invalid",
                opener=FakeOpener([error]),
            ).request("series", {"series_id": "FEDFUNDS"})
        self.assertNotIn(TEST_KEY, str(caught.exception))


class FredCliTests(unittest.TestCase):
    def test_cli_out_of_range_vintage_never_creates_capture(self):
        script = r"""
import io, os, sys
sys.path.insert(0, sys.argv[1])
import money_craft as mc
import fred_adapter as fred
os.environ['FRED_API_KEY'] = 'a'*32
class Response(io.BytesIO):
    headers = {}
class Opener:
    def open(self, request, timeout):
        return Response(b'{"realtime_start":"2026-01-01","realtime_end":"2026-01-31","vintage_dates":["2026-02-01"]}')
fred.urllib.request.build_opener = lambda *args: Opener()
sys.argv = ['money_craft.py','data','vintages','--series-id','FIXTURE','--start','2026-01-01','--end','2026-01-31','--capture-dir',sys.argv[2],'--source-id','S01']
raise SystemExit(mc.main())
"""
        with tempfile.TemporaryDirectory() as directory:
            capture = Path(directory)/"capture"
            result = subprocess.run([sys.executable,"-c",script,str(SCRIPT_DIR),str(capture)],capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,mc.EXIT_SCHEMA,result.stdout+result.stderr)
            self.assertEqual(json.loads(result.stdout)["error"]["kind"],"malformed_response")
            self.assertFalse(capture.exists())
            self.assertNotIn(TEST_KEY,result.stdout+result.stderr)

    def test_cli_partial_page_is_explicit(self):
        script = r"""
import io, os, sys
sys.path.insert(0, sys.argv[1])
import money_craft as mc
import fred_adapter as fred
os.environ['FRED_API_KEY'] = 'a'*32
class Response(io.BytesIO):
    headers = {}
class Opener:
    def open(self, request, timeout):
        return Response(b'{"count":3,"offset":0,"limit":1,"seriess":[{"id":"FIXTURE"}]}')
fred.urllib.request.build_opener = lambda *args: Opener()
sys.argv = ['money_craft.py', 'data', 'search', '--provider', 'fred', '--query', 'fixture', '--limit', '1']
raise SystemExit(mc.main())
"""
        completed = subprocess.run([sys.executable, "-c", script, str(SCRIPT_DIR)], capture_output=True, text=True, timeout=10)
        self.assertEqual(completed.returncode, 0, completed.stdout+completed.stderr)
        result = json.loads(completed.stdout)
        self.assertTrue(result["ok"])
        self.assertTrue(any("partial page" in warning for warning in result["warnings"]))
        self.assertEqual(result["data"]["count"], 3)
        self.assertEqual(len(result["data"]["seriess"]), 1)

    def test_cli_incomplete_transport_returns_error_without_capture(self):
        script = r"""
import http.client, os, sys
sys.path.insert(0, sys.argv[1])
import money_craft as mc
import fred_adapter as fred
os.environ['FRED_API_KEY'] = 'a'*32
attempts = []
class Opener:
    def open(self, request, timeout):
        attempts.append(1)
        raise http.client.IncompleteRead(b'partial')
fred.urllib.request.build_opener = lambda *args: Opener()
sys.argv = ['money_craft.py', 'data', 'series', '--series-id', 'FIXTURE', '--capture-dir', sys.argv[2], '--source-id', 'S01']
code = mc.main()
assert len(attempts) == 3, attempts
raise SystemExit(code)
"""
        with tempfile.TemporaryDirectory() as directory:
            capture = Path(directory)/"capture"
            completed = subprocess.run([sys.executable, "-c", script, str(SCRIPT_DIR), str(capture)], capture_output=True, text=True, timeout=10)
            self.assertEqual(completed.returncode, mc.EXIT_TRANSIENT, completed.stdout+completed.stderr)
            self.assertEqual(json.loads(completed.stdout)["error"]["kind"], "network_error")
            self.assertFalse(capture.exists())
            self.assertNotIn(TEST_KEY, completed.stdout+completed.stderr)

    def test_cli_credential_race_stops_before_network_and_capture(self):
        script = r"""
import os, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import money_craft as mc
import fred_adapter as fred
root = Path(sys.argv[2]).resolve()
os.environ.pop('FRED_API_KEY', None)
os.environ['MONEY_CRAFT_CONFIG_HOME'] = str(root)
path, other = root/'fred-api-key', root/'replacement'
original = Path.lstat
def inspect(target, *args, **kwargs):
    info = original(target, *args, **kwargs)
    if target == path:
        os.replace(other, path)
    return info
Path.lstat = inspect
def unexpected(*args, **kwargs):
    raise AssertionError('network must not start')
fred.FredClient.request = unexpected
sys.argv = ['money_craft.py','data','series','--series-id','FIXTURE','--capture-dir',str(root/'capture'),'--source-id','S01']
raise SystemExit(mc.main())
"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, key in (("fred-api-key", TEST_KEY), ("replacement", "b"*32)):
                path = root/name; path.write_text(key); path.chmod(0o600)
            completed = subprocess.run([sys.executable,"-c",script,str(SCRIPT_DIR),directory], capture_output=True, text=True, timeout=10)
            self.assertEqual(completed.returncode, mc.EXIT_CONFIG, completed.stdout+completed.stderr)
            result = json.loads(completed.stdout)
            self.assertFalse(result["ok"])
            self.assertEqual(result["error"]["kind"], "invalid_configuration")
            self.assertFalse((root/"capture").exists())
            self.assertNotIn(TEST_KEY, completed.stdout+completed.stderr)
            self.assertNotIn("b"*32, completed.stdout+completed.stderr)

    def test_cli_long_provider_error_redacts_key_before_truncation(self):
        script = r"""
import io, json, os, sys
sys.path.insert(0, sys.argv[1])
import money_craft as mc
import fred_adapter as fred
os.environ['FRED_API_KEY'] = 'a'*32
class Response(io.BytesIO):
    headers = {}
class Opener:
    def open(self, request, timeout):
        return Response(json.dumps({'error_code':400,'error_message':'x'*490+'a'*32}).encode())
fred.urllib.request.build_opener = lambda *args: Opener()
sys.argv = ['money_craft.py', 'data', 'series', '--series-id', 'FIXTURE', '--capture-dir', sys.argv[2], '--source-id', 'S01']
raise SystemExit(mc.main())
"""
        with tempfile.TemporaryDirectory() as directory:
            capture = Path(directory)/"capture"
            completed = subprocess.run([sys.executable, "-c", script, str(SCRIPT_DIR), str(capture)], capture_output=True, text=True, timeout=10)
            self.assertEqual(completed.returncode, mc.EXIT_PROVIDER, completed.stdout+completed.stderr)
            result = json.loads(completed.stdout)
            self.assertFalse(result["ok"])
            self.assertEqual(result["error"]["kind"], "provider_error")
            self.assertNotIn(TEST_KEY[:8], completed.stdout+completed.stderr)
            self.assertFalse(capture.exists())

    def test_cli_rejects_invalid_observation_without_capture(self):
        script = r"""
import io, os, sys
sys.path.insert(0, sys.argv[1])
import money_craft as mc
import fred_adapter as fred
os.environ['FRED_API_KEY'] = 'a'*32
class Response(io.BytesIO):
    headers = {}
class Opener:
    def open(self, request, timeout):
        return Response(b'{"observations":[{"date":"2026-02-30","value":"1"}]}')
fred.urllib.request.build_opener = lambda *args: Opener()
sys.argv = ['money_craft.py', 'data', 'observations', '--series-id', 'FIXTURE', '--capture-dir', sys.argv[2], '--source-id', 'S01']
raise SystemExit(mc.main())
"""
        with tempfile.TemporaryDirectory() as directory:
            capture = Path(directory)/"capture"
            completed = subprocess.run([sys.executable, "-c", script, str(SCRIPT_DIR), str(capture)], capture_output=True, text=True, timeout=10)
            self.assertEqual(completed.returncode, mc.EXIT_SCHEMA, completed.stdout+completed.stderr)
            result = json.loads(completed.stdout)
            self.assertFalse(result["ok"])
            self.assertEqual(result["error"]["kind"], "malformed_response")
            self.assertFalse(capture.exists())
            self.assertNotIn(TEST_KEY, completed.stdout+completed.stderr)

    def test_cli_rejects_wrong_identity_and_as_of_before_capture(self):
        script = r"""
import io, json, os, sys
sys.path.insert(0, sys.argv[1])
import money_craft as mc
import fred_adapter as fred
os.environ['FRED_API_KEY'] = 'a'*32
payload = sys.argv[3].encode()
class Response(io.BytesIO):
    headers = {}
class Opener:
    def open(self, request, timeout):
        return Response(payload)
fred.urllib.request.build_opener = lambda *args: Opener()
sys.argv = ['money_craft.py', 'data', sys.argv[4], '--series-id', 'FIXTURE', '--as-known-on', '2026-08-31', '--capture-dir', sys.argv[2], '--source-id', 'S01']
raise SystemExit(mc.main())
"""
        cases = [
            ("series", {"realtime_start":"2026-08-31", "realtime_end":"2026-08-31", "seriess":[{"id":"OTHER", "realtime_start":"2026-08-31", "realtime_end":"2026-08-31"}]}),
            ("observations", {"realtime_start":"2026-09-01", "realtime_end":"2026-09-01", "observations":[{"date":"2026-07-01", "value":"1", "realtime_start":"2026-09-01", "realtime_end":"2026-09-01"}]}),
        ]
        for operation, payload in cases:
            with self.subTest(operation=operation), tempfile.TemporaryDirectory() as directory:
                capture = Path(directory)/"capture"
                completed = subprocess.run([sys.executable, "-c", script, str(SCRIPT_DIR), str(capture), json.dumps(payload), operation], capture_output=True, text=True, timeout=10)
                self.assertEqual(completed.returncode, mc.EXIT_SCHEMA, completed.stdout+completed.stderr)
                self.assertEqual(json.loads(completed.stdout)["error"]["kind"], "malformed_response")
                self.assertFalse(capture.exists())
                self.assertNotIn(TEST_KEY, completed.stdout+completed.stderr)

    def test_cli_maps_current_and_as_known_on_observations(self) -> None:
        parser = mc.build_parser()
        args = parser.parse_args(
            [
                "data",
                "observations",
                "--series-id",
                "t10yie",
                "--start",
                "2025-01-01",
                "--end",
                "2026-01-01",
                "--as-known-on",
                "2026-01-15",
                "--units",
                "lin",
            ]
        )
        operation, path, parameters, output = mc.prepare_operation(args)
        self.assertEqual((operation, path), ("observations", "fred://series/observations"))
        self.assertEqual(parameters["series_id"], "T10YIE")
        self.assertEqual(parameters["realtime_start"], "2026-01-15")
        self.assertEqual(parameters["realtime_end"], "2026-01-15")
        self.assertEqual(output["as_known_on"], "2026-01-15")

    def test_fred_rejects_market_data_operations(self) -> None:
        parser = mc.build_parser()
        args = parser.parse_args(
            ["data", "snapshot", "--provider", "fred", "--thscodes", "600519.SH"]
        )
        with self.assertRaises(mc.MoneyCraftError):
            mc.prepare_operation(args)

    def test_missing_key_cli_exits_three_without_network(self) -> None:
        environment = dict(os.environ)
        environment.pop("FRED_API_KEY", None)
        environment.pop(mc.DATA_PYTHON_ENV, None)
        with tempfile.TemporaryDirectory() as directory:
            environment["HOME"] = directory
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "money_craft.py"),
                    "data",
                    "series",
                    "--series-id",
                    "FEDFUNDS",
                ],
                text=True,
                capture_output=True,
                env=environment,
                check=False,
            )
        payload = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, mc.EXIT_CONFIG)
        self.assertEqual(payload["provider"], "fred")
        self.assertEqual(payload["error"]["kind"], "missing_configuration")

    def test_default_data_runtime_is_stable_and_repo_external(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path, source = mc.preferred_data_python({}, home=Path(directory))
        self.assertEqual(source, "default")
        self.assertEqual(
            path.parts[-7:],
            (".local", "share", "money-craft", "venvs", "data", "bin", "python"),
        )


if __name__ == "__main__":
    unittest.main()
