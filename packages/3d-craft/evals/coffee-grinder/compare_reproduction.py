#!/usr/bin/env python3
"""Compare two clean fixture builds by normalized scene and GLB semantics."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def normalized_scene(report: dict) -> dict:
    return {
        "scene": {key: report["scene"][key] for key in ("dimensions", "meshes", "triangles")},
        "coverage": report["coverage"],
        "integrity": {
            "unapplied_mesh_transforms": report["integrity"]["unapplied_mesh_transforms"],
            "non_manifold_edges": report["integrity"]["non_manifold_edges"],
            "missing_textures": report["integrity"]["missing_textures"],
        },
        "objects": [
            {key: row[key] for key in ("name", "type", "parent", "location", "rotation_euler", "scale", "dimensions", "modifiers", "mesh")}
            for row in report["objects"]
        ],
    }


def digest(value: dict) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--first-inspection", required=True)
    parser.add_argument("--second-inspection", required=True)
    parser.add_argument("--first-gltf", required=True)
    parser.add_argument("--second-gltf", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    first_inspection_report = load(args.first_inspection)
    second_inspection_report = load(args.second_inspection)
    first_gltf_report = load(args.first_gltf)
    second_gltf_report = load(args.second_gltf)
    first_scene = normalized_scene(first_inspection_report)
    second_scene = normalized_scene(second_inspection_report)
    first_gltf = first_gltf_report["semantic"]["semantic_sha256"]
    second_gltf = second_gltf_report["semantic"]["semantic_sha256"]
    first_scene_digest = digest(first_scene)
    second_scene_digest = digest(second_scene)
    report = {
        "schema": "3d-craft.reproduction.v1",
        "match": first_scene_digest == second_scene_digest and first_gltf == second_gltf,
        "candidate": {
            "blend_sha256": first_inspection_report["blend"]["sha256"],
            "gltf_sha256": first_gltf_report["asset"]["sha256"],
        },
        "scene": {"first_sha256": first_scene_digest, "second_sha256": second_scene_digest, "match": first_scene_digest == second_scene_digest},
        "gltf": {"first_semantic_sha256": first_gltf, "second_semantic_sha256": second_gltf, "match": first_gltf == second_gltf},
    }
    output = Path(args.output).expanduser().resolve()
    if output.exists():
        raise ValueError("reproduction output already exists; create a new run for a new candidate")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["match"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
