# 上市公司完整研究

## 统一入口

证券身份、`as_of` 和最新正式报告期明确后，先运行 `money_craft.py research plan`。计划必须绑定已核实的公司名称、唯一 `security_id`、市场、基础币种、最新报告期、真实期末日和最近年度报告期，并输出：

- `identity -> official-evidence -> provider-cross-check -> research -> valuation-and-thesis -> audit` 六阶段门禁；
- 固定来源 ID 的有界 Provider 操作矩阵；无适配器或未配置时矩阵为空并声明 gap，不阻断正式文件研究；
- 最新正式报告、年度报告、交易所或公司 IR 三类必需一手证据，以及按重要性触发的重大事项、管理层问答和期后事项来源槽位；
- report、thesis、financial reconciliation、metadata-only evidence manifest 和五项 audit artifact 合同。

五年财务或正常化基线需要较早年报时，以可选`S21/S22`导入原始历史年报，保留实际报告期、获取时间和引用。它们不替代最新年报`S12`，也不占用事件来源`S18/S19/S20`。较早年报与最新年报来自同一发行人，不构成独立双源。旧已初始化计划保持不变；需要新增历史来源时新建运行，不改写旧plan/case。

公开行情页面无法通过已配置 Provider 获取时，新计划另列可选 `S31/S32`（行情快照及交叉核对快照）。用 `research import-public` 导入本次实际捕获的 PDF/HTML，不使用 `import-official`，不把页面改写成 Provider 响应。先在采集时留存原始 body、URL 与捕获记录，再导入；来源仍为 `public-material / unverified-public`，不替代 `S11/S12/S13`，不自动证明行情、证券身份或来源独立性。两个转载站点也可能共享数据源。

```bash
python3 "$MONEY_CRAFT_SKILL_DIR/scripts/money_craft.py" research import-public \
  --workspace <init返回的workspace> --source-id <S31|S32> \
  --file <原始行情快照> --url <捕获时登记的HTTPS链接> \
  --captured-at <带时区的实际抓取时间> --observed-at <带时区的行情时点> --json
```

`observed-at` 必须来自页面或相应数据说明，不把抓取时间当成行情时间；缺少可核实的时点则保留缺口。观察时间不得晚于抓取时间或研究截止日（按上海日期检查）；抓取时间允许晚于历史研究日，但必须披露为事后回放。时间字段是调用方声明，导入只检查结构与顺序并绑定文件哈希，不能证明网页与声明一致。报告另核对证券、股类、交易币种、价格是否复权、收盘/盘中口径和股本时点，冲突未解决时不输出确定性估值。

公开来源在 `case.public_sources`、状态 `public_results` 与 manifest 中单列；URL、文件哈希、抓取时间和观察时间纳入封存绑定。旧计划没有这些来源槽位时仍按原合同运行，补充行情须新建研究运行。导入共用锁、不可覆盖、封存后禁止写入和中断检测，不能修改旧 case 或放宽引用审计绕过失败。

先把包含 Skill 的目录解析为绝对路径 `MONEY_CRAFT_SKILL_DIR`，再运行：

```bash
python3 "$MONEY_CRAFT_SKILL_DIR/scripts/money_craft.py" research plan \
  --security <已核实的公司名称> --security-id <MARKET:SYMBOL> --base-currency <USD|HKD|CNY|...> \
  --as-of <YYYY-MM-DD> --latest-report <YYYY-1..4> --latest-report-end <YYYY-MM-DD> \
  --latest-annual-report <YYYY-4> \
  --provider <auto|fuyao|yfinance> --provider-mode <auto|required|disabled> --json
```

`research plan` 是可重复的执行规格，不是研究结果。它不访问网络，不证明 Provider 数据存在，也不能替代实际来源捕获、计算和审计。

## 可恢复研究运行

### 初始化前声明附加资料

研究预计使用较早季报、更多历史报告、独立交叉核对页等，且默认槽位不适用时，在 `plan/init` 增加 `--additional-evidence <JSON文件>`。文件是最多16项的数组、最大64 KiB；每项只有 `id`、`kind`、`role` 和可选 `period`。编号为唯一 `Sxx`（2–4位数字），不得与默认来源或 Provider 操作冲突。例：

```json
[
  {"id":"S23","kind":"official-document","role":"单季差分所需的较早季度正式报告","period":"2026-1"},
  {"id":"S40","kind":"public-material","role":"额外公开行情交叉核对"}
]
```

`kind` 仅支持 `official-document`（正式报告）、`official-index`（HTML披露索引）、`official-material`（其他正式PDF/HTML材料）和 `public-material`（公开补充PDF/HTML）。`role` 必须说明用途，1–256字符；报告期如填写则为 `YYYY-1..4`。声明只确定来源角色，不验证材料真假、期间或观点。附加项均为可选来源，不替代默认必需披露；报告实际引用的附加项仍必须成功导入并通过绑定。

正式类型使用 `import-official`，公开类型使用 `import-public`，后者仍需抓取时间与观察时间并保持 `unverified-public`。文件内容在初始化时进入不可变计划，不依赖此JSON文件后续版本。运行中才发现缺少声明时，保留旧运行并用补齐声明的新计划初始化，再导入已捕获原件及真实获取时间；不改写旧plan/case，不重新下载后冒充旧响应，也不把季报塞入用途不符的资本事项槽位。

需要落地研究时，使用 `research init` 将 plan 固化到本地 workspace。`case.json` 必须由 `plan.json` 自动派生；不得另写一份 Provider 操作列表。workspace 的状态真源包括不可变 plan、派生 case、append-only `run-state.json`、私有 `evidence/`、报告、论文、审计和完成收据。

```bash
python3 "$MONEY_CRAFT_SKILL_DIR/scripts/money_craft.py" research init \
  --security <已核实的公司名称> --security-id <MARKET:SYMBOL> --base-currency <三字母币种> \
  --as-of <YYYY-MM-DD> --latest-report <YYYY-1..4> --latest-report-end <YYYY-MM-DD> \
  --latest-annual-report <YYYY-4> \
  --provider <auto|fuyao|yfinance> --provider-mode <auto|required|disabled> --json
python3 "$MONEY_CRAFT_SKILL_DIR/scripts/money_craft.py" research collect \
  --workspace <init返回的workspace> --resume --json
python3 "$MONEY_CRAFT_SKILL_DIR/scripts/money_craft.py" research import-official \
  --workspace <init返回的workspace> --source-id <S11|S12|S13|S21|S22|S18|S19|S20> \
  --file <正式来源文件> --url <HTTPS正式来源> --json
python3 "$MONEY_CRAFT_SKILL_DIR/scripts/money_craft.py" research status \
  --workspace <init返回的workspace> --json
python3 "$MONEY_CRAFT_SKILL_DIR/scripts/money_craft.py" research finalize \
  --workspace <init返回的workspace> --json
```

1. `research collect --resume` 只在 case 含 Provider 操作时执行有界采集，已有 normalized response 和 capture 不覆盖；无适配器时不要调用 `collect`，直接导入正式来源。单项失败形成显式 Provider gap，并返回非零结果。
2. `research import-official` 逐项导入 plan 声明的 `S11/S12/S13`；当重大交易或资本事项、官方问答、报告期后事项影响结论时，再分别导入 `S18/S19/S20`。命令校验 PDF/HTML、HTTPS 来源、大小和 SHA-256，不负责联网下载。
3. `research status` 离线重算每一阶段，列出 missing sources 和 provider gaps；文件存在不等于阶段完成。
4. 完成 plan 自动生成的 `financial-reconciliation.json`，再写报告和 thesis。`research finalize` 生成 metadata-only manifest、四项 report/thesis audit 和 reconciliation audit；只有身份一致性、证据文件、文档引用绑定、计算与勾稽等机器检查全部有效时才产生 completion receipt。
5. 收据绑定 plan、case、manifest、报告、论文和审计文件哈希。收据之后任一绑定文件变化都必须显示 stale，不得继续宣称完成。

写作时以本次初始化生成的 report/thesis 模板保留必需二级标题，扩展主题放在其下的正文或三级标题。例如保留 `## 重大披露与期后事项`，把“资本配置”放到下级，不能改写必需标题导致章节检测失败。论文证伪表使用准确列名 `| ID | 条件 | 严重度 | 当前状态 | 证据 |`；严重度为 `material/fatal`，状态为 `CLEAR/WATCH/TRIGGERED/UNVERIFIED`。触发后的行动可保留在“条件”描述中，证据列绑定实际导入来源。格式修正不删除条件、替换事实或把未知状态改成通过。

报告与 thesis 的引用编号必须来自本次实际成功采集或导入的来源。来源索引中的 `evidence/...` 路径须与该编号的证据记录相符；公开链接须使用该编号导入时登记的精确 URL，可写作裸 URL 或单一 Markdown 链接。Provider 来源未登记公开证据 URL 时使用其本地证据路径（写法见下文完成状态校验），不把接口文档当作数据来源。不能通过自行添加来源索引掩盖虚构编号、失败采集或错配文件/网页；页码等定位说明另写在正文，避免改变登记 URL。

封存收据存在后，`collect`（含 `--resume`）与 `import-official` 拒绝修改该工作区，补充证据须新建研究运行。采集、恢复、状态检查和封存都会用 `capture.json` 核对来源编号、Provider、操作、时间、request ID 及原始响应 SHA-256/字节数；元数据缺失、不匹配或响应漂移时返回结构化错误，不重新计算哈希来接纳变化，也不为旧工作区补造历史哈希。

工作区入口共用一把非阻塞锁；不要手工删除或替换工作区旁的锁文件，也不要绕过 CLI 直接改工作区文件。按返回码处置：

| 返回 | 含义 | 处置 |
|---|---|---|
| `workspace_busy` | 另一入口正持有工作区锁 | 等当前操作结束后重试 |
| `existing_workspace` / `existing_artifact` | 目标已存在或并发写入竞争失败 | 不覆盖；复用已有结果或新建运行 |
| `incomplete_collection` | capture 已发布但标准化结果缺失，或留有暂存目录 | 保留现场，新建运行重新采集；若只缺汇总/事件，可 `collect --resume`，结果中 `network_requests_attempted` 应为 0（缺失来源仍会请求） |
| `incomplete_import` | 官方导入在事件记录前中断，或留有待导入/暂存文件 | 保留现场，新建运行重新导入；不得自行补造完成事件 |
| `state_limit` | 事件容量已满 | 未请求数据、未改写工作区；新建运行 |
| `status` 显示 `stages.finalization_event=pending` | 收据已发布但完成事件未记入 | 重试 `finalize`；它在锁内复核全部绑定后只补记事件，证据漂移时拒绝 |

这些是本地完整性校验，不证明外部来源真实性，也不证明断电耐久性。锁与原子发布的实现细节及未闭环项见源码仓库 `docs/research-lifecycle-boundaries.md`。

`valid`/`complete` 表示各自的执行、审计或封存合同，不表示值得投资。读取 `assessment` 中的证据覆盖、引用绑定、收据完整性、论点支持和来源时效；允许保留 Provider gap 的已封存运行仍应显示覆盖限制。导入成功只证明文件及元数据被保存和哈希绑定，不能自动证明发行人、报告期、披露日期或论点语义正确。因此程序不能独立核验的论点支持与来源时效保持 `UNVERIFIED`；Agent 仍须核对正式披露和研究截止时间，不能将旧材料或成功 HTTP 响应当作当前证据。

默认 workspace 位于 `~/Documents/sixseven/money/<identity>-<company>/<as_of>/.research/<run-id>/`；A 股旧路径仍保持六位代码前缀，其他市场使用 market-symbol 前缀。`MONEY_CRAFT_OUTPUT_ROOT` 和 `--output-root` 可改变根目录，显式 `--workspace` 可完全覆盖。必须复用 `init` 返回的动态路径，不使用 `latest` 软链接或共享可变目录。`.research` 仅是 Money Craft 私有研究态，不得伪装成正式档案；完成正式投资账本、审计、离线 verifier 和 seal 后，准出真源才位于同一公司/日期下的 `revisions/rNNNN/`。任何凭据、原始 Provider payload、下载公告或网页快照都不得进入 Git。

## 研究语义准出

交付前按 [research-semantic-review.md](research-semantic-review.md) 核对决策相关主张、来源血缘、反方对估值的影响和缺失数据的实际限制。completion receipt 不替代此项；仅完成有界观察或敏感性演示时明确交付范围。

## 全球市场口径

- `security_id` 是证券身份，发行人不是证券。A/H 股、普通股/ADR、不同投票权类别分别建身份，并记录权利、股本换算和发行人映射。
- 非 A 股显式记录财政期标签和真实期末日，不把自然季度日历套到 52/53 周财年、非 12 月年结或变更财年的公司。
- 同时保留财报列报币种、交易币种和估值基础币种；汇率来源、时间点和换算公式进入证据链。
- 会计准则、非 GAAP 指标、租赁、少数股东、股权激励和股份稀释在跨市场比较前统一。无法统一时给范围而非伪精确排名。
- 正式来源按当地监管机构、交易所和公司 IR 获取；SEC/EDGAR、港交所、各国监管披露或发行人 HTML filing 都可作为正式文件。任何结构化 Provider 的 symbol 检索都不能替代非 A 股法定身份与 share class 验证。

## 重大披露来源路由

`S13` 是交易所或公司 IR 披露索引，不代表只检查定期报告。出现以下依赖时必须扩展一手披露面：

- 子公司财务、增资、股权激励、稀释、回购权、关联交易或其他或有义务影响结论：检索并导入 `S18`；
- 管理层解释、回避或未回答的问题影响 thesis：检索官方业绩说明会、路演或问答并导入 `S19`；
- 报告期后融资、上市、并购、出售、回购或其他重大事项改变资本结构或估值：导入 `S20`。

没有触发条件时，可选槽位保持 `optional-not-imported`，并在 `material_disclosure_assessment` 中标记 `not-triggered`；不为凑齐来源而导入无关材料。触发后必须导入对应槽位并标记 `imported`，不得只引用搜索摘要或二手报道。artifact 状态与实际导入状态不一致会阻断 finalize。

## 重述与三表勾稽

`financial-reconciliation.json` 是结构化研究回执，不是财务数据来源。至少完成：

1. 本期和比较期分别标记 `reported`、`restated` 或 `comparable-estimate`，禁止重述前后口径直接同比；`comparable-estimate` 必须内嵌可重算的 `calculation`；
2. 校验 `资产 = 负债 + 权益` 以及现金流量表期末现金与资产负债表现金；
3. 最新报告为 Q2-Q4 时，校验 `本期累计 - 上期累计 = 单季值`；
4. 明确会计列报影响、经营解释和现金影响之间的桥接；
5. 明确报告期后重大事项是已识别、未披露还是仍未核实。

所有输入保留单位与 `[S#]`，审计只证明算术、口径标签和来源绑定自洽，不替代对附注及会计政策的人工判断。

## 研究顺序

1. **资料与偏见**：评级资料可得性，写出市场共识和最可能的共识陷阱。
2. **生意本质**：客户是谁、为何付费、收入和成本如何形成、哪些变量决定十年结果。
3. **财务画像**：至少覆盖五年收入、利润、现金流、资本开支、负债、股本和回报率；年度优先，季度用于识别变化。
4. **护城河**：只接受可观察证据，例如价格、留存、份额、单位成本、渠道、牌照、研发结果；区分存量和变化方向。
5. **管理层与治理**：承诺兑现、资本配置、关联交易、股权激励、并购和会计选择。
6. **逆向思考**：列出最强反方论证、可导致永久损失的路径、可能被忽略的替代品和监管变化。
7. **估值与安全边际**：使用适合商业模式的方法，至少给悲观/中性/乐观三种情景和关键敏感变量。
8. **结论**：说明当前证据支持什么、不支持什么、需要观察什么，以及哪些事实会推翻结论。

若结论把公司描述为“时代主线”“行业核心资产”或高增长赛道的 α，必须同时加载 `high-growth-alpha.md`。该主张需要有界产业链、可比同行、财报与高频经营信号、矛盾台账和可观察拐点共同支持；行业景气或股价表现本身只能证明 β，不能证明公司 α。

## 护城河证据表

| 类型 | 事实 | 来源 | 方向 | 反方解释 | 置信度 |
|---|---|---|---|---|---|
| 品牌/定价权 |  | `[S#]` | 变宽/稳定/变窄 |  | 高/中/低 |
| 转换成本 |  | `[S#]` |  |  |  |
| 网络效应 |  | `[S#]` |  |  |  |
| 规模/成本 |  | `[S#]` |  |  |  |
| 技术/牌照 |  | `[S#]` |  |  |  |

“竞争对手投入大量资本能否复制”必须拆成时间、渠道、数据、品牌、组织和监管约束，不能只凭直觉回答。

## 结论纪律

清楚区分好公司、好生意和好价格。若估值所依赖的盈利不是正数、现金流不可持续或数据冲突未解决，停止输出精确目标价，改为条件区间和补证事项。不得把报告完整度当成投资确定性。

完成状态校验需要沿收据→manifest→本地证据文件逐层重算哈希；原始响应或规范化数据漂移时，complete 必须为 false，完整性不得仍标为 VERIFIED。来源索引若使用本地 evidence 路径，只写精确路径（纯文本或行内代码，同一行不加标题）；审计虽接受单一 Markdown 链接，但 HTML/PDF 渲染会拒绝相对路径链接；附加远程 URL 不得绕过本地路径绑定，混合且无法明确解析的格式直接拒绝。

研究计划的报告期必须自洽：A 股显式 `latest_report_end` 应与 `latest_report` 的自然季度期末一致；`latest_annual_report` 的财年/季度序号不得晚于最新报告。非 A 股保留显式财政期末与财政年度标签，不强行套用自然年度。

### 现金口径桥与证券名称

Fuyao 的 `--security` 使用经官方报告核实、与 Provider 身份记录一致的股票简称；报告同时保留法定公司全称、交易所与代码。不要用任意别名绕过身份校验。

当合并资产负债表“货币资金”不等于现金流量表期末现金及现金等价物时，`cash-balance-tie` 保留两个原始输入，可增加 `cash_adjustments`：每项包含唯一 `CAxx` 的 `id`、有符号 `amount`、含报表附注或页码定位的 `reason`、可用证据中的 `source_ids`。系统以原始货币资金加全部调整后勾稽；不提供调整时仍直接勾稽。所有分量必须同报告期、币种、单位和合并范围，防止重复计入。只接受披露支持的范围调整，禁止把差额倒算成无依据的平衡项。机器通过仅证明结构、引用绑定与算术一致，不证明现金可分配性、经营质量或调整解释正确；研究者须对照正式报告复核。
