from __future__ import annotations

from concurrent.futures import Executor, ThreadPoolExecutor
from pathlib import Path

from .runtime_batch import RUNTIME_PROBE_WORKERS, submit_runtime_probe_batch
from .semantic_contract import semantic_paths
from .semantic_runtime import (
    route_probe_requests,
    runtime_validation,
    validate_schema_probe,
)
from .semantic_static import load_toml, static_validation


def semantic_validation(source_root: Path) -> dict:
    with ThreadPoolExecutor(max_workers=RUNTIME_PROBE_WORKERS) as executor:
        return _semantic_validation(source_root, executor)


def _semantic_validation(source_root: Path, executor: Executor) -> dict:
    paths = semantic_paths(source_root)
    probe_batch = submit_runtime_probe_batch(
        executor,
        source_root,
        route_probe_requests(),
    )

    # Static reads overlap the already-submitted runtime subprocesses. Results
    # are assembled in the original schema/error order after both paths finish.
    static_issues = static_validation(paths)
    schema_issues = validate_schema_probe(probe_batch)
    runtime = runtime_validation(paths, probe_batch)
    issues = [*schema_issues, *static_issues, *runtime.issues]
    warnings = runtime.warnings
    return {
        "status": "error" if issues else "warning" if warnings else "ok",
        "issues": issues,
        "warnings": warnings,
        "runtime_probes": runtime.probes,
        "route_modules": [path.name for path in paths.route_files],
        "runtime_profiles": runtime.profiles,
        "model_catalog_source": runtime.model_catalog_source,
    }


__all__ = ["load_toml", "semantic_validation"]
