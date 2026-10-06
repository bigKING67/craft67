#!/usr/bin/env python3
"""Verify GitHub package discovery contracts for Pi and Codex-compatible hosts."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, data: dict[str, object]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def tree_fingerprint(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        kind = "symlink" if path.is_symlink() else "dir" if path.is_dir() else "file"
        digest.update(f"{kind}\0{relative}\0".encode())
        if path.is_file() and not path.is_symlink():
            digest.update(sha256_file(path).encode())
        digest.update(b"\n")
    return digest.hexdigest()


def run_installed_cli(installed: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(installed / "scripts/creative_craft.py"), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def populate_reviewed_reference_pack(reference_root: Path, version: str) -> None:
    manifest_path = reference_root / "reference-pack.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_path = reference_root / "sources/host-smoke.md"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(
        f"Synthetic installed-runtime evidence for Reference Pack {version}.\n",
        encoding="utf-8",
    )
    manifest.update(
        {
            "version": version,
            "status": "reviewed",
            "reviewed_at": "2026-08-04T00:00:00Z",
            "review_after": "2027-08-04T00:00:00Z",
            "source_references": [
                {
                    "source_id": "source-host-smoke",
                    "authority": "research",
                    "uri": "urn:creative-craft:host-smoke-source",
                    "captured_at": "2026-08-04T00:00:00Z",
                    "snapshot_path": "sources/host-smoke.md",
                    "sha256": sha256_file(source_path),
                    "notes": "Synthetic installed-runtime fixture only.",
                }
            ],
            "entities": [
                {
                    "reference_id": "reference-host-smoke",
                    "entity_type": "other",
                    "name": "Synthetic Host Smoke Reference",
                    "relationship": "reference",
                    "summary": "Synthetic installed-runtime fixture only.",
                    "source_refs": ["source-host-smoke"],
                    "observations": [
                        {
                            "observation_id": "observation-host-smoke",
                            "dimension": "runtime-contract",
                            "evidence_state": "OBSERVED",
                            "statement": f"Installed Reference Pack version {version} is present.",
                            "evidence_refs": ["source-host-smoke"],
                        }
                    ],
                    "transferable_principles": [
                        {
                            "principle_id": "principle-host-smoke",
                            "derived_from": ["observation-host-smoke"],
                            "statement": "Use only the abstract runtime contract.",
                            "application_scope": ["host-smoke"],
                            "adaptation_required": True,
                            "must_preserve_primary_brand": ["identity", "claims", "rights"],
                        }
                    ],
                    "non_transferable_elements": ["fixture identity"],
                    "applicable_to": ["host-smoke"],
                    "reference_roles": ["principle"],
                    "rights_policy": "principle_only",
                    "prohibited_use": ["identity imitation"],
                    "asset_refs": [],
                    "may_override_primary_brand": False,
                }
            ],
        }
    )
    write_json(manifest_path, manifest)


def command_error(completed: subprocess.CompletedProcess[str]) -> str:
    return completed.stderr.strip() or completed.stdout.strip() or "no command output"


def grok_discovery_errors(
    payload: object, expected_skill_file: Path
) -> list[str]:
    """Validate that Grok discovered the exact isolated Creative Craft leaf."""
    if not isinstance(payload, dict):
        return ["Grok inspect output must be a JSON object"]
    skills = payload.get("skills")
    if not isinstance(skills, list):
        return ["Grok inspect output has no skills array"]

    expected = expected_skill_file.resolve()
    exact_matches: list[dict[str, object]] = []
    for item in skills:
        if not isinstance(item, dict) or item.get("name") != "creative-craft":
            continue
        source = item.get("source")
        if not isinstance(source, dict):
            continue
        source_path = source.get("path")
        if not isinstance(source_path, str):
            continue
        if Path(source_path).expanduser().resolve() == expected:
            exact_matches.append(item)

    if not exact_matches:
        return [f"Grok did not discover Creative Craft from {expected}"]
    if not any(item.get("userInvocable") is True for item in exact_matches):
        return ["Grok discovered Creative Craft but did not mark it user-invocable"]
    return []


def run_grok_discovery(root: Path, grok_bin: str) -> list[str]:
    """Run a no-model-call Grok discovery probe in an isolated project."""
    executable = shutil.which(grok_bin)
    if executable is None:
        return [f"Grok executable not found: {grok_bin}"]

    with tempfile.TemporaryDirectory(prefix="creative-craft-grok-smoke-") as directory:
        project = Path(directory)
        installed = project / ".grok" / "skills" / "creative-craft"
        installed.parent.mkdir(parents=True)
        shutil.copytree(
            root / "skills" / "creative-craft",
            installed,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        )
        completed = subprocess.run(
            [executable, "inspect", "--json"],
            cwd=project,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            return ["Grok inspect failed: " + command_error(completed)]
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            return [f"Grok inspect returned invalid JSON: {exc}"]
        return grok_discovery_errors(payload, installed / "SKILL.md")


def run_reference_runtime_e2e(
    installed: Path,
    workspace: Path,
    *,
    check_prefix: str = "installed",
) -> tuple[list[str], list[str]]:
    """Exercise the portable Reference Pack runtime from one installed skill leaf."""
    checks: list[str] = []
    errors: list[str] = []
    reference_root = workspace / "acme-creative-references"
    reference_init = run_installed_cli(
        installed,
        "init-reference-pack",
        "--target",
        str(reference_root),
        "--pack-id",
        "acme-creative-references",
        "--name",
        "Acme Creative References",
        "--owner",
        "host-smoke",
    )
    reference_validation = run_installed_cli(
        installed,
        "validate-reference-pack",
        "--root",
        str(reference_root),
        "--json",
    )
    if reference_init.returncode != 0 or reference_validation.returncode != 0:
        failure = reference_init if reference_init.returncode != 0 else reference_validation
        errors.append(
            f"{check_prefix} runtime Reference Pack smoke failed: "
            + command_error(failure)
        )
        return checks, errors

    checks.append(f"{check_prefix}-reference-pack-runtime")
    populate_reviewed_reference_pack(reference_root, "0.1.0")
    reviewed_validation = run_installed_cli(
        installed,
        "validate-reference-pack",
        "--root",
        str(reference_root),
        "--json",
    )
    project_root = workspace / "reference-project"
    seed_project = run_installed_cli(
        installed,
        "seed",
        "--target",
        str(project_root),
    )
    doctor_seed = run_installed_cli(
        installed,
        "doctor-project",
        "--root",
        str(project_root),
        "--json",
    )
    bind_reference = run_installed_cli(
        installed,
        "bind-reference-pack",
        "--target",
        str(project_root),
        "--reference-pack",
        str(reference_root),
        "--reference-source-uri",
        "https://git.invalid/acme-creative-references.git",
        "--reference-source-ref",
        "v0.1.0",
        "--reference-source-commit",
        "1" * 40,
        "--imported-by",
        "host-smoke",
        "--reason",
        "Installed runtime initial binding",
    )
    validate_bound = run_installed_cli(
        installed,
        "validate-project",
        "--root",
        str(project_root),
        "--json",
    )

    update_root = workspace / "acme-creative-references-v2"
    if reference_root.is_dir():
        shutil.copytree(reference_root, update_root)
        populate_reviewed_reference_pack(update_root, "0.2.0")
    update_reference = run_installed_cli(
        installed,
        "update-reference-snapshot",
        "--target",
        str(project_root),
        "--reference-pack",
        str(update_root),
        "--reference-source-uri",
        "https://git.invalid/acme-creative-references.git",
        "--reference-source-ref",
        "v0.2.0",
        "--reference-source-commit",
        "2" * 40,
        "--imported-by",
        "host-smoke",
        "--reason",
        "Installed runtime snapshot update",
    )
    validate_updated = run_installed_cli(
        installed,
        "validate-project",
        "--root",
        str(project_root),
        "--json",
    )
    e2e_commands = (
        reviewed_validation,
        seed_project,
        doctor_seed,
        bind_reference,
        validate_bound,
        update_reference,
        validate_updated,
    )
    if any(command.returncode != 0 for command in e2e_commands):
        failure = next(command for command in e2e_commands if command.returncode != 0)
        errors.append(
            f"{check_prefix} runtime Reference Pack bind/update E2E failed: "
            + command_error(failure)
        )
        return checks, errors

    checks.append(f"{check_prefix}-reference-bind-update-e2e")
    checks.append(f"{check_prefix}-project-doctor-runtime")
    rollback_root = workspace / "acme-creative-references-v3"
    shutil.copytree(update_root, rollback_root)
    populate_reviewed_reference_pack(rollback_root, "0.3.0")
    manifest_tmp = project_root / ".creative-craft/project-manifest.json.tmp"
    manifest_tmp.mkdir()
    before_rollback = tree_fingerprint(project_root)
    failed_update = run_installed_cli(
        installed,
        "update-reference-snapshot",
        "--target",
        str(project_root),
        "--reference-pack",
        str(rollback_root),
        "--imported-by",
        "host-smoke",
        "--reason",
        "Synthetic post-write rollback",
    )
    after_rollback = tree_fingerprint(project_root)
    validate_rollback = run_installed_cli(
        installed,
        "validate-project",
        "--root",
        str(project_root),
        "--json",
    )
    if (
        failed_update.returncode == 0
        or before_rollback != after_rollback
        or validate_rollback.returncode != 0
    ):
        errors.append(
            f"{check_prefix} runtime Reference Pack rollback did not restore "
            "the exact project tree"
        )
    else:
        checks.append(f"{check_prefix}-reference-rollback-e2e")
    return checks, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--grok-bin",
        help="optionally verify Grok Skill discovery without invoking a model",
    )
    args = parser.parse_args()
    root = Path(args.root).resolve()
    errors: list[str] = []
    checks: list[str] = []

    package = json.loads((root / "package.json").read_text(encoding="utf-8"))
    pi_skills = package.get("pi", {}).get("skills", [])
    if pi_skills != ["skills/creative-craft"]:
        errors.append("package.json pi.skills must contain only skills/creative-craft")
    else:
        checks.append("pi-package-discovery")
    if package.get("private") is not True:
        errors.append("package.json must remain private because npm distribution is unsupported")
    else:
        checks.append("github-only-distribution")

    plugin = json.loads((root / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
    skill_pointer = plugin.get("skills")
    if skill_pointer != "./skills/":
        errors.append(".codex-plugin/plugin.json skills must equal ./skills/")
    elif not (root / str(skill_pointer) / "creative-craft/SKILL.md").is_file():
        errors.append("Codex plugin skill pointer does not resolve to creative-craft/SKILL.md")
    else:
        checks.append("codex-plugin-discovery")

    grok_adapter = root / "adapters" / "grok" / "README.md"
    if not grok_adapter.is_file():
        errors.append("missing Grok adapter documentation: adapters/grok/README.md")
    else:
        checks.append("grok-adapter-contract")

    if args.grok_bin:
        grok_errors = run_grok_discovery(root, args.grok_bin)
        if grok_errors:
            errors.extend(grok_errors)
        else:
            checks.append("grok-project-skill-discovery")

    with tempfile.TemporaryDirectory() as directory:
        completed = subprocess.run(
            [
                sys.executable,
                str(root / "scripts/install_skill.py"),
                "--target",
                directory,
            ],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        installed = Path(directory) / "creative-craft"
        if completed.returncode != 0:
            errors.append(f"atomic installer failed: {completed.stderr.strip()}")
        elif not (installed / "INSTALL_PROVENANCE.json").is_file():
            errors.append("atomic installer did not write INSTALL_PROVENANCE.json")
        else:
            checks.append("atomic-skill-install")
        if installed.is_dir():
            self_test = subprocess.run(
                [
                    sys.executable,
                    str(installed / "scripts/creative_craft.py"),
                    "self-test",
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            if self_test.returncode != 0:
                errors.append(f"installed runtime self-test failed: {self_test.stdout.strip()}")
            else:
                try:
                    payload = json.loads(self_test.stdout)
                except json.JSONDecodeError as exc:
                    errors.append(f"installed runtime self-test returned invalid JSON: {exc}")
                else:
                    if payload.get("scope") != "runtime" or payload.get("runtime_valid") is not True:
                        errors.append(
                            "installed runtime self-test did not report a valid runtime scope"
                        )
                    else:
                        checks.append("installed-runtime-self-test")
            validation = subprocess.run(
                [
                    sys.executable,
                    str(installed / "scripts/creative_craft.py"),
                    "validate",
                    "--file",
                    str(installed / "templates/image-job.json"),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            if validation.returncode != 0:
                errors.append(f"installed runtime validation failed: {validation.stdout.strip()}")
            else:
                checks.append("installed-runtime")
            brand_root = Path(directory) / "acme-brand"
            brand_init = subprocess.run(
                [
                    sys.executable,
                    str(installed / "scripts/creative_craft.py"),
                    "init-brand-pack",
                    "--target",
                    str(brand_root),
                    "--brand-id",
                    "acme",
                    "--brand-name",
                    "Acme",
                    "--owner",
                    "host-smoke",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            brand_validation = subprocess.run(
                [
                    sys.executable,
                    str(installed / "scripts/creative_craft.py"),
                    "validate-brand-pack",
                    "--root",
                    str(brand_root),
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            if brand_init.returncode != 0 or brand_validation.returncode != 0:
                errors.append(
                    "installed runtime Brand Pack smoke failed: "
                    + (brand_init.stderr.strip() or brand_validation.stdout.strip())
                )
            else:
                checks.append("installed-brand-pack-runtime")
            reference_checks, reference_errors = run_reference_runtime_e2e(
                installed,
                Path(directory),
            )
            checks.extend(reference_checks)
            errors.extend(reference_errors)

    payload = {"valid": not errors, "checks": checks, "errors": errors}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("PASS host package smoke" if not errors else "FAIL host package smoke")
        for check in checks:
            print(f"  PASS: {check}")
        for error in errors:
            print(f"  ERROR: {error}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
