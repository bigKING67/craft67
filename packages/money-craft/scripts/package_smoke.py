#!/usr/bin/env python3
"""Safely extract and exercise the exact Money Craft npm package."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MAX_COMPRESSED_BYTES = 1 * 1024 * 1024
MAX_UNPACKED_BYTES = 2 * 1024 * 1024
MAX_MEMBERS = 100


def validated_members(archive: tarfile.TarFile) -> list[tarfile.TarInfo]:
    members = archive.getmembers()
    if not members or len(members) > MAX_MEMBERS:
        raise ValueError(f"archive member count must be 1..{MAX_MEMBERS}")
    total = 0
    seen: set[str] = set()
    for member in members:
        name = member.name.rstrip("/")
        parts = name.split("/")
        path = PurePosixPath(name)
        if (
            not name
            or "\\" in name
            or "\x00" in name
            or path.is_absolute()
            or any(part in {"", ".", ".."} for part in parts)
            or not path.parts
            or path.parts[0] != "package"
        ):
            raise ValueError(f"unsafe package member: {member.name!r}")
        if name in seen:
            raise ValueError(f"duplicate package member: {name}")
        seen.add(name)
        if member.issym() or member.islnk() or (not member.isfile() and not member.isdir()):
            raise ValueError(f"unsupported package member type: {name}")
        if "upstreams/" in name or "/reports/" in name or "/captures/" in name:
            raise ValueError(f"excluded content is packaged: {name}")
        total += member.size
        if total > MAX_UNPACKED_BYTES:
            raise ValueError("package exceeds unpacked size limit")
    return members


def safe_extract(package: Path, destination: Path) -> None:
    if package.stat().st_size > MAX_COMPRESSED_BYTES:
        raise ValueError("package exceeds compressed size limit")
    destination.mkdir(parents=True)
    root = destination.resolve()
    with tarfile.open(package, "r:gz") as archive:
        members = validated_members(archive)
        for member in members:
            relative = PurePosixPath(member.name.rstrip("/"))
            target = destination.joinpath(*relative.parts)
            if not target.resolve(strict=False).is_relative_to(root):
                raise ValueError(f"package member escapes destination: {member.name}")
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            source = archive.extractfile(member)
            if source is None:
                raise ValueError(f"missing payload: {member.name}")
            with source, target.open("xb") as output:
                shutil.copyfileobj(source, output)


def run_json(command: list[str], cwd: Path) -> tuple[int, dict[str, Any] | None, str]:
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    raw = completed.stdout.strip()
    try:
        payload = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        payload = None
    return completed.returncode, payload, completed.stderr.strip() or raw


def make_package(destination: Path) -> Path:
    code, payload, output = run_json(["npm", "pack", "--json", "--pack-destination", str(destination)], ROOT)
    if code or not isinstance(payload, list) or len(payload) != 1:
        raise ValueError(f"npm pack failed: {output}")
    filename = payload[0].get("filename")
    if not isinstance(filename, str):
        raise ValueError("npm pack did not return filename")
    return destination / filename


def smoke(package: Path) -> dict[str, Any]:
    checks: list[str] = []
    errors: list[str] = []
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            extracted = temp / "extracted"
            safe_extract(package, extracted)
            checks.append("safe-extraction")
            package_root = extracted / "package"
            metadata = json.loads((package_root / "package.json").read_text(encoding="utf-8"))
            leaf = package_root / "skills" / "money-craft"
            version = (leaf / "VERSION").read_text(encoding="utf-8").strip()
            if metadata.get("name") != "@bigking67/money-craft" or metadata.get("version") != version:
                raise ValueError("package identity mismatch")
            for relative in (
                ".env.example",
                ".codex-plugin/plugin.json",
                ".claude-plugin/plugin.json",
                ".grok-plugin/plugin.json",
                "LICENSES/AI-BERKSHIRE-MIT.txt",
                "skills/money-craft/SKILL.md",
                "scripts/install_skill.py",
            ):
                if not (package_root / relative).is_file():
                    raise ValueError(f"missing packaged file: {relative}")
            checks.append("package-identity")
            code, payload, output = run_json(
                [sys.executable, str(leaf / "scripts" / "money_craft.py"), "self-test", "--json"],
                package_root,
            )
            if code or not isinstance(payload, dict) or payload.get("runtime_valid") is not True:
                raise ValueError(f"packaged runtime self-test failed: {output}")
            checks.append("packaged-runtime-self-test")
            install_root = temp / "installed-skills"
            code, payload, output = run_json(
                [
                    sys.executable,
                    str(package_root / "scripts" / "install_skill.py"),
                    "--host",
                    "custom",
                    "--target-root",
                    str(install_root),
                    "--json",
                ],
                package_root,
            )
            installed = install_root / "money-craft"
            if code or not isinstance(payload, dict) or payload.get("ok") is not True:
                raise ValueError(f"packaged installer failed: {output}")
            if not (installed / "INSTALL_PROVENANCE.json").is_file():
                raise ValueError("installed provenance is missing")
            code, payload, output = run_json(
                [sys.executable, str(installed / "scripts" / "money_craft.py"), "self-test", "--json"],
                temp,
            )
            if code or not isinstance(payload, dict) or payload.get("runtime_valid") is not True:
                raise ValueError(f"installed runtime self-test failed: {output}")
            checks.extend(["atomic-install", "installed-runtime-self-test"])
            research_workspace = temp / "research-run"
            code, payload, output = run_json(
                [
                    sys.executable,
                    str(installed / "scripts" / "money_craft.py"),
                    "research",
                    "init",
                    "--security",
                    "Example Company",
                    "--security-id",
                    "US-NASDAQ:EXAMPLE",
                    "--base-currency",
                    "USD",
                    "--as-of",
                    "2026-08-23",
                    "--latest-report",
                    "2026-2",
                    "--latest-report-end",
                    "2026-06-30",
                    "--latest-annual-report",
                    "2025-4",
                    "--provider-mode",
                    "disabled",
                    "--workspace",
                    str(research_workspace),
                    "--json",
                ],
                temp,
            )
            if code or not isinstance(payload, dict) or payload.get("schema") != "money-craft.research-init.v1":
                raise ValueError(f"installed research init failed: {output}")
            code, payload, output = run_json(
                [
                    sys.executable,
                    str(installed / "scripts" / "money_craft.py"),
                    "research",
                    "status",
                    "--workspace",
                    str(research_workspace),
                    "--json",
                ],
                temp,
            )
            if (
                code
                or not isinstance(payload, dict)
                or payload.get("schema") != "money-craft.research-status.v1"
                or payload.get("network_used_by_status") is not False
                or len(payload.get("missing_sources", [])) != 3
                or payload.get("identity", {}).get("security_id") != "US-NASDAQ:EXAMPLE"
            ):
                raise ValueError(f"installed research status failed: {output}")
            checks.append("installed-research-run-smoke")
            from earnings_smoke import run_smoke
            earnings = run_smoke(installed / "scripts" / "money_craft.py")
            if earnings.get("valid") is not True:
                raise ValueError("installed earnings pipeline failed")
            checks.append("installed-earnings-pipeline-smoke")
    except (OSError, ValueError, tarfile.TarError, json.JSONDecodeError) as exc:
        errors.append(str(exc))
    return {
        "schema": "money-craft.package-smoke.v1",
        "valid": not errors,
        "package": package.name,
        "checks": checks,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.package:
        package = Path(args.package).expanduser().resolve()
        payload = smoke(package)
    else:
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                package = make_package(Path(temp_dir))
                payload = smoke(package)
            except (OSError, ValueError) as exc:
                payload = {
                    "schema": "money-craft.package-smoke.v1",
                    "valid": False,
                    "package": None,
                    "checks": [],
                    "errors": [str(exc)],
                }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
