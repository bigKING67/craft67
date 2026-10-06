"""Case replay integrity, not an automated economics classifier."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('liquidity_replay', ROOT / 'scripts/check_liquidity_semantics.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class LiquidityReplayTests(unittest.TestCase):
    def test_pairs_preserve_facts_and_arithmetic(self):
        cases = json.loads((ROOT / 'acceptance/liquidity-semantics/cases.json').read_text())['cases']
        self.assertEqual(len({c['id'] for c in cases}), 4)
        for case in cases:
            with self.subTest(case=case['id']):
                good = module.report(case, case['supported_claim'])
                bad = module.report(case, case['contradicted_claim'])
                self.assertEqual(good.replace(case['supported_claim'], '<claim>', 1),
                                 bad.replace(case['contradicted_claim'], '<claim>', 1))
                self.assertTrue(module.report_audit(good)['valid'])
                self.assertTrue(module.financial_audit(good)['valid'])
                # A real numeric corruption must fail even when the prose stays sound.
                wrong = good.replace('"expected": "' + case['calculation']['expected'] + '"',
                                     '"expected": "-999999"')
                self.assertNotEqual(wrong, good)
                self.assertFalse(module.financial_audit(wrong)['valid'])

    def test_replay_does_not_claim_semantic_or_host_verdict(self):
        result = module.replay(ROOT / 'acceptance/liquidity-semantics/cases.json')
        self.assertFalse(result['host_skill_evaluated'])
        self.assertFalse(result['independent_semantic_review'])
        self.assertEqual(len(result['results']), 8)
        self.assertTrue(all(not r['manual_label_is_runtime_verdict'] for r in result['results']))


if __name__ == '__main__':
    unittest.main()
