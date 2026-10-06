from __future__ import annotations

import unittest

from scripts.style_metrics import repeated_passages, style_metrics


class StyleMetricsTests(unittest.TestCase):
    def test_counts_contrast_phrases(self) -> None:
        metrics = style_metrics("这是实施顺序，不是缩减需求。演示不能证明质量，也不代表最终类目。")
        self.assertEqual(metrics["contrast_phrases"], 3)
        self.assertEqual(metrics["contrast_breakdown"]["不是"], 1)

    def test_positive_text_has_no_contrasts(self) -> None:
        metrics = style_metrics("先用一个类目试点，出图质量合格后再扩展。")
        self.assertEqual(metrics["contrast_phrases"], 0)
        self.assertEqual(metrics["repeated_passages"], 0)

    def test_finds_repeated_boundary_across_sections(self) -> None:
        boundary = "试点不要求覆盖全部类目也不要求完整设计平台"
        text = f"正文：{boundary}。\n\n附录：{boundary}。"
        repeats = repeated_passages(text, window=12)
        self.assertEqual(len(repeats), 1)
        self.assertIn(boundary, repeats[0])

    def test_empty_text(self) -> None:
        self.assertEqual(style_metrics("")["contrast_per_1000_han"], 0.0)


if __name__ == "__main__":
    unittest.main()
