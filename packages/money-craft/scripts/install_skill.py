#!/usr/bin/env python3
"""Atomically install the canonical Money Craft skill into a host directory."""

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
SOURCE = ROOT / "skills" / "money-craft"
DEFAULT_ROOTS = {
    "agents": Path.home() / ".agents" / "skills",
    "codex": Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "skills",
    "claude": Path.home() / ".claude" / "skills",
    "grok": Path.home() / ".grok" / "skills",
    "pi": Path.home() / ".pi" / "agent" / "skills",
}


def tree_sha256(root: Path, *, excluded_names: set[str] | None = None) -> str:
    excluded_names = excluded_names or set()
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        if "__pycache__" in path.parts or path.suffix == ".pyc" or path.name in excluded_names:
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
        ["git", "status", "--porcelain", "--untracked-files=all", "--", "skills/money-craft"],
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
    completed = subprocess.run(
        [sys.executable, str(staging / "scripts" / "money_craft.py"), "self-test", "--json"],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ValueError(completed.stderr.strip() or completed.stdout.strip() or "staging self-test failed")


def install(target_root: Path, force: bool) -> tuple[Path, Path | None]:
    if SOURCE.is_symlink() or not SOURCE.is_dir():
        raise ValueError("canonical skill source is missing or is a symlink")
    target_root.mkdir(parents=True, exist_ok=True)
    if target_root.is_symlink() or not target_root.is_dir():
        raise ValueError("target root must be a real directory")
    destination = target_root / "money-craft"
    if destination.exists() and not force:
        raise ValueError(f"destination exists: {destination}; use --force after review")
    staging = target_root / f".money-craft.staging.{uuid.uuid4().hex}"
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup_root = target_root.parent / f".{target_root.name}-backups"
    backup = backup_root / f"money-craft.{timestamp}"
    backup_created = False
    try:
        shutil.copytree(SOURCE, staging, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        provenance = {
            "schema": "money-craft.install-provenance.v1",
            "installed_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
            "version": (SOURCE / "VERSION").read_text(encoding="utf-8").strip(),
            "source_repository": "https://github.com/bigKING67/money-craft",
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
            backup_root.mkdir(mode=0o700, parents=False, exist_ok=True)
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=[*DEFAULT_ROOTS, "custom"], required=True)
    parser.add_argument("--target-root")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.host == "custom" and not args.target_root:
        parser.error("--host custom requires --target-root")
    target_root = (
        Path(args.target_root).expanduser().resolve()
        if args.target_root
        else DEFAULT_ROOTS[args.host].expanduser().resolve()
    )
    try:
        destination, backup = install(target_root, args.force)
    except (OSError, ValueError) as exc:
        payload = {"schema": "money-craft.install.v1", "ok": False, "error": str(exc)}
        print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else f"ERROR: {exc}")
        return 1
    payload = {
        "schema": "money-craft.install.v1",
        "ok": True,
        "host": args.host,
        "destination": str(destination),
        "backup": str(backup) if backup else None,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else str(destination))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
