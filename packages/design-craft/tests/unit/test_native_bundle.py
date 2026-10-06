from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.design_craft.release.github_runs import (
    NATIVE_WORKFLOW_NAME,
    NATIVE_WORKFLOW_PATH,
    PHYSICAL_WORKFLOW_NAME,
    PHYSICAL_WORKFLOW_PATH,
    workflow_binding,
)
from tools.design_craft.release.integrity import repository_version, sha256_file
from tools.design_craft.release.native_bundle import (
    build_native_bundle,
    load_native_manifest,
    native_asset_names,
    validate_native_bundle,
    validate_outer_native_bindings,
)
from tools.design_craft.release.native_evidence import (
    EVIDENCE_SCHEMA,
    inspect_evidence_archive,
)


HEAD = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
VERSION = repository_version()


def artifact(role: str, path: Path) -> dict[str, object]:
    return {
        "role": role,
        "path": path.name,
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
    }


def write_evidence(root: Path, *, kind: str) -> None:
    root.mkdir(parents=True)
    platform = "ios" if kind == "ios_simulator" else "android"
    if kind == "ios_simulator":
        before = root / "before.png"
        after = root / "after.png"
        marker = root / "interaction.txt"
        launch = root / "launch.txt"
        before.write_bytes(b"\x89PNG\r\n\x1a\nbefore")
        after.write_bytes(b"\x89PNG\r\n\x1a\nafter")
        marker.write_text("Runtime interaction confirmed\n", encoding="utf-8")
        launch.write_text("fixture launched\n", encoding="utf-8")
        assertions = {
            "build_succeeded": True,
            "install_and_launch_succeeded": True,
            "runtime_interaction_observed": True,
            "before_and_after_screenshots_captured": True,
        }
        artifacts = [
            artifact("before_screenshot", before),
            artifact("after_screenshot", after),
            artifact("interaction_marker", marker),
            artifact("launch_log", launch),
        ]
        output_name = "ios-observed.json"
    else:
        before_xml = root / "before.xml"
        after_xml = root / "after.xml"
        screenshot = root / "after.png"
        launch = root / "launch.txt"
        before_xml.write_text(
            '<hierarchy><node content-desc="Native runtime evidence title" /></hierarchy>',
            encoding="utf-8",
        )
        after_xml.write_text(
            '<hierarchy><node text="Runtime interaction confirmed" /></hierarchy>',
            encoding="utf-8",
        )
        screenshot.write_bytes(b"\x89PNG\r\n\x1a\nafter")
        launch.write_text("fixture launched\n", encoding="utf-8")
        assertions = {
            "build_succeeded": True,
            "install_and_launch_succeeded": True,
            "accessibility_tree_observed": True,
            "interaction_observed": True,
            "screenshot_captured": True,
        }
        if kind == "android_device":
            assertions.update(
                {
                    "physical_device_confirmed": True,
                    "device_authorization_confirmed": True,
                }
            )
        artifacts = [
            artifact("before_accessibility_tree", before_xml),
            artifact("after_accessibility_tree", after_xml),
            artifact("after_screenshot", screenshot),
            artifact("launch_log", launch),
        ]
        output_name = (
            "real-device-observed.json"
            if kind == "android_device"
            else "android-observed.json"
        )
    selected_run = (
        physical_observation() if kind.endswith("_device") else run_observation()
    )
    payload = {
        "schema": EVIDENCE_SCHEMA,
        "platform": platform,
        "verified": True,
        "runtime_kind": kind,
        "evidence_level": "runtime_observed",
        "observed_at": "2026-01-01T00:00:00Z",
        "runtime_id_kind": "sha256",
        "runtime_id": "sha256:" + "a" * 64,
        "tool": "fixture",
        "source_commit": HEAD,
        "source_dirty": False,
        "skill_source_dirty": False,
        "repo_dirty": False,
        "skill_version": VERSION,
        "skill_tree_sha256": "b" * 64,
        "fixture_tree_sha256": "c" * 64,
        "contract_sha256": "d" * 64,
        "capture_context": "fixture",
        "workflow": workflow_binding(
            selected_run,
            kind="physical" if kind.endswith("_device") else "native",
        ),
        "commands": ["fixture command"],
        "assertions": assertions,
        "artifacts": artifacts,
    }
    (root / output_name).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def run_observation() -> dict[str, object]:
    repository = "example/design-craft"
    return {
        "id": 123,
        "attempt": 1,
        "workflow": NATIVE_WORKFLOW_PATH,
        "workflow_name": NATIVE_WORKFLOW_NAME,
        "event": "push",
        "head_branch": f"v{VERSION}",
        "head_sha": HEAD,
        "status": "completed",
        "conclusion": "success",
        "url": f"https://github.com/{repository}/actions/runs/123",
        "repository": repository,
    }


def physical_observation() -> dict[str, object]:
    repository = "example/design-craft"
    return {
        "id": 456,
        "attempt": 1,
        "workflow": PHYSICAL_WORKFLOW_PATH,
        "workflow_name": PHYSICAL_WORKFLOW_NAME,
        "event": "workflow_dispatch",
        "head_branch": "main",
        "head_sha": HEAD,
        "status": "completed",
        "conclusion": "success",
        "url": f"https://github.com/{repository}/actions/runs/456",
        "repository": repository,
    }


def fixture_sources(root: Path) -> tuple[Path, Path, Path]:
    ios = root / "sources/ios"
    android = root / "sources/android"
    physical = root / "sources/physical"
    write_evidence(ios, kind="ios_simulator")
    write_evidence(android, kind="android_emulator")
    write_evidence(physical, kind="android_device")
    return ios, android, physical


def build_fixture(root: Path, output: Path) -> dict[str, object]:
    ios, android, physical = fixture_sources(root)
    return build_native_bundle(
        output,
        run_observation(),
        physical_observation(),
        ios_source=ios,
        android_source=android,
        physical_device_source=physical,
        force=False,
        require_current_source=False,
    )


class NativeBundleTests(unittest.TestCase):
    def test_validation_inspects_the_archive_once(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            output = root / "output"
            build_fixture(root, output)
            with patch(
                "tools.design_craft.release.native_bundle.inspect_evidence_archive",
                wraps=inspect_evidence_archive,
            ) as inspected:
                result = validate_native_bundle(
                    output, require_current_source=False
                )
            self.assertTrue(result["ok"], result["errors"])
            self.assertEqual(inspected.call_count, 1)

    def test_double_build_is_byte_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            ios, android, physical = fixture_sources(root)
            outputs = (root / "output-a", root / "output-b")
            for output in outputs:
                result = build_native_bundle(
                    output,
                    run_observation(),
                    physical_observation(),
                    ios_source=ios,
                    android_source=android,
                    physical_device_source=physical,
                    force=False,
                    require_current_source=False,
                )
                self.assertTrue(result["ok"], result["errors"])
            for name in native_asset_names():
                self.assertEqual(
                    (outputs[0] / name).read_bytes(),
                    (outputs[1] / name).read_bytes(),
                )

    def test_manifest_and_checksum_tampering_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            output = root / "output"
            build_fixture(root, output)
            _, checksum_name, manifest_name = native_asset_names()
            checksum = output / checksum_name
            checksum.write_text("0" * 64 + "  invalid.tgz\n", encoding="utf-8")
            result = validate_native_bundle(output, require_current_source=False)
            self.assertFalse(result["ok"])
            self.assertTrue(any("checksum" in error for error in result["errors"]))
            build_native_bundle(
                output,
                run_observation(),
                physical_observation(),
                ios_source=root / "sources/ios",
                android_source=root / "sources/android",
                physical_device_source=root / "sources/physical",
                force=True,
                require_current_source=False,
            )
            manifest_path = output / manifest_name
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["unexpected"] = True
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = validate_native_bundle(output, require_current_source=False)
            self.assertFalse(result["ok"])
            self.assertTrue(any("fields mismatch" in error for error in result["errors"]))

    def test_existing_assets_require_force(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            output = root / "output"
            build_fixture(root, output)
            with self.assertRaises(FileExistsError):
                build_native_bundle(
                    output,
                    run_observation(),
                    physical_observation(),
                    ios_source=root / "sources/ios",
                    android_source=root / "sources/android",
                    physical_device_source=root / "sources/physical",
                    force=False,
                    require_current_source=False,
                )

    def test_symlinked_evidence_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            ios, android, physical = fixture_sources(root)
            evidence = ios / "ios-observed.json"
            target = root / "outside.json"
            target.write_bytes(evidence.read_bytes())
            evidence.unlink()
            evidence.symlink_to(target)
            with self.assertRaisesRegex(FileNotFoundError, "unsafe"):
                build_native_bundle(
                    root / "output",
                    run_observation(),
                    physical_observation(),
                    ios_source=ios,
                    android_source=android,
                    physical_device_source=physical,
                    force=False,
                    require_current_source=False,
                )

    def test_outer_and_inner_evidence_are_cryptographically_bound(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            output = root / "output"
            build_fixture(root, output)
            inner = load_native_manifest(output)
            inspection = inspect_evidence_archive(output / native_asset_names()[0])
            self.assertEqual(inspection.errors, ())
            outer_evidence: dict[str, object] = {}
            mapping = {
                "ios": "ios_simulator",
                "android": "android_emulator",
                "real_device": "physical_device",
            }
            for inner_key, outer_key in mapping.items():
                summary = inner["evidence"][inner_key]
                evidence = inspection.payloads[inner_key]
                outer_evidence[outer_key] = {
                    "native": outer_key,
                    "evidence_path": f"{outer_key}-observed.json",
                    "evidence_sha256": summary["sha256"],
                    "schema": summary["schema"],
                    "platform": summary["platform"],
                    "runtime_kind": summary["runtime_kind"],
                    "source_commit": summary["source_commit"],
                    "contract_sha256": summary["contract_sha256"],
                    "observed_at": evidence["observed_at"],
                    "workflow": evidence["workflow"],
                    "artifacts": [dict(item) for item in evidence["artifacts"]],
                }
            outer = {"source_commit": HEAD, "native_evidence": outer_evidence}
            self.assertEqual(
                validate_outer_native_bindings(outer, inner, inspection.payloads), []
            )
            outer_evidence["ios_simulator"]["evidence_sha256"] = "0" * 64
            errors = validate_outer_native_bindings(
                outer, inner, inspection.payloads
            )
            self.assertTrue(any("evidence_sha256" in error for error in errors))
            outer_evidence["ios_simulator"]["evidence_sha256"] = inner["evidence"][
                "ios"
            ]["sha256"]
            outer_evidence["ios_simulator"]["artifacts"][0]["sha256"] = "0" * 64
            errors = validate_outer_native_bindings(
                outer, inner, inspection.payloads
            )
            self.assertTrue(any("artifacts" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
