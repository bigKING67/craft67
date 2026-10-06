"""Argument parser and public Creative Craft CLI entrypoint."""

from __future__ import annotations

import argparse

from creative_craft_contracts import SCHEMA_TO_KIND
from creative_craft_packs import (
    cmd_bind_reference_pack,
    cmd_init_brand_pack,
    cmd_init_reference_pack,
    cmd_update_reference_snapshot,
    cmd_validate_brand_pack,
    cmd_validate_reference_pack,
)
from creative_craft_project_ops import (
    cmd_doctor_project,
    cmd_inspect_output,
    cmd_project_status,
    cmd_seed,
    cmd_start_revision,
    cmd_update_brand_snapshot,
    cmd_validate_project,
    cmd_verify_delivery,
)
from creative_craft_runtime import (
    cmd_compile_image,
    cmd_compile_video,
    cmd_doctor,
    cmd_hash,
    cmd_score,
    cmd_self_test,
    cmd_validate,
)
from creative_craft_video import register_video_commands


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="creative-craft",
        description="Validate and compile Creative Craft artifacts without calling providers.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    doctor_parser = sub.add_parser("doctor", help="check repository integrity")
    doctor_parser.add_argument("--root")
    doctor_parser.add_argument("--json", action="store_true")
    doctor_parser.set_defaults(func=cmd_doctor)

    self_test_parser = sub.add_parser(
        "self-test",
        help="run repository or installed-runtime validation and compiler smoke tests",
    )
    self_test_parser.add_argument("--root")
    self_test_parser.add_argument(
        "--scope",
        choices=["auto", "repository", "runtime"],
        default="auto",
        help="force repository or leaf-runtime validation; default auto-detects the checkout",
    )
    self_test_parser.add_argument("--json", action="store_true")
    self_test_parser.set_defaults(func=cmd_self_test)

    validate_parser = sub.add_parser("validate", help="validate a versioned artifact")
    validate_parser.add_argument("--file", required=True)
    validate_parser.add_argument(
        "--kind",
        default="auto",
        choices=["auto", *sorted(set(SCHEMA_TO_KIND.values()))],
    )
    validate_parser.add_argument("--json", action="store_true")
    validate_parser.set_defaults(func=cmd_validate)

    image_parser = sub.add_parser(
        "compile-image", help="compile an image job into a prompt pack"
    )
    image_parser.add_argument("--file", required=True)
    image_parser.add_argument("--output")
    image_parser.set_defaults(func=cmd_compile_image)

    video_parser = sub.add_parser(
        "compile-video", help="compile a video job into a prompt pack"
    )
    video_parser.add_argument("--file", required=True)
    video_parser.add_argument("--output")
    video_parser.set_defaults(func=cmd_compile_video)

    score_parser = sub.add_parser(
        "score", help="calculate an evidence-aware comparative score"
    )
    score_parser.add_argument("--file", required=True)
    score_parser.add_argument(
        "--root", help="project root required for evidence-bound evaluation v2"
    )
    score_parser.add_argument("--json", action="store_true")
    score_parser.set_defaults(func=cmd_score)

    hash_parser = sub.add_parser("hash", help="calculate an asset SHA-256")
    hash_parser.add_argument("--file", required=True)
    hash_parser.add_argument("--json", action="store_true")
    hash_parser.set_defaults(func=cmd_hash)

    init_brand_parser = sub.add_parser(
        "init-brand-pack", help="initialize a private draft Brand Skill authority pack"
    )
    init_brand_parser.add_argument("--target", required=True)
    init_brand_parser.add_argument("--brand-id", required=True)
    init_brand_parser.add_argument("--brand-name", required=True)
    init_brand_parser.add_argument("--owner", required=True)
    init_brand_parser.add_argument("--force", action="store_true")
    init_brand_parser.set_defaults(func=cmd_init_brand_pack)

    validate_brand_parser = sub.add_parser(
        "validate-brand-pack",
        help="validate Brand Pack authority, files, digests, and rights",
    )
    validate_brand_parser.add_argument("--root", required=True)
    validate_brand_parser.add_argument("--json", action="store_true")
    validate_brand_parser.set_defaults(func=cmd_validate_brand_pack)

    init_reference_parser = sub.add_parser(
        "init-reference-pack",
        help="initialize a private draft non-authoritative creative Reference Pack",
    )
    init_reference_parser.add_argument("--target", required=True)
    init_reference_parser.add_argument("--pack-id", required=True)
    init_reference_parser.add_argument("--name", required=True)
    init_reference_parser.add_argument("--owner", required=True)
    init_reference_parser.add_argument("--force", action="store_true")
    init_reference_parser.set_defaults(func=cmd_init_reference_pack)

    validate_reference_parser = sub.add_parser(
        "validate-reference-pack",
        help="validate Reference Pack evidence, files, digests, and input rights",
    )
    validate_reference_parser.add_argument("--root", required=True)
    validate_reference_parser.add_argument("--json", action="store_true")
    validate_reference_parser.set_defaults(func=cmd_validate_reference_pack)

    seed_parser = sub.add_parser(
        "seed", help="seed planning scaffolds and draft job templates into a project"
    )
    seed_parser.add_argument("--target", required=True)
    seed_parser.add_argument("--brand-pack")
    seed_parser.add_argument("--brand-source-uri")
    seed_parser.add_argument("--brand-source-ref")
    seed_parser.add_argument("--brand-source-commit")
    seed_parser.add_argument("--imported-by", default="TBD")
    seed_parser.add_argument("--force", action="store_true")
    seed_parser.set_defaults(func=cmd_seed)

    update_brand_parser = sub.add_parser(
        "update-brand-snapshot",
        help="replace a project Brand Pack snapshot with backup, lineage, and rollback",
    )
    update_brand_parser.add_argument("--target", required=True)
    update_brand_parser.add_argument("--brand-pack", required=True)
    update_brand_parser.add_argument("--reason", required=True)
    update_brand_parser.add_argument("--brand-source-uri")
    update_brand_parser.add_argument("--brand-source-ref")
    update_brand_parser.add_argument("--brand-source-commit")
    update_brand_parser.add_argument("--imported-by", default="TBD")
    update_brand_parser.set_defaults(func=cmd_update_brand_snapshot)

    bind_reference_parser = sub.add_parser(
        "bind-reference-pack",
        help="add an immutable Reference Pack snapshot without changing brand authority",
    )
    bind_reference_parser.add_argument("--target", required=True)
    bind_reference_parser.add_argument("--reference-pack", required=True)
    bind_reference_parser.add_argument("--select", action="append")
    bind_reference_parser.add_argument("--reference-source-uri")
    bind_reference_parser.add_argument("--reference-source-ref")
    bind_reference_parser.add_argument("--reference-source-commit")
    bind_reference_parser.add_argument("--imported-by", default="TBD")
    bind_reference_parser.add_argument("--reason")
    bind_reference_parser.set_defaults(func=cmd_bind_reference_pack)

    update_reference_parser = sub.add_parser(
        "update-reference-snapshot",
        help="replace one Reference Pack snapshot with backup, lineage, and rollback",
    )
    update_reference_parser.add_argument("--target", required=True)
    update_reference_parser.add_argument("--reference-pack", required=True)
    update_reference_parser.add_argument("--select", action="append")
    update_reference_parser.add_argument("--reference-source-uri")
    update_reference_parser.add_argument("--reference-source-ref")
    update_reference_parser.add_argument("--reference-source-commit")
    update_reference_parser.add_argument("--imported-by", default="TBD")
    update_reference_parser.add_argument("--reason", required=True)
    update_reference_parser.set_defaults(func=cmd_update_reference_snapshot)

    project_parser = sub.add_parser(
        "validate-project",
        help="validate a project manifest, digests, and cross-artifact graph",
    )
    project_parser.add_argument("--root", required=True)
    project_parser.add_argument("--json", action="store_true")
    project_parser.set_defaults(func=cmd_validate_project)

    project_doctor_parser = sub.add_parser(
        "doctor-project",
        help="diagnose invalid graphs and unregistered project artifacts without writing",
    )
    project_doctor_parser.add_argument("--root", required=True)
    project_doctor_parser.add_argument("--json", action="store_true")
    project_doctor_parser.set_defaults(func=cmd_doctor_project)

    status_parser = sub.add_parser(
        "project-status", help="project evidence and derived job status summary"
    )
    status_parser.add_argument("--root", required=True)
    status_parser.add_argument("--json", action="store_true")
    status_parser.set_defaults(func=cmd_project_status)

    inspection_parser = sub.add_parser(
        "inspect-output", help="create a digest-bound draft inspection skeleton"
    )
    inspection_parser.add_argument("--job", required=True)
    inspection_parser.add_argument("--receipt", required=True)
    inspection_parser.add_argument("--file", required=True)
    inspection_parser.add_argument("--output", required=True)
    inspection_parser.add_argument("--inspector", default="TBD")
    inspection_parser.add_argument("--force", action="store_true")
    inspection_parser.set_defaults(func=cmd_inspect_output)

    revision_parser = sub.add_parser(
        "start-revision", help="create a draft one-variable revision lineage artifact"
    )
    revision_parser.add_argument("--inspection", required=True)
    revision_parser.add_argument("--output", required=True)
    revision_parser.add_argument("--primary-variable", default="TBD")
    revision_parser.add_argument("--reason", default="TBD")
    revision_parser.add_argument("--force", action="store_true")
    revision_parser.set_defaults(func=cmd_start_revision)

    delivery_parser = sub.add_parser(
        "verify-delivery",
        help="verify a delivered v2 manifest against project evidence",
    )
    delivery_parser.add_argument("--root", required=True)
    delivery_parser.add_argument("--file", required=True)
    delivery_parser.add_argument("--json", action="store_true")
    delivery_parser.set_defaults(func=cmd_verify_delivery)

    register_video_commands(sub)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
