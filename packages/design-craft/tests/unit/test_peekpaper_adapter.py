from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from tools.design_craft.repo import REPO_ROOT


LIB_DIR = REPO_ROOT / "skills/design-craft/lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from design_craft import peekpaper, reference_contract  # noqa: E402


def issue_payload() -> dict:
    return {
        "date": "2026-08-10",
        "count": 2,
        "posts": [
            {
                "slug": "first-site",
                "position": 1,
                "domain": "first.example",
                "url": "https://first.example/",
                "title": "First Site",
                "description": "A first synthetic source.",
                "images": {"desktop": True, "mobile": True, "w": 2880, "h": 1800},
                "capturedAt": "2026-08-10T00:00:00Z",
                "captureId": "must-not-survive",
                "score": 99,
                "reasons": ["must-not-survive"],
                "slot": "must-not-survive",
            },
            {
                "slug": "second-site",
                "position": 0,
                "domain": "second.example",
                "url": "https://second.example/",
                "title": "Second Site",
                "description": "A second synthetic source.",
                "images": {"desktop": True, "mobile": False, "w": 1440, "h": 900},
                "capturedAt": "2026-08-10T00:01:00Z",
            },
        ],
    }


def source(payload: dict | None = None) -> peekpaper.IssueSource:
    raw = json.dumps(payload or issue_payload(), sort_keys=True).encode("utf-8")
    return peekpaper.IssueSource(issue_date="2026-08-10", raw=raw)


class PeekpaperAdapterTests(unittest.TestCase):
    def test_normalizer_is_stable_and_drops_source_internal_fields(self) -> None:
        catalog = peekpaper.build_catalog([source()], observed_at="2026-08-17")
        self.assertEqual(
            [item["id"] for item in catalog["cards"]],
            [
                "peekpaper-2026-08-10-second-site",
                "peekpaper-2026-08-10-first-site",
            ],
        )
        rendered = reference_contract.json_text(catalog)
        for forbidden in ("captureId", "score", "reasons", "slot", "must-not-survive"):
            self.assertNotIn(forbidden, rendered)
        self.assertNotIn("images", rendered)
        self.assertEqual(catalog["cards"][0]["evidence"]["mobile"]["status"], "unavailable")
        errors, _ = reference_contract.validate_catalog(catalog)
        self.assertEqual(errors, [])

    def test_issue_count_and_date_mismatch_fail_closed(self) -> None:
        invalid_count = issue_payload()
        invalid_count["count"] = 3
        with self.assertRaisesRegex(peekpaper.PeekpaperError, "count"):
            peekpaper.normalize_issue(source(invalid_count), observed_at="2026-08-17")

        invalid_date = issue_payload()
        invalid_date["date"] = "2026-08-11"
        with self.assertRaisesRegex(peekpaper.PeekpaperError, "date mismatch"):
            peekpaper.normalize_issue(source(invalid_date), observed_at="2026-08-17")

    def test_issue_and_post_urls_are_fixed_to_official_routes(self) -> None:
        self.assertEqual(
            peekpaper.issue_url("2026-08-10"),
            "https://peekpaper.com/content/editions/2026/08/10.json",
        )
        self.assertEqual(
            peekpaper.post_url("2026-08-10", "first-site"),
            "https://peekpaper.com/2026/08/10/first-site",
        )
        with self.assertRaises(peekpaper.PeekpaperError):
            peekpaper.issue_url("../../secrets")


if __name__ == "__main__":
    unittest.main()
