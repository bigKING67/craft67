## 1. 证据等级与评分区间

- **评审模式**：`design-craft / critique`；Web `Operate` 型 dashboard。
- **证据等级**：**L0 static**——只有产品上下文和界面结构的文字描述；即使上下文较完整，没有截图仍不能升级为 L1。
- **暂定 Product UI taste 区间**：**60–74 / Functional but ordinary**，仅评价概念层的信息架构与产品适配，置信度中低。
- 基本的数据模块已经存在，但界面没有围绕“下一小时该处理什么”建立优先级，因此不能仅凭模块齐全进入 `Clean but generic`。
- 未给出精确分数，因为对齐、字体、间距、token、对比度、真实数据、交互状态均无证据。
- 即使实际视觉执行很整洁，只要 `card soup` 和扁平层级仍是主问题，当前结构也不应超过 **84**。
- **本轮只读，未修改文件，也未进行或声称浏览器验证。**

## 2. Design read

> Reading this as: 一个面向电商收入运营人员的、克制且高密度的企业级操作台，优化目标是让用户在几秒内发现下一小时最值得处理的账号或活动，理解原因、影响和责任人，并立即采取动作；当前概念更像被动的数据目录，而不是决策界面。

核心产品指标应是 **time-to-first-correct-action**，而不是 KPI 覆盖数量。

理想决策链应压缩为：

`哪里异常 → 为什么现在重要 → 可能损失多少 → 谁负责 → 下一步做什么`

## 3. 最主要的层级与产品适配问题

### B1 — P1：12 张等权 KPI 卡造成 `card soup`

等尺寸、等位置权重会把例行总量、异常信号和紧急风险放在同一层级。用户必须自行比较十二个数字，界面没有替用户做第一次判断。

这与“一小时内决定关注对象”的工作目标直接冲突。

### B2 — P1：真正的工作对象——账号表格——被概览模块压后

账号或活动才是可以分派、诊断和操作的对象，但当前顺序先消耗注意力于 KPI 和装饰图表。

现有描述也没有建立任务优先的行语法：`identity / status / risk / impact / owner / next action`。

### B3 — P1：面积图没有获得其占用空间的产品理由

“装饰性”意味着它没有明确回答运营问题。趋势图只有在展示具体异常、阈值、时间窗口、对照基线，并能改变下一步动作时才有决策价值。

否则它只是扩大视觉层级，却没有缩短决策时间。

### B4 — P1：generic tips 右栏是持续性的注意力税

通用建议既不对应当前账号，也不说明证据、业务影响、责任人或下一动作；同时它永久占用横向空间，挤压更重要的表格和诊断区域。

在内部运营工具里，持续展示的内容必须比按需帮助更有时效性和上下文价值。

### B5 — P1：关键决策与运行状态合同未被定义

当前概念没有建立以下信息：作用域、统计窗口、比较基线、数据更新时间、异常阈值、排序规则和责任归属。

加载、无异常、无数据、错误、过期、部分数据和权限不足也均未验证；因此用户可能无法区分“业务正常”和“数据没有正常到达”。这是规格缺口，不是已确认的运行时缺陷。

## 4. Concrete design moves

### M1 `[B5]` — 建立紧凑的 command/context band

页面顶部只保留决策上下文：账号或渠道范围、时间窗口、全局筛选、`Last updated`、数据延迟或完整性状态。

不要做 marketing hero；它应是低高度、稳定、可扫读的操作条。

### M2 `[B1]` — 从 equal KPI grid 改成 `lead + support + action queue`

- 用一个 `Attention now` lead object 表达当前最高风险、潜在收入影响及首要对象。
- 将真正有不同决策用途的辅助 KPI 压缩成一条 summary strip，而不是十二张独立卡。
- 每个被强调的数字必须同时回答：统计周期是什么、与什么比较、是否越过阈值。
- 颜色只表达语义状态，不能用来制造装饰性差异。

### M3 `[B2]` — 把表格提升为 `task-first table`

让异常队列或账号表成为首屏主工作面，并按经业务确认的紧迫度和影响规则排序，而不是按数据库字段顺序排列。

优先列建议为：

`Account/Campaign → Status → Signal/Why now → Revenue impact → Owner/SLA → Next action`

数值右对齐，文本左对齐；筛选、排序和批量动作紧邻表格；行级动作必须明确且可通过键盘到达。

### M4 `[B3]` — 将图表降级为 contextual diagnostic

先给图表写出它要回答的问题，例如：“该账号的转化下降是瞬时波动，还是已经持续越过阈值？”

图表应绑定当前选择对象，显示时间范围、比较基线、阈值或异常标注。图型根据分析问题选择；若无法改变判断或行动，则直接移除，而不是更换装饰样式。

### M5 `[B4]` — 删除 generic tips，或改成 contextual action rail

右栏若保留，应随选中行展示：

`entity → evidence/change/threshold → business impact → owner/SLA → recommended action`

通用方法说明改为按需帮助、tooltip 或文档入口，不应长期占据决策画布。

### M6 `[B1, B2]` — 使用 `enterprise dense` 而非 over-cardified surface

- 以一个稳定页面画布、排版层级和细分隔线组织内容，减少嵌套卡片、阴影和重复圆角。
- 使用 tabular numerals、稳定列轴和紧凑但可辨认的间距节奏。
- 只使用既有 token role，如 `surface`、`text`、`border`、`status-*`、`focus`。
- 异常状态除颜色外必须同时提供文本、图标或形状线索。

### M7 `[B5]` — 把运行状态作为组件合同，而不是后补页面

- `Loading`：保留 command band、筛选和布局，只在正在更新的区域显示局部占位。
- `No exceptions`：明确表示数据已成功检查且当前无异常。
- `No data`：与无异常区分，说明缺失来源及可执行的重试或配置动作。
- `Error / stale / partial`：在安全时保留上次成功数据并显著标注时间和不完整范围，提供局部 `Retry` 与详情。
- `Permission`：解释缺失范围并提供申请访问路径。
- 行动作需要 pending、success、failure 和可恢复反馈；筛选、选择及上下文不得因局部失败而丢失。

### M8 `[B2, B5]` — 设计窄窗口、键盘和辅助访问行为

窄窗口不要简单把十二张卡纵向堆叠；顺序应保持为：

`context → attention queue → task table → diagnostics`

只允许数据区域内部横向滚动，关键标识和动作保持可达；禁止 hover-only 行动作。定义稳定的 `focus-visible`、逻辑焦点顺序、非颜色状态表达，以及图表的文本或表格替代。

## 5. Verified 与 unverified

### 本轮能够确认的内容

这里只能确认**提示词明确声明**了：

- 产品是内部 ecommerce revenue operations dashboard。
- 主要用户需要决定下一小时关注哪个账号或活动。
- 概念包含 12 张等权 KPI 卡、装饰性面积图、密集账号表和 generic tips 右栏。
- 视觉 authority 是克制、密集但平静、token-backed color 的企业控制台。
- 没有提供截图、DOM 或运行态证据。

这些是 brief-grounded facts，不是对真实实现的独立验证。

### 未验证，不能据此宣称的问题

- 实际页面是否严格符合上述结构。
- 字体、间距、栅格、对齐、卡片表面、对比度及 token 合规性。
- KPI 的真实语义、时间范围、基线、数据新鲜度和异常排序逻辑。
- 表格列顺序、扫描效率、排序、筛选、行操作和长内容表现。
- 图表比例尺、标签、图例、tooltip、阈值、数据正确性和可访问替代。
- hover、focus、keyboard、selected、disabled 及行操作反馈。
- loading、empty、error、stale、partial、permission 和真实数据边界。
- 桌面窄窗口、移动视口、缩放、overflow 和响应式行为。
- 实际运营人员是否能快速、正确地找到下一动作。

## 6. 实施前的最小验证计划

1. **锁定决策合同**：让一名实际 operator 和一名数据口径负责人用近期真实案例确认风险信号、阈值、收入影响、排序逻辑、owner、SLA 和允许执行的动作。
2. **采集真实 baseline**：在代表性数据下记录一个主要桌面视口和一个窄窗口；采集截图、DOM/computed style、token 映射、时间范围与数据更新时间，将证据从 L0 提升到至少 L2。
3. **验证低保真决策流**：使用真实账号名、长标签、缺失值和极端数值测试 proposed wireframe；用户应能在约三秒内指出首要风险，并说明证据、影响和下一动作。
4. **先签署 state matrix**：在编码前定义 normal、loading、no exceptions、no data、error、stale、partial、permission 以及行动作成功/失败时分别渲染什么、能做什么、保留哪些上下文。
5. **预先约定实现验收门禁**：完成后再做真实浏览器 desktop+narrow 检查、focus walk、keyboard/hover、sort/filter/action、长内容与各状态验证，并记录截图 artifact；这些均是计划，当前尚未执行。

结论：不建议先做视觉美化。应先把页面从“指标陈列”重构为“异常发现—证据解释—责任归属—立即行动”的决策表面，再落实 token、状态和响应式细节。旧 benchmark 记忆仅用于检查有限 move budget 的 blocker 覆盖；页面结论仍完全以本提示词和本轮读取的当前 `design-craft` 规则为准。

