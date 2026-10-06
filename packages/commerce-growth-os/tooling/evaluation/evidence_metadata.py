"""Build bounded reproducibility metadata for local live-evaluation artifacts."""

from __future__ import annotations

import hashlib
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tooling.manifest import load_manifest


def command_value(command: list[str]) -> str | None:
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part) or None


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_evidence_metadata(
    evidence_type: str,
    files: Mapping[str, Path],
    *,
    include_codex: bool,
    requested_model: str | None = None,
    reasoning_effort: str | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict:
    manifest = load_manifest(ROOT / "skill-pack.json")
    dirty = command_value(["git", "status", "--porcelain"])
    metadata = {
        "evidence_type": evidence_type,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pack_version": manifest["pack_version"],
        "schema_version": manifest["schema_version"],
        "git_head": command_value(["git", "rev-parse", "HEAD"]),
        "git_dirty": bool(dirty),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "input_sha256": {name: file_sha256(path) for name, path in files.items()},
    }
    if include_codex:
        metadata.update(
            {
                "codex_version": command_value(["codex", "--version"]),
                "requested_model": requested_model or "configured-default",
                "reasoning_effort": reasoning_effort,
                "session_mode": "ephemeral-read-only",
            }
        )
    if extra:
        metadata.update(extra)
    return metadata
