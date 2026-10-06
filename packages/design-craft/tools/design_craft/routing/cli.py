from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .export import copy_pack, write_manifest
from .manifest import default_source_root
from .report import build_manifest, emit_human
from .self_check import self_check


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit or export the local Codex frontend route toolkit."
    )
    parser.add_argument("--source-root", default=None, help="Codex home root; default: $CODEX_HOME or ~/.codex.")
    parser.add_argument("--export-dir", default=None, help="Optional directory to receive a whitelisted copy.")
    parser.add_argument("--manifest", default=None, help="Optional manifest output path.")
    parser.add_argument("--json", action="store_true", help="Print the manifest JSON to stdout.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero for manifest, required-file, or semantic validation failures.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would be written without copying files.")
    parser.add_argument("--check", action="store_true", help="Run built-in self-check fixtures.")
    args = parser.parse_args()

    if args.check:
        return self_check()

    source_root = (
        Path(args.source_root).expanduser().resolve()
        if args.source_root
        else default_source_root().resolve()
    )
    payload = build_manifest(source_root)

    export_dir = Path(args.export_dir).expanduser().resolve() if args.export_dir else None
    manifest_path = Path(args.manifest).expanduser().resolve() if args.manifest else None
    copied: list[str] = []

    if export_dir is not None:
        if export_dir == source_root or source_root in export_dir.parents:
            print("Refusing to export the route pack inside the source Codex home.", file=sys.stderr)
            return 2
        if payload.get("route_pack_manifest", {}).get("status") != "ok":
            print("Refusing to export from an invalid route-pack manifest.", file=sys.stderr)
            return 2
        copied = copy_pack(source_root, export_dir, payload["files"], dry_run=args.dry_run)
        if manifest_path is None:
            manifest_path = export_dir / "codex-route-pack.manifest.json"

    if manifest_path is not None:
        write_manifest(payload, manifest_path, dry_run=args.dry_run)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        emit_human(payload, copied, manifest_path, dry_run=args.dry_run)

    if args.strict and payload["status"] != "ok":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
