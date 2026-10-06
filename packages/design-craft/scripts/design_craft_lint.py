#!/usr/bin/env python3
"""Run dependency-free syntax and data-contract lint checks."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


SCHEMA = "design-craft.lint.v1"
ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {
    ".git",
    ".gradle",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "upstreams",
}


def paths_by_suffix(suffixes: tuple[str, ...]) -> dict[str, list[Path]]:
    paths = {suffix: [] for suffix in suffixes}
    for directory, directory_names, file_names in os.walk(ROOT):
        directory_names[:] = sorted(
            name for name in directory_names if name not in EXCLUDED_PARTS
        )
        current = Path(directory)
        for name in sorted(file_names):
            suffix = Path(name).suffix
            if suffix in paths:
                paths[suffix].append(current / name)
    return paths


def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    payload: dict[str, object] = {}
    for key, value in pairs:
        if key in payload:
            raise ValueError(f"duplicate JSON key: {key}")
        payload[key] = value
    return payload


def python_errors(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in paths:
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except (OSError, SyntaxError, UnicodeDecodeError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: Python syntax error: {exc}")
    return errors


def json_errors(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in paths:
        try:
            json.loads(
                path.read_text(encoding="utf-8"),
                object_pairs_hook=unique_object,
            )
        except (OSError, ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: invalid JSON: {exc}")
    return errors


def resolve_command(name: str) -> str | None:
    configured = os.environ.get("DESIGN_CRAFT_BASH") if name == "bash" else None
    resolved = shutil.which(configured or name)
    if name == "bash" and resolved and os.name == "nt":
        normalized = resolved.replace("\\", "/").lower()
        if normalized.endswith("/windows/system32/bash.exe"):
            return None
    return resolved


def command_errors(command: list[str], paths: list[Path], label: str) -> list[str]:
    if not paths:
        return []
    executable = resolve_command(command[0])
    if not executable:
        guidance = ""
        if command[0] == "bash" and os.name == "nt":
            guidance = "; set DESIGN_CRAFT_BASH to Git for Windows bash.exe"
        return [f"{command[0]} is required for {label} lint{guidance}"]
    def check(path: Path) -> str | None:
        result = subprocess.run(
            [executable, *command[1:], str(path)],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or "syntax check failed"
            return f"{path.relative_to(ROOT)}: {label}: {detail}"
        return None

    workers = min(8, len(paths))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        results = executor.map(check, paths)
        return [error for error in results if error is not None]


def validate() -> dict:
    paths = paths_by_suffix((".py", ".sh", ".json", ".cjs"))
    python_paths = paths[".py"]
    shell_paths = paths[".sh"]
    json_paths = paths[".json"]
    node_paths = paths[".cjs"]
    errors = [
        *python_errors(python_paths),
        *json_errors(json_paths),
        *command_errors(["bash", "-n"], shell_paths, "shell syntax error"),
        *command_errors(["node", "--check"], node_paths, "Node syntax error"),
    ]
    return {
        "schema": SCHEMA,
        "root": str(ROOT),
        "counts": {
            "python": len(python_paths),
            "shell": len(shell_paths),
            "json": len(json_paths),
            "node": len(node_paths),
        },
        "ok": not errors,
        "errors": errors,
    }


def self_check() -> None:
    try:
        compile("def broken(:\n", "fixture.py", "exec")
    except SyntaxError:
        pass
    else:
        raise RuntimeError("lint self-check accepted invalid Python")
    try:
        json.loads('{"key": 1, "key": 2}', object_pairs_hook=unique_object)
    except ValueError:
        pass
    else:
        raise RuntimeError("lint self-check accepted duplicate JSON keys")
    previous_bash = os.environ.get("DESIGN_CRAFT_BASH")
    os.environ["DESIGN_CRAFT_BASH"] = sys.executable
    try:
        if resolve_command("bash") != shutil.which(sys.executable):
            raise RuntimeError("lint self-check ignored DESIGN_CRAFT_BASH")
    finally:
        if previous_bash is None:
            os.environ.pop("DESIGN_CRAFT_BASH", None)
        else:
            os.environ["DESIGN_CRAFT_BASH"] = previous_bash


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.check:
        self_check()
    payload = validate()
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    elif payload["ok"]:
        counts = payload["counts"]
        print(
            "lint verified: "
            + ", ".join(f"{name}={count}" for name, count in counts.items())
        )
    else:
        print("\n".join(payload["errors"]), file=sys.stderr)
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
