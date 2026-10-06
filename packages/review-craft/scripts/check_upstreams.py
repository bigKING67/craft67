#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "contracts/upstreams.json"
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
BRANCH_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,127}$")
ALLOWED_STATUSES = {"tracked", "selective_absorbed", "absorbed", "rejected"}
COMMON_SOURCE_FIELDS = {
    "id",
    "repository",
    "branch",
    "reviewedRevision",
    "reviewedAt",
    "license",
    "status",
    "sourcePaths",
    "reviewedBlobs",
}
SURFACE_FIELDS = {
    "watchSurfaces",
    "absorbedSurfaces",
    "excludedSurfaces",
}


class UpstreamContractError(ValueError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate pinned Review Craft upstreams and optionally compare source blobs"
    )
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    parser.add_argument(
        "--remote",
        action="store_true",
        help="explicitly fetch remote source trees; offline validation is the default",
    )
    return parser.parse_args()


def _string(source: dict[str, Any], field: str, *, index: int) -> str:
    value = source.get(field)
    if not isinstance(value, str) or not value.strip():
        raise UpstreamContractError(f"sources[{index}].{field}: expected a non-empty string")
    return value


def _string_list(source: dict[str, Any], field: str, *, index: int) -> list[str]:
    value = source.get(field)
    if (
        not isinstance(value, list)
        or not value
        or not all(isinstance(item, str) and item.strip() for item in value)
    ):
        raise UpstreamContractError(
            f"sources[{index}].{field}: expected a non-empty string array"
        )
    if len(set(value)) != len(value):
        raise UpstreamContractError(f"sources[{index}].{field}: duplicate values")
    return value


def _reviewed_blobs(
    source: dict[str, Any], paths: list[str], *, index: int
) -> dict[str, str]:
    value = source.get("reviewedBlobs")
    if not isinstance(value, dict) or not value:
        raise UpstreamContractError(
            f"sources[{index}].reviewedBlobs: expected a non-empty object"
        )
    if not all(
        isinstance(path, str)
        and isinstance(blob, str)
        and SHA_PATTERN.fullmatch(blob) is not None
        for path, blob in value.items()
    ):
        raise UpstreamContractError(
            f"sources[{index}].reviewedBlobs: expected path keys and lowercase full Git SHAs"
        )
    missing = sorted(set(paths) - set(value))
    unexpected = sorted(set(value) - set(paths))
    if missing or unexpected:
        raise UpstreamContractError(
            f"sources[{index}].reviewedBlobs: unexpected paths {unexpected}; "
            f"missing paths {missing}"
        )
    return value


def _validate_repository(identifier: str, repository: str, *, index: int) -> None:
    parsed = urlparse(repository)
    try:
        port = parsed.port
    except ValueError as error:
        raise UpstreamContractError(
            f"sources[{index}].repository: invalid URL port"
        ) from error
    if (
        parsed.scheme != "https"
        or parsed.hostname != "github.com"
        or parsed.username is not None
        or parsed.password is not None
        or port is not None
        or parsed.query
        or parsed.fragment
    ):
        raise UpstreamContractError(
            f"sources[{index}].repository: expected a public https://github.com URL"
        )
    repository_id = parsed.path.strip("/").removesuffix(".git")
    if identifier == repository_id:
        return
    prefix = f"{repository_id}#"
    if not identifier.startswith(prefix):
        raise UpstreamContractError(
            f"sources[{index}].repository: path must match id or its scoped prefix"
        )
    scope = identifier.removeprefix(prefix)
    path = PurePosixPath(scope)
    if not scope or path.is_absolute() or ".." in path.parts or path.as_posix() != scope:
        raise UpstreamContractError(f"sources[{index}].id: invalid repository scope")


def _validate_source_paths(paths: list[str], *, index: int) -> None:
    for value in paths:
        path = PurePosixPath(value)
        if path.is_absolute() or ".." in path.parts or path.as_posix() != value:
            raise UpstreamContractError(
                f"sources[{index}].sourcePaths: unsafe repository-relative path {value!r}"
            )


def load_contract(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise UpstreamContractError("upstream contract must be a JSON object")
    if payload.get("schema") != "review-craft.upstreams.v2":
        raise UpstreamContractError("unsupported upstream contract schema")
    if set(payload) != {"schema", "sources"}:
        raise UpstreamContractError("upstream contract contains unknown or missing root fields")
    sources = payload.get("sources")
    if not isinstance(sources, list) or not sources:
        raise UpstreamContractError("upstream contract must contain at least one source")
    seen: set[str] = set()
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            raise UpstreamContractError(f"sources[{index}]: expected an object")
        source_fields = set(source)
        unexpected = sorted(source_fields - COMMON_SOURCE_FIELDS - SURFACE_FIELDS)
        missing = sorted(COMMON_SOURCE_FIELDS - source_fields)
        if unexpected or missing:
            raise UpstreamContractError(
                f"sources[{index}]: unexpected fields {unexpected}; missing fields {missing}"
            )
        status = _string(source, "status", index=index)
        if status not in ALLOWED_STATUSES:
            raise UpstreamContractError(f"sources[{index}].status: unsupported status {status!r}")
        if status == "tracked":
            required_surfaces = {"watchSurfaces", "excludedSurfaces"}
            allowed_surfaces = required_surfaces
        elif status == "selective_absorbed":
            required_surfaces = {"absorbedSurfaces", "excludedSurfaces"}
            allowed_surfaces = required_surfaces | {"watchSurfaces"}
        else:
            required_surfaces = {"absorbedSurfaces", "excludedSurfaces"}
            allowed_surfaces = required_surfaces
        unexpected_surfaces = sorted((source_fields & SURFACE_FIELDS) - allowed_surfaces)
        missing_surfaces = sorted(required_surfaces - source_fields)
        if unexpected_surfaces or missing_surfaces:
            raise UpstreamContractError(
                f"sources[{index}]: unexpected surface fields {unexpected_surfaces}; "
                f"missing surface fields {missing_surfaces} for status {status!r}"
            )
        identifier = _string(source, "id", index=index)
        if identifier in seen:
            raise UpstreamContractError(f"sources[{index}].id: duplicate source {identifier!r}")
        seen.add(identifier)
        repository = _string(source, "repository", index=index)
        _validate_repository(identifier, repository, index=index)
        branch = _string(source, "branch", index=index)
        if (
            BRANCH_PATTERN.fullmatch(branch) is None
            or ".." in branch
            or "//" in branch
            or branch.endswith("/")
        ):
            raise UpstreamContractError(f"sources[{index}].branch: invalid Git branch")
        revision = _string(source, "reviewedRevision", index=index)
        if SHA_PATTERN.fullmatch(revision) is None:
            raise UpstreamContractError(
                f"sources[{index}].reviewedRevision: expected a lowercase full Git SHA"
            )
        reviewed_at = _string(source, "reviewedAt", index=index)
        try:
            date.fromisoformat(reviewed_at)
        except ValueError as error:
            raise UpstreamContractError(
                f"sources[{index}].reviewedAt: expected YYYY-MM-DD"
            ) from error
        _string(source, "license", index=index)
        paths = _string_list(source, "sourcePaths", index=index)
        _validate_source_paths(paths, index=index)
        _reviewed_blobs(source, paths, index=index)
        active_fields = ["watchSurfaces"] if status == "tracked" else ["absorbedSurfaces"]
        if status == "selective_absorbed" and "watchSurfaces" in source:
            active_fields.append("watchSurfaces")
        active_surfaces = {
            field: _string_list(source, field, index=index) for field in active_fields
        }
        excluded = _string_list(source, "excludedSurfaces", index=index)
        surface_sets = {field: set(values) for field, values in active_surfaces.items()}
        surface_sets["excludedSurfaces"] = set(excluded)
        surface_names = list(surface_sets)
        for left_index, left in enumerate(surface_names):
            for right in surface_names[left_index + 1 :]:
                overlap = sorted(surface_sets[left] & surface_sets[right])
                if overlap:
                    raise UpstreamContractError(
                        f"sources[{index}]: {left} and {right} overlap: {overlap}"
                    )
    return payload


def _run_git(
    arguments: list[str], *, environment: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *arguments],
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError("git was unavailable or timed out") from error


def _remote_state(source: dict[str, Any]) -> tuple[str, dict[str, str]]:
    reference = f"refs/heads/{source['branch']}"
    environment = dict(os.environ)
    environment["GIT_TERMINAL_PROMPT"] = "0"
    with tempfile.TemporaryDirectory(prefix="review-craft-upstream-") as directory:
        repository = Path(directory) / "source.git"
        initialized = _run_git(
            ["init", "--bare", "--quiet", str(repository)], environment=environment
        )
        if initialized.returncode != 0:
            raise RuntimeError(f"git init exited {initialized.returncode}")
        fetched = _run_git(
            [
                "-C",
                str(repository),
                "fetch",
                "--quiet",
                "--no-tags",
                "--depth=1",
                "--filter=blob:none",
                source["repository"],
                reference,
            ],
            environment=environment,
        )
        if fetched.returncode != 0:
            raise RuntimeError(f"git fetch exited {fetched.returncode}")
        resolved = _run_git(
            ["-C", str(repository), "rev-parse", "--verify", "FETCH_HEAD^{commit}"],
            environment=environment,
        )
        revision = resolved.stdout.strip()
        if resolved.returncode != 0 or SHA_PATTERN.fullmatch(revision) is None:
            raise RuntimeError("git fetch returned an invalid branch revision")
        pathspecs = [f":(literal){path}" for path in source["sourcePaths"]]
        inspected = _run_git(
            [
                "-C",
                str(repository),
                "ls-tree",
                "-r",
                "-z",
                "--full-tree",
                revision,
                "--",
                *pathspecs,
            ],
            environment=environment,
        )
        if inspected.returncode != 0:
            raise RuntimeError(f"git ls-tree exited {inspected.returncode}")

    blobs: dict[str, str] = {}
    for row in inspected.stdout.split("\0"):
        if not row:
            continue
        try:
            metadata, path = row.split("\t", 1)
            _mode, object_type, blob = metadata.split()
        except ValueError as error:
            raise RuntimeError("git ls-tree returned an invalid source result") from error
        if object_type != "blob" or SHA_PATTERN.fullmatch(blob) is None:
            continue
        if path in blobs:
            raise RuntimeError("git ls-tree returned a duplicate source path")
        blobs[path] = blob
    return revision, blobs


def evaluate(contract: dict[str, Any], *, remote: bool) -> tuple[dict[str, Any], int]:
    results: list[dict[str, Any]] = []
    exit_code = 0
    for source in contract["sources"]:
        result = {
            "id": source["id"],
            "branch": source["branch"],
            "reviewedRevision": source["reviewedRevision"],
            "status": "NOT_CHECKED",
        }
        if remote:
            try:
                revision, blobs = _remote_state(source)
                result["remoteRevision"] = revision
                result["repositoryStatus"] = (
                    "CURRENT" if revision == source["reviewedRevision"] else "UPDATED"
                )
                path_results = []
                for path in source["sourcePaths"]:
                    reviewed_blob = source["reviewedBlobs"][path]
                    remote_blob = blobs.get(path)
                    path_results.append(
                        {
                            "path": path,
                            "reviewedBlob": reviewed_blob,
                            "remoteBlob": remote_blob,
                            "status": (
                                "CURRENT"
                                if remote_blob == reviewed_blob
                                else "MISSING"
                                if remote_blob is None
                                else "UPDATED"
                            ),
                        }
                    )
                result["sourcePaths"] = path_results
                if all(item["status"] == "CURRENT" for item in path_results):
                    result["contentStatus"] = "CURRENT"
                    result["status"] = "CURRENT"
                else:
                    result["contentStatus"] = "UPDATED"
                    result["status"] = "UPDATED"
                    exit_code = max(exit_code, 1)
            except RuntimeError as error:
                result["status"] = "UNREACHABLE"
                result["error"] = str(error)
                exit_code = 2
        results.append(result)
    return {
        "schema": "review-craft.upstream-check.v2",
        "mode": "remote" if remote else "offline",
        "sources": results,
    }, exit_code


def main() -> int:
    args = parse_args()
    try:
        contract = load_contract(Path(args.contract).expanduser().resolve(strict=True))
        payload, exit_code = evaluate(contract, remote=args.remote)
    except (OSError, json.JSONDecodeError, UpstreamContractError) as error:
        print(f"review-craft upstream check: {error}", file=sys.stderr)
        return 2
    print(json.dumps(payload, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
