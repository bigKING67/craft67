from __future__ import annotations

import json
import re
import shutil
import tempfile
from pathlib import Path

from .assets import collect_native_evidence, load_release_evidence, validate_assets
from .github_runs import load_artifact_observation, load_observation
from .integrity import repository_head, repository_version, sha256_file
from .policy import ReleaseLevel
from .run_bindings import validate_release_run_bindings


SCHEMA = "design-craft.release-certification.v1"
ARTIFACT_DIGEST_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")


def artifact_name(tag: str, run_id: int) -> str:
    return f"release-certification-{tag}-{run_id}"


def _safe_relative_path(raw: object, *, label: str) -> Path:
    if not isinstance(raw, str) or not raw:
        raise ValueError(f"{label} must be a non-empty relative path")
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{label} must stay relative to its bundle root")
    return path


def _copy_file(source: Path, destination: Path) -> None:
    if source.is_symlink() or not source.is_file():
        raise FileNotFoundError(f"certification source file is missing or unsafe: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _file_record(root: Path, path: Path) -> dict[str, object]:
    relative = path.relative_to(root).as_posix()
    return {
        "path": relative,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def build_certification_bundle(
    output_dir: Path,
    *,
    level: ReleaseLevel,
    tag: str,
    evidence_path: Path,
    evidence_root: Path,
    native_observation: Path,
    benchmark_observation: Path,
    benchmark_result: Path,
    physical_observation: Path | None,
    assets_dir: Path,
    repository: str,
    workflow_run_id: int,
    workflow_run_attempt: int,
) -> dict[str, object]:
    version = repository_version()
    head = repository_head()
    if tag != f"v{version}":
        raise ValueError("certification tag must match the repository version")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("certification repository must be owner/name")
    if level.name == "certified_100" and physical_observation is None:
        raise ValueError("certified_100 certification requires a physical observation")
    if level.name == "operational_95" and physical_observation is not None:
        raise ValueError("operational_95 certification must not include a physical observation")
    for label, value in (
        ("workflow_run_id", workflow_run_id),
        ("workflow_run_attempt", workflow_run_attempt),
    ):
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError(f"{label} must be a positive integer")
    if output_dir.exists() or output_dir.is_symlink():
        raise FileExistsError(f"certification output already exists: {output_dir}")

    evidence = load_release_evidence(evidence_path, level)
    evidence_root = evidence_root.expanduser().resolve()
    bindings = collect_native_evidence(
        evidence,
        level,
        evidence_root=evidence_root,
    )
    native_run = load_observation(native_observation, expected_kind="native")
    benchmark_run = load_observation(
        benchmark_observation,
        expected_kind="benchmark",
    )
    physical_run = (
        load_observation(physical_observation, expected_kind="physical")
        if physical_observation is not None
        else None
    )
    binding_result = validate_release_run_bindings(
        evidence_path,
        level=level,
        native_run=native_run,
        benchmark_run=benchmark_run,
        benchmark_result_path=benchmark_result,
        physical_run=physical_run,
        evidence_root=evidence_root,
    )
    if not binding_result["ok"]:
        raise ValueError("; ".join(binding_result["errors"]))
    asset_result = validate_assets(assets_dir, level=level)
    if not asset_result["ok"]:
        raise ValueError("; ".join(asset_result["errors"]))

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".design-craft-certification-",
        dir=output_dir.parent,
    ) as raw:
        staging = Path(raw) / "bundle"
        staging.mkdir()
        _copy_file(evidence_path, staging / "evidence/release-evidence.json")
        _copy_file(native_observation, staging / "observations/native-run.json")
        _copy_file(
            benchmark_observation,
            staging / "observations/benchmark-run.json",
        )
        _copy_file(
            benchmark_result,
            staging / "benchmark/benchmark-result-full.json",
        )
        if physical_observation is not None:
            _copy_file(
                physical_observation,
                staging / "observations/physical-run.json",
            )
        for binding in bindings.values():
            relative = _safe_relative_path(
                binding.get("evidence_path"),
                label="native evidence_path",
            )
            source = (evidence_root / relative).resolve()
            if source != evidence_root and evidence_root not in source.parents:
                raise ValueError("native evidence_path escapes its evidence root")
            _copy_file(
                source,
                staging / "native-evidence" / relative,
            )
        for name in level.assets(version):
            _copy_file(assets_dir / name, staging / "release" / name)

        files = [
            _file_record(staging, path)
            for path in sorted(staging.rglob("*"))
            if path.is_file()
        ]
        manifest = {
            "schema": SCHEMA,
            "release_level": level.name,
            "tag": tag,
            "source_commit": head,
            "artifact_name": artifact_name(tag, workflow_run_id),
            "certification_workflow": {
                "repository": repository,
                "run_id": workflow_run_id,
                "run_attempt": workflow_run_attempt,
                "workflow": ".github/workflows/release-certify.yml",
                "event": "workflow_dispatch",
                "head_branch": "main",
                "head_sha": head,
            },
            "files": files,
        }
        (staging / "certification.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        validation = validate_certification_bundle(staging, level=level)
        if not validation["ok"]:
            raise RuntimeError("; ".join(validation["errors"]))
        staging.replace(output_dir)
    return validation


def validate_certification_bundle(
    root: Path,
    *,
    level: ReleaseLevel,
    certification_observation: Path | None = None,
    artifact_observation: Path | None = None,
    expected_artifact_id: int | None = None,
    expected_artifact_digest: str | None = None,
) -> dict[str, object]:
    errors: list[str] = []
    manifest_path = root / "certification.json"
    if root.is_symlink() or not root.is_dir():
        errors.append(f"certification bundle is missing or unsafe: {root}")
        manifest: dict[str, object] = {}
    elif manifest_path.is_symlink() or not manifest_path.is_file():
        errors.append("certification bundle is missing certification.json")
        manifest = {}
    else:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"certification manifest is invalid: {exc}")
            manifest = {}
    expected_manifest_keys = {
        "schema",
        "release_level",
        "tag",
        "source_commit",
        "artifact_name",
        "certification_workflow",
        "files",
    }
    if set(manifest) != expected_manifest_keys:
        errors.append("certification manifest fields are invalid")
    if manifest.get("schema") != SCHEMA:
        errors.append(f"certification manifest must use {SCHEMA}")
    version = repository_version()
    head = repository_head()
    if manifest.get("release_level") != level.name:
        errors.append("certification release_level does not match the requested level")
    if manifest.get("tag") != f"v{version}":
        errors.append("certification tag must match the repository version")
    if manifest.get("source_commit") != head:
        errors.append("certification source_commit must match current HEAD")

    file_records = manifest.get("files")
    expected_paths: set[str] = set()
    if not isinstance(file_records, list):
        errors.append("certification files must be an array")
    else:
        for index, record in enumerate(file_records):
            if not isinstance(record, dict):
                errors.append(f"certification file {index} must be an object")
                continue
            if set(record) != {"path", "bytes", "sha256"}:
                errors.append(f"certification file {index} fields are invalid")
                continue
            try:
                relative = _safe_relative_path(
                    record.get("path"),
                    label=f"certification file {index}.path",
                )
            except ValueError as exc:
                errors.append(str(exc))
                continue
            relative_text = relative.as_posix()
            if relative_text in expected_paths:
                errors.append(f"duplicate certification file path: {relative_text}")
                continue
            expected_paths.add(relative_text)
            path = root / relative
            if path.is_symlink() or not path.is_file():
                errors.append(f"certification file is missing or unsafe: {relative_text}")
                continue
            expected_bytes = record.get("bytes")
            if (
                not isinstance(expected_bytes, int)
                or isinstance(expected_bytes, bool)
                or expected_bytes <= 0
            ):
                errors.append(f"certification file bytes are invalid: {relative_text}")
            elif path.stat().st_size != expected_bytes:
                errors.append(f"certification file byte count mismatch: {relative_text}")
            expected_sha = record.get("sha256")
            if not isinstance(expected_sha, str) or re.fullmatch(
                r"[0-9a-f]{64}", expected_sha
            ) is None:
                errors.append(f"certification file digest is invalid: {relative_text}")
            elif sha256_file(path) != expected_sha:
                errors.append(f"certification file digest mismatch: {relative_text}")
    if root.is_dir() and not root.is_symlink():
        unsafe = sorted(
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_symlink()
        )
        if unsafe:
            errors.append(
                "certification bundle contains unsafe symlinks: " + ", ".join(unsafe)
            )
        actual_paths = {
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file()
        }
        allowed = expected_paths | {"certification.json"}
        if actual_paths != allowed:
            errors.append(
                f"certification file set mismatch expected={sorted(allowed)} "
                f"actual={sorted(actual_paths)}"
            )

    workflow = manifest.get("certification_workflow")
    if not isinstance(workflow, dict):
        errors.append("certification_workflow must be an object")
    else:
        expected_workflow_keys = {
            "repository",
            "run_id",
            "run_attempt",
            "workflow",
            "event",
            "head_branch",
            "head_sha",
        }
        if set(workflow) != expected_workflow_keys:
            errors.append("certification_workflow fields are invalid")
        repository = workflow.get("repository")
        if not isinstance(repository, str) or re.fullmatch(
            r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository
        ) is None:
            errors.append("certification_workflow.repository must be owner/name")
        expected_workflow = {
            "workflow": ".github/workflows/release-certify.yml",
            "event": "workflow_dispatch",
            "head_branch": "main",
            "head_sha": head,
        }
        for field, value in expected_workflow.items():
            if workflow.get(field) != value:
                errors.append(f"certification_workflow.{field} must be {value}")
        run_id = workflow.get("run_id")
        run_attempt = workflow.get("run_attempt")
        for field, value in (("run_id", run_id), ("run_attempt", run_attempt)):
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                errors.append(f"certification_workflow.{field} must be a positive integer")
        if isinstance(run_id, int) and not isinstance(run_id, bool) and run_id > 0:
            expected_name = artifact_name(str(manifest.get("tag")), run_id)
            if manifest.get("artifact_name") != expected_name:
                errors.append("certification artifact_name does not match its workflow run")

    evidence_path = root / "evidence/release-evidence.json"
    native_root = root / "native-evidence"
    native_observation = root / "observations/native-run.json"
    benchmark_observation = root / "observations/benchmark-run.json"
    benchmark_result = root / "benchmark/benchmark-result-full.json"
    physical_observation = root / "observations/physical-run.json"
    if not errors:
        try:
            load_release_evidence(evidence_path, level)
            native_run = load_observation(native_observation, expected_kind="native")
            benchmark_run = load_observation(
                benchmark_observation,
                expected_kind="benchmark",
            )
            physical_run = (
                load_observation(physical_observation, expected_kind="physical")
                if level.name == "certified_100"
                else None
            )
            binding_result = validate_release_run_bindings(
                evidence_path,
                level=level,
                native_run=native_run,
                benchmark_run=benchmark_run,
                benchmark_result_path=benchmark_result,
                physical_run=physical_run,
                evidence_root=native_root,
            )
            errors.extend(binding_result["errors"])
            errors.extend(validate_assets(root / "release", level=level)["errors"])
        except (OSError, ValueError, RuntimeError) as exc:
            errors.append(str(exc))

    publication_inputs = (
        certification_observation,
        artifact_observation,
        expected_artifact_id,
        expected_artifact_digest,
    )
    supplied_publication_inputs = [value is not None for value in publication_inputs]
    if any(supplied_publication_inputs) and not all(supplied_publication_inputs):
        errors.append(
            "publication verification requires certification observation, artifact "
            "observation, artifact id, and artifact digest"
        )

    selected_run: dict[str, object] | None = None
    if certification_observation is not None:
        try:
            selected_run = load_observation(
                certification_observation,
                expected_kind="certification",
            )
        except (OSError, ValueError, RuntimeError) as exc:
            errors.append(str(exc))
        else:
            if isinstance(workflow, dict):
                for manifest_key, run_key in (
                    ("repository", "repository"),
                    ("run_id", "id"),
                    ("run_attempt", "attempt"),
                    ("head_branch", "head_branch"),
                    ("head_sha", "head_sha"),
                ):
                    if workflow.get(manifest_key) != selected_run.get(run_key):
                        errors.append(
                            f"certification_workflow.{manifest_key} does not match selected run"
                        )

    if artifact_observation is not None:
        try:
            expected_repository = (
                workflow.get("repository") if isinstance(workflow, dict) else None
            )
            selected_artifact = load_artifact_observation(
                artifact_observation,
                expected_repository=(
                    expected_repository
                    if isinstance(expected_repository, str)
                    else None
                ),
            )
        except (OSError, ValueError, RuntimeError) as exc:
            errors.append(str(exc))
        else:
            if expected_artifact_id is None or expected_artifact_digest is None:
                errors.append("artifact verification requires explicit id and digest")
            else:
                if selected_artifact.get("id") != expected_artifact_id:
                    errors.append("artifact observation id does not match the explicit input")
                if selected_artifact.get("digest") != expected_artifact_digest:
                    errors.append("artifact observation digest does not match the explicit input")
                if selected_artifact.get("name") != manifest.get("artifact_name"):
                    errors.append("artifact observation name does not match the bundle manifest")
                artifact_run = selected_artifact.get("workflow_run")
                if isinstance(workflow, dict) and isinstance(artifact_run, dict):
                    for artifact_key, manifest_key in (
                        ("id", "run_id"),
                        ("head_branch", "head_branch"),
                        ("head_sha", "head_sha"),
                    ):
                        if artifact_run.get(artifact_key) != workflow.get(manifest_key):
                            errors.append(
                                "artifact observation workflow run does not match the "
                                f"bundle manifest {manifest_key}"
                            )
                if isinstance(selected_run, dict) and isinstance(artifact_run, dict):
                    for field in ("id", "head_branch", "head_sha"):
                        if artifact_run.get(field) != selected_run.get(field):
                            errors.append(
                                "artifact observation workflow run does not match the "
                                f"selected certification run {field}"
                            )
                if ARTIFACT_DIGEST_PATTERN.fullmatch(expected_artifact_digest) is None:
                    errors.append("explicit artifact digest must be sha256:<64 lowercase hex>")

    return {
        "schema": SCHEMA,
        "release_level": level.name,
        "tag": manifest.get("tag"),
        "source_commit": manifest.get("source_commit"),
        "artifact_name": manifest.get("artifact_name"),
        "file_count": len(expected_paths),
        "ok": not errors,
        "errors": errors,
    }


__all__ = [
    "ARTIFACT_DIGEST_PATTERN",
    "SCHEMA",
    "artifact_name",
    "build_certification_bundle",
    "validate_certification_bundle",
]
