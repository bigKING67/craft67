from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from .export import copy_pack, write_manifest
from .manifest import ROUTE_PACK_MANIFEST_PATH, ROUTE_PACK_MANIFEST_SCHEMA
from .report import build_manifest


def self_check() -> int:
    with tempfile.TemporaryDirectory(prefix="design-craft-route-pack.") as tmp:
        root = Path(tmp) / "codex-home"
        fixture_files = [
            {
                "path": ROUTE_PACK_MANIFEST_PATH,
                "required": True,
                "kind": "route-manifest",
                "route_pack": True,
                "snapshot": True,
            },
            {
                "path": "tools/frontend_route_plan.sh",
                "required": True,
                "kind": "route-planner",
                "route_pack": True,
                "snapshot": True,
            },
            {
                "path": "tools/frontend_authority_init.sh",
                "required": False,
                "kind": "style-authority-helper",
                "route_pack": True,
                "snapshot": True,
            },
        ]
        manifest_path = root / ROUTE_PACK_MANIFEST_PATH
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(
                {
                    "schema": ROUTE_PACK_MANIFEST_SCHEMA,
                    "version": 1,
                    "files": fixture_files,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        for raw in fixture_files:
            if not raw["required"] or raw["path"] == ROUTE_PACK_MANIFEST_PATH:
                continue
            path = root / raw["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# fixture\n", encoding="utf-8")
            if raw["path"].endswith(".sh"):
                path.chmod(0o755)

        payload = build_manifest(root, include_semantic=False)
        if payload["status"] != "ok":
            print("self-check fixture unexpectedly failed", file=sys.stderr)
            print(json.dumps(payload, indent=2), file=sys.stderr)
            return 1

        export_dir = Path(tmp) / "export"
        copied = copy_pack(root, export_dir, payload["files"], dry_run=False)
        if copied != [ROUTE_PACK_MANIFEST_PATH, "tools/frontend_route_plan.sh"]:
            print("self-check copied an unexpected file count", file=sys.stderr)
            return 1
        export_manifest_path = export_dir / "codex-route-pack.manifest.json"
        write_manifest(payload, export_manifest_path, dry_run=False)
        if not export_manifest_path.is_file():
            print("self-check did not write manifest", file=sys.stderr)
            return 1

        outside = Path(tmp) / "outside-route-pack.txt"
        outside.write_text("not part of the route pack\n", encoding="utf-8")
        symlink = root / "tools/frontend_authority_init.sh"
        symlink.symlink_to(outside)
        symlink_manifest = build_manifest(root, include_semantic=False)
        if symlink_manifest["status"] != "manifest-error":
            print("self-check symlink fixture unexpectedly passed", file=sys.stderr)
            return 1
        try:
            copy_pack(root, Path(tmp) / "symlink-export", payload["files"], dry_run=False)
        except ValueError:
            pass
        else:
            print("self-check export unexpectedly followed a symlink", file=sys.stderr)
            return 1
        symlink.unlink()

        outside_export = Path(tmp) / "outside-export"
        outside_export.mkdir()
        poisoned_export = Path(tmp) / "poisoned-export"
        poisoned_export.mkdir()
        (poisoned_export / "tools").symlink_to(outside_export, target_is_directory=True)
        try:
            copy_pack(root, poisoned_export, payload["files"], dry_run=False)
        except ValueError:
            pass
        else:
            print("self-check export followed a destination symlink", file=sys.stderr)
            return 1
        if any(outside_export.iterdir()):
            print("self-check export wrote outside the export root", file=sys.stderr)
            return 1

        missing = root / "tools/frontend_route_plan.sh"
        missing.unlink()
        failed = build_manifest(root, include_semantic=False)
        if failed["status"] != "missing-required":
            print("self-check missing-required fixture unexpectedly passed", file=sys.stderr)
            return 1

        fixture_files[1]["snapshot"] = False
        manifest_path.write_text(
            json.dumps(
                {
                    "schema": ROUTE_PACK_MANIFEST_SCHEMA,
                    "version": 1,
                    "files": fixture_files,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        invalid_manifest = build_manifest(root, include_semantic=False)
        if invalid_manifest["status"] != "manifest-error":
            print("self-check invalid manifest unexpectedly passed", file=sys.stderr)
            return 1

    return 0
