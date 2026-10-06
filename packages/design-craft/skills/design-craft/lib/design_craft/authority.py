"""Resolve project-owned design and product authority without leaking across workspaces."""

from __future__ import annotations

import ast
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Literal


PROJECT_MARKERS = (
    "package.json",
    "pnpm-workspace.yaml",
    "pnpm-workspace.yml",
    "Package.swift",
    "pubspec.yaml",
    "settings.gradle",
    "settings.gradle.kts",
    "Cargo.toml",
    "go.mod",
    "pyproject.toml",
)
MAX_PROJECT_METADATA_BYTES = 1024 * 1024


class ProjectMetadataError(RuntimeError):
    """A project metadata file exists but is unsafe, invalid, or unsupported."""


@dataclass(frozen=True)
class AuthorityResolution:
    path: Path | None
    source: str
    search_root: Path
    reason: str


@dataclass(frozen=True)
class WorkspaceDeclaration:
    state: Literal["absent", "valid", "invalid"]
    patterns: tuple[str, ...]
    reason: str


def _start_directory(target: Path) -> Path:
    resolved = target.expanduser().resolve()
    return resolved.parent if resolved.is_file() else resolved


def _directories_to(start: Path, boundary: Path) -> tuple[Path, ...]:
    directories: list[Path] = []
    for directory in (start, *start.parents):
        directories.append(directory)
        if directory == boundary:
            break
    return tuple(directories)


def _git_root(start: Path) -> Path | None:
    for directory in (start, *start.parents):
        if (directory / ".git").exists():
            return directory
    return None


def _lexists(path: Path) -> bool:
    return os.path.lexists(path)


def _is_plain_file(path: Path) -> bool:
    try:
        return stat.S_ISREG(path.lstat().st_mode)
    except OSError:
        return False


def _is_project_root(directory: Path) -> bool:
    return any(_lexists(directory / marker) for marker in PROJECT_MARKERS)


def read_owned_text(
    path: Path,
    root: Path,
    *,
    label: str,
    max_bytes: int = MAX_PROJECT_METADATA_BYTES,
) -> str:
    """Read one bounded, non-symlink regular file whose resolved path stays in root."""

    lexical = path.expanduser().absolute()
    owned_root = root.expanduser().resolve()
    if not _lexists(lexical):
        raise FileNotFoundError(lexical)
    try:
        metadata = lexical.lstat()
    except OSError as exc:
        raise ProjectMetadataError(f"{label} metadata is unreadable: {exc}") from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise ProjectMetadataError(f"{label} metadata must be a non-symlink regular file")
    try:
        resolved = lexical.resolve(strict=True)
        resolved.relative_to(owned_root)
    except (OSError, ValueError) as exc:
        raise ProjectMetadataError(f"{label} metadata leaves its project boundary") from exc
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(lexical, flags)
    except OSError as exc:
        raise ProjectMetadataError(f"{label} metadata could not be opened safely: {exc}") from exc
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise ProjectMetadataError(f"{label} metadata must remain a regular file")
        if opened.st_size > max_bytes:
            raise ProjectMetadataError(f"{label} metadata exceeds {max_bytes} bytes")
        chunks: list[bytes] = []
        remaining = max_bytes + 1
        while remaining:
            chunk = os.read(descriptor, min(64 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        if len(raw) > max_bytes or os.read(descriptor, 1):
            raise ProjectMetadataError(f"{label} metadata exceeds {max_bytes} bytes")
        closed = os.fstat(descriptor)
        if (
            opened.st_dev,
            opened.st_ino,
            opened.st_size,
            opened.st_mtime_ns,
            opened.st_ctime_ns,
        ) != (
            closed.st_dev,
            closed.st_ino,
            closed.st_size,
            closed.st_mtime_ns,
            closed.st_ctime_ns,
        ):
            raise ProjectMetadataError(f"{label} metadata changed while it was read")
    finally:
        os.close(descriptor)
    try:
        return raw.decode("utf-8")
    except UnicodeError as exc:
        raise ProjectMetadataError(f"{label} metadata must be UTF-8") from exc


def _package_workspace_patterns(root: Path) -> tuple[bool, list[str]]:
    package_json = root / "package.json"
    if not _lexists(package_json):
        return False, []
    try:
        payload = json.loads(read_owned_text(package_json, root, label="package.json"))
    except (ProjectMetadataError, json.JSONDecodeError) as exc:
        raise ProjectMetadataError(f"invalid package.json workspace metadata: {exc}") from exc
    if not isinstance(payload, dict):
        raise ProjectMetadataError("package.json must contain a JSON object")
    workspaces = payload.get("workspaces")
    if workspaces is None:
        return False, []
    if isinstance(workspaces, dict):
        workspaces = workspaces.get("packages")
    if not isinstance(workspaces, list) or not workspaces:
        raise ProjectMetadataError("package.json workspaces must be a non-empty string list")
    if any(not isinstance(item, str) or not item.strip() for item in workspaces):
        raise ProjectMetadataError("package.json workspaces contains an invalid pattern")
    return True, [item.strip() for item in workspaces]


def _flow_sequence(value: str) -> list[str]:
    if not value.startswith("[") or not value.endswith("]"):
        raise ProjectMetadataError("pnpm packages flow sequence is invalid")
    try:
        parsed = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        parsed = [item.strip().strip("\"'") for item in value[1:-1].split(",")]
    if not isinstance(parsed, (list, tuple)) or not parsed:
        raise ProjectMetadataError("pnpm packages must be a non-empty sequence")
    if any(not isinstance(item, str) or not item.strip() for item in parsed):
        raise ProjectMetadataError("pnpm packages contains an invalid pattern")
    return [item.strip() for item in parsed]


def _pnpm_workspace_patterns(root: Path) -> tuple[bool, list[str]]:
    path = next(
        (candidate for candidate in (root / "pnpm-workspace.yaml", root / "pnpm-workspace.yml") if _lexists(candidate)),
        None,
    )
    if path is None:
        return False, []
    try:
        lines = read_owned_text(path, root, label=path.name).splitlines()
    except ProjectMetadataError as exc:
        raise ProjectMetadataError(f"invalid pnpm workspace metadata: {exc}") from exc
    patterns: list[str] = []
    in_packages = False
    packages_indent = 0
    for raw in lines:
        content = raw.split("#", 1)[0].rstrip()
        if not content.strip():
            continue
        indent = len(content) - len(content.lstrip())
        stripped = content.strip()
        if stripped.startswith("packages:"):
            if in_packages:
                raise ProjectMetadataError("pnpm workspace declares packages more than once")
            in_packages = True
            packages_indent = indent
            inline = stripped.partition(":")[2].strip()
            if inline:
                patterns.extend(_flow_sequence(inline))
                in_packages = False
            continue
        if in_packages and indent <= packages_indent:
            break
        if in_packages and stripped.startswith("-"):
            value = stripped[1:].strip().strip("\"'")
            if value:
                patterns.append(value)
            else:
                raise ProjectMetadataError("pnpm workspace contains an empty pattern")
        elif in_packages:
            raise ProjectMetadataError("pnpm packages must be a sequence")
    if not patterns:
        raise ProjectMetadataError("pnpm workspace must declare non-empty packages")
    return True, patterns


def workspace_declaration(root: Path) -> WorkspaceDeclaration:
    discovered = False
    patterns: list[str] = []
    try:
        for present, values in (_package_workspace_patterns(root), _pnpm_workspace_patterns(root)):
            discovered = discovered or present
            patterns.extend(values)
    except ProjectMetadataError as exc:
        return WorkspaceDeclaration("invalid", (), str(exc))
    if not discovered:
        return WorkspaceDeclaration("absent", (), "no workspace declaration")
    seen: dict[str, None] = {}
    for pattern in patterns:
        normalized = pattern.replace("\\", "/").rstrip("/")
        if normalized:
            seen.setdefault(normalized, None)
    if not seen:
        return WorkspaceDeclaration("invalid", (), "workspace declaration has no usable patterns")
    return WorkspaceDeclaration("valid", tuple(seen), "workspace declaration parsed")


def workspace_patterns(root: Path) -> tuple[str, ...]:
    return workspace_declaration(root).patterns


def _pattern_matches(relative: PurePosixPath, pattern: str) -> bool:
    normalized = pattern.lstrip("./")
    if not normalized or normalized.startswith("!"):
        return False
    if normalized.endswith("/**"):
        base = normalized[:-3].rstrip("/")
        value = relative.as_posix()
        if value == base or value.startswith(base + "/"):
            return True
    return relative.match(normalized)


def workspace_owns(root: Path, target: Path) -> bool:
    """Return whether a declared workspace includes the target's package ancestry."""

    declaration = workspace_declaration(root)
    if declaration.state == "absent":
        return True
    if declaration.state != "valid":
        return False
    patterns = declaration.patterns
    try:
        relative = target.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    if relative == Path("."):
        return True
    candidates = [PurePosixPath(relative.as_posix())]
    candidates.extend(PurePosixPath(parent.as_posix()) for parent in relative.parents if parent != Path("."))
    positive = [pattern for pattern in patterns if not pattern.startswith("!")]
    excluded = [pattern[1:] for pattern in patterns if pattern.startswith("!")]
    if not positive:
        return False
    if any(_pattern_matches(candidate, pattern) for candidate in candidates for pattern in excluded):
        return False
    return any(_pattern_matches(candidate, pattern) for candidate in candidates for pattern in positive)


def asset_root_for(target: Path) -> Path | None:
    """Resolve a package-local root for root-relative browser assets."""

    start = _start_directory(target)
    boundary = project_root_for(start)
    for directory in _directories_to(start, boundary):
        if directory == boundary:
            break
        package_json = directory / "package.json"
        if _lexists(package_json):
            return directory if _is_plain_file(package_json) else None
    declaration = workspace_declaration(boundary)
    if boundary != start and declaration.state != "absent":
        return None
    return boundary


def _implicit_authority(candidate: Path, root: Path) -> tuple[Path | None, str | None]:
    if not _lexists(candidate):
        return None, None
    if not _is_plain_file(candidate):
        return None, "implicit authority must be a non-symlink regular file"
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root.resolve())
    except (OSError, ValueError):
        return None, "implicit authority leaves its project boundary"
    return resolved, None


def project_root_for(target: Path) -> Path:
    """Return the nearest trustworthy project boundary for local asset resolution."""

    start = _start_directory(target)
    git_root = _git_root(start)
    if git_root is not None:
        return git_root
    home = Path.home().resolve()
    for directory in (start, *start.parents):
        if directory == home:
            break
        if _is_project_root(directory):
            return directory
    return start


def resolve_project_authority(
    target: Path,
    name: str,
    *,
    explicit: Path | str | None = None,
) -> AuthorityResolution:
    """Resolve an explicit or project-owned authority file.

    Discovery stops at the nearest Git root. Outside Git, authority is inherited
    only inside a recognized project root. A home-directory authority is never
    inherited implicitly.
    """

    if Path(name).name != name or name in {"", ".", ".."}:
        raise ValueError("authority name must be one filename")
    start = _start_directory(target)
    if explicit:
        path = Path(explicit).expanduser().resolve()
        return AuthorityResolution(
            path=path if path.is_file() else None,
            source="explicit" if path.is_file() else "explicit_missing",
            search_root=start,
            reason="explicit authority file" if path.is_file() else "explicit authority file is missing",
        )

    home = Path.home().resolve()
    target_local = start / name
    if start != home:
        local_path, local_error = _implicit_authority(target_local, start)
        if local_error:
            return AuthorityResolution(None, "unsafe", start, local_error)
        if local_path is not None:
            return AuthorityResolution(
                local_path,
                "target_local",
                start,
                "authority is owned by the target directory",
            )

    git_root = _git_root(start)
    if git_root is not None and git_root != home:
        for directory in _directories_to(start, git_root):
            candidate = directory / name
            candidate_path, candidate_error = _implicit_authority(candidate, git_root)
            if candidate_error:
                return AuthorityResolution(None, "unsafe", git_root, candidate_error)
            if candidate_path is None:
                continue
            if directory == git_root and not workspace_owns(git_root, start):
                return AuthorityResolution(
                    path=None,
                    source="none",
                    search_root=git_root,
                    reason="Git-root authority does not own this workspace target",
                )
            source = "workspace_root" if directory == git_root else "nearest_project"
            return AuthorityResolution(candidate_path, source, git_root, "nearest project-owned authority")
        return AuthorityResolution(None, "none", git_root, "no authority inside the Git project boundary")

    project_root: Path | None = None
    for directory in (start, *start.parents):
        if directory == home:
            break
        if _is_project_root(directory):
            project_root = directory
            break
    if project_root is None:
        return AuthorityResolution(None, "none", start, "no recognized project boundary")
    if not workspace_owns(project_root, start):
        return AuthorityResolution(
            None,
            "none",
            project_root,
            "project authority does not own this target or workspace metadata is invalid",
        )
    for directory in _directories_to(start, project_root):
        candidate = directory / name
        candidate_path, candidate_error = _implicit_authority(candidate, project_root)
        if candidate_error:
            return AuthorityResolution(None, "unsafe", project_root, candidate_error)
        if candidate_path is not None:
            source = "project_root" if directory == project_root else "nearest_project"
            return AuthorityResolution(candidate_path, source, project_root, "nearest project-owned authority")
    return AuthorityResolution(None, "none", project_root, "no authority inside the recognized project boundary")
