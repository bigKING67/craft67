#!/usr/bin/env python3
"""Build the standalone Workflow Craft skill artifact."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from packaging import PackagingError, create_artifact, package_root_from_script


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path, help="Directory that will receive the ZIP and manifest.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        artifact, manifest, data = create_artifact(package_root_from_script(__file__), arguments.output_dir)
    except (OSError, PackagingError) as error:
        print(f"build failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps({"status": "built", "artifact": str(artifact), "manifest": str(manifest), "version": data["version"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
