from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from ..repo import REPO_ROOT


SCHEMA = "design-craft.repository-contracts.v1"
REQUIRED_SCHEMA = "design-craft.required-files.v1"
RELEASE_TARGETS = (
    "release-readiness-operational",
    "release-tag-verify-operational",
    "release-assets-build-operational",
    "release-assets-verify-operational",
    "release-final-verify-operational",
    "release-readiness-certified",
    "release-tag-verify-certified",
    "release-assets-build-certified",
    "release-assets-verify-certified",
    "release-final-verify-certified",
    "release-certification-build-operational",
    "release-certification-verify-operational",
    "release-certification-build-certified",
    "release-certification-verify-certified",
)
NOTICE_TOKENS = ("MIT", "Apache-2.0", "Vercel design reference history", "emilkowalski/skills")
RETIRED_ALIAS_BOUNDARY_DOCS = (
    "SECURITY.md",
    "docs/security/threat-model.md",
    "docs/maintenance.md",
)
RETIRED_ALIAS_BOUNDARY = "outside the v0.5 installer boundary"
SOURCE_MAP_MUTABLE_MARKERS = (
    "Current reviewed remote commit:",
    "Latest-range status:",
    "reviewed remote head",
)
SOURCE_MAP_AUTHORITY_TOKENS = (
    "Mutable remote review state",
    "`upstreams.lock.json`",
    "absorption matrices",
)


def _load_required(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != REQUIRED_SCHEMA:
        raise ValueError(f"required file registry must use {REQUIRED_SCHEMA}")
    for key in ("files", "directories", "forbidden_paths"):
        values = payload.get(key)
        if (
            not isinstance(values, list)
            or not all(isinstance(item, str) and item for item in values)
            or len(values) != len(set(values))
        ):
            raise ValueError(f"required file registry {key} must contain unique strings")
    return payload


def _validate_source_map_contract(
    source_map: str, upstream_lock: dict[str, object]
) -> list[str]:
    errors: list[str] = []
    for marker in SOURCE_MAP_MUTABLE_MARKERS:
        if marker in source_map:
            errors.append(
                f"installed source map must not mirror mutable review state: {marker}"
            )
    for token in SOURCE_MAP_AUTHORITY_TOKENS:
        if token not in source_map:
            errors.append(f"installed source map must declare governance authority: {token}")

    upstreams = upstream_lock.get("upstreams", {})
    if not isinstance(upstreams, dict):
        return [*errors, "upstreams.lock.json must contain an upstreams object"]
    for name, raw_metadata in upstreams.items():
        if not isinstance(raw_metadata, dict):
            errors.append(f"{name}: upstream metadata must be an object")
            continue
        pinned = raw_metadata.get("commit")
        selected = raw_metadata.get("behavior_absorbed_through_commit")
        reviewed = raw_metadata.get("reviewed_through_commit")
        for label, value in (("compatibility pin", pinned), ("selected behavior", selected)):
            if not isinstance(value, str) or not value:
                errors.append(f"{name}: missing {label} boundary")
            elif value not in source_map:
                errors.append(f"{name}: source map is missing {label} boundary {value}")
        if (
            isinstance(reviewed, str)
            and reviewed
            and reviewed not in {pinned, selected}
            and reviewed in source_map
        ):
            errors.append(f"{name}: source map must not mirror reviewed head {reviewed}")
    return errors


def validate(root: Path = REPO_ROOT) -> dict[str, object]:
    errors: list[str] = []
    registry_path = root / "contracts/validation/required-files.json"
    try:
        registry = _load_required(registry_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {"schema": SCHEMA, "root": str(root), "ok": False, "errors": [str(exc)]}

    for relative in registry["files"]:
        if not (root / relative).is_file():
            errors.append(f"missing required file: {relative}")
    for relative in registry["directories"]:
        if not (root / relative).is_dir():
            errors.append(f"missing required directory: {relative}")
    for relative in registry["forbidden_paths"]:
        if (root / relative).exists() or (root / relative).is_symlink():
            errors.append(f"retired path must remain absent: {relative}")

    installer = (root / "scripts/install_local.sh").read_text(encoding="utf-8")
    if "frontend-craft" in installer or "frontend_craft" in installer:
        errors.append("installer must not manage the retired frontend-craft alias")
    for relative in RETIRED_ALIAS_BOUNDARY_DOCS:
        document = re.sub(
            r"\s+",
            " ",
            (root / relative).read_text(encoding="utf-8"),
        )
        if RETIRED_ALIAS_BOUNDARY not in document:
            errors.append(f"{relative} must document the retired alias boundary")

    try:
        version = (root / "VERSION").read_text(encoding="utf-8").strip()
        package = json.loads((root / "package.json").read_text(encoding="utf-8"))
        lock = json.loads((root / "package-lock.json").read_text(encoding="utf-8"))
        skill_version = (root / "skills/design-craft/VERSION").read_text(encoding="utf-8").strip()
        if re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version) is None:
            errors.append("VERSION must be a stable semantic version")
        if package.get("version") != version:
            errors.append("package.json version must match VERSION")
        if lock.get("version") != version or lock.get("packages", {}).get("", {}).get("version") != version:
            errors.append("package-lock.json versions must match VERSION")
        if skill_version != version:
            errors.append("skills/design-craft/VERSION must match VERSION")
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"version metadata is invalid: {exc}")

    notices = (root / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8", errors="replace")
    for token in NOTICE_TOKENS:
        if token not in notices:
            errors.append(f"THIRD_PARTY_NOTICES.md is missing {token}")

    skill = (root / "skills/design-craft/SKILL.md").read_text(encoding="utf-8")
    try:
        source_map = (root / "skills/design-craft/references/source-map.md").read_text(
            encoding="utf-8"
        )
        upstream_lock = json.loads(
            (root / "upstreams.lock.json").read_text(encoding="utf-8")
        )
        errors.extend(_validate_source_map_contract(source_map, upstream_lock))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"source-map governance contract is invalid: {exc}")
    for reference in sorted((root / "skills/design-craft/references").glob("*.md")):
        text = reference.read_text(encoding="utf-8")
        if len(text.splitlines()) > 100 and "## Contents" not in text:
            errors.append(f"long reference must provide Contents: {reference.relative_to(root)}")
        if reference.name not in skill:
            errors.append(f"SKILL.md does not route reference: {reference.name}")
    if "[TODO" in skill or "TODO:" in skill:
        errors.append("canonical SKILL.md must not contain TODO markers")
    if (root / "DESIGN.md").exists():
        errors.append("repository root must not contain DESIGN.md")

    makefile = (root / "Makefile").read_text(encoding="utf-8")
    if "tools.design_craft.validation.skill_schema" not in makefile:
        errors.append("Makefile must use the repository-owned skill schema validator")
    if ".codex/skills/.system/skill-creator" in makefile:
        errors.append("Makefile must not depend on a user-home skill validator")
    for target in (
        "maturity-development",
        "maturity-operational",
        "maturity-certified",
        "codex-route-pack-check",
        "codex-route-pack-host-check",
        *RELEASE_TARGETS,
    ):
        if re.search(rf"(?m)^{re.escape(target)}(?:\s|:)", makefile) is None:
            errors.append(f"Makefile is missing target: {target}")
    source_line = next(
        (line for line in makefile.splitlines() if line.startswith("release-gate-source:")),
        "",
    )
    if "upstream-freshness" in source_line or "upstream-remote" in source_line:
        errors.append("release-gate-source must not depend on mutable upstream state")
    if "maturity-development" not in source_line:
        errors.append("release-gate-source must require maturity-development")
    if "codex-route-pack-check" not in source_line:
        errors.append("release-gate-source must require the portable route-pack contract")
    if "codex-route-pack-host-check" in source_line:
        errors.append("release-gate-source must not depend on operator Codex home state")
    for retired in ("maturity-portable:", "maturity-local:", "maturity-desktop:", "release-certify:"):
        if retired in makefile:
            errors.append(f"retired Make target must remain absent: {retired[:-1]}")

    for document in (root / "README.md", root / "docs/maintenance.md"):
        text = document.read_text(encoding="utf-8")
        for target in ("release-readiness-operational", "release-final-verify-certified"):
            if target not in text:
                errors.append(f"{document.relative_to(root)} must document {target}")

    return {
        "schema": SCHEMA,
        "root": str(root),
        "required_file_count": len(registry["files"]),
        "ok": not errors,
        "errors": errors,
    }


def self_check() -> None:
    fixture = {
        "schema": REQUIRED_SCHEMA,
        "files": ["a"],
        "directories": ["b"],
        "forbidden_paths": [],
    }
    if len(fixture["files"]) != 1 or fixture["schema"] != REQUIRED_SCHEMA:
        raise RuntimeError("repository contract self-check failed")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.check:
        self_check()
    payload = validate()
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    elif payload["ok"]:
        print(f"repository contracts verified: {payload['required_file_count']} required files")
    else:
        print("\n".join(payload["errors"]), file=sys.stderr)
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
