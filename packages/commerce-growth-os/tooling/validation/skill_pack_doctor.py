#!/usr/bin/env python3
"""Diagnose repository, installed-bundle, and duplicate-discovery health."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "skill-pack.json"
BUILDER = ROOT / "tooling/build/build_skill_bundles.py"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tooling.installation.tree_integrity import (
    TreeIntegrityError,
    lexical_absolute,
    tree_hashes,
    validate_real_directory,
)
from tooling.installation.install_skill_pack import (
    INSTALL_JOURNAL_NAME,
    INSTALL_JOURNAL_TEMP_NAME,
    INSTALL_LOCK_NAME,
    prepare_install_root,
)
from tooling.manifest import ManifestError, load_manifest


def path_exists(path: Path) -> bool:
    return os.path.lexists(path)


def command_output(command: list[str]) -> tuple[int, str]:
    try:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    except OSError as exc:
        return 127, str(exc)
    rendered = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
    return result.returncode, rendered


def finding(severity: str, code: str, message: str, **details: Any) -> dict[str, Any]:
    return {"severity": severity, "code": code, "message": message, "details": details}


def diagnose(canonical_root: Path, secondary_roots: list[Path]) -> dict[str, Any]:
    manifest = load_manifest(MANIFEST)
    skills = [skill["name"] for skill in manifest["skills"]]
    findings: list[dict[str, Any]] = []

    canonical_scan_root: Path | None = None
    try:
        canonical_scan_root = validate_real_directory(canonical_root)
    except TreeIntegrityError as exc:
        findings.append(
            finding(
                "error",
                "canonical_root_invalid",
                f"Canonical install root is not a real directory: {canonical_root}",
                path=str(canonical_root),
                error=str(exc),
            )
        )

    secondary_scan_roots: list[Path] = []
    for root in secondary_roots:
        # Secondary discovery roots are optional. A missing root is normal, but every
        # existing component of an opted-in root must be a real directory before it
        # is used for any content or install-state inspection.
        if not path_exists(root):
            continue
        try:
            secondary_scan_roots.append(validate_real_directory(root))
        except TreeIntegrityError as exc:
            findings.append(
                finding(
                    "error",
                    "duplicate_root_invalid",
                    f"Duplicate discovery root is not a real directory: {root}",
                    path=str(root),
                    error=str(exc),
                )
            )

    code, codex_version = command_output(["codex", "--version"])
    if code != 0:
        findings.append(finding("warning", "codex_version_unavailable", "Could not read Codex CLI version."))

    with tempfile.TemporaryDirectory(prefix="skill-pack-doctor-") as temp:
        result = subprocess.run(
            [sys.executable, str(BUILDER), "--output", temp],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            detail = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
            findings.append(finding("error", "bundle_build_failed", "Fresh bundle build failed.", output=detail[-2000:]))
        else:
            for name in skills:
                built = Path(temp) / name
                try:
                    built_hashes = tree_hashes(built)
                except (OSError, TreeIntegrityError) as exc:
                    findings.append(
                        finding(
                            "error",
                            "bundle_tree_invalid",
                            f"Fresh bundle tree is invalid: {name}",
                            path=str(built),
                            error=str(exc),
                        )
                    )
                    continue
                if canonical_scan_root is not None:
                    installed = canonical_scan_root / name
                    if not path_exists(installed):
                        findings.append(
                            finding(
                                "error",
                                "canonical_skill_missing",
                                f"Canonical installed Skill is missing: {name}",
                                path=str(installed),
                            )
                        )
                    else:
                        try:
                            installed_hashes = tree_hashes(installed)
                        except (OSError, TreeIntegrityError) as exc:
                            findings.append(
                                finding(
                                    "error",
                                    "canonical_tree_invalid",
                                    f"Canonical installed Skill tree is invalid: {name}",
                                    path=str(installed),
                                    error=str(exc),
                                )
                            )
                        else:
                            if built_hashes != installed_hashes:
                                findings.append(
                                    finding(
                                        "error",
                                        "canonical_content_mismatch",
                                        f"Installed content differs from fresh bundle: {name}",
                                        path=str(installed),
                                    )
                                )

                for secondary_root in secondary_scan_roots:
                    duplicate = secondary_root / name
                    if not path_exists(duplicate):
                        continue
                    try:
                        duplicate_hashes = tree_hashes(duplicate)
                    except (OSError, TreeIntegrityError) as exc:
                        findings.append(
                            finding(
                                "error",
                                "duplicate_discovery_invalid",
                                f"Duplicate discovery tree is invalid: {name}",
                                path=str(duplicate),
                                error=str(exc),
                            )
                        )
                    else:
                        if built_hashes == duplicate_hashes:
                            findings.append(
                                finding(
                                    "warning",
                                    "duplicate_discovery_same",
                                    f"Duplicate discovery copy is content-identical: {name}",
                                    path=str(duplicate),
                                )
                            )
                        else:
                            findings.append(
                                finding(
                                    "error",
                                    "duplicate_discovery_mismatch",
                                    f"Duplicate discovery copy differs: {name}",
                                    path=str(duplicate),
                                )
                            )

    for root in (
        *(root for root in (canonical_scan_root,) if root is not None),
        *secondary_scan_roots,
    ):
        lock = root / INSTALL_LOCK_NAME
        if path_exists(lock):
            findings.append(
                finding(
                    "error",
                    "install_lock_present",
                    f"Install lock exists or an installation is running: {lock}",
                    path=str(lock),
                )
            )
        for transaction_name in (INSTALL_JOURNAL_NAME, INSTALL_JOURNAL_TEMP_NAME):
            transaction = root / transaction_name
            if path_exists(transaction):
                findings.append(
                    finding(
                        "error",
                        "install_journal_present",
                        f"Interrupted or cleanup-pending install journal exists: {transaction}",
                        path=str(transaction),
                    )
                )
        for name in skills:
            for suffix in ("staged", "backup"):
                stale = root / f".{name}.{suffix}"
                if path_exists(stale):
                    findings.append(
                        finding(
                            "error",
                            "stale_install_artifact",
                            f"Stale install artifact exists: {stale}",
                            path=str(stale),
                        )
                    )

    status_code, status = command_output(["git", "status", "--short", "--branch"])
    if status_code != 0:
        findings.append(finding("warning", "git_status_unavailable", "Could not read Git status."))
    elif len(status.splitlines()) > 1:
        findings.append(finding("info", "repository_dirty", "Repository has uncommitted changes, expected during active development."))

    severity_counts = {severity: sum(item["severity"] == severity for item in findings) for severity in ("error", "warning", "info")}
    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "pack_name": manifest["pack_name"],
        "pack_version": manifest["pack_version"],
        "schema_version": manifest["schema_version"],
        "skills": len(skills),
        "canonical_root": str(canonical_root),
        "secondary_roots": [str(root) for root in secondary_roots],
        "codex_version": codex_version if code == 0 else None,
        "git_status": status if status_code == 0 else None,
        "counts": severity_counts,
        "findings": findings,
        "healthy": severity_counts["error"] == 0,
    }


def self_test() -> None:
    from types import SimpleNamespace
    from unittest.mock import patch

    sample = [
        finding("warning", "duplicate_discovery_same", "duplicate"),
        finding("info", "repository_dirty", "dirty"),
    ]
    counts = {severity: sum(item["severity"] == severity for item in sample) for severity in ("error", "warning", "info")}
    if counts != {"error": 0, "warning": 1, "info": 1}:
        raise AssertionError(f"unexpected doctor counts: {counts}")
    code, detail = command_output(["commerce-growth-os-command-that-does-not-exist"])
    if code != 127 or not detail:
        raise AssertionError("missing diagnostic commands must remain observable")

    manifest = load_manifest(MANIFEST)
    skill_names = [skill["name"] for skill in manifest["skills"]]

    def write_fixture(root: Path) -> None:
        for name in skill_names:
            skill_root = root / name
            skill_root.mkdir(parents=True, exist_ok=True)
            (skill_root / "SKILL.md").write_text(f"# {name}\n", encoding="utf-8")

    def fake_builder(command: list[str], **_: Any) -> SimpleNamespace:
        if command[:2] != [sys.executable, str(BUILDER)]:
            raise AssertionError(f"unexpected subprocess invocation: {command}")
        output = Path(command[command.index("--output") + 1])
        write_fixture(output)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    def fake_command_output(command: list[str]) -> tuple[int, str]:
        if command == ["codex", "--version"]:
            return 0, "codex test"
        if command == ["git", "status", "--short", "--branch"]:
            return 0, "## main"
        raise AssertionError(f"unexpected command output request: {command}")

    with tempfile.TemporaryDirectory(prefix="skill-pack-doctor-self-test-") as temp:
        temporary_root = Path(temp)
        real_parent = temporary_root / "real"
        canonical_root = real_parent / "skills"
        write_fixture(canonical_root)
        alias_parent = temporary_root / "alias"
        alias_parent.symlink_to(real_parent, target_is_directory=True)
        invalid_secondary = temporary_root / "secondary-file"
        invalid_secondary.write_text("not a directory\n", encoding="utf-8")
        missing_secondary = temporary_root / "optional-secondary"

        with patch.object(sys.modules[__name__], "command_output", fake_command_output), patch.object(
            sys.modules[__name__], "subprocess"
        ) as patched_subprocess:
            patched_subprocess.run.side_effect = fake_builder

            alias_report = diagnose(alias_parent / "skills", [])
            alias_codes = {item["code"] for item in alias_report["findings"]}
            if alias_report["healthy"] or alias_codes != {"canonical_root_invalid"}:
                raise AssertionError(f"ancestor symlink must reject canonical root without scanning it: {alias_report}")
            try:
                prepare_install_root(alias_parent / "new-skills")
            except RuntimeError:
                pass
            else:
                raise AssertionError("shared install-root validation must reject an ancestor symlink")

            secondary_report = diagnose(canonical_root, [invalid_secondary, missing_secondary])
            secondary_codes = {item["code"] for item in secondary_report["findings"]}
            if secondary_report["healthy"] or secondary_codes != {"duplicate_root_invalid"}:
                raise AssertionError(
                    "existing non-directory secondary roots must be rejected while missing optional roots remain normal: "
                    f"{secondary_report}"
                )
            missing_report = diagnose(canonical_root, [missing_secondary])
            if not missing_report["healthy"]:
                raise AssertionError(f"missing optional secondary roots must remain normal: {missing_report}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-root")
    parser.add_argument("--secondary-root", action="append", default=[])
    parser.add_argument("--output")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as a non-zero result")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    try:
        if args.self_test:
            self_test()
            print("skill pack doctor self-test passed.")
            return 0
        manifest = load_manifest(MANIFEST)
        canonical_root = lexical_absolute(
            Path(args.canonical_root or manifest["default_install_root"]).expanduser()
        )
        secondary_values = args.secondary_root or manifest.get("duplicate_discovery_roots", [])
        secondary_roots = []
        for value in secondary_values:
            root = lexical_absolute(Path(value).expanduser())
            if root != canonical_root and root not in secondary_roots:
                secondary_roots.append(root)
        report = diagnose(canonical_root, secondary_roots)
        rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
        if args.output:
            output = Path(args.output).expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(rendered + "\n", encoding="utf-8")
            print(f"skill pack doctor artifact: {output}")
        if args.json:
            print(rendered)
        else:
            print(
                f"skill_pack_doctor healthy={str(report['healthy']).lower()} "
                f"errors={report['counts']['error']} warnings={report['counts']['warning']} "
                f"info={report['counts']['info']}"
            )
            for item in report["findings"]:
                print(f"{item['severity']}: {item['code']}: {item['message']}")
        if not report["healthy"]:
            return 1
        if args.strict and report["counts"]["warning"]:
            return 1
        return 0
    except (OSError, KeyError, ManifestError, ValueError) as exc:
        print(f"skill_pack_doctor error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
