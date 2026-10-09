#!/usr/bin/env python3
"""Validate the Write Craft source tree and pinned upstream contract."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

try:
    from scripts.eval_contracts import (
        canonical_json,
        case_sources,
        han_character_count,
        resolved_case_digest,
        semantic_contract_errors,
        sha256_text,
    )
except ModuleNotFoundError:
    from eval_contracts import (  # type: ignore[no-redef]
        canonical_json,
        case_sources,
        han_character_count,
        resolved_case_digest,
        semantic_contract_errors,
        sha256_text,
    )


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "write-craft"
EVAL_FIXTURES = ROOT / "evals" / "fixtures"
EVAL_BASELINES = ROOT / "evals" / "baselines"
EXPECTED_UPSTREAMS = {
    "agent-skills",
    "anthropic-skills",
    "awesome-claude-skills",
    "elements-of-style",
}
EXPECTED_PACKAGE_FILES = {
    "skills/write-craft",
    "LICENSE",
    "LICENSES",
    "README.md",
    "THIRD_PARTY_NOTICES.md",
    "VERSION",
}
REQUIRED_FILES = {
    ROOT / ".gitmodules",
    ROOT / "AGENTS.md",
    ROOT / "LICENSE",
    ROOT / "README.md",
    ROOT / "THIRD_PARTY_NOTICES.md",
    ROOT / "VERSION",
    ROOT / "package.json",
    ROOT / "scripts" / "eval_contracts.py",
    ROOT / "scripts" / "eval_structured_output.ts",
    ROOT / "scripts" / "release_check.py",
    ROOT / "upstreams.lock.json",
    ROOT / "docs" / "upstream-absorption.md",
    ROOT / "evals" / "cases.json",
    ROOT / "evals" / "judge-fixtures.json",
    ROOT / "evals" / "release-policy.json",
    SKILL / "SKILL.md",
    SKILL / "VERSION",
    SKILL / "agents" / "openai.yaml",
}
SKILL_MAX_LINES = 200
SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
PUBLIC_HOME = re.compile(
    r"(?:/Users/[A-Za-z0-9._-]+/|/home/[A-Za-z0-9._-]+/|[A-Za-z]:\\Users\\[A-Za-z0-9._-]+\\)"
)
PLACEHOLDER = re.compile(r"\b(?:TODO|TBD|FILL_ME)\b|\[(?:To be written|Content here)\]", re.I)
TEXT_SUFFIXES = {"", ".json", ".md", ".txt", ".yaml", ".yml"}


def read_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return payload


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def behavior_case_digest(case: dict[str, object]) -> str:
    sources = case_sources(case, ROOT)
    return resolved_case_digest(case, sources)


def validate_baseline_integrity(
    path: Path, baseline: dict[str, object]
) -> list[str]:
    """Validate immutable evidence without binding it to the current candidate."""

    errors: list[str] = []
    label = path.relative_to(ROOT).as_posix()
    match = re.fullmatch(r"pi-v([0-9]+\.[0-9]+\.[0-9]+)\.json", path.name)
    filename_version = match.group(1) if match else None
    if filename_version is None:
        errors.append(f"behavior baseline has an invalid filename: {label}")
    if baseline.get("schema") != "write-craft.behavior-baseline.v1":
        errors.append(f"unexpected behavior baseline schema: {label}")
    if baseline.get("version") != filename_version:
        errors.append(f"behavior baseline version must match its filename: {label}")

    provenance = baseline.get("provenance")
    raw_artifact_roots: list[str] = []
    if not isinstance(provenance, dict):
        errors.append(f"behavior baseline provenance must be an object: {label}")
    else:
        if not isinstance(provenance.get("source_revision"), str) or not COMMIT.fullmatch(
            provenance["source_revision"]
        ):
            errors.append(f"behavior baseline source revision is invalid: {label}")
        if not isinstance(provenance.get("skill_sha256"), str) or not SHA256.fullmatch(
            provenance["skill_sha256"]
        ):
            errors.append(f"behavior baseline Skill hash is invalid: {label}")
        if provenance.get("independent_contexts") is not True:
            errors.append(f"behavior baseline must record independent contexts: {label}")
        if type(provenance.get("cross_model_verification")) is not bool:
            errors.append(f"behavior baseline cross-model evidence must be explicit: {label}")
        if provenance.get("run_mode") not in {
            "single_full_run",
            "segmented_full_with_explicit_rejudge",
        }:
            errors.append(f"behavior baseline run mode is invalid: {label}")
        roots = provenance.get("raw_artifact_roots")
        if (
            not isinstance(roots, list)
            or not roots
            or len(roots) != len(set(roots))
            or not all(
                isinstance(item, str)
                and item.startswith(".artifacts/write-craft-evals/")
                and ".." not in Path(item).parts
                for item in roots
            )
        ):
            errors.append(f"behavior baseline raw artifact roots are invalid: {label}")
        else:
            raw_artifact_roots = roots

    results = baseline.get("results")
    if not isinstance(results, list) or not results:
        errors.append(f"behavior baseline results must be a non-empty array: {label}")
        return errors

    result_ids = [
        result.get("case_id") if isinstance(result, dict) else None
        for result in results
    ]
    if any(not isinstance(case_id, str) or not case_id for case_id in result_ids):
        errors.append(f"behavior baseline case ids must be non-empty: {label}")
    if len(result_ids) != len(set(result_ids)):
        errors.append(f"behavior baseline case ids must be unique: {label}")

    acceptance = baseline.get("acceptance")
    expected_full_result = f"{len(results)}/{len(results)} PASS"
    if (
        not isinstance(acceptance, dict)
        or acceptance.get("full_cases") != expected_full_result
    ):
        errors.append(
            f"behavior baseline acceptance must match its result count: {label}"
        )
    rejudge_count = sum(
        isinstance(result, dict)
        and isinstance(result.get("lineage"), str)
        and result["lineage"].startswith("explicit_rejudge_after_")
        for result in results
    )
    if isinstance(acceptance, dict) and acceptance.get(
        "explicit_rejudges"
    ) != f"{rejudge_count}/{rejudge_count} PASS":
        errors.append(
            f"behavior baseline acceptance must match explicit rejudge lineage: {label}"
        )

    for result in results:
        if not isinstance(result, dict) or result.get("status") != "PASS":
            errors.append(f"every behavior baseline result must be PASS: {label}")
            continue
        case_id = result.get("case_id")
        if not isinstance(result.get("case_digest"), str) or not SHA256.fullmatch(
            result["case_digest"]
        ):
            errors.append(f"behavior baseline case digest is invalid: {case_id}")
        source_artifact = result.get("source_artifact")
        if (
            not isinstance(source_artifact, str)
            or not source_artifact.startswith(".artifacts/write-craft-evals/")
            or ".." in Path(source_artifact).parts
        ):
            errors.append(f"behavior baseline source artifact is invalid: {case_id}")
        elif raw_artifact_roots and not any(
            source_artifact.startswith(f"{artifact_root}/")
            for artifact_root in raw_artifact_roots
        ):
            errors.append(
                f"behavior baseline source artifact is outside its declared roots: {case_id}"
            )
        for field in ("source_input_sha256", "source_result_sha256"):
            value = result.get(field)
            if not isinstance(value, str) or not SHA256.fullmatch(value):
                errors.append(f"behavior baseline {field} is invalid: {case_id}")

        lineage = result.get("lineage")
        if lineage == "original":
            if "original_failure" in result:
                errors.append(
                    f"behavior baseline original result must not claim a failure: {case_id}"
                )
        elif (
            isinstance(lineage, str)
            and lineage.startswith("explicit_rejudge_after_")
            and lineage != "explicit_rejudge_after_"
        ):
            original_failure = result.get("original_failure")
            if (
                not isinstance(original_failure, dict)
                or original_failure.get("status") != "ERROR"
                or not isinstance(original_failure.get("error"), str)
                or not original_failure["error"].strip()
                or not isinstance(original_failure.get("result_sha256"), str)
                or not SHA256.fullmatch(original_failure["result_sha256"])
            ):
                errors.append(
                    f"behavior baseline rejudge lineage is incomplete: {case_id}"
                )
        else:
            errors.append(f"behavior baseline lineage is invalid: {case_id}")

        candidate = result.get("candidate")
        if not isinstance(candidate, str) or not candidate.strip():
            errors.append(f"behavior baseline candidate must be non-empty: {case_id}")
        elif result.get("candidate_sha256") != sha256_text(candidate):
            errors.append(f"behavior baseline candidate hash mismatch: {case_id}")
        metrics = result.get("candidate_metrics")
        if isinstance(candidate, str) and metrics is not None and (
            not isinstance(metrics, dict)
            or metrics.get("han_characters") != han_character_count(candidate)
        ):
            errors.append(f"behavior baseline candidate metrics are invalid: {case_id}")

        judgment = result.get("judgment")
        if (
            not isinstance(judgment, dict)
            or judgment.get("schema") != "write-craft.judgment.v1"
            or judgment.get("status") != "PASS"
        ):
            errors.append(f"behavior baseline judgment must be PASS: {case_id}")
            continue
        if result.get("judgment_sha256") != sha256_text(canonical_json(judgment)):
            errors.append(f"behavior baseline judgment hash mismatch: {case_id}")
        if judgment.get("case_id") != case_id:
            errors.append(f"behavior baseline judgment case id mismatch: {case_id}")
        for field in ("must", "must_not"):
            checks = judgment.get(field)
            if (
                not isinstance(checks, list)
                or not checks
                or any(
                    not isinstance(check, dict)
                    or not isinstance(check.get("criterion"), str)
                    or not check["criterion"].strip()
                    or check.get("status") != "PASS"
                    or not isinstance(check.get("evidence"), str)
                    or not check["evidence"].strip()
                    for check in checks
                )
            ):
                errors.append(
                    f"behavior baseline judgment {field} is incomplete: {case_id}"
                )
        if judgment.get("blocking_issues") != []:
            errors.append(
                f"behavior baseline PASS judgment contains blocking issues: {case_id}"
            )
    return errors


def validate_release_evidence() -> list[str]:
    """Require evidence bound to the current Skill and behavior contract."""

    errors = validate()
    if errors:
        return errors

    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    baseline_path = EVAL_BASELINES / f"pi-v{version}.json"
    if not baseline_path.is_file():
        return [
            f"missing current release baseline: {baseline_path.relative_to(ROOT)}"
        ]
    try:
        baseline = read_json(baseline_path)
        evals = read_json(ROOT / "evals" / "cases.json")
        release_policy = read_json(ROOT / "evals" / "release-policy.json")
        judge_fixtures = read_json(ROOT / "evals" / "judge-fixtures.json")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [str(exc)]

    cases = evals.get("cases")
    if not isinstance(cases, list) or not all(isinstance(case, dict) for case in cases):
        return ["current behavior cases are invalid"]
    current_cases = {case["id"]: case for case in cases}
    current_digests: dict[str, str] = {}
    for case_id, case in current_cases.items():
        try:
            current_digests[case_id] = behavior_case_digest(case)
        except (OSError, ValueError) as exc:
            errors.append(f"release case digest failed for {case_id}: {exc}")

    provenance = baseline.get("provenance")
    if not isinstance(provenance, dict) or provenance.get("skill_sha256") != tree_digest(
        SKILL
    ):
        errors.append("release baseline skill_sha256 does not match the current Skill")

    required_tracks = set(release_policy.get("required_tracks", []))
    regression_cases = {
        case_id: case
        for case_id, case in current_cases.items()
        if case.get("track") in required_tracks
    }
    exploration_cases = {
        case_id: case
        for case_id, case in current_cases.items()
        if case.get("track") == "exploration"
    }
    acceptance = baseline.get("acceptance")
    expected_regression_result = (
        f"{len(regression_cases)}/{len(regression_cases)} PASS"
    )
    if (
        not isinstance(acceptance, dict)
        or acceptance.get("regression_cases") != expected_regression_result
    ):
        errors.append("release baseline must record every regression case as PASS")
    if exploration_cases and (
        not isinstance(acceptance, dict)
        or not isinstance(acceptance.get("exploration_disclosure"), str)
        or not acceptance["exploration_disclosure"].strip()
    ):
        errors.append("release baseline must disclose exploration results or NOT_RUN")

    fixture_count = len(judge_fixtures.get("fixtures", []))
    expected_calibration = f"{fixture_count}/{fixture_count} PASS"
    fixtures_sha256 = sha256_text(canonical_json(judge_fixtures))
    if (
        not isinstance(acceptance, dict)
        or acceptance.get("judge_calibration") != expected_calibration
        or acceptance.get("judge_fixtures_sha256") != fixtures_sha256
    ):
        errors.append("release baseline must bind a passing current judge calibration")

    human_policy = release_policy.get("human_acceptance")
    human_acceptance = acceptance.get("human_acceptance") if isinstance(acceptance, dict) else None
    minimum_documents = (
        human_policy.get("minimum_documents")
        if isinstance(human_policy, dict)
        else None
    )
    if (
        not isinstance(human_acceptance, dict)
        or human_acceptance.get("status") != "PASS"
        or type(human_acceptance.get("documents")) is not int
        or type(minimum_documents) is not int
        or human_acceptance["documents"] < minimum_documents
        or not isinstance(human_acceptance.get("independence_recorded"), bool)
        or human_acceptance.get("independence_recorded") is not True
        or not isinstance(human_acceptance.get("limitations"), list)
        or not human_acceptance["limitations"]
        or not all(
            isinstance(item, str) and item.strip()
            for item in human_acceptance["limitations"]
        )
        or not isinstance(human_acceptance.get("record_sha256"), str)
        or not SHA256.fullmatch(human_acceptance["record_sha256"])
    ):
        errors.append("release baseline must bind the required human acceptance summary")

    results = baseline.get("results")
    if not isinstance(results, list):
        errors.append("release baseline results must be an array")
        return errors
    result_ids = [
        result.get("case_id") if isinstance(result, dict) else None
        for result in results
    ]
    result_counter = Counter(result_ids)
    missing_regressions = [
        case_id for case_id in regression_cases if result_counter[case_id] != 1
    ]
    invalid_result_ids = [
        case_id for case_id in result_ids if case_id not in current_cases
    ]
    if missing_regressions or invalid_result_ids or any(
        count != 1 for count in result_counter.values()
    ):
        errors.append(
            "release baseline must contain exactly one result for every regression case"
        )

    for result in results:
        if not isinstance(result, dict):
            continue
        case_id = result.get("case_id")
        current_case = current_cases.get(case_id) if isinstance(case_id, str) else None
        if current_case is None:
            errors.append(f"release baseline references an invalid case: {case_id!r}")
            continue
        digest_matches = result.get("case_digest") == current_digests.get(case_id)
        if not digest_matches:
            errors.append(
                f"release baseline case_digest does not match current case: {case_id}"
            )

        candidate = result.get("candidate")
        if isinstance(candidate, str) and isinstance(current_case.get("limits"), dict):
            maximum = current_case["limits"].get("max_han_characters")
            actual = han_character_count(candidate)
            metrics = result.get("candidate_metrics")
            if type(maximum) is int and actual > maximum:
                errors.append(
                    f"release baseline candidate exceeds max_han_characters: {case_id}"
                )
            if not isinstance(metrics, dict) or metrics.get("han_characters") != actual:
                errors.append(
                    f"release baseline candidate metrics are invalid: {case_id}"
                )

        judgment = result.get("judgment")
        expected = current_case.get("expected")
        if not isinstance(judgment, dict) or not isinstance(expected, dict):
            errors.append(f"release baseline judgment is invalid: {case_id}")
            continue
        for field in ("must", "must_not"):
            criteria = expected.get(field)
            checks = judgment.get(field)
            if not isinstance(criteria, list) or not isinstance(checks, list):
                errors.append(
                    f"release baseline judgment {field} is incomplete: {case_id}"
                )
                continue
            if len(checks) != len(criteria) or any(
                not isinstance(check, dict)
                or check.get("criterion") != criterion
                or check.get("status") != "PASS"
                or not isinstance(check.get("evidence"), str)
                or not check["evidence"].strip()
                for criterion, check in zip(criteria, checks)
            ):
                errors.append(
                    f"release baseline judgment {field} does not match current contract: {case_id}"
                )

        if not digest_matches:
            continue
        stages = result.get("stages")
        if not isinstance(stages, dict):
            errors.append(f"release baseline stages are missing: {case_id}")
            continue
        if stages.get("generation") != "PASS" or stages.get("fact_review") != "PASS":
            errors.append(f"release baseline required stages did not PASS: {case_id}")
        reader_test = current_case.get("reader_test")
        if isinstance(reader_test, dict):
            if stages.get("reader") != "PASS" or stages.get("reader_review") != "PASS":
                errors.append(f"release baseline reader stages did not PASS: {case_id}")
            reader_response = result.get("reader_response")
            reader_judgment = result.get("reader_judgment")
            question_ids = [
                question.get("id")
                for question in reader_test.get("questions", [])
                if isinstance(question, dict)
            ]
            if (
                not isinstance(reader_response, dict)
                or result.get("reader_response_sha256")
                != sha256_text(canonical_json(reader_response))
                or reader_response.get("schema") != "write-craft.reader-response.v1"
                or reader_response.get("case_id") != case_id
            ):
                errors.append(f"release baseline reader response is invalid: {case_id}")
            else:
                response_ids = [
                    answer.get("question_id")
                    for answer in reader_response.get("answers", [])
                    if isinstance(answer, dict)
                ]
                if response_ids != question_ids:
                    errors.append(
                        f"release baseline reader response coverage is invalid: {case_id}"
                    )
            if (
                not isinstance(reader_judgment, dict)
                or result.get("reader_judgment_sha256")
                != sha256_text(canonical_json(reader_judgment))
                or reader_judgment.get("schema") != "write-craft.reader-judgment.v1"
                or reader_judgment.get("case_id") != case_id
                or reader_judgment.get("status") != "PASS"
                or reader_judgment.get("blocking_issues") != []
            ):
                errors.append(f"release baseline reader judgment is invalid: {case_id}")
            else:
                judgment_answers = reader_judgment.get("answers")
                judgment_ids = (
                    [
                        answer.get("question_id")
                        for answer in judgment_answers
                        if isinstance(answer, dict)
                    ]
                    if isinstance(judgment_answers, list)
                    else []
                )
                if judgment_ids != question_ids or any(
                    not isinstance(answer, dict) or answer.get("status") != "PASS"
                    for answer in judgment_answers or []
                ):
                    errors.append(
                        f"release baseline reader judgment coverage is invalid: {case_id}"
                    )
        elif stages.get("reader") != "NOT_RUN" or stages.get("reader_review") != "NOT_RUN":
            errors.append(f"release baseline undeclared reader stages must be NOT_RUN: {case_id}")

    return errors


def run(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args), cwd=cwd, text=True, capture_output=True, check=False
    )


def frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return {}
    try:
        end = lines.index("---", 1)
    except ValueError:
        return {}
    parsed: dict[str, str] = {}
    for line in lines[1:end]:
        if not line or line.startswith(" ") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        parsed[key.strip()] = value.strip().strip('"').strip("'")
    return parsed


def product_text_files() -> list[Path]:
    roots = [
        ROOT / "AGENTS.md",
        ROOT / "README.md",
        ROOT / "THIRD_PARTY_NOTICES.md",
        ROOT / "VERSION",
        ROOT / "package.json",
        ROOT / "upstreams.lock.json",
        ROOT / "docs",
        ROOT / "evals",
        ROOT / "scripts",
        ROOT / "tests",
        ROOT / ".github",
        SKILL,
    ]
    files: list[Path] = []
    for candidate in roots:
        if candidate.is_file():
            files.append(candidate)
        elif candidate.is_dir():
            files.extend(
                path
                for path in candidate.rglob("*")
                if path.is_file()
                and path.suffix in TEXT_SUFFIXES
                and "__pycache__" not in path.parts
            )
    return sorted(set(files))


def validate() -> list[str]:
    errors: list[str] = []

    for path in sorted(REQUIRED_FILES):
        if not path.is_file():
            errors.append(f"missing required file: {path.relative_to(ROOT)}")

    if errors:
        return errors

    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    leaf_version = (SKILL / "VERSION").read_text(encoding="utf-8").strip()
    if not SEMVER.fullmatch(version):
        errors.append("VERSION must be semantic x.y.z")
    if leaf_version != version:
        errors.append("skills/write-craft/VERSION must match root VERSION")

    try:
        package = read_json(ROOT / "package.json")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(str(exc))
        package = {}
    if package.get("name") != "@bigking67/write-craft":
        errors.append("package name must be @bigking67/write-craft")
    if package.get("version") != version:
        errors.append("package.json version must match VERSION")
    if package.get("private") is not True:
        errors.append("V0.2 package must remain private to prevent accidental publish")
    if package.get("homepage") != "https://github.com/bigKING67/write-craft#readme":
        errors.append("package homepage must point to the canonical GitHub repository")
    repository = package.get("repository")
    if not isinstance(repository, dict) or repository != {
        "type": "git",
        "url": "git+https://github.com/bigKING67/write-craft.git",
    }:
        errors.append("package repository metadata must point to the canonical Git remote")
    configured_files = package.get("files")
    if not isinstance(configured_files, list) or set(configured_files) != EXPECTED_PACKAGE_FILES:
        errors.append("package.json files must expose only the Skill and legal metadata")
    pi = package.get("pi")
    if not isinstance(pi, dict) or pi.get("skills") != ["skills/write-craft"]:
        errors.append("package.json pi.skills must expose only skills/write-craft")

    skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    metadata = frontmatter(skill_text)
    if metadata.get("name") != "write-craft":
        errors.append("SKILL.md frontmatter name must be write-craft")
    description = metadata.get("description", "")
    for required_phrase in ("非技术决策者", "老板版", "不要用于"):
        if required_phrase not in description:
            errors.append(f"SKILL.md description must discriminate routing with: {required_phrase}")

    if len(skill_text.splitlines()) > SKILL_MAX_LINES:
        errors.append(
            f"SKILL.md must stay within {SKILL_MAX_LINES} lines; some hosts read only "
            "the first 200 lines of an entrypoint"
        )

    linked_refs = set(re.findall(r"\(references/([^)]+\.md)\)", skill_text))
    actual_refs = {
        path.name for path in (SKILL / "references").glob("*.md") if path.is_file()
    }
    if linked_refs != actual_refs:
        errors.append(
            "SKILL.md reference links must exactly cover reference files: "
            f"linked={sorted(linked_refs)} actual={sorted(actual_refs)}"
        )

    openai_text = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
    if "$write-craft" not in openai_text:
        errors.append("openai.yaml default_prompt must mention $write-craft")
    if "allow_implicit_invocation: true" not in openai_text:
        errors.append("write-craft must allow implicit invocation")

    try:
        lock = read_json(ROOT / "upstreams.lock.json")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(str(exc))
        lock = {}
    if lock.get("schema") != "write-craft.upstreams-lock.v1":
        errors.append("unexpected upstream lock schema")
    upstreams = lock.get("upstreams")
    if not isinstance(upstreams, dict) or set(upstreams) != EXPECTED_UPSTREAMS:
        errors.append("upstream lock must contain the four approved upstreams")
        upstreams = {}

    modules = run(
        "git",
        "config",
        "-f",
        ".gitmodules",
        "--get-regexp",
        r"^submodule\..*\.path$",
    )
    if modules.returncode != 0:
        errors.append("unable to read .gitmodules")
        module_paths: set[str] = set()
    else:
        module_paths = {
            line.split(maxsplit=1)[1]
            for line in modules.stdout.splitlines()
            if len(line.split(maxsplit=1)) == 2
        }

    for name, raw_entry in sorted(upstreams.items()):
        if not isinstance(raw_entry, dict):
            errors.append(f"upstream {name} must be an object")
            continue
        relative = raw_entry.get("path")
        pinned = raw_entry.get("commit")
        if not isinstance(relative, str) or relative not in module_paths:
            errors.append(f"upstream {name} path is not registered in .gitmodules")
            continue
        if not isinstance(pinned, str) or not COMMIT.fullmatch(pinned):
            errors.append(f"upstream {name} commit must be a 40-character SHA")
            continue
        checkout = ROOT / relative
        if not checkout.is_dir():
            errors.append(f"upstream {name} checkout is missing")
            continue
        head = run("git", "rev-parse", "HEAD", cwd=checkout)
        if head.returncode != 0 or head.stdout.strip() != pinned:
            errors.append(f"upstream {name} checkout does not match the pinned commit")
        dirty = run("git", "status", "--porcelain", cwd=checkout)
        if dirty.returncode != 0 or dirty.stdout.strip():
            errors.append(f"upstream {name} checkout must remain pristine")

    try:
        evals = read_json(ROOT / "evals" / "cases.json")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(str(exc))
        evals = {}
    cases = evals.get("cases")
    if evals.get("schema") != "write-craft.behavior-cases.v3":
        errors.append("unexpected behavior-cases schema")
    if not isinstance(cases, list) or len(cases) < 10:
        errors.append("behavior suite must contain at least ten cases")
    else:
        ids: set[str] = set()
        required_tags: set[str] = set()
        smoke_cases = 0
        for case in cases:
            if not isinstance(case, dict):
                errors.append("every behavior case must be an object")
                continue
            case_id = case.get("id")
            if not isinstance(case_id, str) or not case_id or case_id in ids:
                errors.append("behavior case ids must be non-empty and unique")
            else:
                ids.add(case_id)
            tags = case.get("tags")
            if (
                isinstance(tags, list)
                and tags
                and all(isinstance(tag, str) and tag.strip() for tag in tags)
                and len(tags) == len(set(tags))
            ):
                required_tags.update(tags)
            else:
                errors.append(f"behavior case {case_id!r} has invalid tags")
            limits = case.get("limits")
            if limits is not None and (
                not isinstance(limits, dict)
                or set(limits) != {"max_han_characters"}
                or type(limits.get("max_han_characters")) is not int
                or limits["max_han_characters"] < 1
            ):
                errors.append(f"behavior case {case_id!r} has invalid limits")
            suite = case.get("suite")
            if suite not in {"smoke", "full"}:
                errors.append(f"behavior case {case_id!r} has invalid suite")
            elif suite == "smoke":
                smoke_cases += 1
            track = case.get("track")
            if track not in {"regression", "exploration"}:
                errors.append(f"behavior case {case_id!r} has invalid track")

            source = case.get("source")
            source_file = case.get("source_file")
            sources = case.get("sources")
            has_source = isinstance(source, str) and bool(source.strip())
            has_source_file = isinstance(source_file, str) and bool(source_file.strip())
            has_sources = isinstance(sources, list) and bool(sources)
            if sum((has_source, has_source_file, has_sources)) != 1:
                errors.append(
                    f"behavior case {case_id!r} must define exactly one source shape"
                )
            elif has_source_file:
                fixture = (ROOT / source_file).resolve()
                try:
                    fixture.relative_to(EVAL_FIXTURES.resolve())
                except ValueError:
                    errors.append(
                        f"behavior case {case_id!r} source_file escapes evals/fixtures"
                    )
                else:
                    if not fixture.is_file():
                        errors.append(
                            f"behavior case {case_id!r} source_file does not exist"
                        )
            elif has_sources:
                source_ids: list[str] = []
                for item in sources:
                    if not isinstance(item, dict):
                        errors.append(
                            f"behavior case {case_id!r} source entries must be objects"
                        )
                        continue
                    source_id = item.get("source_id")
                    if not isinstance(source_id, str) or not source_id.strip():
                        errors.append(
                            f"behavior case {case_id!r} sources need source_id"
                        )
                    else:
                        source_ids.append(source_id)
                    text = item.get("text")
                    item_file = item.get("source_file")
                    has_text = isinstance(text, str) and bool(text.strip())
                    has_item_file = isinstance(item_file, str) and bool(
                        item_file.strip()
                    )
                    if has_text == has_item_file:
                        errors.append(
                            f"behavior case {case_id!r} sources need exactly one text shape"
                        )
                    elif has_item_file:
                        fixture = (ROOT / item_file).resolve()
                        try:
                            fixture.relative_to(EVAL_FIXTURES.resolve())
                        except ValueError:
                            errors.append(
                                f"behavior case {case_id!r} source_file escapes evals/fixtures"
                            )
                        else:
                            if not fixture.is_file():
                                errors.append(
                                    f"behavior case {case_id!r} source_file does not exist"
                                )
                if len(source_ids) != len(set(source_ids)):
                    errors.append(
                        f"behavior case {case_id!r} source ids must be unique"
                    )
            expected = case.get("expected")
            if (
                not isinstance(case.get("request"), str)
                or not case["request"].strip()
                or not isinstance(expected, dict)
                or not isinstance(expected.get("must"), list)
                or not isinstance(expected.get("must_not"), list)
            ):
                errors.append(f"behavior case {case_id!r} has an incomplete contract")
            elif any(
                not values
                or not all(isinstance(value, str) and value.strip() for value in values)
                or len(values) != len(set(values))
                for values in (expected["must"], expected["must_not"])
            ):
                errors.append(f"behavior case {case_id!r} has invalid expectations")
            errors.extend(
                semantic_contract_errors(
                    case.get("semantic_contract"),
                    f"behavior case {case_id!r} semantic_contract",
                )
            )
            reader_test = case.get("reader_test")
            if reader_test is not None:
                if not isinstance(reader_test, dict):
                    errors.append(
                        f"behavior case {case_id!r} reader_test must be an object"
                    )
                else:
                    persona = reader_test.get("persona")
                    questions = reader_test.get("questions")
                    if not isinstance(persona, str) or not persona.strip():
                        errors.append(
                            f"behavior case {case_id!r} reader persona is invalid"
                        )
                    if not isinstance(questions, list) or not questions:
                        errors.append(
                            f"behavior case {case_id!r} reader questions are invalid"
                        )
                    else:
                        question_ids: list[str] = []
                        for question in questions:
                            if not isinstance(question, dict):
                                errors.append(
                                    f"behavior case {case_id!r} reader questions must be objects"
                                )
                                continue
                            question_id = question.get("id")
                            prompt = question.get("question")
                            answer_key = question.get("answer_key")
                            if not isinstance(question_id, str) or not question_id.strip():
                                errors.append(
                                    f"behavior case {case_id!r} reader question id is invalid"
                                )
                            else:
                                question_ids.append(question_id)
                            if not isinstance(prompt, str) or not prompt.strip():
                                errors.append(
                                    f"behavior case {case_id!r} reader question is invalid"
                                )
                            if (
                                not isinstance(answer_key, list)
                                or not answer_key
                                or not all(
                                    isinstance(value, str) and value.strip()
                                    for value in answer_key
                                )
                            ):
                                errors.append(
                                    f"behavior case {case_id!r} reader answer key is invalid"
                                )
                        if len(question_ids) != len(set(question_ids)):
                            errors.append(
                                f"behavior case {case_id!r} reader question ids must be unique"
                            )
        for tag in {"rewrite", "diagnose", "evidence", "routing", "reader-test"}:
            if tag not in required_tags:
                errors.append(f"behavior suite is missing required coverage tag: {tag}")
        if smoke_cases != 4:
            errors.append("behavior suite must contain exactly four smoke cases")

    try:
        judge_fixtures = read_json(ROOT / "evals" / "judge-fixtures.json")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(str(exc))
        judge_fixtures = {}
    fixtures = judge_fixtures.get("fixtures")
    if judge_fixtures.get("schema") != "write-craft.judge-fixtures.v1":
        errors.append("unexpected judge-fixtures schema")
    if not isinstance(fixtures, list) or len(fixtures) < 4:
        errors.append("judge calibration must contain at least four fixtures")
    else:
        fixture_ids = [
            fixture.get("id") if isinstance(fixture, dict) else None
            for fixture in fixtures
        ]
        expected_statuses = {
            fixture.get("expected_status")
            for fixture in fixtures
            if isinstance(fixture, dict)
        }
        if (
            any(not isinstance(fixture_id, str) or not fixture_id for fixture_id in fixture_ids)
            or len(fixture_ids) != len(set(fixture_ids))
        ):
            errors.append("judge fixture ids must be non-empty and unique")
        if expected_statuses != {"PASS", "FAIL"}:
            errors.append("judge fixtures must calibrate both PASS and FAIL behavior")
        for fixture in fixtures:
            if not isinstance(fixture, dict):
                errors.append("judge fixtures must be objects")
                continue
            case = fixture.get("case")
            expected = case.get("expected") if isinstance(case, dict) else None
            if (
                not isinstance(case, dict)
                or not isinstance(case.get("id"), str)
                or not isinstance(case.get("request"), str)
                or not case["request"].strip()
                or not isinstance(expected, dict)
                or any(
                    not isinstance(expected.get(field), list) or not expected[field]
                    for field in ("must", "must_not")
                )
                or not isinstance(fixture.get("source"), str)
                or not fixture["source"].strip()
                or not isinstance(fixture.get("candidate"), str)
                or not fixture["candidate"].strip()
            ):
                errors.append(
                    f"judge fixture {fixture.get('id')!r} has an incomplete contract"
                )
            elif isinstance(case, dict):
                errors.extend(
                    semantic_contract_errors(
                        case.get("semantic_contract"),
                        f"judge fixture {fixture.get('id')!r} semantic_contract",
                    )
                )

    try:
        release_policy = read_json(ROOT / "evals" / "release-policy.json")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(str(exc))
        release_policy = {}
    if release_policy.get("schema") != "write-craft.release-policy.v1":
        errors.append("unexpected release-policy schema")
    if release_policy.get("required_tracks") != ["regression"]:
        errors.append("release policy must require the regression track")
    exploration_policy = release_policy.get("exploration")
    if not isinstance(exploration_policy, dict) or exploration_policy.get(
        "require_disclosure"
    ) is not True:
        errors.append("release policy must require exploration disclosure")
    behavior_policy = release_policy.get("behavior")
    if not isinstance(behavior_policy, dict) or any(
        behavior_policy.get(field) is not True
        for field in (
            "require_current_skill_digest",
            "require_current_case_digests",
            "require_deterministic_limits",
        )
    ):
        errors.append("release policy behavior gates are incomplete")
    reader_policy = release_policy.get("reader_testing")
    if not isinstance(reader_policy, dict) or reader_policy.get(
        "require_declared_reader_stages"
    ) is not True:
        errors.append("release policy must require declared reader stages")
    calibration_policy = release_policy.get("judge_calibration")
    if (
        not isinstance(calibration_policy, dict)
        or calibration_policy.get("required") is not True
        or calibration_policy.get("fixtures") != "evals/judge-fixtures.json"
    ):
        errors.append("release policy judge calibration gate is incomplete")
    human_policy = release_policy.get("human_acceptance")
    if (
        not isinstance(human_policy, dict)
        or human_policy.get("required") is not True
        or type(human_policy.get("minimum_documents")) is not int
        or human_policy["minimum_documents"] < 1
        or human_policy.get("require_independence_record") is not True
        or human_policy.get("require_limitations") is not True
    ):
        errors.append("release policy human acceptance gate is incomplete")
    package_policy = release_policy.get("package")
    if not isinstance(package_policy, dict) or package_policy.get(
        "require_boundary_check"
    ) is not True:
        errors.append("release policy package boundary gate is incomplete")

    baseline_paths = sorted(EVAL_BASELINES.glob("pi-v*.json"))
    if not baseline_paths:
        errors.append("at least one immutable behavior baseline is required")
    for baseline_path in baseline_paths:
        try:
            baseline = read_json(baseline_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(str(exc))
            continue
        errors.extend(validate_baseline_integrity(baseline_path, baseline))

    for path in product_text_files():
        text = path.read_text(encoding="utf-8")
        if PUBLIC_HOME.search(text):
            errors.append(f"public text contains an absolute user-home path: {path.relative_to(ROOT)}")
        if PLACEHOLDER.search(text):
            errors.append(f"unfinished scaffold placeholder: {path.relative_to(ROOT)}")

    notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    for marker in ("agent-skills", "doc-coauthoring", "the-elements-of-style", "awesome-claude-skills"):
        if marker not in notices:
            errors.append(f"THIRD_PARTY_NOTICES.md is missing {marker}")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("FAIL Write Craft source validation")
        for error in errors:
            print(f"  ERROR: {error}")
        return 1
    print("PASS Write Craft source validation")
    print("  PASS: Skill metadata and progressive references")
    print("  PASS: version and package identity")
    print("  PASS: pinned pristine upstreams and license notices")
    print("  PASS: behavior-case coverage and public-text hygiene")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
