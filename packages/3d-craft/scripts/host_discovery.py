#!/usr/bin/env python3
"""Verify credential-free 3d-craft discovery in supported Agent hosts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
HOSTS = ("codex", "pi", "grok")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    files = sorted(
        (path for path in root.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(root).as_posix(),
    )
    for path in files:
        relative = path.relative_to(root).as_posix()
        digest.update(f"{sha256_file(path)}  ./{relative}\n".encode())
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def collect_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [text for item in value for text in collect_strings(item)]
    if isinstance(value, dict):
        return [text for item in value.values() for text in collect_strings(item)]
    return []


def collect_objects(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [value, *(item for child in value.values() for item in collect_objects(child))]
    if isinstance(value, list):
        return [item for child in value for item in collect_objects(child)]
    return []


def resolved_path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def paths_match(discovered: str | None, expected: Path) -> bool:
    if not discovered:
        return False
    try:
        return resolved_path(discovered) == expected.resolve()
    except (OSError, RuntimeError):
        return False


def run_command(
    command: list[str],
    *,
    cwd: Path,
    timeout_seconds: float,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        input=input_text,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )


def read_version(executable: str, host: str, cwd: Path, timeout_seconds: float) -> tuple[str | None, str | None]:
    try:
        result = run_command([executable, "--version"], cwd=cwd, timeout_seconds=timeout_seconds)
    except subprocess.TimeoutExpired:
        return None, "version command timed out"
    except OSError as error:
        return None, f"version command could not start: {error}"
    output = (result.stdout or result.stderr).strip().splitlines()
    if result.returncode != 0 or not output:
        return None, f"{host} --version returned exit code {result.returncode}"
    return output[0], None


def codex_discovery(stdout: str, expected: Path) -> tuple[str | None, str]:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return None, "Codex prompt-input did not return JSON"
    strings = collect_strings(payload)
    roots: dict[str, str] = {}
    for text in strings:
        for match in re.finditer(r"(?m)^- `(?P<alias>r\d+)` = `(?P<root>[^`]+)`$", text):
            roots[match.group("alias")] = match.group("root")
    discovered: list[str] = []
    for text in strings:
        for match in re.finditer(r"(?m)^- 3d-craft:.*\(file: (?P<path>[^)]+)\)$", text):
            value = match.group("path")
            alias, separator, relative = value.partition("/")
            if separator and alias in roots:
                value = str(Path(roots[alias]) / relative)
            discovered.append(value)
    exact = next((path for path in discovered if paths_match(path, expected)), None)
    if exact:
        return str(resolved_path(exact)), "Codex model-visible Skill list resolves the expected candidate"
    if discovered:
        return str(resolved_path(discovered[0])), "Codex resolved 3d-craft from a different candidate path"
    return None, "Codex model-visible Skill list does not contain 3d-craft"


def pi_discovery(stdout: str, expected: Path) -> tuple[str | None, str]:
    payloads: list[Any] = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        try:
            payloads.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    commands = [
        item
        for payload in payloads
        for item in collect_objects(payload)
        if item.get("name") == "skill:3d-craft" and item.get("source") == "skill"
    ]
    discovered = [
        item.get("sourceInfo", {}).get("path")
        for item in commands
        if isinstance(item.get("sourceInfo"), dict)
        and isinstance(item.get("sourceInfo", {}).get("path"), str)
    ]
    exact = next((path for path in discovered if paths_match(path, expected)), None)
    if exact:
        return str(resolved_path(exact)), "Pi offline RPC registered skill:3d-craft from the expected candidate"
    if discovered:
        return str(resolved_path(discovered[0])), "Pi registered 3d-craft from a different candidate path"
    if commands:
        return None, "Pi registered skill:3d-craft without candidate path provenance"
    return None, "Pi offline RPC does not contain skill:3d-craft"


def grok_discovery(stdout: str, expected: Path) -> tuple[str | None, str]:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return None, "Grok inspect did not return JSON"
    skills = payload.get("skills", []) if isinstance(payload, dict) else []
    matches = [item for item in skills if isinstance(item, dict) and item.get("name") == "3d-craft"]
    discovered = [
        item.get("source", {}).get("path")
        for item in matches
        if isinstance(item.get("source"), dict)
        and isinstance(item.get("source", {}).get("path"), str)
    ]
    exact = next((path for path in discovered if paths_match(path, expected)), None)
    if exact:
        return str(resolved_path(exact)), "Grok inspect resolves the expected candidate"
    if discovered:
        return str(resolved_path(discovered[0])), "Grok resolved 3d-craft from a different candidate path"
    if matches:
        return None, "Grok resolved 3d-craft without candidate path provenance"
    return None, "Grok inspect does not contain 3d-craft"


def inspect_host(host: str, expected: Path, workspace: Path, timeout_seconds: float) -> dict[str, Any]:
    executable = shutil.which(host)
    invocation = {
        "status": "UNVERIFIED",
        "reason": "model invocation was not run and is not required for installation acceptance",
    }
    if not executable:
        return {
            "host": host,
            "version": None,
            "discovery": "UNVERIFIED",
            "discovered_skill": None,
            "detail": f"{host} executable is unavailable",
            "invocation": invocation,
        }

    version, version_error = read_version(executable, host, workspace, timeout_seconds)
    commands: dict[str, list[str]] = {
        "codex": [executable, "debug", "prompt-input"],
        "pi": [
            executable,
            "--mode",
            "rpc",
            "--no-session",
            "--offline",
            "--no-extensions",
            "--no-prompt-templates",
            "--no-context-files",
            "--no-tools",
        ],
        "grok": [executable, "inspect", "--json"],
    }
    parsers: dict[str, Callable[[str, Path], tuple[str | None, str]]] = {
        "codex": codex_discovery,
        "pi": pi_discovery,
        "grok": grok_discovery,
    }
    input_text = '{"type":"get_commands"}\n' if host == "pi" else None
    try:
        result = run_command(
            commands[host],
            cwd=workspace,
            timeout_seconds=timeout_seconds,
            input_text=input_text,
        )
    except subprocess.TimeoutExpired:
        return {
            "host": host,
            "version": version,
            "discovery": "FAIL",
            "discovered_skill": None,
            "detail": f"{host} discovery command timed out",
            "invocation": invocation,
        }
    except OSError as error:
        return {
            "host": host,
            "version": version,
            "discovery": "FAIL",
            "discovered_skill": None,
            "detail": f"{host} discovery command could not start: {error}",
            "invocation": invocation,
        }

    if result.returncode != 0:
        return {
            "host": host,
            "version": version,
            "discovery": "FAIL",
            "discovered_skill": None,
            "detail": f"{host} discovery returned exit code {result.returncode}",
            "invocation": invocation,
        }

    discovered, detail = parsers[host](result.stdout, expected)
    status = "PASS" if paths_match(discovered, expected) and not version_error else "FAIL"
    if version_error:
        detail = f"{detail}; {version_error}"
    return {
        "host": host,
        "version": version,
        "discovery": status,
        "discovered_skill": discovered,
        "detail": detail,
        "invocation": invocation,
    }


def output_path(value: str | None) -> Path | None:
    if value is None:
        return None
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise ValueError("output must be an absolute path")
    path = path.resolve()
    if path == ROOT or ROOT in path.parents:
        raise ValueError("host discovery output must remain outside the source repository")
    if path.exists():
        raise ValueError(f"output already exists: {path}")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify Codex, Pi, and Grok Skill discovery without invoking a model or accessing credentials."
    )
    parser.add_argument(
        "--skill-root",
        default=str(Path.home() / ".agents" / "skills" / "3d-craft"),
        help="Installed or isolated 3d-craft Skill directory",
    )
    parser.add_argument("--workspace", default=str(Path.cwd()), help="Workspace from which each host performs discovery")
    parser.add_argument("--host", action="append", choices=HOSTS, help="Host to check; repeat as needed (default: all)")
    parser.add_argument("--timeout-seconds", type=float, default=20.0)
    parser.add_argument("--output", help="Optional absolute JSON receipt path outside this repository")
    parser.add_argument("--json", action="store_true", help="Print the full receipt as JSON")
    args = parser.parse_args()

    try:
        skill_root = Path(args.skill_root).expanduser().resolve()
        workspace = Path(args.workspace).expanduser().resolve()
        receipt_path = output_path(args.output)
        if not skill_root.is_dir() or not (skill_root / "SKILL.md").is_file():
            raise ValueError(f"skill root is missing SKILL.md: {skill_root}")
        if not workspace.is_dir():
            raise ValueError(f"workspace does not exist: {workspace}")
        if args.timeout_seconds <= 0 or args.timeout_seconds > 120:
            raise ValueError("timeout-seconds must be greater than 0 and at most 120")
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2

    selected_hosts = list(dict.fromkeys(args.host or HOSTS))
    expected_skill = (skill_root / "SKILL.md").resolve()
    hosts = [inspect_host(host, expected_skill, workspace, args.timeout_seconds) for host in selected_hosts]
    statuses = [item["discovery"] for item in hosts]
    status = "FAIL" if "FAIL" in statuses else "UNVERIFIED" if "UNVERIFIED" in statuses else "PASS"
    payload = {
        "schema": "3d-craft.host-discovery.v1",
        "status": status,
        "verified_at": utc_now(),
        "workspace": str(workspace),
        "candidate": {
            "skill_root": str(skill_root),
            "skill_file": str(expected_skill),
            "tree_sha256": tree_sha256(skill_root),
        },
        "hosts": hosts,
        "security": {
            "model_invocation": "NOT_RUN",
            "credential_access": "NOT_REQUESTED",
            "configuration_mutation": "NOT_RUN",
        },
    }

    if receipt_path:
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"{status}: {len([item for item in hosts if item['discovery'] == 'PASS'])}/{len(hosts)} hosts discovered {expected_skill}")
        if receipt_path:
            print(f"receipt={receipt_path}")
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
