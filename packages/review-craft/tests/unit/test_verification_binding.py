from __future__ import annotations

# tests.support initializes the runtime import path.
# ruff: noqa: I001
import copy
import json
import tempfile
import unittest
from pathlib import Path

from tests import support  # noqa: F401
from review_craft.assurance import _verifier_state, verification_input


class VerificationBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = {
            "manifest": {
                "runId": "test",
                "status": "draft",
                "target": {"sourceFingerprint": "a" * 64},
            },
            "findings": {"findings": []},
            "evidenceRegistry": {"artifacts": []},
        }

    def receipt(self, **changes):
        payload = {
            "schema": "review-craft.assurance-verification.v2",
            "reviewRunId": "test",
            "sourceFingerprint": "a" * 64,
            "findingsSha256": verification_input(self.data)["findingsSha256"],
            "createdAt": "2026-09-22T00:00:00Z",
            "verifier": {"kind": "HUMAN", "identifier": "independent", "independent": True},
            "assessments": [],
            "unverifiedClaims": [],
        }
        payload.update(changes)
        return payload

    def register(self, payload):
        name = str(len(self.data["evidenceRegistry"]["artifacts"]))
        (self.root / name).write_text(json.dumps(payload))
        self.data["evidenceRegistry"]["artifacts"].append(
            {"id": name, "path": name, "kind": "verification"}
        )

    def state(self):
        return _verifier_state(self.data, self.root, True)

    def test_empty_document_and_stale_replacement(self):
        self.register(self.receipt())
        self.assertEqual(self.state()[0]["status"], "VERIFIED")
        original = (self.root / "0").read_bytes()
        self.data["findings"]["context"] = "changed"
        self.assertTrue(self.state()[1])
        self.register(self.receipt())
        self.assertEqual(self.state()[0]["evidenceRef"], "artifact:1")
        self.assertEqual((self.root / "0").read_bytes(), original)
        self.register(self.receipt())
        self.assertTrue(self.state()[1])

    def test_missing_malformed_and_wrong_digest(self):
        for digest in (None, "invalid", "0" * 64):
            with self.subTest(digest=digest):
                self.data["evidenceRegistry"]["artifacts"] = []
                payload = self.receipt(findingsSha256=digest)
                if digest is None:
                    del payload["findingsSha256"]
                self.register(payload)
                self.assertTrue(self.state()[1])

    def test_legacy_only_accepts_sealed_historical_read(self):
        payload = self.receipt(schema="review-craft.assurance-verification.v1")
        del payload["findingsSha256"]
        self.register(payload)
        self.assertTrue(self.state()[1])
        self.data["manifest"].update(status="final", sealedAt="2026-09-22T00:00:00Z")
        self.assertFalse(self.state()[1])
        self.data["manifest"]["status"] = "draft"
        self.assertTrue(self.state()[1])

    def test_digest_binds_arrays_and_document_but_not_serialization(self):
        self.data["findings"] = {"findings": [{"id": "a"}, {"id": "b"}], "schema": "example"}
        original = verification_input(self.data)["findingsSha256"]
        self.data["findings"] = json.loads(
            json.dumps(self.data["findings"], sort_keys=True, indent=4)
        )
        self.assertEqual(verification_input(self.data)["findingsSha256"], original)
        document = copy.deepcopy(self.data["findings"])
        for rows in ([{"id": "b"}, {"id": "a"}], [{"id": "a"}], []):
            self.data["findings"] = {**document, "findings": rows}
            self.assertNotEqual(verification_input(self.data)["findingsSha256"], original)
