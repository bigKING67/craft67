from __future__ import annotations

import json
import subprocess
import sys
import unittest
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts.check_upstreams import UpstreamContractError, evaluate, load_contract
from tests.support import ROOT


class UpstreamCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = load_contract(ROOT / "contracts/upstreams.json")

    def _single_source_contract(self) -> dict[str, object]:
        return {
            "schema": self.contract["schema"],
            "sources": [deepcopy(self.contract["sources"][0])],
        }

    def test_repository_contract_passes_offline_without_network(self) -> None:
        with patch(
            "scripts.check_upstreams._remote_state", side_effect=AssertionError("network forbidden")
        ) as remote:
            result, code = evaluate(deepcopy(self.contract), remote=False)
            self.assertEqual(code, 0)
            self.assertTrue(all(row["status"] == "NOT_CHECKED" for row in result["sources"]))
            remote.assert_not_called()
        completed = subprocess.run(
            [sys.executable, "scripts/check_upstreams.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["mode"], "offline")
        self.assertTrue(payload["sources"])
        self.assertTrue(all(source["status"] == "NOT_CHECKED" for source in payload["sources"]))

    def test_contract_rejects_non_full_revision(self) -> None:
        payload = deepcopy(self.contract)
        payload["sources"][0]["reviewedRevision"] = "add872f"
        with TemporaryDirectory(prefix="review-craft-upstream-") as directory:
            contract_path = Path(directory) / "upstreams.json"
            contract_path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(UpstreamContractError):
                load_contract(contract_path)

    def test_contract_rejects_unsafe_repository_and_unknown_fields(self) -> None:
        for repository, extra in (
            ("file:///tmp/upstream", {}),
            ("https://github.com:invalid/tt-a1i/simplify-codebase", {}),
            (
                "https://github.com/tt-a1i/simplify-codebase",
                {"unreviewedField": True},
            ),
        ):
            payload = deepcopy(self.contract)
            payload["sources"][0]["repository"] = repository
            payload["sources"][0].update(extra)
            with TemporaryDirectory(prefix="review-craft-upstream-") as directory:
                contract_path = Path(directory) / "upstreams.json"
                contract_path.write_text(json.dumps(payload), encoding="utf-8")
                with (
                    self.subTest(repository=repository, extra=extra),
                    self.assertRaises(UpstreamContractError),
                ):
                    load_contract(contract_path)

    def test_contract_requires_one_reviewed_blob_per_source_path(self) -> None:
        for mutation in ("missing", "unexpected", "invalid"):
            payload = deepcopy(self.contract)
            blobs = payload["sources"][0]["reviewedBlobs"]
            if mutation == "missing":
                blobs.pop(next(iter(blobs)))
            elif mutation == "unexpected":
                blobs["unexpected.md"] = "a" * 40
            else:
                blobs[next(iter(blobs))] = "not-a-full-git-blob"
            with TemporaryDirectory(prefix="review-craft-upstream-") as directory:
                contract_path = Path(directory) / "upstreams.json"
                contract_path.write_text(json.dumps(payload), encoding="utf-8")
                with self.subTest(mutation=mutation), self.assertRaises(UpstreamContractError):
                    load_contract(contract_path)

    def test_tracked_status_requires_watch_surfaces_without_absorption_claim(self) -> None:
        payload = self._single_source_contract()
        tracked = payload["sources"][0]
        tracked["status"] = "tracked"
        tracked["watchSurfaces"] = ["candidate contract"]
        tracked.pop("absorbedSurfaces")
        with TemporaryDirectory(prefix="review-craft-upstream-") as directory:
            contract_path = Path(directory) / "upstreams.json"
            contract_path.write_text(json.dumps(payload), encoding="utf-8")
            loaded = load_contract(contract_path)
            tracked = loaded["sources"][0]

        self.assertTrue(tracked["watchSurfaces"])
        self.assertTrue(tracked["excludedSurfaces"])
        self.assertNotIn("absorbedSurfaces", tracked)

        for mutation in ("missing_watch", "false_absorption", "overlap"):
            mutated_payload = self._single_source_contract()
            source = mutated_payload["sources"][0]
            source["status"] = "tracked"
            source["watchSurfaces"] = ["candidate contract"]
            source.pop("absorbedSurfaces")
            if mutation == "missing_watch":
                source.pop("watchSurfaces")
            elif mutation == "false_absorption":
                source["absorbedSurfaces"] = ["unimplemented contract"]
            else:
                source["excludedSurfaces"] = ["candidate contract"]
            with TemporaryDirectory(prefix="review-craft-upstream-") as directory:
                contract_path = Path(directory) / "upstreams.json"
                contract_path.write_text(json.dumps(mutated_payload), encoding="utf-8")
                with self.subTest(mutation=mutation), self.assertRaises(UpstreamContractError):
                    load_contract(contract_path)

    def test_fully_absorbed_status_rejects_watch_metadata(self) -> None:
        payload = self._single_source_contract()
        source = payload["sources"][0]
        source["status"] = "absorbed"
        source["watchSurfaces"] = ["candidate contract"]
        with TemporaryDirectory(prefix="review-craft-upstream-") as directory:
            contract_path = Path(directory) / "upstreams.json"
            contract_path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(UpstreamContractError):
                load_contract(contract_path)

    def test_selective_absorption_can_keep_distinct_watch_surfaces(self) -> None:
        payload = self._single_source_contract()
        source = payload["sources"][0]
        source["status"] = "selective_absorbed"
        source["watchSurfaces"] = ["candidate contract"]

        with TemporaryDirectory(prefix="review-craft-upstream-") as directory:
            contract_path = Path(directory) / "upstreams.json"
            contract_path.write_text(json.dumps(payload), encoding="utf-8")
            loaded = load_contract(contract_path)
            self.assertEqual(loaded["sources"][0]["watchSurfaces"], ["candidate contract"])

            source["watchSurfaces"] = [source["absorbedSurfaces"][0]]
            contract_path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(UpstreamContractError):
                load_contract(contract_path)

    def test_remote_comparison_distinguishes_repository_and_content_drift(self) -> None:
        contract = self._single_source_contract()
        source = contract["sources"][0]
        current_revision = source["reviewedRevision"]
        current_blobs = source["reviewedBlobs"]
        changed_blobs = deepcopy(current_blobs)
        changed_blobs[next(iter(changed_blobs))] = "f" * 40
        for remote_revision, remote_blobs, repository_status, content_status, code in (
            (current_revision, current_blobs, "CURRENT", "CURRENT", 0),
            ("f" * 40, current_blobs, "UPDATED", "CURRENT", 0),
            ("f" * 40, changed_blobs, "UPDATED", "UPDATED", 1),
        ):
            with (
                self.subTest(repository_status=repository_status, content_status=content_status),
                patch(
                    "scripts.check_upstreams._remote_state",
                    return_value=(remote_revision, remote_blobs),
                ),
            ):
                payload, actual_code = evaluate(deepcopy(contract), remote=True)
                result = payload["sources"][0]
                self.assertEqual(result["repositoryStatus"], repository_status)
                self.assertEqual(result["contentStatus"], content_status)
                self.assertEqual(result["status"], content_status)
                self.assertEqual(actual_code, code)

    def test_missing_remote_source_path_is_relevant_drift(self) -> None:
        contract = self._single_source_contract()
        source = contract["sources"][0]
        remote_blobs = deepcopy(source["reviewedBlobs"])
        missing_path = next(iter(remote_blobs))
        remote_blobs.pop(missing_path)
        with patch(
            "scripts.check_upstreams._remote_state",
            return_value=("f" * 40, remote_blobs),
        ):
            payload, code = evaluate(contract, remote=True)

        result = payload["sources"][0]
        path_result = next(item for item in result["sourcePaths"] if item["path"] == missing_path)
        self.assertEqual(code, 1)
        self.assertEqual(result["status"], "UPDATED")
        self.assertEqual(path_result["status"], "MISSING")
        self.assertIsNone(path_result["remoteBlob"])

    def test_remote_failure_is_explicit_and_fails_closed(self) -> None:
        contract = self._single_source_contract()
        with patch(
            "scripts.check_upstreams._remote_state",
            side_effect=RuntimeError("git fetch exited 2"),
        ):
            payload, code = evaluate(contract, remote=True)

        self.assertEqual(code, 2)
        self.assertEqual(payload["sources"][0]["status"], "UNREACHABLE")
        self.assertEqual(payload["sources"][0]["error"], "git fetch exited 2")


if __name__ == "__main__":
    unittest.main()
