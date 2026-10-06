#!/usr/bin/env python3
"""Validate skill-pack schema, semantic version, and optional release tag parity."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tooling.manifest import ManifestError, load_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=str(ROOT / "skill-pack.json"))
    parser.add_argument("--tag", help="Optional release tag, for example v2.1.0")
    args = parser.parse_args()

    try:
        payload = load_manifest(Path(args.manifest))
        pack_version = payload["pack_version"]
        if payload.get("default_install_root") != "~/.agents/skills":
            raise ValueError("default_install_root must be ~/.agents/skills")
        duplicate_roots = payload.get("duplicate_discovery_roots")
        if duplicate_roots != ["~/.codex/skills"]:
            raise ValueError("duplicate_discovery_roots must contain only ~/.codex/skills")
        names = [skill.get("name") for skill in payload.get("skills", [])]
        if len(names) != 8 or len(names) != len(set(names)):
            raise ValueError("release manifest must contain 8 unique skills")
        if args.tag and args.tag.removeprefix("v") != pack_version:
            raise ValueError(f"tag {args.tag!r} does not match pack_version {pack_version!r}")
        print(f"release contract passed: v{pack_version}, {len(names)} skills")
        return 0
    except (OSError, ManifestError, ValueError) as exc:
        print(f"check_release error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
