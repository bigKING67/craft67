from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path

from ..repo import REPO_ROOT


def _completed(
    command: list[str],
    *,
    env: dict[str, str] | None = None,
    cwd: Path = REPO_ROOT,
    timeout: int = 120,
) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    if env:
        environment.update(env)
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"benchmark command could not complete: {' '.join(command)}: {exc}") from exc


def _run(
    command: list[str],
    *,
    env: dict[str, str] | None = None,
    cwd: Path = REPO_ROOT,
    timeout: int = 120,
) -> subprocess.CompletedProcess[str]:
    result = _completed(command, env=env, cwd=cwd, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(
            f"benchmark command failed ({result.returncode}): {' '.join(command)}: "
            + (result.stderr.strip() or result.stdout.strip() or "no process output")
        )
    return result


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            relative = path.relative_to(root).as_posix()
            digest.update(relative.encode("utf-8"))
            digest.update(b"\0")
            digest.update(hashlib.sha256(path.read_bytes()).digest())
            digest.update(b"\n")
    return digest.hexdigest()


def _create_tree(root: Path, count: int) -> None:
    for index in range(count):
        bucket = root / f"d{index // 1000:03d}"
        bucket.mkdir(exist_ok=True)
        (bucket / f"f{index:06d}.txt").write_text(
            f"design-craft benchmark fixture {index}\n", encoding="utf-8"
        )


def _create_validation_fixture(root: Path, count: int = 100) -> list[Path]:
    paths: list[Path] = []
    for index in range(count):
        if index % 3 == 0:
            path = root / f"case_{index:03d}.py"
            content = f"VALUE_{index} = {index}\n"
        elif index % 3 == 1:
            path = root / f"case_{index:03d}.json"
            content = json.dumps({"case": index, "valid": True}) + "\n"
        else:
            path = root / f"case_{index:03d}.md"
            content = f"# Fixture {index}\n\nValidated content.\n"
        path.write_text(content, encoding="utf-8")
        paths.append(path)
    return paths


def _safe_regular_file(root: Path, path: Path) -> Path:
    root = root.resolve()
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"benchmark fixture must be a regular non-symlink file: {path}")
    resolved = path.resolve(strict=True)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"benchmark fixture escapes its temporary root: {path}") from exc
    return resolved


def _validate_changed_files(root: Path, paths: list[Path]) -> str:
    if not paths:
        raise ValueError("incremental validation requires at least one changed file")
    digest = hashlib.sha256()
    seen: set[Path] = set()
    for path in paths:
        resolved = _safe_regular_file(root, path)
        if resolved in seen:
            raise ValueError(f"incremental validation contains a duplicate path: {path}")
        seen.add(resolved)
        content = resolved.read_bytes()
        text = content.decode("utf-8")
        if resolved.suffix == ".py":
            compile(text, str(resolved), "exec")
        elif resolved.suffix == ".json":
            payload = json.loads(text)
            if not isinstance(payload, dict):
                raise ValueError(f"incremental JSON fixture must be an object: {resolved}")
        digest.update(resolved.relative_to(root.resolve()).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(content).digest())
        digest.update(b"\n")
    return digest.hexdigest()


class _BoundedDigestCache:
    def __init__(self, root: Path, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("cache capacity must be positive")
        self.root = root.resolve()
        self.capacity = capacity
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.max_entries_observed = 0
        self._entries: OrderedDict[
            str, tuple[tuple[int, int, int, int, int], str]
        ] = OrderedDict()

    def digest(self, path: Path) -> str:
        resolved = _safe_regular_file(self.root, path)
        relative = resolved.relative_to(self.root).as_posix()
        metadata = resolved.stat()
        signature = (
            metadata.st_dev,
            metadata.st_ino,
            metadata.st_size,
            metadata.st_mtime_ns,
            metadata.st_ctime_ns,
        )
        cached = self._entries.get(relative)
        if cached is not None and cached[0] == signature:
            self.hits += 1
            self._entries.move_to_end(relative)
            return cached[1]
        self.misses += 1
        value = hashlib.sha256(resolved.read_bytes()).hexdigest()
        if relative in self._entries:
            del self._entries[relative]
        self._entries[relative] = (signature, value)
        if len(self._entries) > self.capacity:
            self._entries.popitem(last=False)
            self.evictions += 1
        self.max_entries_observed = max(self.max_entries_observed, len(self._entries))
        return value

    @property
    def entries(self) -> int:
        return len(self._entries)

    def reset_counters(self) -> None:
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.max_entries_observed = len(self._entries)



def _copy_install_fixture(destination: Path) -> None:
    (destination / "scripts").mkdir(parents=True)
    shutil.copytree(REPO_ROOT / "skills/design-craft", destination / "skills/design-craft")
    for relative in (
        "tools/__init__.py",
        "tools/design_craft/__init__.py",
        "tools/design_craft/repo.py",
        "CHANGELOG.md",
        "VERSION",
        "scripts/install_local.sh",
        "scripts/design_craft_install_verify.py",
        "scripts/design_craft_evidence_common.py",
    ):
        source = REPO_ROOT / relative
        destination_path = destination / relative
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination_path)


def _install_command(install_fixture: Path) -> list[str]:
    return [
        "bash",
        str(install_fixture / "scripts/install_local.sh"),
        "--keep-backups",
        "2",
    ]


def _release_bundle_once(output_root: Path) -> tuple[int, str]:
    _run([sys.executable, "scripts/design_craft_package_validate.py", "--validate"])
    output_root.mkdir(parents=True, exist_ok=False)
    result = _run(
        [
            "npm",
            "pack",
            "--json",
            "--ignore-scripts",
            "--pack-destination",
            str(output_root),
        ]
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"npm pack emitted invalid JSON: {exc}") from exc
    if not isinstance(payload, list) or len(payload) != 1 or not isinstance(payload[0], dict):
        raise RuntimeError("npm pack must emit exactly one package record")
    package = output_root / str(payload[0].get("filename", ""))
    if package.is_symlink() or not package.is_file() or package.stat().st_size <= 0:
        raise RuntimeError("release bundle benchmark did not produce a regular package")
    return package.stat().st_size, hashlib.sha256(package.read_bytes()).hexdigest()
