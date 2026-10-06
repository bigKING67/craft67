from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ..repo import REPO_ROOT
from .integrity import repository_head, repository_version


OBSERVATION_SCHEMA = "design-craft.github-run-observation.v1"
ARTIFACT_OBSERVATION_SCHEMA = "design-craft.github-artifact-observation.v1"
RUN_KEYS = {
    "id",
    "attempt",
    "workflow",
    "workflow_name",
    "event",
    "head_branch",
    "head_sha",
    "status",
    "conclusion",
    "url",
    "repository",
}
WORKFLOW_BINDING_KEYS = {
    "repository",
    "run_id",
    "run_attempt",
    "url",
    "event",
    "head_sha",
    "ref",
}
ARTIFACT_KEYS = {
    "id",
    "name",
    "size_in_bytes",
    "digest",
    "expired",
    "created_at",
    "updated_at",
    "workflow_run",
}


@dataclass(frozen=True)
class RunContract:
    kind: str
    workflow_path: str
    workflow_name: str
    event: str
    workflow_file: str
    tag_bound: bool = False

    def head_branch(self, version: str) -> str:
        return f"v{version}" if self.tag_bound else "main"

    def ref(self, version: str) -> str:
        prefix = "tags" if self.tag_bound else "heads"
        return f"refs/{prefix}/{self.head_branch(version)}"


RUN_CONTRACTS = {
    "native": RunContract(
        kind="native",
        workflow_path=".github/workflows/native-runtime.yml",
        workflow_name="Native runtime evidence",
        event="push",
        workflow_file="native-runtime.yml",
        tag_bound=True,
    ),
    "benchmark": RunContract(
        kind="benchmark",
        workflow_path=".github/workflows/benchmark.yml",
        workflow_name="Performance benchmark",
        event="workflow_dispatch",
        workflow_file="benchmark.yml",
        tag_bound=True,
    ),
    "physical": RunContract(
        kind="physical",
        workflow_path=".github/workflows/physical-device.yml",
        workflow_name="Physical device evidence",
        event="workflow_dispatch",
        workflow_file="physical-device.yml",
    ),
    "certification": RunContract(
        kind="certification",
        workflow_path=".github/workflows/release-certify.yml",
        workflow_name="Release certification",
        event="workflow_dispatch",
        workflow_file="release-certify.yml",
    ),
}
NATIVE_WORKFLOW_PATH = RUN_CONTRACTS["native"].workflow_path
NATIVE_WORKFLOW_NAME = RUN_CONTRACTS["native"].workflow_name
PHYSICAL_WORKFLOW_PATH = RUN_CONTRACTS["physical"].workflow_path
PHYSICAL_WORKFLOW_NAME = RUN_CONTRACTS["physical"].workflow_name
CERTIFICATION_WORKFLOW_PATH = RUN_CONTRACTS["certification"].workflow_path
CERTIFICATION_WORKFLOW_NAME = RUN_CONTRACTS["certification"].workflow_name
BENCHMARK_WORKFLOW_PATH = RUN_CONTRACTS["benchmark"].workflow_path
BENCHMARK_WORKFLOW_NAME = RUN_CONTRACTS["benchmark"].workflow_name


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


def _json_output(result: subprocess.CompletedProcess[str], label: str) -> object:
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"cannot query {label}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid JSON from {label}: {exc}") from exc


def repository_name(explicit: str | None = None) -> str:
    if explicit:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", explicit):
            raise ValueError("GitHub repository must be owner/name")
        return explicit
    if not shutil.which("gh"):
        raise RuntimeError("gh CLI is required to inspect GitHub workflow runs")
    result = _run(
        ["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"]
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError(result.stderr.strip() or "cannot resolve GitHub repository")
    return repository_name(result.stdout.strip())


def _expected_run_values(expected_run: dict[str, object]) -> dict[str, object]:
    return {
        "id": expected_run.get("databaseId", expected_run.get("id")),
        "attempt": expected_run.get("attempt"),
        "workflow_name": expected_run.get(
            "workflowName", expected_run.get("workflow_name")
        ),
        "event": expected_run.get("event"),
        "head_branch": expected_run.get(
            "headBranch", expected_run.get("head_branch")
        ),
        "head_sha": expected_run.get("headSha", expected_run.get("head_sha")),
        "status": expected_run.get("status"),
        "conclusion": expected_run.get("conclusion"),
        "url": expected_run.get("url"),
    }


def validate_run(
    observed: dict[str, object],
    *,
    kind: str,
    expected_run: dict[str, object] | None = None,
    version: str | None = None,
    head: str | None = None,
) -> list[str]:
    contract = RUN_CONTRACTS[kind]
    errors: list[str] = []
    expected_version = version or repository_version()
    expected_head = head or repository_head()
    label = f"{kind} GitHub run"
    if set(observed) != RUN_KEYS:
        errors.append(
            f"{label} fields mismatch expected={sorted(RUN_KEYS)} "
            f"actual={sorted(observed)}"
        )
    run_id = observed.get("id")
    if not isinstance(run_id, int) or isinstance(run_id, bool) or run_id <= 0:
        errors.append(f"{label} id must be a positive integer")
    attempt = observed.get("attempt")
    if not isinstance(attempt, int) or isinstance(attempt, bool) or attempt <= 0:
        errors.append(f"{label} attempt must be a positive integer")
    if observed.get("workflow") != contract.workflow_path:
        errors.append(f"{label} workflow must be {contract.workflow_path}")
    if observed.get("workflow_name") != contract.workflow_name:
        errors.append(f"{label} workflow_name must be {contract.workflow_name}")
    if observed.get("event") != contract.event:
        errors.append(f"{label} event must be {contract.event}")
    expected_branch = contract.head_branch(expected_version)
    if observed.get("head_branch") != expected_branch:
        errors.append(f"{label} head_branch must be {expected_branch}")
    if observed.get("head_sha") != expected_head:
        errors.append(f"{label} head_sha must match current HEAD")
    if observed.get("status") != "completed":
        errors.append(f"{label} status must be completed")
    if observed.get("conclusion") != "success":
        errors.append(f"{label} conclusion must be success")
    repository = observed.get("repository")
    if not isinstance(repository, str) or not re.fullmatch(
        r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository
    ):
        errors.append(f"{label} repository must be owner/name")
    expected_url = (
        f"https://github.com/{repository}/actions/runs/{run_id}"
        if isinstance(repository, str)
        and isinstance(run_id, int)
        and not isinstance(run_id, bool)
        else None
    )
    if observed.get("url") != expected_url:
        errors.append(f"{label} url must match repository and run id")
    if expected_run is not None:
        for key, expected_value in _expected_run_values(expected_run).items():
            if expected_value is not None and observed.get(key) != expected_value:
                errors.append(f"{label} {key} must match the selected workflow run")
    return errors


def latest_native_tag_run(repository: str) -> dict[str, object]:
    head = repository_head()
    tag = f"v{repository_version()}"
    result = _run(
        [
            "gh",
            "run",
            "list",
            "--repo",
            repository_name(repository),
            "--workflow",
            RUN_CONTRACTS["native"].workflow_file,
            "--commit",
            head,
            "--limit",
            "20",
            "--json",
            (
                "attempt,databaseId,status,conclusion,headSha,headBranch,url,event,"
                "createdAt,workflowName"
            ),
        ]
    )
    payload = _json_output(result, "native-runtime.yml runs")
    if not isinstance(payload, list):
        raise RuntimeError("native-runtime.yml run list must be an array")
    matching = [
        item
        for item in payload
        if isinstance(item, dict)
        and item.get("headSha") == head
        and item.get("headBranch") == tag
        and item.get("event") == "push"
    ]
    matching.sort(key=lambda item: str(item.get("createdAt", "")), reverse=True)
    if not matching:
        raise RuntimeError(f"native-runtime.yml has no tag-push run for {tag} at {head}")
    latest = matching[0]
    if latest.get("status") != "completed" or latest.get("conclusion") != "success":
        raise RuntimeError(
            "latest native-runtime.yml tag-push run is not completed/success: "
            + str(latest.get("url", "unknown run"))
        )
    return latest


def observe_run(
    kind: str,
    run_id: str | int,
    *,
    repository: str | None = None,
    require_latest: bool | None = None,
) -> dict[str, object]:
    contract = RUN_CONTRACTS[kind]
    raw_id = str(run_id)
    if not re.fullmatch(r"[1-9][0-9]*", raw_id):
        raise ValueError(f"{kind} GitHub run id must contain only decimal digits")
    repo = repository_name(repository)
    view = _json_output(
        _run(
            [
                "gh",
                "run",
                "view",
                raw_id,
                "--repo",
                repo,
                "--json",
                (
                    "attempt,conclusion,databaseId,event,headBranch,headSha,status,"
                    "url,workflowName"
                ),
            ]
        ),
        f"GitHub run {raw_id}",
    )
    api = _json_output(
        _run(["gh", "api", f"repos/{repo}/actions/runs/{raw_id}"]),
        f"GitHub run API {raw_id}",
    )
    if not isinstance(view, dict) or not isinstance(api, dict):
        raise RuntimeError("GitHub run observation must be an object")
    observed: dict[str, object] = {
        "id": view.get("databaseId"),
        "attempt": view.get("attempt"),
        "workflow": api.get("path"),
        "workflow_name": view.get("workflowName"),
        "event": view.get("event"),
        "head_branch": view.get("headBranch"),
        "head_sha": view.get("headSha"),
        "status": view.get("status"),
        "conclusion": view.get("conclusion"),
        "url": view.get("url"),
        "repository": repo,
    }
    errors = validate_run(observed, kind=kind)
    if api.get("id") != observed["id"]:
        errors.append("gh run view and Actions API disagree on run id")
    if api.get("run_attempt") != observed["attempt"]:
        errors.append("gh run view and Actions API disagree on run attempt")
    if api.get("html_url") != observed["url"]:
        errors.append("gh run view and Actions API disagree on run url")
    if api.get("name") not in {None, contract.workflow_name}:
        errors.append("gh run view and Actions API disagree on workflow name")
    for api_key, observed_key in (
        ("event", "event"),
        ("head_branch", "head_branch"),
        ("head_sha", "head_sha"),
        ("status", "status"),
        ("conclusion", "conclusion"),
    ):
        if api.get(api_key) != observed[observed_key]:
            errors.append(
                f"gh run view and Actions API disagree on {observed_key}"
            )
    api_repository = api.get("repository")
    if (
        not isinstance(api_repository, dict)
        or api_repository.get("full_name") != observed["repository"]
    ):
        errors.append("Actions API repository does not match the selected repository")
    latest_required = kind == "native" if require_latest is None else require_latest
    if latest_required:
        if kind != "native":
            raise ValueError("only native tag runs support latest-run enforcement")
        latest = latest_native_tag_run(repo)
        if latest.get("databaseId") != observed["id"]:
            errors.append("selected run is not the latest successful native tag-push run")
        errors.extend(validate_run(observed, kind=kind, expected_run=latest))
    if errors:
        raise RuntimeError("; ".join(errors))
    return observed


def observation_document(kind: str, run: dict[str, object]) -> dict[str, object]:
    errors = validate_run(run, kind=kind)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "schema": OBSERVATION_SCHEMA,
        "kind": kind,
        "source_commit": repository_head(),
        "run": run,
    }


def observe_artifact(
    artifact_id: str | int,
    *,
    run: dict[str, object],
    expected_name: str,
) -> dict[str, object]:
    raw_id = str(artifact_id)
    if not re.fullmatch(r"[1-9][0-9]*", raw_id):
        raise ValueError("GitHub artifact id must contain only decimal digits")
    repository = run.get("repository")
    if not isinstance(repository, str):
        raise ValueError("certification run repository is invalid")
    payload = _json_output(
        _run(["gh", "api", f"repos/{repository}/actions/artifacts/{raw_id}"]),
        f"GitHub artifact {raw_id}",
    )
    if not isinstance(payload, dict):
        raise RuntimeError("GitHub artifact observation must be an object")
    workflow_run = payload.get("workflow_run")
    digest = payload.get("digest")
    errors: list[str] = []
    if payload.get("id") != int(raw_id):
        errors.append("artifact API id does not match the selected artifact")
    if payload.get("name") != expected_name:
        errors.append("artifact name does not match the certification contract")
    if payload.get("expired") is not False:
        errors.append("certification artifact must not be expired")
    if (
        not isinstance(payload.get("size_in_bytes"), int)
        or isinstance(payload.get("size_in_bytes"), bool)
        or payload["size_in_bytes"] <= 0
    ):
        errors.append("certification artifact size must be positive")
    if not isinstance(digest, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is None:
        errors.append("certification artifact must expose a SHA-256 digest")
    for field in ("created_at", "updated_at"):
        if not isinstance(payload.get(field), str) or not payload[field]:
            errors.append(f"certification artifact must expose {field}")
    if not isinstance(workflow_run, dict):
        errors.append("certification artifact must include workflow_run identity")
    else:
        workflow_run_id = workflow_run.get("id")
        if (
            not isinstance(workflow_run_id, int)
            or isinstance(workflow_run_id, bool)
            or workflow_run_id <= 0
        ):
            errors.append("certification artifact workflow_run.id must be positive")
        for artifact_key, run_key in (
            ("id", "id"),
            ("head_branch", "head_branch"),
            ("head_sha", "head_sha"),
        ):
            if workflow_run.get(artifact_key) != run.get(run_key):
                errors.append(
                    f"certification artifact workflow_run.{artifact_key} must match the selected run"
                )
    if errors:
        raise RuntimeError("; ".join(errors))
    return {
        "id": payload["id"],
        "name": payload["name"],
        "size_in_bytes": payload["size_in_bytes"],
        "digest": digest,
        "expired": payload["expired"],
        "created_at": payload.get("created_at"),
        "updated_at": payload.get("updated_at"),
        "workflow_run": {
            "id": workflow_run["id"],
            "head_branch": workflow_run["head_branch"],
            "head_sha": workflow_run["head_sha"],
        },
    }


def artifact_observation_document(
    artifact: dict[str, object],
    *,
    repository: str,
) -> dict[str, object]:
    if re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) is None:
        raise ValueError("GitHub artifact observation repository must be owner/name")
    return {
        "schema": ARTIFACT_OBSERVATION_SCHEMA,
        "source_commit": repository_head(),
        "repository": repository,
        "artifact": artifact,
    }


def load_artifact_observation(
    path: Path,
    *,
    expected_repository: str | None = None,
) -> dict[str, object]:
    if path.is_symlink() or not path.is_file():
        raise FileNotFoundError(f"GitHub artifact observation is missing or unsafe: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or set(payload) != {
        "schema",
        "source_commit",
        "repository",
        "artifact",
    }:
        raise ValueError("GitHub artifact observation document fields are invalid")
    if payload.get("schema") != ARTIFACT_OBSERVATION_SCHEMA:
        raise ValueError(
            f"GitHub artifact observation must use {ARTIFACT_OBSERVATION_SCHEMA}"
        )
    if payload.get("source_commit") != repository_head():
        raise ValueError("GitHub artifact observation source_commit must match current HEAD")
    repository = payload.get("repository")
    if not isinstance(repository, str) or re.fullmatch(
        r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository
    ) is None:
        raise ValueError("GitHub artifact observation repository must be owner/name")
    if expected_repository is not None:
        if re.fullmatch(
            r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", expected_repository
        ) is None:
            raise ValueError("expected GitHub repository must be owner/name")
        if repository != expected_repository:
            raise ValueError(
                "GitHub artifact observation repository does not match the certification"
            )
    artifact = payload.get("artifact")
    if not isinstance(artifact, dict):
        raise ValueError("GitHub artifact observation artifact must be an object")
    if set(artifact) != ARTIFACT_KEYS:
        raise ValueError("GitHub artifact observation artifact fields are invalid")
    if not isinstance(artifact.get("id"), int) or isinstance(artifact.get("id"), bool):
        raise ValueError("GitHub artifact observation id must be a positive integer")
    if artifact["id"] <= 0:
        raise ValueError("GitHub artifact observation id must be a positive integer")
    if not isinstance(artifact.get("name"), str) or not artifact["name"]:
        raise ValueError("GitHub artifact observation name must be non-empty")
    if (
        not isinstance(artifact.get("size_in_bytes"), int)
        or isinstance(artifact.get("size_in_bytes"), bool)
        or artifact["size_in_bytes"] <= 0
    ):
        raise ValueError("GitHub artifact observation size must be positive")
    if not isinstance(artifact.get("digest"), str) or re.fullmatch(
        r"sha256:[0-9a-f]{64}", artifact["digest"]
    ) is None:
        raise ValueError("GitHub artifact observation digest must be SHA-256")
    if artifact.get("expired") is not False:
        raise ValueError("GitHub artifact observation must not be expired")
    for field in ("created_at", "updated_at"):
        if not isinstance(artifact.get(field), str) or not artifact[field]:
            raise ValueError(f"GitHub artifact observation {field} must be non-empty")
    workflow_run = artifact.get("workflow_run")
    if not isinstance(workflow_run, dict) or set(workflow_run) != {
        "id",
        "head_branch",
        "head_sha",
    }:
        raise ValueError("GitHub artifact observation workflow_run is invalid")
    workflow_run_id = workflow_run.get("id")
    if (
        not isinstance(workflow_run_id, int)
        or isinstance(workflow_run_id, bool)
        or workflow_run_id <= 0
    ):
        raise ValueError("GitHub artifact observation workflow_run.id must be positive")
    if workflow_run.get("head_sha") != repository_head():
        raise ValueError("GitHub artifact observation workflow_run must match current HEAD")
    if workflow_run.get("head_branch") != "main":
        raise ValueError("GitHub artifact observation workflow_run must target main")
    return artifact


def load_observation(path: Path, *, expected_kind: str) -> dict[str, object]:
    if path.is_symlink() or not path.is_file():
        raise FileNotFoundError(f"GitHub run observation is missing or unsafe: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected_keys = {"schema", "kind", "source_commit", "run"}
    if not isinstance(payload, dict) or set(payload) != expected_keys:
        raise ValueError("GitHub run observation document fields are invalid")
    if payload.get("schema") != OBSERVATION_SCHEMA:
        raise ValueError(f"GitHub run observation must use {OBSERVATION_SCHEMA}")
    if payload.get("kind") != expected_kind:
        raise ValueError(f"GitHub run observation kind must be {expected_kind}")
    if payload.get("source_commit") != repository_head():
        raise ValueError("GitHub run observation source_commit must match current HEAD")
    run = payload.get("run")
    if not isinstance(run, dict):
        raise ValueError("GitHub run observation run must be an object")
    errors = validate_run(run, kind=expected_kind)
    if errors:
        raise ValueError("; ".join(errors))
    return run


def workflow_binding(run: dict[str, object], *, kind: str) -> dict[str, object]:
    version = repository_version()
    contract = RUN_CONTRACTS[kind]
    return {
        "repository": run.get("repository"),
        "run_id": run.get("id"),
        "run_attempt": run.get("attempt"),
        "url": run.get("url"),
        "event": run.get("event"),
        "head_sha": run.get("head_sha"),
        "ref": contract.ref(version),
    }


def validate_workflow_binding(
    binding: object, run: dict[str, object], *, kind: str, label: str
) -> list[str]:
    if not isinstance(binding, dict):
        return [f"{label} workflow binding must be an object"]
    errors: list[str] = []
    if set(binding) != WORKFLOW_BINDING_KEYS:
        errors.append(
            f"{label} workflow fields mismatch expected={sorted(WORKFLOW_BINDING_KEYS)} "
            f"actual={sorted(binding)}"
        )
    expected = workflow_binding(run, kind=kind)
    for field, value in expected.items():
        if binding.get(field) != value:
            errors.append(f"{label} workflow {field} does not match selected {kind} run")
    return errors


__all__ = [
    "NATIVE_WORKFLOW_NAME",
    "NATIVE_WORKFLOW_PATH",
    "OBSERVATION_SCHEMA",
    "PHYSICAL_WORKFLOW_NAME",
    "PHYSICAL_WORKFLOW_PATH",
    "CERTIFICATION_WORKFLOW_NAME",
    "CERTIFICATION_WORKFLOW_PATH",
    "BENCHMARK_WORKFLOW_NAME",
    "BENCHMARK_WORKFLOW_PATH",
    "ARTIFACT_OBSERVATION_SCHEMA",
    "RUN_CONTRACTS",
    "RUN_KEYS",
    "ARTIFACT_KEYS",
    "latest_native_tag_run",
    "load_artifact_observation",
    "load_observation",
    "observation_document",
    "artifact_observation_document",
    "observe_artifact",
    "observe_run",
    "validate_run",
    "validate_workflow_binding",
    "workflow_binding",
]
