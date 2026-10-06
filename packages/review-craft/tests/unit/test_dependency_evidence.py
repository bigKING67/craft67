from __future__ import annotations

import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.support import RUNTIME_LIB, create_run

sys.path.insert(0, str(RUNTIME_LIB))

from review_craft.cli import main
from review_craft.repository import SourceReader, inventory, source_payload
from review_craft.repository_analysis import build_dependency_map


class DependencyEvidenceTests(unittest.TestCase):
    def _map(self, root: Path) -> dict:
        records, _ = inventory(root)
        return build_dependency_map(root, records)

    def test_dependency_map_rejects_changed_or_missing_inventory_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            app = root / "app.py"
            app.write_text("VALUE = 1\n")
            rows, _ = inventory(root)
            app.write_text("import service\n")
            with self.assertRaisesRegex(ValueError, "no longer matches"):
                build_dependency_map(root, rows)
            app.unlink()
            with self.assertRaisesRegex(ValueError, "no longer matches"):
                build_dependency_map(root, rows)
            app.mkdir()
            with self.assertRaisesRegex(ValueError, "not a regular"):
                build_dependency_map(root, rows)

    def test_source_reader_rejects_file_and_ancestor_symlinks_before_read(self) -> None:
        for ancestor in (False, True):
            with self.subTest(ancestor=ancestor), tempfile.TemporaryDirectory() as directory:
                root = Path(directory) / "repo"
                package = root / "pkg"
                package.mkdir(parents=True)
                app = package / "app.py"
                app.write_text("VALUE = 1\n")
                rows, _ = inventory(root)
                original = package if ancestor else app
                outside = Path(directory) / "outside"
                original.rename(outside)
                try:
                    original.symlink_to(outside, target_is_directory=ancestor)
                except OSError as error:
                    self.skipTest(f"symlink creation unavailable: {error}")
                with (
                    patch("builtins.open", side_effect=AssertionError("must not read")),
                    self.assertRaisesRegex(ValueError, "symlink"),
                ):
                    build_dependency_map(root, rows)

    def test_source_reader_rejects_invalid_relative_paths_before_read(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            invalid = ["../outside.py", str(root / "absolute.py"), ".", ""]
            if os.name == "nt":
                invalid.extend(
                    [
                        "\\outside.py",
                        "C:outside.py",
                        "C:\\outside.py",
                        ".. /outside.py",
                        "pkg/.. /outside.py",
                        "pkg/C:outside.py",
                    ]
                )
            for relative in invalid:
                with (
                    self.subTest(relative=relative),
                    patch(
                        "builtins.open",
                        side_effect=AssertionError("must not read"),
                    ),
                    self.assertRaisesRegex(ValueError, "path is invalid"),
                ):
                    source_payload(root, {"path": relative, "kind": "file"}, diff_base=None)

    def test_reused_reader_rechecks_content_and_directory_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            package = root / "pkg"
            package.mkdir(parents=True)
            app = package / "app.py"
            app.write_bytes(b"VALUE = 1\n")
            rows, _ = inventory(root)
            reader = SourceReader(root)
            self.assertEqual(reader.read(rows[0], diff_base=None), b"VALUE = 1\n")
            app.write_bytes(b"VALUE = 2\n")
            with self.assertRaisesRegex(ValueError, "no longer matches"):
                reader.read(rows[0], diff_base=None)
            outside = Path(directory) / "outside"
            package.rename(outside)
            try:
                package.symlink_to(outside, target_is_directory=True)
            except OSError as error:
                self.skipTest(f"symlink creation unavailable: {error}")
            with self.assertRaisesRegex(ValueError, "symlink"):
                reader.read(rows[0], diff_base=None)

    def test_analysis_failures_remain_explicit_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            app = root / "app.py"
            for payload, reason in (
                (b"def broken(:\n", "Python syntax error"),
                (b"#" + b"a" * 8192 + b"\xff", "UnicodeDecodeError"),
            ):
                with self.subTest(reason=reason):
                    app.write_bytes(payload)
                    result = self._map(root)
                    self.assertEqual(result["edges"], [])
                    self.assertEqual(result["filesAnalyzed"], 0)
                    self.assertEqual(result["filesSkipped"], [{"path": "app.py", "reason": reason}])
            app.write_text("VALUE = 1\n")
            rows, _ = inventory(root)
            with patch(
                "review_craft.repository_analysis.SourceReader.read", side_effect=PermissionError
            ):
                result = build_dependency_map(root, rows)
            self.assertEqual(
                result["filesSkipped"], [{"path": "app.py", "reason": "PermissionError"}]
            )

    @unittest.skipUnless(os.name == "nt", "Windows directory junction boundary")
    def test_source_reader_rejects_directory_junction_before_read(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            package = root / "pkg"
            package.mkdir(parents=True)
            (package / "app.py").write_bytes(b"VALUE = 1\n")
            rows, _ = inventory(root)
            reader = SourceReader(root)
            outside = Path(directory) / "outside"
            package.rename(outside)
            subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(package), str(outside)],
                check=True,
                capture_output=True,
            )
            try:
                with (
                    patch("builtins.open", side_effect=AssertionError("must not read")),
                    self.assertRaisesRegex(ValueError, "reparse point"),
                ):
                    reader.read(rows[0], diff_base=None)
            finally:
                package.rmdir()

    def test_snapshot_drift_blocks_preflight_and_is_a_validation_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            root.mkdir()
            app = root / "app.py"
            app.write_text("VALUE = 1\n")
            output = Path(directory) / "output"
            output.mkdir()

            def mutate_then_analyze(target, records):
                app.write_text("VALUE = 2\n")
                return build_dependency_map(target, records)

            with (
                patch(
                    "review_craft.cli_review.build_dependency_map", side_effect=mutate_then_analyze
                ),
                contextlib.redirect_stderr(io.StringIO()) as stderr,
            ):
                code = main(["preflight", "--target", str(root), "--output-root", str(output)])
            self.assertEqual(code, 2)
            self.assertIn("no longer matches", stderr.getvalue())
            self.assertEqual(list(output.iterdir()), [])
            app.write_text("VALUE = 1\n")
            run = create_run(root, output)
            with (
                patch(
                    "review_craft.contracts.build_dependency_map", side_effect=mutate_then_analyze
                ),
                contextlib.redirect_stderr(io.StringIO()) as stderr,
            ):
                code = main(["validate", "--run-dir", str(run), "--allow-draft"])
            self.assertEqual(code, 2)
            self.assertIn("source verification failed", stderr.getvalue())
            self.assertNotIn("Traceback", stderr.getvalue())

    def test_unrelated_declarations_preserve_import_facts_after_line_rebinding(self) -> None:
        variants = (
            "import service\n",
            "class Other:\n    def service(self):\n        return 0\nimport service\n",
            "def unrelated():\n    service = 0\n    return service\nimport service\n",
            "\n\nimport service\nclass Renamed:\n    pass\n",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "service.py").write_text("VALUE = 42\n", encoding="utf-8")
            for source in variants:
                with self.subTest(source=source):
                    (root / "app.py").write_text(source, encoding="utf-8")
                    result = self._map(root)
                    self.assertEqual(result["filesSkipped"], [])
                    self.assertEqual(
                        result["edges"],
                        [
                            {
                                "from": "app.py",
                                "to": "service.py",
                                "kind": "python-import",
                                "line": source.splitlines().index("import service") + 1,
                            }
                        ],
                    )

    def test_parse_gap_does_not_erase_independent_consumer_or_masquerade_as_success(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "service.py").write_text("VALUE = 42\n", encoding="utf-8")
            (root / "app.py").write_text("import service\n", encoding="utf-8")
            broken = root / "other.py"
            for source, skipped in (("def broken(:\n", True), ("VALUE = 0\n", False)):
                with self.subTest(skipped=skipped):
                    broken.write_text(source, encoding="utf-8")
                    result = self._map(root)
                    self.assertEqual(len(result["edges"]), 1)
                    self.assertEqual(result["edges"][0]["from"], "app.py")
                    self.assertEqual(result["filesAnalyzed"], 2 if skipped else 3)
                    self.assertEqual(
                        result["filesSkipped"],
                        [{"path": "other.py", "reason": "Python syntax error"}] if skipped else [],
                    )

    def test_empty_static_edges_do_not_prove_absence_of_runtime_consumer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "service.py").write_text("VALUE = 42\n", encoding="utf-8")
            app = root / "app.py"
            app.write_text('print(__import__("service").VALUE)\n', encoding="utf-8")
            result = self._map(root)
            self.assertEqual(result["edges"], [])
            self.assertEqual(result["filesSkipped"], [])
            # Execute only this authored fixture, never arbitrary review-target source.
            execution = subprocess.run(
                [sys.executable, "-B", str(app)],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
            self.assertEqual(execution.returncode, 0, execution.stderr)
            self.assertEqual(execution.stdout.strip(), "42")
            app.write_text("print(0)\n", encoding="utf-8")
            self.assertEqual(self._map(root)["edges"], result["edges"])
            execution = subprocess.run(
                [sys.executable, "-B", str(app)],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
            self.assertEqual(execution.returncode, 0, execution.stderr)
            self.assertEqual(execution.stdout.strip(), "0")
