from __future__ import annotations

import re
import json
import subprocess
import tempfile
import os
from unittest import mock
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "money-craft" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import money_craft  # noqa: E402
import report_renderer  # noqa: E402

try:  # 渲染端到端用例需要可选 Markdown 包；核心运行时保持 stdlib-only
    import markdown  # noqa: F401

    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False


SAMPLE_REPORT = """> 研究日期：2026-08-24
> 数据截止：2026-08-23T23:59:59+08:00
> 核心结论：长期质量较高，当前结论为 WATCH。

<style>body { font-size: 9pt; }</style>

# 示例公司（600000.SH）基本面研究

> 研究对象：示例公司

## 结论

截止日收盘价为 84.30 元，按2025年基本每股收益计算的静态 PE 约 14.53 倍。[S01]

## 财务趋势

| 指标 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| 营业收入（亿元） | 100 | 110 | 120 | 130 | 150 |
| 归母净利润（亿元） | 10 | 11 | 13 | 15 | 18 |
| 经营现金流（亿元） | 8 | 13 | 9 | 16 | 14 |

## 估值与假设

| 情景 | EPS | PE | 示意价值 |
|---|---:|---:|---:|
| Bear | 5.50 | 11 | 60.50 元 |
| Base | 6.09 | 14 | 85.26 元 |
| Bull | 6.50 | 17 | 110.50 元 |

## 主要数据来源

- [S01] https://example.invalid/report.pdf
"""


EXTENDED_REPORT = """> 研究日期：2026-08-24
> 数据截止：2026-08-23T23:59:59+08:00
> 核心结论：长期质量较高，当前结论为 WATCH。

# 示例公司（600000.SH）基本面研究

> 研究对象：示例公司

## 结论

截止日收盘价为 84.30 元，按2025年基本每股收益计算的静态 PE 约 14.53 倍。[S01]

## 财务趋势

| 指标 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| 营业收入（亿元） | 100 | 110 | 120 | 130 | 150 |
| 归母净利润（亿元） | 10 | 11 | 13 | 15 | 18 |
| 基本 EPS（元） | 0.98 | 1.06 | 1.24 | 1.42 | 1.70 |
| 经营现金流（亿元） | 8 | 13 | 9 | 16 | 14 |
| 资本开支代理项（亿元） | 5 | 7 | 6 | 9 | 10 |

## 最近一期变化

| 指标 | 2026Q1 | 同比 |
|---|---:|---:|
| 营业收入（亿元） | 40 | +9.50% |
| 归母净利润（亿元） | 4 | -12.30% |
| 经营现金流（亿元） | 2 | 持平 |
| 基本 EPS（元） | 0.38 | -11.20% |

## 估值与假设

| 情景 | EPS | PE | 示意价值 |
|---|---:|---:|---:|
| Bear | 5.50 | 11 | 60.50 元 |
| Base | 6.09 | 14 | 85.26 元 |
| Bull | 6.50 | 17 | 110.50 元 |

## 风险与证伪条件

| 编号 | 条件 | 强度 | 状态 |
|---|---|---|---|
| R01 | 经营现金流连续两年为负 | material | WATCH |
| R02 | 商誉减值超过净资产三成 | fatal | CLEAR |
| R03 | 关联交易占比异常上升 | material | UNVERIFIED |

## 主要数据来源

- [S01] https://example.invalid/report.pdf
"""


class ReportRendererTests(unittest.TestCase):
    @unittest.skipUnless(HAS_MARKDOWN, "optional markdown package required")
    def test_chart_candidates_follow_visible_top_level_markdown_tables(self):
        table = "| 指标 | 2023 | 2024 | 2025 |\n|---|---|---|---|\n| 营业收入（亿元） | 1 | 2 | 3 |\n| 归母净利润（亿元） | 1 | 2 | 3 |"
        examples = ["<!--\n" + table + "\n-->", "<div>\n" + table + "\n</div>",
                    "<details>\n" + table + "\n</details>", "```\n" + table + "\n```",
                    "\n".join("> " + line for line in table.splitlines()),
                    "- example\n\n" + "\n".join("    " + line for line in table.splitlines())]
        for example in examples:
            with self.subTest(example=example[:30]):
                tables = []
                report_renderer.markdown_to_html(example, chart_tables=tables)
                self.assertEqual(tables, [])
                report_renderer.markdown_to_html(example + "\n\n" + table, chart_tables=tables)
                self.assertEqual(tables, report_renderer.parse_markdown_tables(table))

    def test_audit_display_does_not_infer_pass_from_list_or_conflicting_counts(self):
        for payload in ([], [{"valid": False}], {"verdict": "PASS", "total": 2, "check_count": 3, "pass_count": 2}, {"valid": False, "verdict": "PASS"},
                        {"verdict": "PASS", "pass_count": 1, "total": 2},
                        {"verdict": "PASS", "pass_count": True, "total": 1}):
            with self.subTest(payload=payload):
                self.assertNotEqual(report_renderer.audit_summary(payload, None)[1], "PASS")

    @unittest.skipUnless(HAS_MARKDOWN, "optional markdown package required")
    def test_hidden_price_cannot_override_visible_report_or_scenario(self):
        for hidden in ("<!-- 收盘价999元 -->", "```\n收盘价999元\n```", "> 收盘价999元", "<div>收盘价999元</div>"):
            parsed = report_renderer.parse_report(SAMPLE_REPORT.replace("## 结论", "## 结论\n\n" + hidden + "\n"))
            document, _ = report_renderer.build_document(parsed, "a" * 64,
                template=report_renderer.DEFAULT_TEMPLATE.read_text(), style=report_renderer.DEFAULT_STYLE.read_text(),
                script=report_renderer.DEFAULT_SCRIPT.read_text(), audit=None, evidence=None, revision=None,
                archive_manifest=None, charts=True)
            self.assertIn('600000.SH · 2026-08-24', document)
            self.assertIn('截止日 84.30', document)
            self.assertNotIn('截止日 999', document)
            self.assertNotIn('999 元</dd>', document)

    def test_falsification_status_comes_from_status_column(self):
        table = report_renderer.MarkdownTable(("编号", "条件", "强度", "状态"),
            (("R01", "由 WATCH 转为已触发", "material", "BROKEN"),))
        self.assertEqual(report_renderer.falsification_rows([table]), [("R01", "material", "BROKEN")])
        ambiguous = report_renderer.MarkdownTable(("编号", "状态", "强度", "当前状态"), table.rows)
        self.assertIsNone(report_renderer.falsification_rows([ambiguous]))

    def test_company_name_suffix_and_duplicate_scenarios(self):
        self.assertEqual(report_renderer.display_company_name(report_renderer.parse_report(SAMPLE_REPORT)), "示例公司")
        table = report_renderer.scenario_table(report_renderer.parse_markdown_tables(SAMPLE_REPORT))
        self.assertTrue(report_renderer.scenario_chart(table, None))
        duplicate = report_renderer.MarkdownTable(table.headers, table.rows + (table.rows[0],))
        self.assertEqual(report_renderer.scenario_chart(duplicate, None), "")

    def test_code_tables_are_excluded_from_chart_candidates(self):
        table = "| 指标 | 2023 | 2024 | 2025 |\n|---|---|---|---|\n| 营业收入（亿元） | 1 | 2 | 3 |\n| 归母净利润（亿元） | 1 | 2 | 3 |"
        for opening, closing in (("```markdown", "```"), ("~~~~", "~~~~"), ("````", "`````"), ("  ```", "  ```")):
            with self.subTest(opening=opening):
                self.assertEqual(report_renderer.parse_markdown_tables(opening+"\n"+table+"\n"+closing), [])
                self.assertEqual(report_renderer.parse_markdown_tables(opening+"\n"+table), [])
        for indent in ("    ", "\t", " \t", "  \t", "   \t"):
            with self.subTest(indent=repr(indent)):
                self.assertEqual(report_renderer.parse_markdown_tables("\n".join(indent+line for line in table.splitlines())), [])
        self.assertEqual(report_renderer.parse_markdown_tables("```\n"+table+"\n```\n\n"+table), report_renderer.parse_markdown_tables(table))

    def test_table_separator_must_match_every_header_column(self):
        for separator in ("|---|bad|---|", "|---|---|", "|---|---|---|extra|"):
            with self.subTest(separator=separator):
                self.assertEqual(report_renderer.parse_markdown_tables("| a | b | c |\n"+separator+"\n| 1 | 2 | 3 |"), [])

    @unittest.skipUnless(HAS_MARKDOWN, "optional markdown package required")
    def test_cli_code_example_cannot_supply_financial_chart(self):
        content = SAMPLE_REPORT.replace("## 财务趋势", "## 财务趋势\n\n```markdown").replace("## 估值与假设", "```\n\n## 估值与假设")
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory)/"source.md", Path(directory)/"out.html"
            source.write_text(content)
            before = source.read_bytes()
            result = subprocess.run([sys.executable, str(SCRIPT_DIR/"report_renderer.py"), "--source", str(source), "--output-html", str(output), "--html-only"], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr+result.stdout)
            self.assertTrue(json.loads(result.stdout)["valid"])
            rendered = output.read_text()
            self.assertNotIn('data-chart="financial-trends"', rendered)
            self.assertIn('data-chart="valuation-scenarios"', rendered)
            self.assertIn("<pre><code", rendered)
            self.assertIn("营业收入（亿元）", rendered)
            self.assertEqual(source.read_bytes(), before)

    @unittest.skipUnless(HAS_MARKDOWN, "optional markdown package required")
    def test_cli_partial_manifest_does_not_claim_complete_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output, manifest = Path(directory)/"source.md", Path(directory)/"out.html", Path(directory)/"evidence.json"
            source.write_text(SAMPLE_REPORT)
            manifest.write_text(json.dumps({"summary": {"captured": 2, "expected": 15, "failed": 0}, "groups": [{"source_id": "S01", "items": []}]}))
            before = (source.read_bytes(), manifest.read_bytes())
            result = subprocess.run([sys.executable, str(SCRIPT_DIR/"report_renderer.py"), "--source", str(source), "--output-html", str(output), "--html-only", "--evidence-manifest", str(manifest)], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr+result.stdout)
            self.assertTrue(json.loads(result.stdout)["valid"])
            rendered = output.read_text()
            self.assertIn("清单计数 2/15，失败 0", rendered)
            self.assertNotIn("2/15，完整", rendered)
            self.assertNotIn("组已捕获", rendered)
            self.assertEqual((source.read_bytes(), manifest.read_bytes()), before)

    def test_evidence_counts_never_claim_quality_or_completeness(self):
        for captured, expected in ((0, 15), (2, 15), (15, 15), (0, 0)):
            summary = report_renderer.evidence_summary({"summary": {"captured": captured, "expected": expected, "failed": 0}})
            self.assertIn(f"{captured}/{expected}", summary)
            self.assertIn("清单", summary)
            self.assertNotIn("完整", summary)
        for value in ("bad", True, -1, 1.2, [], None):
            with self.subTest(value=value):
                summary = report_renderer.evidence_summary({"summary": {"captured": value, "expected": 15, "failed": 0}})
                self.assertIn("不可用", summary)
        self.assertIn("不可用", report_renderer.evidence_summary({"summary": {"captured": 20, "expected": 15, "failed": 0}}))
        self.assertIn("不可用", report_renderer.evidence_summary({"summary": {"captured": 0, "captured_urls": 15, "expected": 15}}))
        self.assertIn("未提供", report_renderer.evidence_summary({"summary": {"captured": 2, "expected": 15}}))

    def test_empty_evidence_group_is_only_registered_not_captured(self):
        chart = report_renderer.evidence_coverage_chart({"groups": [{"source_id": "S01", "items": []}]})
        self.assertIn("0 项", chart)
        self.assertIn("清单登记", chart)
        self.assertNotIn("已捕获", chart)
        self.assertIn("不代表", chart)
        self.assertIn("条目数未提供", report_renderer.evidence_coverage_chart({"groups": [{"source_id": "S01"}]}))

    @unittest.skipUnless(HAS_MARKDOWN, "optional markdown package required")
    def test_cli_descending_years_keep_forward_growth_and_source(self):
        before, rest = EXTENDED_REPORT.split("## 财务趋势\n", 1)
        table, after = rest.split("## 最近一期变化", 1)
        lines = []
        for line in table.splitlines():
            if line.startswith("|"):
                cells = report_renderer.split_table_row(line)
                line = "| " + " | ".join((cells[0], *reversed(cells[1:]))) + " |"
            lines.append(line)
        content = before + "## 财务趋势\n" + "\n".join(lines) + "\n## 最近一期变化" + after
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory)/"source.md", Path(directory)/"out.html"
            source.write_text(content)
            snapshot = source.read_bytes()
            result = subprocess.run([sys.executable, str(SCRIPT_DIR/"report_renderer.py"), "--source", str(source), "--output-html", str(output), "--html-only"], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr+result.stdout)
            self.assertTrue(json.loads(result.stdout)["valid"])
            rendered = output.read_text()
            canonical = report_renderer.financial_trend_table(report_renderer.parse_markdown_tables(EXTENDED_REPORT))
            self.assertIn(report_renderer.financial_chart(canonical), rendered)
            self.assertIn(report_renderer.cash_flow_structure_chart(canonical), rendered)
            self.assertEqual(source.read_bytes(), snapshot)

    def test_financial_year_order_is_chronological_and_duplicates_rejected(self):
        canonical = report_renderer.MarkdownTable(("指标", "2023", "2024", "2025"), (("营业收入（亿元）", "10", "20", "30"), ("经营现金流（亿元）", "4", "5", "6"), ("资本开支代理项（亿元）", "1", "2", "3")))
        for order in ((0,3,2,1), (0,2,1,3)):
            permuted = report_renderer.MarkdownTable(tuple(canonical.headers[i] for i in order), tuple(tuple(row[i] for i in order) for row in canonical.rows))
            self.assertEqual(report_renderer.financial_chart(permuted), report_renderer.financial_chart(canonical))
            self.assertEqual(report_renderer.cash_flow_structure_chart(permuted), report_renderer.cash_flow_structure_chart(canonical))
        duplicate = report_renderer.MarkdownTable(("指标", "2023", "2023", "2025"), canonical.rows)
        self.assertEqual(report_renderer.financial_chart(duplicate), "")
        self.assertIsNone(report_renderer.cash_flow_structure_chart(duplicate))

    def test_year_identity_uses_numeric_value_across_digit_forms(self):
        rows = (("营业收入（亿元）", "1", "2", "3"), ("经营现金流（亿元）", "4", "5", "6"), ("资本开支代理项（亿元）", "1", "1", "1"))
        duplicate = report_renderer.MarkdownTable(("指标", "2023", "20２３", "20٢٣"), rows)
        self.assertEqual(report_renderer.chronological_year_indices(duplicate), [])
        self.assertEqual(report_renderer.financial_chart(duplicate), "")
        self.assertIsNone(report_renderer.cash_flow_structure_chart(duplicate))
        mixed = report_renderer.MarkdownTable(("指标", "2023", "2025", "20２４"), rows)
        self.assertEqual(report_renderer.chronological_year_indices(mixed), [1,3,2])
        self.assertIn("<svg", report_renderer.financial_chart(mixed))
        self.assertIn("<svg", report_renderer.cash_flow_structure_chart(mixed))

    def test_financial_year_gaps_use_elapsed_year_coordinates(self):
        table = report_renderer.MarkdownTable(("指标", "2020", "2021", "2025"), (("营业收入（亿元）", "10", "20", "30"), ("经营现金流（亿元）", "4", "5", "6"), ("资本开支代理项（亿元）", "1", "2", "3")))
        for chart in (report_renderer.financial_chart(table), report_renderer.cash_flow_structure_chart(table)):
            points = re.search(r'<polyline points="([^"]+)"', chart).group(1).split()
            xs = [float(point.split(",")[0]) for point in points]
            self.assertAlmostEqual((xs[1]-xs[0])/(xs[2]-xs[0]), .2, places=3)

    @unittest.skipUnless(HAS_MARKDOWN, "optional markdown package required")
    def test_cli_nonmonetary_financial_rows_remain_table_only(self):
        content = EXTENDED_REPORT.replace("（亿元）", "（%）")
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory)/"source.md", Path(directory)/"out.html"
            source.write_text(content)
            before = source.read_bytes()
            result = subprocess.run([sys.executable, str(SCRIPT_DIR/"report_renderer.py"), "--source", str(source), "--output-html", str(output), "--html-only"], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr+result.stdout)
            self.assertTrue(json.loads(result.stdout)["valid"])
            rendered = output.read_text()
            for name in ("financial-trends", "cash-flow-structure"):
                self.assertNotIn(f'data-chart="{name}"', rendered)
            self.assertIn("经营现金流（%）", rendered)
            self.assertIn('data-chart="valuation-scenarios"', rendered)
            self.assertEqual(source.read_bytes(), before)

    def test_financial_charts_require_monetary_row_units(self):
        for suffix in ("", "（%）", "（元/股）", "（百分点）", "（未知）"):
            with self.subTest(suffix=suffix):
                table = report_renderer.MarkdownTable(("指标", "2023", "2024", "2025"), (("营业收入"+suffix, "1", "2", "3"), ("经营现金流"+suffix, "4", "5", "6"), ("资本开支代理项"+suffix, "1", "1", "1")))
                self.assertEqual(report_renderer.financial_chart(table), "")
                self.assertIsNone(report_renderer.cash_flow_structure_chart(table))
        for unit in ("亿元", "万美元", "港元"):
            with self.subTest(unit=unit):
                table = report_renderer.MarkdownTable(("指标", "2023", "2024", "2025"), ((f"经营现金流（{unit}）", "4", "5", "6"), (f"资本开支代理项（{unit}）", "1", "1", "1")))
                self.assertIn(f"经营现金流（{unit}）", report_renderer.financial_chart(table))
                self.assertIn(f"{unit} · FCF", report_renderer.cash_flow_structure_chart(table))

    def test_financial_header_and_row_unit_conflict_rejects_charts(self):
        table = report_renderer.MarkdownTable(("指标（万元）", "2023", "2024", "2025"), (("经营现金流（亿元）", "4", "5", "6"), ("资本开支代理项（亿元）", "1", "1", "1")))
        self.assertEqual(report_renderer.financial_chart(table), "")
        self.assertIsNone(report_renderer.cash_flow_structure_chart(table))

    def test_yoy_chart_requires_percentage_units(self):
        for header, cells in (("同比（百分点）", ("2", "3")), ("同比（亿元）", ("2", "3")), ("同比增加额", ("2%", "3%")), ("同比", ("2", "3")), ("同比（bp）", ("2%", "3%"))):
            with self.subTest(header=header):
                table = report_renderer.MarkdownTable(("指标", header), (("营业收入", cells[0]), ("归母净利润", cells[1])))
                self.assertIsNone(report_renderer.yoy_change_table([table]))
                self.assertIsNone(report_renderer.earnings_quality_chart(table, 1))
        for header, cells in (("同比", ("2%", "-3%")), ("同比（%）", ("2", "-3")), ("同比增长率（%）", ("2%", "-3"))):
            with self.subTest(header=header):
                table = report_renderer.MarkdownTable(("指标", header), (("营业收入", cells[0]), ("归母净利润", cells[1])))
                self.assertIsNotNone(report_renderer.yoy_change_table([table]))
                chart = report_renderer.earnings_quality_chart(table, 1)
                self.assertIn("+2.00%", chart)
                self.assertIn("−3.00%", chart)
                # A numeric table alone cannot establish the provenance of its
                # percentages (reported, calculated, or hypothetical).
                self.assertNotIn("OBSERVED", chart)
                self.assertNotIn("INFERRED", chart)
                self.assertIn("证据状态、口径与计算见正文", chart)

    @unittest.skipUnless(HAS_MARKDOWN, "optional markdown package required")
    def test_cli_percentage_point_table_is_not_a_percentage_chart(self):
        content = EXTENDED_REPORT.replace("| 同比 |", "| 同比（百分点） |").replace("+9.50%", "9.5").replace("-12.30%", "-12.3").replace("-11.20%", "-11.2")
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory)/"source.md", Path(directory)/"out.html"
            source.write_text(content)
            before = source.read_bytes()
            result = subprocess.run([sys.executable, str(SCRIPT_DIR/"report_renderer.py"), "--source", str(source), "--output-html", str(output), "--html-only"], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr+result.stdout)
            self.assertTrue(json.loads(result.stdout)["valid"])
            rendered = output.read_text()
            self.assertNotIn('data-chart="earnings-quality"', rendered)
            self.assertIn("同比（百分点）", rendered)
            self.assertIn('data-chart="financial-trends"', rendered)
            self.assertEqual(source.read_bytes(), before)

    def test_scenario_units_must_establish_yuan_per_share(self):
        for header in ("目标价（美元）", "目标价（港元）", "目标价 USD", "企业价值（亿元）", "总价值（元）", "示意价值", "每股价值（元/股，美元）"):
            with self.subTest(header=header):
                table = report_renderer.MarkdownTable(("情景", header), (("Bear", "10"), ("Base", "20"), ("Bull", "30")))
                self.assertEqual(report_renderer.scenario_chart(table, None), "")
        for header, suffix in (("目标价（元/股）", ""), ("每股价值（元）", ""), ("示意价值", " 元"), ("每股合理价值（人民币元/股）", " 元/股")):
            with self.subTest(header=header):
                table = report_renderer.MarkdownTable(("情景", header), tuple((label, str(value)+suffix) for label, value in (("Bear",10),("Base",20),("Bull",30))))
                self.assertIn('data-chart="valuation-scenarios"', report_renderer.scenario_chart(table, None))

    def test_mixed_unit_scenario_cannot_be_silently_dropped(self):
        table = report_renderer.MarkdownTable(("情景", "目标价（元/股）"), (("Bear", "10"), ("Base", "20"), ("Bull", "30"), ("乐观", "40 美元")))
        self.assertEqual(report_renderer.scenario_chart(table, None), "")

    @unittest.skipUnless(HAS_MARKDOWN, "optional markdown package required")
    def test_cli_foreign_currency_scenarios_remain_table_only(self):
        content = SAMPLE_REPORT.replace("示意价值", "目标价（美元）").replace("60.50 元", "60.50").replace("85.26 元", "85.26").replace("110.50 元", "110.50")
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory)/"source.md", Path(directory)/"out.html"
            source.write_text(content)
            before = source.read_bytes()
            result = subprocess.run([sys.executable, str(SCRIPT_DIR/"report_renderer.py"), "--source", str(source), "--output-html", str(output), "--html-only"], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr+result.stdout)
            self.assertTrue(json.loads(result.stdout)["valid"])
            rendered = output.read_text()
            self.assertNotIn('data-chart="valuation-scenarios"', rendered)
            self.assertIn("目标价（美元）", rendered)
            self.assertIn('data-chart="financial-trends"', rendered)
            self.assertEqual(source.read_bytes(), before)

    @unittest.skipUnless(HAS_MARKDOWN, "optional markdown package required")
    def test_cli_tiny_prices_and_zero_bars_keep_their_meaning(self):
        from xml.etree import ElementTree as ET
        content = SAMPLE_REPORT.replace("84.30 元", "0.0001 元").replace("60.50 元", "0 元").replace("85.26 元", "0.0001 元")
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "source.md", Path(directory) / "out.html"
            source.write_text(content)
            before = source.read_bytes()
            result = subprocess.run([sys.executable, str(SCRIPT_DIR / "report_renderer.py"), "--source", str(source), "--output-html", str(output), "--html-only"], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertTrue(json.loads(result.stdout)["valid"])
            rendered = output.read_text()
            scenario = re.search(r'<figure[^>]*data-chart="valuation-scenarios".*?</figure>', rendered, re.S).group()
            svg = ET.fromstring(re.search(r"<svg.*?</svg>", scenario, re.S).group())
            self.assertEqual(float(svg.findall("rect")[0].attrib["width"]), 0)
            self.assertGreater(float(svg.findall("rect")[1].attrib["width"]), 0)
            self.assertIn("截止日 1.000e−04", scenario)
            self.assertIn("Base 1.000e−04 元", scenario)
            self.assertEqual(source.read_bytes(), before)

    def test_chart_labels_preserve_nonzero_magnitude_and_bound_large_text(self):
        for value in (0.0001, -0.0001, 5e-324, -5e-324, 1e300):
            with self.subTest(value=value):
                label = report_renderer.format_value(value).replace("−", "-")
                self.assertNotEqual(float(label.replace(",", "")), 0)
                self.assertLess(len(label), 32)
                percent = report_renderer.format_percent(value).replace("−", "-").removesuffix("%")
                self.assertNotEqual(float(percent), 0)
                self.assertLess(len(percent), 32)
        self.assertEqual(report_renderer.format_value(-0.0), "0")
        self.assertEqual(report_renderer.format_percent(-0.0), "+0.00%")

    def test_zero_bars_have_zero_width_and_tiny_prices_remain_nonzero(self):
        from xml.etree import ElementTree as ET
        scenario = report_renderer.MarkdownTable(("情景", "示意价值（元/股）"), (("Bear", "0"), ("Base", "0.0001"), ("Bull", "1")))
        quality = report_renderer.MarkdownTable(("指标", "同比"), (("营业收入", "0%"), ("净利润", "0.0001%")))
        for chart in (report_renderer.scenario_chart(scenario, .0001), report_renderer.earnings_quality_chart(quality, 1)):
            svg = ET.fromstring(re.search(r"<svg.*?</svg>", chart, re.S).group())
            bars = svg.findall("rect")
            self.assertEqual(float(bars[0].attrib["width"]), 0)
            self.assertGreater(float(bars[1].attrib["width"]), 0)
        self.assertIn("1.000e−04", report_renderer.scenario_chart(scenario, .0001))
        self.assertLess(float(ET.fromstring(re.search(r"<svg.*?</svg>", report_renderer.scenario_chart(scenario, None), re.S).group()).findall("rect")[1].attrib["width"]), .5)

    @unittest.skipUnless(HAS_MARKDOWN, "optional markdown package required")
    def test_cli_extreme_tables_do_not_publish_nonfinite_charts(self):
        content = EXTENDED_REPORT.replace("| 100 | 110 | 120 | 130 | 150 |", "| -1e308 | 0 | 0 | 0 | 1e308 |")
        content = content.replace("| 8 | 13 | 9 | 16 | 14 |", "| 1e308 | 13 | 9 | 16 | 14 |").replace("| 5 | 7 | 6 | 9 | 10 |", "| -1e308 | 7 | 6 | 9 | 10 |")
        content = content.replace("60.50 元", "-1e308 元").replace("110.50 元", "1e308 元").replace("+9.50%", "-1e308%").replace("-12.30%", "1e308%")
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "source.md", Path(directory) / "out.html"
            source.write_text(content)
            before = source.read_bytes()
            result = subprocess.run([sys.executable, str(SCRIPT_DIR / "report_renderer.py"), "--source", str(source), "--output-html", str(output), "--html-only"], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertTrue(json.loads(result.stdout)["valid"])
            rendered = output.read_text()
            for name in ("financial-trends", "cash-flow-structure", "valuation-scenarios", "earnings-quality"):
                self.assertNotIn(f'data-chart="{name}"', rendered)
            self.assertIn("1e308", rendered)
            self.assertEqual(source.read_bytes(), before)

    def test_chart_overflow_omits_unrepresentable_axes_and_derivations(self):
        trend = report_renderer.MarkdownTable(("指标", "2023", "2024", "2025"), (("营业收入（亿元）", "-1e308", "0", "1e308"),))
        self.assertEqual(report_renderer.financial_chart(trend), "")
        scenarios = report_renderer.MarkdownTable(("情景", "示意价值（元/股）"), (("Bear", "-1e308"), ("Base", "0"), ("Bull", "1e308")))
        self.assertEqual(report_renderer.scenario_chart(scenarios, None), "")
        quality = report_renderer.MarkdownTable(("指标", "同比"), (("营业收入", "-1e308%"), ("净利润", "1e308%")))
        self.assertIsNone(report_renderer.earnings_quality_chart(quality, 1))
        cash = report_renderer.MarkdownTable(("指标", "2023", "2024", "2025"), (("经营现金流（亿元）", "1e308", "1", "2"), ("资本开支代理项（亿元）", "-1e308", "1", "2")))
        self.assertIsNone(report_renderer.cash_flow_structure_chart(cash))

    def test_representable_large_axes_keep_finite_svg_coordinates(self):
        scenarios = report_renderer.MarkdownTable(("情景", "示意价值（元/股）"), (("Bear", "1e306"), ("Base", "2e306"), ("Bull", "3e306")))
        quality = report_renderer.MarkdownTable(("指标", "同比"), (("营业收入", "-1e306%"), ("净利润", "1e306%")))
        for chart in (report_renderer.scenario_chart(scenarios, 2e306), report_renderer.earnings_quality_chart(quality, 1)):
            self.assertIn("<svg", chart)
            self.assertNotRegex(chart, r"(?i)\b(?:nan|inf)\b")

    def test_unrepresentable_trend_change_is_explicit_not_infinite(self):
        table = report_renderer.MarkdownTable(("指标", "2023", "2024", "2025"), (("营业收入（亿元）", "1e-300", "1", "1e300"),))
        chart = report_renderer.financial_chart(table)
        self.assertIn("变化率超出数值范围", chart)
        self.assertNotRegex(chart, r"(?i)\b(?:nan|inf)\b")

    @unittest.skipUnless(HAS_MARKDOWN, "optional markdown package required")
    def test_cli_preserves_ambiguous_table_without_inventing_trend(self):
        content = SAMPLE_REPORT.replace("| 100 |", "| 10–20 |").replace("| 10 |", "| 未披露 [S01] |").replace("| 8 |", "| (12.5) |")
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "source.md", Path(directory) / "out.html"
            source.write_text(content)
            before = source.read_bytes()
            result = subprocess.run([sys.executable, str(SCRIPT_DIR / "report_renderer.py"), "--source", str(source), "--output-html", str(output), "--html-only"], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertTrue(json.loads(result.stdout)["valid"])
            rendered = output.read_text()
            self.assertNotIn('data-chart="financial-trends"', rendered)
            self.assertIn('data-chart="valuation-scenarios"', rendered)
            self.assertIn("10–20", rendered)
            self.assertIn("未披露", rendered)
            self.assertIn("(12.5)", rendered)
            self.assertEqual(source.read_bytes(), before)

    def test_chart_numbers_require_complete_unambiguous_scalars(self):
        for raw in ("10–20", "10-20", "未披露 [S01]", "(12.5)", "约 10", ">10", "1,2", "12万元", "12%", "1e309", "1e-999", "1e-99999999999999999999", "9" * 400):
            with self.subTest(raw=raw):
                self.assertIsNone(report_renderer.numeric_value(raw))
        for raw, expected in (("0", 0), ("−12.5", -12.5), (".5", .5), ("1,234.50", 1234.5), ("**12.5**", 12.5), ("1e2", 100)):
            with self.subTest(raw=raw):
                self.assertEqual(report_renderer.numeric_value(raw), expected)

    def test_ambiguous_cells_cannot_supply_chart_values(self):
        for raw in ("10–20", "未披露 [S01]", "(12.5)", "12万元", "12%", "1e309"):
            with self.subTest(raw=raw):
                table = report_renderer.MarkdownTable(("指标", "2023", "2024", "2025"), (("营业收入（亿元）", raw, "20", "30"),))
                self.assertEqual(report_renderer.financial_chart(table), "")
                scenarios = report_renderer.MarkdownTable(("情景", "示意价值"), (("Bear", raw), ("Base", "20 元"), ("Bull", "30 元")))
                self.assertEqual(report_renderer.scenario_chart(scenarios, None), "")
                quality = report_renderer.MarkdownTable(("指标", "同比"), (("营业收入", raw), ("归母净利润", "20%")))
                if raw != "12%":
                    self.assertIsNone(report_renderer.earnings_quality_chart(quality, 1))
                cash = report_renderer.MarkdownTable(("指标", "2023", "2024", "2025"), (("经营现金流（亿元）", raw, "20", "30"), ("资本开支代理项（亿元）", "1", "2", "3")))
                self.assertIsNone(report_renderer.cash_flow_structure_chart(cash))

    @unittest.skipUnless(HAS_MARKDOWN, "optional markdown package required")
    def test_cli_pdf_failure_preserves_prior_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output, pdf = root / "report.md", root / "report.html", root / "report.pdf"
            source.write_text(SAMPLE_REPORT)
            output.write_text("old html"); pdf.write_bytes(b"old pdf")
            before = {p.name: p.read_bytes() for p in root.iterdir()}
            script = r"""
import pathlib, sys
sys.path.insert(0, sys.argv[1])
import report_renderer
args = sys.argv[2:]
def failure(html, pdf):
    pdf.write_bytes(b'%PDF partial')
    raise report_renderer.ReportRenderError('injected PDF failure')
report_renderer.write_pdf = failure
sys.argv = ['report_renderer.py', *args]
raise SystemExit(report_renderer.main())
"""
            result = subprocess.run([sys.executable, "-c", script, str(SCRIPT_DIR), "--source", str(source),
                "--output-html", str(output), "--output-pdf", str(pdf)], capture_output=True, text=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(json.loads(result.stdout)["valid"])
            self.assertEqual(before, {p.name: p.read_bytes() for p in root.iterdir()})

    @unittest.skipUnless(HAS_MARKDOWN, "optional markdown package required")
    def test_render_generation_failure_preserves_existing_outputs(self):
        for failure in ("pdf", "source-drift"):
            for existing in (False, True):
                with self.subTest(failure=failure, existing=existing), tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    source, output, pdf = root / "report.md", root / "report.html", root / "report.pdf"
                    source.write_text(SAMPLE_REPORT)
                    if existing:
                        output.write_bytes(b"old html")
                        pdf.write_bytes(b"old pdf")
                    before = {p.name: p.read_bytes() for p in (output, pdf) if p.exists()}
                    def generate(html_path, pdf_path):
                        self.assertIn('<html', html_path.read_text())
                        pdf_path.write_bytes(b"%PDF partial")
                        if failure == "pdf": raise report_renderer.ReportRenderError("injected PDF failure")
                        source.write_text(SAMPLE_REPORT + "\nchanged externally\n")
                        return 1
                    with mock.patch.object(report_renderer, "write_pdf", side_effect=generate):
                        with self.assertRaises(report_renderer.ReportRenderError):
                            report_renderer.render_report(source, output_html=output, output_pdf=pdf)
                    self.assertEqual(before, {p.name: p.read_bytes() for p in (output, pdf) if p.exists()})
                    self.assertEqual(set(p.name for p in root.iterdir()), {"report.md", *before})

    @unittest.skipUnless(HAS_MARKDOWN, "optional markdown package required")
    def test_successful_staged_render_publishes_both_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "report.md"
            source.write_text(SAMPLE_REPORT)
            output, pdf = root / "html/report.html", root / "pdf/report.pdf"
            output.parent.mkdir(); pdf.parent.mkdir()
            output.write_bytes(b"old html"); pdf.write_bytes(b"old pdf")
            def generate(html_path, pdf_path):
                self.assertNotEqual(html_path, output)
                self.assertNotEqual(pdf_path, pdf)
                self.assertEqual(output.read_bytes(), b"old html")
                self.assertEqual(pdf.read_bytes(), b"old pdf")
                pdf_path.write_bytes(b"%PDF fixture")
                return 1
            with mock.patch.object(report_renderer, "write_pdf", side_effect=generate):
                result = report_renderer.render_report(source, output_html=output, output_pdf=pdf)
            self.assertTrue(result["valid"])
            self.assertEqual(result["pages"], 1)
            self.assertEqual(pdf.read_bytes(), b"%PDF fixture")
            self.assertTrue(report_renderer.verify_rendered_report(source, output, None)["valid"])
            self.assertEqual([p.name for p in output.parent.iterdir()], ["report.html"])
            self.assertEqual([p.name for p in pdf.parent.iterdir()], ["report.pdf"])


    @unittest.skipUnless(HAS_MARKDOWN, "optional markdown package required")
    def test_documented_local_evidence_source_index_renders_portably(self):
        # report-rendering.md: local evidence as a bare path renders; a relative Markdown link does not.
        guidance = (ROOT / "skills/money-craft/references/report-rendering.md").read_text(encoding="utf-8")
        self.assertIn("`- [S11] evidence/S11-official.pdf`", guidance)
        for line, portable in (("- [S01] evidence/S01-official.pdf", True),
                               ("- [S01] `evidence/S01-official.pdf`", True),
                               ("- [S01] [年报](evidence/S01-official.pdf)", False)):
            with self.subTest(line=line), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source = root / "report.md"
                source.write_text(SAMPLE_REPORT.replace("- [S01] https://example.invalid/report.pdf", line))
                output, pdf = root / "report.html", root / "report.pdf"
                def generate(_html_path, pdf_path):
                    pdf_path.write_bytes(b"%PDF fixture")
                    return 1
                with mock.patch.object(report_renderer, "write_pdf", side_effect=generate):
                    if portable:
                        self.assertTrue(report_renderer.render_report(source, output_html=output, output_pdf=pdf)["valid"])
                    else:
                        with self.assertRaises(Exception):
                            report_renderer.render_report(source, output_html=output, output_pdf=pdf)

    @unittest.skipUnless(HAS_MARKDOWN, "optional markdown package required")
    def test_markdown_body_rejects_active_html(self):
        fragments = ('<script>alert(1)</script>', '<![CDATA[><script>alert(1)</script>]]>', '<img src="x" onerror="alert(1)">',
            '<iframe srcdoc="&lt;script&gt;alert(1)&lt;/script&gt;"></iframe>', '<meta http-equiv="refresh" content="0;url=https://example.invalid">',
            '<style>@import "https://example.invalid/style.css";</style>', '<span style="background:url(https://example.invalid/x)">x</span>',
            '<form><input name="x"></form>', '<svg onload="alert(1)"></svg>', '<math></math>', '</article><p>escape</p>',
            '<a href="#ok" ONCLICK="alert(1)">x</a>', '<div data-theme-toggle="true">x</div>')
        for fragment in fragments:
            with self.subTest(fragment=fragment):
                with self.assertRaises(report_renderer.ReportRenderError):
                    report_renderer.markdown_to_html(fragment)
        safe = report_renderer.markdown_to_html('## 标题\n\n| 项目 | 数值 |\n|---|---:|\n| A | 1 |\n\n```html\n<script>alert(1)</script>\n```')
        self.assertIn('<table>', safe)
        self.assertIn('&lt;script&gt;', safe)

    @unittest.skipUnless(HAS_MARKDOWN, "optional markdown package required")
    def test_active_body_cli_rejection_preserves_previous_output(self):
        for fragment in ('<script>document.title="changed";</script>', '<![CDATA[><script>alert(1)</script>]]>'):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source, output = root / "report.md", root / "report.html"
                source.write_text(SAMPLE_REPORT + "\n" + fragment + "\n")
                output.write_text("preserve prior render")
                before = {p.name: p.read_bytes() for p in root.iterdir()}
                result = subprocess.run([sys.executable, str(SCRIPT_DIR / "report_renderer.py"), "--source", str(source),
                    "--output-html", str(output), "--html-only"], capture_output=True, text=True, timeout=10)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(json.loads(result.stdout)["valid"])
                self.assertEqual(before, {p.name: p.read_bytes() for p in root.iterdir()})


    def test_template_values_cannot_expand_other_template_fields(self):
        for values in ({"TITLE": "{{ARTICLE}}", "ARTICLE": "unexpected expansion"},
                       {"ARTICLE": "unexpected expansion", "TITLE": "{{ARTICLE}}"}):
            with self.subTest(order=list(values)):
                with self.assertRaises(report_renderer.ReportRenderError):
                    report_renderer.replace_template("<title>{{TITLE}}</title>", values)
        self.assertEqual(report_renderer.replace_template("{{TITLE}} / {{TITLE}}", {"TITLE": "Plain text"}), "Plain text / Plain text")
        with self.assertRaises(report_renderer.ReportRenderError):
            report_renderer.replace_template("{{UNKNOWN}}", {"TITLE": "Plain text"})

    @unittest.skipUnless(HAS_MARKDOWN, "optional markdown package required")
    def test_source_template_marker_rejected_before_output_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output = root / "report.md", root / "report.html"
            source.write_text(SAMPLE_REPORT + "\n## 附注\n\n{{FOOTER_META}}\n")
            output.write_text("preserve previous render")
            before = {p.name: p.read_bytes() for p in root.iterdir()}
            result = subprocess.run([sys.executable, str(SCRIPT_DIR / "report_renderer.py"), "--source", str(source),
                "--output-html", str(output), "--html-only"], capture_output=True, text=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(json.loads(result.stdout)["valid"])
            self.assertEqual(before, {p.name: p.read_bytes() for p in root.iterdir()})


    @unittest.skipUnless(HAS_MARKDOWN, "optional markdown package required")
    def test_render_cli_protects_source_and_allows_separate_html(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "report.md"
            source.write_text(SAMPLE_REPORT)
            original = source.read_bytes()
            script = str(SCRIPT_DIR / "report_renderer.py")
            collision = subprocess.run([sys.executable, script, "--source", str(source), "--output-html", str(source), "--html-only"], capture_output=True, text=True, timeout=10)
            self.assertNotEqual(collision.returncode, 0)
            self.assertFalse(json.loads(collision.stdout)["valid"])
            self.assertEqual(source.read_bytes(), original)
            output = Path(directory) / "report.html"
            rendered = subprocess.run([sys.executable, script, "--source", str(source), "--output-html", str(output), "--html-only"], capture_output=True, text=True, timeout=10)
            self.assertEqual(rendered.returncode, 0, rendered.stdout + rendered.stderr)
            self.assertTrue(json.loads(rendered.stdout)["valid"])
            self.assertEqual(source.read_bytes(), original)
            self.assertTrue(report_renderer.verify_rendered_report(source, output, None)["valid"])

    @unittest.skipUnless(HAS_MARKDOWN, "optional markdown package required")
    def test_output_aliases_are_rejected_before_any_input_is_modified(self):
        variants = ("source", "source-symlink", "source-hardlink", "template", "style", "script",
                    "evidence", "audit", "revision", "archive", "pdf-source", "same-outputs", "hardlinked-outputs")
        for variant in variants:
            with self.subTest(variant=variant), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source = root / "report.md"
                source.write_text(SAMPLE_REPORT)
                inputs = {"source": source}
                for key, original in (("template", report_renderer.DEFAULT_TEMPLATE), ("style", report_renderer.DEFAULT_STYLE), ("script", report_renderer.DEFAULT_SCRIPT)):
                    inputs[key] = root / original.name
                    inputs[key].write_bytes(original.read_bytes())
                for key in ("evidence", "audit", "revision", "archive"):
                    inputs[key] = root / (key + ".json")
                    inputs[key].write_text("{}")
                output_html, output_pdf = root / "output.html", None
                if variant in inputs: output_html = inputs[variant]
                elif variant == "source-symlink": output_html.symlink_to(source)
                elif variant == "source-hardlink": os.link(source, output_html)
                elif variant == "pdf-source": output_pdf = source
                elif variant == "same-outputs": output_pdf = output_html
                elif variant == "hardlinked-outputs":
                    output_html.write_bytes(b"existing output")
                    output_pdf = root / "output.pdf"
                    os.link(output_html, output_pdf)
                before = {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}
                def pdf_writer(_html, pdf):
                    pdf.write_bytes(b"%PDF fixture")
                    return 1
                with mock.patch.object(report_renderer, "write_pdf", side_effect=pdf_writer):
                    with self.assertRaises(report_renderer.ReportRenderError):
                        report_renderer.render_report(source, output_html=output_html, output_pdf=output_pdf,
                            template_path=inputs["template"], style_path=inputs["style"], script_path=inputs["script"],
                            evidence_manifest=inputs["evidence"], audit_path=inputs["audit"],
                            revision_manifest=inputs["revision"], archive_manifest=inputs["archive"])
                self.assertEqual(before, {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()})


    def test_canonical_frontmatter_dates_survive_rendering(self) -> None:
        source = (ROOT / 'artifacts/acceptance/600519/report.md').read_text(encoding='utf-8')
        parsed = report_renderer.parse_report(source)
        self.assertEqual(parsed.metadata['as_of'], '2026-08-23')
        self.assertEqual(report_renderer.report_date(parsed), '2026-08-23')
        self.assertEqual(report_renderer.data_cutoff(parsed), '2026-08-23T19:40:16+08:00')
        masthead = report_renderer.build_masthead(parsed, None)
        result = report_renderer.verify_html_text(masthead, expected_report=parsed)
        self.assertFalse(any('data-report-date' in e or 'data-data-cutoff' in e for e in result['errors']))
        broken = masthead.replace('2026-08-23', 'UNSPECIFIED')
        errors = report_renderer.verify_html_text(broken, expected_report=parsed)['errors']
        self.assertTrue(any('data-report-date' in e for e in errors))
        self.assertTrue(any('data-data-cutoff' in e for e in errors))

    def test_thousands_price_and_ttm_pe_keep_the_disclosed_basis(self) -> None:
        source = (ROOT / 'artifacts/acceptance/600519/report.md').read_text(encoding='utf-8')
        parsed = report_renderer.parse_report(source)
        self.assertEqual(report_renderer.current_price(parsed), 1272.83)
        self.assertEqual(report_renderer.metric_items(parsed)[1]['label'], 'PE · TTM')
        self.assertEqual(report_renderer.metric_items(parsed)[1]['value'], '19.539×')
        brief = report_renderer.build_decision_brief(parsed)
        self.assertNotIn('待复核', brief)
        self.assertNotIn('见正文', brief)
        self.assertNotIn('静态 PE', brief)

    def test_year_rows_and_year_columns_produce_equivalent_trends(self) -> None:
        table = report_renderer.MarkdownTable(
            headers=('年度', '营业收入（亿元）', '归母净利润（亿元）'),
            rows=(('2023', '100', '10'), ('2024', '110', '12'), ('2025', '120', '11')),
        )
        normalized = report_renderer.financial_trend_table([table])
        expected = report_renderer.MarkdownTable(
            headers=('指标', '2023', '2024', '2025'),
            rows=(('营业收入（亿元）', '100', '110', '120'), ('归母净利润（亿元）', '10', '12', '11')),
        )
        self.assertEqual(normalized, expected)
        self.assertEqual(report_renderer.financial_chart(normalized), report_renderer.financial_chart(expected))

    @unittest.skipUnless(HAS_MARKDOWN, "optional markdown package unavailable")
    def test_acceptance_reading_order_preserves_conclusion_and_citations_once(self) -> None:
        source = (ROOT / 'artifacts/acceptance/600519/report.md').read_text(encoding='utf-8')
        parsed = report_renderer.parse_report(source)
        document, chart_count = report_renderer.build_document(
            parsed, 'a' * 64, template=report_renderer.DEFAULT_TEMPLATE.read_text(encoding='utf-8'),
            style='', script='', audit=None, evidence=None, revision=None,
            archive_manifest=None, charts=True,
        )
        self.assertEqual(chart_count, 2)
        self.assertEqual(document.count('贵州茅台仍具备极强品牌'), 2)  # description + one visible paragraph
        article = document.split('<article class="report-article">', 1)[1].split('</article>', 1)[0]
        self.assertEqual(article.count('贵州茅台仍具备极强品牌'), 1)
        self.assertIn('[S08]', article.split('visual-summary', 1)[0])
        self.assertIn('data-chart="financial-trends"', article)
        self.assertIn('截止日 1272.83', article)
        self.assertNotIn('UNSPECIFIED', document)
        self.assertTrue(report_renderer.verify_html_text(document, expected_report=parsed)['valid'])

    def test_parse_removes_legacy_style_and_preamble(self) -> None:
        parsed = report_renderer.parse_report(SAMPLE_REPORT)
        self.assertEqual(parsed.title, "示例公司（600000.SH）基本面研究")
        self.assertNotIn("<style>", parsed.markdown_body)
        self.assertTrue(parsed.markdown_body.startswith("## 结论"))
        self.assertEqual(report_renderer.report_verdict(parsed), "WATCH")
        self.assertEqual(report_renderer.report_identity(parsed), "600000.SH")
        self.assertEqual(report_renderer.print_identity(parsed), "600000.SH · 2026-08-24")

    def test_metric_extraction_keeps_time_bounded_values(self) -> None:
        parsed = report_renderer.parse_report(SAMPLE_REPORT)
        metrics = report_renderer.metric_items(parsed)
        self.assertEqual(metrics[0]["value"], "84.30 元")
        self.assertEqual(metrics[1]["value"], "14.53×")
        self.assertEqual(metrics[2]["value"], "待复核")

    def test_financial_and_scenario_charts_are_deterministic_inline_svg(self) -> None:
        parsed = report_renderer.parse_report(SAMPLE_REPORT)
        tables = report_renderer.parse_markdown_tables(parsed.markdown_body)
        financial = report_renderer.financial_chart(report_renderer.financial_trend_table(tables))
        scenario = report_renderer.scenario_chart(
            report_renderer.scenario_table(tables), report_renderer.current_price(parsed)
        )
        self.assertIn("<svg", financial)
        self.assertIn("各指标独立量程", financial)
        self.assertIn('class="chart-ring ring-revenue"', financial)
        self.assertIn("归母净利润", financial)
        self.assertIn("经营现金流", financial)
        self.assertNotIn("基本每股收益", financial)
        self.assertNotIn("资本开支代理项", financial)
        self.assertIn("截止日 84.30", scenario)
        without_price = report_renderer.scenario_chart(report_renderer.scenario_table(tables), None)
        self.assertIn("未提供报告截止日价格", without_price)
        self.assertNotIn("虚线为报告截止日价格", without_price)
        self.assertNotIn("<script", financial + scenario)

        chinese = SAMPLE_REPORT.replace("| Bear |", "| 悲观 |").replace(
            "| Base |", "| 中性 |"
        ).replace("| Bull |", "| 乐观 |")
        chinese_tables = report_renderer.parse_markdown_tables(
            report_renderer.parse_report(chinese).markdown_body
        )
        self.assertIsNotNone(report_renderer.scenario_table(chinese_tables))

    def test_source_urls_remain_visible_but_not_navigable(self) -> None:
        rendered = report_renderer.decorate_text_nodes(
            '<p>[S01] https://example.invalid/report.pdf?a=1&amp;b=2</p>'
        )
        self.assertIn('class="source-ref"', rendered)
        self.assertIn('data-source-url="https://example.invalid/report.pdf?a=1&amp;b=2"', rendered)
        self.assertNotIn("&amp;amp;", rendered)
        self.assertNotIn('href="https://', rendered)

    def test_source_heading_receives_source_index_semantics(self) -> None:
        rendered, headings = report_renderer.decorate_headings(
            '<h2 id="sources">主要数据来源</h2><ul><li>[S01] source</li></ul>'
        )
        self.assertEqual(headings, [("sources", "主要数据来源")])
        self.assertIn('data-section-kind="sources"', rendered)

    def test_portability_checks_parsed_resource_attributes(self):
        shell = '<meta name="offline-portable" content="true"><meta name="generator" content="Money Craft"><nav></nav><main><article>{}</article></main>'
        for fragment in ('<img src=https://example.invalid/a.png>', '<img SRC="&#104;ttps://example.invalid/a.png">',
                         '<a href="java&#x73;cript:alert(1)">link</a>', '<img src="relative.png">',
                         '<img srcset="https://example.invalid/a.png 2x">', '<video poster="//example.invalid/a.png"></video>',
                         '<form action="https://example.invalid"></form>', '<object data=//example.invalid></object>',
                         '<svg><use xlink:href="https://example.invalid/a.svg#x"></use></svg>',
                         '<a href="#ok" ping="https://example.invalid">link</a>'):
            with self.subTest(fragment=fragment):
                result = report_renderer.verify_html_text(shell.format(fragment))
                self.assertFalse(result["valid"])
                self.assertGreater(result["external_dependency_count"], 0)
        safe = '<a href="#local">Local</a><span data-source-url="https://example.invalid">Source</span><code>&lt;img src=https://example.invalid&gt;</code>'
        self.assertTrue(report_renderer.verify_html_text(shell.format(safe))["valid"])
        embedded = '<img src="data:image/png;base64,aGVsbG8=">'
        self.assertTrue(report_renderer.verify_html_text(shell.format(embedded))["valid"])

    @unittest.skipUnless(HAS_MARKDOWN, "optional markdown package required")
    def test_render_cli_rejects_unquoted_external_resource_before_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output = root / "report.md", root / "report.html"
            source.write_text(SAMPLE_REPORT + "\n<img src=https://example.invalid/image.png>\n")
            output.write_text("preserve previous output")
            before = {p.name: p.read_bytes() for p in root.iterdir()}
            result = subprocess.run([sys.executable, str(SCRIPT_DIR / "report_renderer.py"), "--source", str(source),
                "--output-html", str(output), "--html-only"], capture_output=True, text=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(json.loads(result.stdout)["valid"])
            self.assertEqual(before, {p.name: p.read_bytes() for p in root.iterdir()})

    def test_portable_html_verifier_rejects_external_dependencies(self) -> None:
        source_hash = "a" * 64
        valid = (
            '<!doctype html><html><head><meta name="offline-portable" content="true">'
            '<meta name="generator" content="Money Craft">'
            f'<meta name="money-craft-source-sha256" content="{source_hash}"></head>'
            '<body><nav></nav><main><article><span data-source-url="https://example.invalid">'
            "source</span></article></main></body></html>"
        )
        self.assertTrue(report_renderer.verify_html_text(valid, source_sha256=source_hash)["valid"])
        invalid = valid.replace("<nav>", '<nav><a href="https://example.invalid">external</a>')
        result = report_renderer.verify_html_text(invalid, source_sha256=source_hash)
        self.assertFalse(result["valid"])
        self.assertEqual(result["external_dependency_count"], 1)

    def test_money_craft_cli_exposes_report_render_and_verify(self) -> None:
        parser = money_craft.build_parser()
        render = parser.parse_args(["report", "render", "--source", "report.md", "--html-only"])
        verify = parser.parse_args(
            ["report", "verify", "--source", "report.md", "--html", "report.html"]
        )
        self.assertEqual(render.report_command, "render")
        self.assertEqual(verify.report_command, "verify")

    def test_render_outputs_must_be_explicit(self) -> None:
        source = Path("/tmp/canonical/report.md")
        with self.assertRaises(report_renderer.ReportRenderError):
            report_renderer.resolve_output_paths(
                source,
                output_dir=None,
                output_html=None,
                output_pdf=None,
                html_only=False,
            )
        html_path, pdf_path = report_renderer.resolve_output_paths(
            source,
            output_dir=Path("/tmp/rendition"),
            output_html=None,
            output_pdf=None,
            html_only=False,
        )
        self.assertEqual(html_path, Path("/tmp/rendition/report.html").resolve())
        self.assertEqual(pdf_path, Path("/tmp/rendition/report.pdf").resolve())
        self.assertNotIn("kami", html_path.name.lower())
        self.assertNotIn("kami", pdf_path.name.lower())

    def test_current_theme_contract_is_editorial_publication(self) -> None:
        self.assertEqual(report_renderer.CANONICAL_THEME, "editorial-ivory")
        self.assertEqual(report_renderer.LAYOUT_MODE, "research-publication")

    def test_reading_typography_uses_full_column_cjk_and_no_shell_shadow(self) -> None:
        css = report_renderer.DEFAULT_STYLE.read_text(encoding="utf-8")
        self.assertNotIn("68ch", css)
        self.assertNotIn("--measure", css)
        self.assertIn("line-break: strict", css)
        self.assertIn("word-break: keep-all", css)
        self.assertNotIn("box-shadow: 0", css)
        self.assertNotIn("backdrop-filter", css)
        template = report_renderer.DEFAULT_TEMPLATE.read_text(encoding="utf-8")
        summary_at = template.index("{{VISUAL_SUMMARY}}")
        article_at = template.index("{{ARTICLE}}")
        lead_at = template.index("{{LEAD}}")
        extended_at = template.index("{{VISUAL_EXTENDED}}")
        self.assertLess(summary_at, article_at)
        self.assertLess(lead_at, summary_at)
        self.assertLess(article_at, extended_at)

    def test_audit_seal_uses_reader_chinese(self) -> None:
        parsed = report_renderer.parse_report(SAMPLE_REPORT)
        seal = report_renderer.build_audit_seal(
            "a" * 64,
            {"valid": True, "verdict": "PASS", "pass_count": 10, "total": 10},
            {"summary": {"captured": 15, "expected": 15, "failed": 0}},
            {"revision_id": "r0002", "offline_verifier": {"ok": True, "verified_offline": True}},
            None,
        )
        self.assertIn("报告审计", seal)
        self.assertIn("证据覆盖", seal)
        self.assertIn("离线核验", seal)
        self.assertIn("源文哈希", seal)
        self.assertIn("10/10 通过", seal)
        self.assertIn("清单计数 15/15，失败 0", seal)
        self.assertIn("通过", seal)
        self.assertNotIn("FAIL 0", seal)
        self.assertNotIn("Report audit", seal)
        self.assertIn("本阅读层绑定版本 r0002", seal)
        masthead = report_renderer.build_masthead(parsed, {"revision_id": "r0002"})
        self.assertIn('class="print-identity"', masthead)
        self.assertIn("600000.SH · 2026-08-24", masthead)

    def test_extended_charts_derive_only_from_disclosed_tables(self) -> None:
        parsed = report_renderer.parse_report(EXTENDED_REPORT)
        tables = report_renderer.parse_markdown_tables(parsed.markdown_body)

        found = report_renderer.yoy_change_table(tables)
        self.assertIsNotNone(found)
        quality_table, value_index = found
        quality = report_renderer.earnings_quality_chart(quality_table, value_index)
        self.assertIn("chart-yoy-pos", quality)
        self.assertIn("chart-yoy-neg", quality)
        self.assertIn("−12.30%", quality)
        self.assertNotIn("经营现金流", quality)  # 「持平」行不绘制

        primary = report_renderer.financial_chart(
            report_renderer.financial_trend_table(tables)
        )
        self.assertIn("营业收入", primary)
        self.assertIn("归母净利润", primary)
        self.assertIn("经营现金流", primary)
        self.assertNotIn("基本每股收益", primary)
        self.assertNotIn("资本开支代理项", primary)
        self.assertEqual(primary.count('class="chart-ring'), 3)

        cash_flow = report_renderer.cash_flow_structure_chart(
            report_renderer.financial_trend_table(tables)
        )
        self.assertIn("chart-fcf", cash_flow)
        self.assertIn("ring-fcf", cash_flow)
        self.assertIn("ring-operating-cash", cash_flow)
        self.assertIn("evidence-state", cash_flow)  # INFERRED 属性以状态徽章呈现
        self.assertIn("INFERRED", cash_flow)
        # FCF 代理 = 经营 − 开支：2025 年 14 - 10 = 4，必须出现在派生序列 title 中
        self.assertIn("FCF 代理 2025 4", cash_flow)
        self.assertIn('figure-meta">亿元 · FCF', cash_flow)
        self.assertNotIn("亿元 / 元", cash_flow)

        rows = report_renderer.falsification_rows(tables)
        self.assertEqual(
            rows,
            [("R01", "material", "WATCH"), ("R02", "fatal", "CLEAR"), ("R03", "material", "UNVERIFIED")],
        )
        falsification = report_renderer.falsification_status_chart(rows)
        self.assertIn('data-severity="fatal"', falsification)
        self.assertIn("WATCH 1 / CLEAR 1 / UNVERIFIED 1", falsification)

        evidence = {
            "groups": [
                {"source_id": "s02", "title": "公司公告", "items": [1]},
                {"source_id": "s01", "title": "年度报告", "items": [1, 2, 3]},
            ]
        }
        coverage = report_renderer.evidence_coverage_chart(evidence)
        self.assertLess(coverage.index("S01"), coverage.index("S02"))
        self.assertIsNone(report_renderer.evidence_coverage_chart(None))
        self.assertIsNone(report_renderer.evidence_coverage_chart({"groups": []}))

        # 缺输入时静默降级：基础样例无同比表、无资本开支行，相关图表不得生成
        bare_tables = report_renderer.parse_markdown_tables(
            report_renderer.parse_report(SAMPLE_REPORT).markdown_body
        )
        self.assertIsNone(report_renderer.yoy_change_table(bare_tables))
        self.assertIsNone(
            report_renderer.cash_flow_structure_chart(
                report_renderer.financial_trend_table(bare_tables)
            )
        )

    def test_cash_flow_derivation_requires_explicit_matching_units(self) -> None:
        for label in ("资本开支代理项（万元）", "资本开支代理项"):
            with self.subTest(label=label):
                source = EXTENDED_REPORT.replace("资本开支代理项（亿元）", label)
                tables = report_renderer.parse_markdown_tables(source)
                self.assertIsNone(report_renderer.cash_flow_structure_chart(
                    report_renderer.financial_trend_table(tables)
                ))

    @unittest.skipUnless(HAS_MARKDOWN, "optional markdown package unavailable")
    def test_build_document_splits_primary_and_extended_views(self) -> None:
        parsed = report_renderer.parse_report(EXTENDED_REPORT)
        document, chart_count = report_renderer.build_document(
            parsed,
            "a" * 64,
            template=report_renderer.DEFAULT_TEMPLATE.read_text(encoding="utf-8"),
            style="",
            script="",
            audit=None,
            evidence=None,
            revision=None,
            archive_manifest=None,
            charts=True,
        )
        self.assertEqual(chart_count, 5)  # 无 evidence manifest 时证据覆盖组件降级
        summary_start = document.index('<section class="visual-summary"')
        article_start = document.index('<article class="report-article"')
        extended_start = document.index('<section class="visual-extended"')
        main_start = document.index('<main id="report-content"')
        main_end = document.index("</main>")
        self.assertLess(main_start, summary_start)
        self.assertLess(article_start, summary_start)
        self.assertLess(article_start, extended_start)
        self.assertLess(extended_start, main_end)
        primary = document[summary_start:document.index('</section>', summary_start)]
        extended = document[extended_start:main_end]
        self.assertEqual(primary.count("<figure"), 2)
        self.assertIn("financial-trends", primary)
        self.assertIn("valuation-scenarios", primary)
        self.assertEqual(extended.count("<figure"), 3)

    @unittest.skipUnless(HAS_MARKDOWN, "optional markdown package unavailable")
    def test_primary_view_never_absorbs_extended_charts_when_trend_table_missing(self) -> None:
        # 缺财务趋势表时主视图降级为仅估值情景；扩展图表不得漂移进主视图
        head, rest = EXTENDED_REPORT.split("## 最近一期变化", 1)
        trendless_source = head.split("## 财务趋势")[0] + "## 最近一期变化" + rest
        parsed = report_renderer.parse_report(trendless_source)
        document, _ = report_renderer.build_document(
            parsed,
            "a" * 64,
            template=report_renderer.DEFAULT_TEMPLATE.read_text(encoding="utf-8"),
            style="",
            script="",
            audit=None,
            evidence=None,
            revision=None,
            archive_manifest=None,
            charts=True,
        )
        summary_start = document.index('<section class="visual-summary"')
        article_start = document.index('<article class="report-article"')
        extended_start = document.index('<section class="visual-extended"')
        primary = document[summary_start:document.index('</section>', summary_start)]
        extended = document[extended_start:]
        self.assertEqual(primary.count("<figure"), 1)
        self.assertIn('data-chart="valuation-scenarios"', primary)
        self.assertNotIn('data-chart="earnings-quality"', primary)
        self.assertIn('data-chart="earnings-quality"', extended)

    def test_chart_palette_tokens_match_css_contract(self) -> None:
        css = report_renderer.DEFAULT_STYLE.read_text(encoding="utf-8")

        def tokens(section: str) -> dict[str, str]:
            if section == "dark":
                start = css.index(':root[data-theme="dark"] {')
            elif section == "print":
                start = css.index("@media print {")
                start = css.index(":root,", start)
            else:
                start = css.index(":root {")
            block = css[start : css.index("}", start)]
            return dict(re.findall(r"(--chart-[a-z-]+):\s*(#[0-9A-Fa-f]{6})", block))

        light_expected = {
            "--chart-revenue": report_renderer.CHART_SERIES_LIGHT["revenue"],
            "--chart-net-profit": report_renderer.CHART_SERIES_LIGHT["net_profit"],
            "--chart-eps": report_renderer.CHART_SERIES_LIGHT["eps"],
            "--chart-operating-cash": report_renderer.CHART_SERIES_LIGHT["operating_cash"],
            "--chart-capex-proxy": report_renderer.CHART_SERIES_LIGHT["capex_proxy"],
            "--chart-scenario": report_renderer.SCENARIO_BAR_LIGHT,
            "--chart-up": report_renderer.SCENARIO_BAR_LIGHT,
            "--chart-down": report_renderer.CHART_SERIES_LIGHT["revenue"],
        }
        dark_expected = {
            "--chart-revenue": report_renderer.CHART_SERIES_DARK["revenue"],
            "--chart-net-profit": report_renderer.CHART_SERIES_DARK["net_profit"],
            "--chart-eps": report_renderer.CHART_SERIES_DARK["eps"],
            "--chart-operating-cash": report_renderer.CHART_SERIES_DARK["operating_cash"],
            "--chart-capex-proxy": report_renderer.CHART_SERIES_DARK["capex_proxy"],
            "--chart-scenario": report_renderer.SCENARIO_BAR_DARK,
            "--chart-up": report_renderer.SCENARIO_BAR_DARK,
            "--chart-down": report_renderer.CHART_SERIES_DARK["revenue"],
        }
        self.assertEqual(tokens("light"), light_expected)
        self.assertEqual(tokens("dark"), dark_expected)
        # 打印强制白纸：显式回到 light 值，阻断暗色模式值泄漏进 PDF
        self.assertEqual(tokens("print"), light_expected)


if __name__ == "__main__":
    unittest.main()
