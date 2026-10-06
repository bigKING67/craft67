from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
import os
import subprocess
import sys

from tools.design_craft.repo import REPO_ROOT


SCRIPT_PATH = (
    REPO_ROOT / "skills/design-craft/scripts/design_craft_route_runtime.py"
)
SPEC = importlib.util.spec_from_file_location("design_craft_route_runtime", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
route_runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(route_runtime)


def platform_payload(
    platform: str = "web", *, signals: list[str] | None = None
) -> dict[str, object]:
    native = platform != "web"
    return {
        "platform": platform,
        "platform_source": "explicit",
        "platform_confidence": 1.0,
        "signals": signals or [],
        "contradictions": [],
        "product_context_path": "",
        "runtime_validation_kind": "browser" if not native else "native",
        "native_validation_required": native,
        "preferred_runtime_tool": "tmwd_browser" if not native else "native-tool",
    }


class RouteRuntimeTests(unittest.TestCase):
    def test_required_reference_contract_is_recommended_across_platforms(self) -> None:
        cases = (
            ("ios", "mobile", "new-page", True, False),
            ("web", "mobile", "reference-only", False, True),
            ("web", "brand", "reference-only", False, True),
            ("web", "landing", "reference-only", False, True),
            ("web", "landing", "new-page", True, False),
        )
        for platform, surface, intent, has_reference, needs_reference in cases:
            with self.subTest(platform=platform, surface=surface, intent=intent):
                payload = route_runtime.build_route_payload(
                    route_payload={}, platform_payload=platform_payload(platform),
                    route_source="portable_fallback", surface=surface, intent=intent,
                    scope="page", style="auto", style_authority_path="",
                    design_authority_mode="auto", existing_project=True,
                    has_reference=has_reference, needs_reference=needs_reference,
                )
                self.assertTrue(payload["reference_workflow"]["required"])
                self.assertIn(payload["reference_workflow"]["contract"], payload["recommended_design_craft_references"])

    def test_conditional_image_and_style_references_preserve_scope(self) -> None:
        common = {"platform": "web", "developer_product_seed_applicable": False}
        image = "references/image-reference-implementation.md"
        generation = "references/web-image-direction.md"
        plain = route_runtime.recommended_references(intent="functional", **common)
        self.assertNotIn(image, plain)
        self.assertNotIn(generation, plain)
        supplied = route_runtime.recommended_references(
            intent="new-page", has_reference=True, **common
        )
        self.assertIn(image, supplied)
        self.assertNotIn(generation, supplied)
        self.assertNotIn("references/reference-workflow.md", supplied)
        for intent in ("reference-only", "new-page"):
            refs = route_runtime.recommended_references(
                intent=intent, needs_reference=True, **common
            )
            self.assertIn(generation, refs)
            self.assertEqual(image in refs, intent == "new-page")
            for relative in refs:
                self.assertTrue((REPO_ROOT / "skills/design-craft" / relative).is_file())
        for surface in ("brand", "mobile"):
            refs = route_runtime.recommended_references(
                intent="reference-only", surface=surface, needs_reference=True, **common
            )
            self.assertNotIn(generation, refs)
        for style in ("high-end", "gpt-taste"):
            refs = route_runtime.recommended_references(intent="new-page", style=style, **common)
            self.assertIn("references/visual-judgment.md", refs)
            self.assertEqual("references/motion-quality.md" in refs, style == "gpt-taste")
        native = route_runtime.recommended_references(
            platform="ios", intent="new-page", has_reference=True, needs_reference=True,
            developer_product_seed_applicable=False,
        )
        self.assertNotIn(generation, native)
        measurement = route_runtime.recommended_references(
            intent="visual-refine", has_reference=True, evidence_mode="comp-fidelity", **common
        )
        self.assertIn("references/comp-fidelity.md", measurement)
        self.assertNotIn(image, measurement)

    def test_fallback_tiers_cover_runtime_risk_levels(self) -> None:
        common = {
            "style": "auto",
            "design_authority_mode": "auto",
            "has_reference": False,
            "needs_reference": False,
        }
        self.assertEqual(
            route_runtime.fallback_tier(
                intent="functional", scope="micro", **common
            ),
            "L0",
        )
        self.assertEqual(
            route_runtime.fallback_tier(
                intent="functional", scope="component", **common
            ),
            "L1-F",
        )
        self.assertEqual(
            route_runtime.fallback_tier(
                intent="visual-refine", scope="component", **common
            ),
            "L1-V",
        )
        self.assertEqual(
            route_runtime.fallback_tier(
                intent="redesign", scope="page", **common
            ),
            "L2",
        )

    def test_portable_fallback_denies_missing_authority(self) -> None:
        payload = route_runtime.build_route_payload(
            route_payload={},
            platform_payload=platform_payload(),
            route_source="portable_fallback",
            surface="dashboard",
            intent="redesign",
            scope="page",
            style="auto",
            style_authority_path="",
            design_authority_mode="auto",
            existing_project=True,
            has_reference=False,
            needs_reference=False,
        )

        self.assertFalse(payload["ok"])
        self.assertEqual(payload["frontend_tier"], "L2")
        self.assertEqual(payload["preflight_code"], "STYLE_AUTHORITY_MISSING")
        self.assertTrue(payload["browser_screenshot_required"])

    def test_global_payload_keeps_planner_decisions_and_normalizes_inputs(self) -> None:
        payload = route_runtime.build_route_payload(
            route_payload={
                "ok": True,
                "frontend_tier": "L1-V",
                "candidate_skills": ["design-craft"],
                "design_craft_conditional_references": [
                    "references/visual-judgment.md", "../../untrusted.md", {},
                ],
                "inputs": "invalid",
            },
            platform_payload=platform_payload(),
            route_source="codex_global",
            surface="dashboard",
            intent="visual-refine",
            scope="component",
            style="auto",
            style_authority_path="",
            design_authority_mode="auto",
            existing_project=True,
            has_reference=False,
            needs_reference=False,
        )

        self.assertEqual(payload["frontend_tier"], "L1-V")
        self.assertEqual(payload["route_source"], "codex_global")
        self.assertFalse(payload["degraded"])
        self.assertEqual(payload["inputs"]["platform"], "web")
        self.assertIn("references/visual-judgment.md", payload["recommended_design_craft_references"])
        self.assertNotIn("../../untrusted.md", payload["recommended_design_craft_references"])

    def test_native_route_recommends_platform_references(self) -> None:
        references = route_runtime.recommended_references(
            platform="adaptive",
            intent="visual-refine",
            developer_product_seed_applicable=False,
        )

        self.assertIn("references/ios-quality.md", references)
        self.assertIn("references/android-quality.md", references)
        self.assertIn("references/adaptive-quality.md", references)
        self.assertIn("references/interaction-physics.md", references)

    def test_react_native_expo_reference_is_conditionally_routed(self) -> None:
        payload = route_runtime.build_route_payload(
            route_payload={"ok": True, "frontend_tier": "L1-V"},
            platform_payload=platform_payload(
                "adaptive", signals=["React Native/Expo dependency"]
            ),
            route_source="codex_global",
            surface="app",
            intent="visual-refine",
            scope="component",
            style="auto",
            style_authority_path="DESIGN.md",
            design_authority_mode="auto",
            existing_project=True,
            has_reference=False,
            needs_reference=False,
        )

        self.assertTrue(payload["react_native_expo_motion_applicable"])
        self.assertIn(
            "references/react-native-expo-motion.md",
            payload["recommended_design_craft_references"],
        )

    def test_non_react_native_adaptive_route_excludes_expo_reference(self) -> None:
        payload = route_runtime.build_route_payload(
            route_payload={"ok": True, "frontend_tier": "L1-V"},
            platform_payload=platform_payload(
                "adaptive", signals=["Flutter pubspec"]
            ),
            route_source="codex_global",
            surface="app",
            intent="visual-refine",
            scope="component",
            style="auto",
            style_authority_path="DESIGN.md",
            design_authority_mode="auto",
            existing_project=True,
            has_reference=False,
            needs_reference=False,
        )

        self.assertFalse(payload["react_native_expo_motion_applicable"])
        self.assertNotIn(
            "references/react-native-expo-motion.md",
            payload["recommended_design_craft_references"],
        )

    def test_expo_reference_routes_for_each_native_scope_without_expanding_scope(self) -> None:
        for platform in ("ios", "android", "adaptive"):
            with self.subTest(platform=platform):
                payload = route_runtime.build_route_payload(
                    route_payload={"ok": True, "frontend_tier": "L1-V"},
                    platform_payload=platform_payload(
                        platform, signals=["React Native/Expo dependency"]
                    ),
                    route_source="codex_global",
                    surface="app",
                    intent="visual-refine",
                    scope="component",
                    style="auto",
                    style_authority_path="DESIGN.md",
                    design_authority_mode="auto",
                    existing_project=True,
                    has_reference=False,
                    needs_reference=False,
                )
                self.assertTrue(payload["react_native_expo_motion_applicable"])
                self.assertIn(
                    "references/react-native-expo-motion.md",
                    payload["recommended_design_craft_references"],
                )

        reference = (
            REPO_ROOT
            / "skills/design-craft/references/react-native-expo-motion.md"
        ).read_text(encoding="utf-8")
        self.assertIn("release build on every shipped target", reference)
        self.assertIn(
            "single-platform scope does not create evidence obligations",
            reference,
        )

    def test_explicit_web_route_excludes_expo_reference_even_with_dependency_signal(self) -> None:
        payload = route_runtime.build_route_payload(
            route_payload={"ok": True, "frontend_tier": "L1-V"},
            platform_payload=platform_payload(
                "web", signals=["React Native/Expo dependency"]
            ),
            route_source="codex_global",
            surface="app",
            intent="visual-refine",
            scope="component",
            style="auto",
            style_authority_path="DESIGN.md",
            design_authority_mode="auto",
            existing_project=True,
            has_reference=False,
            needs_reference=False,
        )

        self.assertFalse(payload["react_native_expo_motion_applicable"])
        self.assertNotIn(
            "references/react-native-expo-motion.md",
            payload["recommended_design_craft_references"],
        )

    def test_nested_expo_source_target_routes_from_nearest_package(self) -> None:
        with tempfile.TemporaryDirectory(prefix="design-craft-expo-route-") as raw:
            root = Path(raw)
            (root / ".git").mkdir()
            (root / "DESIGN.md").write_text("# Design", encoding="utf-8")
            (root / "package.json").write_text(
                json.dumps({"workspaces": ["packages/*"]}), encoding="utf-8"
            )
            mobile = root / "packages/mobile"
            target = mobile / "src/components"
            target.mkdir(parents=True)
            (mobile / "package.json").write_text(
                json.dumps({"dependencies": {"expo": "latest"}}), encoding="utf-8"
            )
            environment = dict(os.environ)
            environment["DESIGN_CRAFT_ROUTE_PLAN"] = str(root / "missing-plan.sh")
            environment["PYTHONDONTWRITEBYTECODE"] = "1"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--target",
                    str(target),
                    "--surface",
                    "app",
                    "--intent",
                    "visual-refine",
                    "--scope",
                    "component",
                    "--json-only",
                ],
                cwd=REPO_ROOT,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["platform"], "adaptive")
            self.assertTrue(payload["react_native_expo_motion_applicable"])
            self.assertIn(
                "references/react-native-expo-motion.md",
                payload["recommended_design_craft_references"],
            )

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unsupported")
    def test_symlinked_package_metadata_cannot_inject_expo_signal(self) -> None:
        with tempfile.TemporaryDirectory(prefix="design-craft-expo-link-") as raw:
            base = Path(raw)
            root = base / "repo"
            (root / ".git").mkdir(parents=True)
            (root / "DESIGN.md").write_text("# Design", encoding="utf-8")
            (root / "package.json").write_text(
                json.dumps({"workspaces": ["packages/*"]}), encoding="utf-8"
            )
            mobile = root / "packages/mobile"
            target = mobile / "src/components"
            target.mkdir(parents=True)
            outside = base / "outside-package.json"
            outside.write_text(
                json.dumps({"dependencies": {"expo": "latest"}}), encoding="utf-8"
            )
            (mobile / "package.json").symlink_to(outside)
            environment = dict(os.environ)
            environment["DESIGN_CRAFT_ROUTE_PLAN"] = str(root / "missing-plan.sh")
            environment["PYTHONDONTWRITEBYTECODE"] = "1"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--target",
                    str(target),
                    "--surface",
                    "app",
                    "--intent",
                    "visual-refine",
                    "--scope",
                    "component",
                    "--json-only",
                ],
                cwd=REPO_ROOT,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["platform"], "web")
            self.assertFalse(payload["react_native_expo_motion_applicable"])
            self.assertTrue(
                any(
                    "package metadata unavailable" in signal
                    for signal in payload["platform_signals"]
                )
            )

    def test_oversized_package_metadata_is_bounded_and_degraded(self) -> None:
        with tempfile.TemporaryDirectory(prefix="design-craft-expo-oversized-") as raw:
            root = Path(raw)
            (root / ".git").mkdir()
            (root / "DESIGN.md").write_text("# Design", encoding="utf-8")
            mobile = root / "packages/mobile"
            target = mobile / "src"
            target.mkdir(parents=True)
            with (mobile / "package.json").open("wb") as handle:
                handle.truncate(1024 * 1024 + 1)
            environment = dict(os.environ)
            environment["DESIGN_CRAFT_ROUTE_PLAN"] = str(root / "missing-plan.sh")
            environment["PYTHONDONTWRITEBYTECODE"] = "1"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--target",
                    str(target),
                    "--surface",
                    "app",
                    "--intent",
                    "visual-refine",
                    "--scope",
                    "component",
                    "--json-only",
                ],
                cwd=REPO_ROOT,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["platform"], "web")
            self.assertTrue(
                any(
                    "exceeds 1048576 bytes" in signal
                    for signal in payload["platform_signals"]
                )
            )

    def test_reference_only_route_exposes_machine_readable_workflow(self) -> None:
        payload = route_runtime.build_route_payload(
            route_payload={"ok": True, "frontend_tier": "L1-V"},
            platform_payload=platform_payload(),
            route_source="codex_global",
            surface="landing",
            intent="reference-only",
            scope="page",
            style="auto",
            style_authority_path="",
            design_authority_mode="auto",
            existing_project=True,
            has_reference=False,
            needs_reference=False,
        )

        self.assertFalse(payload["runtime_validation_required"])
        self.assertEqual(
            payload["reference_workflow"],
            {
                "required": True,
                "triggers": ["reference-only"],
                "contract": "references/reference-workflow.md",
            },
        )
        self.assertIn(
            "references/reference-workflow.md",
            payload["recommended_design_craft_references"],
        )

    def test_reference_only_portable_fallback_does_not_require_style_authority(self) -> None:
        payload = route_runtime.build_route_payload(
            route_payload={},
            platform_payload=platform_payload(),
            route_source="portable_fallback",
            surface="landing",
            intent="reference-only",
            scope="page",
            style="auto",
            style_authority_path="",
            design_authority_mode="auto",
            existing_project=True,
            has_reference=False,
            needs_reference=False,
        )

        self.assertTrue(payload["ok"])
        self.assertEqual(payload["preflight_code"], "OK")
        self.assertFalse(payload["runtime_validation_required"])
        self.assertFalse(payload["browser_validation_required"])
        self.assertFalse(payload["directory_governance_required"])
        self.assertFalse(payload["performance_review_required"])
        self.assertTrue(payload["reference_workflow"]["required"])

    def test_reference_flags_trigger_workflow_without_changing_runtime_need(self) -> None:
        payload = route_runtime.build_route_payload(
            route_payload={"ok": True, "frontend_tier": "L1-V"},
            platform_payload=platform_payload(),
            route_source="codex_global",
            surface="dashboard",
            intent="visual-refine",
            scope="component",
            style="auto",
            style_authority_path="DESIGN.md",
            design_authority_mode="auto",
            existing_project=True,
            has_reference=True,
            needs_reference=True,
        )

        self.assertTrue(payload["runtime_validation_required"])
        self.assertEqual(
            payload["reference_workflow"]["triggers"],
            ["has-reference-image", "needs-generated-reference"],
        )

    def test_comp_fidelity_route_is_measurement_only_without_runtime(self) -> None:
        payload = route_runtime.build_route_payload(
            route_payload={},
            platform_payload=platform_payload(),
            route_source="portable_fallback",
            surface="landing",
            intent="reference-only",
            scope="page",
            style="auto",
            style_authority_path="",
            design_authority_mode="auto",
            existing_project=True,
            has_reference=True,
            needs_reference=False,
            evidence_mode="comp-fidelity",
        )

        self.assertTrue(payload["ok"])
        self.assertEqual(payload["evidence_mode"], "comp-fidelity")
        self.assertFalse(payload["runtime_validation_required"])
        self.assertFalse(payload["browser_validation_required"])
        self.assertFalse(payload["browser_screenshot_required"])
        self.assertFalse(payload["visual_contract_required"])
        self.assertEqual(
            payload["evidence_workflow"]["delivery_state"],
            "measurement_only",
        )
        self.assertIsNone(
            payload["evidence_workflow"]["global_pixel_pass_threshold"]
        )
        self.assertIn(
            "references/comp-fidelity.md",
            payload["recommended_design_craft_references"],
        )

    def test_sealed_rendition_route_requires_web_capture_and_authority(self) -> None:
        payload = route_runtime.build_route_payload(
            route_payload={},
            platform_payload=platform_payload(),
            route_source="portable_fallback",
            surface="landing",
            intent="reference-only",
            scope="page",
            style="auto",
            style_authority_path="DESIGN.md",
            design_authority_mode="auto",
            existing_project=True,
            has_reference=True,
            needs_reference=False,
            evidence_mode="sealed-rendition",
        )

        self.assertTrue(payload["ok"])
        self.assertEqual(payload["evidence_mode"], "sealed-rendition")
        self.assertTrue(payload["runtime_validation_required"])
        self.assertTrue(payload["browser_validation_required"])
        self.assertTrue(payload["browser_screenshot_required"])
        self.assertTrue(payload["visual_contract_required"])
        self.assertTrue(
            payload["evidence_workflow"]["capture_plan_required"]
        )
        self.assertEqual(
            payload["evidence_workflow"]["capture_runtime_owner"],
            "sealed_capture_plan",
        )

    def test_evidence_mode_rejects_missing_reference_and_native_sealed_route(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires --has-reference-image 1"):
            route_runtime.build_route_payload(
                route_payload={},
                platform_payload=platform_payload(),
                route_source="portable_fallback",
                surface="landing",
                intent="reference-only",
                scope="page",
                style="auto",
                style_authority_path="",
                design_authority_mode="auto",
                existing_project=True,
                has_reference=False,
                needs_reference=False,
                evidence_mode="comp-fidelity",
            )

        with self.assertRaisesRegex(ValueError, "supports platform=web"):
            route_runtime.build_route_payload(
                route_payload={},
                platform_payload=platform_payload("ios"),
                route_source="portable_fallback",
                surface="app",
                intent="reference-only",
                scope="page",
                style="auto",
                style_authority_path="DESIGN.md",
                design_authority_mode="auto",
                existing_project=True,
                has_reference=True,
                needs_reference=False,
                evidence_mode="sealed-rendition",
            )

    def test_route_loader_rejects_non_object_json(self) -> None:
        with tempfile.TemporaryDirectory(prefix="design-craft-route-runtime-") as raw:
            path = Path(raw) / "route.json"
            path.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")

            self.assertEqual(route_runtime.load_route_payload(path), {})


if __name__ == "__main__":
    unittest.main()
