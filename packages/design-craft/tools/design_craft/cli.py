from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from .validation.cli import run_validate
from .validation.maturity.cli import run_maturity
from .benchmark.cli import run_benchmark
from .quality.cli import run_quality
from .release.cli import run_release


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.design_craft",
        description="Run design-craft repository governance commands.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate", help="Run a declared validation profile.")
    validate.add_argument(
        "--profile",
        choices=(
            "contracts",
            "portable",
            "local",
            "operational-release",
            "certified-release",
        ),
        default="portable",
    )
    maturity = subparsers.add_parser(
        "maturity", help="Evaluate explicit development or release maturity."
    )
    maturity.add_argument(
        "--profile",
        choices=("development", "operational_95", "certified_100"),
        default="development",
    )
    maturity.add_argument("--phase", choices=("candidate", "final"), default="candidate")
    maturity.add_argument("--baseline", type=Path)
    maturity.add_argument("--benchmark-result", type=Path)
    maturity.add_argument("--benchmark-observation", type=Path)
    maturity.add_argument("--jobs", type=int, default=0)
    maturity.add_argument("--json", action="store_true")
    maturity.add_argument("--check", action="store_true")
    validate.add_argument("--json", action="store_true", help="Emit structured JSON.")
    validate.add_argument("--list", action="store_true", help="List selected gates without running them.")
    validate.add_argument(
        "--jobs",
        type=int,
        default=0,
        help="Maximum parallel jobs; 0 selects a bounded automatic value.",
    )
    benchmark = subparsers.add_parser("benchmark", help="Run performance regression benchmarks.")
    benchmark.add_argument("--scale", choices=("smoke", "full"), default="smoke")
    benchmark.add_argument("--baseline", help="Compare against a benchmark result JSON.")
    benchmark.add_argument("--output", help="Write the current benchmark result JSON.")
    benchmark.add_argument(
        "--migrate-v1",
        help="Explicitly migrate a v1 benchmark result instead of running benchmarks.",
    )
    benchmark.add_argument("--runner-image", help="Runner image family for v1 migration.")
    benchmark.add_argument("--image-version", help="Runner image version for v1 migration.")
    benchmark.add_argument("--node-version", help="Node version for v1 migration.")
    benchmark.add_argument("--json", action="store_true")
    quality = subparsers.add_parser("quality", help="Report independent quality domains.")
    quality.add_argument("--level", choices=("operational_95", "certified_100"), default="operational_95")
    quality.add_argument("--baseline", help="Benchmark baseline JSON.")
    quality.add_argument("--json", action="store_true")
    release = subparsers.add_parser("release", help="Verify a tiered release contract.")
    release_subcommands = release.add_subparsers(dest="release_command", required=True)
    release_verify = release_subcommands.add_parser("verify", help="Verify release evidence.")
    release_verify.add_argument("--level", choices=("operational_95", "certified_100"), required=True)
    release_verify.add_argument("--phase", choices=("candidate", "final"), default="candidate")
    release_verify.add_argument("--baseline", help="Benchmark baseline JSON.")
    release_verify.add_argument(
        "--benchmark-result",
        help="Precomputed full benchmark result JSON for deterministic verification.",
    )
    release_verify.add_argument(
        "--benchmark-observation",
        help="Exact benchmark workflow observation required for final verification.",
    )
    release_verify.add_argument("--output", help="Write the release evidence report.")
    release_verify.add_argument("--json", action="store_true")
    release_assets = release_subcommands.add_parser("assets", help="Build or validate exact release assets.")
    release_assets.add_argument("--level", choices=("operational_95", "certified_100"), required=True)
    release_assets.add_argument("--output-dir", default="dist/release")
    release_assets.add_argument("--evidence", help="Passing release evidence JSON required for builds.")
    release_assets.add_argument(
        "--evidence-root",
        help="Root used to resolve artifact-relative native evidence paths.",
    )
    release_assets.add_argument("--build", action="store_true")
    release_assets.add_argument("--force", action="store_true")
    release_assets.add_argument("--json", action="store_true")
    run_observation = release_subcommands.add_parser(
        "run-observation", help="Observe and persist one exact GitHub workflow run."
    )
    run_observation.add_argument(
        "--kind",
        choices=("native", "physical", "benchmark", "certification"),
        required=True,
    )
    run_observation.add_argument("--run-id", required=True)
    run_observation.add_argument("--repository")
    run_observation.add_argument("--output", required=True)
    run_observation.add_argument("--json", action="store_true")
    artifact_observation = release_subcommands.add_parser(
        "artifact-observation",
        help="Observe one exact GitHub Actions artifact from a certification run.",
    )
    artifact_observation.add_argument("--artifact-id", required=True)
    artifact_observation.add_argument("--certification-observation", required=True)
    artifact_observation.add_argument("--expected-name", required=True)
    artifact_observation.add_argument("--output", required=True)
    artifact_observation.add_argument("--json", action="store_true")
    evidence_bindings = release_subcommands.add_parser(
        "evidence-bindings",
        help="Bind final release evidence to selected workflow observations.",
    )
    evidence_bindings.add_argument(
        "--level", choices=("operational_95", "certified_100"), required=True
    )
    evidence_bindings.add_argument("--evidence", required=True)
    evidence_bindings.add_argument(
        "--evidence-root",
        required=True,
        help="Root used to resolve artifact-relative native evidence paths.",
    )
    evidence_bindings.add_argument("--native-observation", required=True)
    evidence_bindings.add_argument("--benchmark-observation", required=True)
    evidence_bindings.add_argument("--benchmark-result", required=True)
    evidence_bindings.add_argument("--physical-observation")
    evidence_bindings.add_argument("--json", action="store_true")
    certification = release_subcommands.add_parser(
        "certification",
        help="Build or validate an immutable release certification bundle.",
    )
    certification_commands = certification.add_subparsers(
        dest="certification_command",
        required=True,
    )
    certification_build = certification_commands.add_parser("build")
    certification_build.add_argument(
        "--level", choices=("operational_95", "certified_100"), required=True
    )
    certification_build.add_argument("--tag", required=True)
    certification_build.add_argument("--evidence", required=True)
    certification_build.add_argument("--evidence-root", required=True)
    certification_build.add_argument("--native-observation", required=True)
    certification_build.add_argument("--benchmark-observation", required=True)
    certification_build.add_argument("--benchmark-result", required=True)
    certification_build.add_argument("--physical-observation")
    certification_build.add_argument("--assets-dir", required=True)
    certification_build.add_argument("--repository", required=True)
    certification_build.add_argument("--workflow-run-id", type=int, required=True)
    certification_build.add_argument("--workflow-run-attempt", type=int, required=True)
    certification_build.add_argument("--output-dir", required=True)
    certification_build.add_argument("--json", action="store_true")
    certification_validate = certification_commands.add_parser("validate")
    certification_validate.add_argument(
        "--level", choices=("operational_95", "certified_100"), required=True
    )
    certification_validate.add_argument("--input-dir", required=True)
    certification_validate.add_argument("--certification-observation")
    certification_validate.add_argument("--artifact-observation")
    certification_validate.add_argument("--artifact-id", type=int)
    certification_validate.add_argument("--artifact-digest")
    certification_validate.add_argument("--json", action="store_true")
    native_bundle = release_subcommands.add_parser(
        "native-bundle", help="Build or validate the Certified native evidence bundle."
    )
    native_commands = native_bundle.add_subparsers(
        dest="native_bundle_command", required=True
    )
    native_build = native_commands.add_parser(
        "build", help="Build from already downloaded, separately rooted evidence."
    )
    native_build.add_argument("--output-dir", default="dist/release")
    native_build.add_argument("--native-observation", required=True)
    native_build.add_argument("--physical-observation", required=True)
    native_build.add_argument("--ios-source", required=True)
    native_build.add_argument("--android-source", required=True)
    native_build.add_argument("--physical-device-source", required=True)
    native_build.add_argument("--force", action="store_true")
    native_build.add_argument("--json", action="store_true")
    native_validate = native_commands.add_parser(
        "validate", help="Validate an existing native bundle triplet."
    )
    native_validate.add_argument("--output-dir", default="dist/release")
    native_validate.add_argument("--verify-run", action="store_true")
    native_validate.add_argument("--json", action="store_true")
    release_sbom = release_subcommands.add_parser("sbom", help="Generate a deterministic SPDX 2.3 SBOM.")
    release_sbom.add_argument("--package", required=True)
    release_sbom.add_argument("--output", required=True)
    release_sbom.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "validate":
        return run_validate(args)
    if args.command == "maturity":
        return run_maturity(args, parser)
    if args.command == "benchmark":
        return run_benchmark(args)
    if args.command == "quality":
        return run_quality(args)
    if args.command == "release":
        return run_release(args)
    parser.error(f"unknown command: {args.command}")
    return 2
