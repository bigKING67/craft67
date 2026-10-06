from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Any


class ContractError(ValueError):
    def __init__(self, errors: list[str]):
        super().__init__("\n".join(errors))
        self.errors = errors


def non_empty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def string_list(value: Any, *, allow_empty: bool = False) -> bool:
    return (
        isinstance(value, list)
        and (allow_empty or bool(value))
        and all(non_empty(item) for item in value)
    )


def safe_relative(value: Any) -> bool:
    if not non_empty(value) or "\0" in value or "\\" in value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts and not any(
        ":" in part for part in path.parts
    )


def run_file(run_dir: Path, relative: str) -> Path:
    path = run_dir / relative
    if path.is_symlink():
        raise ContractError([f"run artifact must not be a symlink: {relative}"])
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(run_dir)
    except (OSError, ValueError) as error:
        raise ContractError([f"invalid run artifact {relative}: {error}"]) from error
    if not resolved.is_file():
        raise ContractError([f"run artifact must be a file: {relative}"])
    return resolved
