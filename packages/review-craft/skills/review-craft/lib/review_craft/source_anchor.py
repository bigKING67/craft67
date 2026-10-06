from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .constants import ARTIFACT_PATHS, SCHEMA_VERSION
from .contract_core import safe_relative
from .jsonio import read_json, sha256_bytes
from .repository import (
    fingerprint_inventory,
    inspect_git,
    inventory_for_mode,
    source_payload,
    worktree_fingerprint,
)

ANCHOR_ALGORITHM = "sha256-raw-lines-v1"


@dataclass(frozen=True)
class SourceProjection:
    target_root: Path
    records: dict[str, dict[str, Any]]
    diff_base: str | None


def _positive_integer(value: Any, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{field}: expected a positive integer")
    return value


def _raw_lines(payload: bytes) -> list[bytes]:
    lines: list[bytes] = []
    offset = 0
    while offset < len(payload):
        newline = payload.find(b"\n", offset)
        if newline < 0:
            lines.append(payload[offset:])
            break
        lines.append(payload[offset : newline + 1])
        offset = newline + 1
    return lines


def _source_side(record: dict[str, Any]) -> str:
    return "BASE" if record.get("kind") == "deleted" else "CURRENT"


def build_source_anchor(
    projection: SourceProjection,
    *,
    path: str,
    line_start: int,
    line_end: int,
) -> dict[str, Any]:
    start = _positive_integer(line_start, "lineStart")
    end = _positive_integer(line_end, "lineEnd")
    if end < start:
        raise ValueError("lineEnd: expected an integer >= lineStart")
    record = projection.records.get(path)
    if record is None:
        raise ValueError(f"path is not in the canonical source projection: {path}")
    if record.get("kind") not in {"file", "deleted"} or record.get("binary") is not False:
        raise ValueError(f"path is not anchorable text source: {path}")
    payload = source_payload(
        projection.target_root,
        record,
        diff_base=projection.diff_base,
    )
    lines = _raw_lines(payload)
    if end > len(lines):
        raise ValueError(
            f"line range {start}-{end} exceeds source line count {len(lines)}: {path}"
        )
    span = b"".join(lines[start - 1 : end])
    return {
        "algorithm": ANCHOR_ALGORITHM,
        "sourceSide": _source_side(record),
        "sourceSha256": sha256_bytes(payload),
        "sourceLineCount": len(lines),
        "spanSha256": sha256_bytes(span),
    }


def _current_projection(
    target_root: Path, configuration: dict[str, Any]
) -> SourceProjection:
    records, _excluded, _diff = inventory_for_mode(
        target_root,
        mode=configuration["mode"],
        scopes=configuration["scope"],
        excludes=configuration["exclude"],
        generated=configuration["generated"],
        vendored=configuration["vendored"],
        diff_base=configuration["diffBase"],
    )
    return SourceProjection(
        target_root=target_root,
        records={row["path"]: row for row in records},
        diff_base=configuration["diffBase"],
    )


def build_run_location(
    run_dir_value: str | Path,
    *,
    path: str,
    line_start: int,
    line_end: int | None,
    role: str,
) -> dict[str, Any]:
    run_dir = Path(run_dir_value).expanduser().resolve(strict=True)
    manifest = read_json(run_dir / "review-manifest.json")
    if manifest.get("schemaVersion") != SCHEMA_VERSION:
        raise ValueError("anchor-location requires a current run.v5 review")
    if manifest.get("status") != "draft" or manifest.get("sealedAt") is not None:
        raise ValueError("anchor-location requires an unsealed draft review")
    if manifest.get("artifacts") != ARTIFACT_PATHS:
        raise ValueError("review manifest does not declare the current canonical artifact map")
    if not safe_relative(path):
        raise ValueError("--path: expected a safe repository-relative POSIX path")
    if not isinstance(role, str) or not role.strip():
        raise ValueError("--role: expected a non-empty value")

    configuration = manifest.get("configuration")
    if not isinstance(configuration, dict):
        raise ValueError("review manifest configuration is invalid")
    run_state = read_json(run_dir / "run-state.json")
    target_root = Path(run_state["targetRoot"]).resolve(strict=True)
    projection = _current_projection(target_root, configuration)
    records = list(projection.records.values())
    current_fingerprint = fingerprint_inventory(records)
    coverage = read_json(run_dir / ARTIFACT_PATHS["coverage"])
    expected_fingerprint = manifest.get("target", {}).get("sourceFingerprint")
    if (
        current_fingerprint != expected_fingerprint
        or coverage.get("inventoryFingerprint") != expected_fingerprint
    ):
        raise ValueError("canonical source projection changed after preflight")
    if worktree_fingerprint(target_root, records=records) != run_state.get(
        "worktreeFingerprint"
    ):
        raise ValueError("worktree changed after preflight")
    status = inspect_git(target_root).status
    if sha256_bytes(status.encode("utf-8", errors="surrogateescape")) != run_state.get(
        "statusFingerprint"
    ):
        raise ValueError("Git status changed after preflight")
    coverage_rows = {
        row.get("path"): row
        for row in coverage.get("files", [])
        if isinstance(row, dict) and isinstance(row.get("path"), str)
    }
    record = projection.records.get(path)
    coverage_row = coverage_rows.get(path)
    if record is None or coverage_row is None:
        raise ValueError(f"--path is not in canonical coverage: {path}")
    if coverage_row.get("sha256") != record.get("sha256"):
        raise ValueError(f"coverage source identity does not match the inventory: {path}")

    end = line_start if line_end is None else line_end
    return {
        "path": path,
        "lineStart": line_start,
        "lineEnd": end,
        "role": role.strip(),
        "anchor": build_source_anchor(
            projection,
            path=path,
            line_start=line_start,
            line_end=end,
        ),
    }
