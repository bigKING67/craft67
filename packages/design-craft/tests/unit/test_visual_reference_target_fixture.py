from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.design_craft.repo import REPO_ROOT


CASE_DIR = (
    REPO_ROOT
    / "evals/visual-reference/target-validation/reference-assisted-product-landing"
)
RESULT_REF = (
    "evals/visual-reference/target-validation/"
    "reference-assisted-product-landing/result.md#controlled-comparison"
)


class VisualReferenceTargetFixtureTests(unittest.TestCase):
    def test_fixture_holds_content_and_behavior_constant(self) -> None:
        html = (CASE_DIR / "site/index.html").read_text(encoding="utf-8")
        css = (CASE_DIR / "site/styles.css").read_text(encoding="utf-8")
        javascript = (CASE_DIR / "site/app.js").read_text(encoding="utf-8")

        self.assertEqual(
            html.count("Turn visual review into a release decision."),
            1,
        )
        for text in (
            "Start a review",
            "See sample report",
            "12</strong> routes reviewed",
            "3</strong> unresolved states",
            "2</strong> viewports verified",
            "Capture, compare, decide.",
            "Start with one release candidate.",
        ):
            self.assertIn(text, html)

        self.assertIn('new Set(["baseline", "reference-assisted"])', javascript)
        self.assertIn('document.documentElement.dataset.variant = variant', javascript)
        self.assertIn('dialog.querySelector("form").addEventListener', javascript)
        self.assertIn("focus({ preventScroll: true })", javascript)
        self.assertIn('html[data-variant="baseline"]', css)
        self.assertIn('html[data-variant="reference-assisted"]', css)
        self.assertNotIn("gradient(", css.lower())

    def test_fixture_does_not_transfer_source_identity_or_assets(self) -> None:
        site_source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((CASE_DIR / "site").iterdir())
            if path.is_file()
        ).lower()

        self.assertNotIn("design meetup", site_source)
        self.assertNotIn("locket", site_source)
        self.assertNotIn("peekpaper", site_source)
        self.assertNotIn("https://", site_source)

    def test_ready_pack_and_bounded_hypothesis_refs_are_checked_in(self) -> None:
        pack = json.loads((CASE_DIR / "reference-pack.json").read_text(encoding="utf-8"))
        self.assertEqual(pack["status"], "ready")
        self.assertEqual(
            [(item["card_id"], item["role"]) for item in pack["references"]],
            [
                ("peekpaper-2026-08-11-design-meetup", "structure"),
                ("peekpaper-2026-08-11-locket", "responsive"),
            ],
        )

        catalog_path = REPO_ROOT / "evals/visual-reference/peekpaper-pilot/catalog.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        hypotheses = {item["id"]: item for item in catalog["hypotheses"]}

        self.assertEqual(
            hypotheses["typographic-single-focus-entry"]["target_validation_refs"],
            [RESULT_REF],
        )
        self.assertEqual(
            hypotheses["desktop-mobile-priority-reordering"][
                "target_validation_refs"
            ],
            [RESULT_REF],
        )
        self.assertEqual(
            hypotheses["proof-led-trust-sequencing"]["target_validation_refs"],
            [
                "evals/visual-reference/comparative-validation/"
                "reference-assisted-evidence-dossier/"
                "result.md#controlled-comparison"
            ],
        )
        self.assertEqual(
            hypotheses["typographic-single-focus-entry"]["status"], "proposed"
        )
        self.assertEqual(
            hypotheses["proof-led-trust-sequencing"]["status"],
            "project_validated",
        )
        self.assertEqual(
            hypotheses["desktop-mobile-priority-reordering"]["status"],
            "comparative_validated",
        )

    def test_screenshot_manifest_is_portable_and_responsive(self) -> None:
        manifest = json.loads((CASE_DIR / "screenshots.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema"], "design-craft.l4-screenshots.v1")
        self.assertEqual(manifest["case_id"], "reference-assisted-product-landing")

        for phase in ("before", "after"):
            self.assertEqual(set(manifest["artifacts"][phase]), {"desktop", "mobile"})
            for key, expected in (("desktop", [1440, 900]), ("mobile", [390, 844])):
                artifact = manifest["artifacts"][phase][key]
                self.assertEqual(artifact["dimensions"], expected)
                self.assertFalse(artifact["layout_metrics"]["horizontal_overflow"])
                self.assertTrue(artifact["artifact_path"].startswith("browser67://"))
                self.assertEqual(len(artifact["artifact_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
