from __future__ import annotations

import json
import re
import unittest

from tests.support import ROOT

SKILL_ROOT = ROOT / "skills/review-craft"
SKILL_PATH = SKILL_ROOT / "SKILL.md"


def _skill_text() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def _frontmatter(text: str) -> dict[str, str]:
    block = text.split("---\n", 2)[1]
    values: dict[str, str] = {}
    for line in block.splitlines():
        key, value = line.split(":", 1)
        values[key] = value.strip().strip('"')
    return values


class SkillContractTests(unittest.TestCase):
    def test_frontmatter_uses_the_cross_host_minimum_metadata(self) -> None:
        metadata = _frontmatter(_skill_text())

        self.assertEqual(list(metadata), ["name", "description"])
        self.assertEqual(metadata["name"], SKILL_ROOT.name)
        self.assertLessEqual(len(metadata["description"]), 1024)

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for host in ("Codex CLI", "Claude Code", "Pi", "Grok"):
            self.assertIn(f"## Install for {host}", readme)

    def test_core_skill_has_no_forked_or_host_private_execution_dependency(self) -> None:
        text = _skill_text()

        for forbidden in (
            "context: fork",
            "spawn_agent",
            "agent team",
            "Codex Review",
            "Codex Security",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, text)
        self.assertIn("does not require subagents", text)

        integrations = (SKILL_ROOT / "references/integrations.md").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("Codex Review", integrations)
        self.assertNotIn("Codex Security", integrations)
        self.assertIn("Host-native review", integrations)
        self.assertIn("Host-native security workflow", integrations)

    def test_codex_implicit_routing_is_enabled(self) -> None:
        policy = (SKILL_ROOT / "agents/openai.yaml").read_text(encoding="utf-8")

        self.assertIn("allow_implicit_invocation: true", policy)

    def test_all_relative_markdown_links_resolve_inside_the_skill(self) -> None:
        skill_root = SKILL_ROOT.resolve()
        for document in (SKILL_PATH, *sorted((SKILL_ROOT / "references").glob("*.md"))):
            text = document.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
                if "://" in target or target.startswith("#"):
                    continue
                resolved = (document.parent / target.split("#", 1)[0]).resolve()
                with self.subTest(document=document.name, target=target):
                    self.assertTrue(resolved.is_relative_to(skill_root))
                    self.assertTrue(resolved.is_file())

    def test_package_and_plugin_point_to_the_same_skill(self) -> None:
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        plugin = json.loads(
            (ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8")
        )

        self.assertEqual(package["pi"]["skills"], ["skills/review-craft"])
        self.assertEqual(plugin["skills"], "./skills/")
        self.assertTrue((ROOT / package["pi"]["skills"][0] / "SKILL.md").is_file())

    def test_skill_defines_a_bounded_evidence_backed_default(self) -> None:
        text = _skill_text()
        bounded = text.split("## Bounded review fast path", 1)[1].split(
            "## Canonical workflow", 1
        )[0]

        self.assertIn("default path", bounded)
        self.assertIn("evidence-backed", bounded)
        self.assertIn("`KEEP`, `CLEAN_UP`, `DEFER`, `MEASURE`, or `DOCUMENT`", bounded)
        self.assertIn("A no-finding result without evidence supporting", bounded)
        self.assertIn("Do not emit a numeric score", bounded)
        self.assertIn("Do not run `doctor`, `preflight`", bounded)
        self.assertIn("Exit the fast path", bounded)
        self.assertIn("Do not\nautomatically enter the canonical workflow", bounded)
        self.assertIn("request separate\nauthorization", bounded)
        self.assertIn("`DELETE` and `REWRITE`", bounded)
        self.assertIn("several candidates arise", bounded)
        self.assertIn("needs narrow inspection", bounded)
        self.assertIn("materially expand its scope", bounded)
        self.assertIn("full compatibility,\nmigration, rollback, and verification gates", bounded)
        self.assertNotIn("multiple candidates require reconciliation", bounded)

        modes = (SKILL_ROOT / "references/modes-and-profiles.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("evidence-backed set of findings or decisions", modes.replace("\n", " "))
        self.assertIn("Multiple candidates and narrow validation", modes)

    def test_canonical_workflow_remains_explicit_and_deterministic(self) -> None:
        text = _skill_text()
        canonical = text.split("## Canonical workflow", 1)[1].split(
            "## Remediation workflow", 1
        )[0]
        workflow = (SKILL_ROOT / "references/workflow.md").read_text(encoding="utf-8")

        self.assertIn("explicitly requests", canonical)
        self.assertIn(
            "A bounded-path exit condition is not authorization", canonical
        )
        self.assertIn("[workflow.md](references/workflow.md)", canonical)
        for command in (
            "review_craft.py doctor --json",
            "review_craft.py preflight --target <repository>",
            "run-evidence --run-dir <run-dir>",
            "review_craft.py validate --run-dir <run-dir>",
            "review_craft.py finalize --run-dir <run-dir>",
        ):
            self.assertIn(command, workflow)

    def test_simplification_guidance_refines_existing_contracts_only(self) -> None:
        skill = _skill_text()
        reference = (SKILL_ROOT / "references/simplification.md").read_text(
            encoding="utf-8"
        )
        workflow = (SKILL_ROOT / "references/workflow.md").read_text(encoding="utf-8")
        findings = (SKILL_ROOT / "references/finding-lifecycle.md").read_text(
            encoding="utf-8"
        )
        remediation = (SKILL_ROOT / "references/remediation.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("[simplification.md](references/simplification.md)", skill)
        self.assertIn("read `simplification.md`", workflow)
        self.assertIn("Read `simplification.md`", findings)
        self.assertIn("read `simplification.md`", remediation)
        self.assertIn("existing candidate, evidence registry, finding, and decision", reference)
        self.assertIn("does not define a new Review Craft\nmode, score, ledger, report", reference)
        self.assertIn("## Evaluate replacement dependencies", reference)
        self.assertIn("complete obligation delta", reference)
        self.assertIn("clear net ownership reduction", reference)
        self.assertIn("preserve that residual contract", reference)
        self.assertIn("## Compare the structural regression delta", reference)
        self.assertIn("baseline and head obligations", reference)
        self.assertIn("no universal file-line\nthreshold establishes a finding", reference)
        self.assertIn("## Validate canonical ownership and placement", reference)
        self.assertIn("ownership obligation that consolidation would retire", reference)
        self.assertIn("half-applied state", reference)
        self.assertIn("make recovery non-idempotent", reference)
        self.assertIn("complete trace or\nmeasurement", reference)
        self.assertIn("runtime records this evidence but never edits", reference)
        self.assertNotIn("spawn_agent", reference)

    def test_cursor_quality_review_upstream_is_selectively_absorbed_and_attributed(self) -> None:
        contract = json.loads((ROOT / "contracts/upstreams.json").read_text(encoding="utf-8"))
        cursor = next(
            source
            for source in contract["sources"]
            if source["repository"].endswith("cursor/plugins")
        )
        notice = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")

        self.assertEqual(contract["schema"], "review-craft.upstreams.v2")
        self.assertEqual(cursor["status"], "selective_absorbed")
        self.assertEqual(
            set(cursor["reviewedBlobs"]),
            set(cursor["sourcePaths"]),
        )
        self.assertIn("diff-oriented structural regression delta", cursor["absorbedSurfaces"])
        self.assertIn("hard universal file-line blocker", cursor["excludedSurfaces"])
        self.assertIn("Cursor Task subagent orchestration", cursor["excludedSurfaces"])
        self.assertIn("Copyright 2026 Cursor", notice)
        self.assertIn(cursor["reviewedRevision"], notice)

    def test_alibaba_open_code_review_is_selectively_absorbed_and_tracked(self) -> None:
        contract = json.loads((ROOT / "contracts/upstreams.json").read_text(encoding="utf-8"))
        alibaba = next(
            source
            for source in contract["sources"]
            if source["repository"].endswith("alibaba/open-code-review")
        )
        notice = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")

        self.assertEqual(alibaba["status"], "selective_absorbed")
        self.assertTrue(alibaba["absorbedSurfaces"])
        self.assertTrue(alibaba["watchSurfaces"])
        self.assertEqual(set(alibaba["reviewedBlobs"]), set(alibaba["sourcePaths"]))
        self.assertIn(
            "deterministic source-location anchoring with source-side and span-digest closure",
            alibaba["absorbedSurfaces"],
        )
        self.assertIn(
            "sealed coverage denominator bound one-to-one to canonical inventory",
            alibaba["absorbedSurfaces"],
        )
        self.assertIn("coverage-derived run terminal states", alibaba["watchSurfaces"])
        self.assertIn("content-bound review resume and lineage", alibaba["watchSurfaces"])
        self.assertFalse(set(alibaba["absorbedSurfaces"]) & set(alibaba["watchSurfaces"]))
        self.assertIn("default test-file exclusion", alibaba["excludedSurfaces"])
        self.assertIn("independently implemented Python contract", " ".join(notice.split()))
        self.assertIn("No source or text", notice)
        self.assertIn(alibaba["reviewedRevision"], notice)

    def test_fix_authorization_and_source_mutation_boundary_remain_explicit(self) -> None:
        text = _skill_text()
        remediation = text.split("## Remediation workflow", 1)[1].split(
            "## Post-delivery attestation", 1
        )[0]

        self.assertIn("user explicitly asks to implement", remediation)
        self.assertIn("runtime must never mutate target source", remediation)
        self.assertIn("Do not infer implementation authorization", remediation)
        for status in ("`VERIFIED`", "`PARTIAL`", "`FAILED`", "`NO_CHANGES`"):
            self.assertIn(status, remediation)


if __name__ == "__main__":
    unittest.main()
