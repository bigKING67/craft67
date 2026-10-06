from __future__ import annotations

import re
from datetime import datetime
from typing import Any

SUPPORTED_KEYWORDS = {
    "$schema",
    "$id",
    "$defs",
    "$ref",
    "title",
    "description",
    "default",
    "type",
    "const",
    "enum",
    "required",
    "properties",
    "additionalProperties",
    "minProperties",
    "minLength",
    "pattern",
    "format",
    "minimum",
    "maximum",
    "minItems",
    "maxItems",
    "items",
}
SUPPORTED_TYPES = {"object", "array", "string", "integer", "number", "boolean", "null"}
NONNEGATIVE_INTEGER_KEYWORDS = {"minProperties", "minLength", "minItems", "maxItems"}
STRING_KEYWORDS = {"$schema", "$id", "title", "description"}


def _resolve_pointer(root_schema: dict[str, Any], reference: str) -> dict[str, Any]:
    if not isinstance(reference, str) or not reference.startswith("#/"):
        raise ValueError(f"unsupported schema reference: {reference}")
    value: Any = root_schema
    for raw_part in reference[2:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if not isinstance(value, dict) or part not in value:
            raise ValueError(f"unresolved schema reference: {reference}")
        value = value[part]
    if not isinstance(value, dict):
        raise ValueError(f"schema reference is not an object: {reference}")
    return value


def _scalar_definition_errors(schema: dict[str, Any], path: str) -> list[str]:
    errors: list[str] = []
    for keyword in STRING_KEYWORDS:
        if keyword in schema and not isinstance(schema[keyword], str):
            errors.append(f"{path}.{keyword}: expected a string")
    for keyword in NONNEGATIVE_INTEGER_KEYWORDS:
        value = schema.get(keyword)
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or value < 0
        ):
            errors.append(f"{path}.{keyword}: expected a non-negative integer")
    for keyword in ("minimum", "maximum"):
        value = schema.get(keyword)
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, (int, float))
        ):
            errors.append(f"{path}.{keyword}: expected a number")
    return errors


def _collection_definition_errors(schema: dict[str, Any], path: str) -> list[str]:
    errors: list[str] = []
    expected_type = schema.get("type")
    if expected_type is not None:
        values = [expected_type] if isinstance(expected_type, str) else expected_type
        if (
            not isinstance(values, list)
            or not values
            or any(not isinstance(value, str) or value not in SUPPORTED_TYPES for value in values)
            or len(values) != len(set(values))
        ):
            errors.append(f"{path}.type: invalid or unsupported type declaration")
    enum = schema.get("enum")
    if enum is not None and (not isinstance(enum, list) or not enum):
        errors.append(f"{path}.enum: expected a non-empty array")
    required = schema.get("required")
    if required is not None and (
        not isinstance(required, list)
        or any(not isinstance(item, str) for item in required)
        or len(required) != len(set(required))
    ):
        errors.append(f"{path}.required: expected unique string names")
    additional = schema.get("additionalProperties")
    if additional is not None and not isinstance(additional, (bool, dict)):
        errors.append(f"{path}.additionalProperties: expected a boolean or schema")
    if (
        isinstance(schema.get("minItems"), int)
        and isinstance(schema.get("maxItems"), int)
        and schema["minItems"] > schema["maxItems"]
    ):
        errors.append(f"{path}: minItems cannot exceed maxItems")
    return errors


def _pattern_definition_errors(schema: dict[str, Any], path: str) -> list[str]:
    errors: list[str] = []
    pattern = schema.get("pattern")
    if pattern is not None:
        if not isinstance(pattern, str):
            errors.append(f"{path}.pattern: expected a string")
        else:
            try:
                re.compile(pattern)
            except re.error as error:
                errors.append(f"{path}.pattern: invalid regular expression: {error}")
    value_format = schema.get("format")
    if value_format not in {None, "date-time"}:
        errors.append(f"{path}.format: unsupported schema format {value_format!r}")
    return errors


def _definition_value_errors(schema: dict[str, Any], path: str) -> list[str]:
    return [
        *_scalar_definition_errors(schema, path),
        *_collection_definition_errors(schema, path),
        *_pattern_definition_errors(schema, path),
    ]


def _definition_children(schema: dict[str, Any], path: str) -> list[tuple[dict[str, Any], str]]:
    children: list[tuple[dict[str, Any], str]] = []
    for keyword in ("$defs", "properties"):
        mapping = schema.get(keyword)
        if mapping is None:
            continue
        if not isinstance(mapping, dict):
            continue
        for name, child in mapping.items():
            child_path = f"{path}.{keyword}.{name}"
            if isinstance(child, dict):
                children.append((child, child_path))
    items = schema.get("items")
    if isinstance(items, dict):
        children.append((items, f"{path}.items"))
    additional = schema.get("additionalProperties")
    if isinstance(additional, dict):
        children.append((additional, f"{path}.additionalProperties"))
    return children


def _validate_definition_node(
    schema: dict[str, Any],
    *,
    root_schema: dict[str, Any],
    path: str,
    active_refs: frozenset[int],
    visited: set[int],
) -> list[str]:
    if id(schema) in visited and id(schema) not in active_refs:
        return []
    visited.add(id(schema))
    errors: list[str] = []
    unknown = sorted(set(schema) - SUPPORTED_KEYWORDS)
    if unknown:
        errors.append(f"{path}: unsupported schema keywords {', '.join(unknown)}")
    errors.extend(_definition_value_errors(schema, path))
    for keyword in ("$defs", "properties"):
        value = schema.get(keyword)
        if value is not None and (
            not isinstance(value, dict)
            or any(not isinstance(child, dict) for child in value.values())
        ):
            errors.append(f"{path}.{keyword}: expected an object of schemas")
    if "items" in schema and not isinstance(schema["items"], dict):
        errors.append(f"{path}.items: expected a schema object")
    reference = schema.get("$ref")
    if reference is not None:
        try:
            target = _resolve_pointer(root_schema, reference)
        except ValueError as error:
            errors.append(f"{path}: {error}")
        else:
            if id(target) in active_refs or target is schema:
                errors.append(f"{path}: cyclic schema reference is unsupported: {reference}")
            else:
                errors.extend(
                    _validate_definition_node(
                        target,
                        root_schema=root_schema,
                        path=f"{path}.$ref",
                        active_refs=active_refs | {id(schema)},
                        visited=visited,
                    )
                )
    for child, child_path in _definition_children(schema, path):
        errors.extend(
            _validate_definition_node(
                child,
                root_schema=root_schema,
                path=child_path,
                active_refs=active_refs | {id(schema)},
                visited=visited,
            )
        )
    return errors


def validate_schema_definition(schema: Any) -> list[str]:
    if not isinstance(schema, dict):
        return ["$: schema must be an object"]
    return _validate_definition_node(
        schema,
        root_schema=schema,
        path="$",
        active_refs=frozenset(),
        visited=set(),
    )


def _matches_type(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    raise ValueError(f"unsupported schema type: {expected}")


def _json_equal(left: Any, right: Any) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return isinstance(left, bool) and isinstance(right, bool) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            _json_equal(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=True)
        )
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(
            _json_equal(left[key], right[key]) for key in left
        )
    return type(left) is type(right) and left == right


def _valid_datetime(value: str) -> bool:
    if re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}[Tt][0-9]{2}:[0-9]{2}:[0-9]{2}"
        r"(?:\.[0-9]+)?(?:[Zz]|[+-][0-9]{2}:[0-9]{2})",
        value,
    ) is None:
        return False
    normalized = value[:10] + "T" + value[11:]
    if normalized.endswith(("Z", "z")):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _type_errors(instance: Any, schema: dict[str, Any], path: str) -> list[str]:
    expected_type = schema.get("type")
    if expected_type is None:
        return []
    expected_types = [expected_type] if isinstance(expected_type, str) else expected_type
    if any(_matches_type(instance, item) for item in expected_types):
        return []
    return [f"{path}: expected type {' or '.join(expected_types)}"]


def _object_errors(
    instance: dict[str, Any],
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    path: str,
) -> list[str]:
    errors = [
        f"{path}.{key}: required property is missing"
        for key in schema.get("required", [])
        if key not in instance
    ]
    minimum = schema.get("minProperties")
    if minimum is not None and len(instance) < minimum:
        errors.append(f"{path}: expected at least {minimum} properties")
    properties = schema.get("properties", {})
    additional = schema.get("additionalProperties", True)
    for key in sorted(instance):
        child_path = f"{path}.{key}"
        if key in properties:
            errors.extend(
                _validate_instance(instance[key], properties[key], root_schema, child_path)
            )
        elif additional is False:
            errors.append(f"{child_path}: additional property is not allowed")
        elif isinstance(additional, dict):
            errors.extend(_validate_instance(instance[key], additional, root_schema, child_path))
    return errors


def _array_errors(
    instance: list[Any],
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    path: str,
) -> list[str]:
    errors: list[str] = []
    minimum = schema.get("minItems")
    maximum = schema.get("maxItems")
    if minimum is not None and len(instance) < minimum:
        errors.append(f"{path}: expected at least {minimum} items")
    if maximum is not None and len(instance) > maximum:
        errors.append(f"{path}: expected at most {maximum} items")
    item_schema = schema.get("items")
    if isinstance(item_schema, dict):
        for index, value in enumerate(instance):
            errors.extend(_validate_instance(value, item_schema, root_schema, f"{path}[{index}]"))
    return errors


def _string_errors(instance: str, schema: dict[str, Any], path: str) -> list[str]:
    errors: list[str] = []
    minimum = schema.get("minLength")
    if minimum is not None and len(instance) < minimum:
        errors.append(f"{path}: expected at least {minimum} characters")
    pattern = schema.get("pattern")
    if pattern is not None and re.search(pattern, instance) is None:
        errors.append(f"{path}: does not match pattern {pattern!r}")
    if schema.get("format") == "date-time" and not _valid_datetime(instance):
        errors.append(f"{path}: expected an RFC 3339 date-time")
    return errors


def _number_errors(instance: int | float, schema: dict[str, Any], path: str) -> list[str]:
    errors: list[str] = []
    minimum = schema.get("minimum")
    maximum = schema.get("maximum")
    if minimum is not None and instance < minimum:
        errors.append(f"{path}: expected a value >= {minimum}")
    if maximum is not None and instance > maximum:
        errors.append(f"{path}: expected a value <= {maximum}")
    return errors


def _validate_instance(
    instance: Any,
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    path: str,
) -> list[str]:
    reference = schema.get("$ref")
    if reference is not None:
        target = _resolve_pointer(root_schema, reference)
        reference_errors = _validate_instance(instance, target, root_schema, path)
    else:
        reference_errors = []
    local_schema = {key: value for key, value in schema.items() if key != "$ref"}
    type_errors = _type_errors(instance, local_schema, path)
    if type_errors:
        return [*reference_errors, *type_errors]
    errors = list(reference_errors)
    if "const" in local_schema and not _json_equal(instance, local_schema["const"]):
        errors.append(f"{path}: expected constant {local_schema['const']!r}")
    if "enum" in local_schema and not any(
        _json_equal(instance, option) for option in local_schema["enum"]
    ):
        errors.append(f"{path}: expected one of {local_schema['enum']!r}")
    if isinstance(instance, dict):
        errors.extend(_object_errors(instance, local_schema, root_schema, path))
    if isinstance(instance, list):
        errors.extend(_array_errors(instance, local_schema, root_schema, path))
    if isinstance(instance, str):
        errors.extend(_string_errors(instance, local_schema, path))
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        errors.extend(_number_errors(instance, local_schema, path))
    return errors


def validate_instance(
    instance: Any,
    schema: dict[str, Any],
    *,
    root_schema: dict[str, Any] | None = None,
    path: str = "$",
) -> list[str]:
    if root_schema is None:
        definition_errors = validate_schema_definition(schema)
        if definition_errors:
            return definition_errors
        root_schema = schema
    return _validate_instance(instance, schema, root_schema, path)
