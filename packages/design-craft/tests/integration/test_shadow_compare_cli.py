from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.design_craft.repo import REPO_ROOT


LAB_SCRIPT = REPO_ROOT / "skills/design-craft/scripts/design_craft_shadow_lab.py"
COMPARE_SCRIPT = (
    REPO_ROOT / "skills/design-craft/scripts/design_craft_shadow_compare.py"
)


def command(cwd: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        list(arguments),
        cwd=cwd,
        env={
            **os.environ,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30,
    )


def git(repo: Path, *arguments: str) -> None:
    completed = command(repo, "git", "-c", "core.fsmonitor=false", *arguments)
    if completed.returncode != 0:
        raise AssertionError(completed.stderr.decode(errors="replace"))


class ShadowCompareCliTests(unittest.TestCase):
    def test_create_refuses_overwrite_and_live_validate_replays_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            parent = Path(raw)
            repo = parent / "source"
            repo.mkdir()
            git(repo, "init", "--quiet")
            git(repo, "config", "user.name", "Design Craft Tests")
            git(repo, "config", "user.email", "design-craft-tests@example.invalid")
            (repo / "screen.tsx").write_text("export const page = true;\n")
            git(repo, "add", "screen.tsx")
            git(repo, "commit", "--quiet", "-m", "fixture")

            manifests = []
            for _ in range(2):
                prepared = command(
                    REPO_ROOT,
                    sys.executable,
                    str(LAB_SCRIPT),
                    "prepare",
                    "--source",
                    str(repo),
                    "--output-root",
                    str(parent / "labs"),
                )
                self.assertEqual(prepared.returncode, 0, prepared.stdout.decode())
                manifests.append(
                    json.loads(prepared.stdout)["manifest"]["isolation"][
                        "manifest_path"
                    ]
                )

            evidence = parent / "evidence"
            evidence.mkdir()
            variants = []
            for variant_id, manifest in zip(("calm", "dense"), manifests):
                artifact = evidence / f"{variant_id}.png"
                artifact.write_bytes(variant_id.encode())
                variants.append(
                    {
                        "id": variant_id,
                        "manifest": manifest,
                        "axis": f"{variant_id} disclosure strategy",
                        "hypothesis": f"The {variant_id} direction improves task comprehension.",
                        "invariants": ["Same task, content, and viewport"],
                        "risks": ["Requires a deliberate promotion review"],
                        "artifacts": [
                            {
                                "id": f"{variant_id}-desktop",
                                "role": "desktop",
                                "path": str(artifact),
                            }
                        ],
                        "runtime_checks": [
                            {
                                "id": "initial-load",
                                "status": "passed",
                                "evidence_refs": [f"{variant_id}-desktop"],
                                "note": "The initial rendered state remained visible and stable.",
                            }
                        ],
                    }
                )
            spec = {
                "schema": "design-craft.shadow-lab-comparison-spec.v1",
                "comparison_id": "cli-roundtrip",
                "target": {
                    "surface": "settings page",
                    "user_job": "Compare two bounded disclosure strategies.",
                    "acceptance_rules": ["Use identical source and acceptance rules"],
                    "required_evidence_roles": ["desktop"],
                    "required_runtime_checks": ["initial-load"],
                },
                "variants": variants,
                "decision": {
                    "status": "ready_for_selection",
                    "preferred_variant": None,
                    "approval_source": "none",
                    "absorb": [],
                    "adapt": ["Select the best disclosure mechanism"],
                    "reject": ["Do not edit production before selection"],
                    "unverified": ["Keyboard behavior"],
                    "production_promotion_authorized": False,
                },
            }
            spec_path = parent / "spec.json"
            spec_path.write_text(json.dumps(spec))
            output = parent / "comparison.json"

            created = command(
                REPO_ROOT,
                sys.executable,
                str(COMPARE_SCRIPT),
                "create",
                "--spec",
                str(spec_path),
                "--output",
                str(output),
            )
            self.assertEqual(created.returncode, 0, created.stdout.decode())
            self.assertTrue(output.is_file())

            refused = command(
                REPO_ROOT,
                sys.executable,
                str(COMPARE_SCRIPT),
                "create",
                "--spec",
                str(spec_path),
                "--output",
                str(output),
            )
            self.assertEqual(refused.returncode, 2)
            self.assertIn("refusing to overwrite", refused.stdout.decode())

            validated = command(
                REPO_ROOT,
                sys.executable,
                str(COMPARE_SCRIPT),
                "validate",
                "--manifest",
                str(output),
                "--require-live-labs",
            )
            self.assertEqual(validated.returncode, 0, validated.stdout.decode())
            result = json.loads(validated.stdout)
            self.assertTrue(result["ok"])
            self.assertEqual(result["live_labs_verified"], 2)


if __name__ == "__main__":
    unittest.main()
