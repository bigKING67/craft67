from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from test_support import ROOT, route


class RoutingTests(unittest.TestCase):
    def test_all_curated_routes(self) -> None:
        bank = json.loads((ROOT / "tests" / "fixtures" / "route_seeds.json").read_text(encoding="utf-8"))
        self.assertEqual(43, len(bank["routes"]))
        self.assertGreaterEqual(sum(len(items) for items in bank["routes"].values()), 258)
        for expected, hints in bank["routes"].items():
            for hint in hints:
                with self.subTest(route=expected, hint=hint):
                    self.assertEqual(expected, route(hint)["primary"]["id"])

    def test_fallback(self) -> None:
        result = route("understand this opaque artifact")
        self.assertEqual("R0", result["primary"]["id"])
        self.assertEqual(43, result["routing_source"]["routes"])

    def test_exclusion_rules(self) -> None:
        self.assertEqual("R14", route("LLM prompt jailbreak")["primary"]["id"])
        self.assertEqual("R2", route("iOS iPhone jailbreak")["primary"]["id"])
        self.assertEqual("R37", route("OAuth2 OIDC single sign-on")["primary"]["id"])
        self.assertEqual("R12", route("OAuth API authorization")["primary"]["id"])
        self.assertEqual("R17", route("CTF pwn ROP challenge")["primary"]["id"])

    def test_common_js_signing_language_routes_to_r3_without_fallback_ambiguity(self) -> None:
        hints = (
            "逆向网页请求签名参数并定位 JavaScript 加密函数",
            "browser JavaScript reverse engineering request signing crypto hook environment emulation",
            "JS逆向 签名参数 加密参数 补环境 Hook注入 request signing token生成",
        )
        for hint in hints:
            with self.subTest(hint=hint):
                result = route(hint)
                self.assertEqual("R3", result["primary"]["id"])
                self.assertFalse(result["ambiguous"])
                self.assertNotIn("R0", [item["id"] for item in result["secondary"]])

    def test_r0_specialist_rule_can_still_form_a_real_tie(self) -> None:
        result = route("GDB inspect sample.elf")
        self.assertEqual("R6", result["primary"]["id"])
        self.assertTrue(result["ambiguous"])
        self.assertEqual(["R6", "R0"], result["tied"])

    def test_cti_intent_wins_malware_tie_and_preserves_secondary(self) -> None:
        result = route(
            "Use public sources to enrich malware IOCs and correlate an actor campaign"
        )
        self.assertEqual("R44", result["primary"]["id"])
        self.assertTrue(result["ambiguous"])
        self.assertEqual(["R44", "R9"], result["tied"])
        self.assertEqual("R9", result["secondary"][0]["id"])

    def test_generic_social_media_research_does_not_route_to_cti(self) -> None:
        self.assertEqual("R0", route("analyze Twitter engagement for brand marketing")["primary"]["id"])
        self.assertEqual("R0", route("社交媒体品牌营销增长分析")["primary"]["id"])

    def test_malware_artifact_analysis_remains_r9(self) -> None:
        self.assertEqual("R9", route("extract configuration from this malware sample")["primary"]["id"])

    def test_artifact_magic_is_read_only_hint(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            artifact = Path(raw) / "opaque.bin"
            artifact.write_bytes(b"\x7fELF" + b"\x00" * 60)
            result = route("inspect artifact", str(artifact))
            self.assertEqual("R6", result["primary"]["id"])
            self.assertEqual("ELF binary", result["artifact"]["magic"])
            self.assertEqual(64, result["artifact"]["size"])

    def test_missing_artifact_fails(self) -> None:
        from reverse_craft.common import ReverseCraftError

        with self.assertRaises(ReverseCraftError):
            route("inspect", "/definitely/missing/reverse-craft-artifact")


if __name__ == "__main__":
    unittest.main()
