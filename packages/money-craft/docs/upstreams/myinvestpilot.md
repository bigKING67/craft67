# MyInvestPilot（策引）公开文档审读档案

## 2026-09-20 增量复核

通过 browser67 新建任务页，展开全部侧栏折叠后重新枚举目录，匿名捕获全部 155 页（149 正文/概览、6 分类导航），全部 HTTP 200 且存在唯一 article。完整目录与 `article-text-structure.v1` 正文/表格/代码结构指纹逐页对照旧基线：新增 0、目录移除 0、修改 0；revision 仍为 `bd9718319a04f466f9aa323ce7d391eadc0b7225945253336c99b3abb5cc5fa6`。

本轮结论是 **PASS：完整文档快照无变化**。它是全目录重新捕获与指纹核对，不冒充重新逐字审读，也不证明 HTTP 原始 HTML 字节、页面装饰或末尾更新日期完全相同。保留以下 2026-09-14 审读及后续有界吸收决策，没有新的采用/适配动作；只刷新 lock 的观察时间，reviewed/absorbed revision 不变。

收据见 [完整复核记录](../../acceptance/upstream-myinvestpilot-20260920.json)。原始正文保存在仓库外的私有证据目录，不进入运行包或公开仓库。任务页已关闭并验证。服务端引擎、会员能力和许可边界仍未验证。

- **审读日期：** 2026-09-14
- **资料范围：** 公开文档缓存 155 页；149 页正文/概览与 6 页分类导航。缓存中各页面获取状态均为 HTTP 200。
- **证据等级：** 文档声明，非 runtime 验证。本档案未登录会员、未申请或使用令牌、未调用策引会员 MCP、未运行回测、未下载实验数据库工件，也未验证源码、许可证、数据许可或生产服务行为。
- **用途：** 为 Money Craft 的上游/能力评估留存可审阅结论。本文的“拟议方向”均是后续候选，**不表示已经实现、吸收、安装、接入或发布**。

## 结论与定位

策引公开文档描述的是一个自有、服务端受控的模拟策略研究平台：以 canonical Strategy DSL 和受限 built-in 策略表达规则，由 schema、symbol 与语义校验进入确定性策略引擎，再返回可重读的结果与证据。Codex、Claude、Pi、OpenCode 等 Harness 是 MCP 客户端，不是该引擎本体；Agent Lab 当前只公开 resolve_symbols、validate_strategy_config、create_lab_run、get_lab_run 四个研究工具。

Money Craft 应保持自己的证据优先研究、财务数据对账、估值、假设/反证、长期 tracking 与用户明确约束下的决策支持为核心。策引若未来接入，合理位置是可替换的“受控实验 Provider adapter”，而不是主底座或研究真源：

    Money Craft research / evidence / valuation / user constraints / tracking
                                    |
                        experiment-provider adapter
                                    |
               策引 DSL 引擎 | 其他合规回测 Provider | 自建受控能力

策引面向其产品的“AI 不给出买卖结论、正式组合与 test_ 严格分离”等产品限制，不能原样覆盖 Money Craft 已有的估值和个人约束下决策支持；Money Craft 仍应把研究事实、分析判断与账户执行严格分层。

## 值得吸收的设计语义

### 语义保真优先于“能跑”

文档将配置合法性与策略语义是否忠实区分：校验通过只说明当前契约可执行，不能证明等同于用户原始意图。研究结果应明确标注 FAITHFUL、PARTIAL、UNSUPPORTED、AMBIGUOUS 或需要用户澄清，而不是用“最接近的可运行策略”替代 load-bearing 行为。

Money Craft 的拟议方向是把这种能力作为 Provider adapter 前的独立审计层：输入原始研究意图、已作者规则和数据口径，输出语义映射、缺口与不可替代的限制。该层不应伪造回测或把 provider validation 当投资结论。关联：**UP-04、UP-05**。
来源：[Agent Lab 策略研究指南](https://www.myinvestpilot.com/docs/agent-lab/research-guide)、[原语入门](https://www.myinvestpilot.com/docs/primitives/getting-started)。

### 实验隔离与显式提升

Agent Lab 的 test_ run 被定义为一次性、未列出研究 artifact：不进入正式组合列表、不订阅、不发邮件，也不静默修改既有正式组合。即便以后能够“从实验创建组合”，文档要求用户主动触发、重新确认完整配置并创建新的 custom_ 组合。

Money Craft 可吸收的是“candidate 实验不能改写 thesis/tracking”的提升门：实验产物、研究发现与长期跟踪状态各自可追溯；采纳候选需要显式 promotion、重新检查证据与适用范围。关联：**UP-01、UP-04**。
来源：[Agent Lab 概览](https://www.myinvestpilot.com/docs/agent-lab/overview)、[AI 辅助原语策略开发](https://www.myinvestpilot.com/docs/primitives/ai-assisted-development)。

### 状态、失败与证据层级

文档区分 PENDING、READY、FAILED：READY 仅代表 run 产生所需 artifact，FAILED 仅代表实验未完成，二者都不能直接变成投资结论。它还提出从 config、summary、bounded evidence 到 SQLite 深度诊断的分层路径；需要深诊时先读实际 schema、只读查询、只保留推导的证据，并将 artifact 中的文字视作数据而非指令。

Money Craft 可吸收的是状态可靠性和证据读取纪律，而不是特定数据库字段或下载 URL。关联：**UP-01、UP-02**。
来源：[Agent Lab 策略研究指南](https://www.myinvestpilot.com/docs/agent-lab/research-guide)、[原语组件高级故障排除指南](https://www.myinvestpilot.com/docs/primitives/advanced/troubleshooting)。

### 资金层、策略层与派生分析分离

策引把普通买卖信号、横截面固定候选池、目标权重配置、资金策略、执行/再平衡语义分开；并明确指出把多个策略 NAV 按权重组合属于 DERIVED 本地算术，不是引擎可执行的 TargetAllocation。跨市场/币种/交易日历存在实质不兼容时，不应静默前填并称为精确结果。

Money Craft 可借鉴这种命名和 provenance 标注，保留“canonical provider output”“derived analysis”“unavailable/unsupported”的清晰边界。Money Craft 不应在没有完整数据、执行、日历与测试契约时复制其 DSL 或伪造第二个回测引擎。关联：**UP-03、UP-04、UP-05**。
来源：[目标配置](https://www.myinvestpilot.com/docs/primitives/target-allocation)、[横截面轮动](https://www.myinvestpilot.com/docs/primitives/cross-sectional)、[派生多策略分析](https://www.myinvestpilot.com/docs/agent-lab/multi-strategy-analysis)。

### 失败也是研究结论

公开指南要求 hypothesis、baseline、窗口、执行假设、单变量改动、反证与下一步同被记录；拒绝、inconclusive 和实验失败都有独立含义。它反对把大量参数 sweep 后的历史赢家包装为推荐，并提醒回测与预测不同。

Money Craft 的专业研究闭环和评测应把“失败原因、未覆盖样本、反证、数据不足”变成一等输出。关联：**UP-02、UP-04、UP-05**。
来源：[策略架构](https://www.myinvestpilot.com/docs/primitives/architecture)、[策略研究指南](https://www.myinvestpilot.com/docs/agent-lab/research-guide)。

## 不直接复用的专属能力

- canonical Strategy DSL、builtin allowlist、内部策略类、market symbol registry、Transformer、资金策略和 execution/state-machine 语义，是服务端产品能力；公开 JSON 示例不是可移植引擎。
- 会员资格、约 12 小时的临时单会话令牌、四个 MCP 工具、队列/限流和用户侧保存方式，都属于策引产品接入合同，不是 Money Craft 的通用架构。
- TargetAllocation、横截面排名、StockBondSwitch 等需要完整的行情、日历、订单、成本、状态和测试支持；只复制 schema 外形不能建立可信回测。
- 本档案不将策引的 AI 产品禁令迁移到 Money Craft。Money Craft 应继续在证据、估值、假设、风险与用户明确约束基础上提供决策支持，同时保持不自动交易、不把有限样本包装为保证或指令。

## 已发现的口径冲突与文档风险

下列项目是公开页面之间的表述冲突或更新代际风险，不代表已验证 runtime 行为。任何未来 adapter 都应以当前 provider 的 schema、manifest、semantics 与真实 validation response 为准。

| 议题 | 冲突/风险 | 关联来源 |
| --- | --- | --- |
| 比较信号输入顺序 | signals 页开头的 LessThan 文案、其“正确”示例与同页后续 a < b 语义/示例并不一致；不能据此猜测当前引擎行为。 | [signals](https://www.myinvestpilot.com/docs/primitives/signals)、[market-indicators](https://www.myinvestpilot.com/docs/primitives/advanced/market-indicators) |
| 逻辑节点输入数 | market-indicators 页称 And/Or 严格两个输入，signals 与其他示例强调嵌套/组合；应由当前 schema 确定。 | [market-indicators](https://www.myinvestpilot.com/docs/primitives/advanced/market-indicators)、[signals](https://www.myinvestpilot.com/docs/primitives/signals) |
| 旧作者接口 | examples/composition 中仍有 Comparison、CrossAbove/CrossBelow、Streak.condition 风格；入门页明确 legacy/旧例不是新的作者接口，参数以生成 schema 为准。 | [examples](https://www.myinvestpilot.com/docs/primitives/examples)、[composition](https://www.myinvestpilot.com/docs/primitives/composition)、[getting-started](https://www.myinvestpilot.com/docs/primitives/getting-started) |
| 资产再平衡能力 | architecture-limitations 页仍称传统固定比例再平衡不直接支持；TargetAllocation 页已给出静态/动态目标、方向约束与 staged deployment。 | [architecture-limitations](https://www.myinvestpilot.com/docs/primitives/advanced/architecture-limitations)、[target-allocation](https://www.myinvestpilot.com/docs/primitives/target-allocation) |
| 优化方法 | optimization 页含网格搜索、阈值/仓位选择的叙述；较新的 Agent Lab 研究合同强调 baseline、单变量与反扫参。此类案例不能被当作通用推荐。 | [optimization](https://www.myinvestpilot.com/docs/primitives/advanced/optimization)、[research-guide](https://www.myinvestpilot.com/docs/agent-lab/research-guide) |
| 费用口径 | FAQ 对模拟费用的通常处理与研究/配置页的 commission/执行假设表述存在待核对差异；本档案不裁定哪一页代表 runtime。 | [FAQ](https://www.myinvestpilot.com/docs/guides/frequently-asked-questions)、[research-guide](https://www.myinvestpilot.com/docs/agent-lab/research-guide) |

## 源码、许可、导出与 runtime 的未验证项

**未验证：** 此次 155 页公开正文未提供 MyInvestPilot/策引策略引擎的官方开源仓库、源码许可、可复用 SDK、DSL parser 或 engine package。页面提及 Pi 开源，指的是外部 Harness，不是策引引擎源码。

**有文档声明、但未实测：** READY run 可在受控诊断路径返回当前实验的 portfolio.db 工件；signals.db 需要短期、限次、创建者绑定的 Bearer token。公开 official Portfolio 可通过页面声明的 manifest 定位公开 portfolio artifact。这是受限、只读 artifact 路径的文档证据，不等于稳定开放导出协议、通用公开 API、数据再分发许可或用户已获访问权。
来源：[研究指南](https://www.myinvestpilot.com/docs/agent-lab/research-guide)、[多策略派生分析](https://www.myinvestpilot.com/docs/agent-lab/multi-strategy-analysis)。

**未验证：** 会员 runtime、MCP 实际工具表、令牌生命周期、队列、schema/semantics 的当前版本、回测结果、手续费、数据质量、交易日历、执行价格、artifact 表结构及页面示例的实际可运行性。

## 后续改进候选

| ID | 候选方向 | 本次审读关联 |
| --- | --- | --- |
| UP-01 | 状态可靠性：研究、tracking、实验与 promotion 的状态机、receipt 和失败分类。 | test_/formal 隔离、READY/FAILED、artifact receipt |
| UP-02 | 专业研究闭环：hypothesis、baseline、证据、反证、局限、下一步与来源对账。 | 受控实验、证据层级、失败研究 |
| UP-03 | 个人组合分析：在用户明确约束下解释风险、估值、现金流与组合 trade-off。 | 资金分层、TargetAllocation 与 derived analysis 边界 |
| UP-04 | 受控实验：Provider-neutral capability/semantic audit、不可变 run receipt、canonical/derived 标签。 | DSL、built-in、MCP、实验隔离 |
| UP-05 | 评测：固定样本、不可变口径、反例与失败集，避免以单次高收益/单一指标选优。 | 反扫参、样本外限制、inconclusive 结论 |

## 逐页覆盖表

表中 reviewed 表示已纳入本次公开文档审读；content 为正文或概览页，navigation 为六个分类导航页。拟议方向只是后续关联，不表示实现状态。

| # | 题名 | 原 URL | 种类 | 阅读状态 | 拟议方向/关联 |
| ---: | --- | --- | --- | --- | --- |
| 001 | 欢迎使用策引文档 | <https://www.myinvestpilot.com/docs/> | content | reviewed | 背景参考 |
| 002 | Agent Lab 支持的 Built-in 策略 | <https://www.myinvestpilot.com/docs/agent-lab/built-in-strategies> | content | reviewed | UP-04；实验与语义合同 |
| 003 | 连接你的 Agent（Harness）到 Agent Lab | <https://www.myinvestpilot.com/docs/agent-lab/harness-setup> | content | reviewed | UP-04；实验与语义合同 |
| 004 | 用 Open Minis 在手机上连接 Agent Lab | <https://www.myinvestpilot.com/docs/agent-lab/mobile-open-minis> | content | reviewed | UP-04；实验与语义合同 |
| 005 | 派生多策略分析（组合多个策略结果） | <https://www.myinvestpilot.com/docs/agent-lab/multi-strategy-analysis> | content | reviewed | UP-04；实验与语义合同 |
| 006 | Agent Lab：用你自己的 Agent 做策略研究 | <https://www.myinvestpilot.com/docs/agent-lab/overview> | content | reviewed | UP-04；实验与语义合同 |
| 007 | Agent Lab 策略研究指南 | <https://www.myinvestpilot.com/docs/agent-lab/research-guide> | content | reviewed | UP-04；实验与语义合同 |
| 008 | AI 助手最佳实践 | <https://www.myinvestpilot.com/docs/ai-assistant/best-practices> | content | reviewed | UP-02；研究解释与边界 |
| 009 | AI 助手能力范围 | <https://www.myinvestpilot.com/docs/ai-assistant/capabilities> | content | reviewed | UP-02；研究解释与边界 |
| 010 | AI投资助手：信息检索与研究辅助 | <https://www.myinvestpilot.com/docs/ai-assistant/product-overview> | content | reviewed | UP-02；研究解释与边界 |
| 011 | 策引 AI 助手的角色与边界 | <https://www.myinvestpilot.com/docs/ai-assistant/roadmap> | content | reviewed | UP-02；研究解释与边界 |
| 012 | AI 助手使用场景 | <https://www.myinvestpilot.com/docs/ai-assistant/use-cases> | content | reviewed | UP-02；研究解释与边界 |
| 013 | A 股红利均衡组合：目标权重样本 | <https://www.myinvestpilot.com/docs/asset-allocation/china-dividend-balanced> | content | reviewed | UP-03、UP-04；资金层与实验输入 |
| 014 | 经典 60/40 组合：股债目标权重样本 | <https://www.myinvestpilot.com/docs/asset-allocation/classic-60-40> | content | reviewed | UP-03、UP-04；资金层与实验输入 |
| 015 | 定投与再平衡结合：现金流规则样本 | <https://www.myinvestpilot.com/docs/asset-allocation/dca-with-rebalancing> | content | reviewed | UP-03、UP-04；资金层与实验输入 |
| 016 | HFEA 杠杆策略：高波动研究样本 | <https://www.myinvestpilot.com/docs/asset-allocation/hfea> | content | reviewed | UP-03、UP-04；资金层与实验输入 |
| 017 | 资产配置入门 | <https://www.myinvestpilot.com/docs/asset-allocation/introduction> | content | reviewed | UP-03、UP-04；资金层与实验输入 |
| 018 | 再平衡策略组合表现对比 | <https://www.myinvestpilot.com/docs/asset-allocation/performance-comparison> | content | reviewed | UP-03、UP-04；资金层与实验输入 |
| 019 | 永久组合：固定多资产权重样本 | <https://www.myinvestpilot.com/docs/asset-allocation/permanent-portfolio> | content | reviewed | UP-03、UP-04；资金层与实验输入 |
| 020 | 再平衡机制 | <https://www.myinvestpilot.com/docs/asset-allocation/rebalancing> | content | reviewed | UP-03、UP-04；资金层与实验输入 |
| 021 | 现金管理标的百分比策略 | <https://www.myinvestpilot.com/docs/capital-strategies/cash-sweep-percent-capital-strategy> | content | reviewed | UP-03、UP-04；资金层与实验输入 |
| 022 | 定投策略 | <https://www.myinvestpilot.com/docs/capital-strategies/fixed-investment-strategy> | content | reviewed | UP-03、UP-04；资金层与实验输入 |
| 023 | 资金策略概览 | <https://www.myinvestpilot.com/docs/capital-strategies/overview> | content | reviewed | UP-03、UP-04；资金层与实验输入 |
| 024 | 百分比策略 | <https://www.myinvestpilot.com/docs/capital-strategies/percent-strategy> | content | reviewed | UP-03、UP-04；资金层与实验输入 |
| 025 | 差异化仓位策略 | <https://www.myinvestpilot.com/docs/capital-strategies/proportional-capital-strategy> | content | reviewed | UP-03、UP-04；资金层与实验输入 |
| 026 | 再平衡资金策略 | <https://www.myinvestpilot.com/docs/capital-strategies/rebalancing-capital-strategy> | content | reviewed | UP-03、UP-04；资金层与实验输入 |
| 027 | 简单百分比策略 | <https://www.myinvestpilot.com/docs/capital-strategies/simple-percent-strategy> | content | reviewed | UP-03、UP-04；资金层与实验输入 |
| 028 | 人机协作 | <https://www.myinvestpilot.com/docs/category/%E4%BA%BA%E6%9C%BA%E5%8D%8F%E4%BD%9C> | navigation | reviewed | 背景参考（分类导航） |
| 029 | 执行纪律 | <https://www.myinvestpilot.com/docs/category/%E6%89%A7%E8%A1%8C%E7%BA%AA%E5%BE%8B> | navigation | reviewed | 背景参考（分类导航） |
| 030 | 数学现实 | <https://www.myinvestpilot.com/docs/category/%E6%95%B0%E5%AD%A6%E7%8E%B0%E5%AE%9E> | navigation | reviewed | 背景参考（分类导航） |
| 031 | 深度议题 | <https://www.myinvestpilot.com/docs/category/%E6%B7%B1%E5%BA%A6%E8%AE%AE%E9%A2%98> | navigation | reviewed | 背景参考（分类导航） |
| 032 | 破除心魔 | <https://www.myinvestpilot.com/docs/category/%E7%A0%B4%E9%99%A4%E5%BF%83%E9%AD%94> | navigation | reviewed | 背景参考（分类导航） |
| 033 | 纪律手记 | <https://www.myinvestpilot.com/docs/category/%E7%BA%AA%E5%BE%8B%E6%89%8B%E8%AE%B0> | navigation | reviewed | 背景参考（分类导航） |
| 034 | AI 与 Agent 的角色边界 | <https://www.myinvestpilot.com/docs/concepts/ai-agent> | content | reviewed | UP-01、UP-02；规则到长期观察 |
| 035 | 背景与理念 | <https://www.myinvestpilot.com/docs/concepts/background> | content | reviewed | UP-01、UP-02；规则到长期观察 |
| 036 | 核心概念：从规则到长期观察 | <https://www.myinvestpilot.com/docs/concepts/overview> | content | reviewed | UP-01、UP-02；规则到长期观察 |
| 037 | 策引哲学：理解规则，而不是追随答案 | <https://www.myinvestpilot.com/docs/concepts/philosophy> | content | reviewed | UP-01、UP-02；规则到长期观察 |
| 038 | 风险分析 | <https://www.myinvestpilot.com/docs/concepts/risk-analysis> | content | reviewed | UP-01、UP-02；规则到长期观察 |
| 039 | 构建交易系统：从研究到长期观察 | <https://www.myinvestpilot.com/docs/concepts/trading-system> | content | reviewed | UP-01、UP-02；规则到长期观察 |
| 040 | 创建自定义 Portfolio：高级路径与验证边界 | <https://www.myinvestpilot.com/docs/guides/create-portfolio> | content | reviewed | UP-01、UP-03；状态、证据与组合阅读 |
| 041 | 邮件通知服务 | <https://www.myinvestpilot.com/docs/guides/email-notifications> | content | reviewed | UP-01、UP-03；状态、证据与组合阅读 |
| 042 | 策引常见问题 | <https://www.myinvestpilot.com/docs/guides/frequently-asked-questions> | content | reviewed | UP-01、UP-03；状态、证据与组合阅读 |
| 043 | 官方模拟组合：怎么看规则、回撤和当前状态 | <https://www.myinvestpilot.com/docs/guides/official-portfolios> | content | reviewed | UP-01、UP-03；状态、证据与组合阅读 |
| 044 | 投资组合深度分析：回测指标与风险评估详解 | <https://www.myinvestpilot.com/docs/guides/portfolio-analysis> | content | reviewed | UP-01、UP-03；状态、证据与组合阅读 |
| 045 | 快速上手：先看懂一个组合 | <https://www.myinvestpilot.com/docs/guides/quickstart> | content | reviewed | UP-01、UP-03；状态、证据与组合阅读 |
| 046 | 使用场景与学习方法 | <https://www.myinvestpilot.com/docs/guides/user-scenarios> | content | reviewed | UP-01、UP-03；状态、证据与组合阅读 |
| 047 | All-in的诱惑：凯利公式告诉你，全仓是条不归路 | <https://www.myinvestpilot.com/docs/investment-mindset/advanced-topics/all-in-temptation> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 048 | 实战心魔：利润幻觉、仓位代偿、假信号疲劳与补票陷阱 | <https://www.myinvestpilot.com/docs/investment-mindset/advanced-topics/combat-traps> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 049 | 微操即死：为什么频繁调整策略会毁掉你的收益 | <https://www.myinvestpilot.com/docs/investment-mindset/advanced-topics/micro-management-trap> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 050 | 市场的恶作剧：为什么短期正确的决策，长期却是错的 | <https://www.myinvestpilot.com/docs/investment-mindset/advanced-topics/perverse-incentives> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 051 | 为什么策引不支持日内交易/做空/期权/选股？设计理念与风险边界 | <https://www.myinvestpilot.com/docs/investment-mindset/advanced-topics/unsupported-features> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 052 | 学投资，到底在学什么？ | <https://www.myinvestpilot.com/docs/investment-mindset/advanced-topics/what-are-you-learning-in-investing> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 053 | 策引的最佳打开方式：与AI共舞，而非让AI替你决策 | <https://www.myinvestpilot.com/docs/investment-mindset/ai-collaboration/ai-assisted-investing> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 054 | 从一个投资想法到一个可跟踪组合 | <https://www.myinvestpilot.com/docs/investment-mindset/ai-collaboration/from-idea-to-trackable-portfolio> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 055 | 极简主义：少即是多，专注比折腾更有效 | <https://www.myinvestpilot.com/docs/investment-mindset/ai-collaboration/minimalism> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 056 | 被市场戏弄 | <https://www.myinvestpilot.com/docs/investment-mindset/discipline-notes/chau-fomo-market-mocked-me> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 057 | 信号触发，我没执行 | <https://www.myinvestpilot.com/docs/investment-mindset/discipline-notes/execution-deviation-real-case> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 058 | 我判断这是假信号 | <https://www.myinvestpilot.com/docs/investment-mindset/discipline-notes/expert-override-real-case> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 059 | 全靠幻觉 | <https://www.myinvestpilot.com/docs/investment-mindset/discipline-notes/mstx-no-strategy-only-illusion> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 060 | 可以共苦，不能同甘 | <https://www.myinvestpilot.com/docs/investment-mindset/discipline-notes/soxl-can-endure-pain-not-gain> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 061 | 与无聊共处：系统化投资最难的考验 | <https://www.myinvestpilot.com/docs/investment-mindset/execution-discipline/boredom-management> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 062 | 复杂性是焦虑的形状：为什么你的组合越来越臃肿？ | <https://www.myinvestpilot.com/docs/investment-mindset/execution-discipline/complexity-trap> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 063 | 分层资金管理：战略配置与战术执行 | <https://www.myinvestpilot.com/docs/investment-mindset/execution-discipline/layered-money-management> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 064 | 半途上车的艺术：如何在趋势中期理性进场 | <https://www.myinvestpilot.com/docs/investment-mindset/execution-discipline/mid-cycle-entry> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 065 | 投资叙事的保质期：为什么好策略也需要年度体检 | <https://www.myinvestpilot.com/docs/investment-mindset/execution-discipline/narrative-annual-review> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 066 | 打赢了仗，但战利品没运回后方 | <https://www.myinvestpilot.com/docs/investment-mindset/execution-discipline/profit-retention> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 067 | 把账户交给"法治":从人治到规则化执行 | <https://www.myinvestpilot.com/docs/investment-mindset/execution-discipline/rule-based-execution> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 068 | 策略失效判定：何时坚持，何时放弃 | <https://www.myinvestpilot.com/docs/investment-mindset/execution-discipline/strategy-failure-detection> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 069 | 纪律从哪里来：从相信别人，到理解自己为什么相信 | <https://www.myinvestpilot.com/docs/investment-mindset/execution-discipline/trust-before-discipline> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 070 | 模块化作战：水密舱原则与故障隔离 | <https://www.myinvestpilot.com/docs/investment-mindset/execution-discipline/watertight-compartments> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 071 | 从情绪化交易到系统化投资 | <https://www.myinvestpilot.com/docs/investment-mindset/introduction> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 072 | 单次实盘能证明什么？谈投资研究中的证据层级 | <https://www.myinvestpilot.com/docs/investment-mindset/mathematical-reality/evidence-hierarchy> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 073 | 杠杆ETF的数学真相：波动损耗与风险不对称 | <https://www.myinvestpilot.com/docs/investment-mindset/mathematical-reality/leverage-death-math> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 074 | 小仓位不是小赌注：用有限亏损购买右尾机会 | <https://www.myinvestpilot.com/docs/investment-mindset/mathematical-reality/small-position-optionality> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 075 | 沉没成本与市场失忆症：为什么"回本思维"是认知偏差 | <https://www.myinvestpilot.com/docs/investment-mindset/mathematical-reality/sunk-cost-fallacy> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 076 | 你在和一个不存在的自己比：反事实折磨 | <https://www.myinvestpilot.com/docs/investment-mindset/psychological-barriers/counterfactual-trap> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 077 | 目标太大，会成为你系统的最大敌人 | <https://www.myinvestpilot.com/docs/investment-mindset/psychological-barriers/grand-goal-override> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 078 | 持盈比持亏更难：为什么我们总在最好的时候离场？ | <https://www.myinvestpilot.com/docs/investment-mindset/psychological-barriers/holding-winners-paradox> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 079 | 叙事才是真正的仓位：你投的不只是指数 | <https://www.myinvestpilot.com/docs/investment-mindset/psychological-barriers/narrative-allocation-trap> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 080 | "聪明人"陷阱：为什么预测总是输给跟随？ | <https://www.myinvestpilot.com/docs/investment-mindset/psychological-barriers/prediction-trap> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 081 | 你测的不是回撤承受力，是晴天里对自己的幻想 | <https://www.myinvestpilot.com/docs/investment-mindset/psychological-barriers/risk-tolerance-illusion> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 082 | 牛市里的收益率竞赛：为什么别人的十倍会摧毁你的系统？ | <https://www.myinvestpilot.com/docs/investment-mindset/psychological-barriers/social-return-pressure> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 083 | 止损的艺术：有一种痛叫"卖飞"，有一种死叫"归零" | <https://www.myinvestpilot.com/docs/investment-mindset/psychological-barriers/stop-loss-art> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 084 | 盈亏同源：交易者首先要认识自己 | <https://www.myinvestpilot.com/docs/investment-mindset/psychological-barriers/trader-self-knowledge> | content | reviewed | 背景参考；执行纪律与风险叙事 |
| 085 | AI 应该直接告诉你买什么，还是解释原因？ | <https://www.myinvestpilot.com/docs/learning/ai-explains-not-decides> | content | reviewed | UP-03；个人组合理解与边界 |
| 086 | 已经有几只股票和基金了，怎么判断组合风险？ | <https://www.myinvestpilot.com/docs/learning/existing-portfolio-risk-check> | content | reviewed | UP-03；个人组合理解与边界 |
| 087 | 第一次试用策引，第一周应该做什么？ | <https://www.myinvestpilot.com/docs/learning/first-week-trial-guide> | content | reviewed | UP-03；个人组合理解与边界 |
| 088 | 官方组合为什么不是作业？ | <https://www.myinvestpilot.com/docs/learning/official-portfolios-not-homework> | content | reviewed | UP-03；个人组合理解与边界 |
| 089 | 学习资源 | <https://www.myinvestpilot.com/docs/learning/overview> | content | reviewed | UP-03；个人组合理解与边界 |
| 090 | 组合仓位怎样对应到我的账户？ | <https://www.myinvestpilot.com/docs/learning/portfolio-position-vs-account-position> | content | reviewed | UP-03；个人组合理解与边界 |
| 091 | 有了策略信号，实盘前还要看哪几层？ | <https://www.myinvestpilot.com/docs/learning/signal-to-real-trading-checklist> | content | reviewed | UP-03；个人组合理解与边界 |
| 092 | 策略信号为什么不是买卖指令？ | <https://www.myinvestpilot.com/docs/learning/signals-are-not-instructions> | content | reviewed | UP-03；个人组合理解与边界 |
| 093 | 模拟组合和真实账户，差在哪里？ | <https://www.myinvestpilot.com/docs/learning/simulated-portfolio-vs-real-account> | content | reviewed | UP-03；个人组合理解与边界 |
| 094 | 策引到底解决什么问题？ | <https://www.myinvestpilot.com/docs/learning/what-problem-does-myinvestpilot-solve> | content | reviewed | UP-03；个人组合理解与边界 |
| 095 | 策略亏损 20% 时，应该看什么？ | <https://www.myinvestpilot.com/docs/learning/what-to-check-during-20-percent-drawdown> | content | reviewed | UP-03；个人组合理解与边界 |
| 096 | 不知道什么时候买卖，普通投资者该怎么办？ | <https://www.myinvestpilot.com/docs/learning/when-to-buy-or-sell> | content | reviewed | UP-03；个人组合理解与边界 |
| 097 | A股市场分析 | <https://www.myinvestpilot.com/docs/market-analysis/china-market> | content | reviewed | UP-02；市场背景参考 |
| 098 | 加密货币市场分析 | <https://www.myinvestpilot.com/docs/market-analysis/crypto-market> | content | reviewed | UP-02；市场背景参考 |
| 099 | 邮件订阅市场分析 | <https://www.myinvestpilot.com/docs/market-analysis/email-subscription> | content | reviewed | UP-02；市场背景参考 |
| 100 | 市场分析概览 | <https://www.myinvestpilot.com/docs/market-analysis/overview> | content | reviewed | UP-02；市场背景参考 |
| 101 | 美股市场分析 | <https://www.myinvestpilot.com/docs/market-analysis/us-market> | content | reviewed | UP-02；市场背景参考 |
| 102 | 投资组合概览 | <https://www.myinvestpilot.com/docs/portfolios/overview> | content | reviewed | UP-01、UP-03；状态、证据与组合阅读 |
| 103 | 复杂策略分析与架构局限性 | <https://www.myinvestpilot.com/docs/primitives/advanced/architecture-limitations> | content | reviewed | UP-04；实验与语义合同 |
| 104 | 12个加密货币策略组合的实战对比：当数据推翻直觉 | <https://www.myinvestpilot.com/docs/primitives/advanced/crypto-strategy-case> | content | reviewed | UP-04；实验与语义合同 |
| 105 | 从151%到1178%：动态仓位的案例研究 | <https://www.myinvestpilot.com/docs/primitives/advanced/dynamic-position-strategy> | content | reviewed | UP-04；实验与语义合同 |
| 106 | 超越价格的维度：一次基本面风控的价值验证之旅 | <https://www.myinvestpilot.com/docs/primitives/advanced/fundamental-risk-control-case> | content | reviewed | UP-04；实验与语义合同 |
| 107 | 用回测检验想法：一次 SOXL 策略探索记录 | <https://www.myinvestpilot.com/docs/primitives/advanced/leveraged-etf-soxl-strategy> | content | reviewed | UP-04；实验与语义合同 |
| 108 | 市场指标原语指南 | <https://www.myinvestpilot.com/docs/primitives/advanced/market-indicators> | content | reviewed | UP-04；实验与语义合同 |
| 109 | 均值回归的真相：为什么"抄底"很难赚钱 | <https://www.myinvestpilot.com/docs/primitives/advanced/mean-reversion-strategy> | content | reviewed | UP-04；实验与语义合同 |
| 110 | 原语策略优化实战指南：从案例到方法论 | <https://www.myinvestpilot.com/docs/primitives/advanced/optimization> | content | reviewed | UP-04；实验与语义合同 |
| 111 | 信号确认的艺术：速度与质量的艰难权衡 | <https://www.myinvestpilot.com/docs/primitives/advanced/signal-confirmation-case> | content | reviewed | UP-04；实验与语义合同 |
| 112 | 股债轮动策略优化实战：从困境到突破的完整历程 | <https://www.myinvestpilot.com/docs/primitives/advanced/stock-bond-rotation-case> | content | reviewed | UP-04；实验与语义合同 |
| 113 | 原语组件高级故障排除指南 | <https://www.myinvestpilot.com/docs/primitives/advanced/troubleshooting> | content | reviewed | UP-04；实验与语义合同 |
| 114 | 杠杆ETF波动率控制案例：用信号确认驯服市场野兽 | <https://www.myinvestpilot.com/docs/primitives/advanced/volatility-control-case> | content | reviewed | UP-04；实验与语义合同 |
| 115 | AI 辅助原语策略开发 | <https://www.myinvestpilot.com/docs/primitives/ai-assisted-development> | content | reviewed | UP-04；实验与语义合同 |
| 116 | 原语策略系统架构：模块化策略构建指南 | <https://www.myinvestpilot.com/docs/primitives/architecture> | content | reviewed | UP-04；实验与语义合同 |
| 117 | 原语组合模式与最佳实践 | <https://www.myinvestpilot.com/docs/primitives/composition> | content | reviewed | UP-04；实验与语义合同 |
| 118 | 多标的轮动策略：在候选标的之间排名与选择 | <https://www.myinvestpilot.com/docs/primitives/cross-sectional> | content | reviewed | UP-04；实验与语义合同 |
| 119 | 原语策略示例 | <https://www.myinvestpilot.com/docs/primitives/examples> | content | reviewed | UP-04；实验与语义合同 |
| 120 | 原语策略入门：像搭积木一样配置交易系统 | <https://www.myinvestpilot.com/docs/primitives/getting-started> | content | reviewed | UP-04；实验与语义合同 |
| 121 | 指标原语参考：技术指标与基本面指标配置 | <https://www.myinvestpilot.com/docs/primitives/indicators> | content | reviewed | UP-04；实验与语义合同 |
| 122 | 信号原语参考：交叉、比较、逻辑组合等条件配置 | <https://www.myinvestpilot.com/docs/primitives/signals> | content | reviewed | UP-04；实验与语义合同 |
| 123 | 策略的艺术：从逻辑构建到实战优化 | <https://www.myinvestpilot.com/docs/primitives/strategy-design-best-practices> | content | reviewed | UP-04；实验与语义合同 |
| 124 | 目标配置：固定/动态目标、方向约束与分批部署 | <https://www.myinvestpilot.com/docs/primitives/target-allocation> | content | reviewed | UP-04；实验与语义合同 |
| 125 | 策略原语系统故障排除指南 | <https://www.myinvestpilot.com/docs/primitives/troubleshooting> | content | reviewed | UP-04；实验与语义合同 |
| 126 | AI 模型策略 | <https://www.myinvestpilot.com/docs/strategies/ai-model-strategy> | content | reviewed | UP-04；策略能力边界参考 |
| 127 | 交易策略基础 | <https://www.myinvestpilot.com/docs/strategies/basic-concepts> | content | reviewed | UP-04；策略能力边界参考 |
| 128 | 布林带策略：基于价格波动区间的交易方法 | <https://www.myinvestpilot.com/docs/strategies/bollinger-bands> | content | reviewed | UP-04；策略能力边界参考 |
| 129 | 买入持有策略 | <https://www.myinvestpilot.com/docs/strategies/buy-and-hold> | content | reviewed | UP-04；策略能力边界参考 |
| 130 | 吊灯止损策略：基于ATR的动态止损方法 | <https://www.myinvestpilot.com/docs/strategies/chandelier-exit> | content | reviewed | UP-04；策略能力边界参考 |
| 131 | 双均线趋势策略：如何捕捉大趋势并规避震荡损耗 | <https://www.myinvestpilot.com/docs/strategies/dual-moving-average> | content | reviewed | UP-04；策略能力边界参考 |
| 132 | 交易记录策略 | <https://www.myinvestpilot.com/docs/strategies/file-based-strategy> | content | reviewed | UP-04；策略能力边界参考 |
| 133 | MACD策略：趋势方向与动量强弱的双重判断 | <https://www.myinvestpilot.com/docs/strategies/macd-strategy> | content | reviewed | UP-04；策略能力边界参考 |
| 134 | 动量轮动策略详解：原理、ETF回测与实盘逻辑 | <https://www.myinvestpilot.com/docs/strategies/momentum-rotation> | content | reviewed | UP-04；策略能力边界参考 |
| 135 | 原语策略 | <https://www.myinvestpilot.com/docs/strategies/primitive-strategy> | content | reviewed | UP-04；策略能力边界参考 |
| 136 | 目标权重策略：资产配置再平衡规则 | <https://www.myinvestpilot.com/docs/strategies/target-weight-strategy> | content | reviewed | UP-04；策略能力边界参考 |
| 137 | 目标权重趋势过滤策略：让趋势决定你是否持仓 | <https://www.myinvestpilot.com/docs/strategies/target-weight-trend-filter> | content | reviewed | UP-04；策略能力边界参考 |
| 138 | 第一期：A 股双均线，到底有没有用？ | <https://www.myinvestpilot.com/docs/strategy-research-lab/china-market/issue-001-dual-ma-chiext> | content | reviewed | UP-02、UP-05；研究闭环与评测样本 |
| 139 | 第二期：A 股科技板块动量轮动，有没有比买最强的更好的办法？ | <https://www.myinvestpilot.com/docs/strategy-research-lab/china-market/issue-002-momentum-rotation> | content | reviewed | UP-02、UP-05；研究闭环与评测样本 |
| 140 | 第三期：双均线的有效边界——哪类 A 股标的对均线过滤响应更好？ | <https://www.myinvestpilot.com/docs/strategy-research-lab/china-market/issue-003-dual-ma-boundary> | content | reviewed | UP-02、UP-05；研究闭环与评测样本 |
| 141 | A 股策略研究 | <https://www.myinvestpilot.com/docs/strategy-research-lab/china-market/overview> | content | reviewed | UP-02、UP-05；研究闭环与评测样本 |
| 142 | 第一期：BTC 趋势跟踪哪家强？从双均线到自适应止损的完整实证 | <https://www.myinvestpilot.com/docs/strategy-research-lab/crypto-market/issue-001-trend-following-btc> | content | reviewed | UP-02、UP-05；研究闭环与评测样本 |
| 143 | 第二期：动量、波动率和轮动——哪些传统策略在加密市场失效？ | <https://www.myinvestpilot.com/docs/strategy-research-lab/crypto-market/issue-002-momentum-vol-rotation> | content | reviewed | UP-02、UP-05；研究闭环与评测样本 |
| 144 | 第三期：BTC 创新高还能追吗？入场信号与出场机制的实验 | <https://www.myinvestpilot.com/docs/strategy-research-lab/crypto-market/issue-003-btc-max-min-anomalies> | content | reviewed | UP-02、UP-05；研究闭环与评测样本 |
| 145 | 加密资产策略研究 | <https://www.myinvestpilot.com/docs/strategy-research-lab/crypto-market/overview> | content | reviewed | UP-02、UP-05；研究闭环与评测样本 |
| 146 | 策略研究档案 | <https://www.myinvestpilot.com/docs/strategy-research-lab/introduction> | content | reviewed | UP-02、UP-05；研究闭环与评测样本 |
| 147 | 第一期：动量轮动跑得赢 QQQ 吗？ | <https://www.myinvestpilot.com/docs/strategy-research-lab/us-market/issue-001-momentum-vs-qqq> | content | reviewed | UP-02、UP-05；研究闭环与评测样本 |
| 148 | 第二期：3 倍杠杆 ETF 能做卫星仓吗？ | <https://www.myinvestpilot.com/docs/strategy-research-lab/us-market/issue-002-leveraged-satellite> | content | reviewed | UP-02、UP-05；研究闭环与评测样本 |
| 149 | 第三期：铀矿与黄金被否定，电网基础设施仍待验证 | <https://www.myinvestpilot.com/docs/strategy-research-lab/us-market/issue-003-rejected-thematic-etfs> | content | reviewed | UP-02、UP-05；研究闭环与评测样本 |
| 150 | 第四期：防御科技与加密货币 ETF 的实证 | <https://www.myinvestpilot.com/docs/strategy-research-lab/us-market/issue-004-defense-crypto> | content | reviewed | UP-02、UP-05；研究闭环与评测样本 |
| 151 | 第五期：核心仓该加主动规则吗？QQQ/SMH/GBTC 三仓组合完整实证 | <https://www.myinvestpilot.com/docs/strategy-research-lab/us-market/issue-005-core-portfolio-rules> | content | reviewed | UP-02、UP-05；研究闭环与评测样本 |
| 152 | 第六期：定投 QQQ，你真的想清楚了吗？ | <https://www.myinvestpilot.com/docs/strategy-research-lab/us-market/issue-006-dca-qqq-stress-test> | content | reviewed | UP-02、UP-05；研究闭环与评测样本 |
| 153 | 第七期：给 QQQ 加一道出场规则，真的有用吗？ | <https://www.myinvestpilot.com/docs/strategy-research-lab/us-market/issue-007-qqq-trend-exit> | content | reviewed | UP-02、UP-05；研究闭环与评测样本 |
| 154 | 第八期：没有万能策略，但有更聪明的分散方式 | <https://www.myinvestpilot.com/docs/strategy-research-lab/us-market/issue-008-multi-asset-long-term> | content | reviewed | UP-02、UP-05；研究闭环与评测样本 |
| 155 | 美股策略研究 | <https://www.myinvestpilot.com/docs/strategy-research-lab/us-market/overview> | content | reviewed | UP-02、UP-05；研究闭环与评测样本 |
