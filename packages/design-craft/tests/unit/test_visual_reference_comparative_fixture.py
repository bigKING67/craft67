from __future__ import annotations

import json
import unittest

from tools.design_craft.repo import REPO_ROOT


CASE_DIR = (
    REPO_ROOT
    / "evals/visual-reference/comparative-validation/"
    "reference-assisted-evidence-dossier"
)
SITE_DIR = CASE_DIR / "site"
RESULT_REF = (
    "evals/visual-reference/comparative-validation/"
    "reference-assisted-evidence-dossier/result.md#controlled-comparison"
)


class VisualReferenceComparativeFixtureTests(unittest.TestCase):
    def test_one_runtime_holds_content_semantics_and_states_constant(self) -> None:
        html = (SITE_DIR / "index.html").read_text(encoding="utf-8")
        javascript = (SITE_DIR / "app.js").read_text(encoding="utf-8")
        css = (SITE_DIR / "styles.css").read_text(encoding="utf-8")

        self.assertEqual(
            html.count("One dossier. Every claim, control, and open exception."),
            1,
        )
        for text in (
            "Open sample dossier",
            "Review the method",
            "Request a pilot",
            "14 / 14",
            "37 / 40",
            "3 open",
            "18 min",
            "Coverage map",
            "Change impact",
            "Exception ownership",
        ):
            self.assertIn(text, html)

        self.assertIn('new Set(["baseline", "reference-assisted"])', javascript)
        self.assertIn(
            'new Set(["default", "loading", "empty", "error", "success", "long"])',
            javascript,
        )
        self.assertIn('document.documentElement.dataset.variant = variant', javascript)
        self.assertIn("applyState(\"loading\")", javascript)
        self.assertIn("applyState(\"default\")", javascript)
        self.assertIn('html[data-variant="baseline"]', css)
        self.assertIn('html[data-variant="reference-assisted"]', css)
        self.assertIn('html[data-state="error"]', css)

    def test_accessibility_and_performance_instrumentation_is_explicit(self) -> None:
        html = (SITE_DIR / "index.html").read_text(encoding="utf-8")
        javascript = (SITE_DIR / "app.js").read_text(encoding="utf-8")
        css = (SITE_DIR / "styles.css").read_text(encoding="utf-8")

        self.assertEqual(html.count("<h1"), 1)
        self.assertIn('tabindex="-1"', html)
        self.assertIn('aria-live="polite"', html)
        self.assertIn('aria-busy="false"', html)
        self.assertIn("dialog.showModal()", javascript)
        self.assertIn("dossierTrigger?.focus", javascript)
        self.assertIn("window.__CAIRN_A11Y_AUDIT__", javascript)
        self.assertIn("largest-contentful-paint", javascript)
        self.assertIn("layout-shift", javascript)
        self.assertIn("longtask", javascript)
        self.assertIn("@media (prefers-reduced-motion: reduce)", css)

    def test_fixture_does_not_transfer_source_identity_assets_or_network_calls(self) -> None:
        site_source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(SITE_DIR.iterdir())
            if path.is_file()
        ).lower()

        for forbidden in (
            "lightspark",
            "nuehealth",
            "peekpaper",
            "qr code",
            "https://",
            "http://",
            "gradient(",
        ):
            self.assertNotIn(forbidden, site_source)

    def test_ready_pack_uses_distinct_structure_and_responsive_sources(self) -> None:
        pack = json.loads((CASE_DIR / "reference-pack.json").read_text(encoding="utf-8"))

        self.assertEqual(pack["status"], "ready")
        self.assertEqual(
            [(item["card_id"], item["role"]) for item in pack["references"]],
            [
                ("peekpaper-2026-08-11-lightspark", "structure"),
                ("peekpaper-2026-08-11-nue", "responsive"),
            ],
        )
        self.assertEqual(pack["blocking_reasons"], [])

    def test_browser_evidence_is_complete_and_bounded(self) -> None:
        screenshots = json.loads(
            (CASE_DIR / "screenshots.json").read_text(encoding="utf-8")
        )
        checks = json.loads(
            (CASE_DIR / "browser-checks.json").read_text(encoding="utf-8")
        )

        self.assertEqual(screenshots["schema"], "design-craft.l4-screenshots.v1")
        self.assertEqual(screenshots["case_id"], "reference-assisted-evidence-dossier")
        for phase in ("before", "after"):
            self.assertEqual(set(screenshots["artifacts"][phase]), {"desktop", "mobile"})
            for key, expected in (("desktop", [1440, 900]), ("mobile", [390, 844])):
                artifact = screenshots["artifacts"][phase][key]
                self.assertEqual(artifact["dimensions"], expected)
                self.assertFalse(artifact["layout_metrics"]["horizontal_overflow"])
                self.assertEqual(len(artifact["artifact_sha256"]), 64)

        bundle = screenshots["evidence_bundle"]
        self.assertEqual(bundle["shared_artifact_keys"], ["desktop", "mobile"])
        self.assertEqual(bundle["transport_health"]["status"], "healthy")
        self.assertEqual(
            bundle["finalize_summary"]["cleanup_summary"]["closed_count"], 3
        )
        self.assertEqual(
            bundle["finalize_summary"]["cleanup_summary"][
                "remaining_unkept_count"
            ],
            0,
        )
        self.assertEqual(bundle["run"]["run"]["status"], "completed")

        self.assertEqual(
            checks["schema"], "design-craft.visual-reference-browser-checks.v1"
        )
        self.assertEqual(checks["status"], "passed")
        self.assertTrue(checks["interactions"]["dialog"]["focus_restored"])
        self.assertEqual(checks["accessibility"]["screen_reader"], "not_run")
        self.assertEqual(checks["visual_review"]["p0"], [])
        self.assertEqual(checks["visual_review"]["p1"], [])

    def test_catalog_promotion_respects_evidence_prerequisites(self) -> None:
        catalog = json.loads(
            (
                REPO_ROOT / "evals/visual-reference/peekpaper-pilot/catalog.json"
            ).read_text(encoding="utf-8")
        )
        hypotheses = {item["id"]: item for item in catalog["hypotheses"]}

        typography = hypotheses["typographic-single-focus-entry"]
        proof = hypotheses["proof-led-trust-sequencing"]
        responsive = hypotheses["desktop-mobile-priority-reordering"]

        self.assertEqual(typography["status"], "proposed")
        self.assertEqual(typography["comparative_eval_refs"], [])
        self.assertEqual(proof["status"], "project_validated")
        self.assertEqual(proof["target_validation_refs"], [RESULT_REF])
        self.assertEqual(proof["comparative_eval_refs"], [])
        self.assertEqual(responsive["status"], "comparative_validated")
        self.assertEqual(responsive["comparative_eval_refs"], [RESULT_REF])

        result = (CASE_DIR / "result.md").read_text(encoding="utf-8")
        validation = (CASE_DIR / "validation.md").read_text(encoding="utf-8")
        self.assertIn("## Controlled comparison", result)
        self.assertIn("## Promotion boundary", result)
        self.assertIn("## Browser evidence", validation)


if __name__ == "__main__":
    unittest.main()
