#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import queue
import shutil
import subprocess
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_COMMIT = "bb43570f139feafc2632f8da19f34b4863e6bccb"
EXPECTED_TOOLS = 60


class FixtureHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        body = b"<!doctype html><title>Reverse Craft Fixture</title><script>window.reverseCraftSign=x=>'fixture:'+x</script><h1 id='ready'>ready</h1>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate browser67 js-reverse through real MCP JSON-RPC")
    parser.add_argument("--browser67-home")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument(
        "--surface-only",
        action="store_true",
        help="skip managed-tab cleanup, fixture, evidence, rebuild, and finalize calls",
    )
    parser.add_argument("--allow-head-drift", action="store_true")
    return parser.parse_args()


def browser67_home(explicit: str | None) -> Path:
    candidates = [
        explicit,
        os.environ.get("BROWSER67_HOME"),
        str(ROOT.parent / "browser67"),
        str(Path.home() / "Documents" / "sixseven" / "codeproject" / "browser67"),
    ]
    for raw in candidates:
        if raw:
            path = Path(raw).expanduser().resolve()
            if (path / "src/mcp/js-reverse/server.mjs").is_file():
                return path
    raise RuntimeError("browser67 checkout with js-reverse MCP not found")


class McpClient:
    def __init__(self, command: list[str], cwd: Path, timeout: int) -> None:
        self.timeout = timeout
        self.process = subprocess.Popen(
            command, cwd=cwd, text=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            bufsize=1, env={**os.environ, "NO_COLOR": "1"},
        )
        self.responses: queue.Queue[dict[str, Any]] = queue.Queue()
        self.stderr: list[str] = []
        self.next_id = 1
        threading.Thread(target=self._read_stdout, daemon=True).start()
        threading.Thread(target=self._read_stderr, daemon=True).start()

    def _read_stdout(self) -> None:
        assert self.process.stdout
        for line in self.process.stdout:
            if line.strip():
                self.responses.put(json.loads(line))

    def _read_stderr(self) -> None:
        assert self.process.stderr
        for line in self.process.stderr:
            self.stderr.append(line.rstrip())
            if len(self.stderr) > 100:
                self.stderr.pop(0)

    def call(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        request_id = self.next_id
        self.next_id += 1
        assert self.process.stdin
        self.process.stdin.write(json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}) + "\n")
        self.process.stdin.flush()
        while True:
            response = self.responses.get(timeout=self.timeout)
            if response.get("id") == request_id:
                if "error" in response:
                    raise RuntimeError(f"MCP error: {response['error']}")
                return response["result"]

    def notify(self, method: str, params: dict[str, Any]) -> None:
        assert self.process.stdin
        self.process.stdin.write(json.dumps({"jsonrpc": "2.0", "method": method, "params": params}) + "\n")
        self.process.stdin.flush()

    def tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        result = self.call("tools/call", {"name": name, "arguments": arguments})
        content = result.get("content", [])
        if not content or content[0].get("type") != "text":
            raise RuntimeError(f"tool {name} returned no text content")
        outcome = json.loads(content[0]["text"])
        if outcome.get("schema") != "browser67.tool-outcome.v3" or outcome.get("ok") is not True:
            raise RuntimeError(f"tool {name} failed: {json.dumps(outcome, ensure_ascii=False)[:1500]}")
        return outcome

    def close(self) -> None:
        if self.process.stdin:
            self.process.stdin.close()
        try:
            self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()


def git_head(path: Path) -> str | None:
    completed = subprocess.run(["git", "rev-parse", "HEAD"], cwd=path, text=True, capture_output=True, timeout=10, check=False)
    return completed.stdout.strip() if completed.returncode == 0 else None


def page_id(outcome: dict[str, Any]) -> str | None:
    page = outcome.get("page") or {}
    data = outcome.get("data") or {}
    candidates = [page.get("tab_id"), data.get("page_id"), data.get("tab_id"), data.get("session_id")]
    for key in ("session", "page", "managed_page"):
        if isinstance(data.get(key), dict):
            candidates.extend([data[key].get("id"), data[key].get("tab_id")])
    return next((str(value) for value in candidates if value), None)


def selected_fields(value: Any, fields: tuple[str, ...]) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {key: value[key] for key in fields if key in value and isinstance(value[key], (str, int, float, bool, type(None)))}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def url_is_live(url: str) -> bool:
    try:
        with urlopen(url, timeout=0.5) as response:  # noqa: S310 - loopback fixture URLs only
            return response.status == 200
    except Exception:
        return False


def cleanup_fixture_orphans(home: Path, js_client: McpClient, timeout: int) -> int:
    pages = (js_client.tool("list_pages", {}).get("data") or {}).get("pages", [])
    matches = [
        page for page in pages
        if page.get("title") == "Reverse Craft Fixture"
        and str(page.get("url", "")).startswith("http://127.0.0.1:")
        and str(page.get("url", "")).endswith("/fixture")
        and not url_is_live(str(page.get("url")))
    ]
    if not matches:
        return 0
    node = shutil.which("node")
    if not node:
        raise RuntimeError("node is not available for orphan cleanup")
    browser = McpClient([node, str(home / "src/mcp/browser/server.mjs")], home, timeout)
    cleanup_workspace = "reverse-craft-browser67-orphan-cleanup"
    cleanup_task = "stale-fixture-tabs"
    closed = 0
    try:
        browser.call("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "reverse-craft-cleanup", "version": "0.2.0"}})
        browser.notify("notifications/initialized", {})
        for page in matches:
            target = {
                "tab_id": str(page["tab_id"]),
                "browser_instance_id": str(page["browser_instance_id"]),
                "workspace_key": cleanup_workspace,
                "task_id": cleanup_task,
            }
            inspected = browser.tool("browser_tab_lifecycle", {"action": "inspect_adoption", **target})["data"]
            browser.tool("browser_tab_lifecycle", {
                "action": "adopt_existing", **target,
                "adoption_token": inspected["adoption_token"], "confirm_adopt": True,
            })
            close_inspection = browser.tool("browser_tab_lifecycle", {"action": "inspect_close_adopted", **target})["data"]
            result = browser.tool("browser_tab_lifecycle", {
                "action": "close_adopted", **target,
                "close_token": close_inspection["close_token"],
                "close_adopted": True, "confirm_close_adopted": True,
            })["data"]
            if result.get("closed") is not True or result.get("close_verified") is not True:
                raise RuntimeError("browser67 did not verify orphan fixture tab closure")
            closed += 1
    finally:
        browser.close()
    return closed


def maybe_cleanup_fixture_orphans(
    surface_only: bool,
    home: Path,
    js_client: McpClient,
    timeout: int,
) -> dict[str, Any]:
    if surface_only:
        return {
            "status": "not_requested",
            "reason": "surface_only",
            "closed_count": 0,
        }
    return {
        "status": "executed",
        "reason": "full_live_gate",
        "closed_count": cleanup_fixture_orphans(home, js_client, timeout),
    }


def main() -> int:
    args = parse_args()
    server: ThreadingHTTPServer | None = None
    server_thread: threading.Thread | None = None
    client: McpClient | None = None
    results: dict[str, Any] = {}
    workspace_key = "reverse-craft-browser67-gate"
    task_id = "js-reverse-mcp-fixture"
    try:
        home = browser67_home(args.browser67_home)
        head = git_head(home)
        if head != EXPECTED_COMMIT and not args.allow_head_drift:
            raise RuntimeError(f"browser67 HEAD drift: expected {EXPECTED_COMMIT}, got {head}")
        node = shutil.which("node")
        if not node:
            raise RuntimeError("node is not available")
        client = McpClient([node, str(home / "src/mcp/js-reverse/server.mjs")], home, args.timeout)
        initialized = client.call("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "reverse-craft-gate", "version": "0.2.0"}})
        client.notify("notifications/initialized", {})
        listed = client.call("tools/list", {})
        names = [tool["name"] for tool in listed.get("tools", [])]
        if initialized.get("serverInfo", {}).get("name") != "js-reverse":
            raise RuntimeError(f"unexpected MCP server: {initialized.get('serverInfo')}")
        if len(names) != EXPECTED_TOOLS:
            raise RuntimeError(f"expected {EXPECTED_TOOLS} tools, got {len(names)}")
        required = {"check_browser_health", "new_page", "record_reverse_evidence", "export_rebuild_bundle", "finalize_task"}
        if not required.issubset(names):
            raise RuntimeError(f"required tools missing: {sorted(required - set(names))}")
        orphan_cleanup = maybe_cleanup_fixture_orphans(
            args.surface_only,
            home,
            client,
            args.timeout,
        )
        health = client.tool("check_browser_health", {})
        health_data = health.get("data") or {}
        results.update({
            "initialize": initialized["serverInfo"],
            "tools_count": len(names),
            "orphan_cleanup": orphan_cleanup,
            "orphan_cleanup_count": orphan_cleanup["closed_count"],
            "health": {
                **selected_fields(health_data, ("mode", "ok", "pages_count", "transport")),
                "ready": (health_data.get("readiness") or {}).get("ready"),
                "reason": (health_data.get("readiness") or {}).get("reason"),
            },
        })
        if not args.surface_only:
            server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
            server_thread = threading.Thread(target=server.serve_forever, daemon=True)
            server_thread.start()
            url = f"http://127.0.0.1:{server.server_port}/fixture"
            new_page = client.tool("new_page", {
                "url": url, "workspace_key": workspace_key, "task_id": task_id,
                "fresh": True, "reuse": False, "ownership_policy": "fresh", "keep": False,
            })
            selected = page_id(new_page)
            if not selected:
                raise RuntimeError("new_page did not expose a managed tab id")
            route = {"workspace_key": workspace_key, "task_id": task_id}
            if selected:
                route["page_id"] = selected
            evidence = client.tool("record_reverse_evidence", {
                **route,
                "channel": "reverse-craft-gate",
                "evidence": {"source": "dom", "confidence": "exact", "data": {"fixture": "reverse-craft", "url": url}},
            })
            rebuild = client.tool("export_rebuild_bundle", route)
            finalized = client.tool("finalize_task", {
                "workspace_key": workspace_key, "task_id": task_id, "scope": "task", "prune_stale": False,
            })
            evidence_data = evidence.get("data") or {}
            rebuild_data = rebuild.get("data") or {}
            finalized_data = finalized.get("data") or {}
            evidence_path = Path(str(evidence_data.get("path", "")))
            rebuild_files = [Path(str(path)) for path in rebuild_data.get("files", [])]
            if not evidence_path.is_file():
                raise RuntimeError("record_reverse_evidence did not create its artifact")
            if len(rebuild_files) != 4 or not all(path.is_file() for path in rebuild_files):
                raise RuntimeError("export_rebuild_bundle did not create the four-file bundle")
            cleanup = finalized_data.get("cleanup_summary") or {}
            if cleanup.get("closed_count", 0) < 1 or cleanup.get("close_error_count", 0) != 0:
                raise RuntimeError(f"finalize_task did not close the fixture cleanly: {cleanup}")
            results["fixture"] = {
                "url": url, "page_id": selected,
                "evidence": {
                    **selected_fields(evidence_data, ("evidence_id", "channel")),
                    "artifact_sha256": file_sha256(evidence_path),
                },
                "rebuild": {
                    "files_count": len(rebuild_files),
                    "manifest_sha256": hashlib.sha256("".join(file_sha256(path) for path in sorted(rebuild_files)).encode()).hexdigest(),
                },
                "finalize": selected_fields(cleanup, ("scope", "closed_count", "close_error_count", "remaining_kept_count", "remaining_unkept_count")),
            }
        payload = {
            "schema": "reverse-craft.browser67-mcp-gate.v1", "valid": True,
            "browser67": {"path": str(home), "head": head, "expected_head": EXPECTED_COMMIT},
            "surface_only": args.surface_only, "results": results,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        payload = {
            "schema": "reverse-craft.browser67-mcp-gate.v1", "valid": False,
            "error": f"{type(exc).__name__}: {exc}", "results": results,
            "stderr_tail": client.stderr[-20:] if client else [],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 1
    finally:
        if client:
            try:
                # Best-effort cleanup if a prior live step failed.
                if not args.surface_only:
                    client.tool("finalize_task", {
                        "workspace_key": workspace_key, "task_id": task_id, "scope": "task", "prune_stale": False,
                    })
            except Exception:
                pass
            client.close()
        if server:
            server.shutdown()
            server.server_close()
        if server_thread:
            server_thread.join(timeout=2)


if __name__ == "__main__":
    raise SystemExit(main())
