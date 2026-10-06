from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.design_craft.repo import REPO_ROOT


LAB_SCRIPT = REPO_ROOT / "skills/design-craft/scripts/design_craft_shadow_lab.py"
COMPARE_SCRIPT = (
    REPO_ROOT / "skills/design-craft/scripts/design_craft_shadow_compare.py"
)
SCHEMA = (
    REPO_ROOT / "skills/design-craft/contracts/shadow-lab-comparison.schema.json"
)


def load_script(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


shadow_lab = load_script("design_craft_shadow_lab_comparison_test", LAB_SCRIPT)
shadow_compare = load_script("design_craft_shadow_compare_test", COMPARE_SCRIPT)


def git(repo: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-c", "core.fsmonitor=false", *arguments],
        cwd=repo,
        env={
            **os.environ,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
        },
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr)
    return completed.stdout


def create_repo(parent: Path) -> Path:
    repo = parent / "source"
    repo.mkdir()
    git(repo, "init", "--quiet")
    git(repo, "config", "user.name", "Design Craft Tests")
    git(repo, "config", "user.email", "design-craft-tests@example.invalid")
    (repo / "about.html").write_text("<main>baseline</main>\n")
    git(repo, "add", "about.html")
    git(repo, "commit", "--quiet", "-m", "fixture")
    return repo


def write_spec(parent: Path, repo: Path) -> tuple[Path, list[dict]]:
    labs = []
    for _ in range(2):
        labs.append(
            shadow_lab.prepare_lab(
                source_path=repo,
                requested_ref="HEAD",
                output_root_path=parent / "labs",
            )["manifest"]
        )
    evidence = parent / "evidence"
    evidence.mkdir()
    for variant_id in ("identity-first", "responsive-first"):
        (evidence / f"{variant_id}-desktop.png").write_bytes(
            f"{variant_id}:desktop".encode()
        )
        (evidence / f"{variant_id}-mobile.png").write_bytes(
            f"{variant_id}:mobile".encode()
        )
    variants = []
    for variant_id, lab in zip(("identity-first", "responsive-first"), labs):
        variants.append(
            {
                "id": variant_id,
                "manifest": lab["isolation"]["manifest_path"],
                "axis": f"{variant_id} information hierarchy",
                "hypothesis": f"{variant_id} improves the bounded user journey",
                "invariants": ["Preserve the same content and target route"],
                "risks": ["May increase implementation and review cost"],
                "artifacts": [
                    {
                        "id": f"{variant_id}-desktop",
                        "role": "desktop",
                        "path": str(evidence / f"{variant_id}-desktop.png"),
                    },
                    {
                        "id": f"{variant_id}-mobile",
                        "role": "mobile",
                        "path": str(evidence / f"{variant_id}-mobile.png"),
                    },
                ],
                "runtime_checks": [
                    {
                        "id": "mobile-overflow",
                        "status": "passed",
                        "evidence_refs": [f"{variant_id}-mobile"],
                        "note": "The mobile viewport stayed within its document width.",
                    },
                    {
                        "id": "reduced-motion",
                        "status": "unverified",
                        "evidence_refs": [],
                        "note": "Reduced motion still needs a dedicated runtime trace.",
                    },
                ],
            }
        )
    spec = {
        "schema": shadow_compare.SPEC_SCHEMA,
        "comparison_id": "about-page-reference",
        "target": {
            "surface": "about page",
            "user_job": "Understand the author and choose a useful next route.",
            "acceptance_rules": ["Use the same content and viewport set"],
            "required_evidence_roles": ["desktop", "mobile"],
            "required_runtime_checks": ["mobile-overflow", "reduced-motion"],
        },
        "variants": variants,
        "decision": {
            "status": "recommended",
            "preferred_variant": "identity-first",
            "approval_source": "user_delegated",
            "absorb": ["Editorial identity hierarchy"],
            "adapt": ["Responsive mobile composition"],
            "reject": ["Copying source brand assets"],
            "unverified": ["Keyboard focus behavior"],
            "production_promotion_authorized": False,
        },
    }
    spec_path = parent / "comparison-spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    return spec_path, labs


class ShadowLabComparisonTests(unittest.TestCase):
    def test_schema_preserves_the_zero_write_and_promotion_boundaries(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

        self.assertEqual(
            schema["properties"]["schema"]["const"],
            shadow_compare.COMPARISON_SCHEMA,
        )
        boundary = schema["properties"]["boundary"]["properties"]
        self.assertEqual(boundary["source_writes_allowed"], {"const": False})
        self.assertEqual(boundary["artifacts_repo_external"], {"const": True})
        self.assertEqual(
            boundary["production_promotion_authorized"], {"const": False}
        )

    def test_build_and_live_validate_bind_distinct_labs_and_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            parent = Path(raw)
            repo = create_repo(parent)
            spec_path, _ = write_spec(parent, repo)

            payload = shadow_compare.build_comparison(spec_path)
            output = parent / "comparison.json"
            shadow_lab.atomic_write_json(output, payload)
            result = shadow_compare.validate_comparison(
                output,
                require_live_labs=True,
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["variant_count"], 2)
            self.assertEqual(result["artifact_count"], 4)
            self.assertEqual(result["live_labs_verified"], 2)
            self.assertEqual(payload["decision"]["preferred_variant"], "identity-first")
            self.assertFalse(payload["boundary"]["source_writes_allowed"])
            self.assertFalse(
                payload["boundary"]["production_promotion_authorized"]
            )

    def test_rejects_reusing_one_lab_for_two_variants(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            parent = Path(raw)
            repo = create_repo(parent)
            spec_path, labs = write_spec(parent, repo)
            spec = json.loads(spec_path.read_text())
            spec["variants"][1]["manifest"] = labs[0]["isolation"]["manifest_path"]
            spec_path.write_text(json.dumps(spec))

            with self.assertRaisesRegex(
                shadow_compare.ShadowComparisonError,
                "distinct Shadow Lab",
            ):
                shadow_compare.build_comparison(spec_path)

    def test_rejects_evidence_inside_the_source_repo(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            parent = Path(raw)
            repo = create_repo(parent)
            spec_path, _ = write_spec(parent, repo)
            spec = json.loads(spec_path.read_text())
            spec["variants"][0]["artifacts"][0]["path"] = str(
                repo / "about.html"
            )
            spec_path.write_text(json.dumps(spec))

            with self.assertRaisesRegex(
                shadow_compare.ShadowComparisonError,
                "outside the source repo",
            ):
                shadow_compare.build_comparison(spec_path)

    def test_rejects_missing_comparison_evidence_role(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            parent = Path(raw)
            repo = create_repo(parent)
            spec_path, _ = write_spec(parent, repo)
            spec = json.loads(spec_path.read_text())
            spec["variants"][1]["artifacts"] = spec["variants"][1]["artifacts"][:1]
            spec_path.write_text(json.dumps(spec))

            with self.assertRaisesRegex(
                shadow_compare.ShadowComparisonError,
                "missing roles: mobile",
            ):
                shadow_compare.build_comparison(spec_path)

    def test_static_validation_rejects_artifact_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            parent = Path(raw)
            repo = create_repo(parent)
            spec_path, _ = write_spec(parent, repo)
            payload = shadow_compare.build_comparison(spec_path)
            output = parent / "comparison.json"
            shadow_lab.atomic_write_json(output, payload)
            artifact = Path(payload["variants"][0]["artifacts"][0]["path"])
            artifact.write_bytes(b"changed after closeout")

            with self.assertRaisesRegex(
                shadow_compare.ShadowComparisonError,
                "bytes does not match|sha256 does not match",
            ):
                shadow_compare.validate_comparison(
                    output,
                    require_live_labs=False,
                )

    def test_recommendation_requires_explicit_user_delegation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            parent = Path(raw)
            repo = create_repo(parent)
            spec_path, _ = write_spec(parent, repo)
            spec = json.loads(spec_path.read_text())
            spec["decision"]["approval_source"] = "none"
            spec_path.write_text(json.dumps(spec))

            with self.assertRaisesRegex(
                shadow_compare.ShadowComparisonError,
                "must be user_delegated",
            ):
                shadow_compare.build_comparison(spec_path)


if __name__ == "__main__":
    unittest.main()
