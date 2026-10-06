#!/usr/bin/env python3
"""Build a deterministic release archive with exact-source quality evidence."""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
import os
import secrets
import shutil
import statistics
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "skill-pack.json"
BUILDER = ROOT / "tooling/build/build_skill_bundles.py"
SELECTION_CASES = ROOT / "eval/forward-routing/cases.json"
EXECUTION_CASES = ROOT / "eval/execution/cases.json"
JUDGE_RUBRIC = ROOT / "eval/structured-judge/rubric.json"
JUDGE_SCHEMA = ROOT / "eval/structured-judge/output.schema.json"
JUDGE_CALIBRATION_CASES = ROOT / "eval/structured-judge/cases.json"
JUDGE_PROMPT_COMMERCE = ROOT / "eval/cases.json"
JUDGE_PROMPT_MARKETING = ROOT / "eval/marketing/cases.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tooling.installation.tree_integrity import (
    TreeIntegrityError,
    is_runtime_cache,
    lexical_absolute,
    tree_hashes,
    validate_real_directory,
    validate_tree,
)
from tooling.manifest import ManifestError, load_manifest, parse_semantic_version
from tooling.build.verify_release import ReleaseVerificationError, verify_release_directory


class ReleasePackagingError(RuntimeError):
    pass


FaultInjector = Callable[[str, Path], None]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare_real_directory(path: Path) -> Path:
    candidate = lexical_absolute(path)
    missing: list[Path] = []
    existing = candidate
    while not os.path.lexists(existing):
        missing.append(existing)
        parent = existing.parent
        if parent == existing:
            raise ReleasePackagingError(f"release output has no existing ancestor: {candidate}")
        existing = parent
    try:
        normalized = validate_real_directory(existing)
    except TreeIntegrityError as exc:
        raise ReleasePackagingError(f"release output must have a real directory ancestor: {exc}") from exc
    for component in reversed(missing):
        normalized /= component.name
        try:
            normalized.mkdir(mode=0o755)
        except FileExistsError:
            pass
        try:
            normalized = validate_real_directory(normalized)
        except TreeIntegrityError as exc:
            raise ReleasePackagingError(f"release output must be a real directory: {exc}") from exc
    return normalized


def fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_fsynced_text(path: Path, content: str, *, encoding: str) -> None:
    with path.open("x", encoding=encoding) as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())


def git_value(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def case_ids(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = payload.get("cases")
    if not isinstance(cases, list) or any(not isinstance(case, dict) for case in cases):
        raise ReleasePackagingError(f"cases must be a list: {path}")
    ids = [case.get("id") for case in cases]
    if any(not isinstance(case_id, str) for case_id in ids) or len(ids) != len(set(ids)):
        raise ReleasePackagingError(f"case ids must be unique strings: {path}")
    return ids


def calibration_contract(path: Path) -> tuple[list[str], dict[str, Path]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = payload.get("cases")
    if not isinstance(cases, list):
        raise ReleasePackagingError(f"calibration cases must be a list: {path}")
    selected = [
        case
        for case in cases
        if isinstance(case, dict) and case.get("expected_pass") is False
    ]
    ids = [case.get("id") for case in selected]
    if not ids or any(not isinstance(case_id, str) for case_id in ids) or len(ids) != len(set(ids)):
        raise ReleasePackagingError("calibration case ids must be unique strings")
    answers: dict[str, Path] = {}
    for case in selected:
        configured = case.get("answer")
        relative = Path(configured) if isinstance(configured, str) else None
        if (
            relative is None
            or relative.is_absolute()
            or not relative.parts
            or relative.parts[0] != "eval"
            or ".." in relative.parts
        ):
            raise ReleasePackagingError(f"invalid calibration answer path: {configured!r}")
        answer = ROOT / relative
        try:
            validate_tree(answer, allowed_root=ROOT)
        except TreeIntegrityError as exc:
            raise ReleasePackagingError(f"invalid calibration answer: {answer}: {exc}") from exc
        answers[f"calibration_answer:{case['id']}"] = answer
    return ids, answers


def validate_release_tree(root: Path) -> None:
    for path in validate_tree(root, require_directory=True):
        if is_runtime_cache(path.relative_to(root)):
            raise ReleasePackagingError(f"release tree contains runtime cache artifact: {path}")


def validate_quality_evidence(
    payload: dict[str, Any],
    *,
    evidence_path: Path,
    expected_head: str,
    expected_input_sha256: dict[str, str],
    expected_selection_cases: list[dict[str, Any]],
    expected_execution_cases: list[dict[str, Any]],
    expected_calibration_cases: list[dict[str, Any]],
    rubric: dict[str, Any],
) -> dict[str, Any]:
    expected_selection_ids = [case["id"] for case in expected_selection_cases]
    expected_execution_ids = [case["id"] for case in expected_execution_cases]
    expected_calibration_ids = [case["id"] for case in expected_calibration_cases]
    selection_cases = {case["id"]: case for case in expected_selection_cases}
    execution_cases = {case["id"]: case for case in expected_execution_cases}
    calibration_cases = {case["id"]: case for case in expected_calibration_cases}
    if any(
        len(cases) != len(case_ids)
        for cases, case_ids in (
            (selection_cases, expected_selection_ids),
            (execution_cases, expected_execution_ids),
            (calibration_cases, expected_calibration_ids),
        )
    ):
        raise ReleasePackagingError("canonical quality case ids must be unique")

    requested_evidence_path = lexical_absolute(evidence_path)
    try:
        run_dir = validate_real_directory(requested_evidence_path.parent)
        evidence_path = run_dir / requested_evidence_path.name
        validate_tree(evidence_path, allowed_root=run_dir)
    except TreeIntegrityError as exc:
        raise ReleasePackagingError(f"quality evidence path is unsafe: {exc}") from exc
    if os.path.lexists(run_dir / ".quality-regression.lock"):
        raise ReleasePackagingError("quality evidence run is still locked or incomplete")

    metadata = payload.get("metadata")
    if payload.get("schema_version") != 1:
        raise ReleasePackagingError("quality evidence has an unsupported schema_version")
    if payload.get("passed") is not True or not isinstance(metadata, dict):
        raise ReleasePackagingError("quality evidence must be a passing quality-regression artifact")
    run_id = payload.get("run_id")
    if not isinstance(run_id, str) or not run_id or metadata.get("run_id") != run_id:
        raise ReleasePackagingError("quality evidence run identity is missing or inconsistent")
    if metadata.get("evidence_type") != "quality-regression":
        raise ReleasePackagingError("quality evidence has the wrong evidence_type")
    if metadata.get("git_dirty") is not False or metadata.get("git_head") != expected_head:
        raise ReleasePackagingError("quality evidence must come from the current clean Git HEAD")
    input_hashes = metadata.get("input_sha256")
    if not isinstance(input_hashes, dict):
        raise ReleasePackagingError("quality evidence is missing canonical input hashes")
    mismatched_inputs = [
        name
        for name, expected in expected_input_sha256.items()
        if input_hashes.get(name) != expected
    ]
    if mismatched_inputs:
        raise ReleasePackagingError(
            "quality evidence input hashes do not match canonical source: "
            + ", ".join(mismatched_inputs)
        )
    plan = metadata.get("plan")
    selected = plan.get("selected_case_ids") if isinstance(plan, dict) else None
    if not isinstance(selected, dict):
        raise ReleasePackagingError("quality evidence is missing the selected case plan")
    if plan.get("layers") != ["selection", "execution", "judge", "calibration"]:
        raise ReleasePackagingError("quality evidence did not run all required quality layers")
    if selected.get("selection") != expected_selection_ids:
        raise ReleasePackagingError("quality evidence does not cover the full selection suite")
    if selected.get("execution") != expected_execution_ids or selected.get("judge") != expected_execution_ids:
        raise ReleasePackagingError("quality evidence does not cover the full execution and judge suites")
    if selected.get("calibration") != expected_calibration_ids:
        raise ReleasePackagingError("quality evidence does not cover the full judge-calibration suite")
    active_install = plan.get("active_install")
    if not isinstance(active_install, dict) or active_install.get("parity_verified") is not True:
        raise ReleasePackagingError("quality evidence did not verify active-install parity")
    models = plan.get("models")
    requested_model = metadata.get("requested_model")
    if (
        not isinstance(models, dict)
        or set(models) != {"selection", "execution", "judge"}
        or not isinstance(requested_model, str)
        or not requested_model
        or any(models.get(layer) != requested_model for layer in models)
    ):
        raise ReleasePackagingError(
            "release quality evidence must bind every layer to one explicit requested model"
        )

    if payload.get("runtime_errors") != [] or payload.get("quality_failures") != []:
        raise ReleasePackagingError("quality evidence reports runtime or quality failures")

    def exact_results(layer: str, expected_ids: list[str]) -> list[dict[str, Any]]:
        results = payload.get(layer)
        if not isinstance(results, list) or any(not isinstance(result, dict) for result in results):
            raise ReleasePackagingError(f"quality evidence {layer} results are missing or invalid")
        ids = [result.get("id") for result in results]
        if ids != expected_ids or len(ids) != len(set(ids)):
            raise ReleasePackagingError(f"quality evidence {layer} results are incomplete or reordered")
        return results

    selection = exact_results("selection", expected_selection_ids)
    execution = exact_results("execution", expected_execution_ids)
    judged = exact_results("judge", expected_execution_ids)
    calibration = exact_results("calibration", expected_calibration_ids)
    for result in selection:
        case = selection_cases[result["id"]]
        expected = sorted(case.get("expected", []))
        response = result.get("response")
        try:
            response_payload = json.loads(response) if isinstance(response, str) else None
        except json.JSONDecodeError as exc:
            raise ReleasePackagingError("quality evidence contains invalid selection response JSON") from exc
        if not isinstance(response_payload, dict):
            raise ReleasePackagingError("quality evidence contains a missing selection response")
        selected_skills = sorted(response_payload.get("selected_skills", []))
        reason = response_payload.get("reason")
        if (
            result.get("passed") is not True
            or "error" in result
            or result.get("expected") != expected
            or result.get("selected") != selected_skills
            or selected_skills != expected
            or len(expected) != len(set(expected))
            or not isinstance(reason, str)
            or result.get("reason") != reason
            or result.get("prompt_sha256")
            != hashlib.sha256(case["prompt"].encode("utf-8")).hexdigest()
            or result.get("response_sha256")
            != hashlib.sha256(response.encode("utf-8")).hexdigest()
            or result.get("model") != requested_model
        ):
            raise ReleasePackagingError("quality evidence contains an invalid selection result")

    try:
        answer_dir = validate_real_directory(run_dir / "answers")
        answer_files = validate_tree(answer_dir, require_directory=True)
    except TreeIntegrityError as exc:
        raise ReleasePackagingError(f"quality evidence answers are unsafe: {exc}") from exc
    expected_answer_names = [f"{case_id}.txt" for case_id in expected_execution_ids]
    actual_answer_names = sorted(path.relative_to(answer_dir).as_posix() for path in answer_files)
    if actual_answer_names != sorted(expected_answer_names):
        raise ReleasePackagingError("quality evidence answer files are incomplete or unexpected")

    for result in execution:
        case = execution_cases[result["id"]]
        answer_path = answer_dir / f"{result['id']}.txt"
        digest = result.get("answer_sha256")
        if (
            result.get("generated") is not True
            or "error" in result
            or digest != sha256_file(answer_path)
            or result.get("prompt_sha256")
            != hashlib.sha256(case["prompt"].encode("utf-8")).hexdigest()
            or result.get("skill") != case.get("skill")
            or result.get("domain") != case.get("domain")
            or result.get("model") != requested_model
            or not isinstance(result.get("answer_path"), str)
            or lexical_absolute(Path(result["answer_path"])) != answer_path
        ):
            raise ReleasePackagingError("quality evidence contains an invalid execution result")
        if input_hashes.get(f"answer:{result['id']}") != digest:
            raise ReleasePackagingError(
                f"quality evidence answer hash does not match execution result: {result['id']}"
            )

    dimensions = rubric.get("dimensions")
    scale = rubric.get("scale")
    pass_contract = rubric.get("pass")
    if not isinstance(dimensions, dict) or not isinstance(scale, dict) or not isinstance(pass_contract, dict):
        raise ReleasePackagingError("canonical judge rubric is invalid")

    def validate_judge_result(
        result: dict[str, Any],
        case: dict[str, Any],
        expected_quality: bool,
        label: str,
    ) -> int:
        attempts = result.get("attempts")
        if (
            result.get("passed") is not True
            or result.get("expected_quality_pass") is not expected_quality
            or result.get("domain") != case.get("domain")
            or "error" in result
            or not isinstance(attempts, list)
            or not attempts
        ):
            raise ReleasePackagingError(f"quality evidence contains an invalid {label} result")
        for attempt in attempts:
            if not isinstance(attempt, dict) or attempt.get("ok") is not True:
                raise ReleasePackagingError(f"quality evidence contains an invalid {label} attempt")
            response = attempt.get("response")
            try:
                response_payload = json.loads(response) if isinstance(response, str) else None
            except json.JSONDecodeError as exc:
                raise ReleasePackagingError(f"quality evidence contains invalid {label} response JSON") from exc
            if not isinstance(response_payload, dict):
                raise ReleasePackagingError(f"quality evidence contains a missing {label} response")
            scores = response_payload.get("scores")
            hard_failures = response_payload.get("hard_failures")
            summary = response_payload.get("summary")
            if (
                not isinstance(scores, dict)
                or set(scores) != set(dimensions)
                or any(
                    type(score) is not int or not scale["min"] <= score <= scale["max"]
                    for score in scores.values()
                )
                or not isinstance(hard_failures, list)
                or any(not isinstance(item, str) for item in hard_failures)
                or not isinstance(summary, str)
                or not summary.strip()
            ):
                raise ReleasePackagingError(f"quality evidence contains invalid {label} scores")
            total = sum(scores.values())
            quality_passed = (
                total >= pass_contract["minimum_total"]
                and min(scores.values()) >= pass_contract["minimum_dimension"]
                and (
                    not pass_contract["hard_failures_must_be_empty"]
                    or not hard_failures
                )
            )
            duration = attempt.get("duration_seconds")
            if (
                attempt.get("scores") != scores
                or attempt.get("hard_failures") != hard_failures
                or attempt.get("summary") != summary
                or attempt.get("total") != total
                or attempt.get("quality_passed") is not quality_passed
                or attempt.get("model") != requested_model
                or type(duration) not in {int, float}
                or duration < 0
                or attempt.get("response_sha256")
                != hashlib.sha256(response.encode("utf-8")).hexdigest()
            ):
                raise ReleasePackagingError(f"quality evidence {label} attempt is internally inconsistent")
        votes = sum(attempt["quality_passed"] for attempt in attempts)
        aggregate_quality = votes > len(attempts) / 2
        median_total = statistics.median(attempt["total"] for attempt in attempts)
        median_scores = {
            name: statistics.median(attempt["scores"][name] for attempt in attempts)
            for name in dimensions
        }
        duration_seconds = round(sum(attempt["duration_seconds"] for attempt in attempts), 3)
        if (
            result.get("attempt_count") != len(attempts)
            or result.get("quality_pass_votes") != votes
            or result.get("quality_passed") is not aggregate_quality
            or aggregate_quality is not expected_quality
            or result.get("median_total") != median_total
            or result.get("median_scores") != median_scores
            or result.get("duration_seconds") != duration_seconds
            or result.get("aggregate")
            != "strict-majority quality verdict; median scores for reporting; ties fail quality"
        ):
            raise ReleasePackagingError(f"quality evidence {label} aggregate does not match its attempts")
        return len(attempts)

    judge_calls = sum(
        validate_judge_result(result, execution_cases[result["id"]], True, "judge")
        for result in judged
    )
    judge_calls += sum(
        validate_judge_result(
            result,
            calibration_cases[result["id"]],
            False,
            "judge-calibration",
        )
        for result in calibration
    )

    expected_calls = len(selection) + len(execution) + judge_calls
    if payload.get("model_calls") != expected_calls or metadata.get("actual_model_calls") != expected_calls:
        raise ReleasePackagingError("quality evidence model-call count does not match layer results")

    checkpoint_path = run_dir / "checkpoint.json"
    try:
        validate_tree(checkpoint_path, allowed_root=run_dir)
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    except (OSError, TreeIntegrityError, json.JSONDecodeError) as exc:
        raise ReleasePackagingError(f"quality evidence checkpoint is missing or invalid: {exc}") from exc
    if (
        checkpoint.get("schema_version") != 1
        or checkpoint.get("run_id") != run_id
        or checkpoint.get("status") != "passed"
        or checkpoint.get("stage") != "completed"
        or checkpoint.get("plan") != plan
        or checkpoint.get("model_calls") != expected_calls
        or any(checkpoint.get(layer) != payload.get(layer) for layer in ("selection", "execution", "judge", "calibration"))
    ):
        raise ReleasePackagingError("quality evidence checkpoint does not bind the completed passing run")
    return metadata


def validate_bundle_parity(bundle_root: Path, install_root: Path, skill_names: list[str]) -> dict[str, dict[str, str]]:
    try:
        validate_real_directory(bundle_root)
        validate_real_directory(install_root)
    except TreeIntegrityError as exc:
        raise ReleasePackagingError(f"bundle/install root must be a real directory: {exc}") from exc
    actual = sorted(path.name for path in bundle_root.iterdir())
    if actual != sorted(skill_names):
        raise ReleasePackagingError(f"bundle root must contain exactly the manifest Skills: {actual}")
    hashes: dict[str, dict[str, str]] = {}
    for name in skill_names:
        bundle = bundle_root / name
        installed = install_root / name
        validate_release_tree(bundle)
        validate_release_tree(installed)
        hashes[name] = tree_hashes(bundle)
        if hashes[name] != tree_hashes(installed):
            raise ReleasePackagingError(f"isolated installation differs from release Bundle: {name}")
    return hashes


def active_evidence_tree_digest(root: Path) -> str:
    entries = []
    for path in validate_tree(root, require_directory=True):
        relative = path.relative_to(root)
        if is_runtime_cache(relative):
            continue
        entries.append({"path": relative.as_posix(), "sha256": sha256_file(path)})
    encoded = json.dumps(entries, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def validate_quality_active_install(
    metadata: dict[str, Any],
    bundle_root: Path,
    skill_names: list[str],
) -> None:
    plan = metadata.get("plan")
    active = plan.get("active_install") if isinstance(plan, dict) else None
    if not isinstance(active, dict):
        raise ReleasePackagingError("quality evidence is missing active-install details")
    if (
        active.get("parity_verified") is not True
        or active.get("runtime_discovery_override") is not False
        or active.get("discovery_mode") != "canonical-active-root-parity"
        or active.get("selected_skills") != skill_names
    ):
        raise ReleasePackagingError("quality evidence active-install contract is incomplete")
    expected = {name: active_evidence_tree_digest(bundle_root / name) for name in skill_names}
    if active.get("active_bundle_tree_sha256") != expected:
        raise ReleasePackagingError("quality evidence did not run against the exact release Bundle trees")
    roots = active.get("discovery_roots")
    if not isinstance(roots, list) or not roots or not isinstance(roots[0], dict):
        raise ReleasePackagingError("quality evidence is missing discovery-root details")
    canonical = roots[0]
    bundles = canonical.get("bundles")
    if canonical.get("kind") != "canonical" or not isinstance(bundles, dict):
        raise ReleasePackagingError("quality evidence canonical discovery root is invalid")
    canonical_hashes = {
        name: bundles.get(name, {}).get("tree_sha256")
        if isinstance(bundles.get(name), dict)
        else None
        for name in skill_names
    }
    if canonical_hashes != expected:
        raise ReleasePackagingError("quality evidence canonical discovery root differs from release Bundles")


def write_deterministic_archive(bundle_root: Path, archive: Path, prefix: str) -> None:
    validate_real_directory(archive.parent)
    with archive.open("xb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as output:
                for path in sorted(bundle_root.rglob("*")):
                    relative = path.relative_to(bundle_root)
                    info = output.gettarinfo(str(path), arcname=f"{prefix}/{relative.as_posix()}")
                    info.uid = 0
                    info.gid = 0
                    info.uname = ""
                    info.gname = ""
                    info.mtime = 0
                    relative = path.relative_to(bundle_root)
                    if path.is_dir():
                        info.mode = 0o755
                    elif "scripts" in relative.parts:
                        info.mode = 0o755
                    else:
                        info.mode = 0o644
                    if path.is_file():
                        with path.open("rb") as handle:
                            output.addfile(info, handle)
                    else:
                        output.addfile(info)
        raw.flush()
        os.fsync(raw.fileno())


def release_artifact_names(version: str) -> tuple[str, str, str, str]:
    release_id = f"consumer-brand-skill-pack-v{version}"
    archive_name = f"{release_id}.tar.gz"
    return (
        release_id,
        archive_name,
        f"{archive_name}.sha256",
        f"{release_id}.attestation.json",
    )


def publish_release_artifact_set(
    *,
    bundle_root: Path,
    output_root: Path,
    version: str,
    attestation_base: dict[str, Any],
    fault_injector: FaultInjector | None = None,
) -> Path:
    parse_semantic_version(version, field="release version")
    validate_release_tree(bundle_root)
    output_root = prepare_real_directory(output_root)
    release_id, archive_name, checksum_name, attestation_name = release_artifact_names(version)
    final_dir = output_root / f"v{version}"
    if os.path.lexists(final_dir):
        raise ReleasePackagingError(f"release target already exists: {final_dir}")
    stale = sorted(output_root.glob(f".{release_id}.staged-*"))
    if stale:
        raise ReleasePackagingError(
            "stale release staging directories exist; inspect them before retrying: "
            + ", ".join(str(path) for path in stale)
        )

    staging = output_root / f".{release_id}.staged-{secrets.token_hex(6)}"
    staging.mkdir(mode=0o755)
    published = False

    def inject(event: str, path: Path) -> None:
        if fault_injector is not None:
            fault_injector(event, path)

    try:
        archive = staging / archive_name
        checksum = staging / checksum_name
        attestation_path = staging / attestation_name
        write_deterministic_archive(bundle_root, archive, release_id)
        inject("after_archive", archive)
        archive_sha256 = sha256_file(archive)
        attestation = {
            **attestation_base,
            "schema_version": 1,
            "pack_version": version,
            "archive": archive_name,
            "checksum": checksum_name,
            "archive_prefix": release_id,
            "archive_sha256": archive_sha256,
            "archive_bytes": archive.stat().st_size,
            "artifact_set_atomic": True,
        }
        write_fsynced_text(
            attestation_path,
            json.dumps(attestation, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        inject("after_attestation", attestation_path)
        write_fsynced_text(
            checksum,
            f"{archive_sha256}  {archive_name}\n"
            f"{sha256_file(attestation_path)}  {attestation_name}\n",
            encoding="ascii",
        )
        inject("after_checksum", checksum)
        fsync_directory(staging)
        inject("after_staging_fsync", staging)
        verify_release_directory(staging)
        inject("after_verification", staging)
        if os.path.lexists(final_dir):
            raise ReleasePackagingError(f"release target appeared during staging: {final_dir}")
        staging.rename(final_dir)
        published = True
        try:
            fsync_directory(output_root)
        except OSError as exc:
            raise ReleasePackagingError(
                f"release directory was published but parent fsync failed; retain and verify {final_dir}: {exc}"
            ) from exc
        return final_dir
    except BaseException:
        if not published and os.path.lexists(staging):
            try:
                shutil.rmtree(staging)
            except OSError as cleanup_error:
                raise ReleasePackagingError(
                    f"release staging failed and cleanup also failed: {staging}: {cleanup_error}"
                )
        raise


def self_test() -> None:
    with tempfile.TemporaryDirectory(prefix="release-package-self-test-") as temp:
        root = Path(temp).resolve()
        bundles = root / "bundles"
        skill = bundles / "example"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("example\n", encoding="utf-8")
        validate_tree(bundles, require_directory=True)
        first = root / "first.tar.gz"
        second = root / "second.tar.gz"
        write_deterministic_archive(bundles, first, "pack-v1.0.0")
        skill.chmod(0o700)
        (skill / "SKILL.md").chmod(0o600)
        write_deterministic_archive(bundles, second, "pack-v1.0.0")
        if sha256_file(first) != sha256_file(second):
            raise AssertionError("release archive must be deterministic")
        cache = skill / "__pycache__"
        cache.mkdir()
        (cache / "generated.pyc").write_bytes(b"cache")
        try:
            validate_release_tree(skill)
        except ReleasePackagingError:
            pass
        else:
            raise AssertionError("release tree must reject runtime cache artifacts")

        quality_run = root / "quality-run"
        answer_dir = quality_run / "answers"
        answer_dir.mkdir(parents=True)
        answer_path = answer_dir / "execution.txt"
        answer_path.write_text("self-test answer\n", encoding="utf-8")
        evidence_path = quality_run / "quality-regression.json"
        selection_case = {
            "id": "selection",
            "prompt": "selection prompt",
            "expected": ["example"],
        }
        execution_case = {
            "id": "execution",
            "prompt": "execution prompt",
            "skill": "example",
            "domain": "growth",
        }
        calibration_case = {
            "id": "calibration",
            "domain": "growth",
            "expected_pass": False,
        }
        rubric = {
            "scale": {"min": 0, "max": 5},
            "pass": {
                "minimum_total": 21,
                "minimum_dimension": 2,
                "hard_failures_must_be_empty": True,
            },
            "dimensions": {f"dimension_{index}": "test" for index in range(6)},
        }
        selection_response = json.dumps(
            {"selected_skills": ["example"], "reason": "self-test"},
            separators=(",", ":"),
        )
        positive_scores = {name: 4 for name in rubric["dimensions"]}
        negative_scores = {name: 0 for name in rubric["dimensions"]}

        def judge_attempt(response_scores: dict[str, int], summary: str) -> dict[str, Any]:
            response = json.dumps(
                {"scores": response_scores, "hard_failures": [], "summary": summary},
                separators=(",", ":"),
            )
            total = sum(response_scores.values())
            quality_passed = total >= 21 and min(response_scores.values()) >= 2
            return {
                "ok": True,
                "quality_passed": quality_passed,
                "total": total,
                "scores": response_scores,
                "hard_failures": [],
                "summary": summary,
                "model": "fake-model",
                "duration_seconds": 0.1,
                "response_sha256": hashlib.sha256(response.encode("utf-8")).hexdigest(),
                "response": response,
            }

        def judged_result(
            case_id: str,
            attempt: dict[str, Any],
            expected_quality: bool,
        ) -> dict[str, Any]:
            return {
                "id": case_id,
                "domain": "growth",
                "passed": True,
                "quality_passed": expected_quality,
                "expected_quality_pass": expected_quality,
                "quality_pass_votes": int(expected_quality),
                "attempt_count": 1,
                "attempts": [attempt],
                "aggregate": "strict-majority quality verdict; median scores for reporting; ties fail quality",
                "median_total": attempt["total"],
                "median_scores": attempt["scores"],
                "duration_seconds": 0.1,
            }

        answer_digest = sha256_file(answer_path)
        positive_attempt = judge_attempt(positive_scores, "passing self-test")
        negative_attempt = judge_attempt(negative_scores, "failing calibration self-test")
        good = {
            "schema_version": 1,
            "run_id": "run-self-test",
            "passed": True,
            "model_calls": 4,
            "runtime_errors": [],
            "quality_failures": [],
            "selection": [
                {
                    "id": "selection",
                    "passed": True,
                    "expected": ["example"],
                    "selected": ["example"],
                    "reason": "self-test",
                    "prompt_sha256": hashlib.sha256(b"selection prompt").hexdigest(),
                    "response_sha256": hashlib.sha256(selection_response.encode("utf-8")).hexdigest(),
                    "response": selection_response,
                    "model": "fake-model",
                }
            ],
            "execution": [
                {
                    "id": "execution",
                    "generated": True,
                    "answer_sha256": answer_digest,
                    "prompt_sha256": hashlib.sha256(b"execution prompt").hexdigest(),
                    "skill": "example",
                    "domain": "growth",
                    "model": "fake-model",
                    "answer_path": str(answer_path),
                }
            ],
            "judge": [judged_result("execution", positive_attempt, True)],
            "calibration": [judged_result("calibration", negative_attempt, False)],
            "metadata": {
                "evidence_type": "quality-regression",
                "git_dirty": False,
                "git_head": "head",
                "run_id": "run-self-test",
                "actual_model_calls": 4,
                "requested_model": "fake-model",
                "input_sha256": {
                    "manifest": "manifest",
                    "selection_cases": "selection-cases",
                    "execution_cases": "execution-cases",
                    "judge_rubric": "judge-rubric",
                    "judge_schema": "judge-schema",
                    "answer:execution": answer_digest,
                    "calibration_answer:calibration": "b" * 64,
                },
                "plan": {
                    "layers": ["selection", "execution", "judge", "calibration"],
                    "selected_case_ids": {
                        "selection": ["selection"],
                        "execution": ["execution"],
                        "judge": ["execution"],
                        "calibration": ["calibration"],
                    },
                    "active_install": {"parity_verified": True},
                    "models": {
                        "selection": "fake-model",
                        "execution": "fake-model",
                        "judge": "fake-model",
                    },
                },
            },
        }
        checkpoint = {
            "schema_version": 1,
            "run_id": "run-self-test",
            "status": "passed",
            "stage": "completed",
            "plan": good["metadata"]["plan"],
            "model_calls": 4,
            "selection": good["selection"],
            "execution": good["execution"],
            "judge": good["judge"],
            "calibration": good["calibration"],
        }
        evidence_path.write_text(json.dumps(good), encoding="utf-8")
        (quality_run / "checkpoint.json").write_text(json.dumps(checkpoint), encoding="utf-8")
        validation_kwargs = {
            "evidence_path": evidence_path,
            "expected_head": "head",
            "expected_input_sha256": {
                "manifest": "manifest",
                "selection_cases": "selection-cases",
                "execution_cases": "execution-cases",
                "judge_rubric": "judge-rubric",
                "judge_schema": "judge-schema",
                "calibration_answer:calibration": "b" * 64,
            },
            "expected_selection_cases": [selection_case],
            "expected_execution_cases": [execution_case],
            "expected_calibration_cases": [calibration_case],
            "rubric": rubric,
        }
        validate_quality_evidence(good, **validation_kwargs)
        pristine_good = copy.deepcopy(good)
        plan_only = {
            "schema_version": 1,
            "passed": True,
            "runtime_errors": [],
            "quality_failures": [],
            "metadata": copy.deepcopy(good["metadata"]),
        }
        try:
            validate_quality_evidence(plan_only, **validation_kwargs)
        except ReleasePackagingError:
            pass
        else:
            raise AssertionError("resultless quality evidence must fail")
        good["metadata"]["input_sha256"]["judge_rubric"] = "substituted-rubric"
        try:
            validate_quality_evidence(good, **validation_kwargs)
        except ReleasePackagingError:
            pass
        else:
            raise AssertionError("substituted quality contract input must fail")

        good["metadata"]["input_sha256"]["judge_rubric"] = "judge-rubric"
        good["metadata"]["git_dirty"] = True
        try:
            validate_quality_evidence(good, **validation_kwargs)
        except ReleasePackagingError:
            pass
        else:
            raise AssertionError("dirty quality evidence must fail")

        forged_aggregate = copy.deepcopy(pristine_good)
        forged_aggregate["judge"][0]["attempts"][0]["quality_passed"] = False
        try:
            validate_quality_evidence(forged_aggregate, **validation_kwargs)
        except ReleasePackagingError:
            pass
        else:
            raise AssertionError("forged judge aggregate must fail")

        forged_model = copy.deepcopy(pristine_good)
        forged_model["metadata"]["requested_model"] = "definitely-not-run"
        forged_model["metadata"]["plan"]["models"] = {
            layer: "definitely-not-run" for layer in ("selection", "execution", "judge")
        }
        try:
            validate_quality_evidence(forged_model, **validation_kwargs)
        except ReleasePackagingError:
            pass
        else:
            raise AssertionError("unexecuted requested model must fail")

        forged_hash = copy.deepcopy(pristine_good)
        forged_hash["selection"][0]["response_sha256"] = "0" * 64
        forged_hash["execution"][0]["prompt_sha256"] = "0" * 64
        forged_hash["judge"][0]["attempts"][0]["response_sha256"] = "0" * 64
        try:
            validate_quality_evidence(forged_hash, **validation_kwargs)
        except ReleasePackagingError:
            pass
        else:
            raise AssertionError("all-zero quality hashes must fail recomputation")

        forged_scores = copy.deepcopy(pristine_good)
        empty_response = json.dumps(
            {"scores": {}, "hard_failures": ["forged"], "summary": "forged"},
            separators=(",", ":"),
        )
        forged_attempt = forged_scores["judge"][0]["attempts"][0]
        forged_attempt.update(
            {
                "scores": {},
                "total": 0,
                "hard_failures": ["forged"],
                "summary": "forged",
                "response": empty_response,
                "response_sha256": hashlib.sha256(empty_response.encode("utf-8")).hexdigest(),
            }
        )
        try:
            validate_quality_evidence(forged_scores, **validation_kwargs)
        except ReleasePackagingError:
            pass
        else:
            raise AssertionError("empty forged judge scores must fail")

        shutil.rmtree(cache)
        active_digest = active_evidence_tree_digest(skill)
        active_metadata = {
            "plan": {
                "active_install": {
                    "parity_verified": True,
                    "runtime_discovery_override": False,
                    "discovery_mode": "canonical-active-root-parity",
                    "selected_skills": ["example"],
                    "active_bundle_tree_sha256": {"example": active_digest},
                    "discovery_roots": [
                        {
                            "kind": "canonical",
                            "bundles": {"example": {"tree_sha256": active_digest}},
                        }
                    ],
                }
            }
        }
        validate_quality_active_install(active_metadata, bundles, ["example"])
        active_metadata["plan"]["active_install"]["active_bundle_tree_sha256"]["example"] = "0" * 64
        try:
            validate_quality_active_install(active_metadata, bundles, ["example"])
        except ReleasePackagingError:
            pass
        else:
            raise AssertionError("quality evidence from a different active Bundle tree must fail")
        bundle_hashes = tree_hashes(skill)
        attestation_base = {
            "pack_name": "example-pack",
            "git_head": "a" * 40,
            "git_clean": True,
            "manifest_sha256": "b" * 64,
            "quality_contract_input_sha256": {"manifest": "b" * 64},
            "isolated_install_parity_verified": True,
            "bundle_tree_sha256": {
                "example": hashlib.sha256(
                    json.dumps(bundle_hashes, sort_keys=True, separators=(",", ":")).encode("utf-8")
                ).hexdigest()
            },
            "quality_evidence_sha256": "c" * 64,
            "quality_evidence_trust": "self-attested-local",
            "quality_execution_authenticity_verified": False,
            "quality_regression_passed": True,
        }
        output_root = root / "dist-success"
        release_dir = publish_release_artifact_set(
            bundle_root=bundles,
            output_root=output_root,
            version="1.0.0",
            attestation_base=attestation_base,
        )
        verify_release_directory(release_dir)
        original_hashes = tree_hashes(release_dir)
        try:
            publish_release_artifact_set(
                bundle_root=bundles,
                output_root=output_root,
                version="1.0.0",
                attestation_base=attestation_base,
            )
        except ReleasePackagingError:
            pass
        else:
            raise AssertionError("an existing release version directory must fail closed")
        if tree_hashes(release_dir) != original_hashes:
            raise AssertionError("a failed duplicate release must not modify the existing artifact set")

        for target_kind in ("empty_directory", "regular_file"):
            existing_root = root / f"dist-existing-{target_kind}"
            existing_root.mkdir()
            existing_target = existing_root / "v1.0.0"
            if target_kind == "empty_directory":
                existing_target.mkdir()
            else:
                existing_target.write_text("must-stay\n", encoding="utf-8")
            try:
                publish_release_artifact_set(
                    bundle_root=bundles,
                    output_root=existing_root,
                    version="1.0.0",
                    attestation_base=attestation_base,
                )
            except ReleasePackagingError:
                pass
            else:
                raise AssertionError(f"existing {target_kind} release target must fail closed")
            if target_kind == "regular_file" and existing_target.read_text(encoding="utf-8") != "must-stay\n":
                raise AssertionError("existing release file was modified")

        for event in (
            "after_archive",
            "after_attestation",
            "after_checksum",
            "after_staging_fsync",
            "after_verification",
        ):
            fault_root = root / f"dist-fault-{event}"

            def fail_at(injected_event: str, _: Path, *, expected: str = event) -> None:
                if injected_event == expected:
                    raise RuntimeError(f"injected release failure: {expected}")

            try:
                publish_release_artifact_set(
                    bundle_root=bundles,
                    output_root=fault_root,
                    version="1.0.0",
                    attestation_base=attestation_base,
                    fault_injector=fail_at,
                )
            except RuntimeError as exc:
                if "injected release failure" not in str(exc):
                    raise
            else:
                raise AssertionError(f"release fault injection did not trigger: {event}")
            if os.path.lexists(fault_root / "v1.0.0"):
                raise AssertionError(f"pre-publication failure leaked a final release directory: {event}")
            if list(fault_root.glob(".*.staged-*")):
                raise AssertionError(f"pre-publication failure leaked a staging directory: {event}")

        if os.name != "nt":
            real_output = root / "real-output"
            real_output.mkdir()
            linked_output = root / "linked-output"
            linked_output.symlink_to(real_output, target_is_directory=True)
            try:
                publish_release_artifact_set(
                    bundle_root=bundles,
                    output_root=linked_output,
                    version="1.0.0",
                    attestation_base=attestation_base,
                )
            except ReleasePackagingError:
                pass
            else:
                raise AssertionError("release output symlink must fail closed")
            for target_kind in ("symlink", "broken_symlink"):
                existing_root = root / f"dist-existing-{target_kind}"
                existing_root.mkdir()
                existing_target = existing_root / "v1.0.0"
                target = real_output if target_kind == "symlink" else root / "missing-release-target"
                existing_target.symlink_to(target, target_is_directory=True)
                try:
                    publish_release_artifact_set(
                        bundle_root=bundles,
                        output_root=existing_root,
                        version="1.0.0",
                        attestation_base=attestation_base,
                    )
                except ReleasePackagingError:
                    pass
                else:
                    raise AssertionError(f"existing {target_kind} release target must fail closed")
                if not existing_target.is_symlink():
                    raise AssertionError(f"existing {target_kind} release target was modified")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install-root")
    parser.add_argument("--quality-evidence")
    parser.add_argument("--output-dir", default=str(ROOT / "dist"))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    try:
        if args.self_test:
            self_test()
            print("release packaging self-test passed")
            return 0
        if not args.install_root or not args.quality_evidence:
            raise ReleasePackagingError("--install-root and --quality-evidence are required")
        if git_value("status", "--porcelain"):
            raise ReleasePackagingError("release packaging requires a clean Git worktree")

        manifest = load_manifest(MANIFEST)
        head = git_value("rev-parse", "HEAD")
        _, calibration_answers = calibration_contract(JUDGE_CALIBRATION_CASES)
        selection_cases = json.loads(SELECTION_CASES.read_text(encoding="utf-8"))["cases"]
        execution_cases = json.loads(EXECUTION_CASES.read_text(encoding="utf-8"))["cases"]
        calibration_cases = [
            case
            for case in json.loads(JUDGE_CALIBRATION_CASES.read_text(encoding="utf-8"))["cases"]
            if case.get("expected_pass") is False
        ]
        rubric = json.loads(JUDGE_RUBRIC.read_text(encoding="utf-8"))
        canonical_input_sha256 = {
            "manifest": sha256_file(MANIFEST),
            "selection_cases": sha256_file(SELECTION_CASES),
            "execution_cases": sha256_file(EXECUTION_CASES),
            "judge_rubric": sha256_file(JUDGE_RUBRIC),
            "judge_schema": sha256_file(JUDGE_SCHEMA),
            "judge_calibration_cases": sha256_file(JUDGE_CALIBRATION_CASES),
            "judge_prompt_commerce": sha256_file(JUDGE_PROMPT_COMMERCE),
            "judge_prompt_marketing": sha256_file(JUDGE_PROMPT_MARKETING),
            **{name: sha256_file(path) for name, path in calibration_answers.items()},
        }
        evidence_path = lexical_absolute(Path(args.quality_evidence).expanduser())
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        metadata = validate_quality_evidence(
            evidence,
            evidence_path=evidence_path,
            expected_head=head,
            expected_input_sha256=canonical_input_sha256,
            expected_selection_cases=selection_cases,
            expected_execution_cases=execution_cases,
            expected_calibration_cases=calibration_cases,
            rubric=rubric,
        )

        install_root = lexical_absolute(Path(args.install_root).expanduser())
        skill_names = [skill["name"] for skill in manifest["skills"]]
        with tempfile.TemporaryDirectory(prefix="release-canonical-bundles-") as temp:
            bundle_root = Path(temp) / "bundles"
            subprocess.run(
                [sys.executable, str(BUILDER), "--output", str(bundle_root)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            bundle_hashes = validate_bundle_parity(bundle_root, install_root, skill_names)
            validate_quality_active_install(metadata, bundle_root, skill_names)

            version = manifest["pack_version"]
            attestation_base = {
                "pack_name": manifest["pack_name"],
                "git_head": head,
                "git_clean": True,
                "manifest_sha256": canonical_input_sha256["manifest"],
                "quality_contract_input_sha256": canonical_input_sha256,
                "isolated_install_parity_verified": True,
                "bundle_tree_sha256": {
                    name: hashlib.sha256(
                        json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode("utf-8")
                    ).hexdigest()
                    for name, hashes in bundle_hashes.items()
                },
                "quality_evidence_sha256": sha256_file(evidence_path),
                "quality_evidence_generated_at": metadata.get("generated_at"),
                "quality_evidence_model": metadata.get("requested_model"),
                "quality_evidence_trust": "self-attested-local",
                "quality_execution_authenticity_verified": False,
                "quality_regression_passed": True,
            }
            release_dir = publish_release_artifact_set(
                bundle_root=bundle_root,
                output_root=Path(args.output_dir).expanduser(),
                version=version,
                attestation_base=attestation_base,
            )
        _, archive_name, checksum_name, attestation_name = release_artifact_names(version)
        archive = release_dir / archive_name
        checksum = release_dir / checksum_name
        attestation_path = release_dir / attestation_name
        print(archive)
        print(checksum)
        print(attestation_path)
        return 0
    except (
        OSError,
        KeyError,
        TypeError,
        json.JSONDecodeError,
        subprocess.CalledProcessError,
        ManifestError,
        TreeIntegrityError,
        ReleaseVerificationError,
        ReleasePackagingError,
    ) as exc:
        print(f"package_release error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
