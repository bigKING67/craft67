from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from tools.design_craft.cli import main


class ReleaseCertificationCliTests(unittest.TestCase):
    def test_missing_certification_bundle_is_a_semantic_failure(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "release",
                        "certification",
                        "validate",
                        "--level",
                        "operational_95",
                        "--input-dir",
                        str(Path(raw) / "missing"),
                        "--json",
                    ]
                )
            payload = json.loads(stdout.getvalue())
            self.assertEqual(exit_code, 1)
            self.assertFalse(payload["ok"])

    def test_artifact_observation_is_exact_and_non_overwriting(self) -> None:
        run = {"repository": "example/design-craft"}
        artifact = {
            "id": 900,
            "name": "release-certification-v0.5.1-789",
            "size_in_bytes": 1024,
            "digest": f"sha256:{'a' * 64}",
            "expired": False,
            "created_at": "2026-07-23T00:00:00Z",
            "updated_at": "2026-07-23T00:00:01Z",
            "workflow_run": {
                "id": 789,
                "head_branch": "main",
                "head_sha": "a" * 40,
            },
        }
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw) / "artifact.json"
            with patch(
                "tools.design_craft.release.cli.load_observation",
                return_value=run,
            ), patch(
                "tools.design_craft.release.cli.observe_artifact",
                return_value=artifact,
            ), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                args = [
                    "release",
                    "artifact-observation",
                    "--artifact-id",
                    "900",
                    "--certification-observation",
                    str(Path(raw) / "run.json"),
                    "--expected-name",
                    artifact["name"],
                    "--output",
                    str(output),
                ]
                first = main(args)
                second = main(args)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(first, 0)
            self.assertEqual(second, 1)
            self.assertEqual(payload["artifact"], artifact)


if __name__ == "__main__":
    unittest.main()
