#!/usr/bin/env python3
"""Build a deterministic, portable 3d-craft Skill ZIP."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "3d-craft"
VALIDATOR = ROOT / "scripts" / "validate_source.py"
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_files() -> list[Path]:
    files: list[Path] = []
    for path in sorted(SKILL.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_symlink():
            raise ValueError(f"installable Skill must not contain symlinks: {path}")
        if path.is_file():
            files.append(path)
    return files


def validate_source() -> None:
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--skill-root", str(SKILL), "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"source validation failed: {message}")


def build(output: Path) -> dict[str, object]:
    if not output.is_absolute():
        raise ValueError("--output must be an absolute path")
    output = output.resolve()
    if output.suffix.lower() != ".zip":
        raise ValueError("--output must end in .zip")
    if output == ROOT or ROOT in output.parents:
        raise ValueError("package output must remain outside the source repository")

    validate_source()
    files = source_files()
    output.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.name}.", suffix=".tmp", dir=output.parent
    )
    os.close(file_descriptor)
    temporary = Path(temporary_name)

    try:
        with zipfile.ZipFile(temporary, "w") as archive:
            for path in files:
                relative = path.relative_to(SKILL)
                archive_name = (Path("3d-craft") / relative).as_posix()
                executable = bool(path.stat().st_mode & 0o111)
                mode = 0o755 if executable else 0o644
                info = zipfile.ZipInfo(archive_name, date_time=FIXED_ZIP_TIME)
                info.create_system = 3
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (stat.S_IFREG | mode) << 16
                archive.writestr(
                    info,
                    path.read_bytes(),
                    compress_type=zipfile.ZIP_DEFLATED,
                    compresslevel=9,
                )
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)

    version = (SKILL / "VERSION").read_text(encoding="utf-8").strip()
    return {
        "schema": "3d-craft.package.v1",
        "status": "PASS",
        "version": version,
        "artifact": str(output),
        "bytes": output.stat().st_size,
        "files": len(files),
        "sha256": sha256(output),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        payload = build(args.output.expanduser())
    except (OSError, RuntimeError, ValueError) as error:
        print(f"package failed: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            f"PASS: {payload['artifact']} "
            f"sha256={payload['sha256']} files={payload['files']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
