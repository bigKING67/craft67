from __future__ import annotations

import json
import os
import stat
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from test_support import ROOT  # noqa: F401

import reverse_craft.case_store as case_store_module
import reverse_craft.case_validation as case_validation_module
from reverse_craft.case_store import (
    add_evidence,
    add_finding,
    add_path,
    case_dir,
    case_status,
    init_case,
    render_report,
    seal_case,
    validate_case,
)
from reverse_craft.common import FileLock, ReverseCraftError, pid_is_alive


class CaseStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.home = self.root / "home"
        self.artifact = self.root / "sample.bin"
        self.artifact.write_bytes(b"reverse-craft-fixture\x00\x01")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def new_case(self) -> str:
        return init_case("Fixture case", "offline fixture", "R0", str(self.home))["case"]["id"]

    def add_graph(self, case_id: str) -> tuple[str, str, str]:
        evidence = add_evidence(case_id, str(self.artifact), "binary", home=str(self.home))["evidence"]
        finding = add_finding(
            case_id,
            "Controlled fixture branch",
            "high",
            "confirmed",
            [evidence["id"]],
            reproduction="Replay the local fixture",
            confidence="high",
            home=str(self.home),
        )["finding"]
        path = add_path(
            case_id,
            "Input to fixture branch",
            [finding["id"]],
            status="confirmed",
            validation="Clean replay succeeds",
            home=str(self.home),
        )["path"]
        return evidence["id"], finding["id"], path["id"]

    def test_case_store_reexports_existing_contract_constants(self) -> None:
        names = (
            "SNAPSHOTS", "SEVERITIES", "FINDING_STATUSES", "CONFIDENCES", "PATH_STATUSES", "ROUTE_IDS",
            "CASE_REQUIRED_FIELDS", "CASE_OPTIONAL_FIELDS", "CASE_ALLOWED_FIELDS", "COLLECTION_REQUIRED_FIELDS",
            "EVIDENCE_REQUIRED_FIELDS", "FINDING_REQUIRED_FIELDS", "PATH_REQUIRED_FIELDS", "EVENT_REQUIRED_FIELDS",
            "EVENT_TYPES", "EVENT_DATA_FIELDS", "SHA256_RE", "EVIDENCE_ID_RE", "FINDING_ID_RE", "PATH_ID_RE",
        )
        for name in names:
            with self.subTest(name=name):
                self.assertIs(getattr(case_store_module, name), getattr(case_validation_module, name))

    def test_non_contiguous_r44_route_is_supported_but_unregistered_ids_fail(self) -> None:
        case_id = init_case("CTI fixture", "offline public-source fixture", "R44", str(self.home))["case"]["id"]
        self.assertEqual("R44", case_status(case_id, str(self.home))["case"]["route_id"])
        self.assertTrue(validate_case(case_id, str(self.home))["valid"])
        for route_id in ("R42", "R43", "R45"):
            with self.subTest(route_id=route_id), self.assertRaisesRegex(ReverseCraftError, "registered route"):
                init_case("Invalid route", "offline fixture", route_id, str(self.home))

    def test_full_lifecycle_and_seal(self) -> None:
        case_id = self.new_case()
        evidence_id, finding_id, path_id = self.add_graph(case_id)
        report = render_report(case_id, home=str(self.home))
        self.assertTrue(Path(report["path"]).is_file())
        self.assertTrue(validate_case(case_id, str(self.home))["valid"])
        sealed = seal_case(case_id, str(self.home))
        self.assertTrue(sealed["valid"])
        status = case_status(case_id, str(self.home))
        self.assertEqual({"evidence": 1, "findings": 1, "paths": 1, "events": 6}, status["counts"])
        self.assertEqual("sealed", status["case"]["state"])
        self.assertEqual((evidence_id, finding_id, path_id), ("E-0001", "F-0001", "P-0001"))
        with self.assertRaises(ReverseCraftError):
            add_evidence(case_id, str(self.artifact), "binary", home=str(self.home))

    def test_seal_document_rejects_unexpected_fields_and_timestamp_drift(self) -> None:
        case_id = self.new_case()
        self.add_graph(case_id)
        seal_case(case_id, str(self.home))
        seal_path = case_dir(case_id, str(self.home)) / "seal.json"
        original = json.loads(seal_path.read_text(encoding="utf-8"))

        with self.subTest("unexpected field"):
            mutated = {**original, "unexpected": True}
            seal_path.write_text(json.dumps(mutated), encoding="utf-8")
            result = validate_case(case_id, str(self.home))
            self.assertFalse(result["valid"])
            self.assertIn("seal document has unexpected fields: unexpected", result["errors"])

        with self.subTest("timestamp drift"):
            mutated = {**original, "sealed_at": "2000-01-01T00:00:00Z"}
            seal_path.write_text(json.dumps(mutated), encoding="utf-8")
            result = validate_case(case_id, str(self.home))
            self.assertFalse(result["valid"])
            self.assertIn("seal timestamp does not match the case snapshot", result["errors"])

    def test_tampered_artifact_is_detected(self) -> None:
        case_id = self.new_case()
        self.add_graph(case_id)
        directory = case_dir(case_id, str(self.home))
        stored = next((directory / "artifacts").iterdir())
        stored.write_bytes(b"tampered")
        result = validate_case(case_id, str(self.home))
        self.assertFalse(result["valid"])
        self.assertTrue(any("evidence" in error and "mismatch" in error for error in result["errors"]))

    def test_tampered_event_chain_is_detected(self) -> None:
        case_id = self.new_case()
        directory = case_dir(case_id, str(self.home))
        events_path = directory / "events.ndjson"
        event = json.loads(events_path.read_text(encoding="utf-8"))
        event["data"]["id"] = "changed"
        events_path.write_text(json.dumps(event) + "\n", encoding="utf-8")
        result = validate_case(case_id, str(self.home))
        self.assertFalse(result["valid"])
        self.assertIn("event hash mismatch at 1", result["errors"])

    def test_truncated_event_tail_is_detected_before_further_mutation(self) -> None:
        case_id = self.new_case()
        self.add_graph(case_id)
        directory = case_dir(case_id, str(self.home))
        events_path = directory / "events.ndjson"
        events = events_path.read_text(encoding="utf-8").splitlines()
        events_path.write_text("\n".join(events[:-1]) + "\n", encoding="utf-8")

        result = validate_case(case_id, str(self.home))

        self.assertFalse(result["valid"])
        self.assertIn("case event_count does not match the event stream", result["errors"])
        self.assertIn("path.added events do not match the snapshot", result["errors"])
        with self.assertRaisesRegex(ReverseCraftError, "event anchor"):
            add_evidence(case_id, str(self.artifact), "binary", home=str(self.home))
        snapshot = json.loads((directory / "evidence.json").read_text(encoding="utf-8"))
        self.assertEqual(1, len(snapshot["items"]))

    def test_malformed_snapshots_fail_closed_without_traceback(self) -> None:
        case_id = self.new_case()
        self.add_graph(case_id)
        directory = case_dir(case_id, str(self.home))
        findings_path = directory / "findings.json"
        findings = json.loads(findings_path.read_text(encoding="utf-8"))
        findings["items"][0]["evidence_ids"] = None
        findings_path.write_text(json.dumps(findings), encoding="utf-8")

        result = validate_case(case_id, str(self.home))

        self.assertFalse(result["valid"])
        self.assertIn("invalid finding evidence_ids: F-0001", result["errors"])

    def test_non_object_event_fails_closed_without_traceback(self) -> None:
        case_id = self.new_case()
        directory = case_dir(case_id, str(self.home))
        (directory / "events.ndjson").write_text("[]\n", encoding="utf-8")

        result = validate_case(case_id, str(self.home))

        self.assertFalse(result["valid"])
        self.assertIn("event at line 1 is not an object", result["errors"])

    def test_empty_case_document_fails_closed(self) -> None:
        case_id = self.new_case()
        directory = case_dir(case_id, str(self.home))
        (directory / "case.json").write_text("{}\n", encoding="utf-8")

        result = validate_case(case_id, str(self.home))

        self.assertFalse(result["valid"])
        self.assertTrue(any(error.startswith("case missing fields:") for error in result["errors"]))

    def test_unhashable_malformed_values_fail_closed(self) -> None:
        case_id = self.new_case()
        self.add_graph(case_id)
        directory = case_dir(case_id, str(self.home))
        mutations = {
            "case.json": lambda value: value.update({"route_id": []}),
            "evidence.json": lambda value: value["items"][0].update({"acquisition": {}}),
            "findings.json": lambda value: value["items"][0].update({"severity": {}}),
            "paths.json": lambda value: value["items"][0].update({"status": {}}),
        }
        for name, mutate in mutations.items():
            path = directory / name
            value = json.loads(path.read_text(encoding="utf-8"))
            mutate(value)
            path.write_text(json.dumps(value), encoding="utf-8")
        events_path = directory / "events.ndjson"
        events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
        events[0]["type"] = []
        events_path.write_text("\n".join(json.dumps(event) for event in events) + "\n", encoding="utf-8")

        result = validate_case(case_id, str(self.home))

        self.assertFalse(result["valid"])
        self.assertIn("invalid case route id", result["errors"])
        self.assertIn("invalid evidence acquisition: E-0001", result["errors"])
        self.assertIn("invalid finding classification: F-0001", result["errors"])
        self.assertIn("invalid path status: P-0001", result["errors"])
        self.assertIn("invalid event type at 1", result["errors"])

    def test_legacy_case_without_event_anchor_is_valid_and_upgrades_on_write(self) -> None:
        case_id = self.new_case()
        directory = case_dir(case_id, str(self.home))
        case_path = directory / "case.json"
        case = json.loads(case_path.read_text(encoding="utf-8"))
        case.pop("event_count")
        case.pop("last_event_hash")
        case_path.write_text(json.dumps(case), encoding="utf-8")

        before = validate_case(case_id, str(self.home))
        self.assertTrue(before["valid"])
        self.assertIn("legacy case has no event tail anchor", before["warnings"])

        add_evidence(case_id, str(self.artifact), "binary", home=str(self.home))
        upgraded = json.loads(case_path.read_text(encoding="utf-8"))
        self.assertEqual(2, upgraded["event_count"])
        self.assertRegex(upgraded["last_event_hash"], r"^[0-9a-f]{64}$")
        self.assertTrue(validate_case(case_id, str(self.home))["valid"])

    def test_external_evidence_fixity(self) -> None:
        case_id = self.new_case()
        add_evidence(case_id, str(self.artifact), "binary", external=True, home=str(self.home))
        self.assertTrue(validate_case(case_id, str(self.home))["valid"])
        self.artifact.write_bytes(b"changed")
        self.assertFalse(validate_case(case_id, str(self.home))["valid"])

    def test_report_output_cannot_overwrite_reserved_case_files(self) -> None:
        case_id = self.new_case()
        directory = case_dir(case_id, str(self.home))

        with self.assertRaisesRegex(ReverseCraftError, "reports directory"):
            render_report(case_id, output=str(directory / "events.ndjson"), home=str(self.home))

        self.assertTrue(validate_case(case_id, str(self.home))["valid"])

    def test_report_renders_evidence_provenance_and_empty_note(self) -> None:
        case_id = self.new_case()
        evidence = add_evidence(
            case_id,
            str(self.artifact),
            "public-source-html",
            note="",
            source="https://example.test/advisory",
            home=str(self.home),
        )["evidence"]

        report = render_report(case_id, home=str(self.home))
        content = Path(report["path"]).read_text(encoding="utf-8")

        self.assertIn(f"- `{evidence['id']}` `public-source-html`:", content)
        self.assertIn("  - Source: `https://example.test/advisory`", content)
        self.assertIn("  - Acquisition: `verified-copy`", content)
        self.assertIn(f"  - Observed at: `{evidence['observed_at']}`", content)
        self.assertIn("  - Note: not recorded", content)

    def test_report_evidence_free_text_cannot_inject_markdown_structure(self) -> None:
        case_id = self.new_case()
        source = "https://example.test/`source``\n# forged heading"
        note = "`first line\n- forged item with `inline` code`"
        add_evidence(
            case_id,
            str(self.artifact),
            "public`source",
            note=note,
            source=source,
            home=str(self.home),
        )

        report = render_report(case_id, home=str(self.home))
        content = Path(report["path"]).read_text(encoding="utf-8")

        self.assertIn("``public`source``", content)
        self.assertIn("  - Source: ```https://example.test/`source`` # forged heading```", content)
        self.assertIn("  - Note: `` `first line - forged item with `inline` code` ``", content)
        self.assertNotIn("\n# forged heading", content)
        self.assertNotIn("\n- forged item", content)

    def test_finding_requires_known_evidence(self) -> None:
        case_id = self.new_case()
        with self.assertRaises(ReverseCraftError):
            add_finding(case_id, "bad", "high", "confirmed", ["E-9999"], confidence="high", home=str(self.home))
        with self.assertRaises(ReverseCraftError):
            add_finding(case_id, "bad", "high", "confirmed", [], home=str(self.home))

    def test_path_rejects_unknown_or_refuted_finding(self) -> None:
        case_id = self.new_case()
        with self.assertRaises(ReverseCraftError):
            add_path(case_id, "bad", ["F-9999"], home=str(self.home))
        finding = add_finding(case_id, "refuted", "info", "refuted", [], home=str(self.home))["finding"]
        with self.assertRaises(ReverseCraftError):
            add_path(case_id, "bad", [finding["id"]], status="supported", home=str(self.home))

    def test_case_id_path_traversal_is_rejected(self) -> None:
        with self.assertRaises(ReverseCraftError):
            case_dir("../outside", str(self.home))

    def test_invalid_route_is_rejected(self) -> None:
        with self.assertRaises(ReverseCraftError):
            init_case("bad route", "offline fixture", "R99", str(self.home))

    def test_concurrent_evidence_ids_are_unique(self) -> None:
        case_id = self.new_case()
        files: list[Path] = []
        for index in range(6):
            path = self.root / f"sample-{index}.bin"
            path.write_bytes(f"fixture-{index}".encode())
            files.append(path)
        errors: list[Exception] = []

        def add(path: Path) -> None:
            try:
                add_evidence(case_id, str(path), "binary", home=str(self.home))
            except Exception as exc:  # test thread collects failures
                errors.append(exc)

        threads = [threading.Thread(target=add, args=(path,)) for path in files]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual([], errors)
        snapshot = json.loads((case_dir(case_id, str(self.home)) / "evidence.json").read_text(encoding="utf-8"))
        self.assertEqual(6, len(snapshot["items"]))
        self.assertEqual(6, len({item["id"] for item in snapshot["items"]}))

    @unittest.skipIf(os.name == "nt", "POSIX permission modes are not portable to Windows")
    def test_case_directories_and_generated_files_are_private(self) -> None:
        case_id = self.new_case()
        add_evidence(case_id, str(self.artifact), "binary", home=str(self.home))
        report = render_report(case_id, home=str(self.home))
        directory = case_dir(case_id, str(self.home))

        for path in (directory.parent, directory, directory / "artifacts", directory / "reports"):
            self.assertEqual(0o700, stat.S_IMODE(path.stat().st_mode), path)
        generated_files = [
            directory / "case.json",
            directory / "evidence.json",
            directory / "findings.json",
            directory / "paths.json",
            directory / "events.ndjson",
            next((directory / "artifacts").iterdir()),
            Path(report["path"]),
        ]
        for path in generated_files:
            self.assertEqual(0o600, stat.S_IMODE(path.stat().st_mode), path)

    @mock.patch("reverse_craft.common.os.kill")
    def test_windows_pid_probe_never_uses_os_kill(self, kill: mock.Mock) -> None:
        with mock.patch("reverse_craft.common.os.name", "nt"):
            self.assertIsNone(pid_is_alive(1234))
        kill.assert_not_called()

    def test_permission_error_for_existing_lock_is_treated_as_contention(self) -> None:
        lock_path = self.root / "contended.lock"
        lock_path.write_text("{}\n", encoding="utf-8")
        with mock.patch("reverse_craft.common.os.open", side_effect=PermissionError("busy")):
            with self.assertRaisesRegex(ReverseCraftError, "timed out waiting for lock"):
                with FileLock(lock_path, timeout=0.01):
                    self.fail("an inaccessible existing lock must not be acquired")


if __name__ == "__main__":
    unittest.main()
