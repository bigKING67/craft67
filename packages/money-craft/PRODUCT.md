---
product: Money Craft Research Reports
platforms:
  - web
  - print-pdf
primary_users:
  - long-term individual investor
  - evidence-reviewing analyst
accessibility_target: WCAG 2.2 AA where applicable
---

# Money Craft Research Reports

Money Craft 把已审计的投资研究 Markdown 变成适合深度阅读、复核和长期归档的 HTML 与 PDF。

## 用户任务

1. 在两分钟内理解研究结论、估值、核心变量和主要风险。
2. 沿着清晰章节深入财务、生意、管理层、证伪条件和来源。
3. 看到结论的证据边界、时间边界、审计状态与离线校验状态。
4. 在桌面浏览器、窄屏和 A4 PDF 中获得一致的阅读顺序。

## 产品边界

- Canonical Markdown 是研究真源；渲染层不改写研究事实、数字、引用或结论。
- HTML/PDF 是可丢弃、可重建的 rendition，必须绑定源 Markdown SHA-256。
- HTML 必须离线可读，不得包含可导航外链、远程字体、远程图片或外部脚本依赖。
- 来源定位符必须可见，但在归档 HTML 中不可点击。
- 价格、估值区间和风险标签是研究辅助，不是交易指令。

## 完成标准

- 专业、克制、编辑化，不使用通用 SaaS hero、玻璃拟态、渐变或过度卡片化。
- 结论、估值、财务趋势、风险与证据保持明确层级。
- 长文段、密集表格、中英数字混排、负数、空值和长 URL 均不破坏布局。
- HTML 覆盖宽屏与 390px 窄屏；PDF 覆盖封面、正文、表格、图表、来源与页眉页脚。
- 渲染器错误必须显式失败，禁止留下占位符或只生成其中一种格式却报告成功。
