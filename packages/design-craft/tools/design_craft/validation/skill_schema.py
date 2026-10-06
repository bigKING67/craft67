from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from ..repo import REPO_ROOT


SCHEMA = "design-craft.skill-schema-verification.v1"
MAX_SKILL_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
FRONTMATTER_PATTERN = re.compile(
    r"\A---\r?\n(?P<body>.*?)\r?\n---(?:\r?\n|\Z)",
    re.DOTALL,
)
STRING_FIELDS = {"name", "description"}
YAML_NON_STRING_SCALARS = {
    "false",
    "null",
    "true",
    "~",
}


def _parse_string_scalar(raw: str, field: str) -> str:
    value = raw.strip()
    if not value:
        raise ValueError(f"{field} must be a non-empty string")
    if value.startswith('"'):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{field} has invalid double-quoted syntax: {exc}") from exc
        if not isinstance(parsed, str):
            raise ValueError(f"{field} must be a string")
        parsed = parsed.strip()
        if not parsed:
            raise ValueError(f"{field} must be a non-empty string")
        return parsed
    if value.startswith("'"):
        if len(value) < 2 or not value.endswith("'"):
            raise ValueError(f"{field} has invalid single-quoted syntax")
        parsed = value[1:-1].replace("''", "'").strip()
        if not parsed:
            raise ValueError(f"{field} must be a non-empty string")
        return parsed
    if value.endswith(("'", '"')):
        raise ValueError(f"{field} has an unmatched quote")
    if value.lower() in YAML_NON_STRING_SCALARS or re.fullmatch(
        r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)",
        value,
    ):
        raise ValueError(f"{field} must be a string")
    if value.startswith(("[", "{", "|", ">", "&", "*", "!")):
        raise ValueError(f"{field} must use a single-line string scalar")
    return value


def _parse_frontmatter(text: str) -> dict[str, str]:
    match = FRONTMATTER_PATTERN.match(text)
    if match is None:
        raise ValueError("SKILL.md must start with a closed YAML frontmatter block")

    values: dict[str, str] = {}
    for line_number, line in enumerate(match.group("body").splitlines(), start=2):
        if not line.strip():
            continue
        if line[:1].isspace() or ":" not in line:
            raise ValueError(
                f"SKILL.md frontmatter line {line_number} must be a top-level key/value pair"
            )
        key, raw_value = line.split(":", 1)
        key = key.strip()
        if key not in STRING_FIELDS:
            raise ValueError(f"unsupported SKILL.md frontmatter field: {key or '<empty>'}")
        if key in values:
            raise ValueError(f"duplicate SKILL.md frontmatter field: {key}")
        values[key] = _parse_string_scalar(raw_value, key)

    missing = sorted(STRING_FIELDS - set(values))
    if missing:
        raise ValueError("missing SKILL.md frontmatter fields: " + ", ".join(missing))
    return values


def validate_skill(skill_root: Path) -> dict[str, object]:
    root = skill_root.expanduser().resolve()
    errors: list[str] = []
    skill_path = root / "SKILL.md"
    try:
        frontmatter = _parse_frontmatter(skill_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        frontmatter = {}
        errors.append(str(exc))

    name = frontmatter.get("name", "")
    description = frontmatter.get("description", "")
    if name:
        if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) is None:
            errors.append("name must use lowercase hyphen-case without repeated hyphens")
        if len(name) > MAX_SKILL_NAME_LENGTH:
            errors.append(f"name must be at most {MAX_SKILL_NAME_LENGTH} characters")
        if name != root.name:
            errors.append("name must match the canonical skill directory")
    if description:
        if "<" in description or ">" in description:
            errors.append("description must not contain angle brackets")
        if len(description) > MAX_DESCRIPTION_LENGTH:
            errors.append(
                f"description must be at most {MAX_DESCRIPTION_LENGTH} characters"
            )

    return {
        "schema": SCHEMA,
        "root": str(root),
        "name": name or None,
        "ok": not errors,
        "errors": errors,
    }


def self_check() -> None:
    valid = _parse_frontmatter('---\nname: design-craft\ndescription: "Valid."\n---\n')
    if valid != {"name": "design-craft", "description": "Valid."}:
        raise RuntimeError("skill schema parser self-check failed")
    try:
        _parse_frontmatter("---\nname: design-craft\nunexpected: value\n---\n")
    except ValueError:
        return
    raise RuntimeError("skill schema parser accepted an unsupported field")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "skill_directory",
        nargs="?",
        default=str(REPO_ROOT / "skills/design-craft"),
    )
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.check:
        self_check()
    payload = validate_skill(Path(args.skill_directory))
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    elif payload["ok"]:
        print(f"skill schema verified: {payload['name']}")
    else:
        print("\n".join(str(item) for item in payload["errors"]))
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
