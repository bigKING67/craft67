#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_SCRIPT = ROOT / "scripts/package_e2e_fixture.py"


class PackageCheckError(RuntimeError):
    pass


def _resolve_command(command: list[str]) -> list[str]:
    executable = command[0]
    if Path(executable).is_absolute():
        return command
    resolved = shutil.which(executable)
    if resolved is None:
        raise PackageCheckError(f"command not found: {executable}")
    return [resolved, *command[1:]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the exact Review Craft npm package")
    parser.add_argument(
        "--tarball", help="Validate an existing tarball instead of running npm pack"
    )
    parser.add_argument("--output-tarball", help="Preserve the newly packed exact tarball here")
    parser.add_argument("--receipt", help="Write a machine-readable package-check receipt")
    return parser.parse_args()


def _run(
    command: list[str],
    *,
    cwd: Path,
    environment: dict[str, str] | None = None,
    label: str,
    allowed_codes: set[int] | None = None,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        _resolve_command(command),
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    allowed = allowed_codes or {0}
    if completed.returncode not in allowed:
        detail = completed.stderr.strip() or completed.stdout.strip() or "no output"
        raise PackageCheckError(f"{label} failed: {detail}")
    return completed


def _isolated_environment(home: Path) -> dict[str, str]:
    environment = dict(os.environ)
    environment["HOME"] = str(home)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment.pop("PYTHONPATH", None)
    return environment


def _pack(destination: Path) -> Path:
    completed = _run(
        [
            "npm",
            "pack",
            "--ignore-scripts",
            "--pack-destination",
            str(destination),
            "--json",
        ],
        cwd=ROOT,
        label="npm pack",
    )
    payload = json.loads(completed.stdout)
    if not isinstance(payload, list) or len(payload) != 1:
        raise PackageCheckError("npm pack returned an unexpected manifest")
    return (destination / payload[0]["filename"]).resolve(strict=True)


def _archive_metadata(tarball: Path) -> tuple[list[str], str]:
    with tarfile.open(tarball, "r:gz") as archive:
        members = archive.getmembers()
        names = sorted(member.name for member in members if member.isfile())
        package_json = archive.extractfile("package/package.json")
        if package_json is None:
            raise PackageCheckError("packed artifact is missing package/package.json")
        version = json.loads(package_json.read())["version"]
    return names, version


def _boundary_errors(names: list[str], contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    allowed_roots = set(contract["allowedRoots"])
    for name in names:
        path = PurePosixPath(name)
        if not path.parts or path.parts[0] != "package" or ".." in path.parts:
            errors.append(f"unsafe packaged path: {name}")
            continue
        relative = path.relative_to("package")
        allowed = any(
            relative == PurePosixPath(root) or PurePosixPath(root) in relative.parents
            for root in allowed_roots
        )
        if not allowed:
            errors.append(f"unexpected packaged path: {name}")
        for segment in contract["forbiddenSegments"]:
            if segment in name:
                errors.append(f"forbidden packaged segment {segment!r}: {name}")
    missing = sorted(set(contract["requiredPackageFiles"]) - set(names))
    errors.extend(f"missing packaged file: {name}" for name in missing)
    return errors


def _runtime_command(
    package_root: Path,
    arguments: list[str],
    *,
    cwd: Path,
    environment: dict[str, str],
    label: str,
) -> dict[str, Any]:
    script = package_root / "skills/review-craft/scripts/review_craft.py"
    completed = _run(
        [sys.executable, str(script), *arguments],
        cwd=cwd,
        environment=environment,
        label=label,
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise PackageCheckError(f"{label} returned invalid JSON: {error}") from error
    if not isinstance(payload, dict):
        raise PackageCheckError(f"{label} returned a non-object JSON document")
    return payload


def _target_snapshot(target: Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(target.rglob("*")):
        if not path.is_file() or ".git" in path.relative_to(target).parts:
            continue
        content = path.read_bytes()
        rows.append(
            {
                "path": path.relative_to(target).as_posix(),
                "size": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    return rows


def _git(target: Path, *arguments: str) -> str:
    return _run(
        ["git", *arguments],
        cwd=target,
        label=f"git {' '.join(arguments)}",
    ).stdout.rstrip("\n")


def _create_target(root: Path) -> Path:
    target = root / "target"
    target.mkdir()
    (target / "app.py").write_text("def answer():\n    return 41\n", encoding="utf-8")
    behavior = (
        "import json; from pathlib import Path; "
        "assert 'return 42' in Path('app.py').read_text(encoding='utf-8'); "
        "print(json.dumps({'checks': {'fixed': True}}))"
    )
    config = {
        "commands": {
            "check": {
                "argv": [sys.executable, "-c", behavior],
                "evidenceClaims": [
                    {
                        "id": "fixed-behavior-check",
                        "kind": "test",
                        "jsonPointer": "/checks/fixed",
                        "equals": True,
                    }
                ],
            }
        }
    }
    (target / ".review-craft.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _git(target, "init", "--quiet")
    _git(target, "config", "user.email", "package-e2e@example.invalid")
    _git(target, "config", "user.name", "Review Craft Package E2E")
    _git(target, "add", "--", "app.py", ".review-craft.json")
    _git(target, "commit", "--quiet", "-m", "package fixture baseline")
    return target


def _fixture_command(
    package_root: Path,
    arguments: list[str],
    *,
    cwd: Path,
    environment: dict[str, str],
    label: str,
) -> None:
    _run(
        [
            sys.executable,
            str(FIXTURE_SCRIPT),
            "--package-root",
            str(package_root),
            *arguments,
        ],
        cwd=cwd,
        environment=environment,
        label=label,
    )


def _canonical_e2e(
    *,
    package_root: Path,
    work_root: Path,
    environment: dict[str, str],
) -> tuple[Path, Path, list[dict[str, Any]]]:
    target = _create_target(work_root)
    initial = _target_snapshot(target)
    runs = work_root / "runs"
    preflight = _runtime_command(
        package_root,
        [
            "preflight",
            "--target",
            str(target),
            "--config",
            str(target / ".review-craft.json"),
            "--output-root",
            str(runs),
        ],
        cwd=work_root,
        environment=environment,
        label="installed preflight",
    )
    run_dir = Path(preflight["runDir"]).resolve(strict=True)
    note = work_root / "registered-evidence.txt"
    note.write_text("Installed package E2E evidence.\n", encoding="utf-8")
    _runtime_command(
        package_root,
        [
            "register-evidence",
            "--run-dir",
            str(run_dir),
            "--id",
            "package-e2e-note",
            "--source",
            str(note),
            "--kind",
            "other",
            "--producer",
            "package-check",
            "--description",
            "Evidence registered by the exact installed-package E2E.",
            "--media-type",
            "text/plain",
        ],
        cwd=work_root,
        environment=environment,
        label="installed evidence registration",
    )
    _fixture_command(
        package_root,
        ["populate-run", "--run-dir", str(run_dir)],
        cwd=work_root,
        environment=environment,
        label="installed canonical fixture authoring",
    )
    _runtime_command(
        package_root,
        ["validate", "--run-dir", str(run_dir), "--allow-draft"],
        cwd=work_root,
        environment=environment,
        label="installed draft validation",
    )
    _runtime_command(
        package_root,
        ["finalize", "--run-dir", str(run_dir)],
        cwd=work_root,
        environment=environment,
        label="installed finalization",
    )
    _runtime_command(
        package_root,
        ["validate", "--run-dir", str(run_dir)],
        cwd=work_root,
        environment=environment,
        label="installed sealed validation",
    )
    if not (run_dir / "report.md").is_file():
        raise PackageCheckError("installed finalization did not create report.md")
    if _target_snapshot(target) != initial or _git(target, "status", "--porcelain=v1"):
        raise PackageCheckError("canonical installed runtime mutated the target repository")
    return target, run_dir, initial


def _remediation_e2e(
    *,
    package_root: Path,
    work_root: Path,
    target: Path,
    run_dir: Path,
    initial: list[dict[str, Any]],
    environment: dict[str, str],
) -> None:
    prepared = _runtime_command(
        package_root,
        [
            "prepare-fix",
            "--run-dir",
            str(run_dir),
            "--finding",
            "RC-FINDING-001",
            "--command",
            "check",
            "--output-root",
            str(work_root / "fixes"),
        ],
        cwd=work_root,
        environment=environment,
        label="installed fix preparation",
    )
    fix_dir = Path(prepared["fixDir"]).resolve(strict=True)
    if _target_snapshot(target) != initial:
        raise PackageCheckError("installed fix preparation mutated the target repository")
    (target / "app.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
    expected_after_edit = _target_snapshot(target)
    captured = _runtime_command(
        package_root,
        ["capture-fix-attempt", "--fix-dir", str(fix_dir)],
        cwd=work_root,
        environment=environment,
        label="installed fix attempt capture",
    )
    attempt_dir = Path(captured["attemptDir"]).resolve(strict=True)
    assessment = work_root / "attempt-assessment.json"
    _fixture_command(
        package_root,
        [
            "write-assessment",
            "--attempt-dir",
            str(attempt_dir),
            "--output",
            str(assessment),
        ],
        cwd=work_root,
        environment=environment,
        label="installed attempt assessment authoring",
    )
    _runtime_command(
        package_root,
        [
            "finalize-fix-attempt",
            "--attempt-dir",
            str(attempt_dir),
            "--assessment",
            str(assessment),
        ],
        cwd=work_root,
        environment=environment,
        label="installed fix attempt finalization",
    )
    _runtime_command(
        package_root,
        ["validate-fix-attempt", "--attempt-dir", str(attempt_dir)],
        cwd=work_root,
        environment=environment,
        label="installed fix attempt validation",
    )
    lineage = _runtime_command(
        package_root,
        ["list-fix-attempts", "--fix-dir", str(fix_dir)],
        cwd=work_root,
        environment=environment,
        label="installed fix lineage validation",
    )
    if lineage.get("aggregateStatus") != "VERIFIED":
        raise PackageCheckError("installed fix lineage did not finish VERIFIED")
    status_paths = [line[3:] for line in _git(target, "status", "--porcelain=v1").splitlines()]
    if status_paths != ["app.py"] or _target_snapshot(target) != expected_after_edit:
        raise PackageCheckError(
            "installed remediation runtime caused an undeclared target mutation"
        )


def _assurance_e2e(
    *,
    package_root: Path,
    work_root: Path,
    target: Path,
    environment: dict[str, str],
) -> None:
    preflight = _runtime_command(
        package_root,
        [
            "preflight",
            "--target",
            str(target),
            "--config",
            str(target / ".review-craft.json"),
            "--assurance",
            "fast",
            "--output-root",
            str(work_root / "fast-runs"),
        ],
        cwd=work_root,
        environment=environment,
        label="installed fast-assurance preflight",
    )
    run_dir = Path(preflight["runDir"]).resolve(strict=True)
    manifest = json.loads((run_dir / "review-manifest.json").read_text(encoding="utf-8"))
    scope = json.loads((run_dir / "review-scope.json").read_text(encoding="utf-8"))
    scorecard = json.loads((run_dir / "scorecard.json").read_text(encoding="utf-8"))
    if manifest["configuration"].get("assuranceLevel") != "fast":
        raise PackageCheckError("installed preflight did not preserve fast assurance")
    if (
        scope.get("assuranceLevel") != "fast"
        or scorecard.get("assurance", {}).get("level") != "fast"
    ):
        raise PackageCheckError("installed fast assurance artifacts are inconsistent")
    _runtime_command(
        package_root,
        ["validate", "--run-dir", str(run_dir), "--allow-draft"],
        cwd=work_root,
        environment=environment,
        label="installed fast-assurance draft validation",
    )


def _install_and_test(tarball: Path, version: str, temporary: Path) -> None:
    install_root = temporary / "installed"
    _run(
        [
            "npm",
            "install",
            "--ignore-scripts",
            "--no-audit",
            "--no-fund",
            "--prefix",
            str(install_root),
            str(tarball),
        ],
        cwd=temporary,
        label="packed artifact installation",
    )
    package_root = install_root / "node_modules/@bigking67/review-craft"
    home = temporary / "home"
    work_root = temporary / "e2e"
    home.mkdir()
    work_root.mkdir()
    environment = _isolated_environment(home)
    doctor = _runtime_command(
        package_root,
        ["doctor", "--json"],
        cwd=work_root,
        environment=environment,
        label="packaged runtime doctor",
    )
    if doctor.get("ready") is not True or doctor.get("version") != version:
        raise PackageCheckError("packaged runtime doctor identity does not match the tarball")
    target, run_dir, initial = _canonical_e2e(
        package_root=package_root,
        work_root=work_root,
        environment=environment,
    )
    _assurance_e2e(
        package_root=package_root,
        work_root=work_root,
        target=target,
        environment=environment,
    )
    _remediation_e2e(
        package_root=package_root,
        work_root=work_root,
        target=target,
        run_dir=run_dir,
        initial=initial,
        environment=environment,
    )


def _receipt(tarball: Path, *, version: str, file_count: int) -> dict[str, Any]:
    node = _run(["node", "--version"], cwd=ROOT, label="node version").stdout.strip()
    return {
        "schema": "review-craft.package-check-receipt.v1",
        "packageVersion": version,
        "sha256": hashlib.sha256(tarball.read_bytes()).hexdigest(),
        "sizeBytes": tarball.stat().st_size,
        "fileCount": file_count,
        "platform": platform.platform(),
        "pythonVersion": platform.python_version(),
        "nodeVersion": node,
        "checks": {
            "packageBoundary": "PASSED",
            "installation": "PASSED",
            "doctor": "PASSED",
            "canonicalE2E": "PASSED",
            "assuranceE2E": "PASSED",
            "remediationE2E": "PASSED",
            "targetMutationBoundary": "PASSED",
        },
    }


def main() -> int:
    args = parse_args()
    if args.tarball and args.output_tarball:
        print(
            "review-craft package check: --output-tarball requires a new npm pack",
            file=sys.stderr,
        )
        return 2
    try:
        contract = json.loads(
            (ROOT / "contracts/package-boundary.json").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory(prefix="review-craft-package-") as directory:
            temporary = Path(directory)
            tarball = (
                Path(args.tarball).expanduser().resolve(strict=True)
                if args.tarball
                else _pack(temporary)
            )
            names, version = _archive_metadata(tarball)
            errors = _boundary_errors(names, contract)
            if errors:
                raise PackageCheckError("; ".join(errors))
            _install_and_test(tarball, version, temporary)
            receipt = _receipt(tarball, version=version, file_count=len(names))
            if args.output_tarball:
                output = Path(args.output_tarball).expanduser().resolve()
                output.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(tarball, output)
            if args.receipt:
                receipt_path = Path(args.receipt).expanduser().resolve()
                receipt_path.parent.mkdir(parents=True, exist_ok=True)
                receipt_path.write_text(
                    json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
                )
    except (OSError, ValueError, KeyError, json.JSONDecodeError, PackageCheckError) as error:
        print(f"review-craft package check: {error}", file=sys.stderr)
        return 1
    print(f"review-craft package check passed ({len(names)} files, exact installed E2E)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
