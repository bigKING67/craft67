#!/usr/bin/env python3
"""Safely unpack and exercise the exact npm release package."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path, PurePosixPath

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from host_smoke import run_reference_runtime_e2e

MAX_ARCHIVE_MEMBERS = 1_000
# Shared with the npm dry-run boundary. Re-measured 2026-10-05: 658,544 bytes
# across 98 files, 1.4 KB under the previous 660,000 limit. Growth is scripts
# and READMEs, which agents do not load into context; no executor, dependency
# or dist artifact is packaged. The limit guards against accidental inclusion,
# so keep ~6% headroom. Compressed-size, member-count and safe-path limits apply.
MAX_ARCHIVE_BYTES = 700_000


def validated_members(archive: tarfile.TarFile) -> list[tarfile.TarInfo]:
    members = archive.getmembers()
    if not members:
        raise ValueError("package archive is empty")
    if len(members) > MAX_ARCHIVE_MEMBERS:
        raise ValueError(
            f"package archive has {len(members)} members; limit is {MAX_ARCHIVE_MEMBERS}"
        )

    total_bytes = 0
    seen: set[str] = set()
    for member in members:
        name = member.name.rstrip("/")
        if not name or "\\" in name or "\x00" in name:
            raise ValueError(f"unsafe package member path: {member.name!r}")
        raw_parts = name.split("/")
        path = PurePosixPath(name)
        if (
            path.is_absolute()
            or any(part in {"", ".", ".."} for part in raw_parts)
            or not path.parts
            or path.parts[0] != "package"
        ):
            raise ValueError(f"unsafe package member path: {member.name!r}")
        normalized = path.as_posix()
        if normalized in seen:
            raise ValueError(f"duplicate package member path: {normalized}")
        seen.add(normalized)
        if member.issym() or member.islnk():
            raise ValueError(f"package member links are not allowed: {normalized}")
        if not member.isdir() and not member.isfile():
            raise ValueError(f"unsupported package member type: {normalized}")
        if member.size < 0:
            raise ValueError(f"invalid package member size: {normalized}")
        total_bytes += member.size
        if total_bytes > MAX_ARCHIVE_BYTES:
            raise ValueError(
                f"package archive expands beyond {MAX_ARCHIVE_BYTES} bytes"
            )
    return members


def safe_extract_package(package: Path, destination: Path) -> None:
    """Extract regular files and directories after validating the whole archive."""
    destination.mkdir(parents=True, exist_ok=True)
    destination_root = destination.resolve()
    with tarfile.open(package, mode="r:gz") as archive:
        members = validated_members(archive)
        for member in members:
            path = PurePosixPath(member.name.rstrip("/"))
            target = destination.joinpath(*path.parts)
            if not target.resolve(strict=False).is_relative_to(destination_root):
                raise ValueError(f"package member escapes extraction root: {member.name!r}")
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            source = archive.extractfile(member)
            if source is None:
                raise ValueError(f"package member has no file payload: {member.name!r}")
            with source, target.open("xb") as output:
                shutil.copyfileobj(source, output)


def run_runtime_self_test(installed: Path) -> tuple[bool, str]:
    completed = subprocess.run(
        [
            sys.executable,
            str(installed / "scripts/creative_craft.py"),
            "self-test",
            "--scope",
            "runtime",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return False, completed.stderr.strip() or completed.stdout.strip()
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        return False, f"invalid JSON: {exc}"
    if not isinstance(payload, dict):
        return False, "runtime self-test JSON must be an object"
    if payload.get("scope") != "runtime" or payload.get("runtime_valid") is not True:
        return False, "runtime self-test did not report a valid runtime scope"
    return True, ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    package = Path(args.package).expanduser().resolve()
    checks: list[str] = []
    errors: list[str] = []

    if not package.is_file():
        errors.append(f"package does not exist: {package.name}")
    else:
        try:
            with tempfile.TemporaryDirectory() as directory:
                temp_root = Path(directory)
                extracted = temp_root / "extracted"
                safe_extract_package(package, extracted)
                checks.append("safe-package-extraction")

                package_root = extracted / "package"
                installed = package_root / "skills/creative-craft"
                package_json_path = package_root / "package.json"
                version_path = installed / "VERSION"
                if not package_json_path.is_file() or not version_path.is_file():
                    errors.append("package identity files are missing")
                else:
                    metadata = json.loads(package_json_path.read_text(encoding="utf-8"))
                    leaf_version = version_path.read_text(encoding="utf-8").strip()
                    if not isinstance(metadata, dict):
                        errors.append("package.json must contain a JSON object")
                    elif (
                        metadata.get("name") != "@bigking67/creative-craft"
                        or metadata.get("version") != leaf_version
                    ):
                        errors.append("package name or skill version is inconsistent")
                    else:
                        checks.append("package-identity")

                cli_path = installed / "scripts/creative_craft.py"
                if not (installed / "SKILL.md").is_file() or not cli_path.is_file():
                    errors.append("packaged Creative Craft skill leaf is incomplete")
                else:
                    self_test_ok, self_test_error = run_runtime_self_test(installed)
                    if not self_test_ok:
                        errors.append(
                            "packaged runtime self-test failed: " + self_test_error
                        )
                    else:
                        checks.append("packaged-runtime-self-test")
                        workspace = temp_root / "runtime-workspace"
                        workspace.mkdir()
                        reference_checks, reference_errors = run_reference_runtime_e2e(
                            installed,
                            workspace,
                            check_prefix="packaged",
                        )
                        checks.extend(reference_checks)
                        errors.extend(reference_errors)
        except (OSError, tarfile.TarError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"package smoke failed closed: {exc}")

    payload = {
        "schema_version": "creative-craft.package-smoke.v1",
        "valid": not errors,
        "package": package.name,
        "checks": checks,
        "errors": errors,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("PASS packaged runtime smoke" if not errors else "FAIL packaged runtime smoke")
        for check in checks:
            print(f"  PASS: {check}")
        for error in errors:
            print(f"  ERROR: {error}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
