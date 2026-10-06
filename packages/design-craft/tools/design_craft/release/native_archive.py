from __future__ import annotations

import gzip
import io
import re
import tarfile
from pathlib import Path, PurePosixPath


NORMALIZED_MODE = 0o644
MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 128
MAX_MEMBER_BYTES = 32 * 1024 * 1024
MAX_TOTAL_BYTES = 128 * 1024 * 1024


class _LimitedReader:
    def __init__(self, raw: gzip.GzipFile, limit: int) -> None:
        self.raw = raw
        self.limit = limit
        self.count = 0

    def read(self, size: int = -1) -> bytes:
        remaining = self.limit - self.count
        request = remaining + 1 if size < 0 else min(size, remaining + 1)
        data = self.raw.read(request)
        self.count += len(data)
        if self.count > self.limit:
            raise ValueError("native bundle decompressed tar stream is too large")
        return data


def safe_relative(raw: str) -> str:
    if (
        not raw
        or "\\" in raw
        or raw.startswith("/")
        or raw.endswith("/")
        or re.match(r"^[A-Za-z]:", raw)
    ):
        raise ValueError(f"unsafe relative path: {raw!r}")
    parts = raw.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"unsafe relative path: {raw!r}")
    normalized = PurePosixPath(raw).as_posix()
    if normalized != raw:
        raise ValueError(f"non-canonical relative path: {raw!r}")
    return normalized


def regular_tar_info(name: str, size: int) -> tarfile.TarInfo:
    info = tarfile.TarInfo(safe_relative(name))
    info.size = size
    info.mode = NORMALIZED_MODE
    info.mtime = 0
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.type = tarfile.REGTYPE
    return info


def write_deterministic_tar(files: dict[str, bytes], output: Path) -> None:
    if len(files) > MAX_ARCHIVE_ENTRIES:
        raise ValueError("native bundle contains too many files")
    total = sum(len(content) for content in files.values())
    if total > MAX_TOTAL_BYTES:
        raise ValueError("native bundle uncompressed content is too large")
    for name, content in files.items():
        safe_relative(name)
        if len(content) > MAX_MEMBER_BYTES:
            raise ValueError(f"native bundle member is too large: {name}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as zipped:
            with tarfile.open(
                fileobj=zipped, mode="w", format=tarfile.USTAR_FORMAT
            ) as archive:
                for relative, content in sorted(files.items()):
                    archive.addfile(
                        regular_tar_info(relative, len(content)), io.BytesIO(content)
                    )
    if output.stat().st_size > MAX_ARCHIVE_BYTES:
        output.unlink(missing_ok=True)
        raise ValueError("native bundle compressed archive is too large")


def inspect_archive(
    bundle: Path,
    *,
    max_archive_bytes: int = MAX_ARCHIVE_BYTES,
    max_entries: int = MAX_ARCHIVE_ENTRIES,
    max_member_bytes: int = MAX_MEMBER_BYTES,
    max_total_bytes: int = MAX_TOTAL_BYTES,
) -> tuple[dict[str, bytes], list[str]]:
    entries: dict[str, bytes] = {}
    errors: list[str] = []
    if bundle.is_symlink() or not bundle.is_file():
        return {}, [f"native release bundle is missing or unsafe: {bundle}"]
    if bundle.stat().st_size > max_archive_bytes:
        return {}, ["native bundle compressed archive is too large"]
    seen: set[str] = set()
    total_bytes = 0
    max_tar_stream_bytes = max_total_bytes + max_entries * 1024 + 10 * 1024
    try:
        with bundle.open("rb") as compressed:
            with gzip.GzipFile(fileobj=compressed, mode="rb") as uncompressed:
                limited = _LimitedReader(uncompressed, max_tar_stream_bytes)
                with tarfile.open(fileobj=limited, mode="r|") as archive:
                    for index, member in enumerate(archive, start=1):
                        if index > max_entries:
                            errors.append("native bundle contains too many members")
                            break
                        try:
                            name = safe_relative(member.name)
                        except ValueError as exc:
                            errors.append(f"native bundle has an unsafe member: {exc}")
                            continue
                        if name in seen:
                            errors.append(f"native bundle contains duplicate member: {name}")
                            continue
                        seen.add(name)
                        if not member.isfile():
                            errors.append(
                                f"native bundle member must be a regular file: {name}"
                            )
                            continue
                        if member.pax_headers:
                            errors.append(
                                f"native bundle member must not use PAX headers: {name}"
                            )
                        if member.mode != NORMALIZED_MODE:
                            errors.append(
                                f"native bundle member mode is not normalized: {name}"
                            )
                        if member.mtime != 0:
                            errors.append(
                                f"native bundle member mtime is not normalized: {name}"
                            )
                        if member.uid != 0 or member.gid != 0:
                            errors.append(
                                f"native bundle member ownership is not normalized: {name}"
                            )
                        if member.uname or member.gname:
                            errors.append(
                                f"native bundle member owner names are not normalized: {name}"
                            )
                        if member.size < 0 or member.size > max_member_bytes:
                            errors.append(f"native bundle member is too large: {name}")
                            continue
                        total_bytes += member.size
                        if total_bytes > max_total_bytes:
                            errors.append("native bundle uncompressed content is too large")
                            break
                        handle = archive.extractfile(member)
                        if handle is None:
                            errors.append(f"native bundle member cannot be read: {name}")
                            continue
                        content = handle.read(member.size + 1)
                        if len(content) != member.size:
                            errors.append(f"native bundle member size is invalid: {name}")
                            continue
                        entries[name] = content
    except (EOFError, OSError, ValueError, tarfile.TarError) as exc:
        return {}, [f"cannot read native release bundle: {exc}"]
    return entries, errors


def extract_entries(entries: dict[str, bytes], target: Path) -> None:
    for relative, content in entries.items():
        destination = target / Path(safe_relative(relative))
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.is_symlink() or destination.parent.is_symlink():
            raise ValueError(f"native extraction destination is unsafe: {relative}")
        destination.write_bytes(content)
