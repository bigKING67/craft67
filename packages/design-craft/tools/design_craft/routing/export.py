from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path

from .path_policy import (
    validate_export_destination,
    validate_manifest_source_path,
)
from .manifest import sha256_file


def copy_pack(source_root: Path, export_dir: Path, files: list[dict], dry_run: bool) -> list[str]:
    verified: list[tuple[dict, Path, Path, int, str]] = []
    for item in files:
        source = validate_manifest_source_path(source_root, item["path"])
        if not source.is_file():
            continue
        expected_size = item.get("size_bytes")
        expected_digest = item.get("sha256")
        if not isinstance(expected_size, int) or not isinstance(expected_digest, str):
            raise ValueError(
                f"route-pack file entry is missing integrity metadata: {item['path']!r}"
            )
        if source.stat().st_size != expected_size or sha256_file(source) != expected_digest:
            raise ValueError(f"route-pack source changed after validation: {item['path']!r}")
        destination = validate_export_destination(export_dir, item["path"])
        verified.append((item, source, destination, expected_size, expected_digest))

    if dry_run:
        return [item["path"] for item, *_ in verified]

    staged: list[tuple[dict, Path, Path]] = []
    try:
        for item, source, destination, expected_size, expected_digest in verified:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination = validate_export_destination(export_dir, item["path"])
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{destination.name}.",
                suffix=".tmp",
                dir=destination.parent,
            )
            os.close(descriptor)
            temporary = Path(temporary_name)
            staged.append((item, temporary, destination))
            shutil.copy2(source, temporary)
            if (
                temporary.stat().st_size != expected_size
                or sha256_file(temporary) != expected_digest
            ):
                raise ValueError(f"route-pack export integrity check failed: {item['path']!r}")

        copied: list[str] = []
        for item, temporary, destination in staged:
            os.replace(temporary, destination)
            copied.append(item["path"])
        return copied
    finally:
        for _, temporary, _ in staged:
            temporary.unlink(missing_ok=True)


def write_manifest(payload: dict, manifest_path: Path, dry_run: bool) -> None:
    if dry_run:
        return
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{manifest_path.name}.",
        suffix=".tmp",
        dir=manifest_path.parent,
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, manifest_path)
    finally:
        temporary.unlink(missing_ok=True)
