#!/usr/bin/env python3
"""Build self-contained skill bundles from the repository manifest."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "skill-pack.json"
INTERNAL_VALIDATOR = ROOT / "tooling/validation/quick_validate_skill.py"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tooling.installation.tree_integrity import (
    TreeIntegrityError,
    is_runtime_cache,
    lexical_absolute,
    validate_tree,
)
from tooling.manifest import ManifestError, load_manifest


def default_validator() -> Path:
    configured = os.environ.get("SKILL_QUICK_VALIDATOR")
    if configured:
        return Path(configured).expanduser()
    return INTERNAL_VALIDATOR


class BuildError(RuntimeError):
    pass


def safe_source(relative: str) -> Path:
    path = ROOT / relative
    files = validate_tree(path, allowed_root=ROOT)
    cache_artifacts = [item for item in files if is_runtime_cache(item.relative_to(path))]
    if cache_artifacts:
        raise BuildError(f"source contains runtime cache artifact: {cache_artifacts[0]}")
    return path


def copy_resource(source: Path, target: Path) -> None:
    if target.exists():
        raise BuildError(f"bundle target collision: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, target, symlinks=True)
    else:
        shutil.copy2(source, target, follow_symlinks=False)


def parse_skill_name(skill_md: Path) -> str:
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise BuildError(f"missing YAML frontmatter: {skill_md}")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise BuildError(f"unterminated YAML frontmatter: {skill_md}")
    for line in text[4:end].splitlines():
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip()
    raise BuildError(f"missing skill name: {skill_md}")


def selected_skills(manifest: dict[str, Any], requested: list[str]) -> list[dict[str, Any]]:
    skills = manifest["skills"]
    if not requested:
        return skills
    by_name = {skill["name"]: skill for skill in skills}
    missing = sorted(set(requested) - set(by_name))
    if missing:
        raise BuildError(f"unknown skills: {', '.join(missing)}")
    return [by_name[name] for name in requested]


def validate_bundle(bundle: Path, validator: Path) -> None:
    if not validator.is_file():
        raise BuildError(f"quick validator not found: {validator}")
    subprocess.run([sys.executable, str(validator), str(bundle)], check=True)


def build(
    manifest_path: Path,
    output: Path,
    requested: list[str],
    run_validator: bool,
    validator: Path,
) -> list[Path]:
    manifest = load_manifest(manifest_path)
    output = lexical_absolute(output)
    if os.path.lexists(output) and (output.is_symlink() or not output.is_dir()):
        raise BuildError(f"output must be a real directory path: {output}")
    if output.exists() and any(output.iterdir()):
        raise BuildError(f"output directory must be empty: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}.staged-", dir=output.parent))
    built_names: list[str] = []
    try:
        for skill in selected_skills(manifest, requested):
            name = skill["name"]
            source = safe_source(skill["source"])
            skill_md = source / "SKILL.md"
            if not skill_md.is_file():
                raise BuildError(f"missing SKILL.md for {name}")
            if parse_skill_name(skill_md) != name:
                raise BuildError(f"frontmatter name does not match manifest for {name}")

            bundle = staging / name
            shutil.copytree(source, bundle, symlinks=True)
            for resource in skill.get("resources", []):
                target = bundle / resource["target"]
                try:
                    target.resolve().relative_to(bundle.resolve())
                except ValueError as exc:
                    raise BuildError(f"resource target escapes bundle for {name}: {target}") from exc
                copy_resource(safe_source(resource["source"]), target)

            validate_tree(bundle, require_directory=True)
            if run_validator:
                validate_bundle(bundle, validator)
            built_names.append(name)

        if output.exists():
            output.rmdir()
        staging.rename(output)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return [output / name for name in built_names]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--output", required=True)
    parser.add_argument("--skill", action="append", default=[])
    parser.add_argument("--skip-quick-validate", action="store_true")
    parser.add_argument("--validator", default=str(default_validator()))
    args = parser.parse_args()

    try:
        bundles = build(
            Path(args.manifest),
            Path(args.output),
            args.skill,
            not args.skip_quick_validate,
            Path(args.validator),
        )
        for bundle in bundles:
            print(bundle)
        return 0
    except (BuildError, ManifestError, TreeIntegrityError, OSError, subprocess.CalledProcessError) as exc:
        print(f"build_skill_bundles error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
