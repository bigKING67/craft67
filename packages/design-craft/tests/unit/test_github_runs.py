from __future__ import annotations

import json
import subprocess
import unittest
from unittest.mock import patch

from tools.design_craft.release.github_runs import (
    BENCHMARK_WORKFLOW_NAME,
    BENCHMARK_WORKFLOW_PATH,
    CERTIFICATION_WORKFLOW_NAME,
    CERTIFICATION_WORKFLOW_PATH,
    NATIVE_WORKFLOW_NAME,
    NATIVE_WORKFLOW_PATH,
    PHYSICAL_WORKFLOW_NAME,
    PHYSICAL_WORKFLOW_PATH,
    latest_native_tag_run,
    observe_artifact,
    observe_run,
    validate_run,
    validate_workflow_binding,
)
from tools.design_craft.release.integrity import repository_version


HEAD = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
VERSION = repository_version()


def observed_run(run_id: int = 123) -> dict[str, object]:
    repository = "example/design-craft"
    return {
        "id": run_id,
        "attempt": 1,
        "workflow": NATIVE_WORKFLOW_PATH,
        "workflow_name": NATIVE_WORKFLOW_NAME,
        "event": "push",
        "head_branch": f"v{VERSION}",
        "head_sha": HEAD,
        "status": "completed",
        "conclusion": "success",
        "url": f"https://github.com/{repository}/actions/runs/{run_id}",
        "repository": repository,
    }


def listed_run(
    run_id: int, *, conclusion: str, created_at: str
) -> dict[str, object]:
    return {
        "databaseId": run_id,
        "attempt": 1,
        "workflowName": NATIVE_WORKFLOW_NAME,
        "event": "push",
        "headBranch": f"v{VERSION}",
        "headSha": HEAD,
        "status": "completed",
        "conclusion": conclusion,
        "url": f"https://github.com/example/design-craft/actions/runs/{run_id}",
        "createdAt": created_at,
    }


def physical_run(run_id: int = 456) -> dict[str, object]:
    repository = "example/design-craft"
    return {
        "id": run_id,
        "attempt": 2,
        "workflow": PHYSICAL_WORKFLOW_PATH,
        "workflow_name": PHYSICAL_WORKFLOW_NAME,
        "event": "workflow_dispatch",
        "head_branch": "main",
        "head_sha": HEAD,
        "status": "completed",
        "conclusion": "success",
        "url": f"https://github.com/{repository}/actions/runs/{run_id}",
        "repository": repository,
    }


def benchmark_run(run_id: int = 456) -> dict[str, object]:
    repository = "example/design-craft"
    return {
        "id": run_id,
        "attempt": 1,
        "workflow": BENCHMARK_WORKFLOW_PATH,
        "workflow_name": BENCHMARK_WORKFLOW_NAME,
        "event": "workflow_dispatch",
        "head_branch": f"v{VERSION}",
        "head_sha": HEAD,
        "status": "completed",
        "conclusion": "success",
        "url": f"https://github.com/{repository}/actions/runs/{run_id}",
        "repository": repository,
    }


def certification_run(run_id: int = 789) -> dict[str, object]:
    repository = "example/design-craft"
    return {
        "id": run_id,
        "attempt": 1,
        "workflow": CERTIFICATION_WORKFLOW_PATH,
        "workflow_name": CERTIFICATION_WORKFLOW_NAME,
        "event": "workflow_dispatch",
        "head_branch": "main",
        "head_sha": HEAD,
        "status": "completed",
        "conclusion": "success",
        "url": f"https://github.com/{repository}/actions/runs/{run_id}",
        "repository": repository,
    }


class NativeGitHubRunTests(unittest.TestCase):
    def test_valid_run_matches_current_tag_contract(self) -> None:
        self.assertEqual(validate_run(observed_run(), kind="native"), [])

    def test_valid_physical_run_matches_main_dispatch_contract(self) -> None:
        self.assertEqual(validate_run(physical_run(), kind="physical"), [])

    def test_valid_benchmark_run_matches_current_tag_contract(self) -> None:
        self.assertEqual(validate_run(benchmark_run(), kind="benchmark"), [])

    def test_benchmark_run_rejects_wrong_tag_or_source(self) -> None:
        wrong_branch = benchmark_run()
        wrong_branch["head_branch"] = "main"
        self.assertTrue(
            any(
                "head_branch" in error
                for error in validate_run(wrong_branch, kind="benchmark")
            )
        )
        wrong_source = benchmark_run()
        wrong_source["head_sha"] = "0" * 40
        self.assertTrue(
            any(
                "head_sha" in error
                for error in validate_run(wrong_source, kind="benchmark")
            )
        )

    def test_valid_certification_run_matches_main_dispatch_contract(self) -> None:
        self.assertEqual(validate_run(certification_run(), kind="certification"), [])

    def test_artifact_observation_binds_digest_and_certification_run(self) -> None:
        run = certification_run()
        result = subprocess.CompletedProcess(
            ["gh", "api"],
            0,
            stdout=json.dumps(
                {
                    "id": 900,
                    "name": "release-certification-v0.5.1-789",
                    "size_in_bytes": 1024,
                    "digest": f"sha256:{'a' * 64}",
                    "expired": False,
                    "created_at": "2026-07-23T00:00:00Z",
                    "updated_at": "2026-07-23T00:00:01Z",
                    "workflow_run": {
                        "id": run["id"],
                        "head_branch": run["head_branch"],
                        "head_sha": run["head_sha"],
                    },
                }
            ),
            stderr="",
        )
        with patch("tools.design_craft.release.github_runs._run", return_value=result):
            artifact = observe_artifact(
                900,
                run=run,
                expected_name="release-certification-v0.5.1-789",
            )
        self.assertEqual(artifact["digest"], f"sha256:{'a' * 64}")
        self.assertEqual(artifact["workflow_run"]["id"], run["id"])

    def test_artifact_observation_rejects_wrong_run(self) -> None:
        run = certification_run()
        result = subprocess.CompletedProcess(
            ["gh", "api"],
            0,
            stdout=json.dumps(
                {
                    "id": 900,
                    "name": "release-certification-v0.5.1-789",
                    "size_in_bytes": 1024,
                    "digest": f"sha256:{'a' * 64}",
                    "expired": False,
                    "workflow_run": {
                        "id": 999,
                        "head_branch": "main",
                        "head_sha": HEAD,
                    },
                }
            ),
            stderr="",
        )
        with patch("tools.design_craft.release.github_runs._run", return_value=result):
            with self.assertRaisesRegex(RuntimeError, "workflow_run.id"):
                observe_artifact(
                    900,
                    run=run,
                    expected_name="release-certification-v0.5.1-789",
                )

    def test_artifact_observation_requires_server_timestamps(self) -> None:
        run = certification_run()
        result = subprocess.CompletedProcess(
            ["gh", "api"],
            0,
            stdout=json.dumps(
                {
                    "id": 900,
                    "name": "release-certification-v0.5.1-789",
                    "size_in_bytes": 1024,
                    "digest": f"sha256:{'a' * 64}",
                    "expired": False,
                    "workflow_run": {
                        "id": run["id"],
                        "head_branch": run["head_branch"],
                        "head_sha": run["head_sha"],
                    },
                }
            ),
            stderr="",
        )
        with patch("tools.design_craft.release.github_runs._run", return_value=result):
            with self.assertRaisesRegex(RuntimeError, "created_at"):
                observe_artifact(
                    900,
                    run=run,
                    expected_name="release-certification-v0.5.1-789",
                )

    def test_selected_run_id_and_attempt_are_bound(self) -> None:
        expected = listed_run(124, conclusion="success", created_at="2026-01-01")
        expected["attempt"] = 2
        errors = validate_run(observed_run(), kind="native", expected_run=expected)
        self.assertTrue(any("run id" in error for error in errors))
        self.assertTrue(any("run attempt" in error for error in errors))

    def test_repository_and_url_must_identify_the_same_run(self) -> None:
        payload = observed_run()
        payload["url"] = "https://github.com/other/repo/actions/runs/123"
        self.assertTrue(
            any("url" in error for error in validate_run(payload, kind="native"))
        )

    def test_bool_is_not_accepted_as_a_run_number(self) -> None:
        payload = observed_run()
        payload["id"] = True
        payload["attempt"] = False
        errors = validate_run(payload, kind="native")
        self.assertTrue(any("id" in error for error in errors))
        self.assertTrue(any("attempt" in error for error in errors))

    def test_latest_failed_tag_run_blocks_an_older_success(self) -> None:
        payload = [
            listed_run(2, conclusion="failure", created_at="2026-01-02T00:00:00Z"),
            listed_run(1, conclusion="success", created_at="2026-01-01T00:00:00Z"),
        ]
        result = subprocess.CompletedProcess(
            ["gh"], 0, stdout=json.dumps(payload), stderr=""
        )
        with patch(
            "tools.design_craft.release.github_runs._run", return_value=result
        ):
            with self.assertRaisesRegex(RuntimeError, "latest.*not completed/success"):
                latest_native_tag_run("example/design-craft")

    def test_physical_workflow_binding_is_exact(self) -> None:
        run = physical_run()
        binding = {
            "repository": run["repository"],
            "run_id": run["id"],
            "run_attempt": run["attempt"],
            "url": run["url"],
            "event": run["event"],
            "head_sha": run["head_sha"],
            "ref": "refs/heads/main",
        }
        self.assertEqual(
            validate_workflow_binding(
                binding, run, kind="physical", label="physical evidence"
            ),
            [],
        )
        binding["ref"] = "refs/tags/main"
        self.assertTrue(
            any(
                "ref" in error
                for error in validate_workflow_binding(
                    binding, run, kind="physical", label="physical evidence"
                )
            )
        )

    def test_physical_observation_binds_view_and_actions_api(self) -> None:
        run = physical_run()
        view = subprocess.CompletedProcess(
            ["gh"],
            0,
            stdout=json.dumps(
                {
                    "databaseId": run["id"],
                    "attempt": run["attempt"],
                    "workflowName": run["workflow_name"],
                    "event": run["event"],
                    "headBranch": run["head_branch"],
                    "headSha": run["head_sha"],
                    "status": run["status"],
                    "conclusion": run["conclusion"],
                    "url": run["url"],
                }
            ),
            stderr="",
        )
        api = subprocess.CompletedProcess(
            ["gh"],
            0,
            stdout=json.dumps(
                {
                    "id": run["id"],
                    "run_attempt": run["attempt"],
                    "html_url": run["url"],
                    "path": run["workflow"],
                    "name": run["workflow_name"],
                    "event": run["event"],
                    "head_branch": run["head_branch"],
                    "head_sha": run["head_sha"],
                    "status": run["status"],
                    "conclusion": run["conclusion"],
                    "repository": {"full_name": run["repository"]},
                }
            ),
            stderr="",
        )
        with patch(
            "tools.design_craft.release.github_runs._run", side_effect=(view, api)
        ):
            observed = observe_run(
                "physical",
                run["id"],
                repository=str(run["repository"]),
                require_latest=False,
            )
        self.assertEqual(observed, run)


if __name__ == "__main__":
    unittest.main()
