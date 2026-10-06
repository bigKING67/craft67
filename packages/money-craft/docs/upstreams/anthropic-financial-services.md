# Anthropic financial-services：UP-02 选择性审读

## 2026-09-20 增量与方法对照

当前固定提交为 `fca3cc8e6c5692ba576b46d7c4783b8443c2a223`。完整 Git tree 未截断；已登记范围共 73 个文件，相对原观察版本只有 README 新增一行 `claude-for-financial-advisors` 入口。新增入口属于理财顾问 CRM/客户服务工作流，不自动扩展为本轮研究或运行依赖。

本轮下载并逐一核对 13 份文件的 Git blob SHA-1 和内容 SHA-256。全文读取根 LICENSE 及 6 份研究材料；README 仅阅读完整差异与上下文，initiating-coverage 入口仅阅读 1–110 行和标题清单；历史审读的 earnings-analysis、model-update、dcf-model、comps-analysis 四份入口与原哈希一致，未重复全文审读。详细覆盖及哈希见[本轮收据](../../acceptance/upstream-anthropic-20260920.json)。这不构成 73 个文件全部审完，`reviewed_revision` 保持 null，`absorbed_revision` 仍指向此前实际适配的版本。

### 方法与本地能力对照

下表源路径相对 `plugins/vertical-plugins/`，均绑定本轮固定提交；上游文档作为评估资料，其操作指令不支配本项目。

| 全文审读材料 | 有价值的方法 | 本地现状与本轮处置 |
|---|---|---|
| equity-research/skills/earnings-preview/SKILL.md | 保存预期来源与日期，围绕业务指标预先记录关注点 | `earnings_baseline.py` 已分离 analyst/management/consensus，并封存首披前后时间边界；不增加重复前瞻层，不将情景当股价预测 |
| equity-research/skills/catalyst-calendar/SKILL.md | 事件日期复核、过去事件与结果留档 | 已有事件窗口、确认/证伪条件、来源和复盘；事件发生不等于论文成立。多公司日历、邮件与日历写入不接入 |
| equity-research/skills/thesis-tracker/SKILL.md | 按论点记录支持/反证和跨期变化 | 已有不可改写历史、假设/红线状态与结构化 diff；不将论点变化自动映射为仓位操作 |
| equity-research/skills/initiating-coverage/references/task1-company-research.md | 业务模式、管理层、竞争、行业和风险的证据依赖 | 既有公司研究合同已覆盖主题；真正待加强的是实际同业数据案例，不能靠增加章节或字数完成 |
| equity-research/skills/initiating-coverage/references/valuation-methodologies.md | 现金流与折现率匹配、资本投入约束、EV 至股权桥、估值方法交叉核对 | 正常化与现金口径已有合同；完整 DCF/comps/并购可比仍 defer。通用参数区间、方法权重和溢价不是公司特定证据 |
| financial-analysis/skills/competitive-analysis/SKILL.md | 先选行业关键指标，再对齐期间、定义、币种及竞争维度 | 全球公司研究已要求口径对齐；同业横向研究尚缺同等强度案例，不把“读过”写成能力通过 |

固定来源：[equity-research](https://github.com/anthropics/financial-services/tree/fca3cc8e6c5692ba576b46d7c4783b8443c2a223/plugins/vertical-plugins/equity-research/skills)、[competitive-analysis](https://github.com/anthropics/financial-services/blob/fca3cc8e6c5692ba576b46d7c4783b8443c2a223/plugins/vertical-plugins/financial-analysis/skills/competitive-analysis/SKILL.md)。

### 不吸收的约束与下一次触发条件

不移植固定字数/页数/图表数量、用户已授权完整流程却仍要求每阶段另发请求、机构版式或某个 Office 宿主的操作程序。不将上游的示例概率、资本开支比例、WACC 输入、可比溢价或方法权重设成本地默认值；数据可比和假设依据必须来自当前案例。

下一项优先候选是有真实材料的同业比较，而不是先开发新引擎：明确公司集合、研究截止日和决策问题；逐项核对财政期间、业务构成、会计定义、币种与证券身份；对不可比项保留缺口；解释可比组纳入/排除理由；再判断能否支持估值倍数。财务数字、股价时点与预期来源不能混搭。若开展 DCF，还需明确 UFCF/FCFE、折现率口径、资本再投入、终值条件、股权桥和敏感性；缺失时只交付研究观察，不能补造完整目标价。

本轮没有足够新证据要求改动已冻结核心，也没有新增运行行为。根 Apache-2.0 LICENSE 与旧哈希一致；所选路径无更近许可，tree 未发现 NOTICE/ATTRIBUTION。全文只保存在本地忽略目录，公开档案保留原创分析和元数据，未复制上游模板或代码到 Skill。

## 2026-09-15 历史适配记录

本轮固定到 `734150c2d9f312421611926f6e84c09d07ba13b1`，只审读以下源 Skill、README 与根 LICENSE。没有审完此前登记的两个完整 vertical 目录，因此来源级 reviewed_revision 保持 null。

| 固定源路径（均位于 plugins/vertical-plugins/） | 内容 SHA-256 | 本轮处置 |
| --- | --- | --- |
| equity-research/skills/earnings-analysis/SKILL.md | 4db857c27a53141b6ebc38ec9ee7f0020dec59cab084ae6753e53366d118c8ee | 适配旧预期/实际/差异/来源的连接方法，补全首次披露与财政窗口门禁 |
| equity-research/skills/model-update/SKILL.md | 62b2256bf3b52ac3759cb446a10aaa3066a51b4909e09bae0e3b98b741a37fb5 | 适配旧新输入、变化原因、重算估值和论文影响的记录链 |
| financial-analysis/skills/dcf-model/SKILL.md | 2bb3ed672ab2fa76f8820ee919b158a67dc6df10e7052eeb661599140a9a2494 | 已阅读公式可复算、敏感性基准等约束；完整 DCF 延后 |
| financial-analysis/skills/comps-analysis/SKILL.md | 2d49d9d694297da6ca3b084564ce10ed496f4ff21f275dae6b6c50d7b4dd889a | 已阅读可比组和口径约束；完整 peers/comps 引擎延后 |

官方来源：[固定目录](https://github.com/anthropics/financial-services/tree/734150c2d9f312421611926f6e84c09d07ba13b1/plugins/vertical-plugins)。下载内容的 Git blob SHA-1 与固定 commit tree 匹配。这里只保留原创审读结论、路径和哈希，不再分发上游 Skill 全文。

最值得保留的工作方法是：财报事件改变某些实际值或假设后，必须留下旧值、新值、原因、口径和来源，再重算估值，最后说明对既有论文的影响。Money Craft 将其落实为 `earnings_update.py` 的确定性计算、源文件绑定、顺序桥接和待确认 tracking handoff；并复用已有财务审计与历史封存。

机构报告篇幅、DOCX/Excel/Office JS 操作、供应商优先级以及宿主审批步骤不迁入共用核心。正式披露优先级和用户授权仍按 Money Craft 自身合同执行。原始数据与分析假设分开，程序不自动证明论点或生成买卖动作。

固定版本根 LICENSE 是 Apache-2.0，SHA-256 为 `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`；该 tree 未发现 NOTICE/ATTRIBUTION，所选四个 Skill 路径未发现更近许可文件。[固定 LICENSE](https://github.com/anthropics/financial-services/blob/734150c2d9f312421611926f6e84c09d07ba13b1/LICENSE)。本轮按行为独立实现，没有复制代码、模板或全文；未来若复制，应重新核验对应路径许可并履行归属要求。

## 行业与想法筛选增量审读（2026-09-20）

现场分支仍为 `fca3cc8e6c5692ba576b46d7c4783b8443c2a223`。本次全文审读 `equity-research/skills/sector-overview/SKILL.md`、`skills/idea-generation/SKILL.md` 及 `commands/sector.md`（前缀均为 `plugins/vertical-plugins/`）。逐文件验证固定tree中的Git blob及内容SHA-256；根LICENSE与此前已审Apache-2.0文件哈希一致，仅复核哈希，未声称新做全文许可审查。[审读回执](../../acceptance/upstream-anthropic-industry-20260920.json)。

行业概览强调研究范围、市场分层、竞争与投资含义；想法筛选强调行业主题到受益方的传导，以及筛选后仍需基本面研究。这些与本地产业链、反方、身份/日期及估值证据规则相容，不能因读到相似内容就声称新增能力。

有价值但本次暂不实现的部分是直接/间接受益、纯业务/多元暴露、市场规模叙事与实际可服务市场的区分。应用到锂案例时，下一步需要候选公司的分部收入与利润、产品及客户暴露、实际产能与利用率、同口径价格和估值材料；现有两份行业摘要不能填出这些数值。没有真实候选任务时，不新增通用筛选引擎或强制扩展报告。

不吸收上游固定筛选阈值、固定报告体量/图表及候选数量，也不因行业增长直接生成long/short结论。上游只是参考资料，其流程指令不取得本项目操作权限。

本次只更新来源决策和覆盖记录。三份文件不构成73文件完整审查，`reviewed_revision`继续为null，`absorbed_revision`保持原已适配版本；状态仍为review_required，原因是范围未审完，不能用“分支无新提交”把它标成全部完成。
