"""Repository and installed-leaf runtime checks plus core CLI adapters."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from creative_craft_contracts import (
    ARTIFACT_REGISTRY,
    IMAGE_PROFILE_ID,
    METADATA_SCHEMAS,
    REPO_ROOT,
    SKILL_ROOT,
    VIDEO_PROFILE_ID,
    Result,
    ValidationContext,
    load_json,
    nonempty,
    provider_profiles,
    sha256_file,
    surface_profiles,
    validate_against_schema,
    validate_data,
    write_atomic,
)
from creative_craft_evaluation import (
    compile_image_markdown,
    compile_video_markdown,
    render_result,
    score_evaluation,
)
from creative_craft_project import validate_project


def markdown_local_links(path: Path) -> Iterable[tuple[str, Path]]:
    text = path.read_text(encoding="utf-8")
    for target in re.findall(r"\]\(([^)]+)\)", text):
        target = target.split("#", 1)[0].strip()
        if not target or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):
            continue
        yield target, (path.parent / target).resolve()


def validate_skill_runtime(skill_root: Path) -> Result:
    """Validate the canonical Skill without requiring repository-only files."""
    r = Result()
    context = ValidationContext(skill_root)
    required = [
        "SKILL.md",
        "VERSION",
        "providers/openai-gpt-image-2.json",
        "providers/bytedance-seedance-2.5.json",
        "providers/surfaces/openai-image-api.json",
        "providers/surfaces/bytedance-jimeng-web.json",
        "scripts/creative_craft.py",
    ]
    for rel in required:
        r.require(
            (skill_root / rel).is_file(), f"skill runtime missing required file: {rel}"
        )

    for schema_version, entry in ARTIFACT_REGISTRY.items():
        r.require(
            (context.schemas_dir / str(entry["schema"])).is_file(),
            f"missing schema for {schema_version}: {entry['schema']}",
        )
        template = entry.get("template")
        if template:
            r.require(
                (skill_root / "templates" / str(template)).is_file(),
                f"missing template for {schema_version}: {template}",
            )
    for schema_version, filename in METADATA_SCHEMAS.items():
        r.require(
            (context.schemas_dir / filename).is_file(),
            f"missing metadata schema for {schema_version}: {filename}",
        )

    try:
        profiles = provider_profiles(context.providers_dir)
        surfaces = surface_profiles(context.surfaces_dir)
    except ValueError as exc:
        r.errors.append(str(exc))
        profiles = {}
        surfaces = {}
    r.require(
        IMAGE_PROFILE_ID in profiles, f"missing provider profile {IMAGE_PROFILE_ID}"
    )
    r.require(
        VIDEO_PROFILE_ID in profiles, f"missing provider profile {VIDEO_PROFILE_ID}"
    )
    for profile_id, profile in profiles.items():
        metadata_result = validate_against_schema(
            profile,
            context.schemas_dir / METADATA_SCHEMAS["creative-craft.provider.v1"],
        )
        r.errors.extend(
            f"provider {profile_id}: {message}" for message in metadata_result.errors
        )
    for surface_id, surface in surfaces.items():
        metadata_result = validate_against_schema(
            surface, context.schemas_dir / METADATA_SCHEMAS["creative-craft.surface.v1"]
        )
        r.errors.extend(
            f"surface {surface_id}: {message}" for message in metadata_result.errors
        )
        for profile_id in surface.get("provider_profiles", []):
            r.require(
                profile_id in profiles,
                f"surface {surface_id} references unknown provider_profile {profile_id}",
            )
    return r


def is_repository_checkout(root: Path) -> bool:
    sentinels = [
        "package.json",
        ".codex-plugin/plugin.json",
        "sources.lock.json",
        "skills/creative-craft/SKILL.md",
    ]
    return all((root / rel).is_file() for rel in sentinels)


def doctor(root: Path = REPO_ROOT) -> Result:
    r = Result()
    skill_root = root / "skills" / "creative-craft"
    context = ValidationContext(skill_root)
    required = [
        "README.md",
        "README.zh-CN.md",
        "LICENSE",
        "VERSION",
        "package.json",
        ".codex-plugin/plugin.json",
        "sources.lock.json",
    ]
    for rel in required:
        r.require((root / rel).is_file(), f"missing required file: {rel}")
    r.extend(validate_skill_runtime(skill_root))

    if (root / "VERSION").is_file():
        version = (root / "VERSION").read_text(encoding="utf-8").strip()
        if (root / "skills/creative-craft/VERSION").is_file():
            r.require(
                (root / "skills/creative-craft/VERSION")
                .read_text(encoding="utf-8")
                .strip()
                == version,
                "root and skill VERSION do not match",
            )
        for rel, field_path in [
            ("package.json", ("version",)),
            (".codex-plugin/plugin.json", ("version",)),
        ]:
            path = root / rel
            if path.is_file():
                try:
                    data = load_json(path)
                    actual: Any = data
                    for field_name in field_path:
                        actual = actual[field_name]
                    r.require(
                        actual == version,
                        f"{rel} version {actual!r} does not match {version!r}",
                    )
                except (ValueError, KeyError) as exc:
                    r.errors.append(str(exc))

        package_path = root / "package.json"
        plugin_path = root / ".codex-plugin/plugin.json"
        if package_path.is_file() and plugin_path.is_file():
            try:
                package_metadata = load_json(package_path)
                plugin_metadata = load_json(plugin_path)
                package_python = package_metadata.get("creativeCraft", {}).get("python")
                plugin_python = plugin_metadata.get("runtime", {}).get("python")
                r.require(
                    nonempty(package_python),
                    "package.json must declare creativeCraft.python",
                )
                r.require(
                    plugin_python == package_python,
                    ".codex-plugin/plugin.json runtime.python must match package.json creativeCraft.python",
                )
            except ValueError as exc:
                r.errors.append(str(exc))

        expected_tag = f"v{version}"
        published_install_tag = expected_tag
        if package_path.is_file():
            try:
                package_metadata = load_json(package_path)
                creative_craft_metadata = package_metadata.get("creativeCraft", {})
                release_status = creative_craft_metadata.get("releaseStatus")
                r.require(
                    release_status in {"unreleased-candidate", "released"},
                    "package.json creativeCraft.releaseStatus must be unreleased-candidate or released",
                )
                declared_tag = creative_craft_metadata.get("publishedInstallTag")
                if declared_tag is not None:
                    r.require(
                        isinstance(declared_tag, str)
                        and re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", declared_tag)
                        is not None,
                        "package.json creativeCraft.publishedInstallTag must be an immutable release tag",
                    )
                    if isinstance(declared_tag, str):
                        published_install_tag = declared_tag
                if release_status == "released":
                    r.require(
                        published_install_tag == expected_tag,
                        "released package metadata must publish the tag matching VERSION",
                    )
                elif release_status == "unreleased-candidate":
                    r.require(
                        published_install_tag != expected_tag,
                        "unreleased candidate metadata must not claim its VERSION tag is published",
                    )
            except ValueError as exc:
                r.errors.append(str(exc))
        for rel in ("adapters/pi/README.md", "adapters/codex/README.md"):
            path = root / rel
            if not path.is_file():
                r.errors.append(f"missing Tier 1 adapter documentation: {rel}")
                continue
            tags = re.findall(
                r"(?<![A-Za-z0-9])v[0-9]+\.[0-9]+\.[0-9]+",
                path.read_text(encoding="utf-8"),
            )
            r.require(bool(tags), f"{rel} must contain an immutable release tag")
            for tag in sorted(set(tags)):
                r.require(
                    tag == published_install_tag,
                    f"{rel} install tag {tag!r} does not match declared published tag {published_install_tag!r}",
                )

    ignored_parts = {".git", ".venv", "__pycache__", "dist", "node_modules"}
    for path in sorted(root.rglob("*.json")):
        if any(part in ignored_parts for part in path.parts):
            continue
        try:
            load_json(path)
        except ValueError as exc:
            r.errors.append(str(exc))

    source_lock = root / "sources.lock.json"
    if source_lock.is_file():
        source_data = load_json(source_lock)
        metadata_result = validate_against_schema(
            source_data,
            context.schemas_dir / METADATA_SCHEMAS["creative-craft.sources.v1"],
        )
        r.errors.extend(
            f"sources.lock.json: {message}" for message in metadata_result.errors
        )
        source_ids: set[str] = set()
        for source in source_data.get("sources", []):
            if isinstance(source, dict) and isinstance(source.get("id"), str):
                r.require(
                    source["id"] not in source_ids,
                    f"sources.lock.json has duplicate source id {source['id']}",
                )
                source_ids.add(source["id"])

    for path in sorted(root.rglob("*.md")):
        if any(part in ignored_parts for part in path.parts):
            continue
        for target, resolved in markdown_local_links(path):
            r.require(
                resolved.exists(),
                f"broken local link in {path.relative_to(root)}: {target}",
            )

    return r


def cmd_doctor(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve() if args.root else REPO_ROOT
    result = doctor(root)
    return render_result(root, "repository", result, args.json)


def cmd_self_test(args: argparse.Namespace) -> int:
    """Run repository or installed-runtime smoke tests without network access."""
    requested_root = Path(args.root).resolve() if args.root else None
    requested_scope = getattr(args, "scope", "auto")
    repository_scope = requested_scope == "repository" or (
        requested_scope == "auto"
        and (requested_root is not None or is_repository_checkout(REPO_ROOT))
    )
    if repository_scope:
        root = requested_root or REPO_ROOT
        skill_root = root / "skills" / "creative-craft"
        preflight = doctor(root)
        runtime_valid = validate_skill_runtime(skill_root).ok
        label = "package self-test"
    else:
        root = requested_root or SKILL_ROOT
        skill_root = root
        preflight = validate_skill_runtime(skill_root)
        runtime_valid = preflight.ok
        label = "installed runtime self-test"
    context = ValidationContext(skill_root)
    checks: list[dict[str, Any]] = []
    errors = list(preflight.errors)
    warnings = list(preflight.warnings)

    templates_dir = skill_root / "templates"
    for path in sorted(templates_dir.glob("*.json")):
        try:
            data = load_json(path)
        except ValueError as exc:
            errors.append(str(exc))
            checks.append({"file": str(path), "kind": "unknown", "valid": False})
            continue
        kind, result = validate_data(data, "auto", context)
        errors.extend(f"{path.name}: {message}" for message in result.errors)
        warnings.extend(f"{path.name}: {message}" for message in result.warnings)
        checks.append(
            {
                "file": str(path.relative_to(root)),
                "kind": kind,
                "valid": result.ok,
            }
        )

    # Exercise deterministic compilers and the evidence-aware scoring path.
    try:
        image_data = load_json(templates_dir / "image-job.json")
        image_pack = compile_image_markdown(image_data)
        if "# Image execution pack" not in image_pack:
            errors.append("image compiler did not produce an execution pack")

        video_data = load_json(templates_dir / "video-job.json")
        video_pack = compile_video_markdown(video_data)
        if "# Video execution pack" not in video_pack:
            errors.append("video compiler did not produce an execution pack")

        evaluation_data = load_json(templates_dir / "evaluation.json")
        score = score_evaluation(evaluation_data)
        if score.get("status") not in {"scored", "withheld", "blocked"}:
            errors.append("evaluation scorer returned an invalid status")
    except (KeyError, OSError, TypeError, ValueError) as exc:
        errors.append(f"package smoke path failed: {exc}")

    payload = {
        "valid": not errors,
        "scope": "repository" if repository_scope else "runtime",
        "root": str(root),
        "repository_valid": preflight.ok if repository_scope else None,
        "runtime_valid": runtime_valid,
        "artifact_checks": checks,
        "errors": errors,
        "warnings": warnings,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"PASS {label}" if not errors else f"FAIL {label}")
        print(f"  Artifact templates: {len(checks)}")
        for message in errors:
            print(f"  ERROR: {message}")
        for message in warnings:
            print(f"  WARN:  {message}")
    return 0 if not errors else 1


def cmd_validate(args: argparse.Namespace) -> int:
    path = Path(args.file).resolve()
    try:
        data = load_json(path)
    except ValueError as exc:
        result = Result(errors=[str(exc)])
        return render_result(path, args.kind, result, args.json)
    kind, result = validate_data(data, args.kind)
    return render_result(path, kind, result, args.json)


def output_text(text: str, output: str | None) -> None:
    if output:
        path = Path(output).expanduser().absolute()
        write_atomic(path, text)
        print(path)
    else:
        print(text, end="")


def cmd_compile_image(args: argparse.Namespace) -> int:
    path = Path(args.file).resolve()
    try:
        data = load_json(path)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    _, result = validate_data(data, "image")
    if not result.ok:
        render_result(path, "image", result, False)
        return 1
    for warning in result.warnings:
        print(f"WARN: {warning}", file=sys.stderr)
    try:
        output_text(compile_image_markdown(data), args.output)
    except (OSError, ValueError) as exc:
        print(f"ERROR: failed to compile image output: {exc}", file=sys.stderr)
        return 1
    return 0


def cmd_compile_video(args: argparse.Namespace) -> int:
    path = Path(args.file).resolve()
    try:
        data = load_json(path)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    _, result = validate_data(data, "video")
    if not result.ok:
        render_result(path, "video", result, False)
        return 1
    for warning in result.warnings:
        print(f"WARN: {warning}", file=sys.stderr)
    try:
        output_text(compile_video_markdown(data), args.output)
    except (OSError, ValueError) as exc:
        print(f"ERROR: failed to compile video output: {exc}", file=sys.stderr)
        return 1
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    path = Path(args.file).resolve()
    try:
        data = load_json(path)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    graph = validate_project(Path(args.root)) if args.root else None
    result = score_evaluation(data, graph)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Status: {result['status']}")
        if result.get("score") is not None:
            print(f"Score: {result['score']:.2f}/100")
        if result.get("coverage") is not None:
            print(f"Evidence coverage: {result['coverage']:.2f}%")
        if result.get("confidence"):
            print(f"Confidence: {result['confidence']}")
        if result.get("failed_gates"):
            print("Failed gates: " + ", ".join(result["failed_gates"]))
        if result.get("reason"):
            print("Reason: " + result["reason"])
        if result.get("recommendation"):
            print("Recommendation: " + result["recommendation"])
        for warning in result.get("warnings", []):
            print(f"WARN: {warning}")
        for error in result.get("errors", []):
            print(f"ERROR: {error}")
    return 0 if result["status"] in {"scored", "withheld", "blocked"} else 1


def cmd_hash(args: argparse.Namespace) -> int:
    path = Path(args.file).resolve()
    if not path.is_file():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 1
    digest = sha256_file(path)
    if args.json:
        print(
            json.dumps(
                {
                    "file": str(path),
                    "bytes": path.stat().st_size,
                    "sha256": digest,
                },
                indent=2,
            )
        )
    else:
        print(digest)
    return 0
