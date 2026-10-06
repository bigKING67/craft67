#!/usr/bin/env python3
"""Build one content-bound GitHub release candidate from a clean commit."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def normalize_receipt_argv(argv: list[str]) -> list[str]:
    normalized: list[str] = []
    for value in argv:
        if value == sys.executable:
            normalized.append("<python>")
            continue
        path = Path(value)
        if not path.is_absolute():
            normalized.append(value)
            continue
        try:
            relative = path.resolve(strict=False).relative_to(ROOT)
        except ValueError:
            normalized.append(f"<absolute>/{path.name}")
        else:
            normalized.append(f"<repo>/{relative.as_posix()}")
    return normalized


def run(argv: list[str]) -> dict[str, object]:
    completed = subprocess.run(
        argv,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    receipt_argv = normalize_receipt_argv(argv)
    receipt: dict[str, object] = {
        "argv": receipt_argv,
        "exit_code": completed.returncode,
        "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr.encode()).hexdigest(),
    }
    if completed.returncode != 0:
        print(completed.stdout)
        print(completed.stderr, file=sys.stderr)
        raise RuntimeError(f"release gate failed: {' '.join(receipt_argv)}")
    return receipt


def git_output(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, text=True, capture_output=True, check=True
    ).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="dist/release")
    args = parser.parse_args()
    if git_output("status", "--porcelain", "--untracked-files=all"):
        parser.error("release candidate requires a clean Git worktree")
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    output = (ROOT / args.output).resolve()
    if output.exists() and any(output.iterdir()):
        parser.error(f"output directory is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)

    commands = [
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "skills/creative-craft/scripts",
            "scripts",
            "tests",
        ],
        [sys.executable, "scripts/validate_schemas.py"],
        [sys.executable, "scripts/validate.py"],
        [sys.executable, "scripts/host_smoke.py", "--json"],
        [sys.executable, "scripts/check_package.py"],
        [sys.executable, "-m", "compileall", "-q", "skills", "scripts", "tests"],
    ]
    receipts = [run(command) for command in commands]
    before_pack = {path.name for path in output.iterdir()}
    receipts.append(run(["npm", "pack", "--pack-destination", str(output)]))
    packages = [path for path in output.glob("*.tgz") if path.name not in before_pack]
    if len(packages) != 1:
        raise RuntimeError(f"expected exactly one package, found {len(packages)}")
    package = packages[0]
    receipts.append(
        run(
            [
                sys.executable,
                "scripts/package_smoke.py",
                "--package",
                str(package),
                "--json",
            ]
        )
    )
    digest = hashlib.sha256(package.read_bytes()).hexdigest()
    checksum_path = output / f"{package.name}.sha256"
    checksum_path.write_text(f"{digest}  {package.name}\n", encoding="utf-8")
    summary = {
        "schema_version": "creative-craft.release-validation.v1",
        "version": version,
        "commit": git_output("rev-parse", "HEAD"),
        "branch": git_output("branch", "--show-current"),
        "built_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "artifact": package.name,
        "artifact_bytes": package.stat().st_size,
        "artifact_sha256": digest,
        "commands": receipts,
        "claims": {
            "provider_network_adapters": False,
            "real_golden_evals": False,
            "agent_quality_text_eval_in_ci": False,
            "packaged_reference_runtime_e2e": True,
            "npm_published": False,
            "distribution": "github-release",
        },
    }
    summary_path = output / "release-validation.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(summary_path)
    print(package)
    print(checksum_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
