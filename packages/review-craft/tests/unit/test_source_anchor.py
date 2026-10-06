from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from review_craft.constants import ARTIFACT_PATHS, PREVIOUS_SCHEMA_VERSION, SCHEMA_VERSION
from review_craft.contracts import ContractError, validate_run
from review_craft.jsonio import read_json, read_jsonl, sha256_bytes, write_json, write_jsonl
from review_craft.source_anchor import ANCHOR_ALGORITHM, build_run_location

from tests.support import (
    create_run,
    make_target,
    populate_valid_run,
    rewrite_fixture_run_schema,
    run_cli,
)


class SourceAnchorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.target_temporary, self.target = make_target()
        self.addCleanup(self.target_temporary.cleanup)
        self.output_temporary = tempfile.TemporaryDirectory(
            prefix="review-craft-anchor-output-"
        )
        self.addCleanup(self.output_temporary.cleanup)
        self.output_root = Path(self.output_temporary.name)
        self.run_dir = create_run(self.target, self.output_root)

    def _anchor_cli(
        self,
        *,
        run_dir: Path | None = None,
        path: str = "app.py",
        line_start: int = 1,
        line_end: int = 2,
        role: str = "primary",
    ) -> tuple[object, dict[str, object] | None]:
        completed = run_cli(
            "anchor-location",
            "--run-dir",
            str(run_dir or self.run_dir),
            "--path",
            path,
            "--line-start",
            str(line_start),
            "--line-end",
            str(line_end),
            "--role",
            role,
        )
        payload = json.loads(completed.stdout) if completed.returncode == 0 else None
        return completed, payload

    def test_preflight_creates_run_v5_and_cli_binds_current_source_span(self) -> None:
        manifest = read_json(self.run_dir / "review-manifest.json")
        self.assertEqual(manifest["schemaVersion"], SCHEMA_VERSION)

        completed, location = self._anchor_cli()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIsNotNone(location)
        assert location is not None
        source = (self.target / "app.py").read_bytes()
        self.assertEqual(location["path"], "app.py")
        self.assertEqual(location["lineStart"], 1)
        self.assertEqual(location["lineEnd"], 2)
        self.assertEqual(location["role"], "primary")
        self.assertEqual(
            location["anchor"],
            {
                "algorithm": ANCHOR_ALGORITHM,
                "sourceSide": "CURRENT",
                "sourceSha256": sha256_bytes(source),
                "sourceLineCount": 2,
                "spanSha256": sha256_bytes(source),
            },
        )

    def test_anchor_cli_rejects_out_of_range_or_uncovered_locations(self) -> None:
        out_of_range, _payload = self._anchor_cli(line_end=3)
        self.assertEqual(out_of_range.returncode, 2)
        self.assertIn("exceeds source line count 2", out_of_range.stderr)

        uncovered, _payload = self._anchor_cli(path="missing.py", line_end=1)
        self.assertEqual(uncovered.returncode, 2)
        self.assertIn("not in canonical coverage", uncovered.stderr)

    def test_anchor_uses_lf_delimiters_and_preserves_crlf_and_final_line_bytes(self) -> None:
        target_temporary, target = make_target()
        self.addCleanup(target_temporary.cleanup)
        source = b"one\r\ntwo\r\nthree"
        (target / "app.py").write_bytes(source)
        run_dir = create_run(target, self.output_root)

        location = build_run_location(
            run_dir,
            path="app.py",
            line_start=2,
            line_end=3,
            role="primary",
        )

        self.assertEqual(location["anchor"]["sourceLineCount"], 3)
        self.assertEqual(
            location["anchor"]["spanSha256"],
            sha256_bytes(b"two\r\nthree"),
        )

    def test_deleted_diff_location_is_bound_to_the_immutable_base_side(self) -> None:
        target_temporary, target = make_target(commit=True)
        self.addCleanup(target_temporary.cleanup)
        base = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=target,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        base_source = subprocess.run(
            ["git", "show", f"{base}:app.py"],
            cwd=target,
            check=True,
            capture_output=True,
        ).stdout
        worktree_source = base_source.replace(b"\n", b"\r\n")
        self.assertNotEqual(worktree_source, base_source)
        (target / "app.py").write_bytes(worktree_source)
        (target / "app.py").unlink()
        completed = run_cli(
            "preflight",
            "--target",
            str(target),
            "--output-root",
            str(self.output_root),
            "--mode",
            "diff",
            "--base",
            base,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        run_dir = Path(json.loads(completed.stdout)["runDir"])

        anchored, location = self._anchor_cli(run_dir=run_dir)
        self.assertEqual(anchored.returncode, 0, anchored.stderr)
        assert location is not None
        self.assertEqual(location["anchor"]["sourceSide"], "BASE")
        self.assertEqual(location["anchor"]["sourceSha256"], sha256_bytes(base_source))
        self.assertEqual(location["anchor"]["spanSha256"], sha256_bytes(base_source))

    def test_run_v5_rejects_missing_or_tampered_candidate_anchor(self) -> None:
        populate_valid_run(self.run_dir)
        ledger_path = self.run_dir / ARTIFACT_PATHS["candidateLedger"]
        candidates = read_jsonl(ledger_path)
        candidates[0]["locations"][0].pop("anchor")
        write_jsonl(ledger_path, candidates)
        with self.assertRaises(ContractError) as missing:
            validate_run(self.run_dir)
        self.assertIn("anchor: required for review-craft.run.v5", str(missing.exception))

        location = build_run_location(
            self.run_dir,
            path="app.py",
            line_start=1,
            line_end=2,
            role="primary",
        )
        location["anchor"]["spanSha256"] = "f" * 64
        candidates[0]["locations"] = [location]
        write_jsonl(ledger_path, candidates)
        findings_path = self.run_dir / ARTIFACT_PATHS["findings"]
        findings = read_json(findings_path)
        findings["findings"][0]["locations"] = [location]
        write_json(findings_path, findings)
        with self.assertRaises(ContractError) as tampered:
            validate_run(self.run_dir)
        self.assertIn(
            "anchor.spanSha256: does not match canonical source",
            str(tampered.exception),
        )

    def test_run_v5_finding_must_reuse_candidate_locations_exactly(self) -> None:
        populate_valid_run(self.run_dir)
        findings_path = self.run_dir / ARTIFACT_PATHS["findings"]
        findings = read_json(findings_path)
        findings["findings"][0]["locations"][0]["role"] = "secondary"
        write_json(findings_path, findings)
        with self.assertRaises(ContractError) as mismatch:
            validate_run(self.run_dir)
        self.assertIn(
            "locations: must exactly match the run.v5 candidate anchors",
            str(mismatch.exception),
        )

    def test_run_v4_remains_validation_only_and_rejects_v5_anchor_fields(self) -> None:
        populate_valid_run(self.run_dir)
        current_location = build_run_location(
            self.run_dir,
            path="app.py",
            line_start=1,
            line_end=2,
            role="primary",
        )
        rewrite_fixture_run_schema(self.run_dir, PREVIOUS_SCHEMA_VERSION)
        validate_run(self.run_dir)

        ledger_path = self.run_dir / ARTIFACT_PATHS["candidateLedger"]
        candidates = read_jsonl(ledger_path)
        candidates[0]["locations"] = [current_location]
        write_jsonl(ledger_path, candidates)
        with self.assertRaises(ContractError) as incompatible:
            validate_run(self.run_dir)
        self.assertIn(
            "anchor: unsupported by frozen review-craft.run.v4",
            str(incompatible.exception),
        )


if __name__ == "__main__":
    unittest.main()
