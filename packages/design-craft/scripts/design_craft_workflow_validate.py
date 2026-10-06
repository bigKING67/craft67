#!/usr/bin/env python3
"""Validate GitHub workflow pinning and native evidence runner contracts."""

from __future__ import annotations

import argparse
import json
import plistlib
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


SCHEMA = "design-craft.workflow-verification.v1"
ROOT = Path(__file__).resolve().parents[1]
ACTION_PATTERN = re.compile(r"\buses:\s*[^@\s]+@([^\s#]+)")


def require_tokens(text: str, tokens: tuple[str, ...], label: str) -> list[str]:
    return [f"{label} missing {token}" for token in tokens if token not in text]


def action_pin_errors(workflow: Path, text: str) -> list[str]:
    errors: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        match = ACTION_PATTERN.search(line)
        if match and not re.fullmatch(r"[0-9a-f]{40}", match.group(1)):
            errors.append(f"{workflow.relative_to(ROOT)}:{line_number}: action must use a full SHA")
    return errors


def workflow_job_block(text: str, job_name: str) -> str:
    start_match = re.search(rf"(?m)^  {re.escape(job_name)}:\s*$", text)
    if start_match is None:
        return ""
    next_match = re.search(
        r"(?m)^  [A-Za-z0-9_-]+:\s*$",
        text[start_match.end() :],
    )
    if next_match is None:
        return text[start_match.start() :]
    end = start_match.end() + next_match.start()
    return text[start_match.start() : end]


def benchmark_artifact_contract_errors(
    benchmark_workflow: str,
    release_certify_workflow: str,
) -> list[str]:
    errors: list[str] = []
    operational = workflow_job_block(benchmark_workflow, "operational-candidate")
    errors.extend(
        require_tokens(
            operational,
            (
                '${RUNNER_TEMP}/operational-candidate/benchmark-result-full.json',
                '${RUNNER_TEMP}/operational-candidate/dist/evidence/operational-95-candidate.json',
                "OPERATIONAL_CANDIDATE_EVIDENCE=",
                '${{ runner.temp }}/operational-candidate/benchmark-result-full.json',
                '${{ runner.temp }}/operational-candidate/dist/evidence/operational-95-candidate.json',
            ),
            ".github/workflows/benchmark.yml operational-candidate staging",
        )
    )
    for forbidden in (
        "--output benchmark-result-smoke.json",
        "--output benchmark-result-full.json",
        "BENCHMARK_RESULT=benchmark-result-full.json",
        "path: benchmark-result-smoke.json",
        "path: benchmark-result-full.json",
    ):
        if forbidden in benchmark_workflow:
            errors.append(
                ".github/workflows/benchmark.yml must not write benchmark evidence "
                f"into the source checkout: {forbidden}"
            )
    errors.extend(
        require_tokens(
            release_certify_workflow,
            (
                'BENCHMARK_RESULT=${RUNNER_TEMP}/benchmark/benchmark-result-full.json',
                'test -f "${BENCHMARK_RESULT}"',
                'test -f "${RUNNER_TEMP}/benchmark/dist/evidence/operational-95-candidate.json"',
            ),
            ".github/workflows/release-certify.yml benchmark artifact consumer",
        )
    )
    return errors


def validate() -> dict:
    errors: list[str] = []
    native_workflow_path = ROOT / ".github/workflows/native-runtime.yml"
    validate_workflow_path = ROOT / ".github/workflows/validate.yml"
    benchmark_workflow_path = ROOT / ".github/workflows/benchmark.yml"
    codeql_workflow_path = ROOT / ".github/workflows/codeql.yml"
    release_certify_workflow_path = ROOT / ".github/workflows/release-certify.yml"
    release_publish_workflow_path = ROOT / ".github/workflows/release-publish.yml"
    physical_workflow_path = ROOT / ".github/workflows/physical-device.yml"
    dependabot_path = ROOT / ".github/dependabot.yml"
    ios_runner_path = ROOT / "scripts/native_runtime_ci_ios.sh"
    android_runner_path = ROOT / "scripts/native_runtime_ci_android.sh"
    android_common_path = ROOT / "scripts/native_runtime_android_common.sh"
    portable_validator_path = ROOT / "scripts/validate.sh"
    lint_validator_path = ROOT / "scripts/design_craft_lint.py"
    maturity_validator_path = ROOT / "tools/design_craft/validation/maturity/process_runner.py"
    maturity_entrypoint_path = ROOT / "scripts/design_craft_maturity.py"
    git_attributes_path = ROOT / ".gitattributes"
    ios_fixture_path = ROOT / "evals/native-runtime/fixtures/ios/App.swift"
    ios_observation_path = (
        ROOT / "tools/design_craft/release/native_ios_observation.py"
    )

    required_paths = (
        native_workflow_path,
        validate_workflow_path,
        benchmark_workflow_path,
        codeql_workflow_path,
        release_certify_workflow_path,
        release_publish_workflow_path,
        physical_workflow_path,
        dependabot_path,
        ios_runner_path,
        android_runner_path,
        android_common_path,
        portable_validator_path,
        lint_validator_path,
        maturity_validator_path,
        maturity_entrypoint_path,
        git_attributes_path,
        ios_fixture_path,
        ios_observation_path,
    )
    for path in required_paths:
        if not path.is_file():
            errors.append(f"missing workflow contract file: {path.relative_to(ROOT)}")
    if errors:
        return {"schema": SCHEMA, "root": str(ROOT), "ok": False, "errors": errors}

    native_workflow = native_workflow_path.read_text(encoding="utf-8")
    validate_workflow = validate_workflow_path.read_text(encoding="utf-8")
    benchmark_workflow = benchmark_workflow_path.read_text(encoding="utf-8")
    codeql_workflow = codeql_workflow_path.read_text(encoding="utf-8")
    release_certify_workflow = release_certify_workflow_path.read_text(encoding="utf-8")
    release_publish_workflow = release_publish_workflow_path.read_text(encoding="utf-8")
    physical_workflow = physical_workflow_path.read_text(encoding="utf-8")
    dependabot = dependabot_path.read_text(encoding="utf-8")
    ios_runner = ios_runner_path.read_text(encoding="utf-8")
    android_runner = android_runner_path.read_text(encoding="utf-8")
    android_common = android_common_path.read_text(encoding="utf-8")
    portable_validator = portable_validator_path.read_text(encoding="utf-8")
    lint_validator = lint_validator_path.read_text(encoding="utf-8")
    maturity_validator = maturity_validator_path.read_text(encoding="utf-8")
    git_attributes = git_attributes_path.read_text(encoding="utf-8")
    ios_fixture = ios_fixture_path.read_text(encoding="utf-8")
    ios_observation = ios_observation_path.read_text(encoding="utf-8")

    errors.extend(
        require_tokens(
            native_workflow,
            (
                "native_runtime_ci_ios.sh",
                "reactivecircus/android-emulator-runner@",
                "native_runtime_ci_android.sh",
                "Enable KVM access",
                "-no-metrics",
                "concurrency:",
                "cancel-in-progress: false",
            ),
            ".github/workflows/native-runtime.yml",
        )
    )
    errors.extend(
        require_tokens(
            validate_workflow,
            (
                "DESIGN_CRAFT_NATIVE_BUILD_ONLY",
                "android-fixture-build",
                'tags: ["v*"]',
                "concurrency:",
                "cancel-in-progress: true",
                "name: lint",
                "name: contract-tests",
                "make lint",
                "make contract-tests",
                "--profile development",
            ),
            ".github/workflows/validate.yml",
        )
    )
    errors.extend(
        require_tokens(
            benchmark_workflow,
            (
                "schedule:",
                "workflow_dispatch:",
                "operational-candidate",
                "native_run_id:",
                "benchmark_baseline:",
                "github.event_name == 'push' || github.event_name == 'pull_request'",
                "(github.event_name == 'workflow_dispatch' && inputs.mode == 'full')",
                "inputs.mode == 'operational-candidate'",
                "ubuntu-24.04",
                "--scale smoke",
                "--scale full",
                "benchmark-result-smoke.json",
                "benchmark-result-full.json",
                '${RUNNER_TEMP}/benchmark-result-smoke.json',
                '${RUNNER_TEMP}/benchmark-result-full.json',
                "release-readiness-operational",
                'test -f "${BENCHMARK_BASELINE}"',
                'BENCHMARK_BASELINE="${BENCHMARK_BASELINE}"',
                "DESIGN_CRAFT_NATIVE_EVIDENCE_ROOT",
                "operational-95-candidate.json",
                "actions/upload-artifact@",
                "retention-days: 30",
                "retention-days: 90",
                "concurrency:",
                "cancel-in-progress: true",
            ),
            ".github/workflows/benchmark.yml",
        )
    )
    if benchmark_workflow.count("timeout-minutes:") != 3:
        errors.append(
            ".github/workflows/benchmark.yml must set a timeout on all three benchmark jobs"
        )
    for job_name in ("smoke", "full", "operational-candidate"):
        block = workflow_job_block(benchmark_workflow, job_name)
        if "submodules: recursive" not in block or "fetch-depth: 0" not in block:
            errors.append(
                f".github/workflows/benchmark.yml {job_name} must fetch recursive submodules and full history"
            )
    full_benchmark_job = workflow_job_block(benchmark_workflow, "full")
    if "inputs.mode == 'full'" not in full_benchmark_job:
        errors.append(
            ".github/workflows/benchmark.yml full must only handle full workflow dispatches"
        )
    operational_candidate_job = workflow_job_block(
        benchmark_workflow,
        "operational-candidate",
    )
    errors.extend(
        require_tokens(
            operational_candidate_job,
            (
                "permissions:",
                "actions: read",
                "contents: read",
                "gh run view",
                "gh run download",
                "native-runtime-ios-${NATIVE_RUN_ID}",
                "native-runtime-android-${NATIVE_RUN_ID}",
                "release-readiness-operational",
                "DESIGN_CRAFT_NATIVE_EVIDENCE_ROOT",
                "Run immutable full benchmark",
                "OPERATIONAL_CANDIDATE_EVIDENCE=",
                "operational-candidate-${{ github.run_id }}",
                "operational-95-candidate.json",
                "if: always()",
            ),
            ".github/workflows/benchmark.yml operational-candidate",
        )
    )
    if operational_candidate_job.count("--scale full") != 1:
        errors.append(
            ".github/workflows/benchmark.yml operational-candidate must run the full benchmark exactly once"
        )
    errors.extend(
        benchmark_artifact_contract_errors(
            benchmark_workflow,
            release_certify_workflow,
        )
    )
    errors.extend(
        require_tokens(
            codeql_workflow,
            (
                "schedule:",
                "security-events: write",
                "contents: read",
                "timeout-minutes:",
                "matrix:",
                "python",
                "javascript-typescript",
                "github/codeql-action/init@",
                "github/codeql-action/analyze@",
                "concurrency:",
                "cancel-in-progress: true",
            ),
            ".github/workflows/codeql.yml",
        )
    )
    if codeql_workflow.count("timeout-minutes:") != 1:
        errors.append(".github/workflows/codeql.yml must set a timeout on its analysis job")
    errors.extend(
        require_tokens(
            release_certify_workflow,
            (
                "workflow_dispatch:",
                "operational_95",
                "certified_100",
                "confirm_certification:",
                "benchmark_run_id:",
                "release verify",
                "--phase final",
                "--require-tag-run",
                "actions: read",
                "GH_TOKEN: ${{ github.token }}",
                "release run-observation",
                "--kind native",
                "--kind benchmark",
                "--kind physical",
                "release evidence-bindings",
                "--evidence-root",
                "--native-observation",
                "--benchmark-observation",
                "--benchmark-result",
                "--physical-observation",
                "Download immutable benchmark evidence",
                "operational-candidate-${BENCHMARK_RUN_ID}",
                "benchmark-result-full.json",
                "benchmark/dist/evidence/operational-95-candidate.json",
                "Upload release verification diagnostics",
                "release-verification-${{ inputs.tag }}-${{ github.run_id }}",
                "if: always()",
                "release-assets-build-operational",
                "release-assets-build-certified",
                "release certification build",
                "release certification validate",
                "actions/upload-artifact@",
                "release-certification-${{ inputs.tag }}-${{ github.run_id }}",
                "steps.certification-artifact.outputs.artifact-id",
                "steps.certification-artifact.outputs.artifact-digest",
                'artifact_digest="${CERTIFICATION_ARTIFACT_DIGEST}"',
                'artifact_digest="sha256:${artifact_digest}"',
                '[[ "${artifact_digest}" =~ ^sha256:[0-9a-f]{64}$ ]]',
                "GITHUB_STEP_SUMMARY",
                "Configure isolated certification paths",
                "GITHUB_ENV",
                "RUNNER_TEMP",
            ),
            ".github/workflows/release-certify.yml",
        )
    )
    if "tools.design_craft benchmark" in release_certify_workflow:
        errors.append(
            ".github/workflows/release-certify.yml must verify immutable benchmark evidence without rerunning timings"
        )
    for forbidden in (
        "Preflight release governance credential",
        "RELEASE_GOVERNANCE_TOKEN",
        "--preflight",
        "--require-release-credential",
    ):
        if forbidden in release_certify_workflow:
            errors.append(
                ".github/workflows/release-certify.yml must not depend on "
                f"admin-only governance credentials: {forbidden}"
            )
    for forbidden in (
        "contents: write",
        "id-token: write",
        "attestations: write",
        "actions/attest-build-provenance@",
        "gh release create",
        "npm publish",
    ):
        if forbidden in release_certify_workflow:
            errors.append(
                f".github/workflows/release-certify.yml must not contain publication authority: {forbidden}"
            )
    certify_job = workflow_job_block(release_certify_workflow, "certify")
    if certify_job.count("permissions:") != 1:
        errors.append(
            ".github/workflows/release-certify.yml must scope read permissions to the certify job"
        )
    certify_job_header = certify_job.split("    steps:", 1)[0]
    if "${{ runner." in certify_job_header:
        errors.append(
            ".github/workflows/release-certify.yml must not use the runner context before steps"
        )
    errors.extend(
        require_tokens(
            release_publish_workflow,
            (
                "workflow_dispatch:",
                "certification_run_id:",
                "certification_artifact_id:",
                "certification_artifact_digest:",
                "confirm_publication:",
                "verify:",
                "publish:",
                "needs: verify",
                "actions: read",
                "contents: write",
                "id-token: write",
                "attestations: write",
                "--kind certification",
                "release artifact-observation",
                "release certification validate",
                "--artifact-id",
                "--artifact-digest",
                "actions/artifacts/${CERTIFICATION_ARTIFACT_ID}/zip",
                "sha256sum",
                "X-GitHub-Api-Version: 2022-11-28",
                "actions/attest-build-provenance@",
                "gh release create",
                "GitHub Release ${RELEASE_TAG} already exists",
                "Configure isolated verification paths",
                "GITHUB_ENV",
                "RUNNER_TEMP",
            ),
            ".github/workflows/release-publish.yml",
        )
    )
    if "npm publish" in release_publish_workflow:
        errors.append(
            ".github/workflows/release-publish.yml must not publish to the npm registry"
        )
    if "RELEASE_GOVERNANCE_TOKEN" in release_publish_workflow:
        errors.append(
            ".github/workflows/release-publish.yml must consume the completed certification rather than governance credentials"
        )
    verify_job = workflow_job_block(release_publish_workflow, "verify")
    if verify_job.count("permissions:") != 1:
        errors.append(
            ".github/workflows/release-publish.yml must scope read permissions to the verify job"
        )
    for forbidden in (
        "contents: write",
        "id-token: write",
        "attestations: write",
        "actions/attest-build-provenance@",
        "gh release create",
    ):
        if forbidden in verify_job:
            errors.append(
                ".github/workflows/release-publish.yml verify job must not contain "
                f"publication authority: {forbidden}"
            )
    publish_job = workflow_job_block(release_publish_workflow, "publish")
    if publish_job.count("permissions:") != 1:
        errors.append(
            ".github/workflows/release-publish.yml must scope write permissions to the publish job"
        )
    publish_job_header = publish_job.split("    steps:", 1)[0]
    if "${{ runner." in publish_job_header:
        errors.append(
            ".github/workflows/release-publish.yml must not use the runner context before steps"
        )
    for forbidden in (
        "actions/checkout@",
        "actions/setup-python@",
        "python3 -m tools.design_craft",
        "release certification validate",
    ):
        if forbidden in publish_job:
            errors.append(
                ".github/workflows/release-publish.yml publish job must not execute "
                f"repository validation code: {forbidden}"
            )
    errors.extend(
        require_tokens(
            physical_workflow,
            (
                "workflow_dispatch:",
                "runs-on: [self-hosted, linux, android-physical-device]",
                "if: github.ref == 'refs/heads/main'",
                "environment: physical-device",
                "capture-physical-device",
                "native_runtime_device_android.sh",
                "native-runtime-physical-${{ github.run_id }}",
                "retention-days: 90",
            ),
            ".github/workflows/physical-device.yml",
        )
    )
    if validate_workflow.count("timeout-minutes:") != 5:
        errors.append(".github/workflows/validate.yml must set a timeout on all five jobs")
    for job_name in ("portable", "windows-portable"):
        block = workflow_job_block(validate_workflow, job_name)
        if "submodules: recursive" not in block or "fetch-depth: 0" not in block:
            errors.append(
                f".github/workflows/validate.yml {job_name} must fetch recursive submodules and full history"
            )
    windows_block = workflow_job_block(validate_workflow, "windows-portable")
    for token in (
        "shell: bash",
        "git config --global core.autocrlf false",
        "git config --global core.eol lf",
        "DESIGN_CRAFT_BASH=",
        "GITHUB_ENV",
    ):
        if token not in windows_block:
            errors.append(
                f".github/workflows/validate.yml windows-portable missing {token}"
            )
    if native_workflow.count("timeout-minutes:") != 2:
        errors.append(
            ".github/workflows/native-runtime.yml must set a timeout on both jobs"
        )
    errors.extend(
        require_tokens(
            ios_runner,
            (
                "xcrun simctl",
                "-parse-as-library",
                "-module-name DesignCraftEvidence",
                "simctl openurl",
                "live/cold deep-link interaction",
                "before_screenshot=",
                "interaction_marker=",
                "launch_log=",
                "simulator-selection.txt",
                "runtime-events.txt",
                "runtime-poll-observations.jsonl",
                "native_ios_observation",
                "marker_visibility_grace",
                "openurl-${phase}-exit.txt",
                "attempt=${live_attempt}",
                "open-confirmation.png",
                'tap --label "Open"',
                "confirmation_tap_point",
                "coordinate-tap.log",
                "26a64009c09a3ae980b1f1b4b377bd2a2dd96cbbde24821935e47352cb71cc69",
            ),
            "scripts/native_runtime_ci_ios.sh",
        )
    )
    if "--confirm-runtime" in ios_runner or "--confirm-runtime" in ios_fixture:
        errors.append("iOS certification must not use a test-only --confirm-runtime path")
    if "DESIGN_CRAFT_RUNTIME_URL_RECEIVED" not in ios_fixture:
        errors.append("iOS fixture must log receipt of the real runtime URL")
    if "createDirectory" not in ios_fixture or "runtime-events.txt" not in ios_fixture:
        errors.append("iOS fixture must preserve observable URL and marker-write diagnostics")
    for token in (
        "Runtime interaction pending",
        "interaction-confirmed:\\(attempt)",
        "Runtime interaction confirmed attempt=\\(attempt)",
    ):
        if token not in ios_fixture:
            errors.append(f"iOS fixture missing correlated marker contract: {token}")
    if 'rm -f "${interaction_marker}"' in ios_runner:
        errors.append("iOS runner must not delete the persistent interaction marker")
    errors.extend(
        require_tokens(
            ios_observation,
            (
                "url_receipt",
                "app_confirmation",
                "marker_confirmed",
                "fallback_allowed",
                "openurl_nonzero_after_delivery",
                "url-received:designcraft-evidence:",
            ),
            "tools/design_craft/release/native_ios_observation.py",
        )
    )

    errors.extend(
        require_tokens(
            portable_validator,
            (
                'cygpath -w "${BASH}"',
                "export DESIGN_CRAFT_BASH",
                "tools.design_craft.validation.skill_schema",
                "exec python3 -m tools.design_craft validate --profile portable",
            ),
            "scripts/validate.sh",
        )
    )
    for forbidden in (
        "design_craft_package_validate.py",
        "python3 -m unittest discover",
        "design_craft_maturity.py --profile development",
    ):
        if forbidden in portable_validator:
            errors.append(
                "scripts/validate.sh must delegate source gates to the validation registry: "
                + forbidden
            )
    if ".codex/skills/.system/skill-creator" in portable_validator:
        errors.append("scripts/validate.sh must not depend on a user-home skill validator")

    errors.extend(
        require_tokens(
            lint_validator,
            (
                'os.environ.get("DESIGN_CRAFT_BASH")',
                'normalized.endswith("/windows/system32/bash.exe")',
                "[executable, *command[1:], str(path)]",
            ),
            "scripts/design_craft_lint.py",
        )
    )
    errors.extend(
        require_tokens(
            maturity_validator,
            (
                'os.environ.get("DESIGN_CRAFT_BASH")',
                'normalized.endswith("/windows/system32/bash.exe")',
                "resolved[0] = executable",
            ),
            "tools/design_craft/validation/maturity/process_runner.py",
        )
    )
    errors.extend(
        require_tokens(
            git_attributes,
            (
                "* text=auto eol=lf",
                "evals/comparative/*/blind-packet.md whitespace=-blank-at-eol",
                "evals/comparative/*/output.*.md whitespace=-blank-at-eol",
            ),
            ".gitattributes",
        )
    )

    errors.extend(
        require_tokens(
            android_runner,
            (
                "design_craft_native_runtime_record.py",
                "native_runtime_android_common.sh",
                "before_accessibility_tree=",
                "after_accessibility_tree=",
                "after_screenshot=",
                "launch_log=",
            ),
            "scripts/native_runtime_ci_android.sh",
        )
    )
    errors.extend(
        require_tokens(
            android_common,
            ("uiautomator", "adb exec-out cat", "android:id/aerr_close"),
            "scripts/native_runtime_android_common.sh",
        )
    )
    errors.extend(
        require_tokens(
            dependabot,
            ("package-ecosystem: github-actions", "package-ecosystem: npm"),
            ".github/dependabot.yml",
        )
    )

    for workflow_path in (ROOT / ".github/workflows").glob("*.yml"):
        errors.extend(action_pin_errors(workflow_path, workflow_path.read_text(encoding="utf-8")))

    try:
        probe = json.loads(
            (ROOT / "evals/native-runtime/environment-probe.json").read_text(encoding="utf-8")
        )
        if probe.get("schema") != "design-craft.native-runtime-probe.v1":
            errors.append("native runtime environment probe schema is invalid")
        if not isinstance(probe.get("ios", {}).get("ready"), bool):
            errors.append("native runtime iOS readiness must be boolean")
        if not isinstance(probe.get("android", {}).get("ready"), bool):
            errors.append("native runtime Android readiness must be boolean")
    except Exception as exc:
        errors.append(f"native runtime environment probe is invalid: {exc}")

    try:
        plist = plistlib.loads((ROOT / "evals/native-runtime/fixtures/ios/Info.plist").read_bytes())
        if plist.get("CFBundleIdentifier") != "dev.designcraft.runtime-evidence":
            errors.append("iOS fixture bundle identifier is invalid")
        url_types = plist.get("CFBundleURLTypes", [])
        if not url_types or url_types[0].get("CFBundleTypeRole") != "Viewer":
            errors.append("iOS fixture URL type must declare the Viewer role")
        scene_manifest = plist.get("UIApplicationSceneManifest", {})
        scene_configs = scene_manifest.get("UISceneConfigurations", {})
        if scene_manifest.get("UIApplicationSupportsMultipleScenes") is not False:
            errors.append("iOS fixture must disable multiple scenes")
        if not scene_configs.get("UIWindowSceneSessionRoleApplication"):
            errors.append("iOS fixture must register the UIWindowScene application role")
    except Exception as exc:
        errors.append(f"iOS Info.plist is invalid: {exc}")

    try:
        ET.parse(ROOT / "evals/native-runtime/fixtures/android/app/src/main/AndroidManifest.xml")
    except Exception as exc:
        errors.append(f"Android fixture manifest is invalid: {exc}")

    return {
        "schema": SCHEMA,
        "root": str(ROOT),
        "workflow_count": len(list((ROOT / ".github/workflows").glob("*.yml"))),
        "ok": not errors,
        "errors": errors,
    }


def self_check() -> list[str]:
    errors: list[str] = []
    fake = ROOT / ".github/workflows/fixture.yml"
    if action_pin_errors(fake, "- uses: actions/checkout@v4") == []:
        errors.append("workflow validator did not reject an unpinned action")
    if action_pin_errors(fake, "- uses: actions/checkout@" + "a" * 40):
        errors.append("workflow validator rejected a full-SHA action pin")
    fixture = (
        "jobs:\n"
        "  portable:\n"
        "    steps:\n"
        "      - with:\n"
        "          fetch-depth: 0\n"
        "  windows-portable:\n"
        "    steps: []\n"
    )
    portable = workflow_job_block(fixture, "portable")
    windows = workflow_job_block(fixture, "windows-portable")
    if "fetch-depth: 0" not in portable or "windows-portable" in portable:
        errors.append("workflow job-block parser did not isolate the portable job")
    if "steps: []" not in windows:
        errors.append("workflow job-block parser did not isolate the final job")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not args.check and not args.validate:
        args.validate = True

    errors = self_check() if args.check else []
    payload = validate() if args.validate else {
        "schema": SCHEMA,
        "root": str(ROOT),
        "workflow_count": 0,
        "ok": True,
        "errors": [],
    }
    errors.extend(payload["errors"])
    payload["errors"] = errors
    payload["ok"] = not errors

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    elif payload["ok"]:
        print(f"workflow contracts verified: {payload['workflow_count']} workflows")
    else:
        print("\n".join(errors), file=sys.stderr)
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
