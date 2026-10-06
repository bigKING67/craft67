#!/usr/bin/env python3
"""Compatibility CLI for the modular Codex frontend route-pack tooling."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))


if __name__ == "__main__":
    if sys.argv[1:] == ["--check"]:
        from tools.design_craft.routing.self_check import self_check as run_cli
    else:
        from tools.design_craft.routing.cli import main as run_cli

    raise SystemExit(run_cli())


from tools.design_craft.routing.cli import main
from tools.design_craft.routing.export import copy_pack, write_manifest
from tools.design_craft.routing.manifest import (
    PackFile,
    ROUTE_PACK_MANIFEST_PATH,
    ROUTE_PACK_MANIFEST_SCHEMA,
    SCHEMA,
    default_source_root,
    file_entry,
    load_json,
    load_route_pack_files,
    sha256_file,
)
from tools.design_craft.routing.report import build_manifest, emit_human
from tools.design_craft.routing.self_check import self_check
from tools.design_craft.routing.semantic_audit import semantic_validation


__all__ = [
    "PackFile",
    "ROUTE_PACK_MANIFEST_PATH",
    "ROUTE_PACK_MANIFEST_SCHEMA",
    "SCHEMA",
    "build_manifest",
    "copy_pack",
    "default_source_root",
    "emit_human",
    "file_entry",
    "load_json",
    "load_route_pack_files",
    "main",
    "self_check",
    "semantic_validation",
    "sha256_file",
    "write_manifest",
]
