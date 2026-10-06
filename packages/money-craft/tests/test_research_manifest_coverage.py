import json
from pathlib import Path
import tempfile
import unittest
import test_research_run as fixtures
from test_research_run import research_run as rr

class ManifestCoverageTests(unittest.TestCase):
    def test_rehashed_manifest_cannot_omit_or_relabel_expected_evidence(self):
        helper=fixtures.ResearchRunTests()
        for mutation in ('sources','file','role','identity','count','duplicate'):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as directory:
                root=helper.initialize(directory);helper.collect(root)
                helper.import_official_sources(root,directory);helper.write_finalization_artifacts(root)
                self.assertTrue(rr.finalize_workspace(root)['valid'])
                path=root/'evidence-manifest.json';manifest=json.loads(path.read_text())
                if mutation=='sources':manifest['sources']=[];manifest['source_count']=0
                elif mutation=='file':manifest['sources'][0]['files'].pop()
                elif mutation=='role':manifest['sources'][0]['files'][0]['role']='unverified-relabel'
                elif mutation=='identity':manifest['security_id']='CN-SSE:600519'
                elif mutation=='count':manifest['source_count']=999
                else:manifest['sources'].append(manifest['sources'][0]);manifest['source_count']+=1
                path.write_text(json.dumps(manifest))
                receipt_path=root/'completion-receipt.json';receipt=json.loads(receipt_path.read_text());receipt['bindings']['evidence-manifest.json']=rr.sha256_file(path);receipt_path.write_text(json.dumps(receipt))
                status=rr.research_status(root)
                self.assertFalse(status['complete'])
                self.assertEqual(status['assessment']['receipt_integrity'],'INVALID')
                with self.assertRaises(rr.ResearchRunError):rr.finalize_workspace(root)
