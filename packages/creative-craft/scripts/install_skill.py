#!/usr/bin/env python3
"""Atomically install the canonical Creative Craft skill into a host skill directory."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills" / "creative-craft"


def tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def source_commit() -> str | None:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    value = completed.stdout.strip()
    return value if completed.returncode == 0 and value else None


def source_dirty() -> bool | None:
    completed = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all", "--", "skills/creative-craft"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if completed.returncode != 0:
        return None
    return bool(completed.stdout.strip())


def validate_staging(staging: Path) -> None:
    cli = staging / "scripts" / "creative_craft.py"
    subprocess.run(
        [sys.executable, str(cli), "self-test", "--json"],
        check=True,
        stdout=subprocess.DEVNULL,
    )


def install(target_root: Path, force: bool) -> tuple[Path, Path | None]:
    target_root.mkdir(parents=True, exist_ok=True)
    destination = target_root / "creative-craft"
    if destination.exists() and not force:
        raise ValueError(f"destination exists: {destination}; use --force after review")

    staging = target_root / f".creative-craft.staging.{uuid.uuid4().hex}"
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = target_root / f".creative-craft.backup.{timestamp}"
    backup_created = False
    try:
        shutil.copytree(
            SOURCE,
            staging,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        provenance = {
            "schema_version": "creative-craft.install-provenance.v1",
            "installed_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
            "version": (SOURCE / "VERSION").read_text(encoding="utf-8").strip(),
            "source_repository": "https://github.com/bigKING67/creative-craft",
            "source_commit": source_commit(),
            "source_dirty": source_dirty(),
            "source_skill_sha256": tree_sha256(SOURCE),
            "installer": "scripts/install_skill.py",
        }
        (staging / "INSTALL_PROVENANCE.json").write_text(
            json.dumps(provenance, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        validate_staging(staging)
        if destination.exists():
            if backup.exists():
                raise ValueError(f"backup path already exists: {backup}")
            os.replace(destination, backup)
            backup_created = True
        try:
            os.replace(staging, destination)
        except Exception:
            if backup_created and not destination.exists():
                os.replace(backup, destination)
                backup_created = False
            raise
        return destination, backup if backup_created else None
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--target", required=True,
        help="Host skills directory; creative-craft/ will be created inside it.",
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    try:
        destination, backup = install(Path(args.target).expanduser().resolve(), args.force)
    except (OSError, subprocess.CalledProcessError, ValueError) as exc:
        print(f"ERROR: installation failed: {exc}", file=sys.stderr)
        return 1
    print(destination)
    if backup:
        print(f"Backup: {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
