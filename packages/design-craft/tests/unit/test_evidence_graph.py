from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.design_craft.evaluation.evidence_graph import (
    binding_domain,
    domain_dirty,
    domain_fingerprint,
    git_domain_fingerprint,
    git_projected_skill_tree_sha256,
    graph_errors,
    project_skill_domain,
    projected_skill_tree_sha256,
    repository_graph_errors,
)
from tools.design_craft.repo import REPO_ROOT
from scripts.design_craft_evidence_common import tree_sha256
from scripts.design_craft_evidence_common import git_head


def copy_source_fixture(destination: Path) -> Path:
    graph = destination / "contracts/evaluation/evidence-graph.json"
    graph.parent.mkdir(parents=True)
    shutil.copy2(REPO_ROOT / "contracts/evaluation/evidence-graph.json", graph)
    shutil.copytree(
        REPO_ROOT / "skills/design-craft",
        destination / "skills/design-craft",
    )
    return destination


class EvidenceGraphTests(unittest.TestCase):
    def test_repository_graph_is_complete(self) -> None:
        self.assertEqual(repository_graph_errors(), [])

    def test_version_metadata_does_not_change_behavior_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = copy_source_fixture(Path(raw))
            domain = binding_domain(
                "cross_agent", "same-prompt-motion-review", root=root
            )
            before = domain_fingerprint(root, domain)
            version_path = root / "skills/design-craft/VERSION"
            version_path.write_bytes(b"999.999.999\n")
            self.assertEqual(domain_fingerprint(root, domain), before)

    def test_motion_reference_only_changes_motion_domain(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = copy_source_fixture(Path(raw))
            motion = binding_domain(
                "comparative", "emil-motion-ablation", root=root
            )
            visual = binding_domain(
                "comparative", "taste-visual-critique-ablation", root=root
            )
            motion_before = domain_fingerprint(root, motion)
            visual_before = domain_fingerprint(root, visual)
            path = root / "skills/design-craft/references/motion-quality.md"
            original = path.read_bytes()
            path.write_bytes(original + b"\n<!-- domain fixture -->\n")
            self.assertNotEqual(domain_fingerprint(root, motion), motion_before)
            self.assertEqual(domain_fingerprint(root, visual), visual_before)

    def test_visual_reference_does_not_change_motion_domain(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = copy_source_fixture(Path(raw))
            motion = binding_domain(
                "comparative", "emil-motion-ablation", root=root
            )
            visual = binding_domain(
                "comparative", "taste-visual-critique-ablation", root=root
            )
            motion_before = domain_fingerprint(root, motion)
            visual_before = domain_fingerprint(root, visual)
            path = root / "skills/design-craft/references/visual-judgment.md"
            original = path.read_bytes()
            path.write_bytes(original + b"\n<!-- domain fixture -->\n")
            self.assertEqual(domain_fingerprint(root, motion), motion_before)
            self.assertNotEqual(domain_fingerprint(root, visual), visual_before)

    def test_projection_contains_only_domain_files(self) -> None:
        domain = binding_domain("cross_agent", "same-prompt-motion-review")
        with tempfile.TemporaryDirectory() as raw:
            destination = Path(raw) / "design-craft"
            project_skill_domain(
                REPO_ROOT,
                REPO_ROOT / "skills/design-craft",
                domain,
                destination,
            )
            self.assertTrue((destination / "SKILL.md").is_file())
            self.assertTrue((destination / "references/motion-quality.md").is_file())
            self.assertFalse((destination / "VERSION").exists())
            self.assertFalse((destination / "references/visual-judgment.md").exists())
            self.assertEqual(
                projected_skill_tree_sha256(
                    REPO_ROOT, REPO_ROOT / "skills/design-craft", domain
                ),
                tree_sha256(destination),
            )

    def test_git_fingerprint_matches_clean_checkout(self) -> None:
        domain = binding_domain("cross_agent", "same-prompt-motion-review")
        if domain_dirty(REPO_ROOT, domain):
            self.skipTest("current behavior domain is intentionally dirty")
        commit = git_head(REPO_ROOT)
        self.assertEqual(
            git_domain_fingerprint(REPO_ROOT, domain, commit),
            domain_fingerprint(REPO_ROOT, domain),
        )
        self.assertEqual(
            git_projected_skill_tree_sha256(
                REPO_ROOT,
                REPO_ROOT / "skills/design-craft",
                domain,
                commit,
            ),
            projected_skill_tree_sha256(
                REPO_ROOT, REPO_ROOT / "skills/design-craft", domain
            ),
        )

    def test_graph_rejects_cycles(self) -> None:
        payload = {
            "schema": "design-craft.evidence-graph.v2",
            "domains": {
                "one": {"extends": ["two"], "include": []},
                "two": {"extends": ["one"], "include": []},
            },
            "bindings": {
                "cross_agent": {"task": "one"},
                "comparative": {"case": "one"},
                "operational": {"release": "two"},
            },
        }
        self.assertTrue(any("cycle" in error for error in graph_errors(payload)))


if __name__ == "__main__":
    unittest.main()
