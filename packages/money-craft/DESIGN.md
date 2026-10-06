---
schema: money-craft.report-design.v3
surface: research-publication
mode: read
default_theme: editorial-ivory
tokens:
  color:
    canvas: "#ECECE8"
    paper: "#FCFBF7"
    ink: "#242724"
    ink_secondary: "#4C504C"
    ink_muted: "#686D67"
    line: "#DDDFD6"
    line_strong: "#B1B7AC"
    accent: "#315868"
    accent_dark: "#244959"
    cool: "#315868"
    warning: "#8A601C"
  type:
    display: "Songti SC, STSong, Noto Serif CJK SC, Source Han Serif SC, serif"
    body: "PingFang SC, Hiragino Sans GB, Microsoft YaHei, Noto Sans CJK SC, system-ui, sans-serif"
    numeric: "SFMono-Regular, Menlo, Consolas, ui-monospace, monospace"
  measure:
    prose: "full-column"
    report: "1080px"
---

# Money Craft Research Publication System

## 设计解读

Money Craft 的最终报告是一份给长期投资者阅读和复核的中文研究刊物。它应当显得 **成熟、具体、编辑化、具有判断力**，而不是 dashboard、审计后台、券商模板或 AI 自动生成页面。

内部参数：`DESIGN_VARIANCE=5`，`MOTION_INTENSITY=1`，`VISUAL_DENSITY=6`。

## 核心原则

1. **刊物而非应用外壳。** 页面围绕标题、判断、图表、正文和脚注组织，不使用左侧后台导航、四等分 KPI 仪表盘或通用卡片网格。
2. **先判断，再解释，再复核。** 页头交代公司、证券、研究期和正文已有的关键数字，完整结论及其引用只呈现一次，随后呈现有数据支持的核心图表。不要为首屏塞入两张图而挤压结论，或生成空指标槽位。
3. **编辑留白，不留空页。** 留白用于建立段落与章节关系，不得让 A4 页面下半部空置，也不得用巨型标题制造虚假高级感。
4. **中西文角色明确。** 中文刊物标题可使用宋体/现代衬线建立编辑气质；正文、表格和界面辅助信息使用高可读无衬线；数字、日期和哈希使用等宽字体。
5. **颜色表达语义。** 温和白纸、石墨正文与蓝灰索引构成主视觉；图表实体系列延续固定色表，朱砂保留为负向提示和收入系列色。颜色不替代标签、位置或文字说明。
6. **图表属于文章。** 图表使用细线、直接标注、明确单位和解释文字，与正文共享网格；不放进圆角 dashboard 卡片。

## 阅读结构

1. **Publication masthead**：Money Craft 字标、报告类型、证券、研究日、数据截止和 revision。
2. **Research opening**：公司名、报告类型与已披露指标采用非对称编辑网格；仅当源文明确给出判断标签时显示该标签。结论、反方边界和引用由原文完整保留，不自动输出“待复核”评级。
3. **Evidence spread**：财务趋势和估值情景组成一个双栏证据跨页，宽屏并排、窄屏顺序堆叠。
4. **Research narrative**：每节回答一个研究问题；章节编号、标题和正文沿统一基线组织。
5. **Risk and falsification**：风险、反方证据和反转条件使用更强的文字层级，而不是红色卡片。
6. **Sources and seal**：来源使用脚注索引式排版，最后以审计、证据、离线验证和源哈希收口。

## 字体与排版

- HTML 公司名：32-46px，宋体/现代中文衬线，字重 600 左右，不使用超粗黑体。
- HTML 核心命题：19-22px / 1.65；正文：16-17px / 1.78，主栏全宽。
- 中文正文使用 `line-break: strict`；宽屏保留 `word-break: keep-all`，760px 以下使用 `word-break: normal` 允许中文自然折行，避免整段词组挤到下一行。长 URL、哈希和等宽定位符才允许 `break-all`。
- HTML H2：27-32px；H3：18-21px；章节编号作为边栏坐标，不做装饰徽章。
- PDF 正文：9.5pt / 1.65；公司名 28pt；章节标题 16pt。
- 表格数字右对齐并使用 tabular numerals；长 SHA 与 URL 允许断行。
- 禁止大面积全大写英文、过度字距、遍地等宽字体和连续粗黑标题。

## 组件、页面与网格

- 屏幕主体最大宽度 1080px；正文与图表共用刊物宽度和 padding，禁止用西文 `ch` 把中文主栏掐出空白。
- 页头采用标题与实际指标的非对称布局，完整结论位于其后；PDF 的页头和指标使用打印稳定的表格布局，不复用屏幕 flex 的收缩行为。
- 桌面目录是顶部安静索引，不占据永久左栏；移动端目录使用明确的展开按钮，不显示被裁掉的半个章节。
- 区块默认依靠分隔线、标题和间距分组；只有真正需要状态边界的内容才使用底色。
- 圆角只用于按钮焦点和少数状态控件；研究正文、图表、表格和来源不使用卡片圆角。

## 颜色与材质

- 主纸张为温和象牙白，不做仿古纹理、渐变、玻璃、光晕、目录毛玻璃或软阴影堆叠。
- 蓝灰用于阅读索引、引用和截止日价格；正文主体保持近黑。
- 深色阅读模式使用低饱和深色纸面与浅灰文字，保留系列和状态语义，不做简单反相。
- 打印始终是白纸、近黑正文和受控强调；保证灰度打印时仍可依靠线型和文字区分。

## 图表

- 财务趋势采用有数据支持的 small multiples；各自量程独立，直接标注起止值和累计变化。支持年份为行或列的财务表；未披露的现金流不补画，非正起点不强算增长率。
- 估值情景采用细条/区间而非厚重 dashboard 柱形；明确标出当前价格和假设属性。
- 图表必须显示分析问题、单位、时间边界、数据状态和解释，不得只显示漂亮线条。
- SVG 颜色、字重、网格线和正文排版共享 token；图表无圆角外框、无阴影、无渐变。

## 交互与可访问性

- 无 JavaScript 时正文、图表和来源全部可见；JavaScript 只增强主题、目录和阅读进度。
- 桌面目录支持页内导航；移动目录通过 44px 以上按钮展开并在选择章节后关闭。
- 主题按钮、目录按钮和链接具备清晰 `focus-visible`。
- 只允许 `#anchor` 内链；外部来源以不可点击的文本定位符保存。
- `prefers-reduced-motion` 关闭过渡；不使用滚动入场或循环动画。

## PDF

- A4 首页按页头、完整结论、核心图表展开；内容长时自然分页，禁止缩小字体来强行容纳固定模块数。
- 页眉显示 Money Craft 与当前章节；页脚显示证券、研究日期和页码，三者缺一不可。
- 表头跨页重复；避免孤立标题、孤立图表、空白尾页和仅含审计封印的页面。
- HTML/PDF 文件名统一为 `report.html` / `report.pdf`；禁止在 Money Craft 当前输出中出现 Kami 命名。

## 禁止模式

- `report-kami.*`、Kami 品牌、Kami renderer 或旧兼容命名出现在当前交付。
- 左侧后台导航、巨型粗黑 hero、四等分 KPI dashboard、同尺寸卡片阵列。
- 图表圆角卡片、低对比灰绿配色、通用绿色金融模板。
- 移动端横向截断目录、不可见剩余内容或只有桌面缩小版的响应式处理。
- 大片无意义空白、每章强制换页、单页只有少量文字。
- 用西文 `68ch`/`70ch`/`72ch` 限制中文正文行宽。
- 末页审计封使用 `FAIL 0`、全大写英文标签等系统回执腔。

## 本次参考与边界（2026-09-05）

lieflat-charts（`eace082a317b696c5570c25826a53a7fa113e984`）仅作为视觉参考：采用细线、直接标注、真实单位、图注参与叙事的通用方法。未复制其模板、脚本、字体或素材，未安装该 Skill；其 PolyForm Noncommercial 许可和 CDN 依赖不进入 Money Craft 分发。继续使用自有确定性 SVG、离线 HTML 与 WeasyPrint PDF。
