"""Exercise the delivery checker and the evidence ledger against shipped fixtures and deliberate regressions."""
import datetime as dt
import importlib.util
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(f'drama_{name}', PACKAGE / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check_eval = load('check_eval')
evidence = load('evidence')

CASE_02 = PACKAGE / 'evals/cases/02-dropoff-diagnosis.md'
CASE_04 = PACKAGE / 'evals/cases/04-hook-candidates.md'
BASE_02 = PACKAGE / 'evals/baselines/02-dropoff-diagnosis.md'
BASE_04 = PACKAGE / 'evals/baselines/04-hook-candidates.md'
TODAY = dt.date(2026, 11, 18)


class DeliveryChecks(unittest.TestCase):
    def setUp(self):
        self.case = check_eval.parse_case(CASE_02)
        self.text = BASE_02.read_text(encoding='utf-8')

    def errors(self, case=None, text=None):
        return check_eval.check_delivery(case or self.case, text if text is not None else self.text)

    def mutate(self, old, new):
        self.assertIn(old, self.text)
        return self.text.replace(old, new, 1)

    def test_shipped_baselines_pass(self):
        report = check_eval.run_all()
        self.assertTrue(report['ok'], report)
        self.assertEqual(report['cases'], ['01-three-directions', '02-dropoff-diagnosis', '03-retrospective',
                                           '04-hook-candidates', '05-batch-library'])
        self.assertEqual(report['uncovered'], [])

    def test_coverage_requirement_is_enforced(self):
        self.assertTrue(check_eval.run_all(require_coverage=5)['ok'])
        self.assertFalse(check_eval.run_all(require_coverage=9)['ok'])

    def test_missing_shot_column_is_rejected(self):
        errors = self.errors(text=self.mutate('| 卖点 | 素材来源 |', '| 卖点 | 来源 |'))
        self.assertTrue(any('missing columns' in error and '素材来源' in error for error in errors), errors)

    def test_non_contiguous_timecode_is_rejected(self):
        errors = self.errors(text=self.mutate('| S03 | 5.0–7.5 |', '| S03 | 6.0–7.5 |'))
        self.assertTrue(any('not contiguous' in error for error in errors), errors)

    def test_shot_longer_than_grid_is_rejected(self):
        errors = self.errors(text=self.mutate('| 3.5s |', '| 6.5s |'))
        self.assertTrue(any('generation grid' in error for error in errors), errors)

    def test_unknown_source_is_rejected(self):
        errors = self.errors(text=self.mutate('| 人群圈定 | AI |', '| 人群圈定 | 素材 |'))
        self.assertTrue(any('素材来源 must be one of' in error for error in errors), errors)

    def test_bad_asset_number_is_rejected(self):
        errors = self.errors(text=self.mutate('CH-01 / CH-02 / SC-01', 'CH-1 / CH-02'))
        self.assertTrue(any('参考资产 must use' in error for error in errors), errors)

    def test_long_dialogue_is_rejected(self):
        errors = self.errors(text=self.mutate('店员："你试试"', '店员："你先试一下这个再跟她们解释一下"'))
        self.assertTrue(any('台词 has' in error for error in errors), errors)

    def test_mechanism_without_number_is_rejected(self):
        errors = self.errors(text=self.mutate('字幕：39.9 两只送粉扑', '字幕：两只装送粉扑'))
        self.assertTrue(any('carries no number' in error for error in errors), errors)

    def test_empty_cell_is_rejected(self):
        errors = self.errors(text=self.mutate('| 手势只到伸手拦，不抓手腕 |', '|  |'))
        self.assertTrue(any('生成要点 must not be empty' in error for error in errors), errors)

    def test_matrix_with_two_changes_is_rejected(self):
        text = '\n'.join([
            '## 五、变量矩阵',
            '',
            '| 编号 | 原型 | 钩子形态 | 转化镜 | 本轮状态 |',
            '| --- | --- | --- | --- | --- |',
            '| R1-A | P1 | 反常台词 | 2s 上妆 | 基线 |',
            '| R2-A | P1 | 结果前置 | 硬切实拍 | 改了两列 |',
        ])
        errors = self.errors(text=text)
        self.assertTrue(any('changes 2 columns' in error for error in errors), errors)

    def test_component_as_main_prototype_is_rejected(self):
        text = '\n'.join([
            '## 五、变量矩阵',
            '',
            '| 编号 | 原型 | 转化镜 | 本轮状态 |',
            '| --- | --- | --- | --- |',
            '| R1-A | P10 | 2s 上妆 | 基线 |',
            '| R2-A | P10 | 硬切实拍 | 仅改转化镜 |',
        ])
        errors = self.errors(text=text)
        self.assertTrue(any('not a main prototype' in error for error in errors), errors)

    def test_forbidden_shot_table_is_rejected(self):
        case = check_eval.parse_case(CASE_04)
        text = BASE_04.read_text(encoding='utf-8')
        shot = BASE_02.read_text(encoding='utf-8').split('## 四、改写后分镜表', 1)[1].split('## 五、', 1)[0]
        errors = check_eval.check_delivery(case, text + '\n## 分镜表' + shot)
        self.assertTrue(any('must not ship a shot table' in error for error in errors), errors)

    def test_missing_required_section_is_rejected(self):
        errors = self.errors(text=self.text.replace('## 五、冻结不变量', '## 五、备注'))
        self.assertTrue(any('冻结不变量' in error for error in errors), errors)


class EvidenceChecks(unittest.TestCase):
    def ledger(self, rounds=(), library=()):
        return {'schema_version': 1, 'rounds': list(rounds), 'library': list(library)}

    def round(self, prototype='P1', samples=3, attribution='hypothesis_rejected', conclusion='keep'):
        return {'prototype': prototype, 'round': 'R1', 'variable': '转化镜形态', 'samples': samples,
                'metrics': {'3s': 0.42}, 'conclusion': conclusion, 'attribution': attribution}

    def declared(self, **levels):
        payload = {f'P{n}': 'C' for n in range(1, 12)}
        payload.update(levels)
        return {'schema_version': 1, 'levels': payload}

    def test_empty_ledger_is_all_c(self):
        computed = evidence.compute(self.ledger(), TODAY)
        self.assertEqual(set(computed.values()), {'C'})
        self.assertEqual(len(computed), 11)

    def test_three_strong_rounds_reach_a(self):
        rounds = [self.round() for _ in range(3)]
        self.assertEqual(evidence.compute(self.ledger(rounds=rounds), TODAY)['P1'], 'A')

    def test_weak_round_blocks_upgrade(self):
        rounds = [self.round() for _ in range(3)]
        rounds[2] = self.round(samples=1)
        self.assertEqual(evidence.compute(self.ledger(rounds=rounds), TODAY)['P1'], 'C')

    def test_insufficient_sample_attribution_blocks_upgrade(self):
        rounds = [self.round(attribution='insufficient_sample') for _ in range(3)]
        self.assertEqual(evidence.compute(self.ledger(rounds=rounds), TODAY)['P1'], 'C')

    def test_five_library_samples_reach_b(self):
        library = [{'prototype': 'P2', 'samples': 5, 'window': '2026-03..2026-06', 'reviewed': '2026-11-01'}]
        self.assertEqual(evidence.compute(self.ledger(library=library), TODAY)['P2'], 'B')

    def test_stale_review_falls_back_to_c(self):
        library = [{'prototype': 'P2', 'samples': 5, 'window': '2025-01..2025-03', 'reviewed': '2026-01-01'}]
        self.assertEqual(evidence.compute(self.ledger(library=library), TODAY)['P2'], 'C')

    def test_understated_level_is_rejected(self):
        errors = evidence.check(self.ledger(rounds=[self.round() for _ in range(3)]),
                                self.declared(), '均为 C 级', TODAY)
        self.assertTrue(any('upgrade levels.json' in error for error in errors), errors)

    def test_overstated_level_is_rejected(self):
        errors = evidence.check(self.ledger(), self.declared(P1='B'), '', TODAY)
        self.assertTrue(any('only supports C' in error for error in errors), errors)

    def test_readme_must_state_all_c(self):
        errors = evidence.check(self.ledger(), self.declared(), '证据等级 C', TODAY)
        self.assertTrue(any('均为 C 级' in error for error in errors), errors)

    def test_readme_must_not_claim_all_c_after_upgrade(self):
        library = [{'prototype': 'P2', 'samples': 5, 'reviewed': '2026-11-01'}]
        errors = evidence.check(self.ledger(library=library), self.declared(P2='B'), '均为 C 级', TODAY)
        self.assertTrue(any('still claims 均为 C 级' in error for error in errors), errors)

    def test_unknown_prototype_and_attribution_are_rejected(self):
        rounds = [{'prototype': 'P13', 'round': 'R9', 'variable': '', 'samples': 0,
                   'attribution': 'vibes', 'conclusion': 'maybe'}]
        errors = evidence.check(self.ledger(rounds=rounds), self.declared(), '均为 C 级', TODAY)
        self.assertTrue(any('unknown prototype' in error for error in errors), errors)
        self.assertTrue(any('does not name the single variable' in error for error in errors), errors)
        self.assertTrue(any('unknown attribution' in error for error in errors), errors)

    def test_shipped_ledger_matches_shipped_levels(self):
        ledger = evidence.load(evidence.LEDGER)
        declared = evidence.load(evidence.LEVELS)
        readme = evidence.README.read_text(encoding='utf-8')
        self.assertEqual(evidence.check(ledger, declared, readme, TODAY), [])


if __name__ == '__main__':
    unittest.main()
