from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.design_craft.routing.manifest import (
    ROUTE_PACK_MANIFEST_PATH,
    ROUTE_PACK_MANIFEST_SCHEMA,
    load_route_pack_files,
)
from tools.design_craft.routing.export import copy_pack, write_manifest as write_export_manifest
from tools.design_craft.routing.report import build_manifest
from tools.design_craft.routing.runtime_batch import (
    RUNTIME_PROBE_WORKERS,
    submit_runtime_probe_batch,
)


class PendingFuture:
    def result(self, *args: object, **kwargs: object) -> object:
        raise AssertionError("probe submission must not wait for a result")


class RecordingExecutor:
    def __init__(self) -> None:
        self.submissions: list[
            tuple[object, tuple[object, ...], dict[str, object], PendingFuture]
        ] = []

    def submit(
        self,
        function: object,
        *args: object,
        **kwargs: object,
    ) -> PendingFuture:
        future = PendingFuture()
        self.submissions.append((function, args, kwargs, future))
        return future


def write_manifest(root: Path, files: list[dict[str, object]]) -> Path:
    path = root / ROUTE_PACK_MANIFEST_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema": ROUTE_PACK_MANIFEST_SCHEMA,
                "version": 1,
                "files": files,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def valid_files() -> list[dict[str, object]]:
    return [
        {
            "path": ROUTE_PACK_MANIFEST_PATH,
            "required": True,
            "route_pack": True,
            "snapshot": True,
            "kind": "route-manifest",
        },
        {
            "path": "tools/frontend_route_plan.sh",
            "required": True,
            "route_pack": True,
            "snapshot": True,
            "kind": "route-planner",
        },
    ]


class RoutePackManifestTests(unittest.TestCase):
    def test_runtime_probes_are_submitted_as_one_non_blocking_batch(self) -> None:
        executor = RecordingExecutor()
        requests = [
            (["--browser-context", "external"], None, None),
            (["--browser-context", "local"], "gpt-5.6-sol", "max"),
        ]

        batch = submit_runtime_probe_batch(executor, Path("/route-pack"), requests)

        self.assertEqual(RUNTIME_PROBE_WORKERS, 11)
        self.assertEqual(len(executor.submissions), 4 + len(requests) + 1)
        futures = [submission[3] for submission in executor.submissions]
        self.assertIs(batch.schema, futures[0])
        self.assertIs(batch.telemetry, futures[1])
        self.assertIs(batch.browser_capture, futures[2])
        self.assertIs(batch.browser_receipt, futures[3])
        self.assertEqual(batch.routes, tuple(futures[4:-1]))
        self.assertIs(batch.model_catalog, futures[-1])

    def test_valid_manifest_returns_declared_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            manifest_path = write_manifest(root, valid_files())
            planner = root / "tools/frontend_route_plan.sh"
            planner.write_text("#!/usr/bin/env bash\n", encoding="utf-8")

            files, metadata = load_route_pack_files(root)

            self.assertEqual([item.path for item in files], [
                ROUTE_PACK_MANIFEST_PATH,
                "tools/frontend_route_plan.sh",
            ])
            self.assertEqual(metadata["selected_files"], 2)
            self.assertEqual(metadata["required_files"], 2)
            self.assertEqual(len(metadata["sha256"]), 64)
            self.assertTrue(manifest_path.is_file())

    def test_duplicate_and_invalid_types_fail_closed(self) -> None:
        cases = []
        duplicate = valid_files()
        duplicate.append(dict(duplicate[-1]))
        cases.append((duplicate, "duplicate path"))
        invalid_type = valid_files()
        invalid_type[-1]["required"] = "yes"
        cases.append((invalid_type, "required must be boolean"))
        missing_snapshot = valid_files()
        missing_snapshot[-1]["snapshot"] = False
        cases.append((missing_snapshot, "must also be snapshot=true"))

        for files, message in cases:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                write_manifest(root, files)
                with self.assertRaisesRegex(ValueError, message):
                    load_route_pack_files(root)

    def test_missing_required_file_is_a_structural_failure(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            write_manifest(root, valid_files())

            payload = build_manifest(root, include_semantic=False)

            self.assertEqual(payload["status"], "missing-required")
            self.assertEqual(
                payload["summary"]["missing_required"],
                ["tools/frontend_route_plan.sh"],
            )

    def test_export_rejects_source_changed_after_manifest_build(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            temporary = Path(raw)
            source = temporary / "source"
            export = temporary / "export"
            write_manifest(source, valid_files())
            planner = source / "tools/frontend_route_plan.sh"
            planner.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            payload = build_manifest(source, include_semantic=False)
            planner.write_text("#!/usr/bin/env bash\necho changed\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "changed after validation"):
                copy_pack(source, export, payload["files"], dry_run=False)

            self.assertFalse((export / ROUTE_PACK_MANIFEST_PATH).exists())
            self.assertFalse((export / "tools/frontend_route_plan.sh").exists())

    def test_manifest_write_replaces_symlink_without_touching_target(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            outside = root / "outside.json"
            outside.write_text('{"outside": true}\n', encoding="utf-8")
            manifest = root / "export/manifest.json"
            manifest.parent.mkdir()
            manifest.symlink_to(outside)

            write_export_manifest({"status": "ok"}, manifest, dry_run=False)

            self.assertFalse(manifest.is_symlink())
            self.assertEqual(
                json.loads(manifest.read_text(encoding="utf-8")),
                {"status": "ok"},
            )
            self.assertEqual(outside.read_text(encoding="utf-8"), '{"outside": true}\n')


if __name__ == "__main__":
    unittest.main()
