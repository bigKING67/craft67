#!/usr/bin/env python3
from __future__ import annotations

import json
import py_compile
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "reverse-craft"
LIB = SKILL / "lib"
sys.path.insert(0, str(LIB))

from reverse_craft import __version__  # noqa: E402
from reverse_craft.case_validation import (  # noqa: E402
    CASE_ALLOWED_FIELDS,
    CASE_REQUIRED_FIELDS,
    COLLECTION_REQUIRED_FIELDS,
    EVIDENCE_REQUIRED_FIELDS,
    EVENT_DATA_FIELDS,
    EVENT_REQUIRED_FIELDS,
    EVENT_TYPES,
    FINDING_REQUIRED_FIELDS,
    MANIFEST_FILE_REQUIRED_FIELDS,
    PATH_REQUIRED_FIELDS,
    ROUTE_IDS,
    SEAL_REQUIRED_FIELDS,
)
from reverse_craft.provenance import audit_references  # noqa: E402

REQUIRED = (
    ".github/workflows/ci.yml", ".gitignore", "AGENTS.md", "LICENSE",
    "README.md", "THIRD_PARTY_NOTICES.md", "VERSION", "package.json", "pyproject.toml",
    "skills/reverse-craft/.npmignore", "skills/reverse-craft/SKILL.md", "skills/reverse-craft/VERSION",
    "skills/reverse-craft/agents/openai.yaml", "skills/reverse-craft/scripts/reverse_craft.py",
    "skills/reverse-craft/lib/reverse_craft/case_validation.py",
    "skills/reverse-craft/references/modules.json", "skills/reverse-craft/references/provenance.json",
    "skills/reverse-craft/references/upstream/reverse-skill-routing.json",
    "scripts/run_route_bank.py", "scripts/run_scenario_bank.py", "scripts/run_host_eval.py",
    "scripts/check_browser67_mcp.py",
)
SCHEMAS = (
    "route", "case", "evidence", "finding", "path", "report", "event", "seal",
)
FORBIDDEN_PARTS = {"__pycache__", ".pytest_cache", ".ruff_cache", ".venv", "node_modules", "test-results"}


def source_files() -> list[Path]:
    completed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT, capture_output=True, check=True,
    )
    return sorted(ROOT / raw.decode("utf-8") for raw in completed.stdout.split(b"\0") if raw and (ROOT / raw.decode("utf-8")).is_file())


def main() -> int:
    errors: list[str] = []
    files = source_files()
    relative = {path.relative_to(ROOT).as_posix() for path in files}
    for required in REQUIRED:
        if required not in relative:
            errors.append(f"missing required file: {required}")
    for name in SCHEMAS:
        path = f"skills/reverse-craft/schemas/{name}.schema.json"
        if path not in relative:
            errors.append(f"missing schema: {path}")
    schema_contracts = {
        "case": (CASE_REQUIRED_FIELDS, CASE_ALLOWED_FIELDS),
        "evidence": (COLLECTION_REQUIRED_FIELDS, EVIDENCE_REQUIRED_FIELDS),
        "finding": (COLLECTION_REQUIRED_FIELDS, FINDING_REQUIRED_FIELDS),
        "path": (COLLECTION_REQUIRED_FIELDS, PATH_REQUIRED_FIELDS),
    }
    for name, (document_fields, item_fields) in schema_contracts.items():
        schema = json.loads((SKILL / f"schemas/{name}.schema.json").read_text(encoding="utf-8"))
        if set(schema.get("required", [])) != document_fields or set(schema.get("properties", {})) != (
            CASE_ALLOWED_FIELDS if name == "case" else COLLECTION_REQUIRED_FIELDS
        ):
            errors.append(f"{name} schema document fields drifted from the runtime validator")
        if name != "case":
            item_schema = schema.get("properties", {}).get("items", {}).get("items", {})
            if (
                set(item_schema.get("required", [])) != item_fields or
                set(item_schema.get("properties", {})) != item_fields
            ):
                errors.append(f"{name} schema item fields drifted from the runtime validator")
    event_schema = json.loads((SKILL / "schemas/event.schema.json").read_text(encoding="utf-8"))
    if (
        set(event_schema.get("required", [])) != EVENT_REQUIRED_FIELDS or
        set(event_schema.get("properties", {})) != EVENT_REQUIRED_FIELDS or
        set(event_schema.get("properties", {}).get("type", {}).get("enum", [])) != EVENT_TYPES
    ):
        errors.append("event schema fields or types drifted from the runtime validator")
    all_of = event_schema.get("allOf", [])
    branches = (
        all_of[0].get("oneOf", [])
        if len(all_of) == 1 and isinstance(all_of[0], dict)
        else []
    )
    definitions = event_schema.get("$defs", {})
    event_data_contracts: dict[str, tuple[set[str], set[str]]] = {}
    for branch in branches:
        properties = branch.get("properties", {}) if isinstance(branch, dict) else {}
        event_type = properties.get("type", {}).get("const")
        reference = properties.get("data", {}).get("$ref", "")
        definition = definitions.get(reference.removeprefix("#/$defs/"), {})
        if isinstance(event_type, str) and isinstance(definition, dict):
            event_data_contracts[event_type] = (
                set(definition.get("required", [])), set(definition.get("properties", {})),
            )
    expected_event_data = {
        name: (fields, fields) for name, fields in EVENT_DATA_FIELDS.items()
    }
    if event_data_contracts != expected_event_data:
        errors.append("event data schemas drifted from the runtime validator")
    seal_schema = json.loads(
        (SKILL / "schemas/seal.schema.json").read_text(encoding="utf-8")
    )
    seal_properties = seal_schema.get("properties", {})
    seal_file_schema = seal_properties.get("files", {}).get("items", {})
    if (
        set(seal_schema.get("required", [])) != SEAL_REQUIRED_FIELDS or
        set(seal_properties) != SEAL_REQUIRED_FIELDS or
        set(seal_file_schema.get("required", [])) != MANIFEST_FILE_REQUIRED_FIELDS or
        set(seal_file_schema.get("properties", {})) != MANIFEST_FILE_REQUIRED_FIELDS
    ):
        errors.append("seal schema fields drifted from the runtime validator")
    skills = sorted(path for path in files if path.name == "SKILL.md")
    if skills != [SKILL / "SKILL.md"]:
        errors.append(f"expected exactly one SKILL.md, found: {[str(path.relative_to(ROOT)) for path in skills]}")
    project_version_match = re.search(
        r'^version = "([^"]+)"$',
        (ROOT / "pyproject.toml").read_text(encoding="utf-8"),
        flags=re.MULTILINE,
    )
    versions = {
        "root": (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
        "skill": (SKILL / "VERSION").read_text(encoding="utf-8").strip(),
        "package": json.loads((ROOT / "package.json").read_text(encoding="utf-8"))["version"],
        "project": project_version_match.group(1) if project_version_match else None,
        "runtime": __version__,
    }
    if len(set(versions.values())) != 1:
        errors.append(f"version mismatch: {versions}")
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    if package.get("private") is not True or package.get("pi", {}).get("skills") != ["skills/reverse-craft"]:
        errors.append("package must remain private and expose exactly one Pi skill")
    skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    if not skill_text.startswith("---\nname: reverse-craft\ndescription:"):
        errors.append("SKILL.md frontmatter is missing required name/description")
    for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", skill_text):
        if "://" not in link and not link.startswith("#") and not (SKILL / link).resolve().is_file():
            errors.append(f"broken SKILL.md link: {link}")
    upstream = json.loads((SKILL / "references/upstream/reverse-skill-routing.json").read_text(encoding="utf-8"))
    modules = json.loads((SKILL / "references/modules.json").read_text(encoding="utf-8"))
    expected_ids = ROUTE_IDS
    if set(upstream.get("routes", {})) != expected_ids or set(upstream.get("priority", [])) != expected_ids:
        errors.append("routing source must contain exactly the registered route IDs")
    if set(modules.get("routes", {})) != expected_ids:
        errors.append("module map must contain exactly the registered route IDs")
    route_bank = json.loads((ROOT / "tests/fixtures/route_seeds.json").read_text(encoding="utf-8"))
    if set(route_bank.get("routes", {})) != expected_ids:
        errors.append("route bank must contain exactly the registered route IDs")
    for route_id, mapping in modules.get("routes", {}).items():
        reference = SKILL / "references" / mapping["reference"]
        if not reference.is_file():
            errors.append(f"route {route_id} has missing reference: {mapping['reference']}")
    for path in files:
        if path.suffix == ".json":
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                errors.append(f"invalid JSON {path.relative_to(ROOT)}: {exc}")
        if any(part in FORBIDDEN_PARTS for part in path.parts):
            errors.append(f"forbidden generated path: {path.relative_to(ROOT)}")
    unfinished_tokens = ("TO" + "DO", "FIX" + "ME", "T" + "BD", "PLACE" + "HOLDER")
    searchable = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in files
        if path != Path(__file__).resolve() and path.suffix in {".md", ".py", ".json", ".yaml", ".yml"}
    )
    if any(re.search(rf"\b{token}\b", searchable) for token in unfinished_tokens):
        errors.append("unfinished scaffold marker found")
    if "shell=True" in (SKILL / "lib/reverse_craft/setup_ops.py").read_text(encoding="utf-8"):
        errors.append("setup runtime must not use shell=True")
    for path in sorted((SKILL / "lib").rglob("*.py")) + sorted((SKILL / "scripts").glob("*.py")):
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(f"compile failed {path.relative_to(ROOT)}: {exc}")
    audit = audit_references()
    if not audit["valid"]:
        errors.append("provenance audit failed")
    result = {
        "schema": "reverse-craft.source-validation.v1",
        "valid": not errors,
        "version": versions["root"],
        "files": len(files),
        "routes": len(upstream["routes"]),
        "schemas": len(SCHEMAS),
        "scenarios": len(list((ROOT / "tests" / "scenarios").glob("*.json"))),
        "route_cases": sum(len(items) for items in route_bank["routes"].values()),
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
