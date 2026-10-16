"""Bounded GET-only transport shared by the two supported platforms."""

from __future__ import annotations

import ipaddress
import json
import os
import socket
import time
from dataclasses import dataclass
from typing import Any, Mapping
from urllib import error, parse, request


_PAGE_SIZE = 50
_MAX_RESPONSE_BYTES = 4 * 1024 * 1024
_RETRYABLE_STATUSES = frozenset({429, 500, 502, 503, 504})


class ProviderError(RuntimeError):
    """A safe provider failure suitable for users and structured callers.

    ``code`` is intentionally stable and never contains a token, URL query,
    response body, or raw transport exception.
    """

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


class _NoRedirect(request.HTTPRedirectHandler):
    """Reject all redirects so an Authorization header cannot be forwarded."""

    def redirect_request(self, req: request.Request, fp: Any, code: int,
                         msg: str, headers: Any, newurl: str) -> None:
        return None


@dataclass(frozen=True)
class _Response:
    data: Any
    headers: Mapping[str, str]


class ReadOnlyAPI:
    api_prefix = ""
    auth_scheme = "Bearer"
    accept = "application/json"
    page_size_parameter = "page_size"

    def __init__(
        self,
        base_url: str,
        token_env: str,
        timeout: float = 10,
        *,
        allow_loopback_http: bool = False,
        opener: Any | None = None,
        max_pages: int = 20,
        retries: int = 2,
        retry_delay: float = 0.05,
    ) -> None:
        self._base_url = self._validate_base_url(base_url, allow_loopback_http)
        if not isinstance(token_env, str) or not token_env or "=" in token_env:
            raise ProviderError("invalid_response", "token environment variable name is invalid")
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ProviderError("invalid_response", "timeout must be positive")
        if isinstance(max_pages, bool) or not isinstance(max_pages, int) or max_pages < 1:
            raise ProviderError("invalid_response", "max_pages must be at least one")
        if isinstance(retries, bool) or not isinstance(retries, int) or retries < 0:
            raise ProviderError("invalid_response", "retries must not be negative")
        if isinstance(retry_delay, bool) or not isinstance(retry_delay, (int, float)) or retry_delay < 0:
            raise ProviderError("invalid_response", "retry_delay must not be negative")

        self.token_env = token_env
        self.timeout = float(timeout)
        self.max_pages = max_pages
        self.retries = retries
        self.retry_delay = float(retry_delay)
        self._opener = opener or request.build_opener(_NoRedirect())


    @staticmethod
    def _validate_base_url(base_url: str, allow_loopback_http: bool) -> str:
        if not isinstance(base_url, str) or not base_url:
            raise ProviderError("invalid_response", "base URL is invalid")
        # urlsplit normalizes some control characters, so reject them before
        # parsing rather than validating the normalized representation only.
        if any(ord(character) < 32 or ord(character) == 127 for character in base_url):
            raise ProviderError("invalid_response", "base URL is invalid")
        try:
            parts = parse.urlsplit(base_url)
            hostname = parts.hostname
            port = parts.port  # Validate malformed ports without exposing the URL.
        except ValueError as exc:
            raise ProviderError("invalid_response", "base URL is invalid") from exc
        del port
        if (
            parts.scheme not in {"https", "http"}
            or not parts.netloc
            or not hostname
            or parts.username is not None
            or parts.password is not None
            or parts.query
            or parts.fragment
        ):
            raise ProviderError("invalid_response", "base URL must be an absolute URL without credentials or query data")
        if parts.scheme == "http" and not (allow_loopback_http and ReadOnlyAPI._is_loopback(hostname)):
            raise ProviderError("invalid_response", "HTTP is allowed only for an explicit loopback test server")
        if any(ord(character) < 32 for character in parts.path):
            raise ProviderError("invalid_response", "base URL path is invalid")
        return parse.urlunsplit((parts.scheme, parts.netloc, parts.path.rstrip("/"), "", ""))


    @staticmethod
    def _is_loopback(hostname: str) -> bool:
        if hostname.lower() == "localhost":
            return True
        try:
            return ipaddress.ip_address(hostname).is_loopback
        except ValueError:
            return False


    @staticmethod
    def _segment(value: str) -> str:
        return parse.quote(value, safe="")


    @staticmethod
    def _number(value: int) -> str:
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ProviderError("invalid_response", "task and change numbers must be positive integers")
        return str(value)


    @staticmethod
    def _sha(value: str) -> str:
        if (
            not isinstance(value, str)
            or not value
            or any(character in value for character in "/\\?#%")
            or any(ord(character) < 32 for character in value)
        ):
            raise ProviderError("invalid_response", "commit SHA is invalid")
        return parse.quote(value, safe="")


    def _object(self, path: str) -> dict[str, Any]:
        response = self._get(path)
        if not isinstance(response.data, dict):
            raise ProviderError("invalid_response", "Provider returned an unexpected object response")
        return response.data


    def _list(self, path: str) -> list[Any]:
        items: list[Any] = []
        for page in range(1, self.max_pages + 1):
            response = self._get(path, {"page": page, self.page_size_parameter: _PAGE_SIZE})
            if not isinstance(response.data, list):
                raise ProviderError("invalid_response", "Provider returned an unexpected list response")
            items.extend(response.data)
            # A provider may clamp the requested page size. A short page
            # therefore does not prove completion. Continue until a page request
            # returns an empty array, or fail closed at the configured cap.
            if not response.data:
                return items
        raise ProviderError("incomplete", "Provider result reached the configured pagination limit")


    def _get(self, path: str, query: Mapping[str, int] | None = None) -> _Response:
        token = os.environ.get(self.token_env)
        if not token:
            raise ProviderError("auth_required", "Provider access token is not available")
        if any(ord(character) < 32 or ord(character) == 127 for character in token):
            raise ProviderError("auth_required", "Provider access token is invalid")
        encoded_path = self.api_prefix + path
        url = self._base_url + encoded_path
        if query:
            url += "?" + parse.urlencode(query)
        headers = {
            "Accept": self.accept,
            "Authorization": f"{self.auth_scheme} {token}",
            "User-Agent": "team-workflow-craft",
        }
        req = request.Request(url, headers=headers, method="GET")

        for attempt in range(self.retries + 1):
            try:
                with self._opener.open(req, timeout=self.timeout) as response:
                    status = response.status if hasattr(response, "status") else response.getcode()
                    if status != 200:
                        if status in _RETRYABLE_STATUSES and attempt < self.retries:
                            self._pause(attempt)
                            continue
                        raise self._status_error(status)
                    content_length = response.headers.get("Content-Length")
                    if content_length is not None:
                        try:
                            if int(content_length) > _MAX_RESPONSE_BYTES:
                                raise ProviderError("invalid_response", "Provider response is too large")
                        except ValueError as exc:
                            raise ProviderError("invalid_response", "Provider response length is invalid") from exc
                    body = response.read(_MAX_RESPONSE_BYTES + 1)
                    if len(body) > _MAX_RESPONSE_BYTES:
                        raise ProviderError("invalid_response", "Provider response is too large")
                    try:
                        data = json.loads(body.decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                        raise ProviderError("invalid_response", "Provider returned invalid JSON") from exc
                    return _Response(data=data, headers=dict(response.headers.items()))
            except ProviderError:
                raise
            except error.HTTPError as exc:
                try:
                    if 300 <= exc.code < 400:
                        raise ProviderError("unavailable", "Provider redirect responses are refused") from None
                    if exc.code in _RETRYABLE_STATUSES and attempt < self.retries:
                        self._pause(attempt)
                        continue
                    raise self._status_error(exc.code) from None
                finally:
                    exc.close()
            except (error.URLError, socket.timeout, TimeoutError, OSError):
                if attempt < self.retries:
                    self._pause(attempt)
                    continue
                raise ProviderError("unavailable", "Provider could not be reached") from None
        raise ProviderError("unavailable", "Provider could not be reached")


    def _pause(self, attempt: int) -> None:
        if self.retry_delay:
            time.sleep(self.retry_delay * (attempt + 1))


    @staticmethod
    def _status_error(status: int) -> ProviderError:
        if status == 401:
            return ProviderError("auth_required", "Provider rejected the access token")
        if status == 403:
            return ProviderError("forbidden", "Provider denied access to this resource")
        if status == 404:
            return ProviderError("not_found", "Provider resource was not found")
        if status in {405, 501}:
            return ProviderError("unsupported", "Provider does not support this read operation")
        return ProviderError("unavailable", "Provider request did not succeed")


