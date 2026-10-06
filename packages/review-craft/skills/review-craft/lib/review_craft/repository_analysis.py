from __future__ import annotations

import ast
import json
import posixpath
import re
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any

from .constants import PROFILES, SCHEMA_VERSION
from .repository import SourceReader, source_payload

MAX_ANALYZED_FILE_BYTES = 2 * 1024 * 1024
SOURCE_SUFFIXES = {".py", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"}
MODULE_CONTAINERS = {"apps", "packages", "services", "libs", "crates", "plugins", "skills"}
RUNTIME_CAPABILITY_DIRS = {"agents", "lib", "references", "schemas", "scripts", "templates"}
ENTRY_POINT_NAMES = {
    "__main__.py",
    "app.py",
    "cli.py",
    "index.js",
    "index.jsx",
    "index.ts",
    "index.tsx",
    "main.go",
    "main.py",
    "main.rs",
    "server.js",
    "server.ts",
}

JS_IMPORT_PATTERNS = (
    re.compile(r"(?:^|\s)(?:import|export)\s+(?:[^'\"]+?\s+from\s+)?['\"]([^'\"]+)['\"]"),
    re.compile(r"\brequire\(\s*['\"]([^'\"]+)['\"]\s*\)"),
    re.compile(r"\bimport\(\s*['\"]([^'\"]+)['\"]\s*\)"),
)


def _profile_text(
    root: Path, record: dict[str, Any] | None, skipped: list[str]
) -> str | None:
    if record is None:
        return None
    path = record["path"]
    if record["kind"] != "file" or record["binary"]:
        reason = "binary" if record["binary"] else record["kind"]
        skipped.append(f"skipped profile context {path}: {reason} inventory entry")
        return None
    try:
        return source_payload(root, record, diff_base=None).decode("utf-8")
    except (OSError, ValueError) as error:
        skipped.append(f"skipped profile context {path}: {type(error).__name__}")
        return None


def _profile_context(
    root: Path, records: list[dict[str, Any]]
) -> tuple[dict[str, Any], set[str], str, list[str]]:
    manifests = {row["path"]: row for row in records}
    skipped: list[str] = []
    package: dict[str, Any] = {}
    package_text = _profile_text(root, manifests.get("package.json"), skipped)
    if package_text is not None:
        try:
            value = json.loads(package_text)
            if not isinstance(value, dict):
                raise ValueError("package.json must contain an object")
            package = value
        except ValueError as error:
            skipped.append(f"skipped profile context package.json: {type(error).__name__}")
    dependencies: dict[str, Any] = {}
    for field in ("dependencies", "devDependencies", "peerDependencies"):
        value = package.get(field)
        if isinstance(value, dict):
            dependencies.update(value)
    pyproject_text = _profile_text(root, manifests.get("pyproject.toml"), skipped)
    return package, set(dependencies), pyproject_text or "", skipped


def _add_profile_signal(
    scores: Counter[str],
    signals: dict[str, list[str]],
    profile: str,
    weight: int,
    reason: str,
) -> None:
    scores[profile] += weight
    signals[profile].append(reason)


def _add_repository_shape_signals(
    paths: set[str],
    package: dict[str, Any],
    scores: Counter[str],
    signals: dict[str, list[str]],
) -> None:
    add = lambda profile, weight, reason: _add_profile_signal(  # noqa: E731
        scores, signals, profile, weight, reason
    )
    if any(path.endswith("/SKILL.md") or path == "SKILL.md" for path in paths):
        add("agent-project", 8, "contains an agent SKILL.md")
    if ".codex-plugin/plugin.json" in paths:
        add("agent-project", 6, "contains a Codex plugin manifest")
    if isinstance(package.get("workspaces"), (list, dict)) or any(
        path in paths for path in ("pnpm-workspace.yaml", "lerna.json", "nx.json")
    ):
        add("monorepo", 9, "declares a workspace or monorepo manifest")
    if any(path.startswith("apps/") for path in paths) and any(
        path.startswith("packages/") for path in paths
    ):
        add("monorepo", 5, "contains both apps/ and packages/")


def _add_runtime_signals(
    paths: set[str],
    dependency_names: set[str],
    scores: Counter[str],
    signals: dict[str, list[str]],
) -> None:
    if any(path.startswith("src-tauri/") for path in paths) or "electron" in dependency_names:
        _add_profile_signal(
            scores, signals, "desktop-app", 9, "contains Tauri or Electron runtime signals"
        )
    frontend_markers = {
        "react",
        "react-dom",
        "next",
        "vue",
        "nuxt",
        "svelte",
        "@angular/core",
        "vite",
    }
    if dependency_names & frontend_markers or "index.html" in paths:
        _add_profile_signal(
            scores,
            signals,
            "frontend",
            7,
            "contains a browser frontend framework or entry HTML",
        )
    backend_markers = {"express", "fastify", "koa", "@nestjs/core", "hapi"}
    if dependency_names & backend_markers or any(
        path in paths for path in ("manage.py", "wsgi.py", "asgi.py")
    ):
        _add_profile_signal(
            scores,
            signals,
            "backend-service",
            7,
            "contains a backend service framework or entrypoint",
        )
    if any(
        path in paths for path in ("dbt_project.yml", "airflow.cfg", "dvc.yaml", "prefect.yaml")
    ) or any(path.startswith(("dags/", "etl/", "pipelines/")) for path in paths):
        _add_profile_signal(
            scores, signals, "data-pipeline", 8, "contains data-pipeline manifests or directories"
        )


def _add_distribution_signals(
    paths: set[str],
    package: dict[str, Any],
    pyproject_text: str,
    scores: Counter[str],
    signals: dict[str, list[str]],
) -> None:
    if isinstance(package.get("bin"), (str, dict)):
        _add_profile_signal(scores, signals, "cli", 8, "package.json declares a CLI entry")
    if "[project.scripts]" in pyproject_text:
        _add_profile_signal(scores, signals, "cli", 7, "pyproject.toml declares project scripts")
    if any(PurePosixPath(path).name in {"__main__.py", "cli.py"} for path in paths):
        _add_profile_signal(scores, signals, "cli", 3, "contains a conventional CLI entry module")
    if any(key in package for key in ("main", "module", "exports", "types")):
        _add_profile_signal(scores, signals, "library", 5, "package.json declares library exports")
    if "[project]" in pyproject_text and not scores["backend-service"]:
        _add_profile_signal(
            scores, signals, "library", 3, "pyproject.toml declares a Python project"
        )


def detect_profile(root: Path, records: list[dict[str, Any]], requested: str) -> dict[str, Any]:
    if requested not in PROFILES:
        raise ValueError(f"unsupported profile: {requested}")
    if requested != "auto":
        return {
            "requested": requested,
            "resolved": requested,
            "confidence": "HIGH",
            "signals": [f"explicit profile: {requested}"],
        }

    paths = {row["path"] for row in records}
    package, dependency_names, pyproject_text, skipped = _profile_context(root, records)
    scores: Counter[str] = Counter()
    signals: dict[str, list[str]] = {profile: [] for profile in PROFILES if profile != "auto"}
    _add_repository_shape_signals(paths, package, scores, signals)
    _add_runtime_signals(paths, dependency_names, scores, signals)
    _add_distribution_signals(paths, package, pyproject_text, scores, signals)
    if not scores:
        _add_profile_signal(
            scores,
            signals,
            "application",
            1,
            "no stronger project profile signal was detected",
        )

    order = [
        "monorepo",
        "desktop-app",
        "agent-project",
        "data-pipeline",
        "backend-service",
        "frontend",
        "cli",
        "library",
        "application",
        "generic",
    ]
    resolved = min(order, key=lambda profile: (-scores[profile], order.index(profile)))
    score = scores[resolved]
    confidence = "HIGH" if score >= 8 else "MEDIUM" if score >= 4 else "LOW"
    return {
        "requested": requested,
        "resolved": resolved,
        "confidence": confidence,
        "signals": signals[resolved] + skipped,
    }


def module_id(path: str) -> str:
    parts = PurePosixPath(path).parts
    if len(parts) <= 1:
        return "."
    if (
        len(parts) >= 4
        and parts[0] in {"plugins", "skills"}
        and parts[2] in RUNTIME_CAPABILITY_DIRS
    ):
        return "/".join(parts[:3])
    if parts[0] in MODULE_CONTAINERS and len(parts) >= 3:
        return "/".join(parts[:2])
    if parts[0] == "src" and len(parts) >= 3:
        return "/".join(parts[:2])
    return parts[0]


def build_module_map(records: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in records:
        grouped.setdefault(module_id(row["path"]), []).append(row)
    modules: list[dict[str, Any]] = []
    for identifier in sorted(grouped):
        rows = grouped[identifier]
        entry_points = sorted(
            row["path"] for row in rows if PurePosixPath(row["path"]).name in ENTRY_POINT_NAMES
        )
        modules.append(
            {
                "id": identifier,
                "path": identifier,
                "fileCount": len(rows),
                "sourceFileCount": sum(
                    row.get("classification") == "source" and not row.get("binary", False)
                    for row in rows
                ),
                "totalBytes": sum(int(row.get("sizeBytes", 0)) for row in rows),
                "entryPoints": entry_points,
            }
        )
    return {
        "documentType": "review-craft.module-map",
        "schemaVersion": SCHEMA_VERSION,
        "strategy": (
            "repository path boundaries; plugin/skill runtime capability directories use three "
            "segments and other known container directories use two"
        ),
        "modules": modules,
    }


def _python_module_candidates(source: str, module: str, level: int) -> list[str]:
    source_path = PurePosixPath(source)
    source_parts = list(source_path.with_suffix("").parts)
    package_parts = source_parts[:-1]
    if source_path.name == "__init__.py":
        package_parts = source_parts[:-1]
    module_parts = module.split(".") if module else []
    if level:
        trim = max(level - 1, 0)
        base = package_parts[: len(package_parts) - trim] if trim else package_parts
        target = base + module_parts
    else:
        target = module_parts
    if not target:
        return []
    prefix = "/".join(target)
    candidates = [f"{prefix}.py", f"{prefix}/__init__.py"]
    if source_parts and source_parts[0] == "src" and not prefix.startswith("src/"):
        candidates.extend([f"src/{prefix}.py", f"src/{prefix}/__init__.py"])
    return candidates


def _resolve_python_import(source: str, module: str, level: int, files: set[str]) -> str | None:
    resolved = next(
        (
            candidate
            for candidate in _python_module_candidates(source, module, level)
            if candidate in files
        ),
        None,
    )
    if resolved is not None or level or not module:
        return resolved
    module_path = module.replace(".", "/")
    suffixes = (f"/{module_path}.py", f"/{module_path}/__init__.py")
    matches = sorted(
        path
        for path in files
        if path in {suffix[1:] for suffix in suffixes}
        or any(path.endswith(suffix) for suffix in suffixes)
    )
    return matches[0] if len(matches) == 1 else None


def _resolve_js_import(source: str, specifier: str, files: set[str]) -> str | None:
    if not specifier.startswith("."):
        return None
    base = PurePosixPath(source).parent.joinpath(specifier)
    normalized_parts: list[str] = []
    for part in base.parts:
        if part == ".":
            continue
        if part == "..":
            if not normalized_parts:
                return None
            normalized_parts.pop()
        else:
            normalized_parts.append(part)
    normalized = "/".join(normalized_parts)
    suffixes = ("", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx")
    candidates = [normalized + suffix for suffix in suffixes]
    candidates.extend(f"{normalized}/index{suffix}" for suffix in suffixes[1:])
    return next((candidate for candidate in candidates if candidate in files), None)


def build_dependency_map(root: Path, records: list[dict[str, Any]]) -> dict[str, Any]:
    analyzable = {
        row["path"]: row
        for row in records
        if row.get("kind") == "file"
        and row.get("classification") == "source"
        and not row.get("binary", False)
        and posixpath.splitext(row["path"])[1].lower() in SOURCE_SUFFIXES
    }
    files = set(analyzable)
    edges: set[tuple[str, str, str, int]] = set()
    skipped: list[dict[str, str]] = []
    analyzed = 0
    reader = SourceReader(root)
    for relative in sorted(analyzable):
        row = analyzable[relative]
        if int(row.get("sizeBytes", 0)) > MAX_ANALYZED_FILE_BYTES:
            skipped.append({"path": relative, "reason": "file exceeds the 2 MiB analysis limit"})
            continue
        try:
            text = reader.read(row, diff_base=None).decode("utf-8")
        except (OSError, UnicodeDecodeError) as error:
            skipped.append({"path": relative, "reason": type(error).__name__})
            continue
        suffix = posixpath.splitext(relative)[1].lower()
        try:
            if suffix == ".py":
                _add_python_edges(relative, text, files, edges)
            else:
                _add_javascript_edges(relative, text, files, edges)
        except SyntaxError:
            skipped.append({"path": relative, "reason": "Python syntax error"})
            continue
        analyzed += 1

    edge_rows = [
        {"from": source, "to": target, "kind": kind, "line": line}
        for source, target, kind, line in sorted(edges)
    ]
    module_counts: Counter[tuple[str, str]] = Counter()
    for row in edge_rows:
        source_module = module_id(row["from"])
        target_module = module_id(row["to"])
        if source_module != target_module:
            module_counts[(source_module, target_module)] += 1
    module_edges = [
        {"from": source, "to": target, "count": count}
        for (source, target), count in sorted(module_counts.items())
    ]
    return {
        "documentType": "review-craft.dependency-map",
        "schemaVersion": SCHEMA_VERSION,
        "filesAnalyzed": analyzed,
        "filesSkipped": skipped,
        "edges": edge_rows,
        "moduleEdges": module_edges,
        "limitations": [
            "Only current, non-deleted source files in the selected inventory are analyzed; "
            "deleted files are not parsed.",
            "Python imports are parsed with ast and resolved only within that selected inventory.",
            "Absolute Python imports outside the repository root are resolved only when a unique "
            "selected-inventory suffix matches.",
            "JavaScript and TypeScript imports use conservative line-based matching.",
            "Runtime, plugin, reflection, generated, and framework-injected edges require "
            "separate evidence.",
        ],
    }


def _add_python_edges(
    relative: str,
    text: str,
    files: set[str],
    edges: set[tuple[str, str, str, int]],
) -> None:
    tree = ast.parse(text, filename=relative)
    for node in ast.walk(tree):
        targets: list[str] = []
        if isinstance(node, ast.Import):
            targets.extend(alias.name for alias in node.names)
            level = 0
        elif isinstance(node, ast.ImportFrom):
            level = node.level
            base = node.module or ""
            targets.append(base)
            targets.extend(f"{base}.{alias.name}" if base else alias.name for alias in node.names)
        else:
            continue
        for target in targets:
            resolved = _resolve_python_import(relative, target, level, files)
            if resolved and resolved != relative:
                edges.add((relative, resolved, "python-import", node.lineno))


def _add_javascript_edges(
    relative: str,
    text: str,
    files: set[str],
    edges: set[tuple[str, str, str, int]],
) -> None:
    for line_number, line in enumerate(text.splitlines(), start=1):
        for pattern in JS_IMPORT_PATTERNS:
            for match in pattern.finditer(line):
                resolved = _resolve_js_import(relative, match.group(1), files)
                if resolved and resolved != relative:
                    edges.add((relative, resolved, "javascript-import", line_number))
