from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from scripts.design_craft_evidence_common import (
    digest_snapshot,
    sha256_bytes,
    sha256_file,
)

from ..repo import REPO_ROOT


GRAPH_SCHEMA = "design-craft.evidence-graph.v2"
DOMAIN_FINGERPRINT_SCHEMA = "design-craft.evidence-domain-fingerprint.v2"
GRAPH_RELATIVE_PATH = Path("contracts/evaluation/evidence-graph.json")
DOMAIN_PATTERN = re.compile(r"[a-z0-9][a-z0-9-]*")
BINDING_KINDS = ("cross_agent", "comparative", "operational")


class EvidenceGraphError(ValueError):
    pass


def graph_path(root: Path = REPO_ROOT) -> Path:
    return root.expanduser().resolve() / GRAPH_RELATIVE_PATH


def load_graph(root: Path = REPO_ROOT) -> dict[str, object]:
    path = graph_path(root)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceGraphError(f"cannot load {path}: {exc}") from exc
    errors = graph_errors(payload)
    if errors:
        raise EvidenceGraphError("; ".join(errors))
    return payload


def graph_errors(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return ["evidence graph must be a JSON object"]
    errors: list[str] = []
    if set(payload) != {"schema", "domains", "bindings"}:
        errors.append("evidence graph keys must be schema, domains, and bindings")
    if payload.get("schema") != GRAPH_SCHEMA:
        errors.append(f"evidence graph schema must be {GRAPH_SCHEMA}")

    domains = payload.get("domains")
    if not isinstance(domains, dict) or not domains:
        return [*errors, "evidence graph domains must be a non-empty object"]
    for domain, definition in domains.items():
        if not isinstance(domain, str) or DOMAIN_PATTERN.fullmatch(domain) is None:
            errors.append(f"invalid evidence domain id: {domain!r}")
            continue
        if not isinstance(definition, dict) or set(definition) != {"extends", "include"}:
            errors.append(f"domain {domain} must contain extends and include")
            continue
        parents = definition.get("extends")
        patterns = definition.get("include")
        if not isinstance(parents, list) or any(
            not isinstance(parent, str) for parent in parents
        ):
            errors.append(f"domain {domain}.extends must be an array of domain ids")
        if not isinstance(patterns, list) or any(
            not isinstance(pattern, str) or not pattern.strip() for pattern in patterns
        ):
            errors.append(f"domain {domain}.include must be an array of path patterns")
        elif not parents and not patterns:
            errors.append(f"domain {domain} must include or extend at least one file set")
        for pattern in patterns if isinstance(patterns, list) else ():
            candidate = Path(pattern)
            if candidate.is_absolute() or ".." in candidate.parts:
                errors.append(f"domain {domain} has unsafe include pattern {pattern!r}")

    if isinstance(domains, dict):
        for domain, definition in domains.items():
            if not isinstance(definition, dict):
                continue
            for parent in definition.get("extends", ()):
                if parent not in domains:
                    errors.append(f"domain {domain} extends unknown domain {parent}")
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(domain: str) -> None:
            if domain in visited or domain not in domains:
                return
            if domain in visiting:
                errors.append(f"evidence domain cycle includes {domain}")
                return
            visiting.add(domain)
            definition = domains.get(domain)
            if isinstance(definition, dict):
                for parent in definition.get("extends", ()):
                    if isinstance(parent, str):
                        visit(parent)
            visiting.remove(domain)
            visited.add(domain)

        for domain in domains:
            visit(domain)

    bindings = payload.get("bindings")
    if not isinstance(bindings, dict) or set(bindings) != set(BINDING_KINDS):
        errors.append(f"evidence graph bindings must contain {list(BINDING_KINDS)}")
    else:
        for kind in BINDING_KINDS:
            values = bindings.get(kind)
            if not isinstance(values, dict) or not values:
                errors.append(f"bindings.{kind} must be a non-empty object")
                continue
            for identifier, domain in values.items():
                if not isinstance(identifier, str) or not identifier.strip():
                    errors.append(f"bindings.{kind} contains an invalid identifier")
                if not isinstance(domain, str) or domain not in domains:
                    errors.append(
                        f"bindings.{kind}.{identifier} references unknown domain {domain!r}"
                    )
    return errors


def repository_graph_errors(root: Path = REPO_ROOT) -> list[str]:
    root = root.expanduser().resolve()
    try:
        payload = load_graph(root)
    except EvidenceGraphError as exc:
        return [str(exc)]

    errors: list[str] = []
    bindings = payload["bindings"]
    expected = {
        "cross_agent": {
            path.name
            for path in (root / "evals/cross-agent").glob("same-prompt-*")
            if path.is_dir()
        },
        "comparative": {
            path.name
            for path in (root / "evals/comparative").iterdir()
            if path.is_dir() and path.name != "history" and not path.name.startswith("_")
        },
    }
    for kind, identifiers in expected.items():
        observed = set(bindings[kind])
        if observed != identifiers:
            errors.append(
                f"bindings.{kind} mismatch missing={sorted(identifiers - observed)} "
                f"extra={sorted(observed - identifiers)}"
            )
    for domain in payload["domains"]:
        try:
            resolve_domain_files(root, domain, payload=payload)
        except EvidenceGraphError as exc:
            errors.append(str(exc))
    return errors


def binding_domain(
    kind: str,
    identifier: str,
    *,
    root: Path = REPO_ROOT,
    payload: dict[str, object] | None = None,
) -> str:
    graph = payload or load_graph(root)
    if kind not in BINDING_KINDS:
        raise EvidenceGraphError(f"unknown evidence binding kind: {kind}")
    bindings = graph["bindings"]
    assert isinstance(bindings, dict)
    values = bindings[kind]
    assert isinstance(values, dict)
    domain = values.get(identifier)
    if not isinstance(domain, str):
        raise EvidenceGraphError(f"missing evidence domain binding for {kind}:{identifier}")
    return domain


def _domain_patterns(
    payload: dict[str, object], domain: str, *, stack: tuple[str, ...] = ()
) -> list[str]:
    domains = payload["domains"]
    assert isinstance(domains, dict)
    definition = domains.get(domain)
    if not isinstance(definition, dict):
        raise EvidenceGraphError(f"unknown evidence domain: {domain}")
    if domain in stack:
        raise EvidenceGraphError(f"evidence domain cycle includes {domain}")
    patterns: list[str] = []
    for parent in definition["extends"]:
        patterns.extend(_domain_patterns(payload, parent, stack=(*stack, domain)))
    patterns.extend(definition["include"])
    return patterns


def resolve_domain_files(
    root: Path,
    domain: str,
    *,
    payload: dict[str, object] | None = None,
) -> tuple[Path, ...]:
    root = root.expanduser().resolve()
    graph = payload or load_graph(root)
    matched: dict[str, Path] = {}
    for pattern in _domain_patterns(graph, domain):
        paths = sorted(path for path in root.glob(pattern) if path.is_file())
        if not paths:
            raise EvidenceGraphError(
                f"evidence domain {domain} pattern matched no files: {pattern}"
            )
        for path in paths:
            resolved = path.resolve()
            try:
                relative = resolved.relative_to(root).as_posix()
            except ValueError as exc:
                raise EvidenceGraphError(
                    f"evidence domain {domain} escaped repository root: {path}"
                ) from exc
            matched[relative] = resolved
    if not matched:
        raise EvidenceGraphError(f"evidence domain {domain} resolved no files")
    return tuple(matched[relative] for relative in sorted(matched))


def domain_fingerprint(
    root: Path,
    domain: str,
    *,
    payload: dict[str, object] | None = None,
) -> str:
    root = root.expanduser().resolve()
    files = resolve_domain_files(root, domain, payload=payload)
    material = {
        "schema": DOMAIN_FINGERPRINT_SCHEMA,
        "domain": domain,
        "files": {
            path.relative_to(root).as_posix(): sha256_file(path) for path in files
        },
    }
    encoded = json.dumps(
        material, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return sha256_bytes(encoded)


def git_domain_fingerprint(root: Path, domain: str, commit: str) -> str:
    root = root.expanduser().resolve()
    material: dict[str, str] = {}
    for path in resolve_domain_files(root, domain):
        relative = path.relative_to(root).as_posix()
        result = subprocess.run(
            ["git", "-C", str(root), "show", f"{commit}:./{relative}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0:
            detail = result.stderr.decode("utf-8", errors="replace").strip()
            raise EvidenceGraphError(
                f"cannot read evidence domain {domain} at {commit}: {relative}: {detail}"
            )
        material[relative] = sha256_bytes(result.stdout)
    encoded = json.dumps(
        {
            "schema": DOMAIN_FINGERPRINT_SCHEMA,
            "domain": domain,
            "files": material,
        },
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256_bytes(encoded)


def domain_dirty(root: Path, domain: str) -> bool:
    root = root.expanduser().resolve()
    relative_paths = [
        path.relative_to(root).as_posix()
        for path in resolve_domain_files(root, domain)
    ]
    result = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--",
            *relative_paths,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise EvidenceGraphError(
            f"cannot inspect evidence domain {domain} dirty state: {detail}"
        )
    return bool(result.stdout)


def skill_projection_paths(
    root: Path,
    skill_root: Path,
    domain: str,
) -> tuple[Path, ...]:
    root = root.expanduser().resolve()
    skill_root = skill_root.expanduser().resolve()
    paths = resolve_domain_files(root, domain)
    outside = [path for path in paths if skill_root not in path.parents]
    if outside:
        display = ", ".join(path.relative_to(root).as_posix() for path in outside)
        raise EvidenceGraphError(
            f"skill evidence domain {domain} contains non-skill files: {display}"
        )
    if skill_root / "SKILL.md" not in paths:
        raise EvidenceGraphError(f"skill evidence domain {domain} must include SKILL.md")
    return paths


def projected_skill_tree_sha256(root: Path, skill_root: Path, domain: str) -> str:
    skill_root = skill_root.expanduser().resolve()
    values = {
        path.relative_to(skill_root).as_posix(): sha256_file(path)
        for path in skill_projection_paths(root, skill_root, domain)
    }
    return digest_snapshot(values)


def git_projected_skill_tree_sha256(
    root: Path,
    skill_root: Path,
    domain: str,
    commit: str,
) -> str:
    root = root.expanduser().resolve()
    skill_root = skill_root.expanduser().resolve()
    values: dict[str, str] = {}
    for path in skill_projection_paths(root, skill_root, domain):
        repository_relative = path.relative_to(root).as_posix()
        projection_relative = path.relative_to(skill_root).as_posix()
        result = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "show",
                f"{commit}:./{repository_relative}",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0:
            detail = result.stderr.decode("utf-8", errors="replace").strip()
            raise EvidenceGraphError(
                f"cannot read projected skill domain {domain} at {commit}: "
                f"{repository_relative}: {detail}"
            )
        values[projection_relative] = sha256_bytes(result.stdout)
    return digest_snapshot(values)


def project_skill_domain(
    root: Path,
    skill_root: Path,
    domain: str,
    destination: Path,
) -> Path:
    skill_root = skill_root.expanduser().resolve()
    destination = destination.expanduser().resolve()
    if destination.exists():
        raise EvidenceGraphError(f"skill projection destination already exists: {destination}")
    destination.mkdir(parents=True)
    for source in skill_projection_paths(root, skill_root, domain):
        target = destination / source.relative_to(skill_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    observed = digest_snapshot(
        {
            path.relative_to(destination).as_posix(): sha256_file(path)
            for path in sorted(destination.rglob("*"))
            if path.is_file()
        }
    )
    expected = projected_skill_tree_sha256(root, skill_root, domain)
    if observed != expected:
        raise EvidenceGraphError(
            f"projected skill tree does not match evidence domain {domain}"
        )
    return destination


def graph_is_tracked(root: Path = REPO_ROOT) -> bool:
    root = root.expanduser().resolve()
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--error-unmatch", str(GRAPH_RELATIVE_PATH)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0
