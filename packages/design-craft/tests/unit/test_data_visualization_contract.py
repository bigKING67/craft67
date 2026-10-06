from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def read_compact(relative_path: str) -> str:
    return " ".join(read(relative_path).split())


class DataVisualizationContractTests(unittest.TestCase):
    def test_chart_and_report_intent_remain_separate(self) -> None:
        surface = read_compact("skills/design-craft/references/surface-playbooks.md")
        report = read_compact("skills/design-craft/references/report-quality.md")

        for fragment in (
            "a chart request stays a chart request",
            "analysis alone does not imply a complete report",
            "operational dashboard product surface",
            "smallest deliverable that answers the stated question",
        ):
            self.assertIn(fragment, f"{surface}\n{report}".lower())

    def test_selection_is_question_and_data_shape_driven(self) -> None:
        report = read_compact("skills/design-craft/references/report-quality.md")

        for fragment in (
            "analytical question and data shape",
            "comparison or rank",
            "change over time",
            "composition",
            "distribution",
            "relationship or flow",
            "two or three candidates",
            "encoding truth",
            "label density",
            "expected reading time",
            "Project `DESIGN.md`",
            "Do not force candidate theater",
        ):
            self.assertIn(fragment, report)

    def test_multi_chart_composition_uses_independent_conclusions(self) -> None:
        report = read_compact("skills/design-craft/references/report-quality.md")

        self.assertIn("Count charts by independent conclusions", report)
        self.assertIn("not columns, metrics, chart types", report)
        self.assertIn("one primary chart per conclusion", report)
        self.assertIn("restates the same ranking, trend, or composition", report)

    def test_encoding_integrity_covers_common_failure_modes(self) -> None:
        report = read_compact("skills/design-craft/references/report-quality.md")

        for fragment in (
            "Length-encoded bars use a zero baseline",
            "radius scales by the square root",
            "meaningful hierarchy and non-negative weights",
            "geographic area is not a value encoding",
            "greater-than-100-percent values",
            "Color must not be the only cue",
            "real queryable records",
        ):
            self.assertIn(fragment, report)

    def test_browser_validation_checks_data_binding_and_edge_states(self) -> None:
        validation = read_compact(
            "skills/design-craft/references/validation-contract.md"
        )

        for fragment in (
            "source records to marks and labels",
            "square-root radius scaling",
            "non-negative hierarchical weights",
            "negative, zero, missing, single-value, dense, extreme",
            "real queryable records",
            "Static schema, syntax, or catalog validation cannot prove",
        ):
            self.assertIn(fragment, validation)

    def test_restricted_reference_has_fixed_provenance_without_payload(self) -> None:
        source_map = read_compact("skills/design-craft/references/source-map.md")

        for fragment in (
            "https://github.com/larashero3-dotcom/lieflat-charts",
            "475c9b67ead1f3d63bda73a94b9bf339e9d5c0b6",
            "PolyForm Noncommercial License 1.0.0",
            "not an upstream submodule, code dependency",
            "No source, templates, catalogs, tokens, media, or runtime",
        ):
            self.assertIn(fragment, source_map)

    def test_governance_registers_contract_test(self) -> None:
        required = json.loads(
            read("contracts/validation/required-files.json")
        )["files"]

        self.assertIn("tests/unit/test_data_visualization_contract.py", required)


if __name__ == "__main__":
    unittest.main()
