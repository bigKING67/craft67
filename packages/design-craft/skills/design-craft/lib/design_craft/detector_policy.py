"""Security and local-asset policy for detector wrapper output."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit


URL_USERINFO = re.compile(
    r"(?P<prefix>(?:[A-Za-z][A-Za-z0-9+.-]*:)?//)"
    r"(?P<userinfo>[^/@\s<>\"']+)@"
    r"(?P<host>[^\s<>\"']+)"
)
MAX_HTML_BYTES = 1024 * 1024


def redact_url_userinfo(value: str) -> str:
    """Redact URL userinfo without masking ordinary email addresses."""

    return URL_USERINFO.sub(
        lambda match: f"{match.group('prefix')}[REDACTED]@{match.group('host')}",
        value,
    )


def sanitize_payload(value: Any) -> Any:
    """Recursively redact URL credentials in detector-controlled JSON."""

    if isinstance(value, str):
        return redact_url_userinfo(value)
    if isinstance(value, list):
        return [sanitize_payload(item) for item in value]
    if isinstance(value, tuple):
        return [sanitize_payload(item) for item in value]
    if isinstance(value, dict):
        return {
            redact_url_userinfo(key) if isinstance(key, str) else key: sanitize_payload(item)
            for key, item in value.items()
        }
    return value


class _StylesheetLinks(HTMLParser):
    def __init__(self, *, limit: int) -> None:
        super().__init__(convert_charrefs=True)
        self.limit = limit
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "link" or len(self.hrefs) >= self.limit:
            return
        values = {key.lower(): value or "" for key, value in attrs}
        rel = {part.lower() for part in values.get("rel", "").split()}
        href = values.get("href", "").strip()
        if "stylesheet" in rel and href:
            self.hrefs.append(href)


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _has_symlink_component(path: Path, root: Path) -> bool:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return True
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def linked_stylesheet_files(
    html_path: Path,
    project_root: Path,
    *,
    asset_root: Path | None = None,
    max_links: int = 64,
) -> tuple[list[Path], list[str]]:
    """Resolve bounded local CSS links without leaving or tunneling through a project."""

    if max_links < 1:
        return [], ["linked stylesheet scan disabled by a non-positive limit"]
    html_path = html_path.expanduser().resolve()
    project_root = project_root.expanduser().resolve()
    asset_root = asset_root.expanduser().resolve() if asset_root is not None else None
    if asset_root is not None and not _inside(asset_root, project_root):
        return [], ["root-relative stylesheet asset root leaves the project boundary"]
    try:
        if html_path.stat().st_size > MAX_HTML_BYTES:
            return [], [f"HTML exceeds the {MAX_HTML_BYTES}-byte linked stylesheet scan bound"]
        source = html_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [], [f"unable to read HTML for linked stylesheets: {exc}"]
    parser = _StylesheetLinks(limit=max_links)
    try:
        parser.feed(source)
    except Exception as exc:
        return [], [f"unable to parse linked stylesheets: {exc}"]

    files: list[Path] = []
    issues: list[str] = []
    seen: set[Path] = set()
    for href in parser.hrefs:
        try:
            parsed = urlsplit(href)
        except ValueError:
            issues.append(f"rejected malformed stylesheet URL: {redact_url_userinfo(href)}")
            continue
        if parsed.scheme or parsed.netloc or href.startswith("//"):
            continue
        decoded = unquote(parsed.path)
        if not decoded or "\x00" in decoded:
            issues.append("rejected empty or invalid local stylesheet path")
            continue
        if decoded.startswith("/"):
            if asset_root is None:
                issues.append(
                    f"skipped ambiguous root-relative stylesheet without a package asset root: {decoded}"
                )
                continue
            lexical = asset_root / decoded.lstrip("/")
        else:
            lexical = html_path.parent / decoded
        resolved = lexical.resolve()
        if not _inside(resolved, project_root):
            issues.append(f"rejected stylesheet outside project root: {decoded}")
            continue
        if _has_symlink_component(lexical, project_root):
            issues.append(f"rejected stylesheet through symlink: {decoded}")
            continue
        if resolved.suffix.lower() != ".css" or not resolved.is_file():
            continue
        if resolved not in seen:
            files.append(resolved)
            seen.add(resolved)
    return files, issues
