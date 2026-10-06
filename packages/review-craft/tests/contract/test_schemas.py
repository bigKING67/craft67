from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from tests.support import ROOT, create_run, make_target, populate_valid_run, run_cli


class SchemaTests(unittest.TestCase):
    def test_declarative_policy_fields_disclose_their_enforcement_boundary(self) -> None:
        schema_path = ROOT / "skills/review-craft/schemas/config.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        policy = schema["properties"]["policy"]["properties"]
        for field in ("allowNetwork", "allowInstall"):
            description = policy[field].get("description", "")
            self.assertIn("declarative", description)
            self.assertIn("does not enforce", description)

    def test_final_artifacts_match_public_schemas(self) -> None:
        target_tmp, target = make_target()
        self.addCleanup(target_tmp.cleanup)
        with tempfile.TemporaryDirectory() as output:
            run_dir = create_run(target, Path(output))
            populate_valid_run(run_dir)
            finalized = run_cli("finalize", "--run-dir", str(run_dir))
            self.assertEqual(finalized.returncode, 0, finalized.stderr)
            pairs = (
                ("review-manifest.json", "review-manifest.schema.json"),
                ("review-scope.json", "review-scope.schema.json"),
                ("quality-model.json", "quality-model.schema.json"),
                ("coverage.json", "coverage.schema.json"),
                ("module-map.json", "module-map.schema.json"),
                ("dependency-map.json", "dependency-map.schema.json"),
                ("findings.json", "findings.schema.json"),
                ("decisions.json", "decisions.schema.json"),
                ("scorecard.json", "scorecard.schema.json"),
                ("remediation-plan.json", "remediation-plan.schema.json"),
                ("evidence-registry.json", "evidence-registry.schema.json"),
            )
            schema_root = ROOT / "skills/review-craft/schemas"
            for artifact, schema_name in pairs:
                schema = json.loads((schema_root / schema_name).read_text(encoding="utf-8"))
                instance = json.loads((run_dir / artifact).read_text(encoding="utf-8"))
                errors = list(
                    Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(
                        instance
                    )
                )
                self.assertEqual(errors, [], f"{artifact}: {errors}")

if __name__ == "__main__":
    unittest.main()
