from __future__ import annotations

# tests.support adds the canonical runtime library to sys.path before product imports.
# ruff: noqa: I001

import json
import unittest
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from tests.support import ROOT

from review_craft.schema_validation import (  # noqa: E402
    validate_instance,
    validate_schema_definition,
)


class RuntimeSchemaParityTests(unittest.TestCase):
    def assert_parity(self, schema: dict[str, Any], instances: list[Any]) -> None:
        official = Draft202012Validator(schema, format_checker=FormatChecker())
        self.assertEqual(validate_schema_definition(schema), [])
        for instance in instances:
            with self.subTest(instance=instance):
                runtime_valid = not validate_instance(instance, schema)
                official_valid = not list(official.iter_errors(instance))
                self.assertEqual(runtime_valid, official_valid)

    def test_supported_keyword_corpus_matches_draft_2020_12(self) -> None:
        corpora = (
            (
                {
                    "type": "object",
                    "required": ["name"],
                    "minProperties": 1,
                    "additionalProperties": False,
                    "properties": {
                        "name": {"type": "string", "minLength": 1, "pattern": "^[^\\x00]+$"}
                    },
                },
                [{}, {"name": "审查"}, {"name": ""}, {"name": "ok", "extra": True}],
            ),
            (
                {
                    "$defs": {
                        "value": {"type": ["integer", "null"], "minimum": 0, "maximum": 3}
                    },
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 3,
                    "items": {"$ref": "#/$defs/value"},
                },
                [[], [None], [0, 3], [-1], [4], [True], [1, 2, 3, None]],
            ),
            (
                {
                    "type": "object",
                    "additionalProperties": {"type": "string", "minLength": 1},
                },
                [{}, {"x": "ok"}, {"x": ""}, {"x": 1}],
            ),
            (
                {"enum": [1, True, "1", None], "default": None},
                [1, 1.0, True, False, "1", None],
            ),
            (
                {"const": {"enabled": True, "count": 1}},
                [
                    {"enabled": True, "count": 1},
                    {"enabled": 1, "count": True},
                    {"enabled": True, "count": 1.0},
                ],
            ),
            (
                {"type": "string", "format": "date-time"},
                [
                    "2026-08-19T08:00:00Z",
                    "2026-08-19t08:00:00z",
                    "2026-02-30T08:00:00Z",
                    "2026-08-19",
                ],
            ),
        )
        for schema, instances in corpora:
            with self.subTest(schema=schema):
                self.assert_parity(schema, instances)

    def test_packaged_schema_definitions_use_only_the_runtime_subset(self) -> None:
        schema_root = ROOT / "skills/review-craft/schemas"
        for path in sorted(schema_root.glob("*.schema.json")):
            with self.subTest(schema=path.name):
                schema = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(validate_schema_definition(schema), [])

    def test_unknown_keyword_in_unused_definition_fails_eagerly(self) -> None:
        schema = {
            "type": "object",
            "$defs": {"unused": {"type": "string", "oneOf": [{"const": "x"}]}},
        }
        errors = validate_schema_definition(schema)
        self.assertTrue(any("unsupported schema keywords oneOf" in error for error in errors))

    def test_invalid_and_cyclic_internal_references_fail_eagerly(self) -> None:
        missing = {"$defs": {"value": {"type": "string"}}, "$ref": "#/$defs/missing"}
        self.assertTrue(
            any(
                "unresolved schema reference" in error
                for error in validate_schema_definition(missing)
            )
        )

        cyclic = {
            "$defs": {
                "node": {
                    "type": "object",
                    "properties": {"child": {"$ref": "#/$defs/node"}},
                }
            },
            "$ref": "#/$defs/node",
        }
        self.assertTrue(
            any(
                "cyclic schema reference" in error
                for error in validate_schema_definition(cyclic)
            )
        )

    def test_deep_nested_and_large_array_inputs_remain_deterministic(self) -> None:
        schema: dict[str, Any] = {"type": "integer", "minimum": 0}
        instance: Any = 1
        for _ in range(40):
            schema = {"type": "array", "minItems": 1, "maxItems": 1, "items": schema}
            instance = [instance]
        self.assert_parity(schema, [instance])
        self.assert_parity(
            {"type": "array", "maxItems": 1000, "items": {"type": "integer"}},
            [list(range(1000)), [*range(1000), "invalid"]],
        )


if __name__ == "__main__":
    unittest.main()
