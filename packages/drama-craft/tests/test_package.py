"""Exercise the drama-craft static checks against the real skill and deliberate regressions."""
import contextlib
import importlib.util
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('drama_check', PACKAGE / 'scripts/check.py')
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)

SKILL = Path('skills') / 'drama-craft'


class SkillChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.package = Path(self.temp.name) / 'drama-craft'
        shutil.copytree(PACKAGE, self.package, ignore=shutil.ignore_patterns('__pycache__', '.venv'))
        self.root = self.package / SKILL

    def edit(self, relative, old, new):
        path = self.root / relative
        text = path.read_text(encoding='utf-8')
        self.assertIn(old, text)
        path.write_text(text.replace(old, new, 1), encoding='utf-8')

    def edit_doc(self, name, old, new):
        path = self.package / name
        text = path.read_text(encoding='utf-8')
        self.assertIn(old, text)
        path.write_text(text.replace(old, new, 1), encoding='utf-8')

    def skill_errors(self):
        return check.check_skill(self.root)

    def test_shipped_package_passes(self):
        self.assertEqual(check.check_skill(PACKAGE / SKILL), [])
        self.assertEqual(check.check_docs(PACKAGE), [])

    def test_missing_reference_is_rejected(self):
        (self.root / 'references' / 'iteration-loop.md').unlink()
        self.assertTrue(any('iteration-loop.md' in error for error in self.skill_errors()))

    def test_orphan_reference_is_rejected(self):
        (self.root / 'references' / 'extra.md').write_text('# extra\n', encoding='utf-8')
        self.assertTrue(any('not linked from SKILL.md' in error for error in self.skill_errors()))

    def test_broken_link_is_rejected(self):
        self.edit('SKILL.md', '(references/iteration-loop.md)', '(references/missing.md)')
        self.assertTrue(any('link target is missing' in error for error in self.skill_errors()))

    def test_escaping_link_is_rejected(self):
        self.edit('SKILL.md', '(references/iteration-loop.md)', '(../../../etc/passwd)')
        self.assertTrue(any('escapes the skill directory' in error for error in self.skill_errors()))

    def test_placeholder_is_rejected(self):
        self.edit('references/iteration-loop.md', '## 六、反模式', 'TODO\n\n## 六、反模式')
        self.assertTrue(any('placeholder marker' in error for error in self.skill_errors()))

    def test_name_mismatch_is_rejected(self):
        self.edit('SKILL.md', 'name: drama-craft', 'name: other-craft')
        self.assertTrue(any('does not match directory' in error for error in self.skill_errors()))

    def test_missing_description_is_rejected(self):
        path = self.root / 'SKILL.md'
        lines = [line for line in path.read_text(encoding='utf-8').splitlines() if not line.startswith('description:')]
        path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        self.assertTrue(any('missing description' in error for error in self.skill_errors()))

    def test_missing_iron_rule_is_rejected(self):
        self.edit('SKILL.md', '施压者永远不是主角', '施压者可以是主角')
        self.assertTrue(any('iron rule' in error for error in self.skill_errors()))

    def test_iron_rule_outside_its_section_is_rejected(self):
        self.edit('SKILL.md', '1. **施压者永远不是主角**：顾客', '1. **压力方安排**：顾客')
        self.edit('SKILL.md', '## 常见失败模式', '## 常见失败模式\n\n- 施压者永远不是主角。')
        errors = self.skill_errors()
        self.assertTrue(any('施压者永远不是主角' in error and 'iron rule' in error for error in errors), errors)

    def test_iron_rule_section_needs_scope_marker(self):
        self.edit('SKILL.md', '**适用范围：主原型 P1–P5 与 P11**。P6–P8 与组件 P9、P10 用下方等价硬约束替代——不要为了让剧本"符合铁律"给无冲突原型硬塞施压者。', '先遵守再谈创新。')
        self.edit('SKILL.md', '等价硬约束（无施压者、或全片即机制的原型）：', '其他原型：')
        errors = self.skill_errors()
        self.assertTrue(any('适用范围' in error or '等价硬约束' in error for error in errors), errors)

    def test_prototype_gap_is_rejected(self):
        self.edit('references/story-patterns.md', '## P5 古装宫斗型', '## 古装宫斗型')
        self.assertTrue(any('P1-P11' in error for error in self.skill_errors()))

    def test_prototype_missing_field_is_rejected(self):
        self.edit('references/story-patterns.md', '- **生产提示**：质疑者必须外化', '- **执行提示**：质疑者必须外化')
        errors = self.skill_errors()
        self.assertTrue(any('P1 is missing field: 生产提示' in error for error in errors), errors)

    def test_main_prototype_missing_emotion_path_is_rejected(self):
        self.edit('references/story-patterns.md', '- **情绪路径**：被质疑 → 解释 → 给质疑者试用 → 被认可。', '- **推进**：被质疑 → 解释 → 给质疑者试用 → 被认可。')
        errors = self.skill_errors()
        self.assertTrue(any('main prototype P1 is missing field: 情绪路径' in error for error in errors), errors)

    def test_mechanism_placeholder_statement_is_required(self):
        self.edit('references/output-templates.md', '**不得直接作为宣称**', '可作为宣称')
        errors = self.skill_errors()
        self.assertTrue(any('不得直接作为宣称' in error for error in errors), errors)

    def test_generation_handoff_is_required(self):
        self.edit('references/production-craft.md', '## 生成交接（写脚本时就决定怎么生成）', '## 提示词备注')
        errors = self.skill_errors()
        self.assertTrue(any('生成交接' in error for error in errors), errors)


class DocChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.package = Path(self.temp.name) / 'drama-craft'
        shutil.copytree(PACKAGE, self.package, ignore=shutil.ignore_patterns('__pycache__', '.venv'))

    def edit_doc(self, name, old, new):
        path = self.package / name
        text = path.read_text(encoding='utf-8')
        self.assertIn(old, text)
        path.write_text(text.replace(old, new, 1), encoding='utf-8')

    def test_shipped_docs_pass(self):
        self.assertEqual(check.check_docs(PACKAGE), [])

    def test_prototype_count_drift_is_rejected(self):
        self.edit_doc('README.md', 'P1–P11', 'P1–P10')
        self.assertTrue(any('prototype range' in error for error in check.check_docs(self.package)))

    def test_source_version_drift_is_rejected(self):
        self.edit_doc('VERSION', '0.2.0', '0.3.0')
        errors = check.check_docs(self.package)
        self.assertTrue(any('源码' in error for error in errors), errors)
        self.assertTrue(any('CHANGELOG.md must open a section' in error for error in errors), errors)

    def test_readme_overclaim_is_rejected(self):
        self.edit_doc('README.md', '11 个已归类原型', '11 个已验证原型')
        self.assertTrue(any('verified' in error for error in check.check_docs(self.package)))


class CommandLine(unittest.TestCase):
    def test_main_reports_ok_and_exit_code(self):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = check.main()
        report = json.loads(buffer.getvalue())
        self.assertEqual(code, 0)
        self.assertTrue(report['ok'])
        self.assertEqual(report['skill'], 'drama-craft')
        self.assertEqual(report['prototypes'], 11)
        self.assertEqual(report['errors'], [])


if __name__ == '__main__':
    unittest.main()
