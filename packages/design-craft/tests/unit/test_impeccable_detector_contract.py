from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
import sys

from tests.bash_support import bash_command


REPO_ROOT = Path(__file__).resolve().parents[2]
DETECTOR = REPO_ROOT / "upstreams/impeccable/skill/scripts/detect.mjs"
DETECTOR_FACADE = (
    REPO_ROOT / "upstreams/impeccable/cli/engine/detect-antipatterns.mjs"
)
CSS_CASCADE = (
    REPO_ROOT
    / "upstreams/impeccable/cli/engine/engines/static-html/css-cascade.mjs"
)
PARSER = REPO_ROOT / "upstreams/impeccable/skill/scripts/lib/design-parser.mjs"
FIXTURES = REPO_ROOT / "evals/fixtures/impeccable-detector"
WRAPPER = REPO_ROOT / "skills/design-craft/scripts/design_craft_detect.sh"
LIB_DIR = REPO_ROOT / "skills/design-craft/lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from design_craft.detector_policy import linked_stylesheet_files, sanitize_payload


def scan(relative_path: str) -> list[dict]:
    result = subprocess.run(
        ["node", str(DETECTOR), "--json", str(FIXTURES / relative_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode not in {0, 2}:
        raise AssertionError(result.stderr)
    return json.loads(result.stdout)


def rules(findings: list[dict]) -> set[str]:
    return {
        str(finding.get("antipattern") or finding.get("id") or "")
        for finding in findings
        if isinstance(finding, dict)
    }


def node_json(script: str, *args: str) -> object:
    result = subprocess.run(
        ["node", "--input-type=module", "--eval", script, *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return json.loads(result.stdout)


def write_fake_detector(root: Path, *, exit_code: int, parser_modules: bool) -> Path:
    detector = root / "skill/scripts/detect.mjs"
    detector.parent.mkdir(parents=True)
    detector.write_text(
        "process.stdout.write(JSON.stringify(["
        "{antipattern: 'fixture-finding', severity: 'warning'}"
        "]) + '\\n');\n"
        f"process.exit({exit_code});\n",
        encoding="utf-8",
    )
    engine = root / "cli/engine/engines/static-html/detect-html.mjs"
    engine.parent.mkdir(parents=True)
    engine.write_text("export const fixture = true;\n", encoding="utf-8")
    if parser_modules:
        for name in ("htmlparser2", "css-select", "css-tree", "domutils"):
            package = root / "node_modules" / name
            package.mkdir(parents=True)
            (package / "package.json").write_text(
                json.dumps(
                    {
                        "name": name,
                        "type": "module",
                        "exports": "./index.js",
                    }
                ),
                encoding="utf-8",
            )
            (package / "index.js").write_text(
                "export const fixture = true;\n", encoding="utf-8"
            )
    return detector


def run_wrapper(detector: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["DESIGN_CRAFT_IMPECCABLE_DETECTOR"] = str(detector)
    return subprocess.run(
        bash_command(
            WRAPPER,
            "--target",
            str(FIXTURES / "rounded-none-pass.tsx"),
            *args,
        ),
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


class ImpeccableDetectorContractTests(unittest.TestCase):
    def test_detector_payload_url_credentials_are_redacted_in_all_json_modes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            detector = root / "skill/scripts/detect.mjs"
            detector.parent.mkdir(parents=True)
            detector.write_text(
                "process.stdout.write(JSON.stringify([{severity: 'warning', "
                "message: 'fetch https://alice:secret@example.test/a.css?x=1'}]));\n",
                encoding="utf-8",
            )

            raw = run_wrapper(detector, "--json-only")
            full = run_wrapper(detector, "--full-json")

        self.assertEqual(raw.returncode, 0, raw.stderr)
        self.assertEqual(full.returncode, 0, full.stderr)
        self.assertNotIn("alice", raw.stdout)
        self.assertNotIn("secret", raw.stdout)
        self.assertIn("https://[REDACTED]@example.test", raw.stdout)
        self.assertNotIn("alice", full.stdout)
        self.assertNotIn("secret", full.stdout)

    def test_detector_stderr_url_credentials_are_redacted_in_all_json_modes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            detector = root / "skill/scripts/detect.mjs"
            detector.parent.mkdir(parents=True)
            detector.write_text(
                "process.stderr.write('failed https://alice:secret@example.test/a.css\\n');\n"
                "process.stdout.write('[]\\n');\n",
                encoding="utf-8",
            )

            raw = run_wrapper(detector, "--json-only")
            full = run_wrapper(detector, "--full-json")

        for result in (raw, full):
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("alice", result.stderr)
            self.assertNotIn("secret", result.stderr)
            self.assertIn("https://[REDACTED]@example.test", result.stderr)

    def test_recursive_payload_sanitizer_preserves_non_url_emails(self) -> None:
        payload = sanitize_payload(
            {
                "message": "owner alice@example.test; source //bob:pw@example.test/file",
                "nested": ["https://token@example.test/path"],
            }
        )

        self.assertIn("alice@example.test", payload["message"])
        self.assertNotIn("bob:pw", payload["message"])
        self.assertEqual(payload["nested"], ["https://[REDACTED]@example.test/path"])

    def test_linked_stylesheets_resolve_queries_and_reject_boundary_escapes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            page = root / "pages/index.html"
            css = root / "assets/theme.css"
            outside = root.parent / "outside.css"
            page.parent.mkdir(parents=True)
            css.parent.mkdir(parents=True)
            css.write_text(".safe { color: green; }", encoding="utf-8")
            outside.write_text(".outside { color: red; }", encoding="utf-8")
            page.write_text(
                '<link rel="stylesheet" href="/assets/theme.css?v=7#stable">\n'
                '<link rel="stylesheet" href="../../outside.css">\n',
                encoding="utf-8",
            )

            files, issues = linked_stylesheet_files(page, root, asset_root=root)

            self.assertEqual(files, [css.resolve()])
            self.assertTrue(any("outside project root" in issue for issue in issues))

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unsupported")
    def test_linked_stylesheets_reject_symlink_components(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            real = root / "real"
            real.mkdir(parents=True)
            (real / "theme.css").write_text(".x {}", encoding="utf-8")
            (root / "linked").symlink_to(real, target_is_directory=True)
            page = root / "index.html"
            page.write_text(
                '<link rel="stylesheet" href="linked/theme.css">', encoding="utf-8"
            )

            files, issues = linked_stylesheet_files(page, root)

            self.assertEqual(files, [])
            self.assertTrue(any("through symlink" in issue for issue in issues))

    def test_root_relative_stylesheet_uses_package_local_asset_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            package = root / "apps/web"
            css = package / "assets/theme.css"
            page = package / "index.html"
            css.parent.mkdir(parents=True)
            css.write_text(".package-local { color: green; }", encoding="utf-8")
            page.write_text(
                '<link rel="stylesheet" href="/assets/theme.css">', encoding="utf-8"
            )

            files, issues = linked_stylesheet_files(
                page, root, asset_root=package
            )

            self.assertEqual(files, [css.resolve()])
            self.assertEqual(issues, [])

    def test_ambiguous_root_relative_stylesheet_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            page = root / "apps/web/index.html"
            page.parent.mkdir(parents=True)
            page.write_text(
                '<link rel="stylesheet" href="/assets/theme.css">', encoding="utf-8"
            )

            files, issues = linked_stylesheet_files(page, root, asset_root=None)

            self.assertEqual(files, [])
            self.assertTrue(any("ambiguous root-relative" in issue for issue in issues))

    def test_wrapper_discloses_regex_fallback_and_preserves_findings(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            detector = write_fake_detector(
                Path(temp), exit_code=2, parser_modules=False
            )

            full = run_wrapper(detector, "--full-json")
            self.assertEqual(full.returncode, 0, full.stderr)
            payload = json.loads(full.stdout)
            self.assertTrue(payload["degraded"])
            self.assertEqual(
                payload["upstream_detector"]["status"],
                "available_regex_fallback",
            )
            self.assertEqual(payload["upstream_detector"]["exit_code"], 2)
            self.assertIn(
                "optional static HTML/CSS parser dependencies unavailable",
                payload["upstream_detector"]["message"],
            )
            self.assertEqual(
                payload["upstream_findings"][0]["antipattern"],
                "fixture-finding",
            )

            human = run_wrapper(detector)
            self.assertEqual(human.returncode, 0, human.stderr)
            self.assertIn(
                "upstream_detector_status: available_regex_fallback", human.stdout
            )
            self.assertIn("upstream_detector_exit_code: 2", human.stdout)

            raw = run_wrapper(detector, "--json-only")
            self.assertEqual(raw.returncode, 0, raw.stderr)
            self.assertEqual(
                json.loads(raw.stdout),
                [{"antipattern": "fixture-finding", "severity": "warning"}],
            )

    def test_wrapper_reports_static_parser_availability(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            detector = write_fake_detector(
                Path(temp), exit_code=0, parser_modules=True
            )
            result = run_wrapper(detector, "--full-json")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["degraded"])
        self.assertEqual(payload["upstream_detector"]["status"], "available")
        self.assertEqual(payload["upstream_detector"]["exit_code"], 0)

    def test_wrapper_reports_unavailable_detector(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            result = run_wrapper(Path(temp) / "missing.mjs", "--full-json")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["degraded"])
        self.assertEqual(payload["upstream_detector"]["status"], "unavailable")
        self.assertIsNone(payload["upstream_detector"]["exit_code"])

    def test_style_carriers_ignore_prose_but_detect_applied_css(self) -> None:
        payload = node_json(
            f"""
import fs from 'node:fs';
import {{ checkHtmlPatterns }} from {json.dumps(DETECTOR_FACADE.as_uri())};
const ids = (file) => checkHtmlPatterns(fs.readFileSync(file, 'utf8')).map(x => x.id);
process.stdout.write(JSON.stringify({{
  passing: ids(process.argv[1]),
  failing: ids(process.argv[2]),
}}));
""",
            str(FIXTURES / "style-carriers-pass.html"),
            str(FIXTURES / "style-carriers-fail.html"),
        )
        self.assertIsInstance(payload, dict)
        passing = set(payload["passing"])
        failing = set(payload["failing"])

        self.assertNotIn("gradient-text", passing)
        self.assertNotIn("ai-color-palette", passing)
        self.assertIn("gradient-text", failing)

    def test_false_positive_regressions_stay_fixed(self) -> None:
        self.assertNotIn(
            "border-accent-on-rounded", rules(scan("rounded-none-pass.tsx"))
        )
        self.assertNotIn("broken-image", rules(scan("comment-image-pass.tsx")))
        self.assertNotIn("single-font", rules(scan("single-font-pass.css")))

    def test_versioned_stylesheets_and_blade_compound_suffixes_are_scanned(self) -> None:
        css = node_json(
            f"""
import {{ collectStaticCssText }} from {json.dumps(CSS_CASCADE.as_uri())};
const root = {{ children: [] }};
const modules = {{
  selectAll(selector) {{
    if (selector === 'style') return [];
    if (selector === 'link') return [{{ attribs: {{ rel: 'stylesheet', href: 'theme.css?v=7#stable' }} }}];
    return [];
  }},
  domutils: {{ textContent() {{ return ''; }} }},
}};
process.stdout.write(JSON.stringify(collectStaticCssText(root, process.argv[1], null, process.argv[2], modules)));
""",
            str(FIXTURES / "versioned-stylesheet"),
            str(FIXTURES / "versioned-stylesheet/index.html"),
        )
        self.assertIn("border-left: 4px", css)

        blade_payload = node_json(
            f"""
import fs from 'node:fs';
import {{ walkDir, detectText }} from {json.dumps(DETECTOR_FACADE.as_uri())};
const files = walkDir(process.argv[1]);
const findings = files.flatMap(file => detectText(fs.readFileSync(file, 'utf8'), file));
process.stdout.write(JSON.stringify({{
  files,
  rules: findings.map(x => x.antipattern),
}}));
""",
            str(FIXTURES / "blade"),
        )
        self.assertTrue(
            any(path.endswith("card.blade.php") for path in blade_payload["files"])
        )
        self.assertTrue(
            {"side-tab", "border-accent-on-rounded"}
            & set(blade_payload["rules"])
        )

    def test_yaml_quote_escapes_are_decoded(self) -> None:
        script = f"""
import fs from 'node:fs';
import {{ parseDesignMd }} from {json.dumps(PARSER.as_uri())};
const model = parseDesignMd(fs.readFileSync(process.argv[1], 'utf8'));
process.stdout.write(JSON.stringify({{
  fontFamily: model.frontmatter.typography.body.fontFamily,
  name: model.frontmatter.name,
}}));
"""
        result = subprocess.run(
            [
                "node",
                "--input-type=module",
                "--eval",
                script,
                str(FIXTURES / "yaml-escaped-design.md"),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(
            payload["fontFamily"], '"IBM Plex Sans", system-ui, sans-serif'
        )
        self.assertEqual(payload["name"], "It's quiet")


if __name__ == "__main__":
    unittest.main()
