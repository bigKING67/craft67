from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "skills" / "3d-craft" / "scripts" / "3d_craft.py"


class ThreeDCraftCliTests(unittest.TestCase):
    def run_cli(self, *arguments: str, expected: int = 0) -> dict:
        result = subprocess.run(
            ["python3", str(CLI), *arguments, "--json"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, expected, result.stderr or result.stdout)
        return json.loads(result.stdout)

    @staticmethod
    def write_json(path: Path, value: dict) -> None:
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    @staticmethod
    def file_entry(path: Path, value: bytes | None = None) -> dict:
        if value is not None:
            path.write_bytes(value)
        contents = path.read_bytes()
        return {
            "path": str(path),
            "sha256": hashlib.sha256(contents).hexdigest(),
            "bytes": len(contents),
        }

    @staticmethod
    def write_png_header(path: Path, width: int, height: int) -> None:
        path.write_bytes(
            b"\x89PNG\r\n\x1a\n"
            + struct.pack(">I", 13)
            + b"IHDR"
            + struct.pack(">II", width, height)
        )

    @staticmethod
    def performance_profile() -> dict:
        return {
            "test_status": "PASS",
            "source": "viewer-observability",
            "warmup_ms": 3000,
            "sample_ms": 10000,
            "started_at_ms": 100,
            "sample_started_at_ms": 3100,
            "completed_at_ms": 13100,
            "sample_count": 600,
            "viewport": [1440, 900],
            "device_pixel_ratio": 1,
            "visibility_state": "visible",
            "frame_p50_ms": 7,
            "frame_p95_ms": 8,
            "renderer_peak": {
                "draw_calls": 1,
                "triangles": 3,
                "geometries": 2,
                "textures": 0,
            },
        }

    @staticmethod
    def resource_stability(*, geometry_delta: int = 0, texture_delta: int = 0) -> dict:
        samples = [
            {
                "mounts": cycle + 1,
                "disposes": cycle * 2,
                "geometries": 2 + (geometry_delta if cycle == 3 else 0),
                "textures": texture_delta if cycle == 3 else 0,
                "captured_at_ms": 14000 + cycle * 1000,
            }
            for cycle in range(4)
        ]
        return {
            "test_status": "PASS",
            "source": "viewer-observability",
            "cycles": 3,
            "samples": samples,
            "geometry_delta": geometry_delta,
            "texture_delta": texture_delta,
        }

    def profile_observation(self, glb: Path) -> dict:
        glb_hash = hashlib.sha256(glb.read_bytes()).hexdigest()
        profile = self.performance_profile()
        renderer = profile["renderer_peak"]
        return {
            "schema": "3d-craft.web-profile-observation.v1",
            "status": "PASS",
            "source": "viewer-observability",
            "asset": {"url": "/asset.glb", "sha256": glb_hash},
            "page": {
                "visibility_state": "visible",
                "viewport": [1440, 900],
                "device_pixel_ratio": 1,
            },
            "metrics": {
                **renderer,
                "frame_p50_ms": profile["frame_p50_ms"],
                "frame_p95_ms": profile["frame_p95_ms"],
            },
            "performance_profile": profile,
            "resource_stability": self.resource_stability(),
        }

    def browser_draft(
        self,
        *,
        glb: Path,
        desktop: Path,
        mobile: Path,
        desktop_visibility: str = "visible",
        network_sha256: str | None = None,
    ) -> dict:
        glb_bytes = glb.read_bytes()
        glb_hash = hashlib.sha256(glb_bytes).hexdigest()
        return {
            "schema": "3d-craft.browser-runtime-draft.v1",
            "status": "ready",
            "asset_url": "/asset.glb",
            "console_errors": 0,
            "network": {
                "status": "PASS",
                "bytes": len(glb_bytes),
                "sha256": network_sha256 or glb_hash,
            },
            "raf": {"delta": 10},
            "metrics": {
                "draw_calls": 1,
                "textures": 0,
                "frame_p50_ms": 7,
                "frame_p95_ms": 8,
                "geometries": 2,
                "triangles": 3,
            },
            "performance_profile": self.performance_profile(),
            "lifecycle": {
                "remount_test_status": "PASS",
                "ready_after_clean_reload": True,
                "context_loss": {
                    "test_status": "PASS",
                    "supported": True,
                    "losses": 1,
                    "restores": 1,
                    "ready_after_restore": True,
                    "raf_resumed_after_restore": True,
                },
                "resource_stability": self.resource_stability(),
            },
            "cross_runtime": {"required_node_coverage_percent": 100, "bbox_drift_percent": 0.1},
            "desktop_screenshot": {
                "source_path": str(desktop),
                "css_viewport": [1440, 900],
                "device_pixel_ratio": 1,
                "capture_target": "viewport",
                "visibility_state": desktop_visibility,
                "horizontal_overflow": False,
                "visual_review": "PASS",
            },
            "responsive_layout": {
                "status": "PASS",
                "horizontal_overflow": False,
                "viewport": [390, 844],
                "scroll_extent": [390, 1269],
            },
            "mobile_screenshot": {
                "source_path": str(mobile),
                "css_viewport": [390, 844],
                "device_pixel_ratio": 1,
                "capture_target": "full_page",
                "visibility_state": "visible",
                "horizontal_overflow": False,
                "visual_review": "PASS",
                "note": "Layout evidence only; physical mobile GPU remains unverified.",
            },
            "warnings": [],
            "unverified": ["Physical-mobile GPU frame timing was not measured."],
        }

    def create_valid_run(
        self,
        run_dir: Path,
        *,
        target: str = "bridge",
        evidence_level: str = "assured",
    ) -> dict[str, Path | dict]:
        assets = run_dir / "assets"
        evidence = run_dir / "evidence"
        source_dir = run_dir / "source"
        reports = run_dir / "reports"
        for directory in (assets, evidence, source_dir, reports):
            directory.mkdir(parents=True)

        route_payload = self.run_cli(
            "route",
            "--target",
            target,
            "--intent",
            "build",
            "--profile",
            "product-asset",
            "--quality-tier",
            "production",
            "--authoring-mode",
            "hybrid",
            "--evidence-level",
            evidence_level,
        )
        route = {key: value for key, value in route_payload.items() if key not in {"command", "status"}}

        source = source_dir / "source.blend"
        source_entry = self.file_entry(source, b"source")
        blend_file = assets / "asset.blend"
        blend_entry = self.file_entry(blend_file, b"blend") if target in {"blender", "bridge"} else None
        glb_file = assets / "asset.glb"
        glb_entry = self.file_entry(glb_file, b"glb") if target in {"bridge", "web3d"} else None

        scene = {
            "schema": "3d-craft.scene.v1",
            "units": "meters",
            "up_axis": "Z",
            "origin_policy": "object-base-center",
            "topology_policy": "closed",
            "authoring_mode": "hybrid",
            "dimensions": {"width": 1, "depth": 1, "height": 1, "tolerance_percent": 1},
            "identity_features": [
                {"id": "body", "description": "fixture body", "importance": "critical", "status": "specified"}
            ],
            "components": ["body"],
            "materials": ["matte"],
            "cameras": ["front", "back", "left", "right", "top", "perspective"],
            "runtime": {
                "engine": "r3f" if target != "blender" else "none",
                "renderer": "webgl" if target != "blender" else "none",
                "target_devices": ["desktop", "mobile"] if target != "blender" else [],
            },
            "budgets": {
                "status": "approved",
                "asset_bytes": 1024,
                "triangles": 100,
                "draw_calls": 10,
                "textures": 4,
                "frame_p95_ms": 20,
                "performance_profile": {
                    "viewport": [1440, 900],
                    "device_pixel_ratio": 1,
                    "warmup_ms": 3000,
                    "sample_ms": 10000,
                    "resource_reload_cycles": 3,
                    "max_geometry_delta": 0,
                    "max_texture_delta": 0,
                },
                "required_node_coverage_percent": 100,
                "bbox_drift_percent": 0.5,
            },
            "required_evidence": [],
        }
        required_evidence = set()
        if "reproduction" in route["hard_gates"]:
            required_evidence.add("clean-reproduction")
        if "scene_integrity" in route["hard_gates"]:
            required_evidence.add("blend-inspection")
        if "blender.render" in route["required_capabilities"]:
            required_evidence.update(("front", "back", "left", "right", "top", "perspective", "contact-sheet", "lookdev", "visual-review"))
        if "gltf" in route["hard_gates"]:
            required_evidence.add("gltf-validation")
        if "web_runtime" in route["hard_gates"] or "cross_runtime" in route["hard_gates"]:
            required_evidence.update(("browser-runtime", "browser-desktop-screenshot", "browser-mobile-screenshot"))
        scene["required_evidence"] = sorted(required_evidence)
        self.write_json(run_dir / "scene.json", scene)

        derived = [entry for entry in (blend_entry, glb_entry) if entry]
        asset = {
            "schema": "3d-craft.asset.v1",
            "authority": "hybrid",
            "source": source_entry,
            "derived": derived,
            "tool_versions": {"3d-craft": "0.1.0"},
            "licenses": [{"subject": "fixture", "license": "MIT", "source": "test"}],
            "gltf_summary": {
                "nodes": 1 if glb_entry else 0,
                "meshes": 1 if glb_entry else 0,
                "primitives": 1 if glb_entry else 0,
                "materials": 1 if glb_entry else 0,
                "textures": 0,
                "animations": 0,
                "triangles": 1 if glb_entry else 0,
                "extensions": [],
            },
        }
        self.write_json(run_dir / "asset.json", asset)

        run = {
            "schema": "3d-craft.run.v1",
            "run_id": "fixture-0001",
            "project_key": "fixture",
            "created_at": "2026-09-02T00:00:00Z",
            "input_hashes": {"scene_contract": hashlib.sha256((run_dir / "scene.json").read_bytes()).hexdigest()},
            "route": route,
            "capabilities": {name: "available" for name in route["required_capabilities"]},
            "versions": {"3d-craft": "0.1.0"},
            "stages": [{"id": name, "status": "pending"} for name in route["hard_gates"]],
            "repairs": [],
            "evidence": [],
            "unverified": [],
        }
        self.write_json(run_dir / "run.json", run)

        if blend_entry:
            self.write_json(
                evidence / "blend-inspection.json",
                {
                    "schema": "3d-craft.blend-inspection.v1",
                    "status": "PASS",
                    "blend": {"path": str(blend_file), "sha256": blend_entry["sha256"]},
                    "coverage": {"components_percent": 100, "materials_percent": 100},
                },
            )
            reproduction_candidate = {"blend_sha256": blend_entry["sha256"]}
            if glb_entry:
                reproduction_candidate["gltf_sha256"] = glb_entry["sha256"]
            self.write_json(
                evidence / "reproduction.json",
                {"schema": "3d-craft.reproduction.v1", "match": True, "candidate": reproduction_candidate},
            )

        if blend_entry and "blender.render" in route["required_capabilities"]:
            views = []
            for view in ("front", "back", "left", "right", "top", "perspective"):
                views.append({"view": view, **self.file_entry(evidence / f"{view}.png", view.encode())})
            render_path = evidence / "render-evidence.json"
            self.write_json(
                render_path,
                {
                    "schema": "3d-craft.render-evidence.v1",
                    "status": "PASS",
                    "blend": {"path": str(blend_file), "sha256": blend_entry["sha256"]},
                    "scene_contract": {
                        "path": str(run_dir / "scene.json"),
                        "sha256": hashlib.sha256((run_dir / "scene.json").read_bytes()).hexdigest(),
                    },
                    "views": views,
                    "contact_sheet": self.file_entry(evidence / "contact.png", b"contact"),
                    "lookdev": self.file_entry(evidence / "lookdev.png", b"lookdev"),
                },
            )
            self.write_json(
                evidence / "visual-review.json",
                {
                    "schema": "3d-craft.visual-review.v1",
                    "status": "PASS",
                    "candidate": {
                        "blend_sha256": blend_entry["sha256"],
                        "render_evidence_sha256": hashlib.sha256(render_path.read_bytes()).hexdigest(),
                    },
                    "reviewer": {"kind": "agent", "name": "test-agent"},
                    "reviewed_at": "2026-09-02T00:00:00Z",
                    "features": [
                        {
                            "id": feature["id"],
                            "importance": feature["importance"],
                            "status": "PASS",
                            "views": ["front", "perspective"],
                            "note": "Observed in fixed test evidence.",
                        }
                        for feature in scene["identity_features"]
                    ],
                    "overall_note": "All required fixture identity features are visible.",
                },
            )

        if glb_entry:
            semantic = {**asset["gltf_summary"], "bytes": glb_entry["bytes"]}
            self.write_json(
                evidence / "gltf-validation.json",
                {
                    "schema": "3d-craft.gltf-validation.v1",
                    "status": "PASS",
                    "asset": {"path": str(glb_file), "sha256": glb_entry["sha256"]},
                    "validator": {"issues": {"numErrors": 0}},
                    "semantic": semantic,
                },
            )

        if glb_entry and "browser.capture" in route["required_capabilities"]:
            desktop = self.file_entry(evidence / "browser-desktop.png", b"desktop")
            mobile = self.file_entry(evidence / "browser-mobile.png", b"mobile")
            desktop["visual_review"] = "PASS"
            mobile["visual_review"] = "PASS"
            self.write_json(
                evidence / "browser-runtime.json",
                {
                    "schema": "3d-craft.browser-runtime.v1",
                    "status": "ready",
                    "runtime": "browser67",
                    "console_errors": 0,
                    "asset": {"sha256": glb_entry["sha256"], "bytes": glb_entry["bytes"]},
                    "network": {"status": "PASS", "bytes": glb_entry["bytes"], "sha256": glb_entry["sha256"]},
                    "raf": {"delta": 10},
                    "metrics": {
                        "draw_calls": 1,
                        "textures": 0,
                        "frame_p50_ms": 7,
                        "frame_p95_ms": 8,
                        "geometries": 2,
                        "triangles": 3,
                    },
                    "performance_profile": self.performance_profile(),
                    "lifecycle": {
                        "remount_test_status": "PASS",
                        "ready_after_clean_reload": True,
                        "context_loss": {
                            "test_status": "PASS",
                            "supported": True,
                            "losses": 1,
                            "restores": 1,
                            "ready_after_restore": True,
                            "raf_resumed_after_restore": True,
                        },
                        "resource_stability": self.resource_stability(),
                    },
                    "cross_runtime": {"required_node_coverage_percent": 100, "bbox_drift_percent": 0.1},
                    "desktop_screenshot": desktop,
                    "responsive_layout": {"status": "PASS", "horizontal_overflow": False},
                    "mobile_screenshot": mobile,
                    "warnings": [],
                    "unverified": [],
                },
            )
        return {"source": source, "blend": blend_file, "glb": glb_file, "route": route}

    def test_route_selects_bridge_references_and_gates(self) -> None:
        payload = self.run_cli("route", "--target", "bridge", "--intent", "build", "--profile", "product-asset", "--quality-tier", "production", "--authoring-mode", "hybrid", "--evidence-level", "assured")
        self.assertEqual(payload["schema"], "3d-craft.route.v1")
        self.assertIn("gltf-web-handoff.md", payload["selected_references"])
        self.assertIn("web_runtime", payload["hard_gates"])
        self.assertIn("browser.capture", payload["required_capabilities"])
        self.assertIn("blender.export", payload["required_capabilities"])

    def test_validate_intent_does_not_require_mutating_blender_execution(self) -> None:
        payload = self.run_cli("route", "--target", "bridge", "--intent", "validate", "--evidence-level", "static")
        self.assertNotIn("blender.execute", payload["required_capabilities"])
        self.assertNotIn("blender.export", payload["required_capabilities"])

    def test_static_blender_route_excludes_browser(self) -> None:
        payload = self.run_cli("route", "--target", "blender", "--evidence-level", "static")
        self.assertNotIn("browser.capture", payload["required_capabilities"])
        self.assertNotIn("gltf", payload["hard_gates"])

    def test_route_rejects_incoherent_target_evidence_pair(self) -> None:
        result = subprocess.run(
            ["python3", str(CLI), "route", "--target", "web3d", "--evidence-level", "rendered", "--json"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("rendered-only", result.stderr)

    def test_init_run_requires_absolute_explicit_directory(self) -> None:
        result = subprocess.run(["python3", str(CLI), "init-run", "--project-key", "fixture", "--run-dir", "relative", "--json"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("must be absolute", result.stderr)

    def test_init_run_rejects_unsafe_run_id_and_nonempty_directory(self) -> None:
        unsafe = subprocess.run(
            ["python3", str(CLI), "init-run", "--project-key", "fixture", "--run-id", "../../escape", "--json"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(unsafe.returncode, 2)
        self.assertIn("run-id must match", unsafe.stderr)
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            (run_dir / "stale.txt").write_text("stale", encoding="utf-8")
            result = subprocess.run(
                ["python3", str(CLI), "init-run", "--project-key", "fixture", "--run-dir", str(run_dir), "--json"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("absent or empty", result.stderr)

    def test_init_run_creates_external_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            payload = self.run_cli("init-run", "--project-key", "fixture", "--run-dir", directory)
            run = json.loads((Path(directory) / "run.json").read_text())
            self.assertEqual(payload["status"], "pass")
            self.assertEqual(run["schema"], "3d-craft.run.v1")
            self.assertLessEqual(len(run["repairs"]), 3)
            self.assertTrue((Path(directory) / "evidence").is_dir())

    def test_bind_asset_builds_manifest_and_scene_hash_from_observed_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            fixture = self.create_valid_run(run_dir, evidence_level="rendered")
            (run_dir / "asset.json").unlink()
            run_path = run_dir / "run.json"
            run = json.loads(run_path.read_text())
            run["input_hashes"] = {}
            self.write_json(run_path, run)
            payload = self.run_cli(
                "bind-asset",
                "--run-dir",
                str(run_dir),
                "--source",
                str(fixture["source"]),
                "--license",
                "MIT",
                "--license-subject",
                "fixture",
                "--license-source",
                "original test fixture",
            )
            asset = json.loads((run_dir / "asset.json").read_text())
            rebound_run = json.loads(run_path.read_text())
            self.assertEqual(payload["status"], "pass")
            self.assertEqual(asset["derived"][1]["path"], str((run_dir / "assets" / "asset.glb").resolve()))
            self.assertEqual(rebound_run["input_hashes"]["scene_contract"], hashlib.sha256((run_dir / "scene.json").read_bytes()).hexdigest())
            self.assertEqual(self.run_cli("validate", "--run-dir", str(run_dir))["status"], "PASS")

    def test_bridge_assured_validation_binds_fixed_view_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            self.create_valid_run(run_dir)
            passing = self.run_cli("validate", "--run-dir", str(run_dir))
            self.assertEqual(passing["status"], "PASS")
            blender_commands = [command for command in passing["delivery"]["commands"] if command.startswith("blender ")]
            self.assertTrue(blender_commands)
            self.assertTrue(all("--python-exit-code 2" in command for command in blender_commands))
            validated_run = json.loads((run_dir / "run.json").read_text())
            self.assertEqual(validated_run["unverified"], [])
            self.assertTrue(all(value == "available" for value in validated_run["capabilities"].values()))
            (run_dir / "evidence" / "front.png").write_bytes(b"tampered")
            failing = self.run_cli("validate", "--run-dir", str(run_dir), expected=2)
            identity = next(item for item in failing["gates"] if item["id"] == "identity")
            self.assertEqual(identity["status"], "FAIL")

    def test_static_blender_validation_remains_unverified_without_visual_identity_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            self.create_valid_run(run_dir, target="blender", evidence_level="static")
            payload = self.run_cli("validate", "--run-dir", str(run_dir), expected=2)
            self.assertEqual(payload["status"], "UNVERIFIED")
            self.assertEqual(
                [item["id"] for item in payload["gates"]],
                ["authority", "reproduction", "scene_integrity", "identity", "delivery"],
            )
            identity = next(item for item in payload["gates"] if item["id"] == "identity")
            self.assertEqual(identity["status"], "UNVERIFIED")

    def test_visual_review_template_is_bound_and_does_not_claim_a_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            self.create_valid_run(run_dir, evidence_level="rendered")
            (run_dir / "evidence" / "visual-review.json").unlink()
            payload = self.run_cli(
                "init-visual-review",
                "--run-dir",
                str(run_dir),
                "--reviewer-name",
                "Codex",
            )
            review = json.loads((run_dir / "evidence" / "visual-review.json").read_text())
            self.assertEqual(payload["status"], "pass")
            self.assertEqual(review["status"], "UNVERIFIED")
            self.assertIsNone(review["reviewed_at"])
            validation = self.run_cli("validate", "--run-dir", str(run_dir), expected=2)
            identity = next(item for item in validation["gates"] if item["id"] == "identity")
            self.assertEqual(identity["status"], "UNVERIFIED")

    def test_authority_fails_when_source_bytes_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            fixture = self.create_valid_run(run_dir, target="blender", evidence_level="static")
            Path(fixture["source"]).write_bytes(b"changed")
            payload = self.run_cli("validate", "--run-dir", str(run_dir), expected=2)
            authority = next(item for item in payload["gates"] if item["id"] == "authority")
            self.assertEqual(authority["status"], "FAIL")

    def test_validate_fails_closed_for_malformed_nested_evidence(self) -> None:
        mutations = (
            ("run.json", lambda value: value.update({"capabilities": "invalid"})),
            ("asset.json", lambda value: value.update({"source": "invalid"})),
            (
                "evidence/gltf-validation.json",
                lambda value: value.update({"validator": "invalid", "semantic": "invalid"}),
            ),
            (
                "evidence/browser-runtime.json",
                lambda value: value.update(
                    {
                        "asset": "invalid",
                        "cross_runtime": "invalid",
                        "metrics": "invalid",
                        "network": "invalid",
                        "raf": "invalid",
                        "lifecycle": "invalid",
                        "responsive_layout": "invalid",
                    }
                ),
            ),
        )
        for relative, mutate in mutations:
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as directory:
                run_dir = Path(directory)
                self.create_valid_run(run_dir)
                path = run_dir / relative
                value = json.loads(path.read_text())
                mutate(value)
                self.write_json(path, value)
                payload = self.run_cli("validate", "--run-dir", str(run_dir), expected=2)
                self.assertEqual(payload["status"], "FAIL")

    def test_authority_rejects_required_evidence_runtime_and_license_drift(self) -> None:
        mutations = (
            lambda run_dir, scene, asset: scene["required_evidence"].remove("gltf-validation"),
            lambda run_dir, scene, asset: scene.update({"runtime": {"engine": "none", "renderer": "none", "target_devices": []}}),
            lambda run_dir, scene, asset: scene.pop("topology_policy"),
            lambda run_dir, scene, asset: scene["identity_features"].append(dict(scene["identity_features"][0])),
            lambda run_dir, scene, asset: asset.update({"licenses": []}),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate.__code__.co_firstlineno), tempfile.TemporaryDirectory() as directory:
                run_dir = Path(directory)
                self.create_valid_run(run_dir, evidence_level="rendered")
                scene_path = run_dir / "scene.json"
                asset_path = run_dir / "asset.json"
                run_path = run_dir / "run.json"
                scene = json.loads(scene_path.read_text())
                asset = json.loads(asset_path.read_text())
                mutate(run_dir, scene, asset)
                self.write_json(scene_path, scene)
                self.write_json(asset_path, asset)
                run = json.loads(run_path.read_text())
                run["input_hashes"]["scene_contract"] = hashlib.sha256(scene_path.read_bytes()).hexdigest()
                self.write_json(run_path, run)
                payload = self.run_cli("validate", "--run-dir", str(run_dir), expected=2)
                authority = next(item for item in payload["gates"] if item["id"] == "authority")
                self.assertEqual(authority["status"], "FAIL")

    def test_visual_review_must_bind_the_current_render_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            self.create_valid_run(run_dir, evidence_level="rendered")
            render_path = run_dir / "evidence" / "render-evidence.json"
            render = json.loads(render_path.read_text())
            render["review_probe"] = "changed after visual assessment"
            self.write_json(render_path, render)
            payload = self.run_cli("validate", "--run-dir", str(run_dir), expected=2)
            identity = next(item for item in payload["gates"] if item["id"] == "identity")
            self.assertEqual(identity["status"], "FAIL")

    def test_visual_review_requires_exact_features_and_timezone(self) -> None:
        mutations = (
            lambda review: review["features"].append(
                {"id": "invented", "importance": "minor", "status": "PASS", "views": ["front"], "note": "not contracted"}
            ),
            lambda review: review.update({"reviewed_at": "2026-09-02T00:00:00"}),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate.__code__.co_firstlineno), tempfile.TemporaryDirectory() as directory:
                run_dir = Path(directory)
                self.create_valid_run(run_dir, evidence_level="rendered")
                review_path = run_dir / "evidence" / "visual-review.json"
                review = json.loads(review_path.read_text())
                mutate(review)
                self.write_json(review_path, review)
                payload = self.run_cli("validate", "--run-dir", str(run_dir), expected=2)
                identity = next(item for item in payload["gates"] if item["id"] == "identity")
                self.assertIn(identity["status"], {"FAIL", "UNVERIFIED"})

    def test_browser_screenshots_must_be_copied_into_run_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            self.create_valid_run(run_dir)
            report_path = run_dir / "evidence" / "browser-runtime.json"
            report = json.loads(report_path.read_text())
            external = run_dir / "external-browser.png"
            report["desktop_screenshot"] = self.file_entry(external, b"external")
            report["desktop_screenshot"]["visual_review"] = "PASS"
            self.write_json(report_path, report)
            payload = self.run_cli("validate", "--run-dir", str(run_dir), expected=2)
            cross_runtime = next(item for item in payload["gates"] if item["id"] == "cross_runtime")
            self.assertEqual(cross_runtime["status"], "FAIL")

    def test_bind_browser_evidence_seals_candidate_and_run_owned_pngs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            fixture = self.create_valid_run(run_dir)
            for path in (
                run_dir / "evidence" / "browser-runtime.json",
                run_dir / "evidence" / "browser-desktop.png",
                run_dir / "evidence" / "browser-mobile.png",
            ):
                path.unlink()
            desktop_source = run_dir / "source" / "browser67-desktop.png"
            mobile_source = run_dir / "source" / "browser67-mobile.png"
            self.write_png_header(desktop_source, 1440, 900)
            self.write_png_header(mobile_source, 390, 1269)
            draft_path = run_dir / "source" / "browser-observation.json"
            self.write_json(
                draft_path,
                self.browser_draft(
                    glb=fixture["glb"],
                    desktop=desktop_source,
                    mobile=mobile_source,
                ),
            )

            payload = self.run_cli(
                "bind-browser-evidence",
                "--run-dir",
                str(run_dir),
                "--observation",
                str(draft_path),
            )
            report_path = run_dir / "evidence" / "browser-runtime.json"
            report = json.loads(report_path.read_text())
            desktop_copy = run_dir / "evidence" / "browser-desktop.png"
            mobile_copy = run_dir / "evidence" / "browser-mobile.png"
            glb_bytes = Path(fixture["glb"]).read_bytes()
            self.assertEqual(payload["status"], "pass")
            self.assertEqual(report["asset"]["sha256"], hashlib.sha256(glb_bytes).hexdigest())
            self.assertEqual(report["network"]["sha256"], report["asset"]["sha256"])
            self.assertEqual(report["desktop_screenshot"]["dimensions"], [1440, 900])
            self.assertEqual(report["mobile_screenshot"]["dimensions"], [390, 1269])
            self.assertEqual(report["desktop_screenshot"]["path"], str(desktop_copy.resolve()))
            self.assertEqual(report["lifecycle"]["context_loss"]["test_status"], "PASS")
            self.assertEqual(report["performance_profile"]["source"], "viewer-observability")
            self.assertEqual(report["lifecycle"]["resource_stability"]["cycles"], 3)
            self.assertEqual(desktop_copy.read_bytes(), desktop_source.read_bytes())
            self.assertEqual(mobile_copy.read_bytes(), mobile_source.read_bytes())
            self.assertEqual(self.run_cli("validate", "--run-dir", str(run_dir))["status"], "PASS")

            before = report_path.read_bytes()
            repeated = subprocess.run(
                [
                    "python3",
                    str(CLI),
                    "bind-browser-evidence",
                    "--run-dir",
                    str(run_dir),
                    "--observation",
                    str(draft_path),
                    "--json",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(repeated.returncode, 2)
            self.assertIn("already exists", repeated.stderr)
            self.assertEqual(report_path.read_bytes(), before)

    def test_bind_browser_evidence_merges_and_seals_a_viewer_profile_observation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            fixture = self.create_valid_run(run_dir)
            for path in (
                run_dir / "evidence" / "browser-runtime.json",
                run_dir / "evidence" / "browser-desktop.png",
                run_dir / "evidence" / "browser-mobile.png",
            ):
                path.unlink()
            desktop_source = run_dir / "source" / "browser67-desktop.png"
            mobile_source = run_dir / "source" / "browser67-mobile.png"
            self.write_png_header(desktop_source, 1440, 900)
            self.write_png_header(mobile_source, 390, 1269)
            profile_source = run_dir / "source" / "web-profile-observation.json"
            self.write_json(profile_source, self.profile_observation(fixture["glb"]))
            draft = self.browser_draft(
                glb=fixture["glb"],
                desktop=desktop_source,
                mobile=mobile_source,
            )
            draft.pop("metrics")
            draft.pop("performance_profile")
            draft["lifecycle"].pop("resource_stability")
            draft["profile_observation_path"] = str(profile_source)
            draft_path = run_dir / "source" / "browser-observation.json"
            self.write_json(draft_path, draft)

            payload = self.run_cli(
                "bind-browser-evidence",
                "--run-dir",
                str(run_dir),
                "--observation",
                str(draft_path),
            )

            report = json.loads((run_dir / "evidence" / "browser-runtime.json").read_text())
            sealed_profile = run_dir / "evidence" / "browser-profile-observation.json"
            self.assertEqual(payload["profile_observation"], str(sealed_profile.resolve()))
            self.assertEqual(report["metrics"], self.profile_observation(fixture["glb"])["metrics"])
            self.assertEqual(report["performance_profile"]["test_status"], "PASS")
            self.assertEqual(report["lifecycle"]["resource_stability"]["cycles"], 3)
            self.assertEqual(report["profile_observation"]["path"], str(sealed_profile.resolve()))
            self.assertEqual(report["profile_observation"]["sha256"], hashlib.sha256(profile_source.read_bytes()).hexdigest())
            self.assertEqual(sealed_profile.read_bytes(), profile_source.read_bytes())
            run = json.loads((run_dir / "run.json").read_text())
            self.assertIn(
                {"kind": "browser-profile-observation", "path": "evidence/browser-profile-observation.json"},
                run["evidence"],
            )
            self.assertEqual(self.run_cli("validate", "--run-dir", str(run_dir))["status"], "PASS")
            original_report = json.dumps(report)
            sealed_bytes = sealed_profile.read_bytes()
            for case in ("metrics", "timing", "resources", "asset-url"):
                with self.subTest(report_drift=case):
                    changed = json.loads(original_report)
                    if case == "metrics":
                        changed["metrics"]["frame_p95_ms"] = 7.5
                        changed["performance_profile"]["frame_p95_ms"] = 7.5
                    elif case == "timing":
                        changed["performance_profile"]["completed_at_ms"] += 100
                    elif case == "resources":
                        changed["lifecycle"]["resource_stability"]["samples"][-1]["captured_at_ms"] += 100
                    else:
                        changed["asset"]["url"] = "/different-asset.glb"
                    self.write_json(run_dir / "evidence" / "browser-runtime.json", changed)
                    validation = self.run_cli("validate", "--run-dir", str(run_dir), expected=2)
                    self.assertEqual({g["id"]: g["status"] for g in validation["gates"]}["web_runtime"], "FAIL")
                    self.assertEqual(sealed_profile.read_bytes(), sealed_bytes)
            for case in ("malformed", "failed", "page-drift"):
                with self.subTest(sealed_content=case):
                    observation = json.loads(sealed_bytes)
                    if case == "malformed":
                        observation = {}
                    elif case == "failed":
                        observation = {
                            "schema": "3d-craft.web-profile-observation.v1",
                            "source": "viewer-observability",
                            "status": "FAIL",
                            "reason": "interrupted observation",
                        }
                    else:
                        observation["page"]["viewport"] = [800, 600]
                        observation["performance_profile"]["viewport"] = [800, 600]
                    self.write_json(sealed_profile, observation)
                    changed = json.loads(original_report)
                    changed["profile_observation"] = self.file_entry(sealed_profile)
                    self.write_json(run_dir / "evidence" / "browser-runtime.json", changed)
                    validation = self.run_cli("validate", "--run-dir", str(run_dir), expected=2)
                    self.assertEqual({g["id"]: g["status"] for g in validation["gates"]}["web_runtime"], "FAIL")
            sealed_profile.write_bytes(sealed_bytes)
            self.write_json(run_dir / "evidence" / "browser-runtime.json", report)
            sealed_profile.write_text("{}\n", encoding="utf-8")
            validation = self.run_cli("validate", "--run-dir", str(run_dir), expected=2)
            by_gate = {item["id"]: item["status"] for item in validation["gates"]}
            self.assertEqual(by_gate["web_runtime"], "FAIL")

    def test_linked_viewer_profile_rejects_mismatch_and_dual_authority_atomically(self) -> None:
        cases = ("asset-mismatch", "nested-failure", "dual-authority")
        for name in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                run_dir = Path(directory)
                fixture = self.create_valid_run(run_dir)
                for path in (
                    run_dir / "evidence" / "browser-runtime.json",
                    run_dir / "evidence" / "browser-desktop.png",
                    run_dir / "evidence" / "browser-mobile.png",
                ):
                    path.unlink()
                desktop = run_dir / "source" / "browser67-desktop.png"
                mobile = run_dir / "source" / "browser67-mobile.png"
                self.write_png_header(desktop, 1440, 900)
                self.write_png_header(mobile, 390, 1269)
                profile = self.profile_observation(fixture["glb"])
                if name == "asset-mismatch":
                    profile["asset"]["sha256"] = "0" * 64
                elif name == "nested-failure":
                    profile["resource_stability"] = {
                        "test_status": "FAIL",
                        "reason": "resource counters did not settle",
                    }
                profile_path = run_dir / "source" / "web-profile-observation.json"
                self.write_json(profile_path, profile)
                draft = self.browser_draft(glb=fixture["glb"], desktop=desktop, mobile=mobile)
                draft["profile_observation_path"] = str(profile_path)
                if name != "dual-authority":
                    draft.pop("metrics")
                    draft.pop("performance_profile")
                    draft["lifecycle"].pop("resource_stability")
                draft_path = run_dir / "source" / "browser-observation.json"
                self.write_json(draft_path, draft)
                result = subprocess.run(
                    [
                        "python3",
                        str(CLI),
                        "bind-browser-evidence",
                        "--run-dir",
                        str(run_dir),
                        "--observation",
                        str(draft_path),
                        "--json",
                    ],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 2)
                expected = {
                    "asset-mismatch": "does not match",
                    "nested-failure": "must contain passing nested observations",
                    "dual-authority": "must be omitted",
                }[name]
                self.assertIn(expected, result.stderr)
                self.assertFalse((run_dir / "evidence" / "browser-runtime.json").exists())
                self.assertFalse((run_dir / "evidence" / "browser-profile-observation.json").exists())

    def test_bind_browser_evidence_rejects_invalid_or_mismatched_samples_atomically(self) -> None:
        cases = (
            ("hidden", {"desktop_visibility": "hidden"}, (1440, 900), "INVALID SAMPLE"),
            ("network", {"network_sha256": "0" * 64}, (1440, 900), "do not match"),
            ("viewport", {}, (1439, 900), "PNG dimensions"),
        )
        for name, draft_options, desktop_size, expected_error in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                run_dir = Path(directory)
                fixture = self.create_valid_run(run_dir)
                for path in (
                    run_dir / "evidence" / "browser-runtime.json",
                    run_dir / "evidence" / "browser-desktop.png",
                    run_dir / "evidence" / "browser-mobile.png",
                ):
                    path.unlink()
                desktop_source = run_dir / "source" / "browser67-desktop.png"
                mobile_source = run_dir / "source" / "browser67-mobile.png"
                self.write_png_header(desktop_source, *desktop_size)
                self.write_png_header(mobile_source, 390, 1269)
                draft_path = run_dir / "source" / "browser-observation.json"
                self.write_json(
                    draft_path,
                    self.browser_draft(
                        glb=fixture["glb"],
                        desktop=desktop_source,
                        mobile=mobile_source,
                        **draft_options,
                    ),
                )
                result = subprocess.run(
                    [
                        "python3",
                        str(CLI),
                        "bind-browser-evidence",
                        "--run-dir",
                        str(run_dir),
                        "--observation",
                        str(draft_path),
                        "--json",
                    ],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 2)
                self.assertIn(expected_error, result.stderr)
                self.assertFalse((run_dir / "evidence" / "browser-runtime.json").exists())
                self.assertFalse((run_dir / "evidence" / "browser-desktop.png").exists())
                self.assertFalse((run_dir / "evidence" / "browser-mobile.png").exists())

    def test_bind_browser_evidence_preserves_an_honest_capture_blocker_without_fake_pngs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            fixture = self.create_valid_run(run_dir)
            for path in (
                run_dir / "evidence" / "browser-runtime.json",
                run_dir / "evidence" / "browser-desktop.png",
                run_dir / "evidence" / "browser-mobile.png",
            ):
                path.unlink()
            draft = self.browser_draft(
                glb=fixture["glb"],
                desktop=run_dir / "unused-desktop.png",
                mobile=run_dir / "unused-mobile.png",
            )
            draft["status"] = "BLOCKED"
            draft["page_status"] = "ready"
            draft["blocker"] = "browser.capture timed out"
            draft.pop("desktop_screenshot")
            draft.pop("mobile_screenshot")
            draft_path = run_dir / "source" / "browser-observation.json"
            self.write_json(draft_path, draft)

            payload = self.run_cli(
                "bind-browser-evidence",
                "--run-dir",
                str(run_dir),
                "--observation",
                str(draft_path),
            )
            self.assertEqual(payload["screenshots"], [])
            report = json.loads((run_dir / "evidence" / "browser-runtime.json").read_text())
            self.assertNotIn("desktop_screenshot", report)
            validation = self.run_cli("validate", "--run-dir", str(run_dir), expected=2)
            by_gate = {item["id"]: item["status"] for item in validation["gates"]}
            self.assertEqual(by_gate["cross_runtime"], "BLOCKED")
            self.assertEqual(by_gate["web_runtime"], "BLOCKED")
            self.assertEqual(by_gate["delivery"], "BLOCKED")

    def test_browser_blocker_propagates_without_becoming_a_page_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            self.create_valid_run(run_dir)
            report_path = run_dir / "evidence" / "browser-runtime.json"
            report = json.loads(report_path.read_text())
            report["status"] = "BLOCKED"
            report["page_status"] = "ready"
            report["blocker"] = "browser.capture timed out"
            self.write_json(report_path, report)
            payload = self.run_cli("validate", "--run-dir", str(run_dir), expected=2)
            by_gate = {item["id"]: item["status"] for item in payload["gates"]}
            self.assertEqual(by_gate["cross_runtime"], "BLOCKED")
            self.assertEqual(by_gate["web_runtime"], "BLOCKED")
            self.assertEqual(by_gate["delivery"], "BLOCKED")

    def test_context_loss_failure_prevents_web_runtime_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            self.create_valid_run(run_dir)
            report_path = run_dir / "evidence" / "browser-runtime.json"
            report = json.loads(report_path.read_text())
            report["lifecycle"]["context_loss"] = {
                "test_status": "FAIL",
                "supported": True,
                "losses": 1,
                "restores": 0,
                "ready_after_restore": False,
                "raf_resumed_after_restore": False,
            }
            self.write_json(report_path, report)
            payload = self.run_cli("validate", "--run-dir", str(run_dir), expected=2)
            by_gate = {item["id"]: item["status"] for item in payload["gates"]}
            self.assertEqual(by_gate["web_runtime"], "FAIL")

    def test_context_loss_pass_requires_observed_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            self.create_valid_run(run_dir)
            report_path = run_dir / "evidence" / "browser-runtime.json"
            report = json.loads(report_path.read_text())
            report["lifecycle"]["context_loss"]["restores"] = 0
            self.write_json(report_path, report)
            payload = self.run_cli("validate", "--run-dir", str(run_dir), expected=2)
            by_gate = {item["id"]: item["status"] for item in payload["gates"]}
            self.assertEqual(by_gate["web_runtime"], "FAIL")

    def test_bind_browser_evidence_rejects_forged_performance_profiles(self) -> None:
        mutations = (
            (
                "short-window",
                lambda draft: draft["performance_profile"].update({"completed_at_ms": 13099}),
                "performance profile",
            ),
            (
                "summary-mismatch",
                lambda draft: draft["metrics"].update({"frame_p95_ms": 9}),
                "do not match",
            ),
            (
                "resource-delta-mismatch",
                lambda draft: draft["lifecycle"]["resource_stability"].update({"geometry_delta": 1}),
                "deltas do not match",
            ),
        )
        for name, mutate, expected_error in mutations:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                run_dir = Path(directory)
                fixture = self.create_valid_run(run_dir)
                for path in (
                    run_dir / "evidence" / "browser-runtime.json",
                    run_dir / "evidence" / "browser-desktop.png",
                    run_dir / "evidence" / "browser-mobile.png",
                ):
                    path.unlink()
                desktop = run_dir / "source" / "browser67-desktop.png"
                mobile = run_dir / "source" / "browser67-mobile.png"
                self.write_png_header(desktop, 1440, 900)
                self.write_png_header(mobile, 390, 1269)
                draft = self.browser_draft(glb=fixture["glb"], desktop=desktop, mobile=mobile)
                mutate(draft)
                draft_path = run_dir / "source" / "browser-observation.json"
                self.write_json(draft_path, draft)
                result = subprocess.run(
                    [
                        "python3",
                        str(CLI),
                        "bind-browser-evidence",
                        "--run-dir",
                        str(run_dir),
                        "--observation",
                        str(draft_path),
                        "--json",
                    ],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 2)
                self.assertIn(expected_error, result.stderr)
                self.assertFalse((run_dir / "evidence" / "browser-runtime.json").exists())

    def test_performance_profile_budget_and_legacy_compatibility(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            self.create_valid_run(run_dir)
            report_path = run_dir / "evidence" / "browser-runtime.json"
            report = json.loads(report_path.read_text())
            report["lifecycle"]["resource_stability"] = self.resource_stability(geometry_delta=1)
            self.write_json(report_path, report)
            payload = self.run_cli("validate", "--run-dir", str(run_dir), expected=2)
            by_gate = {item["id"]: item["status"] for item in payload["gates"]}
            self.assertEqual(by_gate["web_runtime"], "FAIL")

        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            self.create_valid_run(run_dir)
            report_path = run_dir / "evidence" / "browser-runtime.json"
            report = json.loads(report_path.read_text())
            report.pop("performance_profile")
            report["lifecycle"].pop("resource_stability")
            self.write_json(report_path, report)
            payload = self.run_cli("validate", "--run-dir", str(run_dir), expected=2)
            by_gate = {item["id"]: item["status"] for item in payload["gates"]}
            self.assertEqual(by_gate["web_runtime"], "UNVERIFIED")

            scene_path = run_dir / "scene.json"
            scene = json.loads(scene_path.read_text())
            scene["budgets"].pop("performance_profile")
            self.write_json(scene_path, scene)
            scene_sha256 = hashlib.sha256(scene_path.read_bytes()).hexdigest()
            run_path = run_dir / "run.json"
            run = json.loads(run_path.read_text())
            run["input_hashes"]["scene_contract"] = scene_sha256
            self.write_json(run_path, run)
            render_path = run_dir / "evidence" / "render-evidence.json"
            render = json.loads(render_path.read_text())
            render["scene_contract"]["sha256"] = scene_sha256
            self.write_json(render_path, render)
            review_path = run_dir / "evidence" / "visual-review.json"
            review = json.loads(review_path.read_text())
            review["candidate"]["render_evidence_sha256"] = hashlib.sha256(render_path.read_bytes()).hexdigest()
            self.write_json(review_path, review)
            self.assertEqual(self.run_cli("validate", "--run-dir", str(run_dir))["status"], "PASS")

    def test_gltf_gate_fails_when_report_targets_another_asset(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            self.create_valid_run(run_dir, evidence_level="static")
            report_path = run_dir / "evidence" / "gltf-validation.json"
            report = json.loads(report_path.read_text())
            report["asset"]["sha256"] = "0" * 64
            self.write_json(report_path, report)
            payload = self.run_cli("validate", "--run-dir", str(run_dir), expected=2)
            gltf_gate = next(item for item in payload["gates"] if item["id"] == "gltf")
            self.assertEqual(gltf_gate["status"], "FAIL")

    def test_provisional_budget_remains_unverified(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            self.create_valid_run(run_dir, evidence_level="static")
            scene_path = run_dir / "scene.json"
            scene = json.loads(scene_path.read_text())
            scene["budgets"]["status"] = "provisional"
            self.write_json(scene_path, scene)
            run_path = run_dir / "run.json"
            run = json.loads(run_path.read_text())
            run["input_hashes"]["scene_contract"] = hashlib.sha256(scene_path.read_bytes()).hexdigest()
            self.write_json(run_path, run)
            payload = self.run_cli("validate", "--run-dir", str(run_dir), expected=2)
            gltf_gate = next(item for item in payload["gates"] if item["id"] == "gltf")
            self.assertEqual(gltf_gate["status"], "UNVERIFIED")


if __name__ == "__main__":
    unittest.main()
