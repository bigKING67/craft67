# Revenue Operations Dashboard 设计评审

## 1. 证据等级与评分区间

- **评审方式**：`design-craft`，`critique` 模式
- **Evidence level：L0 static**
  - 现有证据只有产品背景和界面结构的文字描述。
  - 没有截图、线框图、DOM、组件源码、设计 token、真实数据或运行态证据。
  - 虽然 prompt 提供了用户和任务背景，但 `L1 contextual` 仍要求至少有截图，因此本次不能提升到 L1。
- **暂定 Product UI taste score band：75–84 / 100**
- **成熟度区间：Clean but generic**
- **置信度：中低，仅适用于概念结构**

该结构与典型的 **dashboard card soup** 高度一致：形式整齐，但产品判断和注意力层级偏平。由于“12 个等权 KPI 卡片”仍是核心结构，按照 anti-inflation 规则，概念层面的评分上限不应超过 **84**。

这不是对实际视觉完成度的精确评分。没有截图时，无法判断它最终是否真的具备 75 分以上所需的排版、对齐、字体、色彩和表面质量。

---

## 2. Design read

> **Reading this as：一个面向内部电商运营人员、克制且高密度的 enterprise ops command center，优化目标是在 3 秒内识别未来一小时最需要处理的 account 或 campaign，理解风险、影响、原因和责任人，并直接采取下一步动作。**

它不应该优化为“展示尽可能多的经营数字”，而应该优化为：

1. **哪里正在偏离预期？**
2. **哪一个异常影响最大、最紧急？**
3. **为什么发生？**
4. **由谁处理？**
5. **现在应该做什么？**

主导的人类需求是 **理解、判断和及时行动**，不是浏览、探索或被营销式视觉吸引。正确的视觉方向应是：

- `enterprise dense`
- `ops command center`
- blocker-first hierarchy
- table-first rhythm
- semantic state color
- minimal elevation
- quiet, state-oriented motion

---

## 3. 主要层级与产品适配问题

### P1 — 12 个等权 KPI 卡片制造了错误的注意力模型

所有 KPI 使用相同尺寸、位置和表面权重，意味着界面在视觉上宣称它们同样重要。但运营人员并不是来平均阅读 12 个指标，而是来寻找当前最值得介入的异常。

直接影响：

- 高风险指标和例行总量难以快速区分。
- 用户需要逐卡解码，而不是沿着明确的判断路径扫描。
- 正常、异常、预警和阻断状态可能被相似性吞没。
- 首屏缺少唯一、稳定的第一焦点。

这是典型的 **flat KPI grid**：信息存在，但优先级没有被设计出来。

### P1 — 信息顺序与“未来一小时采取行动”的任务不一致

当前结构是：

`12 KPI cards → decorative chart → dense table → generic tips`

更接近经营概览或模板化 BI 首页，而不是操作决策面。描述中没有出现：

- urgent exception queue
- revenue-at-risk / impact ranking
- threshold breach
- owner
- recommended next action
- data freshness
- action status

因此，当前概念把“概览”放在“决策”之前，把“历史展示”放在“异常处理”之前。正确的 continuity 应该是：

`风险摘要 → 紧急异常 → 原因诊断 → 下一步动作 → 全量明细`

### P1 — Decorative area chart 消耗了注意力，但没有承担分析任务

dashboard 中的每张图都应该回答一个具体问题，例如：

- 风险从什么时候开始扩大？
- 当前异常来自哪个渠道、账户或活动？
- 指标变化是趋势、突发还是周期性波动？
- 哪个事件与拐点相关？

“Decorative”意味着该图目前主要填充空间或制造 dashboard 感，而不是支持判断。它会与真正需要第一时间看到的异常、影响和操作入口竞争。

如果无法为图表写出一个清晰的问题标题和相应决策，它应该被删除，而不是被重新美化。

### P1 — Generic tips 右侧栏与当前对象和决策脱节

通用 tips 通常存在三个问题：

- 不随当前账户、活动或异常变化。
- 不能解释当前风险为何发生。
- 不能直接推动下一步动作。

这会造成一个低价值但永久占宽的视觉区域，并压缩高密度表格的有效空间。对于内部运营台，右栏应具备明确的情境责任，否则应移除。

更合理的替代是：

- 当前异常的 `next-action rail`
- 需要处理的 exception queue
- 当前选中行的诊断和操作面板
- 阈值、owner、数据新鲜度和处理状态
- 可关闭或按需展开的 contextual inspector

### P1 — Dense table 尚未证明是 task-first table

prompt 只能证明存在一张高密度表格，不能证明其字段顺序、筛选、排序和行操作支持决策。

一张运营表格不能只是 data dump。用户应该无需横向解码，就能连续看到：

1. Account / Campaign identity
2. Current status
3. Risk or anomaly
4. Estimated impact
5. Cause or signal
6. Owner
7. Data freshness / last change
8. Next action

如果列顺序来自数据 schema，而不是运营决策顺序，那么表格即使很密，也只是“高密度地展示数据”，而不是“高效率地支持行动”。

### P2 — KPI 缺少可解释性合同

prompt 没有说明 KPI 是否包含：

- comparison period
- benchmark
- threshold
- delta direction
- owner
- freshness timestamp
- scope
- confidence or completeness

这部分不能判定为实际缺失，但它是实施前必须补齐的合同。任何被强调的数字都必须回答：

> **Compared to what, over which period, under which scope, and why does it require attention now?**

### P2 — 现有结构与“克制企业控制台”的 style authority 存在概念冲突

风险不在于卡片本身，而在于过度卡片化：

- 每个对象都有边框、圆角和独立表面。
- 页面依靠容器数量而不是信息层级组织内容。
- chart 和 tips 形成模板化 dashboard 语法。
- 运营阻断项与一般经营指标缺少明确差异。

克制的企业控制台应该更多依靠：

- typography hierarchy
- density gradient
- alignment
- section rhythm
- subtle dividers
- semantic status treatment

而不是更多卡片、阴影、彩色背景或“大数字 hero”。

---

## 4. 具体设计动作

### 4.1 `Dashboard card soup → decision surface`

将首屏从等权网格改成：

```text
Scope / Time window / Data freshness / Global filters
------------------------------------------------------
Lead operational state      Compact supporting metric strip
------------------------------------------------------
Urgent exception queue / highest-impact accounts or campaigns
------------------------------------------------------
Diagnostic chart, only when it explains the exception
------------------------------------------------------
Task-first account or campaign table
```

推荐结构是：

> **`lead + support + action queue + diagnostic + detail`**

其中：

- **Lead**：一个最需要运营关注的状态，而不是营销式 hero。
- **Support**：将原 12 个 KPI 中的支持性指标压缩为紧凑 summary strip。
- **Action queue**：按影响、紧急度或阈值突破排序的待处理对象。
- **Diagnostic**：解释异常，不与异常本身竞争。
- **Detail**：全量 table 用于比较、筛选和执行。

不要简单删除 12 个指标；应把它们重新分层为：

- lead
- supporting
- diagnostic
- progressively disclosed

### 4.2 `Flat KPI grid → priority hierarchy`

先根据运营决策定义 KPI 层级：

| 层级 | 作用 | 处理方式 |
|---|---|---|
| Lead | 当前最重要的风险或机会 | 单一主导区域，明确影响和下一步动作 |
| Supporting | 判断整体态势所需的少量上下文 | 紧凑 metric strip，不使用 12 个独立重卡片 |
| Diagnostic | 解释 lead 状态为何发生 | 放入异常详情、图表或展开区域 |
| Reference | 偶尔查询但不驱动即时动作 | 下移、折叠或进入二级页面 |

Lead 对象可以是“未来一小时预估收入风险”“突破阈值的 campaign 数量”等，但最终定义必须来自真实运营规则，不能由视觉设计自行猜测。

每个强调指标至少需要：

- 值
- 时间范围
- 对比基线
- delta
- threshold 或目标
- scope
- freshness
- semantic state

### 4.3 `Generic tips rail → contextual action rail`

右栏只在能够承担上下文操作时保留。

建议内容：

- 当前选中异常的影响摘要
- 可能原因及证据
- owner 和处理状态
- 推荐动作
- 进入账户或活动详情
- acknowledge / assign / resolve 等明确操作
- 最近一次数据更新时间

如果没有足够可靠、可执行的上下文内容，则移除右栏，把空间还给 exception queue 和 table。

### 4.4 `Decorative chart → diagnostic chart`

图表必须以问题命名，而不是以数据类型命名。

弱：

> Revenue trend

更有效：

> Revenue risk accelerated after 14:00; which campaigns caused the change?

图表要求：

- 与 lead risk 使用相同时间范围和筛选范围。
- 标记 threshold、异常区间和重要事件。
- 提供明确轴、单位、基线和数据新鲜度。
- 采用 direct labels 或清晰 legend。
- 颜色使用 data/state token，不使用装饰性色彩。
- 图表位置低于异常队列，除非趋势本身就是首要决策对象。
- 如果它不能改变用户的判断或动作，直接移除。

### 4.5 `Table as data dump → task-first table`

推荐优先字段顺序：

```text
Account / Campaign
Status
Risk / Anomaly
Estimated Impact
Cause / Signal
Owner
Last Change / Freshness
Next Action
```

次要 metadata 可：

- 合并到次级信息行
- 放入可展开详情
- 使用列配置
- 下移到横向滚动区域

表格设计规则：

- 文本左对齐，数字右对齐。
- 金额、百分比和 delta 使用稳定的 tabular figures。
- filters 与它所影响的表格相邻。
- 默认排序应服务“先处理谁”，而不是数据库顺序。
- row action 应显式、可键盘访问，不依赖 hover 才出现。
- 状态不能只靠颜色；同时使用文字、图标或形态。
- sticky column/header 只在确实提升扫描效率时使用。
- loading、empty、error、stale、partial-data 状态应出现在表格附近，并提供恢复路径。

### 4.6 建立清晰的 density gradient

目标不是降低信息量，而是让信息按决策价值排列：

- 首屏顶部：低数量、高优先级、高解释力。
- 中部：异常队列和诊断证据。
- 下部：高密度全量数据。
- 二级区域：低频 metadata 和历史细节。

这样可以保持“dense but calm”，避免把 enterprise console 做成稀疏营销页，也避免所有区域都同样拥挤。

### 4.7 执行 token-backed semantic color

建议采用明确的角色层，而不是直接指定具体颜色：

- `surface.page`
- `surface.section`
- `surface.selected`
- `border.divider`
- `text.primary`
- `text.secondary`
- `text.muted`
- `state.warning`
- `state.danger`
- `state.success`
- `state.info`
- `data.positiveDelta`
- `data.negativeDelta`
- `focus.ring`

使用原则：

- 大多数页面保持中性表面和细分隔线。
- warning/danger 只用于真实异常或风险。
- 正常总量不因“重要”就获得彩色背景。
- 不用颜色区分布局层级；优先使用位置、字号、字重、密度和留白。
- 状态必须在去除颜色后仍可理解。
- elevation 只用于 overlay、selection 或真实层级，不为每个 KPI 卡片制造阴影。

### 4.8 把真实状态纳入组件合同

实施前必须定义：

- default
- hover
- selected
- focus-visible
- loading
- empty
- error
- stale data
- partial data
- permission-limited
- long label
- extreme value
- success / resolved

恢复信息应靠近受影响对象，并说明：

1. 发生了什么。
2. 哪个对象受影响。
3. 用户现在可以做什么。

---

## 5. 已有依据与未验证项

### 由 prompt 明确提供的事实

以下仅属于**文字 brief 证据**，不是运行时验证：

- 产品是内部电商团队使用的 revenue operations dashboard。
- 核心用户需要判断未来一小时应该关注哪个账户或活动。
- 当前概念包含 12 个等权 KPI 卡片。
- 当前概念包含一张 decorative area chart。
- 当前概念包含一张 dense account table。
- 当前概念包含 generic tips 右栏。
- 目标风格是 restrained enterprise console。
- 要求 dense but calm，不采用 marketing hero treatment。
- 颜色应完全由 token 支撑。

### 可从概念结构直接推导的判断

- 12 个等权 KPI 卡片会形成平坦优先级。
- decorative chart 没有被赋予明确分析问题。
- generic tips 与具体运营对象和动作的关系不足。
- 页面缺少明确描述的 exception-first / next-action-first 信息结构。
- 当前概念更接近通用 admin dashboard 语法，而不是面向一小时决策的 ops command center。

### 未验证，不能作为已完成质量声明

- 实际视觉质量、构图和页面平衡
- 字体、字号、字重、行高和 numeric typography
- spacing、padding、alignment 和 grid discipline
- 实际颜色值、对比度及 token 使用情况
- 卡片的 border、radius、shadow 和 elevation
- KPI 是否已有 comparison、threshold、owner 或 freshness
- 表格真实列顺序、排序、筛选、固定列和 row action
- 图表 scale、axis、legend、tooltip、annotation 和数据正确性
- hover、active、selected、disabled 和 focus-visible
- keyboard navigation 和 screen-reader semantics
- loading、empty、error、stale、partial-data 和 permission 状态
- long content、极端数值和真实数据密度
- 响应式布局、最小支持宽度和移动端行为
- 性能、图表渲染成本或大表格滚动表现
- light/dark theme parity
- 浏览器或任何运行时行为

本次没有使用截图、DOM、源码或浏览器证据，因此不能声称上述项目通过验证。

---

## 6. 实施前的最小验证计划

### Gate 1 — 确认运营决策合同

与至少一名实际 operator 和业务 owner 确认：

- “未来一小时最重要的决定”具体是什么。
- account/campaign 的优先级如何计算。
- 什么条件构成 warning、critical 和 blocker。
- 哪个指标表达影响，哪个指标表达紧急度。
- 用户可以在 dashboard 内直接执行哪些动作。
- 动作由谁负责，如何表示 assigned / acknowledged / resolved。
- 数据允许多旧，何时必须显示 stale。
- 默认 scope、时间窗口和比较基线是什么。

**通过条件**：能够写出一条无歧义的默认排序规则，并能说明为什么排在第一的对象必须先处理。

### Gate 2 — 获取最小真实证据包

实施前至少需要：

- 一张当前主要桌面宽度下的完整页面截图或线框。
- 当前 `DESIGN.md`、token 表或等效 style authority。
- 5–10 行脱敏的代表性真实数据。
- 至少包含：
  - 正常对象
  - warning
  - critical
  - 长 account/campaign 名称
  - 极大金额或百分比
  - 缺失值
  - stale data
  - 无数据场景
- 当前支持的最小 viewport 宽度。
- 现有组件和表格能力清单。

**通过条件**：能够验证新的层级不是基于理想化短文本和正常数据设计。

### Gate 3 — 对每个模块写出决策责任

在进入视觉实现前，为模块填写：

| 模块 | 用户问题 | 输入证据 | 下一步动作 |
|---|---|---|---|
| Lead state | 现在最严重的问题是什么？ | impact、threshold、freshness | 查看或处理首要异常 |
| Support strip | 整体态势是否支持该判断？ | 核心 supporting metrics | 调整 scope 或进入诊断 |
| Exception queue | 先处理哪个对象？ | priority、risk、owner | assign / inspect / resolve |
| Diagnostic chart | 为什么、何时开始变化？ | trend、event、threshold | 定位原因 |
| Task-first table | 还有哪些对象需要比较？ | 全量明细 | filter / sort / act |

**通过条件**：不能回答具体用户问题或不能改变下一步动作的模块，应删除、合并或降级。

### Gate 4 — 进行低保真任务测试

用低保真结构完成至少三个场景：

1. 找出未来一小时收入影响最大的异常。
2. 找出负责该对象的 owner，并确定下一步动作。
3. 判断这是单一 campaign 问题还是广泛趋势。

建议验收条件：

- 用户在 **3 秒内**能指出首要风险或动作。
- 不需要逐个阅读 12 个 KPI。
- 用户能解释“为什么它排第一”。
- exception queue 出现在低风险概览和历史图表之前。
- table 中 identity、status、risk、impact、owner 和 next action 可连续扫描。
- chart 能回答一个明确问题；否则移除。
- semantic state 在不依赖颜色的情况下仍可识别。

### Gate 5 — 在开工前锁定实现后的验证矩阵

至少预先约定：

- **Viewports**：主要桌面宽度和产品声明支持的最小宽度。
- **Data cases**：正常、长文本、极端数值、空数据、错误、stale、partial data。
- **Interactions**：filter、sort、row selection、row action、keyboard focus。
- **Chart**：axis、scale、legend、tooltip、annotation、overflow。
- **Accessibility**：contrast、focus-visible、非颜色状态表达、语义标签。
- **Design system**：无未经解释的 literal color；状态、数据和表面使用正确 token role。
- **Acceptance**：首要动作 3 秒可识别，阻断项先于例行指标，所有强调数字都回答“compared to what”。

在这些最小证据和验收条件确定之前，不建议直接进入高保真视觉实现；否则很容易只是把现有 card soup 做得更整齐，而没有把它转化为真正的运营决策面。