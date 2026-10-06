from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "money-craft" / "scripts"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "fuyao"
sys.path.insert(0, str(SCRIPT_DIR))

import money_craft as mc  # noqa: E402
import fuyao_client  # noqa: E402


def fixture_bytes(name: str) -> bytes:
    return (FIXTURE_DIR / name).read_bytes()


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


class QueueHandler(BaseHTTPRequestHandler):
    responses: list[tuple[int, bytes, dict[str, str]]] = []
    api_keys: list[str | None] = []

    def do_GET(self) -> None:
        type(self).api_keys.append(self.headers.get("X-api-key"))
        status, body, headers = type(self).responses.pop(0)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        for key, value in headers.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return None


def response(code: int = 0, data: dict[str, object] | None = None, message: str = "success") -> FakeResponse:
    payload = {
        "code": code,
        "message": message,
        "request_id": "request-1",
        "data": data,
    }
    return FakeResponse(json.dumps(payload).encode("utf-8"))


class FuyaoClientTests(unittest.TestCase):
    def test_success_preserves_decimal_precision_and_header(self) -> None:
        raw = fixture_bytes("snapshot.success.synthetic.json")
        opener = FakeOpener([FakeResponse(raw)])
        client = mc.FuyaoClient("test-secret", base_url="https://fixture.invalid", opener=opener)
        result = client.request("snapshot", "/snapshot", {"thscodes": "600519.SH"})
        self.assertEqual(result.payload["data"]["item"][0]["last_price"], Decimal("1.2300"))
        request = opener.requests[0]
        self.assertEqual(request.get_header("X-api-key"), "test-secret")
        self.assertIn("thscodes=600519.SH", request.full_url)

    def test_business_auth_error_is_not_retried(self) -> None:
        opener = FakeOpener([response(2001, None, "invalid key")])
        sleeps: list[float] = []
        client = mc.FuyaoClient("secret", opener=opener, sleeper=sleeps.append)
        with self.assertRaises(mc.MoneyCraftError) as caught:
            client.request("snapshot", "/snapshot", {})
        self.assertEqual(caught.exception.kind, "authentication_error")
        self.assertFalse(caught.exception.retryable)
        self.assertEqual(len(opener.requests), 1)
        self.assertEqual(sleeps, [])

    def test_transient_business_error_retries_then_succeeds(self) -> None:
        opener = FakeOpener(
            [
                response(4001, None, "rate limited"),
                response(5002, None, "timeout"),
                response(0, {"timestamp": 1, "item": []}),
            ]
        )
        sleeps: list[float] = []
        client = mc.FuyaoClient("secret", opener=opener, sleeper=sleeps.append)
        result = client.request("snapshot", "/snapshot", {})
        self.assertEqual(result.payload["code"], 0)
        self.assertEqual(sleeps, [0.5, 1.0])

    def test_http_retry_after_is_bounded_and_used(self) -> None:
        error = urllib.error.HTTPError(
            "https://fixture.invalid/snapshot",
            429,
            "rate limited",
            {"Retry-After": "99"},
            io.BytesIO(b""),
        )
        opener = FakeOpener([error, response(0, {"timestamp": 1, "item": []})])
        sleeps: list[float] = []
        client = mc.FuyaoClient("secret", opener=opener, sleeper=sleeps.append)
        client.request("snapshot", "/snapshot", {})
        self.assertEqual(sleeps, [10.0])

    def test_malformed_envelope_fails_closed(self) -> None:
        opener = FakeOpener([FakeResponse(fixture_bytes("malformed-envelope.synthetic.json"))])
        client = mc.FuyaoClient("secret", opener=opener)
        with self.assertRaises(mc.MoneyCraftError) as caught:
            client.request("snapshot", "/snapshot", {})
        self.assertEqual(caught.exception.exit_code, mc.EXIT_SCHEMA)

    def test_synthetic_data_gap_is_bounded_and_classified(self) -> None:
        raw = fixture_bytes("transient-empty.synthetic.json")
        opener = FakeOpener([FakeResponse(raw), FakeResponse(raw), FakeResponse(raw)])
        sleeps: list[float] = []
        client = mc.FuyaoClient("secret", opener=opener, sleeper=sleeps.append)
        with self.assertRaises(mc.MoneyCraftError) as caught:
            client.request("indicators", "/indicators", {})
        self.assertEqual(caught.exception.kind, "transient_provider_error")
        self.assertEqual(caught.exception.code, 5003)
        self.assertTrue(caught.exception.retryable)
        self.assertEqual(sleeps, [0.5, 1.0])

    def test_response_size_limit(self) -> None:
        opener = FakeOpener([FakeResponse(b"x" * (fuyao_client.MAX_RESPONSE_BYTES + 1))])
        client = mc.FuyaoClient("secret", opener=opener)
        with self.assertRaises(mc.MoneyCraftError) as caught:
            client.request("snapshot", "/snapshot", {})
        self.assertEqual(caught.exception.kind, "response_too_large")

    def test_loopback_http_fixture_exercises_wire_contract(self) -> None:
        limited = json.dumps(
            {"code": 4001, "message": "rate", "request_id": "r0", "data": None}
        ).encode("utf-8")
        success = json.dumps(
            {"code": 0, "message": "success", "request_id": "r1", "data": {"timestamp": 1, "item": []}}
        ).encode("utf-8")
        QueueHandler.responses = [(200, limited, {}), (200, success, {})]
        QueueHandler.api_keys = []
        server = ThreadingHTTPServer(("127.0.0.1", 0), QueueHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            sleeps: list[float] = []
            client = mc.FuyaoClient(
                "wire-secret",
                base_url=f"http://127.0.0.1:{server.server_port}",
                sleeper=sleeps.append,
            )
            result = client.request("snapshot", "/snapshot", {"thscodes": "600519.SH"})
            self.assertEqual(result.payload["request_id"], "r1")
            self.assertEqual(sleeps, [0.5])
            self.assertEqual(QueueHandler.api_keys, ["wire-secret", "wire-secret"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


class InputAndCaptureTests(unittest.TestCase):
    def test_secure_file_credential_and_environment_precedence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            path = mc.fuyao_api_key_path(home, {})
            path.parent.mkdir(parents=True)
            path.write_text("file-secret\n", encoding="utf-8")
            path.chmod(0o600)
            credential = mc.load_fuyao_credential({}, home=home)
            self.assertEqual(credential.api_key, "file-secret")
            self.assertEqual(credential.source, "secure-file")
            overridden = mc.load_fuyao_credential({"FUYAO_API_KEY": "environment-secret"}, home=home)
            self.assertEqual(overridden.api_key, "environment-secret")
            self.assertEqual(overridden.source, "environment")

    def test_secure_file_rejects_permissive_mode_and_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            path = mc.fuyao_api_key_path(home, {})
            path.parent.mkdir(parents=True)
            path.write_text("file-secret\n", encoding="utf-8")
            path.chmod(0o644)
            with self.assertRaises(mc.MoneyCraftError) as permissive:
                mc.load_fuyao_credential({}, home=home)
            self.assertEqual(permissive.exception.kind, "invalid_configuration")
            path.unlink()
            target = path.parent / "target"
            target.write_text("file-secret\n", encoding="utf-8")
            target.chmod(0o600)
            path.symlink_to(target)
            with self.assertRaises(mc.MoneyCraftError) as symlinked:
                mc.load_fuyao_credential({}, home=home)
            self.assertEqual(symlinked.exception.kind, "invalid_configuration")

    def test_thscode_and_date_contracts(self) -> None:
        self.assertEqual(mc.parse_thscodes("600519.sh,600519.SH"), ["600519.SH"])
        with self.assertRaises(mc.MoneyCraftError):
            mc.parse_thscodes("600519")
        with self.assertRaises(mc.MoneyCraftError):
            mc.validate_range("2010-01-01", "2021-01-02", max_years=10)
        self.assertEqual(mc.date_to_ms("2026-01-01"), 1767196800000)

    def test_calendar_filters_locally(self) -> None:
        data = fuyao_client.parse_json(fixture_bytes("calendar.success.synthetic.json"))["data"]
        filtered = mc.filter_calendar(data, "2026-01-02", "2026-01-02")
        self.assertEqual(filtered["item"], [{"date": "20260102", "date_ms": 2}])

    def test_capture_is_atomic_redacted_and_non_overwriting(self) -> None:
        secret = "local-test-secret"
        raw = b'{"code":0,"message":"success","request_id":"r1","data":{"timestamp":1,"item":[]}}'
        result = mc.ProviderResult(
            operation="snapshot",
            path="/api/a-share/prices/snapshot",
            parameters={"thscodes": "600519.SH"},
            payload=fuyao_client.parse_json(raw),
            raw_response=raw,
            fetched_at="2026-08-23T00:00:00Z",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            destination = mc.capture_result(root, "S01", result, output_parameters=result.parameters)
            combined = b"".join(path.read_bytes() for path in destination.iterdir() if path.is_file())
            self.assertNotIn(secret.encode(), combined)
            request_payload = json.loads((destination / "request.json").read_text(encoding="utf-8"))
            self.assertEqual(request_payload["authentication"], "environment:FUYAO_API_KEY")
            with self.assertRaises(mc.MoneyCraftError):
                mc.capture_result(root, "S01", result, output_parameters=result.parameters)

    def test_capture_rejects_reflected_authentication_material(self) -> None:
        secret = "reflected-secret"
        raw = json.dumps(
            {"code": 0, "message": "success", "request_id": "r1", "data": {"item": [secret]}}
        ).encode("utf-8")
        result = mc.ProviderResult(
            operation="snapshot",
            path="/snapshot",
            parameters={},
            payload=fuyao_client.parse_json(raw),
            raw_response=raw,
            fetched_at="2026-08-23T00:00:00Z",
        )
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(mc.MoneyCraftError):
                mc.capture_result(
                    Path(directory),
                    "S01",
                    result,
                    output_parameters={},
                    forbidden_values=(secret,),
                )

    def test_financial_and_indicator_parameter_contracts(self) -> None:
        parser = mc.build_parser()
        args = parser.parse_args(
            [
                "data",
                "financials",
                "--thscode",
                "600519.SH",
                "--statement",
                "income",
                "--period",
                "annual",
                "--limit",
                "3",
            ]
        )
        operation, path, parameters, _ = mc.prepare_operation(args)
        self.assertEqual(operation, "financials.income")
        self.assertEqual(path, "/api/a-share/financials/income-statements")
        self.assertEqual(parameters["limit"], 3)
        conflict = parser.parse_args(
            [
                "data",
                "financials",
                "--thscode",
                "600519.SH",
                "--statement",
                "income",
                "--limit",
                "3",
                "--start",
                "2025-01-01",
                "--end",
                "2025-12-31",
            ]
        )
        with self.assertRaises(mc.MoneyCraftError):
            mc.prepare_operation(conflict)
        bad_indicator = parser.parse_args(
            ["data", "indicators", "--thscode", "600519.SH", "--report", "2025-Q1"]
        )
        with self.assertRaises(mc.MoneyCraftError):
            mc.prepare_operation(bad_indicator)

    def test_missing_key_cli_exits_three_without_network(self) -> None:
        environment = dict(os.environ)
        environment.pop("FUYAO_API_KEY", None)
        with tempfile.TemporaryDirectory() as directory:
            environment["HOME"] = directory
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "money_craft.py"),
                    "data",
                    "snapshot",
                    "--thscodes",
                    "600519.SH",
                ],
                text=True,
                capture_output=True,
                env=environment,
                check=False,
            )
        payload = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, mc.EXIT_CONFIG)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["kind"], "missing_configuration")


if __name__ == "__main__":
    unittest.main()
