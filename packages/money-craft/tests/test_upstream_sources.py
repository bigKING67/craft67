from __future__ import annotations

import copy
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import upstream_sources as sources
import upstream_status as status


def capture() -> dict:
    return {"schema": sources.CAPTURE_SCHEMA, "source_id": "example-docs",
            "captured_at": sources.utc_now(), "catalog_complete": True,
            "catalog_urls": ["https://example.com/docs/", "https://example.com/docs/risk"],
            "pages": [{"url": "https://example.com/docs/", "status": 200, "title": "Index",
                       "text": "Documentation index", "structure_sha256": sources.structure_digest([])},
                      {"url": "https://example.com/docs/risk", "status": 200, "title": "Risk",
                       "text": 'Risk threshold 0.25\ncode = "a  b"\n最后于 2026年8月26日 更新',
                       "structure_sha256": sources.structure_digest([])}]}


def doc_source() -> dict:
    source = {"id": "example-docs", "kind": "docs", "role": "primary-reference",
              "url": "https://example.com/docs/", "runtime_dependency": False,
              "purpose": "study risk methods", "license_status": "unverified",
              "absorbed_revision": None, "decisions": []}
    snapshot = sources.make_snapshot(capture(), source)
    source.update(reviewed_snapshot=snapshot, reviewed_revision=snapshot["revision"],
                  observed={"revision": snapshot["revision"], "checked_at": snapshot["captured_at"]})
    return source


def git_source() -> dict:
    return {"id": "example-git", "kind": "git", "role": "adapter-candidate",
            "url": "https://github.com/example/project", "branch": "main",
            "tracked_paths": ["README.md", "src/"], "runtime_dependency": False,
            "purpose": "candidate", "license_status": "unverified", "decisions": [],
            "observed": {"revision": "a" * 40, "checked_at": sources.utc_now()},
            "reviewed_revision": "a" * 40, "absorbed_revision": None}


class DocumentObservationTests(unittest.TestCase):
    def test_nested_navigation_articles_are_one_content_root(self) -> None:
        raw = capture()
        raw["pages"][0]["html"] = '<article><article>Documentation </article><article>index</article></article>'
        self.assertEqual(sources.make_snapshot(raw, doc_source())["revision"],
                         sources.make_snapshot(capture(), doc_source())["revision"])
        raw["pages"][0]["html"] = '<article>Documentation </article><article>index</article>'
        with self.assertRaises(ValueError):
            sources.make_snapshot(raw, doc_source())

    def test_article_chrome_and_footer_noise_do_not_change_hash(self) -> None:
        source = doc_source()
        original = capture()
        changed = copy.deepcopy(original)
        changed["pages"][1].pop("text")
        changed["pages"][1]["html"] = ('<nav>different menu</nav><article>'
            'Risk threshold 0.25\ncode = "a  b"\n最后于 2026年9月14日 更新'
            '</article><footer>new links</footer>')
        self.assertEqual(sources.make_snapshot(original, source)["revision"],
                         sources.make_snapshot(changed, source)["revision"])

    def test_numbers_code_whitespace_and_order_are_significant(self) -> None:
        source = doc_source()
        original = capture()
        base = sources.make_snapshot(original, source)
        for text in ('Risk threshold 0.26\ncode = "a  b"',
                     'Risk threshold 0.25\ncode = "a b"',
                     'Risk threshold 0.25\ncode = "a\u200b  b"',
                     'code = "a  b"\nRisk threshold 0.25'):
            with self.subTest(text=text):
                changed = copy.deepcopy(original)
                changed["pages"][1]["text"] = text
                diff = sources.document_delta(base, sources.make_snapshot(changed, source))
                self.assertEqual(diff, [{"path": "https://example.com/docs/risk", "change": "modified"}])

    def test_table_cell_boundaries_and_code_block_structure_are_significant(self) -> None:
        source = doc_source()
        for first, second in (
            ('<article><table><tr><td>1</td><td>23</td></tr></table></article>',
             '<article><table><tr><td>12</td><td>3</td></tr></table></article>'),
            ('<article><pre>123</pre></article>', '<article><pre>1</pre><pre>23</pre></article>'),
            ('<article><table><tr><td>1</td><td>2</td></tr></table></article>',
             '<article><table><tr><td colspan="2">1</td><td>2</td></tr></table></article>')):
            before, after = capture(), capture()
            before["pages"][1]["html"] = first; after["pages"][1]["html"] = second
            delta = sources.document_delta(sources.make_snapshot(before, source), sources.make_snapshot(after, source))
            self.assertEqual(delta[0]["change"], "modified")

    def test_text_capture_requires_explicit_structure_evidence(self) -> None:
        raw = capture(); del raw["pages"][1]["structure_sha256"]
        with self.assertRaises(ValueError):
            sources.make_snapshot(raw, doc_source())

    def test_add_remove_rename_and_redirect(self) -> None:
        source = doc_source()
        changed = capture()
        changed["catalog_urls"] = [changed["catalog_urls"][0], "https://example.com/docs/new"]
        changed["pages"][1]["url"] = changed["catalog_urls"][1]
        delta = sources.document_delta(source["reviewed_snapshot"], sources.make_snapshot(changed, source))
        self.assertEqual({x["change"] for x in delta}, {"added", "removed_from_catalog"})
        changed = capture()
        changed["pages"][1]["final_url"] = "https://example.com/docs/renamed"
        self.assertEqual(sources.document_delta(source["reviewed_snapshot"], sources.make_snapshot(changed, source))[0]["change"], "redirected")
        changed = capture()
        changed["pages"][1]["title"] = "New title"
        self.assertEqual(sources.document_delta(source["reviewed_snapshot"], sources.make_snapshot(changed, source))[0]["change"], "modified")

    def test_partial_duplicate_empty_or_missing_root_catalog_is_rejected(self) -> None:
        candidates = []
        raw = capture(); raw["catalog_complete"] = False; candidates.append(raw)
        raw = capture(); raw["pages"].pop(); candidates.append(raw)
        raw = capture(); raw["catalog_urls"].append(raw["catalog_urls"][0]); candidates.append(raw)
        raw = capture(); raw["pages"][1] = raw["pages"][0]; candidates.append(raw)
        raw = capture(); raw["catalog_urls"] = []; raw["pages"] = []; candidates.append(raw)
        raw = capture(); raw["catalog_urls"].pop(0); raw["pages"].pop(0); candidates.append(raw)
        for index, raw in enumerate(candidates):
            with self.subTest(index=index), self.assertRaises(ValueError):
                sources.make_snapshot(raw, doc_source())

    def test_failed_login_challenge_missing_article_and_external_redirect_rejected(self) -> None:
        for field, value in (("status", 403), ("text", ""), ("title", "Just a moment"),
                             ("html", "<main>sign in</main>"),
                             ("html", "<article>a</article><article>b</article>"),
                             ("final_url", "https://example.com/login"),
                             ("final_url", "https://elsewhere.example/docs/risk")):
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                raw = capture(); raw["pages"][1][field] = value
                sources.make_snapshot(raw, doc_source())

    def test_private_query_and_credentials_are_rejected_without_echo(self) -> None:
        for url in ("https://example.com/docs?token=secretvalue", "https://secretvalue@example.com/docs"):
            with self.subTest(url=url), self.assertRaises(ValueError) as error:
                sources.public_url(url)
            self.assertNotIn("secretvalue", str(error.exception))

    def test_new_capture_is_metadata_only_and_stable_under_catalog_order(self) -> None:
        source, raw = doc_source(), capture()
        before = sources.make_snapshot(raw, source)
        raw["pages"].reverse(); raw["catalog_urls"].reverse()
        after = sources.make_snapshot(raw, source)
        self.assertEqual(before["revision"], after["revision"])
        self.assertTrue(all(set(p) == {"url", "final_url", "title", "sha256"} for p in after["pages"]))

    def test_changed_normalizer_requires_explicit_new_baseline(self) -> None:
        before = doc_source()["reviewed_snapshot"]
        after = copy.deepcopy(before); after["normalizer"] = "different"
        with self.assertRaises(ValueError):
            sources.document_delta(before, after)

    def test_fresh_stale_and_future_captures(self) -> None:
        source, raw = doc_source(), capture()
        self.assertEqual(sources.source_status(source, False, raw)["state"], "current")
        raw["captured_at"] = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        self.assertEqual(sources.source_status(source, False, raw)["state"], "stale")
        raw["pages"][1]["text"] = "A known older change still needs review"
        self.assertEqual(sources.source_status(source, False, raw)["state"], "review_required")
        raw["captured_at"] = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        with self.assertRaises(ValueError):
            sources.source_status(source, False, raw)

    def test_no_capture_never_claims_live_document_check(self) -> None:
        with patch.object(sources, "fetch_json") as fetch:
            self.assertEqual(sources.source_status(doc_source(), False)["state"], "cached")
            self.assertEqual(sources.source_status(doc_source(), True)["state"], "unavailable")
            fetch.assert_not_called()

    def test_reverted_document_does_not_clear_a_recorded_pending_observation(self) -> None:
        source = doc_source(); source["observed"]["revision"] = "b" * 64
        result = sources.source_status(source, False, capture())
        self.assertEqual(result["state"], "review_required")
        self.assertEqual(result["pending_observed_revision"], "b" * 64)


class GitObservationTests(unittest.TestCase):
    def test_reverted_git_branch_does_not_clear_pending_observation(self) -> None:
        source = git_source(); source["observed"]["revision"] = "b" * 40
        with patch.object(sources, "fetch_json", return_value={"object": {"type": "commit", "sha": "a" * 40}}):
            result = sources.source_status(source, True)
        self.assertEqual(result["state"], "review_required")
        self.assertEqual(result["pending_observed_revision"], "b" * 40)
    def test_cached_and_live_equal_revision_are_distinct(self) -> None:
        source = git_source()
        with patch.object(sources, "fetch_json") as fetch:
            self.assertEqual(sources.source_status(source, False)["state"], "cached")
            fetch.assert_not_called()
            fetch.return_value = {"object": {"type": "commit", "sha": "a" * 40}}
            self.assertEqual(sources.source_status(source, True)["state"], "current")

    def test_partially_read_source_is_not_completely_reviewed(self) -> None:
        source = git_source(); source["reviewed_revision"] = None
        self.assertEqual(sources.source_status(source, False)["state"], "review_required")

    def test_unreviewed_source_can_compare_new_updates_without_claiming_review(self) -> None:
        source = git_source(); source["reviewed_revision"] = None
        changes = [{"path": "src/risk.py", "change": "modified"}]
        with patch.object(sources, "fetch_json", return_value={"object": {"type": "commit", "sha": "b" * 40}}), patch.object(sources, "git_delta", return_value=changes) as delta:
            result = sources.source_status(source, True)
        delta.assert_called_once_with(source, "a" * 40, "b" * 40)
        self.assertEqual(result["changes"], changes)
        self.assertEqual(result["change_coverage"], "tracked_paths_since_observation")
        self.assertIsNone(result["reviewed_revision"])
        self.assertIsNone(source["reviewed_revision"])
        self.assertEqual(result["state"], "review_required")

    def test_changed_files_including_unicode_deletion_mode_and_scope(self) -> None:
        def tree(rows):
            return {"truncated": False, "tree": [{"path": path, "mode": mode, "sha": sha, "type": "blob"}
                    for path, mode, sha in rows]}
        old = tree([("src/旧规则.py", "100644", "1"), ("src/a.py", "100644", "2"),
                    ("src/exec.py", "100644", "3"), ("data/result.csv", "100644", "4")])
        new = tree([("src/a.py", "100644", "5"), ("src/exec.py", "100755", "3"),
                    ("src/new.py", "100644", "6"), ("data/result.csv", "100644", "7")])
        with patch.object(sources, "fetch_json", side_effect=[old, new]):
            changes = sources.git_delta(git_source(), "a" * 40, "b" * 40)
        self.assertEqual({(d["path"], d["change"]) for d in changes},
                         {("src/旧规则.py", "removed"), ("src/a.py", "modified"),
                          ("src/exec.py", "modified"), ("src/new.py", "added")})

    def test_truncated_tree_cannot_close_coverage(self) -> None:
        with patch.object(sources, "fetch_json", return_value={"truncated": True, "tree": []}):
            with self.assertRaises(ValueError):
                sources.git_delta(git_source(), "a" * 40, "b" * 40)

    def test_out_of_scope_commit_still_requires_disposition(self) -> None:
        with patch.object(sources, "fetch_json", return_value={"object": {"type": "commit", "sha": "b" * 40}}), patch.object(sources, "git_delta", return_value=[]):
            result = sources.source_status(git_source(), True)
        self.assertEqual(result["state"], "review_required")
        self.assertEqual(result["changes"], [])


class MultiSourceContractTests(unittest.TestCase):
    def lock_file(self, directory: str) -> Path:
        path = Path(directory) / "sources.lock.json"
        path.write_text(json.dumps({"upstreams": [], "reference_tracking": {
            "schema": "money-craft.reference-tracking.v1", "sources": [doc_source(), git_source()]}}))
        return path

    def test_partial_failure_preserves_other_results_and_lock_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self.lock_file(directory); before = path.read_bytes()
            with patch.object(status, "LOCK_PATH", path), patch.object(sources, "fetch_json", side_effect=OSError("private content")):
                result = status.build_all_status(True, [capture()], ["example-docs", "example-git"])
            self.assertEqual(result["state"], "partial")
            self.assertEqual({r["id"]: r["state"] for r in result["sources"]},
                             {"example-docs": "current", "example-git": "unavailable"})
            self.assertEqual(path.read_bytes(), before)
            self.assertNotIn("private content", json.dumps(result))

    def test_invalid_document_capture_does_not_abort_git_observation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self.lock_file(directory); raw = capture(); raw["pages"].pop()
            with patch.object(status, "LOCK_PATH", path), patch.object(sources, "fetch_json", return_value={"object": {"type": "commit", "sha": "a" * 40}}):
                result = status.build_all_status(True, [raw], ["example-docs", "example-git"])
            self.assertEqual(result["state"], "partial")
            self.assertEqual(result["sources"][1]["state"], "current")

    def test_unidentifiable_capture_does_not_abort_other_sources(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self.lock_file(directory)
            for raw in ({"pages": []}, [], None):
                with patch.object(status, "LOCK_PATH", path), patch.object(sources, "fetch_json", return_value={"object": {"type": "commit", "sha": "a" * 40}}):
                    result = status.build_all_status(True, [raw], ["example-git"])
                self.assertEqual(result["state"], "partial")
                self.assertEqual(result["sources"][0]["state"], "current")
                self.assertEqual(len(result["capture_errors"]), 1)

    def test_cli_invalid_json_capture_keeps_independent_results(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self.lock_file(directory)
            bad = Path(directory) / "invalid.json"; bad.write_text("{invalid")
            argv = ["upstream_status.py", "--source", "example-git", "--fetch", "--snapshot", str(bad)]
            with patch.object(sys, "argv", argv), patch.object(status, "LOCK_PATH", path), patch.object(sources, "fetch_json", return_value={"object": {"type": "commit", "sha": "a" * 40}}), redirect_stdout(io.StringIO()) as output:
                code = status.main()
            result = json.loads(output.getvalue())
            self.assertEqual(code, 1)
            self.assertEqual(result["state"], "partial")
            self.assertEqual(result["sources"][0]["state"], "current")

    def test_unknown_and_duplicate_capture_sources_are_input_errors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(status, "LOCK_PATH", self.lock_file(directory)):
                with self.assertRaises(ValueError):
                    status.build_all_status(False, source_ids=["unknown"])
                result = status.build_all_status(False, [capture(), capture()], ["example-docs"])
                self.assertEqual(result["state"], "partial")
                self.assertEqual(result["sources"][0]["state"], "unavailable")

    def test_legacy_cli_output_and_exit_codes_are_preserved(self) -> None:
        for state, code in (("current", 0), ("review_required", 2)):
            payload = {"schema": "money-craft.upstream-status.v1", "state": state}
            with patch.object(sys, "argv", ["upstream_status.py", "--json"]), patch.object(status, "build_status", return_value=payload), redirect_stdout(io.StringIO()) as output:
                self.assertEqual(status.main(), code)
            self.assertEqual(json.loads(output.getvalue()), payload)

    def test_v2_cli_exit_codes_and_source_selection(self) -> None:
        for state, code in (("current", 0), ("cached", 2), ("stale", 2), ("review_required", 2), ("partial", 1), ("unavailable", 1)):
            payload = {"schema": "money-craft.upstream-status.v2", "state": state}
            with patch.object(sys, "argv", ["upstream_status.py", "--source", "example-docs"]), patch.object(status, "build_all_status", return_value=payload), redirect_stdout(io.StringIO()):
                self.assertEqual(status.main(), code)

    def test_registry_rejects_false_adoption_duplicate_sources_and_bad_snapshot(self) -> None:
        base = {"upstreams": [], "reference_tracking": {
            "schema": "money-craft.reference-tracking.v1", "sources": [doc_source(), git_source()]}}
        self.assertEqual(sources.validate_tracking(base, ROOT), [])
        bad = copy.deepcopy(base); bad["reference_tracking"]["sources"].append(git_source())
        self.assertTrue(sources.validate_tracking(bad, ROOT))
        bad = copy.deepcopy(base); bad["reference_tracking"]["sources"][0]["reviewed_snapshot"]["pages"][0]["sha256"] = "0" * 64
        self.assertTrue(sources.validate_tracking(bad, ROOT))
        bad = copy.deepcopy(base); bad["reference_tracking"]["sources"][1]["decisions"] = [{
            "scope": "src/", "disposition": "adapt", "reason": "only a proposal", "targets": ["README.md"]}]
        self.assertTrue(sources.validate_tracking(bad, ROOT))

    def test_reviewed_document_inventory_matches_human_coverage(self) -> None:
        lock = json.loads((ROOT / "sources.lock.json").read_text())
        source = next(s for s in lock["reference_tracking"]["sources"] if s["id"] == "myinvestpilot")
        rows = [line.split("|") for line in (ROOT / "docs/upstreams/myinvestpilot.md").read_text().splitlines()
                if line.startswith("| ") and line.split("|")[1].strip().isdigit()]
        urls = [sources.public_url(row[3].strip().strip("<>")) for row in rows]
        self.assertEqual(len(urls), 155)
        self.assertEqual(len(set(urls)), 155)
        self.assertEqual(set(urls), {p["url"] for p in source["reviewed_snapshot"]["pages"]})
        self.assertEqual(sum(row[4].strip() == "navigation" for row in rows), 6)
        self.assertTrue(all(row[5].strip() == "reviewed" for row in rows))

if __name__ == "__main__":
    unittest.main()
