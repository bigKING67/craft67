#!/usr/bin/env python3
"""Validate the source tree or one installed 3d-craft Skill without third-party Python packages."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


VENDORED_GLTF_FILES = {
    "module.mjs": "d2a88775a8b22f61be8e00644760f0f04b615fad0fc5175fefd40e0da4df2c8f",
    "gltf_validator.dart.js": "b73a7b2d455ac217567725138b46d826a13d7d1bb0c88c15f7c571bfb349298c",
    "LICENSE": "3ddf9be5c28fe27dad143a5dc76eea25222ad1dd68934a047064e56ed2fa40c5",
    "NOTICES": "933f161ca1e7b3ead5a6cf93ebb3bf6cb67f0e79b38e08d2046f8cdc41cb78a3",
    "package.json": "3578d16153fa237c72784588da2e8fcccc9cd3c1c58ef34c7912f0732d2f5fa6",
}

VENDORED_GLTF_BINARY_PATHS = {
    "skills/3d-craft/vendor/gltf-validator/LICENSE",
    "skills/3d-craft/vendor/gltf-validator/NOTICES",
    "skills/3d-craft/vendor/gltf-validator/gltf_validator.dart.js",
    "skills/3d-craft/vendor/gltf-validator/module.mjs",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def validate_skill(skill: Path, errors: list[str]) -> None:
    skill_file = skill / "SKILL.md"
    if not skill_file.is_file():
        fail(errors, f"missing {skill_file}")
        return
    text = skill_file.read_text(encoding="utf-8")
    lines = text.splitlines()
    if len(lines) > 500:
        fail(errors, f"SKILL.md exceeds 500 lines: {len(lines)}")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        fail(errors, "SKILL.md frontmatter is missing")
    frontmatter = text.split("---", 2)[1]
    allowed_frontmatter = {"name", "description", "license", "allowed-tools", "metadata"}
    top_level_keys = set(re.findall(r"(?m)^([A-Za-z0-9-]+):", frontmatter))
    unexpected_keys = top_level_keys - allowed_frontmatter
    if unexpected_keys:
        fail(errors, f"unsupported top-level SKILL.md frontmatter fields: {sorted(unexpected_keys)}")
    for field in ("name:", "description:", "license:", "metadata:"):
        if not re.search(rf"(?m)^{re.escape(field)}", frontmatter):
            fail(errors, f"SKILL.md missing frontmatter field {field[:-1]}")
    if not re.search(r"(?m)^  compatibility:\s+\S", frontmatter):
        fail(errors, "SKILL.md metadata.compatibility is required")
    if not re.search(r"(?m)^name:\s+3d-craft\s*$", frontmatter):
        fail(errors, "Skill name must be 3d-craft")
    version = (skill / "VERSION").read_text(encoding="utf-8").strip() if (skill / "VERSION").is_file() else ""
    if not version or f'version: "{version}"' not in frontmatter:
        fail(errors, "Skill VERSION does not match metadata.version")
    openai_yaml = skill / "agents" / "openai.yaml"
    if not openai_yaml.is_file() or "$3d-craft" not in openai_yaml.read_text(encoding="utf-8"):
        fail(errors, "agents/openai.yaml missing or default prompt does not mention $3d-craft")
    required_refs = {"authority-and-evidence.md", "blender-production.md", "gltf-web-handoff.md", "web3d-runtime-qa.md", "repair-and-security.md"}
    actual_refs = {path.name for path in (skill / "references").glob("*.md")}
    if required_refs != actual_refs:
        fail(errors, f"reference set mismatch: expected={sorted(required_refs)} actual={sorted(actual_refs)}")
    schema_ids = set()
    for schema_path in sorted((skill / "schemas").glob("*.json")):
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            fail(errors, f"invalid JSON {schema_path}: {error}")
            continue
        schema_id = schema.get("$id")
        if not schema_id or schema_id in schema_ids:
            fail(errors, f"missing or duplicate $id in {schema_path}")
        schema_ids.add(schema_id)
    if len(schema_ids) != 7:
        fail(errors, f"expected seven schemas, found {len(schema_ids)}")
    for script in ("3d_craft.py", "blend_inspect.py", "render_evidence.py", "gltf_validate.mjs"):
        if not (skill / "scripts" / script).is_file():
            fail(errors, f"missing Skill script {script}")
    vendor = skill / "vendor" / "gltf-validator"
    for name, expected_hash in VENDORED_GLTF_FILES.items():
        path = vendor / name
        if not path.is_file():
            fail(errors, f"missing vendored glTF Validator runtime file: {path}")
        elif sha256(path) != expected_hash:
            fail(errors, f"vendored glTF Validator file differs from the audited bytes: {path}")
    vendor_package = vendor / "package.json"
    if vendor_package.is_file():
        package = json.loads(vendor_package.read_text(encoding="utf-8"))
        if package.get("version") != "2.0.0-dev.3.10" or package.get("license") != "Apache-2.0":
            fail(errors, "vendored glTF Validator package identity is invalid")
    viewer = skill / "assets" / "r3f-viewer"
    viewer_package_path = viewer / "package.json"
    viewer_lock_path = viewer / "package-lock.json"
    if not viewer_package_path.is_file() or not viewer_lock_path.is_file():
        fail(errors, "viewer package.json and package-lock.json are both required")
    else:
        viewer_package = json.loads(viewer_package_path.read_text(encoding="utf-8"))
        viewer_lock = json.loads(viewer_lock_path.read_text(encoding="utf-8"))
        locked_root = viewer_lock.get("packages", {}).get("", {})
        if viewer_package.get("version") != version or locked_root.get("version") != version:
            fail(errors, "viewer package and lock versions must match Skill VERSION")
        for dependency_group in ("dependencies", "devDependencies"):
            declared = viewer_package.get(dependency_group, {})
            locked = locked_root.get(dependency_group, {})
            if declared != locked:
                fail(errors, f"viewer {dependency_group} differ from the nested lockfile")
            for dependency, constraint in declared.items():
                if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?", constraint):
                    fail(errors, f"viewer dependency must use an exact version: {dependency}={constraint}")
    forbidden_generated = [
        viewer / "node_modules",
        viewer / "dist",
        viewer / "tsconfig.tsbuildinfo",
        viewer / "public" / "asset.glb",
    ]
    for path in forbidden_generated:
        if path.exists():
            fail(errors, f"generated viewer artifact must remain outside the installable Skill: {path}")
    for path in skill.rglob("*"):
        if path.is_symlink():
            fail(errors, f"installable Skill must not contain symlinks: {path}")
        if path.name == "__pycache__" or path.suffix in {".pyc", ".pyo"}:
            fail(errors, f"generated Python artifact must remain outside the installable Skill: {path}")


def validate_root(root: Path, errors: list[str]) -> None:
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    skill_version = (root / "skills" / "3d-craft" / "VERSION").read_text(encoding="utf-8").strip()
    if version != skill_version:
        fail(errors, "root VERSION and Skill VERSION differ")
    package = json.loads((root / "package.json").read_text(encoding="utf-8"))
    if package.get("version") != version:
        fail(errors, "package.json version differs from VERSION")
    if package.get("pi", {}).get("skills") != ["skills/3d-craft"]:
        fail(errors, "package.json pi.skills must expose only skills/3d-craft")
    attributes_path = root / ".gitattributes"
    attributes = set(attributes_path.read_text(encoding="utf-8").splitlines()) if attributes_path.is_file() else set()
    for path in sorted(VENDORED_GLTF_BINARY_PATHS):
        if f"{path} binary" not in attributes:
            fail(errors, f"vendored exact-byte file must be marked binary in .gitattributes: {path}")
    upstreams = json.loads((root / "upstreams.lock.json").read_text(encoding="utf-8"))
    if upstreams.get("schema") != "3d-craft.upstreams.v1":
        fail(errors, "upstreams.lock.json has an unsupported schema")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", upstreams.get("reviewed_at", "")):
        fail(errors, "upstreams.lock.json reviewed_at must be an ISO date")
    upstream_guide = root / "UPSTREAM.md"
    if not upstream_guide.is_file():
        fail(errors, "missing root upstream learning guide UPSTREAM.md")
        upstream_text = ""
    else:
        upstream_text = upstream_guide.read_text(encoding="utf-8")
    copied_upstreams = []
    seen_repos = set()
    for item in upstreams.get("upstreams", []):
        repo = item.get("repo", "")
        if not re.fullmatch(r"[^/\s]+/[^/\s]+", repo):
            fail(errors, f"invalid upstream repository name: {repo!r}")
        elif repo in seen_repos:
            fail(errors, f"duplicate upstream repository: {repo}")
        seen_repos.add(repo)
        if repo and repo not in upstream_text:
            fail(errors, f"UPSTREAM.md does not describe locked repository {repo}")
        if not re.fullmatch(r"[a-f0-9]{40}", item.get("commit", "")):
            fail(errors, f"upstream {repo} is not pinned to a full commit")
        for field in ("license", "source_paths", "absorbed_concepts", "copied_files", "local_destinations", "validation_cases"):
            value = item.get(field)
            if value in (None, "", []) and field != "copied_files":
                fail(errors, f"upstream {repo} is missing {field}")
        relationship = item.get("relationship")
        strategy = item.get("freshness", {}).get("strategy")
        if relationship == "absorbed_reference":
            if strategy != "target-path-git-blob":
                fail(errors, f"absorbed upstream {repo} must use target-path-git-blob freshness")
            if item.get("copied_files"):
                fail(errors, f"absorbed upstream {repo} must not declare copied files")
        elif relationship == "vendored_runtime":
            if strategy != "npm-package-integrity":
                fail(errors, f"vendored upstream {repo} must use npm-package-integrity freshness")
        else:
            fail(errors, f"upstream {repo} has unsupported relationship {relationship!r}")
        if item.get("copied_files"):
            copied_upstreams.append(item)
    if len(copied_upstreams) != 1 or copied_upstreams[0].get("repo") != "KhronosGroup/glTF-Validator":
        fail(errors, "only the audited Khronos glTF Validator runtime may be copied in V0.1")
    elif copied_upstreams[0].get("npm_integrity") != "sha512-odJ4k0tRkGXiDGn78yDBg+fBbAIvBnXxh3RwAta0emSxGtyagFE8B4xELB1oYe3S5RD8Ci3uZAsZaascH2LAEQ==":
        fail(errors, "Khronos glTF Validator npm integrity is missing or changed")
    for script in ("host_discovery.py", "install_local.sh", "package_skill.py", "release_gate.py", "upstream_diff.py"):
        if not (root / "scripts" / script).is_file():
            fail(errors, f"missing root release script {script}")
    for document in ("PRODUCT.md", "ARCHITECTURE.md", "MATURITY.md", "ROADMAP.md", "HOST_COMPATIBILITY.md"):
        if not (root / "docs" / document).is_file():
            fail(errors, f"missing product document {document}")
    for relative in ("README.md", "skills/3d-craft/SKILL.md"):
        automation_text = (root / relative).read_text(encoding="utf-8")
        if automation_text.count("--python-exit-code 2") < automation_text.count("blender --background"):
            fail(errors, f"Blender automation in {relative} must set --python-exit-code 2")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-root")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    skill = Path(args.skill_root).expanduser().resolve() if args.skill_root else root / "skills" / "3d-craft"
    errors: list[str] = []
    validate_skill(skill, errors)
    if not args.skill_root:
        validate_root(root, errors)
    payload = {"schema": "3d-craft.source-validation.v1", "status": "PASS" if not errors else "FAIL", "skill_root": str(skill), "errors": errors}
    print(json.dumps(payload, indent=2, sort_keys=True) if args.json else f"{payload['status']}: {len(errors)} error(s)")
    for error in errors:
        print(error, file=sys.stderr)
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
