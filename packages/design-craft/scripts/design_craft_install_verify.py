#!/usr/bin/env python3
"""Verify a design-craft installation and its generated provenance metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from design_craft_evidence_common import (
    git_dirty,
    git_head,
    git_is_ancestor,
    git_root,
    git_tree_sha256,
    skill_provenance,
)


SCHEMA = "design-craft.install-verification.v1"
METADATA_SCHEMA_V1 = "design-craft.install.v1"
METADATA_SCHEMA_V2 = "design-craft.install.v2"
METADATA_NAME = ".design-craft-install.json"
RELEASE_STATES = {"development", "release_candidate", "released", "unknown"}


def ignored(path: Path) -> bool:
    return (
        "__pycache__" in path.parts
        or path.name in {".DS_Store", METADATA_NAME}
        or path.suffix in {".pyc", ".pyo"}
    )


def snapshot(root: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not root.is_dir():
        return values
    for path in sorted(root.rglob("*")):
        if not path.is_file() or ignored(path):
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        values[path.relative_to(root).as_posix()] = digest
    return values


def tree_digest(values: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for path, file_digest in sorted(values.items()):
        digest.update(path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_digest.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def source_provenance(source: Path) -> tuple[Path, str, bool, bool]:
    fallback_root = source.parent.parent if source.parent.name == "skills" else source
    try:
        repo_root = git_root(source)
        return (
            fallback_root.resolve(),
            git_head(repo_root),
            git_dirty(repo_root),
            git_dirty(repo_root, source),
        )
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError):
        return fallback_root.resolve(), "unavailable", True, True


def source_release_state(source_root: Path, version: str, source_commit: str) -> str:
    changelog_path = source_root / "CHANGELOG.md"
    if not changelog_path.is_file():
        return "unknown"
    changelog = changelog_path.read_text(encoding="utf-8")
    match = re.search(
        rf"^## {re.escape(version)} - (?P<label>[^\n]+)$",
        changelog,
        flags=re.M,
    )
    if not match:
        return "unknown"
    label = match.group("label").strip()
    if label == "Unreleased":
        return "development"
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", label):
        return "unknown"
    tag_result = subprocess.run(
        ["git", "-C", str(source_root), "rev-list", "-n", "1", f"v{version}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    return "released" if tag_result.stdout.strip() == source_commit else "release_candidate"


def validate_metadata(
    installed: Path,
    *,
    expected_name: str | None,
    expected_version: str | None,
    expected_tree_digest: str,
    expected_source_root: Path,
    expected_source_path: Path,
    expected_source_commit: str,
    expected_skill_source_dirty: bool,
    expected_release_state: str,
) -> tuple[dict, list[str]]:
    path = installed / METADATA_NAME
    if not path.is_file():
        return {}, [f"missing installation metadata: {path}"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"invalid installation metadata: {exc}"]

    errors: list[str] = []
    metadata_schema = payload.get("schema")
    if metadata_schema not in {METADATA_SCHEMA_V1, METADATA_SCHEMA_V2}:
        errors.append(
            f"metadata schema must be {METADATA_SCHEMA_V1} or {METADATA_SCHEMA_V2}"
        )
    if expected_name and payload.get("skill_name") != expected_name:
        errors.append(f"metadata skill_name must be {expected_name}")
    if expected_version and payload.get("version") != expected_version:
        errors.append(f"metadata version must be {expected_version}")
    release_state = payload.get("release_state")
    if release_state not in RELEASE_STATES:
        errors.append(f"metadata release_state must be one of {sorted(RELEASE_STATES)}")
    elif release_state != expected_release_state:
        errors.append(f"metadata release_state must match current source state {expected_release_state}")
    if payload.get("source_tree_sha256") != expected_tree_digest:
        errors.append("metadata source_tree_sha256 must match the installed source tree")
    source_commit = str(payload.get("source_commit", ""))
    if source_commit != "unavailable" and not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        errors.append("metadata source_commit must be a full lowercase Git SHA or unavailable")
    elif expected_source_commit == "unavailable":
        if source_commit != "unavailable":
            errors.append("metadata source_commit must be unavailable outside a Git source")
    elif source_commit == "unavailable":
        errors.append("metadata source_commit must identify the installed Git source")
    elif not git_is_ancestor(expected_source_root, source_commit, expected_source_commit):
        errors.append(
            "metadata source_commit must be an ancestor of the current source HEAD "
            f"{expected_source_commit}"
        )
    elif not expected_skill_source_dirty:
        try:
            recorded_commit_digest = git_tree_sha256(
                expected_source_root,
                expected_source_path,
                source_commit,
            )
        except (OSError, ValueError, subprocess.CalledProcessError) as exc:
            errors.append(f"cannot inspect skill tree at metadata source_commit: {exc}")
        else:
            if recorded_commit_digest != expected_tree_digest:
                errors.append(
                    "metadata source_commit skill tree must match source_tree_sha256"
                )

    source_dirty = payload.get("source_dirty")
    if not isinstance(source_dirty, bool):
        errors.append("metadata source_dirty must be boolean")
    elif source_dirty is not expected_skill_source_dirty:
        errors.append(
            "metadata source_dirty must match current skill source dirty state "
            f"{expected_skill_source_dirty}"
        )

    if metadata_schema == METADATA_SCHEMA_V2:
        skill_source_dirty = payload.get("skill_source_dirty")
        if not isinstance(skill_source_dirty, bool):
            errors.append("metadata skill_source_dirty must be boolean")
        elif skill_source_dirty is not expected_skill_source_dirty:
            errors.append(
                "metadata skill_source_dirty must match current skill source dirty state "
                f"{expected_skill_source_dirty}"
            )
        if isinstance(source_dirty, bool) and isinstance(skill_source_dirty, bool):
            if source_dirty is not skill_source_dirty:
                errors.append("metadata source_dirty must alias skill_source_dirty")
        if not isinstance(payload.get("repo_dirty"), bool):
            errors.append("metadata repo_dirty must be boolean")

    if not isinstance(payload.get("installed_at"), str) or not payload["installed_at"].endswith("Z"):
        errors.append("metadata installed_at must be a UTC timestamp ending in Z")
    expected_installer_version = 3 if metadata_schema == METADATA_SCHEMA_V2 else 2
    if payload.get("installer_version") != expected_installer_version:
        errors.append(f"metadata installer_version must be {expected_installer_version}")
    for field in ("source_root", "source_path", "source_repo"):
        if not isinstance(payload.get(field), str) or not payload[field].strip():
            errors.append(f"metadata {field} must be a non-empty string")
    if isinstance(payload.get("source_root"), str) and payload["source_root"].strip():
        if Path(payload["source_root"]).expanduser().resolve() != expected_source_root:
            errors.append(f"metadata source_root must match current source root {expected_source_root}")
    if isinstance(payload.get("source_path"), str) and payload["source_path"].strip():
        if Path(payload["source_path"]).expanduser().resolve() != expected_source_path:
            errors.append(f"metadata source_path must match current source path {expected_source_path}")

    return payload, errors


def verify(
    source: Path,
    installed: Path,
    *,
    expected_name: str | None,
    expected_version: str | None,
    require_metadata: bool,
) -> dict:
    source_files = snapshot(source)
    installed_files = snapshot(installed)
    source_root, source_commit, repo_dirty, skill_source_dirty = source_provenance(source)
    release_state = source_release_state(
        source_root,
        expected_version or "",
        source_commit,
    )
    missing = sorted(set(source_files) - set(installed_files))
    extra = sorted(set(installed_files) - set(source_files))
    changed = sorted(
        path
        for path in set(source_files) & set(installed_files)
        if source_files[path] != installed_files[path]
    )

    metadata: dict = {}
    metadata_errors: list[str] = []
    if require_metadata:
        metadata, metadata_errors = validate_metadata(
            installed,
            expected_name=expected_name,
            expected_version=expected_version,
            expected_tree_digest=tree_digest(source_files),
            expected_source_root=source_root,
            expected_source_path=source.resolve(),
            expected_source_commit=source_commit,
            expected_skill_source_dirty=skill_source_dirty,
            expected_release_state=release_state,
        )

    errors: list[str] = []
    if not source.is_dir():
        errors.append(f"source directory missing: {source}")
    if not installed.is_dir():
        errors.append(f"installed directory missing: {installed}")
    if missing:
        errors.append(f"missing files: {missing[:10]}")
    if extra:
        errors.append(f"extra files: {extra[:10]}")
    if changed:
        errors.append(f"changed files: {changed[:10]}")
    errors.extend(metadata_errors)

    return {
        "schema": SCHEMA,
        "source": str(source),
        "installed": str(installed),
        "ok": not errors,
        "source_file_count": len(source_files),
        "installed_file_count": len(installed_files),
        "missing": missing,
        "extra": extra,
        "changed": changed,
        "expected_source": {
            "root": str(source_root),
            "path": str(source.resolve()),
            "commit": source_commit,
            "dirty": skill_source_dirty,
            "skill_source_dirty": skill_source_dirty,
            "repo_dirty": repo_dirty,
            "release_state": release_state,
        },
        "metadata": metadata,
        "errors": errors,
    }


def run_self_check() -> None:
    with tempfile.TemporaryDirectory(prefix="design-craft-install-verify-") as tmp_value:
        tmp = Path(tmp_value)
        repo = tmp / "source-repo"
        source = repo / "skills/design-craft"
        installed = tmp / "installed/design-craft"
        source.mkdir(parents=True)
        (source / "SKILL.md").write_text("# Fixture skill\n", encoding="utf-8")
        (source / "VERSION").write_text("0.0.0\n", encoding="utf-8")
        (source / "references").mkdir()
        (source / "references/example.md").write_text("# Example\n", encoding="utf-8")
        (repo / "CHANGELOG.md").write_text(
            "# Changelog\n\n## 0.0.0 - Unreleased\n\n- Fixture.\n",
            encoding="utf-8",
        )
        (repo / "unrelated.txt").write_text("initial\n", encoding="utf-8")

        for command in (
            ("git", "init", "-q"),
            ("git", "config", "user.email", "fixture@example.invalid"),
            ("git", "config", "user.name", "Fixture"),
            ("git", "add", "."),
            ("git", "commit", "-qm", "initial fixture"),
        ):
            subprocess.run(command, cwd=repo, check=True)

        shutil.copytree(source, installed)
        source_commit = git_head(repo)
        metadata = {
            "schema": METADATA_SCHEMA_V2,
            "installer_version": 3,
            "skill_name": "design-craft",
            "version": "0.0.0",
            "release_state": "development",
            "source_root": str(repo.resolve()),
            "source_path": str(source.resolve()),
            "source_repo": "https://example.invalid/design-craft",
            "source_commit": source_commit,
            "source_dirty": False,
            "skill_source_dirty": False,
            "repo_dirty": False,
            "source_tree_sha256": tree_digest(snapshot(source)),
            "installed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        (installed / METADATA_NAME).write_text(
            json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
        )

        initial = verify(
            source,
            installed,
            expected_name="design-craft",
            expected_version="0.0.0",
            require_metadata=True,
        )
        if not initial["ok"]:
            raise RuntimeError("clean install fixture failed: " + "; ".join(initial["errors"]))

        (repo / "unrelated.txt").write_text("committed later\n", encoding="utf-8")
        subprocess.run(("git", "add", "unrelated.txt"), cwd=repo, check=True)
        subprocess.run(("git", "commit", "-qm", "unrelated change"), cwd=repo, check=True)
        ancestor = verify(
            source,
            installed,
            expected_name="design-craft",
            expected_version="0.0.0",
            require_metadata=True,
        )
        if not ancestor["ok"]:
            raise RuntimeError(
                "unchanged skill at an ancestor commit failed: " + "; ".join(ancestor["errors"])
            )

        (repo / "unrelated.txt").write_text("uncommitted unrelated work\n", encoding="utf-8")
        unrelated = verify(
            source,
            installed,
            expected_name="design-craft",
            expected_version="0.0.0",
            require_metadata=True,
        )
        if not unrelated["ok"]:
            raise RuntimeError(
                "unrelated repo work invalidated skill parity: " + "; ".join(unrelated["errors"])
            )
        if unrelated["expected_source"]["repo_dirty"] is not True:
            raise RuntimeError("unrelated dirty work was not reported at repo scope")
        if unrelated["expected_source"]["skill_source_dirty"] is not False:
            raise RuntimeError("unrelated dirty work leaked into skill scope")
        provenance = skill_provenance(source)
        if provenance.get("repo_dirty") is not True:
            raise RuntimeError("evidence provenance did not report repo_dirty=true")
        if provenance.get("skill_source_dirty") is not False:
            raise RuntimeError("evidence provenance did not preserve a clean skill scope")

        (source / "SKILL.md").write_text("# Changed fixture skill\n", encoding="utf-8")
        changed = verify(
            source,
            installed,
            expected_name="design-craft",
            expected_version="0.0.0",
            require_metadata=True,
        )
        if changed["ok"]:
            raise RuntimeError("changed skill source unexpectedly passed install parity")
        if changed["expected_source"]["skill_source_dirty"] is not True:
            raise RuntimeError("changed skill source was not reported dirty")

        subprocess.run(("git", "add", "skills/design-craft/SKILL.md"), cwd=repo, check=True)
        subprocess.run(("git", "commit", "-qm", "change fixture skill"), cwd=repo, check=True)
        shutil.copy2(source / "SKILL.md", installed / "SKILL.md")
        metadata["source_tree_sha256"] = tree_digest(snapshot(source))
        (installed / METADATA_NAME).write_text(
            json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
        )
        forged_ancestor = verify(
            source,
            installed,
            expected_name="design-craft",
            expected_version="0.0.0",
            require_metadata=True,
        )
        if forged_ancestor["ok"]:
            raise RuntimeError(
                "metadata pointing at an ancestor with a different skill tree unexpectedly passed"
            )
        if not any(
            "source_commit skill tree" in error for error in forged_ancestor["errors"]
        ):
            raise RuntimeError(
                "historical skill-tree mismatch did not produce a provenance error"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source")
    parser.add_argument("--installed")
    parser.add_argument("--expected-name")
    parser.add_argument("--expected-version")
    parser.add_argument("--require-metadata", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.check:
        run_self_check()
        print("install_verifier_self_check=ok")
        return 0
    if not args.source or not args.installed:
        parser.error("--source and --installed are required unless --check is used")

    payload = verify(
        Path(args.source).expanduser().resolve(),
        Path(args.installed).expanduser().resolve(),
        expected_name=args.expected_name,
        expected_version=args.expected_version,
        require_metadata=args.require_metadata,
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    elif payload["ok"]:
        print(f"install parity verified: {payload['installed']}")
    else:
        print("\n".join(payload["errors"]), file=sys.stderr)
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
