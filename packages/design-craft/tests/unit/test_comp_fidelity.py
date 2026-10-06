from __future__ import annotations

import hashlib
import json
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch

from tools.design_craft.repo import REPO_ROOT


LIB_DIR = REPO_ROOT / "skills/design-craft/lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import design_craft.comp_fidelity as comp_module
from design_craft.comp_fidelity import (
    CompFidelityError,
    MAX_FILE_BYTES,
    PNG_SIGNATURE,
    PngImage,
    _chunk,
    compare,
    load_spec,
    read_png,
    validate_report,
    write_png,
)


def spec_payload(width: int = 3, height: int = 2) -> dict[str, object]:
    return {
        "schema": "design-craft.comp-fidelity-spec.v1",
        "case_id": "fixture",
        "coordinate_space": {"width": width, "height": height},
        "changed_pixel_delta": 0.01,
        "regions": [
            {
                "id": "primary",
                "box": [0, 0, width, height],
                "salience": "primary",
                "dimensions": ["geometry", "type"],
                "note": "whole fixture",
            }
        ],
    }


class CompFidelityTests(unittest.TestCase):
    def test_snapshot_requests_binary_mode_when_platform_exposes_it(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "bytes.bin"
            payload = b"\x00\r\n\x1a\xff"
            path.write_bytes(payload)
            original_open = comp_module.os.open
            native_binary_flag = getattr(comp_module.os, "O_BINARY", 0)
            binary_flag = native_binary_flag or 0x8000
            observed_flags: list[int] = []

            def open_without_synthetic_flag(path_value: Path, flags: int) -> int:
                observed_flags.append(flags)
                platform_flags = flags if native_binary_flag else flags & ~binary_flag
                return original_open(path_value, platform_flags)

            with (
                patch.object(comp_module.os, "O_BINARY", binary_flag, create=True),
                patch.object(comp_module.os, "open", side_effect=open_without_synthetic_flag),
            ):
                snapshot = comp_module._snapshot_file(path, label="binary fixture")

            self.assertEqual(snapshot.data, payload)
            self.assertEqual(len(observed_flags), 1)
            self.assertTrue(observed_flags[0] & binary_flag)

    def test_png_round_trip_preserves_rgba(self) -> None:
        image = PngImage(2, 1, bytes((1, 2, 3, 4, 250, 240, 230, 220)))
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "image.png"
            write_png(path, image)
            loaded = read_png(path)
        self.assertEqual(loaded, image)

    def test_png_rejects_idat_before_ihdr(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "invalid-order.png"
            ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
            path.write_bytes(
                PNG_SIGNATURE
                + _chunk(b"IDAT", zlib.compress(bytes((0, 1, 2, 3))))
                + _chunk(b"IHDR", ihdr)
                + _chunk(b"IEND", b"")
            )

            with self.assertRaisesRegex(CompFidelityError, "IDAT order"):
                read_png(path)

    def test_compare_is_measurement_only_and_hash_validated(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            reference = root / "reference.png"
            rendered = root / "rendered.png"
            spec = root / "spec.json"
            write_png(reference, PngImage(3, 2, bytes((0, 0, 0, 255)) * 6))
            write_png(rendered, PngImage(3, 2, bytes((20, 10, 0, 255)) * 6))
            spec.write_text(json.dumps(spec_payload()), encoding="utf-8")

            report = compare(
                reference_path=reference,
                rendered_path=rendered,
                spec_path=spec,
                output_dir=root / "evidence",
                observed_at="2026-08-29T00:00:00Z",
            )
            validation = validate_report(
                root / "evidence/report.json",
                reference_path=reference,
                rendered_path=rendered,
                spec_path=spec,
                strict=True,
            )

            self.assertEqual(report["verdict"], "measurement_only")
            self.assertGreater(report["overall_metrics"]["mean_delta"], 0)
            self.assertEqual(validation["artifact_count"], 4)

            persisted = root / "evidence/report.json"
            tampered = json.loads(persisted.read_text(encoding="utf-8"))
            tampered["overall_metrics"]["mean_delta"] = 0.0
            persisted.write_text(json.dumps(tampered), encoding="utf-8")
            with self.assertRaisesRegex(CompFidelityError, "overall metrics"):
                validate_report(
                    persisted,
                    reference_path=reference,
                    rendered_path=rendered,
                    spec_path=spec,
                    strict=True,
                )

    def test_compare_binds_metrics_and_hash_to_one_input_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            reference = root / "reference.png"
            rendered = root / "rendered.png"
            spec = root / "spec.json"
            black = PngImage(3, 2, bytes((0, 0, 0, 255)) * 6)
            white = PngImage(3, 2, bytes((255, 255, 255, 255)) * 6)
            write_png(reference, black)
            write_png(rendered, white)
            original_hash = hashlib.sha256(reference.read_bytes()).hexdigest()
            spec.write_text(json.dumps(spec_payload()), encoding="utf-8")
            original_metrics = comp_module._metrics
            mutated = False

            def mutate_after_snapshot(*args, **kwargs):
                nonlocal mutated
                if not mutated:
                    write_png(reference, white)
                    mutated = True
                return original_metrics(*args, **kwargs)

            with patch.object(comp_module, "_metrics", side_effect=mutate_after_snapshot):
                report = compare(
                    reference_path=reference,
                    rendered_path=rendered,
                    spec_path=spec,
                    output_dir=root / "evidence",
                    observed_at="2026-08-29T00:00:00Z",
                )

            self.assertEqual(report["inputs"]["reference"]["sha256"], original_hash)
            self.assertEqual(report["overall_metrics"]["mean_delta"], 1.0)
            with self.assertRaisesRegex(CompFidelityError, "reference input record"):
                validate_report(
                    root / "evidence/report.json",
                    reference_path=reference,
                    rendered_path=rendered,
                    spec_path=spec,
                    strict=True,
                )

    def test_spec_rejects_region_outside_coordinate_space(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "spec.json"
            payload = spec_payload()
            payload["regions"][0]["box"] = [2, 0, 2, 2]
            path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(CompFidelityError, "leaves the coordinate space"):
                load_spec(path)

    def test_spec_rejects_unbounded_overlapping_region_work(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "spec.json"
            payload = spec_payload(2000, 2000)
            payload["regions"] = [
                {
                    "id": f"region-{index}",
                    "box": [0, 0, 2000, 2000],
                    "salience": "primary",
                    "dimensions": ["geometry"],
                    "note": "bounded work fixture",
                }
                for index in range(5)
            ]
            path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(CompFidelityError, "processing bound"):
                load_spec(path)

    def test_compare_refuses_dimension_coercion_and_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            reference = root / "reference.png"
            rendered = root / "rendered.png"
            spec = root / "spec.json"
            write_png(reference, PngImage(3, 2, bytes((0, 0, 0, 255)) * 6))
            write_png(rendered, PngImage(2, 2, bytes((0, 0, 0, 255)) * 4))
            spec.write_text(json.dumps(spec_payload()), encoding="utf-8")
            with self.assertRaisesRegex(CompFidelityError, "must match exactly"):
                compare(reference_path=reference, rendered_path=rendered, spec_path=spec, output_dir=root / "evidence")

            write_png(rendered, PngImage(3, 2, bytes((0, 0, 0, 255)) * 6))
            (root / "evidence").mkdir()
            with self.assertRaisesRegex(CompFidelityError, "must not already exist"):
                compare(reference_path=reference, rendered_path=rendered, spec_path=spec, output_dir=root / "evidence")

    def test_non_strict_validation_rejects_missing_report_contract_fields(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            manifest = root / "report.json"
            manifest.write_text(
                json.dumps({"schema": "design-craft.comp-fidelity-report.v1", "verdict": "measurement_only"}),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(CompFidelityError, "fields mismatch"):
                validate_report(manifest)

    def test_artifact_metadata_rejects_boolean_dimensions(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            reference = root / "reference.png"
            rendered = root / "rendered.png"
            spec = root / "spec.json"
            image = PngImage(1, 1, bytes((1, 2, 3, 255)))
            write_png(reference, image)
            write_png(rendered, image)
            spec.write_text(json.dumps(spec_payload(1, 1)), encoding="utf-8")
            compare(
                reference_path=reference,
                rendered_path=rendered,
                spec_path=spec,
                output_dir=root / "evidence",
                observed_at="2026-08-29T00:00:00Z",
            )
            manifest = root / "evidence/report.json"
            report = json.loads(manifest.read_text(encoding="utf-8"))
            report["artifacts"]["heatmap"]["width"] = True
            manifest.write_text(json.dumps(report), encoding="utf-8")

            with self.assertRaisesRegex(CompFidelityError, "width must be a positive integer"):
                validate_report(manifest)

    def test_oversized_artifact_is_rejected_before_content_read(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            reference = root / "reference.png"
            rendered = root / "rendered.png"
            spec = root / "spec.json"
            image = PngImage(1, 1, bytes((1, 2, 3, 255)))
            write_png(reference, image)
            write_png(rendered, image)
            spec.write_text(json.dumps(spec_payload(1, 1)), encoding="utf-8")
            compare(
                reference_path=reference,
                rendered_path=rendered,
                spec_path=spec,
                output_dir=root / "evidence",
                observed_at="2026-08-29T00:00:00Z",
            )
            oversized = root / "evidence/oversized.png"
            with oversized.open("wb") as handle:
                handle.truncate(MAX_FILE_BYTES + 1)
            manifest = root / "evidence/report.json"
            report = json.loads(manifest.read_text(encoding="utf-8"))
            report["artifacts"]["heatmap"] = {
                "path": "oversized.png",
                "bytes": MAX_FILE_BYTES + 1,
                "sha256": "0" * 64,
                "width": 1,
                "height": 1,
            }
            manifest.write_text(json.dumps(report), encoding="utf-8")
            original_snapshot = comp_module._snapshot_file
            observed_paths: list[Path] = []

            def track_snapshot(path, **kwargs):
                observed_paths.append(Path(path))
                return original_snapshot(path, **kwargs)

            with patch.object(comp_module, "_snapshot_file", side_effect=track_snapshot):
                with self.assertRaisesRegex(CompFidelityError, "artifact bound"):
                    validate_report(manifest)

            self.assertNotIn(oversized, observed_paths)


if __name__ == "__main__":
    unittest.main()
