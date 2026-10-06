# Money Craft 上游参考、吸收与演进策略

2026-09-20：已完成[skfolio数据入口有界评估](upstreams/skfolio.md)与跟踪路径修正；运行时接入保持defer。此次仅推进观察及明确的局部评审决策，不推进来源级reviewed/absorbed，也不改变冻结Skill。

决定日期：2026-09-14。用户已确认最终同时建设 Skill 与独立应用，先做强 Skill 和共用研究核心，再建设应用。本文件是维护与能力演进依据，不是投资收益声明或运行时能力证明。

## 自主核心与两种入口

Money Craft 保持自己的产品定义和研究核心，在现有实现上逐步演进。Skill 负责研究意图、任务组织与结果解释；共用核心负责对象身份、证据、财务计算、估值、研究运行、审计、档案与 tracking；可选适配器提供数据、组合计算、回测实验与渲染；后续应用提供工作台、进度、检索、版本比较与长期观察体验。

共用核心沿用 Python，随着真实调用需求逐步脱离 CLI 参数、宿主提示词和展示逻辑。现有 CLI、档案与运行收据保持兼容；应用复用同一套计算、证据等级和状态语义。第一批上游治理不引入 Web 服务、数据库迁移、桌面框架或投资运行依赖，也不实施大规模目录重组。

Money Craft 的正式披露优先、证券身份、可复算数值、事实/推断/假设/未验证分级、反方证据与长期跟踪继续有效。外部页面和 Skill 是待评估资料，不取得本项目的指令权限；其供应商优先级、宿主约束、产品禁令或审批流程不能直接覆盖 Money Craft。研究、估值和用户明确约束下的决策支持与账户执行保持分离。

## 来源职责与当前证据

版本、哈希与决策的机器真源是仓库根目录的 `sources.lock.json`。本表说明用途，不重复维护可漂移的版本号。

| 来源 | 定位与拟议吸收内容 | 当前边界 |
| --- | --- | --- |
| [Anthropic financial-services](https://github.com/anthropics/financial-services) | 专业研究 Skill 的主要参考：财报前瞻/复盘、估值、模型更新、催化剂、行业覆盖 | 已评估公开结构和部分 Skill；跟踪范围尚未逐文件完整审查。优先使用原始 vertical skills，避免重复吸收 bundled copies。商业数据授权单独核验。 |
| [策引 MyInvestPilot](https://www.myinvestpilot.com/docs/) | 组合研究与长期观察的主要参考：状态证据、规则/资金分层、语义保真、实验隔离、失败记录 | 155 个公开目录入口完成正文审读；完整记录见[专题档案](upstreams/myinvestpilot.md)。引擎源码、会员运行时、数据和代码许可未验证。 |
| [AI Berkshire](https://github.com/xbtlin/ai-berkshire) | 延续公司质量、投资论文、反证与财务核对的方法来源 | 保留现有 pin、pristine submodule、许可、映射和连续审查历史。 |
| [skfolio](https://skfolio.org/) | 优先评估的组合计算适配器：风险预算、约束、压力与样本外验证 | 候选，未安装或接入；不将优化结果直接作为个人配置。 |
| [OpenBB](https://docs.openbb.co/odp) | 当现有 Provider 覆盖不足时补充数据接口 | 候选；保留 Fuyao、yfinance、FRED/ALFRED 和正式披露优先级。模块及数据许可分别验证。 |
| [Dexter](https://github.com/virattt/dexter) | 研究任务组织、正确性及矛盾评测 | 借鉴方法，暂不复制独立 Agent runtime；许可原文仍须确认。 |
| [Qlib](https://github.com/microsoft/qlib)、[RD-Agent](https://github.com/microsoft/RD-Agent) | 因子与量化实验观察名单 | 有明确研究任务和可用数据时再审查接入。 |
| [LEAN](https://github.com/QuantConnect/Lean) | 策略模拟与执行语义观察名单 | 有独立回测立项后评估；本轮不建设账户执行。 |
| [TradingAgents](https://github.com/TauricResearch/TradingAgents) | 多视角研究与历史信息泄漏控制参考 | 未独立验证收益或本地可运行性；多 Agent 数量不是质量证明。 |

源代码参考、文档参考、数据来源、可选依赖和实际采用是不同关系。许可证元数据/README 声明仅用于初筛；复制代码前核验对应固定版本的 LICENSE/NOTICE，必要时保留归属。公共文档可阅读不等于可整站再分发。候选仓库不会作为 submodule 或运行依赖自动加入。

## 检查、审查与吸收

### 机器记录

保留 `money-craft.sources.v1` 的已有 `upstreams` 和 `documents`；新增可选、独立版本化的 `reference_tracking`（`money-craft.reference-tracking.v1`）。旧 `documents` 是历史引用，不被伪装为本轮已自动监测的上游。

每个新增来源记录 `kind`、`role`、用途、许可状态、跟踪范围、`observed`、`reviewed_revision`、`absorbed_revision` 与 `decisions`。Git 使用 40 位提交；文档使用正文与目录快照的 SHA-256。只有完整审查了声明的跟踪范围，才能设置 `reviewed_revision`；看过 README 或少量文件的来源保持空值，阅读范围在 `review_notes` 中说明。

文档的 `reviewed_snapshot` 保存规范 URL、最终 URL、标题、正文哈希及完整目录声明，不保存全文。它是审读版本基线，不证明网站当前仍相同。`observed` 是某次观察，也不表示内容已被吸收。现有 AI Berkshire 使用其历史 `reviews[-1].through_commit` 作为检查基线，既有字段语义不变。

### 使用命令

```bash
# 旧接口保持 v1 输出与原有退出码，只检查 AI Berkshire。
python3 scripts/upstream_status.py --fetch --json

# v2：检查登记的全部候选和 AI Berkshire；默认不访问网络。
python3 scripts/upstream_status.py --all --json

# 现场读取公开 Git 分支；策引需要完整浏览器目录快照。
python3 scripts/upstream_status.py --all --fetch --json

# 只检查指定来源，可重复 --source。
python3 scripts/upstream_status.py --source anthropic-financial-services --fetch --json
python3 scripts/upstream_status.py --source myinvestpilot --snapshot /tmp/myinvestpilot-capture.json --json

# 将完整捕获转换为仅含哈希等元数据的候选快照，输出到 stdout。
python3 scripts/upstream_status.py --snapshot-only /tmp/myinvestpilot-capture.json
```

v2 的 `current` 要求所选全部来源均有现场证据或 24 小时内的完整文档快照，并且没有待审查版本。`cached` 只说明本地记录，`stale` 表示快照超过 24 小时，`review_required` 表示需要审查；`unavailable`/`partial` 表示无法核验全部来源。退出码：0 全部 current；2 缓存/过期/待审查；1 输入错误、来源不可用或部分失败。上游更新与故障应分别处理，不为退出码变绿推进审查记录。

Git 检查固定分支引用；存在已审查基线时比较两个不可变 tree 在 `tracked_paths` 内的文件，报告新增、删除和修改（重命名表现为删除+新增）。tree 截断时不能关闭覆盖。即使新提交没有命中所跟踪路径，也需要明确记录该轮范围外变化的处置，不自动推进基线。

尚未完成初次完整审查的来源，若分支相对登记的 observed 版本又有更新，仍可比较这段新增变化；输出 `tracked_paths_since_observation`，不会伪称整个待审查范围已覆盖。没有比较时明确输出 `not_compared`，空 changes 不等于上游没有变化。

策引侧栏需要在浏览器中展开才能确认完整目录，CLI 不把服务器渲染的局部链接当作完整 sitemap。`--fetch` 没有提供完整快照时将其报告为 unavailable，其他 Git 来源仍继续检查。损坏、不可读或缺少来源 ID 的捕获通过 capture_errors 报告，并保留其他来源结果。不绕过登录、访问挑战或会员边界。

### 文档捕获合同

按宿主的 browser67 规则创建自己的公开页面 tab，展开目录所有折叠项，去重全部文档链接，再读取每个页面。捕获存放在仓库外，格式如下；`catalog_urls` 和 `pages` 必须一一对应，且包含文档根页面。

```json
{
  "schema": "money-craft.doc-capture.v1",
  "source_id": "myinvestpilot",
  "captured_at": "2026-09-14T12:00:00+00:00",
  "catalog_complete": true,
  "catalog_urls": ["https://www.myinvestpilot.com/docs/"],
  "pages": [{
    "url": "https://www.myinvestpilot.com/docs/",
    "final_url": "https://www.myinvestpilot.com/docs/",
    "status": 200,
    "title": "策引文档中心",
    "structure_sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
    "text": "这里填写真实 article.textContent；此 JSON 仅演示格式。"
  }]
}
```

`text` 必须取真实 `article.textContent`，同时提供浏览器计算的 `structure_sha256`，标题使用目录题名并在改名时更新。通过 browser67 在自有文档 tab 中执行仓库的 `scripts/upstream_capture.js`，按小批次调用 `captureUpstreamPages(catalog)` 获取两者；catalog 是已展开的目录题名与 URL 列表。也可用 `html` 代替 `text`，检查器从唯一最外层 article 提取正文并计算结构摘要，允许分类导航在其中嵌套 article 卡片。捕获者对目录完整性负责；检查器能验证集合闭合，不能独立证明浏览器已展开所有目录。示例摘要表示无表格/代码块，仅演示格式，不是验收证据。

`article-text-structure.v1` 忽略 article 外的页面装饰，统一正文换行并去掉末尾的策引更新日期，保留内部空格、零宽字符、数字和代码字面量。浏览器 helper 与 HTML parser 使用相同结构 token：table/tr/td/th/pre 的开闭边界、rowspan/colspan 和内部文本；结构摘要采用紧凑 JSON 的 SHA-256。页面哈希为 SHA256(归一化正文 + 换行 + 结构摘要)，防止 1|23 和 12|3 两张表被合并成同一个 123。摘要由捕获者提供，不是服务器签名或独立来源认证。改变算法必须重新审读建基线。同域文档路径内的跳转独立报告；跳到登录或其他路径、失败响应、挑战页、缺正文、重复 URL、漏页或不完整目录会拒绝该快照，不能据此认定页面删除。

目录移除表示 `removed_from_catalog`，不宣称原页面已经 HTTP 404。它与“页面仍在目录但读取失败”分别处理。正文快照使用同一个完整目录，新增和移除不能被预先固定的旧 URL 列表掩盖。

### 人工审查与采纳

每周检查一次，修改对应能力前再检查一次。当前不创建后台任务、邮件或外部通知。维护者按以下流程处理结果：

1. 记录观察版本、变化范围和读取失败；先修复证据缺口。
2. 阅读相关差异及上下文，识别文档冲突、接口变化、数据/许可限制、失败案例和已知缺陷。
3. 给出 `adopt`（直接采用）、`adapt`（适配后采用）、`defer`（暂缓）、`reject`（不采用）；记录范围、理由、本地目标与验证证据。暂缓必须有重新评估条件。决策按时间追加，后续处置只覆盖其明确 scope；absorbed_revision 表示已适配方法所依据的版本，不表示整套文档或项目均已吸收。
4. 在本地实现、行为验证与许可要求满足后，才能记录 `adopt/adapt` 和 `absorbed_revision`；仅有文档候选用 `defer`。完整审查可以推进 reviewed，但不移动 submodule pin、不冒充已采用。
5. 审查记录和代码一起接受范围内验证。上游回到旧基线也不能清除已经登记的未审查 observation，必须显式处置。检查器与快照转换器始终不修改 lock；commit、push、安装和发布分别遵循当前授权。

## 能力建设顺序

以下队列随实际交付更新。UP-01 已完成首批研究与跟踪可靠性实现，验证见 [UP-01 记录](../openspec/changes/fix-research-status-reliability/validation.md)；UP-02 的首条财报更新链也已通过两期正式年报回放，见 [UP-02 验证](../openspec/changes/add-earnings-update-core/validation.md)；其余仍待实施。每项实施前形成有界规格和案例验收，不以新增提示词或文档替代运行验证。

| ID | 能力 | 验收方向 |
| --- | --- | --- |
| UP-01 | 研究与状态可靠性（已实现） | 未知评分、复核时效、v1 档案兼容、计算失败与引用绑定通过本地回归；来源语义与实际时效保持 UNVERIFIED。 |
| UP-02 | 专业研究闭环（首条更新链已实现） | 财报比较 → 旧新模型输入 → 三情景倍数估值桥 → 论文/tracking交接已验证；独立前瞻、催化剂系统、DCF和完整comps仍待扩展。 |
| UP-03 | 个人组合分析 | 现金流、币种、集中度、重叠暴露、回撤与压力情景；计算口径和用户约束明确。 |
| UP-04 | 受控策略实验 | 假设、基线、语义保真、成本/数据/样本、实验收据和失败记录；候选不静默改写正式研究。 |
| UP-05 | 研究评测 | 固定案例覆盖事实/计算错误、证据缺失、矛盾解释、前视偏差和异常结果，衡量真实改善。 |

应用阶段在这些核心能力经过真实研究验证后，建设工作台、进度、档案检索、组合视图和版本比较。应用与 Skill 对同一输入须使用相同的核心结果、证据和状态，不另造口径。

## 本批验收

- 专题覆盖必须与登记的 155 个 URL 一致，149 content + 6 navigation；审读不等于引擎验证。
- 离线测试覆盖 Git 新/改/删、文档新/改/目录移除/重定向、装饰噪音、数字与代码变化、过期/不完整/挑战页面、局部来源失败和旧 CLI 兼容。
- 检查前后来源 lock 字节保持一致；部分失败不妨碍其他来源给出结果，也不得输出全部 current。
- 现有来源映射、验证和打包检查继续通过。docs、检查脚本、测试、规范与完整第三方资料不进入运行包；lock 中仅增加归属与哈希等元数据。
- 现场网络状态单独报告。离线测试通过不能证明外部服务可用，更不能证明已接入回测或投资能力。

### 行业研究后的吸收决策

2026-09-20新增[Anthropic行业与想法筛选审读](upstreams/anthropic-financial-services.md)：三份原始vertical文件全文核验，当前分支未变化。来源锁新增精确范围的defer/reject记录，未推进来源级reviewed或absorbed。行业增长到候选公司经济暴露的映射留待真实候选研究，不把通用阈值和报告配额设为默认值。当前Skill及全局安装不变。
