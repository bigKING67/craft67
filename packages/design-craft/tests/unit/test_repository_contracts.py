from __future__ import annotations

import unittest

from tools.design_craft.validation.repository_contracts import (
    _validate_source_map_contract,
)


PINNED = "1" * 40
SELECTED = "2" * 40
REVIEWED = "3" * 40


def upstream_lock() -> dict[str, object]:
    return {
        "upstreams": {
            "fixture": {
                "commit": PINNED,
                "behavior_absorbed_through_commit": SELECTED,
                "reviewed_through_commit": REVIEWED,
            }
        }
    }


def stable_source_map() -> str:
    return "\n".join(
        (
            "Mutable remote review state is repository governance metadata.",
            "Authority: `upstreams.lock.json` and the matching absorption matrices.",
            f"Pinned compatibility commit: `{PINNED}`",
            f"Selected-behavior boundary: `{SELECTED}`",
        )
    )


class RepositorySourceMapContractTests(unittest.TestCase):
    def test_stable_source_map_keeps_pins_without_reviewed_head(self) -> None:
        self.assertEqual(
            _validate_source_map_contract(stable_source_map(), upstream_lock()),
            [],
        )

    def test_mutable_review_state_is_rejected(self) -> None:
        source_map = "\n".join(
            (
                stable_source_map(),
                "Current reviewed remote commit:",
                REVIEWED,
                "Latest-range status: provenance_only",
            )
        )

        errors = _validate_source_map_contract(source_map, upstream_lock())

        self.assertTrue(
            any("Current reviewed remote commit:" in error for error in errors)
        )
        self.assertTrue(any("Latest-range status:" in error for error in errors))
        self.assertIn(
            f"fixture: source map must not mirror reviewed head {REVIEWED}", errors
        )


if __name__ == "__main__":
    unittest.main()
