from __future__ import annotations

from pathlib import Path, PurePosixPath


def normalize_manifest_path(raw_path: object) -> str:
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ValueError("route-pack manifest file path must be a non-empty string")
    path = raw_path.strip()
    posix_path = PurePosixPath(path)
    if (
        posix_path.is_absolute()
        or "\\" in path
        or any(part in {"", ".", ".."} for part in posix_path.parts)
    ):
        raise ValueError(
            f"route-pack manifest file path must be a safe relative POSIX path: {path!r}"
        )
    return posix_path.as_posix()


def _safe_path(root: Path, rel_path: str, *, label: str) -> Path:
    resolved_root = root.resolve(strict=False)
    candidate = root
    for part in PurePosixPath(rel_path).parts:
        candidate /= part
        if candidate.is_symlink():
            raise ValueError(f"{label} must not use symlinks: {rel_path!r}")
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"{label} resolves outside root: {rel_path!r}") from exc
    return candidate


def validate_manifest_source_path(source_root: Path, rel_path: str) -> Path:
    return _safe_path(source_root, rel_path, label="route-pack manifest file path")


def validate_export_destination(export_dir: Path, rel_path: str) -> Path:
    return _safe_path(export_dir, rel_path, label="route-pack export path")
