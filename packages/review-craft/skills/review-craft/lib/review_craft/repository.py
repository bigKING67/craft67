from __future__ import annotations

import codecs
import fnmatch
import hashlib
import os
import re
import stat as stat_mode
import subprocess
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from json.encoder import encode_basestring
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from .constants import DEFAULT_EXCLUDES
from .jsonio import canonical_compact, sha256_bytes


@dataclass(frozen=True)
class GitState:
    is_repository: bool
    root: Path
    revision: str | None
    branch: str | None
    remote: str | None
    status: str
    unborn: bool


def run_git(root: Path, *args: str, check: bool = False) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        check=check,
    )


def safe_remote(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    if re.match(r"^[a-z][a-z0-9+.-]*://", value, flags=re.IGNORECASE):
        try:
            split = urlsplit(value)
            host = split.hostname or ""
        except ValueError:
            # A malformed remote is not safe identity material because userinfo
            # cannot be separated from the host reliably.
            return None
        if not host:
            return None
        if ":" in host and not host.startswith("["):
            host = f"[{host}]"
        try:
            port = split.port
        except ValueError:
            return None
        if port:
            host = f"{host}:{port}"
        return urlunsplit((split.scheme, host, split.path, "", ""))
    scp_like = re.match(
        r"^[^@/\s]+@(?P<host>\[[^\]]+\]|[^:/\s]+):(?P<path>.+)$",
        value,
    )
    if scp_like:
        path = re.split(r"[?#]", scp_like.group("path"), maxsplit=1)[0]
        return f"{scp_like.group('host')}:{path}" if path else None
    if "@" in value:
        return None
    return value


def inspect_git(target: Path, *, _legacy_identity: bool = False) -> GitState:
    target = target.resolve(strict=True)
    probe = run_git(target, "rev-parse", "--show-toplevel")
    if probe.returncode != 0:
        return GitState(False, target, None, None, None, "", False)
    root_text = (
        probe.stdout.decode("utf-8", errors="replace").strip()
        if _legacy_identity
        else os.fsdecode(probe.stdout.removesuffix(b"\n"))
    )
    root = Path(root_text).resolve()
    revision_result = run_git(root, "rev-parse", "HEAD")
    revision = (
        revision_result.stdout.decode("utf-8", errors="replace").strip()
        if revision_result.returncode == 0
        else None
    )
    branch_result = run_git(root, "symbolic-ref", "--short", "-q", "HEAD")
    branch = (
        branch_result.stdout.decode("utf-8", errors="replace").strip()
        if branch_result.returncode == 0
        else None
    )
    remote_result = run_git(root, "remote", "get-url", "origin")
    remote = (
        safe_remote(remote_result.stdout.decode("utf-8", errors="replace"))
        if remote_result.returncode == 0
        else None
    )
    status_result = (
        run_git(root, "status", "--porcelain=v1", "-z")
        if _legacy_identity
        else run_git(
            root,
            "-c",
            f"core.fileMode={'false' if os.name == 'nt' else 'true'}",
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=normal",
            "--ignore-submodules=none",
        )
    )
    if status_result.returncode != 0:
        raise RuntimeError(
            f"git status failed (exit code {status_result.returncode}); "
            "worktree cleanliness is unknown"
        )
    status = status_result.stdout.decode("utf-8", errors="surrogateescape")
    return GitState(True, root, revision, branch, remote, status, revision is None)


def resolve_git_revision(root: Path, value: str, *, _legacy_identity: bool = False) -> str:
    if not value or value.startswith("-") or any(character in value for character in "\0\r\n"):
        raise ValueError("diff base must be a non-option Git revision")
    state = inspect_git(root, _legacy_identity=_legacy_identity)
    if not state.is_repository:
        raise ValueError("diff mode requires a Git repository")
    result = run_git(state.root, "rev-parse", "--verify", f"{value}^{{commit}}")
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"invalid diff base {value!r}: {message or 'not a commit'}")
    return result.stdout.decode("ascii").strip()


def git_diff_changes(
    root: Path,
    base_revision: str,
    *,
    _legacy_identity: bool = False,
) -> list[dict[str, Any]]:
    state = inspect_git(root, _legacy_identity=_legacy_identity)
    if not state.is_repository:
        raise ValueError("diff mode requires a Git repository")
    result = run_git(
        state.root,
        *(
            []
            if _legacy_identity
            else ["-c", f"core.fileMode={'false' if os.name == 'nt' else 'true'}"]
        ),
        "diff",
        "--name-status",
        "-z",
        "--find-renames",
        *([] if _legacy_identity else ["--ignore-submodules=none"]),
        base_revision,
        "--",
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace").strip())
    tokens = [
        item.decode("utf-8", errors="surrogateescape")
        for item in result.stdout.split(b"\0")
        if item
    ]
    changes: dict[str, dict[str, Any]] = {}
    index = 0
    while index < len(tokens):
        status_token = tokens[index]
        index += 1
        status = status_token[0]
        if status in {"R", "C"}:
            if index + 1 >= len(tokens):
                raise RuntimeError("git diff returned a truncated rename/copy record")
            previous = tokens[index]
            path = tokens[index + 1]
            index += 2
            row = {
                "path": Path(path).as_posix(),
                "status": status,
                "statusDetail": status_token,
                "previousPath": Path(previous).as_posix(),
                "untracked": False,
            }
        else:
            if index >= len(tokens):
                raise RuntimeError("git diff returned a truncated path record")
            path = tokens[index]
            index += 1
            row = {
                "path": Path(path).as_posix(),
                "status": status,
                "statusDetail": status_token,
                "untracked": False,
            }
        changes[row["path"]] = row
    untracked = run_git(state.root, "ls-files", "--others", "--exclude-standard", "-z")
    if untracked.returncode != 0:
        raise RuntimeError(untracked.stderr.decode("utf-8", errors="replace").strip())
    for item in untracked.stdout.split(b"\0"):
        if not item:
            continue
        path = Path(item.decode("utf-8", errors="surrogateescape")).as_posix()
        changes.setdefault(
            path,
            {
                "path": path,
                "status": "A",
                "statusDetail": "untracked",
                "untracked": True,
            },
        )
    return [changes[path] for path in sorted(changes)]


def _matches(path: str, patterns: Iterable[str]) -> bool:
    candidates = {path, f"{path}/"}
    for pattern in patterns:
        normalized = pattern.removeprefix("./")
        if any(fnmatch.fnmatch(candidate, normalized) for candidate in candidates):
            return True
        if normalized.endswith("/**"):
            prefix = normalized[:-3].rstrip("/")
            if path == prefix or path.startswith(prefix + "/"):
                return True
    return False


def _is_in_scope(path: str, scopes: Iterable[str]) -> bool:
    for scope in scopes:
        normalized = scope.removeprefix("./").rstrip("/")
        if not normalized or normalized == ".":
            return True
        if path == normalized or path.startswith(normalized + "/"):
            return True
    return False


def _git_paths(root: Path) -> list[str]:
    result = run_git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace").strip())
    paths = {
        item.decode("utf-8", errors="surrogateescape")
        for item in result.stdout.split(b"\0")
        if item
    }
    # Full-review identity follows the current filesystem. Diff mode supplies
    # deleted paths explicitly so it can preserve their base-revision content.
    return sorted(path for path in paths if (root / path).exists() or (root / path).is_symlink())


def _filesystem_paths(root: Path) -> list[str]:
    paths: list[str] = []
    for directory, names, files in os.walk(root, followlinks=False):
        names[:] = sorted(name for name in names if name != ".git")
        for name in sorted(files):
            paths.append((Path(directory) / name).relative_to(root).as_posix())
        for name in names:
            candidate = Path(directory) / name
            if candidate.is_symlink():
                paths.append(candidate.relative_to(root).as_posix())
    return sorted(set(paths))


def repository_paths(root: Path) -> list[str]:
    root = root.resolve(strict=True)
    return _git_paths(root) if inspect_git(root).is_repository else _filesystem_paths(root)


def _binary_preview(preview: bytes, *, complete: bool) -> bool:
    if b"\0" in preview:
        return True
    try:
        decoder = codecs.getincrementaldecoder("utf-8")(errors="strict")
        decoder.decode(preview, final=complete)
    except UnicodeDecodeError:
        return True
    return False


def _file_record(root: Path, relative: str) -> dict[str, Any]:
    path = root / relative
    stat = path.lstat()
    if path.is_symlink():
        target = os.readlink(path)
        return {
            "path": relative,
            "kind": "symlink",
            "sizeBytes": stat.st_size,
            "sha256": sha256_bytes(target.encode("utf-8", errors="surrogateescape")),
            "linkTarget": target,
            "binary": False,
        }
    if not path.is_file():
        return {
            "path": relative,
            "kind": "other",
            "sizeBytes": stat.st_size,
            "sha256": sha256_bytes(b""),
            "binary": True,
        }
    digest = hashlib.sha256()
    preview = b""
    size = 0
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            if len(preview) < 8192:
                preview += chunk[: 8192 - len(preview)]
            digest.update(chunk)
            size += len(chunk)
    return {
        "path": relative,
        "kind": "file",
        "sizeBytes": size,
        "sha256": digest.hexdigest(),
        "binary": _binary_preview(preview, complete=size == len(preview)),
        "sourceIdentity": {
            "executable": bool(stat.st_mode & 0o100),
            "gitlink": None,
            "checkout": None,
        },
    }


def _index_entries(root: Path) -> dict[str, tuple[str, str]]:
    result = run_git(root, "ls-files", "--stage", "-z")
    if result.returncode != 0:
        raise RuntimeError("git index inspection failed; source identity is unknown")
    entries = {}
    for item in result.stdout.split(b"\0"):
        if not item:
            continue
        metadata, path = item.split(b"\t", 1)
        mode, oid, stage = metadata.decode("ascii").split()
        relative = path.decode("utf-8", errors="surrogateescape")
        entries[relative] = (mode if stage == "0" else "unmerged", oid)
    return entries


def _submodule_record(root: Path, relative: str, oid: str) -> dict[str, Any]:
    path = root / relative
    checkout = None
    nested_identity = sha256_bytes(b"")
    if path.is_symlink():
        raise RuntimeError(f"submodule {relative!r} is a symlink; identity is unknown")
    if (path / ".git").exists():
        child = inspect_git(path)
        if child.root != path.resolve() or child.revision is None:
            raise RuntimeError(f"submodule {relative!r} checkout identity is unknown")
        # Git configuration must not hide executable-bit changes in a POSIX child.
        status = run_git(
            path,
            "-c",
            f"core.fileMode={'false' if os.name == 'nt' else 'true'}",
            "-c",
            "status.showUntrackedFiles=normal",
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=normal",
            "--ignore-submodules=none",
        )
        if status.returncode != 0 or status.stdout:
            raise RuntimeError(
                f"submodule {relative!r} is dirty or unreadable; "
                "recursive worktree identity is not supported"
            )
        checkout = child.revision
        nested_identity = _submodule_index_identity(path)
    elif path.exists() and (not path.is_dir() or any(path.iterdir())):
        raise RuntimeError(f"submodule {relative!r} has no verifiable checkout")
    return {
        "path": relative,
        "kind": "other",
        "sizeBytes": 0,
        "sha256": nested_identity,
        "binary": True,
        "sourceIdentity": {"executable": None, "gitlink": oid, "checkout": checkout},
    }


def _submodule_index_identity(root: Path) -> str:
    flags = run_git(root, "ls-files", "-v", "-z")
    if flags.returncode != 0:
        raise RuntimeError(f"submodule {root.name!r} index visibility is unknown")
    for row in flags.stdout.split(b"\0"):
        if row and (row[:1].islower() or row[:1] == b"S"):
            raise RuntimeError(
                f"submodule {root.name!r} has hidden index flags; worktree cleanliness is unknown"
            )
    nested = [
        _submodule_record(root, path, oid)
        for path, (mode, oid) in sorted(_index_entries(root).items())
        if mode == "160000"
    ]
    return sha256_bytes(canonical_compact(nested).encode("utf-8"))


def _current_file_record(
    root: Path,
    relative: str,
    entry: tuple[str, str] | None,
    deleted_revision: str | None,
) -> dict[str, Any]:
    if entry is not None:
        mode, oid = entry
        if mode == "unmerged":
            raise RuntimeError(f"unmerged index entry: {relative}")
        if mode == "160000":
            return _submodule_record(root, relative, oid)
    path = root / relative
    if not path.exists() and not path.is_symlink() and deleted_revision is not None:
        return _file_record_at_revision(root, deleted_revision, relative)
    record = _file_record(root, relative)
    if os.name == "nt" and record["kind"] == "file":
        # Windows has no POSIX executable bit: bind Git's tracked executable flag.
        record["sourceIdentity"]["executable"] = entry is not None and entry[0] == "100755"
    return record


def _payload_at_revision(root: Path, revision: str, relative: str) -> bytes:
    result = run_git(root, "show", f"{revision}:{relative}")
    if result.returncode != 0:
        raise OSError(result.stderr.decode("utf-8", errors="replace").strip())
    return result.stdout


def _file_record_at_revision(
    root: Path,
    revision: str,
    relative: str,
    *,
    _legacy_identity: bool = False,
) -> dict[str, Any]:
    tree = run_git(root, "ls-tree", "-z", revision, "--", f":(literal){relative}")
    if tree.returncode != 0 or not tree.stdout:
        raise OSError(f"cannot read base source identity: {relative}")
    mode, _, oid = tree.stdout.split(b"\t", 1)[0].decode("ascii").split()
    if mode == "160000" and not _legacy_identity:
        return {
            "path": relative,
            "kind": "deleted",
            "sizeBytes": 0,
            "sha256": sha256_bytes(b""),
            "binary": True,
            "sourceIdentity": {"executable": None, "gitlink": oid, "checkout": None},
        }
    payload = _payload_at_revision(root, revision, relative)
    preview = payload[:8192]
    return {
        "path": relative,
        "kind": "deleted",
        "sizeBytes": len(payload),
        "sha256": sha256_bytes(payload),
        "binary": _binary_preview(preview, complete=len(payload) == len(preview)),
        "sourceIdentity": {"executable": mode == "100755", "gitlink": None, "checkout": None},
    }


def _current_source_path(root: str, parts: list[str], relative: str) -> str:
    """Check every component on every read; this is not an atomic snapshot."""
    path = root
    try:
        for part in parts:
            path += os.sep + part
            metadata = os.lstat(path)
            if stat_mode.S_ISLNK(metadata.st_mode) or (
                getattr(metadata, "st_file_attributes", 0) & stat_mode.FILE_ATTRIBUTE_REPARSE_POINT
            ):
                raise ValueError(f"source path traverses a symlink or reparse point: {relative}")
        # A canonical root, relative components without '..', and no links/reparse
        # points establish containment without a second full realpath traversal.
        if not stat_mode.S_ISREG(metadata.st_mode):
            raise ValueError(f"source path is not a regular current file: {relative}")
    except (FileNotFoundError, NotADirectoryError) as error:
        raise ValueError(f"source path no longer matches the inventory: {relative}") from error
    return path


def _source_parts(relative: str) -> list[str]:
    native = relative.replace("\\", "/") if os.name == "nt" else relative
    parts = [part for part in native.split("/") if part and part != "."]
    if not parts or native.startswith("/") or ".." in parts or os.path.splitdrive(native)[0]:
        raise ValueError("source record path is invalid")
    if os.name == "nt" and any(part.endswith((" ", ".")) or ":" in part for part in parts):
        raise ValueError("source record path is invalid")
    return parts


class SourceReader:
    """One bounded analysis shares root normalization, never file state or content."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve(strict=True)
        self.root_string = str(self.root)

    def read(self, record: Mapping[str, Any], *, diff_base: str | None) -> bytes:
        relative = record.get("path")
        if not isinstance(relative, str) or not relative:
            raise ValueError("source record path is invalid")
        parts = _source_parts(relative)
        if record.get("kind") == "deleted":
            if not diff_base:
                raise ValueError("deleted source requires an immutable diff base")
            payload = _payload_at_revision(self.root, diff_base, relative)
        else:
            path = _current_source_path(self.root_string, parts, relative)
            with open(path, "rb") as source:
                payload = source.read()
        if sha256_bytes(payload) != record.get("sha256"):
            raise ValueError(f"source content no longer matches the inventory: {relative}")
        return payload


def source_payload(root: Path, record: Mapping[str, Any], *, diff_base: str | None) -> bytes:
    """Read the exact source side represented by one canonical inventory record."""
    return SourceReader(root).read(record, diff_base=diff_base)


def inventory(
    root: Path,
    *,
    scopes: Iterable[str] = (".",),
    excludes: Iterable[str] = (),
    generated: Iterable[str] = (),
    vendored: Iterable[str] = (),
    paths: Iterable[str] | None = None,
    deleted_revision: str | None = None,
    _legacy_identity: bool = False,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    root = root.resolve(strict=True)
    is_repository = run_git(root, "rev-parse", "--show-toplevel").returncode == 0
    entries = _index_entries(root) if is_repository and not _legacy_identity else {}
    candidate_paths = (
        sorted(set(paths))
        if paths is not None
        else (_git_paths(root) if is_repository else _filesystem_paths(root))
    )
    if paths is None:
        candidate_paths = sorted(
            set(candidate_paths)
            | {path for path, (mode, _) in entries.items() if mode in {"160000", "unmerged"}}
        )
    exclude_patterns = tuple(DEFAULT_EXCLUDES) + tuple(excludes)
    included: list[dict[str, Any]] = []
    excluded: list[dict[str, str]] = []
    for relative in candidate_paths:
        relative = Path(relative).as_posix()
        if not _is_in_scope(relative, scopes):
            excluded.append({"path": relative, "reason": "outside configured scope"})
            continue
        if _matches(relative, exclude_patterns):
            excluded.append({"path": relative, "reason": "matched exclude pattern"})
            continue
        try:
            if _legacy_identity:
                if (
                    not (root / relative).exists()
                    and not (root / relative).is_symlink()
                    and deleted_revision
                ):
                    record = _file_record_at_revision(
                        root, deleted_revision, relative, _legacy_identity=True
                    )
                else:
                    record = _file_record(root, relative)
                record.pop("sourceIdentity", None)
            else:
                record = _current_file_record(
                    root, relative, entries.get(relative), deleted_revision
                )
        except OSError as error:
            if entries.get(relative, (None,))[0] == "160000":
                raise RuntimeError(f"submodule {relative!r} identity is unreadable") from error
            record = {
                "path": relative,
                "kind": "unreadable",
                "sizeBytes": 0,
                "sha256": sha256_bytes(str(error).encode("utf-8")),
                "binary": True,
                "readError": type(error).__name__,
            }
        if _matches(relative, generated):
            record["classification"] = "generated"
        elif _matches(relative, vendored):
            record["classification"] = "vendored"
        else:
            record["classification"] = "source"
        included.append(record)
    return sorted(included, key=lambda item: item["path"]), sorted(
        excluded, key=lambda item: item["path"]
    )


def inventory_for_mode(
    root: Path,
    *,
    mode: str,
    scopes: Iterable[str] = (".",),
    excludes: Iterable[str] = (),
    generated: Iterable[str] = (),
    vendored: Iterable[str] = (),
    diff_base: str | None = None,
    _legacy_identity: bool = False,
) -> tuple[list[dict[str, Any]], list[dict[str, str]], dict[str, Any] | None]:
    if mode != "diff":
        records, excluded = inventory(
            root,
            scopes=scopes,
            excludes=excludes,
            generated=generated,
            vendored=vendored,
            _legacy_identity=_legacy_identity,
        )
        return records, excluded, None
    if not diff_base:
        raise ValueError("diff mode requires a diff base")
    base_revision = resolve_git_revision(root, diff_base, _legacy_identity=_legacy_identity)
    changes = git_diff_changes(root, base_revision, _legacy_identity=_legacy_identity)
    records, excluded = inventory(
        root,
        scopes=scopes,
        excludes=excludes,
        generated=generated,
        vendored=vendored,
        paths=[row["path"] for row in changes],
        deleted_revision=base_revision,
        _legacy_identity=_legacy_identity,
    )
    changes_by_path = {row["path"]: row for row in changes}
    for record in records:
        change = changes_by_path[record["path"]]
        record["diffStatus"] = change["status"]
        if change.get("previousPath"):
            record["previousPath"] = change["previousPath"]
        if change["untracked"]:
            record["untracked"] = True
    included_paths = {row["path"] for row in records}
    excluded_reasons = {row["path"]: row["reason"] for row in excluded}
    scoped_changes = []
    for change in changes:
        row = dict(change)
        row["inScope"] = row["path"] in included_paths
        row["reason"] = (
            "in configured scope"
            if row["inScope"]
            else excluded_reasons.get(row["path"], "not present in the selected inventory")
        )
        scoped_changes.append(row)
    return records, excluded, {"baseRevision": base_revision, "changes": scoped_changes}


def source_inventory_configuration(
    configuration: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the only configuration fields allowed to influence source identity."""
    value = configuration or {}
    return {
        "mode": value.get("mode", "review"),
        "scope": list(value.get("scope", ["."])),
        "exclude": list(value.get("exclude", [])),
        "generated": list(value.get("generated", [])),
        "vendored": list(value.get("vendored", [])),
        "diffBase": value.get("diffBase"),
    }


def inventory_for_configuration(
    root: Path,
    configuration: Mapping[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, str]], dict[str, Any] | None]:
    value = source_inventory_configuration(configuration)
    return inventory_for_mode(
        root,
        mode=value["mode"],
        scopes=value["scope"],
        excludes=value["exclude"],
        generated=value["generated"],
        vendored=value["vendored"],
        diff_base=value["diffBase"],
    )


_PLAIN_IDENTITIES = (
    {"executable": False, "gitlink": None, "checkout": None},
    {"executable": True, "gitlink": None, "checkout": None},
)
_PLAIN_IDENTITY_JSON = tuple(canonical_compact(value) for value in _PLAIN_IDENTITIES)


def _inventory_fingerprint_row(row: Mapping[str, Any]) -> str:
    extra = ("diffStatus", "previousPath", "untracked")
    identity = row.get("sourceIdentity")
    if (
        not any(field in row for field in extra)
        and identity in _PLAIN_IDENTITIES
        and type(identity["executable"]) is bool
    ):
        # Preserve the exact canonical JSON bytes while avoiding repeated nested
        # dictionary serialization for the two ordinary-file identity shapes.
        suffix = _PLAIN_IDENTITY_JSON[_PLAIN_IDENTITIES.index(identity)]
        return (
            f'{{"classification":{encode_basestring(row["classification"])},'
            f'"kind":{encode_basestring(row["kind"])},'
            f'"path":{encode_basestring(row["path"])},'
            f'"sha256":{encode_basestring(row["sha256"])},"sourceIdentity":{suffix}}}'
        )
    value = {field: row[field] for field in ("path", "kind", "sha256", "classification")}
    value.update((field, row[field]) for field in (*extra, "sourceIdentity") if field in row)
    return canonical_compact(value)


def fingerprint_inventory(records: list[dict[str, Any]]) -> str:
    rows = (_inventory_fingerprint_row(row) for row in sorted(records, key=lambda r: r["path"]))
    return sha256_bytes(("[" + ",".join(rows) + "]").encode("utf-8"))


def worktree_fingerprint(
    root: Path,
    *,
    records: Iterable[dict[str, Any]] | None = None,
    configuration: Mapping[str, Any] | None = None,
) -> str:
    """Hash the canonical source projection without reopening excluded content."""
    root = root.resolve(strict=True)
    if records is not None and configuration is not None:
        raise ValueError("worktree fingerprint accepts records or configuration, not both")
    if records is None:
        records, _, _ = inventory_for_configuration(root, configuration)
    return fingerprint_inventory(list(records))


def repository_identity(state: GitState, records: list[dict[str, Any]]) -> str:
    seed = {
        "remote": state.remote,
        "revision": state.revision,
        "branch": state.branch,
        "sourceFingerprint": fingerprint_inventory(records),
    }
    return sha256_bytes(canonical_compact(seed).encode("utf-8"))
