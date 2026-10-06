from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import install_skill  # noqa: E402
import upstream_status  # noqa: E402
import verify_evidence  # noqa: E402


class RepositoryContractTests(unittest.TestCase):
    ACTION_RELEASES = {
        "actions/checkout": ("3d3c42e5aac5ba805825da76410c181273ba90b1", "v7.0.1"),
        "actions/setup-python": ("5fda3b95a4ea91299a34e894583c3862153e4b97", "v7.0.0"),
        "actions/setup-node": ("820762786026740c76f36085b0efc47a31fe5020", "v7.0.0"),
        "actions/upload-artifact": ("043fb46d1a93c77aae656e7c1c64a875d1fc6a0a", "v7.0.1"),
    }

    def test_version_parity(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        paths = [
            ROOT / "package.json",
            ROOT / ".codex-plugin" / "plugin.json",
            ROOT / ".claude-plugin" / "plugin.json",
            ROOT / ".grok-plugin" / "plugin.json",
        ]
        self.assertEqual((ROOT / "skills" / "money-craft" / "VERSION").read_text(encoding="utf-8").strip(), version)
        for path in paths:
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["version"], version)

    def test_workflow_schemas_are_packaged(self) -> None:
        schema_root = ROOT / "skills" / "money-craft" / "schemas"
        expected = {
            "earnings-update-input.schema.json": "money-craft.earnings-update-input.v1",
            "earnings-update.schema.json": "money-craft.earnings-update.v1",
            "company-research-plan.schema.json": "money-craft.company-research-plan.v1",
            "financial-reconciliation.schema.json": "money-craft.financial-reconciliation.v1",
            "financial-reconciliation-audit.schema.json": "money-craft.financial-reconciliation-audit.v1",
            "official-import.schema.json": "money-craft.official-import.v1",
            "research-case.schema.json": "money-craft.research-case.v1",
            "research-collection.schema.json": "money-craft.research-collection.v1",
            "research-completion-receipt.schema.json": "money-craft.research-completion-receipt.v1",
            "research-finalize.schema.json": "money-craft.research-finalize.v1",
            "research-init.schema.json": "money-craft.research-init.v1",
            "research-run-state.schema.json": "money-craft.research-run-state.v1",
            "research-status.schema.json": "money-craft.research-status.v1",
            "report-render.schema.json": "money-craft.report-render.v1",
            "report-render-verify.schema.json": "money-craft.report-render-verify.v1",
            "thesis-update-plan.schema.json": "money-craft.thesis-update-plan.v1",
            "thesis-diff.schema.json": "money-craft.thesis-diff.v1",
            "tracking-current.schema.json": "money-craft.tracking-current.v1",
            "tracking-init.schema.json": "money-craft.tracking-init.v1",
            "tracking-revision.schema.json": "money-craft.tracking-revision.v1",
            "tracking-run-state.schema.json": "money-craft.tracking-run-state.v1",
            "tracking-state.schema.json": "money-craft.tracking-state.v1",
            "tracking-status.schema.json": "money-craft.tracking-status.v1",
            "tracking-state.v2.schema.json": "money-craft.tracking-state.v2",
            "tracking-current.v2.schema.json": "money-craft.tracking-current.v2",
            "tracking-revision.v2.schema.json": "money-craft.tracking-revision.v2",
            "tracking-status.v2.schema.json": "money-craft.tracking-status.v2",
            "tracking-verify.schema.json": "money-craft.tracking-verify.v1",
        }
        for filename, schema_name in expected.items():
            payload = json.loads((schema_root / filename).read_text(encoding="utf-8"))
            self.assertEqual(payload["properties"]["schema"]["const"], schema_name)

    def test_pinned_submodule_and_source_targets(self) -> None:
        lock = json.loads((ROOT / "sources.lock.json").read_text(encoding="utf-8"))
        upstream = lock["upstreams"][0]
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT / "upstreams" / "ai-berkshire",
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(completed.stdout.strip(), upstream["pinned_commit"])
        for mapping in upstream["mappings"]:
            self.assertTrue((ROOT / "upstreams" / "ai-berkshire" / mapping["source"]).is_file())
            for target in mapping["targets"]:
                self.assertTrue((ROOT / target).is_file())

    def test_selective_upstream_review_closes_coverage(self) -> None:
        lock = json.loads((ROOT / "sources.lock.json").read_text(encoding="utf-8"))
        review = lock["upstreams"][0]["reviews"][-1]
        self.assertEqual(review["disposition"], "pin-retained-selective-reimplementation")
        coverage = review["coverage"]
        self.assertEqual(coverage["pending_files"], 0)
        self.assertEqual(
            coverage["changed_files"],
            coverage["reviewed_files"] + coverage["accounted_excluded_files"],
        )
        self.assertEqual(
            sum(coverage["categories"].values()),
            coverage["changed_files"],
        )
        skill = (ROOT / "skills/money-craft/SKILL.md").read_text(encoding="utf-8")
        routing = (ROOT / "skills/money-craft/references/routing.md").read_text(encoding="utf-8")
        self.assertIn("references/high-growth-alpha.md", skill)
        self.assertIn("`research + thesis + alpha`", routing)
        self.assertIn("`industry/theme + alpha`", routing)
        self.assertIn("security_id", routing)

    def test_entrypoint_defers_mode_specific_operations_to_routed_references(self) -> None:
        skill = (ROOT / "skills/money-craft/SKILL.md").read_text(encoding="utf-8")
        research = (ROOT / "skills/money-craft/references/company-research.md").read_text(encoding="utf-8")
        provider = (ROOT / "skills/money-craft/references/providers/yfinance.md").read_text(encoding="utf-8")
        rendering = (ROOT / "skills/money-craft/references/report-rendering.md").read_text(encoding="utf-8")
        tracking = (ROOT / "skills/money-craft/references/tracking-workflow.md").read_text(encoding="utf-8")
        self.assertIn("不要读取完整公司研究运行合同", skill)
        self.assertNotIn('scripts/money_craft.py" research init', skill)
        self.assertIn('scripts/money_craft.py" research init', research)
        self.assertIn("迁移兼容回退", provider)
        self.assertIn("report render", rendering)
        self.assertIn("track init", tracking)

    def test_upstream_categories_preserve_unicode_paths(self) -> None:
        self.assertEqual(upstream_status.category("reports/快手/赔率表.md"), "excluded-content")
        self.assertEqual(upstream_status.category("实盘记录/卖出条件.md"), "excluded-content")
        self.assertEqual(upstream_status.category("skills/era-alpha.md"), "skills")
        self.assertEqual(upstream_status.category("codex-prompts/era-alpha.md"), "skills")

    def test_workflow_actions_are_pinned_to_reviewed_node24_releases(self) -> None:
        seen: set[str] = set()
        pattern = re.compile(r"uses:\s+([^@\s]+)@([0-9a-f]{40})\s+#\s+(v[0-9]+\.[0-9]+\.[0-9]+)")
        for path in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
            text = path.read_text(encoding="utf-8")
            all_uses = [line for line in text.splitlines() if "uses:" in line]
            matches = pattern.findall(text)
            self.assertEqual(len(matches), len(all_uses), f"unreviewed mutable action ref in {path.name}")
            for action, revision, version in matches:
                self.assertIn(action, self.ACTION_RELEASES)
                self.assertEqual((revision, version), self.ACTION_RELEASES[action])
                seen.add(action)
        self.assertEqual(seen, set(self.ACTION_RELEASES))

    def test_report_runtime_has_a_real_ci_smoke_gate(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("  report-render:\n", workflow)
        self.assertIn("python3 scripts/test_environment.py --runtime report", workflow)
        self.assertIn('"$MONEY_CRAFT_REPORT_PYTHON" -m unittest tests.test_report_renderer -v', workflow)
        self.assertIn('"$MONEY_CRAFT_REPORT_PYTHON" scripts/report_smoke.py', workflow)

    def test_runtime_paths_are_xdg_split_and_dotenv_is_explicit_only(self) -> None:
        runtime = (ROOT / "skills" / "money-craft" / "scripts" / "runtime_paths.py").read_text(
            encoding="utf-8"
        )
        example = (ROOT / ".env.example").read_text(encoding="utf-8")
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertIn('CONFIG_HOME_ENV = "MONEY_CRAFT_CONFIG_HOME"', runtime)
        self.assertIn('DATA_HOME_ENV = "MONEY_CRAFT_DATA_HOME"', runtime)
        self.assertIn('CACHE_HOME_ENV = "MONEY_CRAFT_CACHE_HOME"', runtime)
        self.assertIn('ENV_FILE_ENV = "MONEY_CRAFT_ENV_FILE"', runtime)
        self.assertNotIn("Path.cwd()", runtime)
        self.assertIn("MONEY_CRAFT_ENV_FILE", example)
        self.assertIn("FRED_API_KEY=", example)
        self.assertIn(".env.*", gitignore)
        self.assertIn("!.env.example", gitignore)
        self.assertIn(".env.example", package["files"])

    def test_yfinance_is_optional_pinned_and_documented_without_redefining_primary_evidence(self) -> None:
        requirements = (ROOT / "skills/money-craft/requirements-yfinance.txt").read_text(encoding="utf-8")
        self.assertEqual(requirements.strip(), "yfinance==1.7.0")
        lock = json.loads((ROOT / "sources.lock.json").read_text(encoding="utf-8"))
        release = next(item for item in lock["documents"] if item["id"] == "yfinance-pypi-1.7.0")
        self.assertEqual(release["version"], "1.7.0")
        self.assertEqual(
            release["wheel_sha256"],
            "91281ecd1f71069a37155ff8653aff2d3085f3492bd8721f18b70955da62911a",
        )
        skill = (ROOT / "skills/money-craft/SKILL.md").read_text(encoding="utf-8")
        provider = (ROOT / "skills/money-craft/references/providers/yfinance.md").read_text(encoding="utf-8")
        self.assertIn("references/providers/yfinance.md", skill)
        self.assertIn("正式披露", provider)
        self.assertIn("personal use", provider)

    def test_fred_is_documented_as_macro_vintage_data_with_rights_and_secret_boundaries(self) -> None:
        lock = json.loads((ROOT / "sources.lock.json").read_text(encoding="utf-8"))
        ids = {item["id"] for item in lock["documents"]}
        self.assertTrue(
            {
                "fred-api-key-reference",
                "fred-series-search-reference",
                "fred-series-reference",
                "fred-series-observations-reference",
                "fred-series-vintagedates-reference",
                "fred-realtime-period-reference",
                "fred-api-terms",
            }.issubset(ids)
        )
        skill = (ROOT / "skills/money-craft/SKILL.md").read_text(encoding="utf-8")
        provider = (ROOT / "skills/money-craft/references/providers/fred.md").read_text(encoding="utf-8")
        notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
        self.assertIn("references/providers/fred.md", skill)
        self.assertIn("as-known-on", provider)
        self.assertIn("FRED_API_KEY", provider)
        self.assertIn("not endorsed or certified", notices)
        self.assertNotRegex(provider, r"(?<![A-Za-z0-9])[a-z0-9]{32}(?![A-Za-z0-9])")

    def test_atomic_installer_and_force_backup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "skills"
            destination, backup = install_skill.install(root, force=False)
            self.assertIsNone(backup)
            self.assertTrue((destination / "INSTALL_PROVENANCE.json").is_file())
            with self.assertRaises(ValueError):
                install_skill.install(root, force=False)
            destination, backup = install_skill.install(root, force=True)
            self.assertTrue(destination.is_dir())
            self.assertIsNotNone(backup)
            self.assertTrue(backup.is_dir())
            self.assertEqual(backup.parent, root.parent / ".skills-backups")
            self.assertEqual([path.name for path in root.iterdir()], ["money-craft"])

    def test_public_evidence_manifests_are_metadata_only(self) -> None:
        paths = sorted((ROOT / "artifacts" / "acceptance").glob("*/evidence-manifest.json"))
        self.assertTrue(paths)
        for path in paths:
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(verify_evidence.validate_manifest(payload), [], path.parent.name)
            self.assertFalse(payload["distribution"]["provider_payloads_distributed"])
            self.assertFalse(payload["distribution"]["downloaded_documents_distributed"])


if __name__ == "__main__":
    unittest.main()
