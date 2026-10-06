#!/usr/bin/env python3
"""Build and atomically install owned skills without pruning unrelated skills."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Iterator


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "skill-pack.json"
BUILDER = ROOT / "tooling/build/build_skill_bundles.py"
INSTALLER_VERSION = "2.2.0"
INSTALL_LOCK_NAME = ".consumer-skill-pack.install.lock"
INSTALL_LOCK_OWNER_NAME = "owner.json"
INSTALL_JOURNAL_NAME = ".consumer-skill-pack.install.json"
INSTALL_JOURNAL_TEMP_NAME = f"{INSTALL_JOURNAL_NAME}.tmp"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tooling.installation.tree_integrity import (
    TreeIntegrityError,
    lexical_absolute,
    tree_hashes,
    validate_real_directory,
    validate_tree,
)
from tooling.manifest import ManifestError, load_manifest, parse_semantic_version


FaultInjector = Callable[[str, Path], None]


def load_install_manifest() -> dict:
    manifest = load_manifest(MANIFEST)
    required = manifest.get("minimum_installer_version", "0.0.0")
    if parse_semantic_version(INSTALLER_VERSION, field="installer version") < parse_semantic_version(
        required, field="minimum_installer_version"
    ):
        raise ValueError(f"installer {INSTALLER_VERSION} is older than required {required}")
    return manifest


def expand_root(value: str) -> Path:
    expanded = Path(os.path.expandvars(os.path.expanduser(value)))
    return lexical_absolute(expanded)


def prepare_install_root(path: Path) -> Path:
    """Create a missing install root only below a fully validated real ancestor."""

    candidate = lexical_absolute(path)
    missing: list[Path] = []
    existing = candidate
    while not os.path.lexists(existing):
        missing.append(existing)
        parent = existing.parent
        if parent == existing:
            raise RuntimeError(f"install root has no existing ancestor: {candidate}")
        existing = parent
    try:
        normalized = validate_real_directory(existing)
    except TreeIntegrityError as exc:
        raise RuntimeError(f"install root must have a real directory ancestor: {candidate}: {exc}") from exc
    for component in reversed(missing):
        normalized /= component.name
        try:
            normalized.mkdir(mode=0o755)
        except FileExistsError:
            pass
        try:
            normalized = validate_real_directory(normalized)
        except TreeIntegrityError as exc:
            raise RuntimeError(f"install root must be a real directory: {candidate}: {exc}") from exc
    return normalized


def path_exists(path: Path) -> bool:
    return os.path.lexists(path)


def remove_path(path: Path) -> None:
    if path.is_symlink() or not path.is_dir():
        path.unlink()
    else:
        shutil.rmtree(path)


def journal_paths(install_root: Path) -> tuple[Path, Path]:
    return install_root / INSTALL_JOURNAL_NAME, install_root / INSTALL_JOURNAL_TEMP_NAME


def fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError:
        if os.name == "nt":
            return
        raise
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def tree_digest(root: Path) -> str:
    encoded = json.dumps(tree_hashes(root), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def fsync_tree(root: Path) -> None:
    files = validate_tree(root, require_directory=True)
    directories = {root}
    for path in files:
        with path.open("rb") as handle:
            os.fsync(handle.fileno())
        current = path.parent
        while current != root:
            directories.add(current)
            current = current.parent
    for directory in sorted(directories, key=lambda item: len(item.parts), reverse=True):
        fsync_directory(directory)


def write_install_journal(install_root: Path, payload: dict) -> None:
    journal, temporary = journal_paths(install_root)
    with temporary.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, journal)
    fsync_directory(install_root)


def clear_install_journal(install_root: Path) -> None:
    changed = False
    for path in journal_paths(install_root):
        try:
            path.unlink()
            changed = True
        except FileNotFoundError:
            pass
    if changed:
        fsync_directory(install_root)


def cleanup_lock(lock: Path) -> None:
    owner = lock / INSTALL_LOCK_OWNER_NAME
    try:
        owner.unlink()
    except FileNotFoundError:
        pass
    lock.rmdir()


@contextmanager
def installation_lock(install_root: Path) -> Iterator[None]:
    try:
        validate_real_directory(install_root)
    except TreeIntegrityError as exc:
        raise RuntimeError(f"install root must be a real directory: {install_root}: {exc}") from exc
    lock = install_root / INSTALL_LOCK_NAME
    try:
        lock.mkdir()
    except FileExistsError as exc:
        raise RuntimeError(f"another installation is running or a stale install lock exists: {lock}") from exc
    owner = lock / INSTALL_LOCK_OWNER_NAME
    try:
        owner.write_text(json.dumps({"pid": os.getpid()}) + "\n", encoding="utf-8")
    except BaseException:
        try:
            cleanup_lock(lock)
        except OSError:
            pass
        raise
    try:
        yield
    except BaseException as exc:
        try:
            cleanup_lock(lock)
        except OSError as cleanup_exc:
            raise RuntimeError(
                f"installation failed: {exc}; install lock cleanup also failed: {cleanup_exc}"
            ) from exc
        raise
    else:
        try:
            cleanup_lock(lock)
        except OSError as exc:
            raise RuntimeError(f"operation completed but install lock cleanup failed: {exc}") from exc


def load_install_journal(install_root: Path, owned_names: set[str]) -> dict:
    journal, _ = journal_paths(install_root)
    try:
        payload = json.loads(journal.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot read install transaction journal: {journal}: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != 2:
        raise RuntimeError(f"unsupported install transaction journal: {journal}")
    manifest = load_install_manifest()
    if payload.get("pack_name") != manifest["pack_name"] or payload.get("pack_version") != manifest["pack_version"]:
        raise RuntimeError(f"install transaction does not match the current pack identity: {journal}")
    try:
        journal_installer = parse_semantic_version(
            payload.get("installer_version"), field="journal installer_version"
        )
        current_installer = parse_semantic_version(INSTALLER_VERSION, field="installer version")
    except ManifestError as exc:
        raise RuntimeError(f"invalid install transaction installer version: {journal}") from exc
    transaction_id = payload.get("transaction_id")
    if (
        journal_installer > current_installer
        or not isinstance(transaction_id, str)
        or len(transaction_id) != 32
        or any(character not in "0123456789abcdef" for character in transaction_id)
    ):
        raise RuntimeError(f"unsafe install transaction identity: {journal}")
    phase = payload.get("phase")
    skills = payload.get("skills")
    if phase not in {"staging", "backing_up", "activating", "committed"} or not isinstance(skills, list):
        raise RuntimeError(f"invalid install transaction journal: {journal}")
    seen_names: set[str] = set()
    for entry in skills:
        if not isinstance(entry, dict) or set(entry) != {"name", "had_target", "tree_sha256"}:
            raise RuntimeError(f"invalid install transaction entry: {journal}")
        name = entry.get("name")
        expected_digest = entry.get("tree_sha256")
        if (
            not isinstance(name, str)
            or not name
            or Path(name).name != name
            or name in {".", ".."}
            or type(entry.get("had_target")) is not bool
            or not isinstance(expected_digest, str)
            or len(expected_digest) != 64
            or any(character not in "0123456789abcdef" for character in expected_digest)
        ):
            raise RuntimeError(f"unsafe install transaction entry: {journal}")
        if name not in owned_names:
            raise RuntimeError(f"install transaction contains an unowned Skill: {name}")
        if name in seen_names:
            raise RuntimeError(f"install transaction contains duplicate Skill entries: {name}")
        seen_names.add(name)
    return payload


def recover_installation(
    install_root: Path,
    *,
    force_stale_lock: bool = False,
    owned_names: set[str] | None = None,
) -> list[str]:
    """Recover a journaled interrupted transaction without touching unrelated Skills."""

    try:
        validate_real_directory(install_root)
    except TreeIntegrityError as exc:
        raise RuntimeError(f"install root must be a real directory: {install_root}: {exc}") from exc
    if owned_names is None:
        owned_names = {skill["name"] for skill in load_install_manifest()["skills"]}
    lock = install_root / INSTALL_LOCK_NAME
    if path_exists(lock):
        if not force_stale_lock:
            raise RuntimeError(
                f"install lock exists; confirm no installer is running, then retry with --force-stale-lock: {lock}"
            )
        if lock.is_symlink() or not lock.is_dir():
            raise RuntimeError(f"stale install lock is not a real directory: {lock}")
        remove_path(lock)

    actions: list[str] = []
    with installation_lock(install_root):
        journal, temporary = journal_paths(install_root)
        if not path_exists(journal):
            if path_exists(temporary):
                remove_path(temporary)
                actions.append(f"removed incomplete journal temp: {temporary}")
            if not actions:
                actions.append("no interrupted transaction found")
            return actions

        payload = load_install_journal(install_root, owned_names)
        committed = payload["phase"] == "committed"
        entries = payload["skills"]
        if committed:
            for entry in entries:
                target = install_root / entry["name"]
                if not path_exists(target) or target.is_symlink() or not target.is_dir():
                    raise RuntimeError(f"committed install target is missing or invalid: {target}")
                try:
                    actual_digest = tree_digest(target)
                except (OSError, TreeIntegrityError) as exc:
                    raise RuntimeError(f"committed install target is invalid: {target}: {exc}") from exc
                if actual_digest != entry["tree_sha256"]:
                    raise RuntimeError(
                        f"committed install target digest differs; backup retained: {target}"
                    )
        for entry in reversed(entries):
            name = entry["name"]
            target = install_root / name
            staged = install_root / f".{name}.staged"
            backup = install_root / f".{name}.backup"
            if committed:
                if path_exists(staged):
                    remove_path(staged)
                    actions.append(f"removed committed staging path: {staged}")
                if path_exists(backup):
                    remove_path(backup)
                    actions.append(f"removed committed backup: {backup}")
                continue

            if path_exists(backup):
                if path_exists(target):
                    remove_path(target)
                backup.rename(target)
                actions.append(f"restored previous target: {target}")
            elif entry["had_target"]:
                if not path_exists(target):
                    raise RuntimeError(f"cannot recover missing original target: {target}")
            elif path_exists(target):
                if target.is_symlink() or not target.is_dir():
                    raise RuntimeError(f"newly activated target is not a real directory; retained: {target}")
                try:
                    actual_digest = tree_digest(target)
                except (OSError, TreeIntegrityError) as exc:
                    raise RuntimeError(f"newly activated target is invalid; retained: {target}: {exc}") from exc
                if actual_digest != entry["tree_sha256"]:
                    raise RuntimeError(f"newly activated target digest differs; retained: {target}")
                remove_path(target)
                actions.append(f"removed newly activated target: {target}")
            if path_exists(staged):
                remove_path(staged)
                actions.append(f"removed staging path: {staged}")
        clear_install_journal(install_root)
        actions.append("install transaction recovery completed")
    return actions


def install_bundles(
    bundles: list[Path],
    install_root: Path,
    *,
    fault_injector: FaultInjector | None = None,
) -> list[str]:
    """Install one bundle set with a pre-commit rollback and observable post-commit cleanup."""

    def inject(event: str, path: Path) -> None:
        if fault_injector is not None:
            fault_injector(event, path)

    records: list[dict[str, object]] = []
    cleanup_warnings: list[str] = []
    with installation_lock(install_root):
        journal, journal_temp = journal_paths(install_root)
        if path_exists(journal) or path_exists(journal_temp):
            raise RuntimeError(
                "unfinished install transaction exists; run the installer with --recover-only"
            )
        names = [bundle.name for bundle in bundles]
        if len(names) != len(set(names)):
            raise RuntimeError("bundle set contains duplicate names")
        manifest = load_install_manifest()

        for bundle in bundles:
            validate_tree(bundle, require_directory=True)
            target = install_root / bundle.name
            staged = install_root / f".{bundle.name}.staged"
            backup = install_root / f".{bundle.name}.backup"
            if path_exists(staged) or path_exists(backup):
                raise RuntimeError(f"stale install staging path exists for {bundle.name}")
            if path_exists(target) and (target.is_symlink() or not target.is_dir()):
                raise RuntimeError(f"install target is not a real directory: {target}")

            records.append(
                {
                    "target": target,
                    "staged": staged,
                    "backup": backup,
                    "activated": False,
                    "had_target": path_exists(target),
                    "tree_sha256": tree_digest(bundle),
                }
            )

        journal_payload = {
            "schema_version": 2,
            "pack_name": manifest["pack_name"],
            "pack_version": manifest["pack_version"],
            "installer_version": INSTALLER_VERSION,
            "transaction_id": uuid.uuid4().hex,
            "phase": "staging",
            "skills": [
                {
                    "name": bundle.name,
                    "had_target": bool(record["had_target"]),
                    "tree_sha256": str(record["tree_sha256"]),
                }
                for bundle, record in zip(bundles, records)
            ],
        }
        write_install_journal(install_root, journal_payload)

        try:
            for bundle, record in zip(bundles, records):
                staged = record["staged"]
                assert isinstance(staged, Path)
                shutil.copytree(bundle, staged, symlinks=True)
                validate_tree(staged, require_directory=True)
                if tree_digest(staged) != record["tree_sha256"]:
                    raise RuntimeError(f"staged bundle differs from source: {staged}")
                fsync_tree(staged)
                inject("after_stage", staged)

            journal_payload["phase"] = "backing_up"
            write_install_journal(install_root, journal_payload)
            for record in records:
                target = record["target"]
                backup = record["backup"]
                assert isinstance(target, Path) and isinstance(backup, Path)
                if path_exists(target):
                    target.rename(backup)
                    inject("after_backup", backup)
            journal_payload["phase"] = "activating"
            write_install_journal(install_root, journal_payload)
            for record in records:
                staged = record["staged"]
                target = record["target"]
                assert isinstance(staged, Path) and isinstance(target, Path)
                staged.rename(target)
                record["activated"] = True
                inject("after_activate", target)
            journal_payload["phase"] = "committed"
            write_install_journal(install_root, journal_payload)
        except BaseException as exc:
            rollback_errors: list[str] = []
            for record in reversed(records):
                target = record["target"]
                staged = record["staged"]
                backup = record["backup"]
                assert isinstance(target, Path) and isinstance(staged, Path) and isinstance(backup, Path)
                try:
                    if record["activated"] and path_exists(target):
                        remove_path(target)
                    if path_exists(backup):
                        if path_exists(target):
                            raise RuntimeError(f"rollback target already exists: {target}")
                        backup.rename(target)
                    if path_exists(staged):
                        remove_path(staged)
                except Exception as rollback_exc:
                    rollback_errors.append(f"{target.name}: {rollback_exc}")
            if rollback_errors:
                detail = "; ".join(rollback_errors)
                raise RuntimeError(f"installation failed: {exc}; rollback also failed: {detail}") from exc
            try:
                clear_install_journal(install_root)
            except OSError as journal_exc:
                raise RuntimeError(
                    f"installation failed: {exc}; rollback succeeded but journal cleanup failed: {journal_exc}"
                ) from exc
            raise

        for bundle in bundles:
            backup = install_root / f".{bundle.name}.backup"
            if not path_exists(backup):
                continue
            try:
                inject("before_cleanup", backup)
                remove_path(backup)
            except Exception as exc:
                cleanup_warnings.append(f"install committed but backup cleanup failed for {backup}: {exc}")
        if not cleanup_warnings:
            clear_install_journal(install_root)
    return cleanup_warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install-root")
    parser.add_argument("--skill", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--build-only", action="store_true")
    parser.add_argument("--recover-only", action="store_true")
    parser.add_argument("--force-stale-lock", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()

    try:
        manifest = load_install_manifest()
    except (OSError, ManifestError, ValueError) as exc:
        print(f"install_skill_pack error: {exc}", file=sys.stderr)
        return 2
    install_root = expand_root(args.install_root or manifest["default_install_root"])
    if args.force_stale_lock and not args.recover_only:
        print("--force-stale-lock requires --recover-only", file=sys.stderr)
        return 2
    if args.recover_only:
        if args.dry_run or args.build_only or args.output or args.skill:
            print("--recover-only cannot be combined with build, dry-run, output, or skill options", file=sys.stderr)
            return 2
        try:
            actions = recover_installation(
                install_root,
                force_stale_lock=args.force_stale_lock,
                owned_names={skill["name"] for skill in manifest["skills"]},
            )
        except (OSError, RuntimeError) as exc:
            print(f"install_skill_pack recovery error: {exc}", file=sys.stderr)
            return 2
        for action in actions:
            print(f"recovery\t{action}")
        return 0

    selected = args.skill or [skill["name"] for skill in manifest["skills"]]
    known = {skill["name"] for skill in manifest["skills"]}
    unknown = sorted(set(selected) - known)
    if unknown:
        print(f"unknown skills: {', '.join(unknown)}", file=sys.stderr)
        return 2

    if args.dry_run:
        for name in selected:
            target = install_root / name
            state = "replace" if target.exists() else "create"
            print(f"{state}\t{target}")
        for value in manifest.get("duplicate_discovery_roots", []):
            duplicate_root = expand_root(value)
            if duplicate_root == install_root:
                continue
            duplicates = [name for name in selected if (duplicate_root / name).exists()]
            if duplicates:
                print(f"duplicate-discovery-warning\t{duplicate_root}\t{','.join(duplicates)}")
        return 0

    if args.build_only and not args.output:
        print("--build-only requires --output", file=sys.stderr)
        return 2

    temporary = None
    try:
        if args.output:
            build_root = Path(args.output).resolve()
            build_root.mkdir(parents=True, exist_ok=True)
        else:
            temporary = tempfile.TemporaryDirectory(prefix="consumer-skill-pack-")
            build_root = Path(temporary.name)

        command = [sys.executable, str(BUILDER), "--output", str(build_root)]
        for name in selected:
            command.extend(["--skill", name])
        subprocess.run(command, cwd=ROOT, check=True)

        if args.build_only:
            print(build_root)
            temporary = None
            return 0

        install_root = prepare_install_root(install_root)
        warnings = install_bundles([build_root / name for name in selected], install_root)
        for name in selected:
            print(f"installed\t{install_root / name}")
        for warning in warnings:
            print(f"warning: {warning}", file=sys.stderr)
        if warnings:
            print(
                "install committed but cleanup is incomplete; run --recover-only before the next install",
                file=sys.stderr,
            )
            return 1
        return 0
    except (
        OSError,
        ValueError,
        RuntimeError,
        ManifestError,
        TreeIntegrityError,
        subprocess.CalledProcessError,
    ) as exc:
        print(f"install_skill_pack error: {exc}", file=sys.stderr)
        return 2
    finally:
        if temporary is not None:
            temporary.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
