#!/usr/bin/env python3
"""Build and verify a reproducible local 3d-craft release candidate."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGER = ROOT / "scripts" / "package_skill.py"
VALIDATOR = ROOT / "scripts" / "validate_source.py"


def run(
    command: list[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None
) -> None:
    process_env = os.environ.copy()
    if env:
        process_env.update(env)
    result = subprocess.run(
        command, cwd=cwd, env=process_env, capture_output=True, text=True
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"command failed ({' '.join(command)}): {detail[-4000:]}")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def write_minimal_glb(path: Path) -> None:
    document = json.dumps(
        {"asset": {"version": "2.0", "generator": "3d-craft-release-gate"}, "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [{"name": "Root"}]},
        separators=(",", ":"),
    ).encode()
    document += b" " * ((4 - len(document) % 4) % 4)
    total_length = 12 + 8 + len(document)
    path.write_bytes(
        struct.pack("<III", 0x46546C67, 2, total_length)
        + struct.pack("<II", len(document), 0x4E4F534A)
        + document
    )


def git_state() -> tuple[str | None, bool]:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True
    )
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True
    )
    return (commit.stdout.strip() if commit.returncode == 0 else None, bool(status.stdout.strip()))


def gate(output_dir: Path) -> dict[str, object]:
    if not output_dir.is_absolute():
        raise ValueError("--output-dir must be an absolute path")
    output_dir = output_dir.resolve()
    if output_dir == ROOT or ROOT in output_dir.parents:
        raise ValueError("--output-dir must remain outside the source repository")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("--output-dir must be absent or empty")
    output_dir.mkdir(parents=True, exist_ok=True)

    checks: list[str] = []
    with tempfile.TemporaryDirectory(prefix="3d-craft-release-gate.") as temporary_name:
        temporary = Path(temporary_name)
        run([sys.executable, str(VALIDATOR), "--json"])
        checks.append("source-validation")
        run(["npm", "test"])
        checks.append("unit-and-contract-tests")
        run(["npm", "run", "viewer:typecheck"])
        checks.append("viewer-typecheck")
        run(
            ["npm", "run", "viewer:build"],
            env={"VITE_OUT_DIR": str(temporary / "viewer-dist")},
        )
        checks.append("viewer-build")

        first = temporary / "candidate-a.zip"
        second = temporary / "candidate-b.zip"
        run([sys.executable, str(PACKAGER), "--output", str(first), "--json"])
        run([sys.executable, str(PACKAGER), "--output", str(second), "--json"])
        first_digest = digest(first)
        second_digest = digest(second)
        if first_digest != second_digest:
            raise RuntimeError("two package builds produced different SHA-256 digests")
        checks.append("reproducible-package")

        extracted = temporary / "extracted"
        with zipfile.ZipFile(first) as archive:
            archive.extractall(extracted)
        run(
            [
                sys.executable,
                str(VALIDATOR),
                "--skill-root",
                str(extracted / "3d-craft"),
                "--json",
            ]
        )
        checks.append("isolated-package-validation")
        minimal_glb = temporary / "minimal.glb"
        gltf_report = temporary / "minimal-gltf-validation.json"
        write_minimal_glb(minimal_glb)
        run(
            [
                "node",
                str(extracted / "3d-craft" / "scripts" / "gltf_validate.mjs"),
                str(minimal_glb),
                "--output",
                str(gltf_report),
            ],
            cwd=temporary,
        )
        gltf_payload = json.loads(gltf_report.read_text(encoding="utf-8"))
        if gltf_payload.get("status") != "PASS":
            raise RuntimeError("the packaged glTF validator did not accept the minimal GLB")
        checks.append("isolated-gltf-runtime")
        doctor_report = temporary / "isolated-doctor.json"
        run(
            [
                sys.executable,
                str(extracted / "3d-craft" / "scripts" / "3d_craft.py"),
                "doctor",
                "--json",
                "--output",
                str(doctor_report),
            ],
            cwd=temporary,
        )
        doctor_payload = json.loads(doctor_report.read_text(encoding="utf-8"))
        if doctor_payload.get("capabilities", {}).get("asset.gltf.validate") != "available":
            raise RuntimeError("the packaged doctor did not observe its bundled glTF validator")
        checks.append("isolated-doctor-gltf-capability")

        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        artifact = output_dir / f"3d-craft-{version}.zip"
        shutil.copyfile(first, artifact)

    commit, dirty = git_state()
    payload: dict[str, object] = {
        "schema": "3d-craft.release-candidate.v1",
        "status": "PASS",
        "verified_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "artifact": {
            "path": str(artifact),
            "bytes": artifact.stat().st_size,
            "sha256": digest(artifact),
        },
        "checks": checks,
        "source": {"git_commit": commit, "dirty": dirty},
        "release_eligible": commit is not None and not dirty,
        "limitations": ([] if commit is not None and not dirty else [
            "Source is not an immutable clean Git commit; this is a local candidate, not release provenance."
        ]),
    }
    attestation = output_dir / "release-candidate-attestation.json"
    attestation.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    payload["attestation"] = str(attestation)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        payload = gate(args.output_dir.expanduser())
    except (OSError, RuntimeError, ValueError, zipfile.BadZipFile) as error:
        print(f"release candidate gate failed: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        artifact = payload["artifact"]
        assert isinstance(artifact, dict)
        print(
            f"PASS: {artifact['path']} sha256={artifact['sha256']} "
            f"release_eligible={str(payload['release_eligible']).lower()}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
