"""Public quotation admission must preserve evidence and sealing boundaries."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import test_research_run as fixtures

run = fixtures.research_run


class PublicEvidenceTests(unittest.TestCase):
    initialize = fixtures.ResearchRunTests.initialize
    collect = fixtures.ResearchRunTests.collect
    import_official_sources = fixtures.ResearchRunTests.import_official_sources
    write_finalization_artifacts = fixtures.ResearchRunTests.write_finalization_artifacts

    def admit(self, workspace, directory, **overrides):
        source = Path(directory) / 'quote.html'
        source.write_text('<!doctype html><html>000333 quotation 84.40</html>')
        args = dict(source_id='S31', source_file=source, url='https://example.invalid/quote',
                    captured_at='2026-08-23T10:00:00+08:00', observed_at='2026-08-21T15:00:00+08:00')
        args.update(overrides)
        return run.import_public_source(workspace, **args)

    def complete_inputs(self, workspace, directory):
        self.collect(workspace)
        self.import_official_sources(workspace, directory)
        self.write_finalization_artifacts(workspace)
        for name in ('report.md', 'thesis.md'):
            p = workspace / name
            p.write_text(p.read_text().replace('## 来源索引', '## 来源索引\n\n- [S31] https://example.invalid/quote'))

    def test_public_quote_can_finalize_without_becoming_official_or_verified(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory)
            result = self.admit(workspace, directory)
            self.assertEqual(result['schema'], 'money-craft.public-import.v1')
            self.assertEqual(result['kind'], 'public-material')
            self.assertEqual(result['local_path'], 'evidence/S31-public.html')
            self.assertTrue({'S11', 'S12', 'S13'}.issubset(run.research_status(workspace)['missing_sources']))
            self.assertNotIn('S31', run.research_status(workspace)['missing_sources'])
            self.complete_inputs(workspace, directory)
            self.assertTrue(run.finalize_workspace(workspace)['valid'])
            status = run.research_status(workspace)
            self.assertTrue(status['complete'])
            self.assertEqual(status['assessment']['claim_support'], 'UNVERIFIED')
            self.assertNotIn('S31', [x['id'] for x in status['official_results']])
            manifest = json.loads((workspace / 'evidence-manifest.json').read_text())
            source = next(x for x in manifest['sources'] if x['id'] == 'S31')
            self.assertEqual(source['trust'], 'unverified-public')
            self.assertEqual(source['observed_at'], '2026-08-21T15:00:00+08:00')
            with self.assertRaisesRegex(run.ResearchRunError, 'sealed'):
                self.admit(workspace, directory, source_id='S32')

    def test_wrong_url_remains_rejected_and_unknown_source_cannot_be_admitted(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory)
            self.admit(workspace, directory, url='https://example.invalid/different')
            self.complete_inputs(workspace, directory)
            result = run.finalize_workspace(workspace)
            self.assertFalse(result['valid'])
            self.assertTrue(any('URL' in e for e in result['audits']['report']['citation_binding']['errors']))
            with self.assertRaises(run.ResearchRunError):
                self.admit(workspace, directory, source_id='S99')
            with self.assertRaises(run.ResearchRunError):
                run.import_official_source(workspace, source_id='S32', source_file=Path(directory)/'quote.html', url='https://example.invalid/quote')

    def test_hash_drift_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory)
            self.admit(workspace, directory)
            (workspace/'evidence/S31-public.html').write_text('<html>changed quote</html>')
            with self.assertRaisesRegex(run.ResearchRunError, 'changed after import'):
                run.research_status(workspace)

    def test_time_boundaries_do_not_write_evidence(self):
        invalid = [dict(captured_at='2026-08-23'), dict(observed_at='2026-08-24T10:00:00+08:00'),
                   dict(captured_at='2026-08-20T10:00:00+08:00'), dict(observed_at='not-a-date')]
        for values in invalid:
            with self.subTest(values=values), tempfile.TemporaryDirectory() as directory:
                workspace = self.initialize(directory)
                before = (workspace/'case.json').read_bytes()
                with self.assertRaisesRegex(run.ResearchRunError, 'timezone-aware'):
                    self.admit(workspace, directory, **values)
                self.assertEqual(before, (workspace/'case.json').read_bytes())
                self.assertFalse((workspace/'evidence/S31-public.html').exists())

    def test_old_plan_has_no_new_slots_and_still_finalizes(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)/'old'
            plan = fixtures.example_plan()
            plan.pop('public_evidence_requirements')
            run.initialize_workspace(workspace, plan, template_root=fixtures.ROOT/'skills/money-craft/templates')
            before = (workspace/'plan.json').read_bytes()
            with self.assertRaises(run.ResearchRunError):
                self.admit(workspace, directory)
            self.collect(workspace)
            self.import_official_sources(workspace, directory)
            self.write_finalization_artifacts(workspace)
            self.assertTrue(run.finalize_workspace(workspace)['valid'])
            self.assertEqual(before, (workspace/'plan.json').read_bytes())
            self.assertNotIn('public_sources', json.loads((workspace/'case.json').read_text()))

    def test_interrupted_public_import_is_not_silently_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory)
            with patch.object(run, 'record_event', side_effect=OSError('interrupted')):
                with self.assertRaises(OSError):
                    self.admit(workspace, directory)
            with self.assertRaisesRegex(run.ResearchRunError, 'no completion event'):
                run.research_status(workspace)

    def test_public_source_identity_cannot_be_promoted(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory)
            self.admit(workspace, directory)
            p = workspace/'case.json'; case = json.loads(p.read_text())
            case['public_sources'][0]['kind'] = 'official-document'
            p.write_text(json.dumps(case))
            with self.assertRaisesRegex(run.ResearchRunError, 'identity'):
                run.research_status(workspace)

    def test_duplicate_import_and_staged_orphan_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory)
            self.admit(workspace, directory)
            before = (workspace/'evidence/S31-public.html').read_bytes()
            with self.assertRaisesRegex(run.ResearchRunError, 'already imported'):
                self.admit(workspace, directory)
            self.assertEqual(before, (workspace/'evidence/S31-public.html').read_bytes())
            (workspace/'evidence/S32-public.html').write_text('<html>orphan</html>')
            with self.assertRaisesRegex(run.ResearchRunError, 'unregistered'):
                run.research_status(workspace)

    def test_public_symlink_and_capture_date_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory)
            target = Path(directory)/'target.html'; target.write_text('<html>data</html>')
            link = Path(directory)/'link.html'; link.symlink_to(target)
            with self.assertRaisesRegex(run.ResearchRunError, 'symlink'):
                self.admit(workspace, directory, source_file=link)
            with self.assertRaisesRegex(run.ResearchRunError, 'capture date'):
                self.admit(workspace, directory, retrieved_on='2026-08-22')

    def test_sealed_public_timestamp_drift_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.initialize(directory)
            self.admit(workspace, directory)
            self.complete_inputs(workspace, directory)
            self.assertTrue(run.finalize_workspace(workspace)['valid'])
            p = workspace/'case.json'; data = json.loads(p.read_text())
            data['public_sources'][0]['observed_at'] = '2026-08-20T15:00:00+08:00'
            p.write_text(json.dumps(data))
            self.assertFalse(run.research_status(workspace)['complete'])

    def test_duplicate_ids_across_collections_rejected(self):
        plan = fixtures.example_plan()
        plan['public_evidence_requirements'][0]['id'] = 'S11'
        with self.assertRaises(run.ResearchRunError):
            run.derived_case(plan, 'a'*64)


if __name__ == '__main__':
    unittest.main()
