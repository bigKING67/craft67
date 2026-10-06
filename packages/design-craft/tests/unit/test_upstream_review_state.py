from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.design_craft.repo import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts"))

from design_craft_absorption_common import validate_review_state  # noqa: E402


PINNED = "1" * 40
PREVIOUS_REVIEW = "2" * 40
ABSORBED = "3" * 40
REVIEWED = "4" * 40


def metadata() -> dict[str, str]:
    return {
        "commit": PINNED,
        "reviewed_commit": REVIEWED,
        "absorbed_commit": ABSORBED,
        "cumulative_status": "selective_absorbed",
        "reviewed_through_commit": REVIEWED,
        "behavior_absorbed_through_commit": ABSORBED,
        "latest_range_base_commit": PREVIOUS_REVIEW,
        "latest_range_head_commit": REVIEWED,
        "latest_range_status": "selective_absorbed",
        "reviewed_at": "2026-07-23",
        "decision": "partial",
        "notes": "reviewed",
    }


def git_output(_path: Path, *args: str) -> str:
    if args == ("rev-parse", "HEAD"):
        return PINNED
    if args == ("rev-parse", "--is-shallow-repository"):
        return "false"
    raise AssertionError(args)


class UpstreamReviewStateTests(unittest.TestCase):
    @patch("design_craft_absorption_common.git_success", return_value=True)
    @patch("design_craft_absorption_common.git_output", side_effect=git_output)
    @patch(
        "design_craft_absorption_common.subprocess.run",
        return_value=subprocess.CompletedProcess([], 0),
    )
    def test_reviewed_remote_head_can_advance_without_pinned_source(
        self, _run: object, _git_output: object, _git_success: object
    ) -> None:
        state, errors = validate_review_state("fixture", metadata(), Path("fixture"))

        self.assertEqual(errors, [])
        self.assertEqual(state["current_commit"], PINNED)
        self.assertEqual(state["reviewed_through_commit"], REVIEWED)
        self.assertEqual(state["latest_range_base_commit"], PREVIOUS_REVIEW)
        self.assertEqual(state["behavior_absorbed_through_commit"], ABSORBED)

    @patch("design_craft_absorption_common.git_success", return_value=False)
    @patch("design_craft_absorption_common.git_output", side_effect=git_output)
    def test_latest_range_head_must_equal_reviewed_boundary(
        self, _git_output: object, _git_success: object
    ) -> None:
        payload = metadata()
        payload["latest_range_head_commit"] = "5" * 40

        _state, errors = validate_review_state("fixture", payload, Path("fixture"))

        self.assertIn(
            "fixture: latest_range_head_commit must match reviewed_through_commit",
            errors,
        )


if __name__ == "__main__":
    unittest.main()
