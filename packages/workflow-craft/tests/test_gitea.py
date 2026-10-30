"""Offline contract tests for the read-only Gitea adapter."""

from __future__ import annotations

import json
import os
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


_RUNTIME = Path(__file__).resolve().parents[1] / "skills" / "workflow-craft" / "scripts"
sys.path.insert(0, str(_RUNTIME))

from twc_lib.providers.gitea import Gitea, ProviderError  # noqa: E402


class _GiteaHandler(BaseHTTPRequestHandler):
    routes: dict[tuple[str, tuple[tuple[str, tuple[str, ...]], ...]], tuple[int, object, dict[str, str]]] = {}
    requests: list[tuple[str, str | None]] = []

    def do_GET(self) -> None:  # noqa: N802
        from urllib.parse import parse_qs, urlsplit

        parts = urlsplit(self.path)
        query = tuple(sorted((key, tuple(values)) for key, values in parse_qs(parts.query).items()))
        type(self).requests.append((self.path, self.headers.get("Authorization")))
        status, payload, headers = type(self).routes.get(
            (parts.path, query), (404, {"message": "not found"}, {})
        )
        self.send_response(status)
        for key, value in headers.items():
            self.send_header(key, value)
        if isinstance(payload, bytes):
            body = payload
        else:
            body = json.dumps(payload).encode("utf-8")
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


class _FailingOpener:
    def __init__(self) -> None:
        self.calls = 0

    def open(self, req: object, timeout: float) -> object:
        from urllib.error import URLError

        self.calls += 1
        raise URLError("offline")


class GiteaAdapterTests(unittest.TestCase):
    token_name = "TWC_GITEA_TEST_TOKEN"

    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), _GiteaHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def setUp(self) -> None:
        _GiteaHandler.routes = {}
        _GiteaHandler.requests = []
        self.previous_token = os.environ.get(self.token_name)
        os.environ[self.token_name] = "test-token"

    def tearDown(self) -> None:
        if self.previous_token is None:
            os.environ.pop(self.token_name, None)
        else:
            os.environ[self.token_name] = self.previous_token

    def provider(self, **kwargs: object) -> Gitea:
        return Gitea(
            self.base_url,
            "team/repo",
            token_env=self.token_name,
            allow_loopback_http=True,
            retry_delay=0,
            **kwargs,
        )

    @staticmethod
    def route(path: str, payload: object, *, query: dict[str, tuple[str, ...]] | None = None,
              status: int = 200, headers: dict[str, str] | None = None) -> None:
        normalized = tuple(sorted((query or {}).items()))
        _GiteaHandler.routes[(path, normalized)] = (status, payload, headers or {})

    def test_reads_documented_endpoints_and_returns_raw_json(self) -> None:
        self.route("/api/v1/user", {"login": "intern"})
        self.route("/api/v1/version", {"version": "1.24.0"})
        self.route("/api/v1/repos/team/repo", {"full_name": "team/repo"})
        self.route("/api/v1/repos/team/repo/issues/7", {"number": 7, "title": "task"})
        self.route("/api/v1/repos/team/repo/pulls/8", {"number": 8, "head": {"sha": "abc"}})
        page_one = {"page": ("1",), "limit": ("50",)}
        page_two = {"page": ("2",), "limit": ("50",)}
        self.route("/api/v1/repos/team/repo/pulls/8/reviews", [{"id": 1}], query=page_one)
        self.route("/api/v1/repos/team/repo/pulls/8/reviews", [], query=page_two)
        self.route("/api/v1/repos/team/repo/statuses/abc", [{"state": "success"}], query=page_one)
        self.route("/api/v1/repos/team/repo/statuses/abc", [], query=page_two)

        provider = self.provider()
        self.assertEqual(provider.get_identity(), {"login": "intern"})
        self.assertEqual(provider.get_version(), {"version": "1.24.0"})
        self.assertEqual(provider.get_repository(), {"full_name": "team/repo"})
        self.assertEqual(provider.get_task(7), {"number": 7, "title": "task"})
        self.assertEqual(provider.get_change(8), {"number": 8, "head": {"sha": "abc"}})
        self.assertEqual(provider.get_reviews(8), [{"id": 1}])
        self.assertEqual(provider.get_checks("abc"), [{"state": "success"}])
        self.assertTrue(all(header == "token test-token" for _, header in _GiteaHandler.requests))

    def test_short_pages_continue_until_a_legitimate_empty_page(self) -> None:
        page_one = {"page": ("1",), "limit": ("50",)}
        page_two = {"page": ("2",), "limit": ("50",)}
        page_three = {"page": ("3",), "limit": ("50",)}
        self.route("/api/v1/repos/team/repo/pulls/9/reviews", [{"id": 1}], query=page_one)
        self.route("/api/v1/repos/team/repo/pulls/9/reviews", [{"id": 2}], query=page_two)
        self.route("/api/v1/repos/team/repo/pulls/9/reviews", [], query=page_three)

        self.assertEqual(self.provider().get_reviews(9), [{"id": 1}, {"id": 2}])
        review_paths = [path for path, _ in _GiteaHandler.requests]
        self.assertEqual(len(review_paths), 3)
        self.assertIn("page=3", review_paths[-1])

    def test_missing_token_and_http_statuses_are_safe_and_classified(self) -> None:
        os.environ.pop(self.token_name, None)
        with self.assertRaisesRegex(ProviderError, "access token") as missing:
            self.provider().get_identity()
        self.assertEqual(missing.exception.code, "auth_required")
        self.assertEqual(_GiteaHandler.requests, [])

        os.environ[self.token_name] = "not-to-be-leaked"
        for status, expected in ((401, "auth_required"), (403, "forbidden"), (404, "not_found"), (405, "unsupported")):
            with self.subTest(status=status):
                self.route("/api/v1/user", {}, status=status)
                with self.assertRaises(ProviderError) as captured:
                    self.provider(retries=0).get_identity()
                self.assertEqual(captured.exception.code, expected)
                self.assertNotIn("not-to-be-leaked", str(captured.exception))

    def test_rejects_unsafe_base_url_and_repository(self) -> None:
        for base_url in (
            "http://gitea.example",
            "https://token@gitea.example",
            "https://gitea.example/?token=bad",
            "https://gitea.example/#fragment",
            "https://gitea.example/\nignored",
        ):
            with self.subTest(base_url=base_url):
                with self.assertRaises(ProviderError):
                    Gitea(base_url, "team/repo")
        with self.assertRaises(ProviderError):
            Gitea("https://gitea.example", "team/repo/other")
        with self.assertRaises(ProviderError):
            Gitea("https://gitea.example", "team/repo?token=bad")
        with self.assertRaises(ProviderError):
            Gitea("https://gitea.example", "team /repo")

    def test_rejects_header_injection_token_and_mismatched_resource_number(self) -> None:
        os.environ[self.token_name] = "unsafe\r\ntoken"
        with self.assertRaises(ProviderError) as token_error:
            self.provider().get_identity()
        self.assertEqual(token_error.exception.code, "auth_required")
        self.assertNotIn("unsafe", str(token_error.exception))
        self.assertEqual(_GiteaHandler.requests, [])

        os.environ[self.token_name] = "test-token"
        self.route("/api/v1/repos/team/repo/issues/12", {"number": 13})
        with self.assertRaises(ProviderError) as number_error:
            self.provider().get_task(12)
        self.assertEqual(number_error.exception.code, "invalid_response")

    def test_rejects_redirect_without_following_it_or_exposing_token(self) -> None:
        self.route("/api/v1/user", b"", status=302, headers={"Location": "http://example.invalid/steal"})
        os.environ[self.token_name] = "redirect-secret"
        with self.assertRaises(ProviderError) as captured:
            self.provider(retries=0).get_identity()
        self.assertEqual(captured.exception.code, "unavailable")
        self.assertNotIn("redirect-secret", str(captured.exception))
        self.assertEqual(len(_GiteaHandler.requests), 1)
        self.assertEqual(_GiteaHandler.requests[0][1], "token redirect-secret")

    def test_network_retries_are_bounded_and_safe(self) -> None:
        opener = _FailingOpener()
        os.environ[self.token_name] = "network-secret"
        with self.assertRaises(ProviderError) as captured:
            self.provider(opener=opener, retries=1).get_identity()
        self.assertEqual(captured.exception.code, "unavailable")
        self.assertEqual(opener.calls, 2)
        self.assertNotIn("network-secret", str(captured.exception))

    def test_bounded_pagination_never_claims_a_complete_result(self) -> None:
        full_page = [{"id": value} for value in range(50)]
        self.route(
            "/api/v1/repos/team/repo/pulls/4/reviews",
            full_page,
            query={"page": ("1",), "limit": ("50",)},
        )
        self.route(
            "/api/v1/repos/team/repo/pulls/4/reviews",
            full_page,
            query={"page": ("2",), "limit": ("50",)},
        )
        with self.assertRaises(ProviderError) as captured:
            self.provider(max_pages=2).get_reviews(4)
        self.assertEqual(captured.exception.code, "incomplete")

    def test_invalid_json_is_not_accepted_as_evidence(self) -> None:
        self.route("/api/v1/user", b"not json")
        with self.assertRaises(ProviderError) as captured:
            self.provider().get_identity()
        self.assertEqual(captured.exception.code, "invalid_response")


if __name__ == "__main__":
    unittest.main()
