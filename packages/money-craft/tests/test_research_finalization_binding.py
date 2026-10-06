import json
from pathlib import Path
import tempfile
import unittest
import test_research_run as fixtures
from test_research_run import research_run as rr

class FinalizationBindingTests(unittest.TestCase):
    def test_wrong_duplicate_or_nonterminal_event_cannot_complete(self):
        helper=fixtures.ResearchRunTests()
        for mutation in ('hash','count','bool','details','duplicate','after','missing_receipt'):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as directory:
                root=helper.initialize(directory);helper.collect(root)
                helper.import_official_sources(root,directory);helper.write_finalization_artifacts(root)
                self.assertTrue(rr.finalize_workspace(root)['valid'])
                path=root/'run-state.json';state=json.loads(path.read_text());event=state['events'][-1]
                if mutation=='missing_receipt':(root/'completion-receipt.json').unlink()
                elif mutation=='hash':event['details']['manifest_sha256']='0'*64
                elif mutation=='count':event['details']['provider_gap_count']=999
                elif mutation=='bool':event['details']['provider_gap_count']=False
                elif mutation=='details':event['details']={}
                else:
                    extra=json.loads(json.dumps(event));extra['sequence']+=1
                    if mutation=='after':extra['type']='provider-collection'
                    state['events'].append(extra);state['revision']+=1
                path.write_text(json.dumps(state))
                before={str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}
                status=rr.research_status(root)
                self.assertFalse(status['complete'])
                with self.assertRaises(rr.ResearchRunError):rr.finalize_workspace(root)
                self.assertEqual(before,{str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()})
